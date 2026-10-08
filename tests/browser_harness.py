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
`streamlit run tools/calibration_app/app.py` on a free port with the developer
key on, opens Chromium at its Manual labelling page (a page of its own since the
app redesign's I1; it was the "Label" display mode before), and operates the
page with real pointer events
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

`LabelPage` never presses Save. `research/labels/manual_labels.yaml` is the
artefact the whole front exists to produce, and a test suite that can write to it
is a test suite that can corrupt it. Everything asserted through `LabelPage` is
read from the phase table, which is Streamlit rendering the same
`st.session_state` list that a save would serialise. The one test that does
save (tests/test_app_pages_browser.py) starts its server with `labels_path=` a
temporary COPY of the file: `AppServer` then patches `labels_core.LABELS_PATH`
inside the server process before Streamlit starts, so every read and write of
the app goes to the copy.
"""

from __future__ import annotations

import os
import re
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

# Run instead of `python -m streamlit` when a labels path is given: it points
# labels_core at that file inside the server process, then hands over to
# Streamlit's own CLI. label_tab imports the SAME module object from
# sys.modules, and labels_core reads LABELS_PATH at call time.
_LAUNCH_WITH_LABELS_PATH = """
import sys
from pathlib import Path
labels_path, labels_pkg = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, labels_pkg)
import labels_core
labels_core.LABELS_PATH = labels_path
from streamlit.web import cli
sys.argv = ["streamlit", "run", *sys.argv[3:]]
sys.exit(cli.main())
"""


# ── controls whose DOM differs between supported Streamlit versions ──────────
# Measured in Chromium (research/app_redesign/i1/diag_chromium/): on streamlit
# 1.56.0 a selectbox is a combobox whose accessible name is "Selected <value>.
# <label>" and whose <input> value is empty, and a slider is a
# <div role="slider"> carrying aria-valuenow; on 1.63.0 the combobox is named by
# its label alone and holds the value, and the slider is an <input
# type="range">. These helpers find and read both.

def selectbox(page, label: str):
    """The selectbox labelled `label`, in either naming."""
    return page.locator(f'[role="combobox"][aria-label="{label}"], '
                        f'[role="combobox"][aria-label$=". {label}"]')


def selectbox_value(page, label: str) -> str:
    """The value a selectbox shows, from its input or from its accessible name."""
    box = selectbox(page, label).first
    value = box.input_value()
    if value:
        return value
    m = re.match(r"^Selected (.*)\. " + re.escape(label) + r"$",
                 box.get_attribute("aria-label") or "", re.S)
    return m.group(1) if m else ""


SLIDER_HANDLE = ('[data-testid="stSlider"] input[type="range"], '
                 '[data-testid="stSlider"] [role="slider"]')


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class AppServer:
    """`streamlit run` on a free port, torn down on exit."""

    def __init__(self, log_path: Path, developer: bool = True,
                 labels_path: Path | None = None):
        self.port = free_port()
        self.log_path = Path(log_path)
        self.developer = developer
        self.labels_path = labels_path
        self._log = None
        self._proc = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    def start(self) -> "AppServer":
        self._log = open(self.log_path, "w")
        args = [str(APP),
                "--server.port", str(self.port),
                "--server.headless", "true",
                "--server.fileWatcherType", "none",
                "--browser.gatherUsageStats", "false"]
        if self.labels_path is None:
            cmd = [sys.executable, "-m", "streamlit", "run", *args]
        else:
            cmd = [sys.executable, "-c", _LAUNCH_WITH_LABELS_PATH,
                   str(self.labels_path), str(REPO_ROOT / "research" / "labels"),
                   *args]
        env = dict(os.environ, STREAMLIT_BROWSER_GATHER_USAGE_STATS="false")
        env.pop("CYCLOPHASER_APP_DEV", None)
        if self.developer:
            env["CYCLOPHASER_APP_DEV"] = "1"
        self._proc = subprocess.Popen(
            cmd, stdout=self._log, stderr=subprocess.STDOUT, text=True,
            cwd=str(REPO_ROOT), env=env,
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
    """The Manual labelling page of the running app, driven through a real browser.

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
    def open(self, url: str, min_steps: int | None = 110) -> "LabelPage":
        # The way a user gets there: the app's root (Calibrate), then the menu
        # entry, which exists only with the developer key (AppServer sets it by
        # default). Loading `url + "label"` directly also works, but Streamlit's
        # frontend first probes `/label/_stcore/health` and `/host-config` and
        # logs two 404s to the console before finding the server at the root,
        # which `test_no_javascript_errors_on_the_page` would rightly report.
        self.page.goto(url, wait_until="load")
        # Calibrate's sidebar (since I2 its main area is empty until data is loaded)
        self.page.wait_for_selector("text=1 · Data", timeout=RENDER_TIMEOUT)
        self.page.locator('[data-testid="stSidebarNav"]').get_by_text(
            "Manual labelling", exact=True).click()
        self.page.wait_for_selector("text=Manual labelling — the",
                                    timeout=RENDER_TIMEOUT)
        self.settle()
        if min_steps:
            self.step_to_long_unlocked_case(min_steps)
        return self

    def step_to_long_unlocked_case(self, min_steps: int, max_steps: int = 90) -> None:
        """Next ▸ until the case is at least `min_steps` long, not locked and
        not a frozen synthetic.

        The page opens on the first UNLABELLED case of the queue. Since item 30
        the queue ends with the swell batches, so that case is now a 30-step
        validation case — and the fixtures here type positions up to 100. Every
        fixture move then left a number input pending ("Press Enter to apply")
        and the suite failed wholesale, on develop too (d339c7d: 16 failed, 8
        errors). The suite is about the chart and the table, not about which
        case comes first, so it steps to one that can hold its positions.
        Next ▸ never saves.
        """
        for _ in range(max_steps):
            status = self.page.locator('[data-testid="stCaptionContainer"]').filter(
                has_text="blind").first.inner_text()
            if (self._n_steps() >= min_steps and "🔒" not in status
                    and "❄️" not in status):
                return
            self.page.get_by_role("button", name="Next ▸").click()
            self.settle()
        raise AssertionError(f"no unlocked case of >= {min_steps} steps in {max_steps}")

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
        """Read through `selectbox_value`, which handles both supported
        Streamlit renderings (see the comment above it). On the react-aria one
        the chosen value lives in its `<input value="...">` attribute, not as
        visible text content. `.inner_text()` reads rendered text nodes and returns '' for
        this widget regardless of which one — confirmed against unmodified
        develop-v2.1 too, so this is a Streamlit-version rendering change,
        predating and unrelated to anything on this front. Read via the
        accessible label instead of position: `get_by_label` matches this
        widget's own `aria-label` directly, so it needs no index arithmetic
        and does not care how many OTHER selectboxes (the case-navigation
        dropdown included) sit before it on the page.
        """
        return selectbox_value(self.page, f"phase, row {k}")

    def is_unsure(self, k: int) -> bool:
        return self.page.get_by_label(f"unsure, row {k}", exact=True).is_checked()

    def is_end_unsure(self, k: int) -> bool:
        return self.page.get_by_label(f"end unsure, row {k}", exact=True).is_checked()

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
        self._click_labelled_checkbox(f"unsure, row {k}", value)

    def set_end_unsure(self, k: int, value: bool) -> None:
        self._click_labelled_checkbox(f"end unsure, row {k}", value)

    def _click_labelled_checkbox(self, label: str, value: bool) -> None:
        box = self.page.get_by_label(label, exact=True)
        if box.is_checked() != value:
            lbl = box.locator("xpath=ancestor::label[1]")
            lbl.scroll_into_view_if_needed()
            lbl.click()
            self.settle()

    # ── overlays (available at any time; revealing one unblinds the case) ────
    def enable_overlay(self, layer_label_substring: str) -> None:
        """Turn the master overlay switch on, then one layer by its visible
        (partial) label text, e.g. 'vorticity_smoothed2'."""
        master = self.page.get_by_role("checkbox", name="Show filtered/smoothed overlays",
                                        exact=False)
        if not master.is_checked():
            master.locator("xpath=ancestor::label[1]").click()
            self.settle()
        layer = self.page.get_by_label(layer_label_substring, exact=False)
        if not layer.is_checked():
            layer.locator("xpath=ancestor::label[1]").click()
            self.settle()

    # ── layout ───────────────────────────────────────────────────────────────
    def chart_box(self) -> dict:
        return self.page.locator(self.CHART).bounding_box()

    def working_area(self) -> tuple[float, float]:
        """(top, bottom) of the block you actually label in, in viewport pixels.

        Top of the curve to the bottom of the button row. Everything between is
        needed at once: you cannot judge a shape you cannot see while typing the
        number that describes it.
        """
        chart = self.chart_box()
        buttons = self.page.get_by_role("button", name="Next ▸").bounding_box()
        return chart["y"], buttons["y"] + buttons["height"]

    def clipped_chart_labels(self) -> list[str]:
        """Any boundary tag or band label pushed off the top of the window."""
        return self.page.locator(self.CHART).evaluate(
            """(svg) => [...svg.querySelectorAll('text')]
                 .filter((t) => t.textContent &&
                                t.getBoundingClientRect().top < 0)
                 .map((t) => t.textContent)""")

    # ── forcing a rerun from outside the chart ───────────────────────────────
    _poke_up = True

    def poke_sidebar(self) -> None:
        """Change a widget outside the chart, which reruns the whole script.

        Used two ways: to fire a rerender in the middle of a drag, and to prove
        afterwards that a value survived one — a value that is still on screen
        after the server has re-rendered the page came from the server.

        Name kept from when this poked a Calibrate sidebar slider: the Manual
        labelling page has no parameter sidebar since I1 of the app redesign.
        It now steps the page's own "Default ± steps for a new boundary" input,
        up and down alternately, so repeated pokes never drift; that value is
        only the starting margin of a boundary ADDED later, so no existing
        phase depends on it. By KEYBOARD only (focus, then the arrow key): one
        caller pokes in the middle of a drag, with the mouse button held down,
        and a click would release that drag.
        """
        box = self.page.get_by_label("Default ± steps for a new boundary",
                                     exact=True)
        key = "ArrowUp" if self._poke_up else "ArrowDown"
        self._poke_up = not self._poke_up
        box.press(key)
