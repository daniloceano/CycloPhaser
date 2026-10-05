"""The sidebar must carry every public parameter — checked, not eyeballed.

The sidebar was reorganised into the detector's execution order (item 5,
Entrega 3). Moving ~600 lines of widget code around is exactly the operation
that loses a control or renders one twice, and neither is visible by scrolling
past it: a lost widget looks like a tidier sidebar, and a duplicated key looks
like nothing at all until two controls disagree.

So the layout is verified mechanically, from the package's own signature:

  * **nothing lost** — every parameter of `process_vorticity` + `get_periods`
    appears in `app._PARAM_WIDGET_KEYS`, and every key it names actually renders;
  * **nothing duplicated** — no widget key renders twice, and no key serves two
    different parameters except the extrema enable/mode pair, which is declared
    as shared because the two prominence parameters are mutually exclusive in
    the package.

Conditional controls are the reason two app states are needed rather than one:
several widgets are deliberately *hidden* (not merely disabled) when the mode
that reads them is not selected — `mature_amplitude_fraction` under
`mature_method='derivative'`, `threshold_incipient_length` under
`incipient_method='plateau'`, and so on. The union of the two states below
activates every branch; the assertions are per-state, so a widget is only
required where it is supposed to exist.
"""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from cyclophaser.determine_periods import get_periods, process_vorticity  # noqa: E402


def _app_module():
    """Import app.py for its declarations only (no Streamlit run)."""
    spec = importlib.util.spec_from_file_location("_calib_app_decls", APP)
    mod = importlib.util.module_from_spec(spec)
    # app.py executes Streamlit calls at import; running it outside a script run
    # is what AppTest is for. The declarations we need are plain dicts defined
    # before any of that matters, so read them out of the source instead.
    src = APP.read_text()
    ns: dict = {}
    start = src.index("_PARAM_WIDGET_KEYS: dict[str, tuple[str, ...]] = {")
    end = src.index("_NON_PARAMETER_ARGS = frozenset({")
    end = src.index("})", end) + 2
    exec(compile(src[start:end], str(APP), "exec"), {"frozenset": frozenset}, ns)
    return ns


DECLS = _app_module()
PARAM_WIDGET_KEYS = DECLS["_PARAM_WIDGET_KEYS"]
SHARED = DECLS["_SHARED_SELECTOR_KEYS"]
NON_PARAM = DECLS["_NON_PARAMETER_ARGS"]


def _public_parameters() -> set[str]:
    out = set()
    for fn in (process_vorticity, get_periods):
        for name in inspect.signature(fn).parameters:
            if name not in NON_PARAM:
                out.add(name)
    return out


def _rendered_keys(at) -> list[str]:
    widgets = (list(at.slider) + list(at.selectbox) + list(at.radio)
               + list(at.checkbox) + list(at.number_input)
               + list(at.select_slider) + list(at.text_area)
               + list(at.multiselect))
    return [w.key for w in widgets if w.key]


def _base_app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _set(at, key, value):
    for group in (at.slider, at.selectbox, at.radio, at.checkbox,
                  at.number_input, at.select_slider):
        for w in group:
            if w.key == key:
                w.set_value(value)
                return True
    return False


def _state_derivative_geometric() -> AppTest:
    """The 'derivative' + 'geometric' + relative-prominence branches.

    The plateau sub-options are *disabled* under `incipient_method='geometric'`
    and are deliberately not touched here — AppTest refuses to drive a disabled
    widget, exactly as a browser user could not. They are covered by the other
    state, which selects the method that owns them.
    """
    at = _base_app()
    _set(at, "sm_mode", "manual")
    _set(at, "mature_method", "derivative")
    _set(at, "incipient_method", "geometric")
    _set(at, "extrema_prominence_enabled", True)
    _set(at, "decay_tail_enabled", True)
    at.run()
    _set(at, "sm2_mode", "manual")
    _set(at, "extrema_prominence_mode", "relative")
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _state_amplitude_plateau() -> AppTest:
    """The 'amplitude' + 'plateau' + absolute-prominence branches.

    `incipient_plateau_k` renders only under crossing='sustained' and the two
    probe-smoothing widgets only under signal='vorticity'; both radios are
    themselves disabled unless the method is 'plateau', so the method has to be
    switched first and the script re-run before either can be set.
    """
    at = _base_app()
    _set(at, "mature_method", "amplitude")
    _set(at, "incipient_method", "plateau")
    _set(at, "extrema_prominence_enabled", True)
    at.run()
    _set(at, "extrema_prominence_mode", "absolute")
    _set(at, "incipient_plateau_crossing", "sustained")
    _set(at, "incipient_plateau_signal", "vorticity")
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


# ══════════════════════════════════════════════════════════════════════════
# nothing lost
# ══════════════════════════════════════════════════════════════════════════

def test_every_public_parameter_is_declared():
    """The declaration covers the signature exactly — in both directions."""
    params = _public_parameters()
    declared = set(PARAM_WIDGET_KEYS)
    assert declared == params, (
        f"undeclared parameters: {sorted(params - declared)}; "
        f"declared but not in the signature: {sorted(declared - params)}")


def test_every_declared_key_renders_somewhere():
    """Each declared widget key exists in at least one of the two app states.

    A key that renders in neither is a control that was lost in the reorder —
    the declaration would still name it and nothing else would complain.
    """
    seen = set(_rendered_keys(_state_derivative_geometric()))
    seen |= set(_rendered_keys(_state_amplitude_plateau()))
    declared = {k for keys in PARAM_WIDGET_KEYS.values() for k in keys}
    assert declared <= seen, f"declared but never rendered: {sorted(declared - seen)}"


@pytest.mark.parametrize("param", sorted(PARAM_WIDGET_KEYS))
def test_parameter_has_a_live_control(param):
    """Every parameter is reachable: at least one of its keys renders."""
    seen = set(_rendered_keys(_state_derivative_geometric()))
    seen |= set(_rendered_keys(_state_amplitude_plateau()))
    keys = set(PARAM_WIDGET_KEYS[param])
    assert keys & seen, f"{param} has no rendered control (declared {sorted(keys)})"


# ══════════════════════════════════════════════════════════════════════════
# nothing duplicated
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("state", ["derivative_geometric", "amplitude_plateau"])
def test_no_widget_key_renders_twice(state):
    at = (_state_derivative_geometric() if state == "derivative_geometric"
          else _state_amplitude_plateau())
    keys = _rendered_keys(at)
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    assert not dupes, f"widget key(s) rendered more than once: {dupes}"


def test_only_the_declared_selector_keys_are_shared_between_parameters():
    """A key serving two parameters is a design decision, not an accident."""
    owners: dict[str, list[str]] = {}
    for param, keys in PARAM_WIDGET_KEYS.items():
        for k in keys:
            owners.setdefault(k, []).append(param)
    shared = {k: v for k, v in owners.items() if len(v) > 1}
    assert set(shared) == set(SHARED), (
        f"unexpected shared keys: { {k: v for k, v in shared.items() if k not in SHARED} }; "
        f"declared shared but not actually shared: {sorted(set(SHARED) - set(shared))}")


# ══════════════════════════════════════════════════════════════════════════
# the group numbering promises the execution order — it must not lie
# ══════════════════════════════════════════════════════════════════════════

def _numbered_groups(at):
    """[(header_number, header_title, step_number_cited_in_its_caption), ...].

    The sidebar is read top to bottom, so a group's caption is the first
    "Step N" caption that follows its header.
    """
    import re
    items = []
    for el in at.sidebar:
        t = getattr(el, "value", None)
        if not isinstance(t, str):
            continue
        h = re.match(r"^(\d+) · (.+)$", t.strip())
        if h:
            items.append(["header", int(h.group(1)), h.group(2)])
            continue
        c = re.match(r"^Step (\d+) — ", t.strip())
        if c:
            items.append(["caption", int(c.group(1)), t.strip()])

    out, pending = [], None
    for kind, num, text in items:
        if kind == "header":
            pending = (num, text)
        elif pending is not None:
            out.append((pending[0], pending[1], num))
            pending = None
    return out


def test_every_group_header_number_matches_the_step_its_caption_cites():
    """A header that says 8 above a caption that says "Step 9" makes the
    numbering worthless — it is supposed to BE the execution order.

    Step 8 (`post_process_periods`) takes no parameter and so has no group; the
    numbering skips 8 rather than closing the gap, which is why this asserts
    agreement rather than a contiguous 1..N sequence.
    """
    at = _base_app()
    groups = _numbered_groups(at)
    assert groups, "no numbered sidebar groups were found"
    wrong = [(h, title, step) for h, title, step in groups if h != step]
    assert not wrong, (
        "group header number disagrees with the step cited in its caption: "
        + "; ".join(f"'{h} · {title}' cites Step {step}" for h, title, step in wrong))


def test_the_numbering_covers_every_parameterised_step_and_skips_only_step_8():
    at = _base_app()
    numbers = sorted(h for h, _, _ in _numbered_groups(at))
    assert numbers == [1, 2, 3, 4, 5, 6, 7, 9], (
        f"unexpected group numbering {numbers}; step 8 (post_process_periods) "
        "takes no parameter and is the only one that may be absent")
