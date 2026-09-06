"""Drive the real calibration app in a real browser.

Why this exists, in one paragraph
---------------------------------
The labelling chart's drag interaction was delivered three times and worked zero
times. Each round was checked, and each check passed. The last of them ran the
component's JavaScript against a hand-written DOM stub under Node — which tests
the JS in isolation, and the JS was never the problem. The bug was in the Python
that MOUNTS the component (`key=f"lab_chart__{sid}"`; `__` is reserved inside a
bidirectional component's id, so the mount raised on every render and the
exception was swallowed by a static fallback). No amount of simulated DOM could
have found that, because the simulated DOM never ran the mount.

So this harness does the only thing that would have: it starts
`streamlit run tools/calibration_app/app.py` on a free port, opens Chromium at
it, clicks into the Label mode, and operates the page with real pointer events
(`mouse.move` / `mouse.down` / `mouse.up` — not `dispatchEvent`). Every assertion
is read back from the values Streamlit rendered from PYTHON state, never from a
pixel: "the bar moved on screen" is not a pass, because the bar moving on screen
is exactly what a broken build does before the value is dropped.

Cost and scope
--------------
Booting Streamlit and Chromium takes a few seconds per session, so the server and
the browser are session-scoped and every test shares one page. Playwright and its
Chromium are TEST-only dependencies: they are installed by hand
(`pip install playwright && python -m playwright install chromium`) and every
test that needs them skips when they are absent. Nothing here is added to the
package's requirements, to requirements-app.txt, or to CI.

This harness never presses Save. `research/labels/manual_labels.yaml` is the
artefact the whole front exists to produce, and a test suite that can write to it
is a test suite that can corrupt it. Everything asserted here is read from the
phase table, which is Streamlit rendering the same `st.session_state` list that
a save would serialise.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"

BOOT_TIMEOUT = 120        # seconds to wait for the HTTP server to answer
RENDER_TIMEOUT = 180_000  # ms; the first render loads 51 CSVs and 12 synthetics


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class AppServer:
    """`streamlit run` on a free port, torn down on exit."""

    def __init__(self, log_path: Path):
        self.port = free_port()
        self.log_path = Path(log_path)
        self._log = None
        self._proc = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    def start(self) -> "AppServer":
        self._log = open(self.log_path, "w")
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(APP),
             "--server.port", str(self.port),
             "--server.headless", "true",
             "--server.fileWatcherType", "none",
             "--browser.gatherUsageStats", "false"],
            stdout=self._log, stderr=subprocess.STDOUT, text=True,
            cwd=str(REPO_ROOT),
            env=dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"),
        )
        deadline = time.time() + BOOT_TIMEOUT
        while time.time() < deadline:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"streamlit died during boot:\n{self.log()}")
            try:
                urllib.request.urlopen(self.url, timeout=2).read()
                return self
            except Exception:
                time.sleep(0.4)
        raise RuntimeError(f"streamlit did not answer in {BOOT_TIMEOUT}s")

    def log(self) -> str:
        try:
            return Path(self.log_path).read_text()
        except OSError:
            return ""

    def stop(self) -> None:
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        if self._log is not None:
            self._log.close()


class LabelPage:
    """The Label mode of the running app, driven through a real browser.

    Index arithmetic is done in the page via the SVG's own screen CTM rather than
    recomputed here from the viewBox: the chart scales with
    `preserveAspectRatio`, so the mapping from a step index to a viewport pixel
    is something only the live element knows. That also means the coordinates fed
    to `mouse.move` are the ones the browser will hand back as `clientX`, which
    is the number the component actually reads.
    """

    CHART = "#cp-label-chart svg"

    def __init__(self, page):
        self.page = page
        self.errors: list[str] = []
        page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: (
            self.errors.append(f"console.{m.type}: {m.text}")
            if m.type == "error" else None))

    # ── getting there ────────────────────────────────────────────────────────
    def open(self, url: str) -> "LabelPage":
        self.page.goto(url, wait_until="load")
        self.page.wait_for_selector("text=Display mode", timeout=RENDER_TIMEOUT)
        self.page.get_by_text("Label", exact=True).first.click()
        self.page.wait_for_selector("text=Manual labelling",
                                    timeout=RENDER_TIMEOUT)
        self.settle()
        return self

    def settle(self, ms: int = 1200) -> None:
        """Wait for Streamlit to stop rerunning.

        Streamlit shows a "Running..." status while a rerun is in flight; when it
        is gone and the DOM has been quiet briefly, the value on screen is the
        value Python rendered.
        """
        self.page.wait_for_timeout(250)
        try:
            self.page.wait_for_selector('[data-testid="stStatusWidget"]',
                                        state="detached", timeout=30_000)
        except Exception:
            pass
        self.page.wait_for_timeout(ms)

    # ── the chart ────────────────────────────────────────────────────────────
    def has_chart(self) -> bool:
        return self.page.locator(self.CHART).count() > 0

    def mount_error(self) -> str | None:
        """The visible message when the component could not be mounted."""
        loc = self.page.get_by_text("The interactive chart could not be mounted")
        return loc.first.inner_text() if loc.count() else None

    def chart_alert(self) -> str:
        """The component's own in-chart warning text (empty when all is well)."""
        if not self.has_chart():
            return ""
        return self.page.locator(self.CHART).evaluate(
            "(svg) => { const t = [...svg.querySelectorAll('text')]"
            ".filter(e => e.getAttribute('fill') === '#c1121f');"
            "return t.length ? t[0].textContent : ''; }")

    def _client_x(self, index: float) -> float:
        """Viewport x of a step index, from the live SVG's own transform."""
        return self.page.locator(self.CHART).evaluate(
            """(svg, i) => {
                 const vb = svg.viewBox.baseVal;
                 const ml = 74, mr = 22;
                 const pw = vb.width - ml - mr;
                 const n = +svg.dataset.n;
                 const vx = ml + (i / (n - 1)) * pw;
                 const p = svg.createSVGPoint();
                 p.x = vx; p.y = 0;
                 return p.matrixTransform(svg.getScreenCTM()).x;
               }""", index)

    def _client_y(self) -> float:
        box = self.page.locator(self.CHART).bounding_box()
        return box["y"] + box["height"] * 0.55

    def _n_steps(self) -> int:
        return int(self.page.locator(self.CHART).evaluate(
            "(svg) => +svg.dataset.n"))

    # ── real pointer gestures ────────────────────────────────────────────────
    def drag_boundary(self, k: int, to_index: int, release: bool = True,
                      release_outside: bool = False, before_release=None) -> None:
        """Grab boundary `k` by its body and slide it to `to_index`.

        Real pointer events, moved in several steps: a single jump from press to
        release is not what a hand does, and a handler that only works for one
        big move is not working.
        """
        y = self._client_y()
        start = self._client_x(self.start_idx(k))
        end = self._client_x(to_index)
        self.page.mouse.move(start, y)
        self.page.mouse.down()
        for j in range(1, 9):
            self.page.mouse.move(start + (end - start) * j / 8, y, steps=2)
        if before_release is not None:
            before_release()
        if release_outside:
            # Leave the plotting surface VERTICALLY, keeping the same x. Moving
            # out sideways would be a different test: the boundary follows the
            # pointer, so it would legitimately end up clamped at the neighbour
            # rather than at `to_index`, and the assertion would be about
            # clamping instead of about delivery. Straight down, the intended
            # index is unchanged and the only question left is whether a
            # `pointerup` the <svg> cannot see still commits the edit — which is
            # the gesture that used to lose it in silence.
            box = self.page.locator(self.CHART).bounding_box()
            below = min(box["y"] + box["height"] + 160,
                        self.page.viewport_size["height"] - 3)
            self.page.mouse.move(end, below, steps=4)
        if release:
            self.page.mouse.up()
        self.settle()

    def drag_tolerance(self, k: int, to_index: int) -> None:
        """Grab boundary `k`'s edge handle and drag it to `to_index`.

        The handle sits at the bar's edge, i.e. `tolerance_idx` steps from the
        boundary, so the press has to land there rather than on the centre.
        """
        y = self._client_y()
        centre = self.start_idx(k)
        tol = self.tolerance_idx(k)
        edge = centre + max(tol, 2)          # the right-hand handle
        self.page.mouse.move(self._client_x(edge), y)
        self.page.mouse.down()
        end = self._client_x(to_index)
        start = self._client_x(edge)
        for j in range(1, 9):
            self.page.mouse.move(start + (end - start) * j / 8, y, steps=2)
        self.page.mouse.up()
        self.settle()

    def click_boundary(self, k: int) -> None:
        """Select boundary `k` without moving it (press and release in place)."""
        y = self._client_y()
        x = self._client_x(self.start_idx(k))
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        self.page.mouse.up()
        self.settle()

    def press(self, key: str, times: int = 1) -> None:
        for _ in range(times):
            self.page.locator(self.CHART).press(key)
            self.settle(600)

    # ── what actually reached Python ─────────────────────────────────────────
    # Every one of these reads a widget Streamlit rendered from st.session_state.
    # None of them reads the SVG. A value here is a value the server has.
    def _num(self, kind: str, k: int):
        return self.page.get_by_label(f"{kind}, row {k}", exact=True)

    def start_idx(self, k: int) -> int:
        return int(self._num("start_idx", k).input_value())

    def tolerance_idx(self, k: int) -> int:
        return int(self._num("tolerance_idx", k).input_value())

    def phase_name(self, k: int) -> str:
        """A Streamlit selectbox renders as a combobox whose value is text in
        the widget, not an input value — so it is read, not typed. Scoped to the
        main area because the sidebar has selectboxes of its own, three of them
        ahead of these in document order."""
        return self.page.locator(
            '[data-testid="stMain"] [data-testid="stSelectbox"]'
        ).nth(k).inner_text().strip().splitlines()[0]

    def is_unsure(self, k: int) -> bool:
        return self.page.get_by_label(f"unsure, row {k}", exact=True).is_checked()

    def n_rows(self) -> int:
        k = 0
        while self._num("tolerance_idx", k).count():
            k += 1
        return k

    def table_state(self) -> list[tuple[int, int, bool]]:
        return [(self.start_idx(k), self.tolerance_idx(k), self.is_unsure(k))
                for k in range(self.n_rows())]

    # ── typing into the table (the canonical path) ───────────────────────────
    def set_start_idx(self, k: int, value: int) -> None:
        self._type(self._num("start_idx", k), value)

    def set_tolerance_idx(self, k: int, value: int) -> None:
        self._type(self._num("tolerance_idx", k), value)

    def _type(self, locator, value) -> None:
        locator.click()
        locator.press("ControlOrMeta+a")
        locator.type(str(value))
        locator.press("Enter")
        self.settle()

    def set_unsure(self, k: int, value: bool) -> None:
        """Click the checkbox's own <label>.

        Streamlit hides the real <input> behind a styled span, so the input has
        no clickable box of its own and Playwright refuses it as "outside of the
        viewport". The label is what a person clicks, so it is what this clicks.
        """
        box = self.page.get_by_label(f"unsure, row {k}", exact=True)
        if box.is_checked() != value:
            label = box.locator("xpath=ancestor::label[1]")
            label.scroll_into_view_if_needed()
            label.click()
            self.settle()

    # ── forcing a rerun from outside the chart ───────────────────────────────
    def poke_sidebar(self) -> None:
        """Change a sidebar widget, which reruns the whole script.

        Used two ways: to fire a rerender in the middle of a drag, and to prove
        afterwards that a value survived one — a value that is still on screen
        after the server has re-rendered the page came from the server.
        """
        slider = self.page.locator(
            '[data-testid="stSidebar"] [data-testid="stSlider"]').first
        slider.locator('[role="slider"]').first.press("ArrowRight")
