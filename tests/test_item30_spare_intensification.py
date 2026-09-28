"""Item 30 part 3 — `incipient_plateau_spare_intensification` (opt-in, default False).

The plateau method writes `incipient` over [0, boundary). With the option on, an
intensification that lies WHOLLY before the boundary stops it at its start.

Covered here:

* the rule itself on minimal synthetic maps, with the POSITIVE CONTROL the
  premise needs: it changes the output when E ends before the boundary, and
  leaves it untouched when E runs past it;
* default False reaches every layer: `get_periods` / `determine_periods`
  signatures, the `args_periods` handed to the stage, and an absent key;
* equivalence, on the 5 adjudicated TRAIN cases, with the counterfactual of
  1a3ad76 (item 30, `diagnostics/item30/figs_cf.py`).
"""

import inspect
import sys
from pathlib import Path

import pandas as pd
import pytest

import cyclophaser.find_stages as fs
from cyclophaser.determine_periods import determine_periods, get_periods

REPO_ROOT = Path(__file__).resolve().parent.parent
KEY = "incipient_plateau_spare_intensification"


# ── the helper on bare maps ─────────────────────────────────────────────────

def _m(*runs):
    return pd.Series([ph for ph, n in runs for _ in range(n)])


@pytest.mark.parametrize("periods, boundary, want", [
    # E = (2, 4) ends before 9 -> pulled back to 2
    (_m(("decay", 2), ("intensification", 3), ("mature", 2), ("decay", 5)), 9, 2),
    # E starts at 0 and ends before the boundary -> 0, no incipient at all
    (_m(("intensification", 3), ("mature", 2), ("decay", 5)), 8, 0),
    # numbered intensifications count as intensification
    (_m(("decay", 1), ("intensification 2", 2), ("decay", 7)), 6, 1),
    # E runs PAST the boundary -> unchanged
    (_m(("decay", 2), ("intensification", 6), ("decay", 4)), 5, 5),
    # E ends exactly AT boundary - 1 -> still wholly before, pulled back
    (_m(("decay", 2), ("intensification", 3), ("decay", 5)), 5, 2),
    # E ends AT the boundary index -> not wholly before, unchanged
    (_m(("decay", 2), ("intensification", 4), ("decay", 4)), 5, 5),
    # no intensification before the boundary -> unchanged
    (_m(("decay", 6), ("intensification", 3), ("decay", 3)), 5, 5),
    # no intensification at all -> unchanged
    (_m(("decay", 12)), 7, 7),
    # boundary 0 -> nothing to spare
    (_m(("intensification", 4), ("decay", 4)), 0, 0),
])
def test_the_helper_moves_the_boundary_only_when_e_ends_before_it(periods, boundary, want):
    assert fs._spare_enclosed_intensification(periods, boundary) == want


# ── find_incipient_period end to end, the plateau fixed by stubs ────────────

def _run(monkeypatch, periods, boundary, **extra):
    monkeypatch.setattr(fs, "_incipient_plateau_rel", lambda *a, **k: None)
    monkeypatch.setattr(fs, "_incipient_plateau_boundary", lambda *a, **k: boundary)
    df = pd.DataFrame({"periods": periods.astype(object)})
    out = fs.find_incipient_period(df, threshold_incipient_length=0.4,
                                   incipient_method="plateau", **extra)
    return list(out["periods"])


def test_on_the_rule_spares_an_enclosed_intensification(monkeypatch):
    p = _m(("decay", 2), ("intensification", 3), ("mature", 2), ("decay", 5))
    off = _run(monkeypatch, p, 9)
    on = _run(monkeypatch, p, 9, **{KEY: True})
    assert off == ["incipient"] * 9 + ["decay"] * 3          # H: all erased
    assert on == ["incipient"] * 2 + list(p[2:])             # spared from its start
    assert on != off                                          # the control bites


def test_on_the_rule_changes_nothing_when_e_runs_past_the_boundary(monkeypatch):
    p = _m(("decay", 2), ("intensification", 6), ("decay", 4))
    assert _run(monkeypatch, p, 5, **{KEY: True}) == _run(monkeypatch, p, 5)


def test_e_starting_at_zero_leaves_no_incipient(monkeypatch):
    p = _m(("intensification", 3), ("mature", 2), ("decay", 5))
    assert _run(monkeypatch, p, 8, **{KEY: True}) == list(p)


def test_absent_and_false_are_the_same(monkeypatch):
    p = _m(("decay", 2), ("intensification", 3), ("mature", 2), ("decay", 5))
    assert _run(monkeypatch, p, 9) == _run(monkeypatch, p, 9, **{KEY: False})


def test_the_geometric_method_never_reads_the_key(monkeypatch):
    seen = []
    monkeypatch.setattr(fs, "_spare_enclosed_intensification",
                        lambda *a: seen.append(a) or a[1])
    df = pd.DataFrame({"periods": ["decay"] * 5, "dz_peaks_valleys": [None] * 5})
    fs.find_incipient_period(df, threshold_incipient_length=0.4,
                             incipient_method="geometric", **{KEY: True})
    assert seen == []


# ── default True in every public signature (item 31; False up to 2.0.0), ─────
#    forwarded as given ──────────────────────────────────────────────────────

@pytest.mark.parametrize("fn", [get_periods, determine_periods])
def test_the_public_default_is_true(fn):
    assert inspect.signature(fn).parameters[KEY].default is True


def test_get_periods_forwards_the_key_to_the_stages(monkeypatch):
    # `import cyclophaser.determine_periods` yields the FUNCTION of that name
    # (the package re-exports it), so the module is taken from sys.modules.
    dp = sys.modules["cyclophaser.determine_periods"]
    got = {}
    orig = dp.find_incipient_period

    def spy(df, **a):
        got.update(a)
        return orig(df, **a)

    monkeypatch.setattr(dp, "find_incipient_period", spy)
    from cyclophaser import example_file
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    vort = dp.process_vorticity(pd.DataFrame({"zeta": track["min_max_zeta_850"].values}))
    get_periods(vort)
    assert got[KEY] is True
    get_periods(vort, **{KEY: False})
    assert got[KEY] is False


# ── the 5 adjudicated TRAIN cases: params-track == the counterfactual ──────────

def test_params_track_reproduces_the_counterfactual_in_the_five():
    pytest.importorskip("yaml")
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels" / "diagnostics" / "item30"))
    import figs_cf
    import item30_core as core

    batch = core.lc.load_batch_series()
    # params-14 left the repo in item 31. It was params-track minus this one key
    # (asserted in item 31, stage 0), so it is params-track with the key OFF.
    cfg15 = core.load_config("params-track")
    cfg14 = (cfg15[0], {**cfg15[1], KEY: False})
    for sid in ("20120297", "19940445", "19810854", "19860380", "19870927"):
        r14 = core.run_series(batch[sid], *cfg14)
        cand = figs_cf.sep.candidates(r14, pd.Series(r14["z"]))
        cf, from_s5 = figs_cf.counterfactual(r14, cand)
        assert from_s5, sid
        final15 = core.run_series(batch[sid], *cfg15)["final"]
        assert final15 == cf, sid
        assert final15 != r14["final"], sid        # the control: it did change


# ── the app: a YAML without the key imports as OFF ──────────────────────────

def _app_yaml_loader():
    """app.py's real `_load_yaml_config`, bound to a stub `st.session_state`.

    app.py runs Streamlit at import, so — as tests/test_sidebar_coverage.py does
    for its declarations — the stretch from `_DEFAULTS` to the end of
    `_load_yaml_config` (declarations and function definitions only) is executed
    in a namespace of its own."""
    import datetime as _dt
    import types

    import yaml
    src = (REPO_ROOT / "tools" / "calibration_app" / "app.py").read_text()
    start = src.index("_DEFAULTS: dict = {")
    fn = src.index("def _load_yaml_config(")
    end = src.index("\ndef ", fn + 1)
    st = types.SimpleNamespace(session_state={})
    ns = {"st": st, "yaml": yaml, "Path": Path, "datetime": _dt.datetime,
          "timezone": _dt.timezone, "__name__": "_app_yaml_loader"}
    sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))   # config_defaults
    exec(compile(src[start:end], "app.py", "exec"), ns)
    return ns["_load_yaml_config"], st.session_state


def _config_bytes(name):
    return (REPO_ROOT / "research" / "labels" / "configs"
            / f"cyclophaser_{name}.yaml").read_bytes()


def _without_key_bytes():
    """params-track's text with the key's line removed — a real config without the
    key (params-14 was exactly that, and left the repo in item 31)."""
    lines = _config_bytes("params-track").decode().splitlines(keepends=True)
    kept = [ln for ln in lines if not ln.strip().startswith(f"{KEY}:")]
    assert len(kept) == len(lines) - 1
    return "".join(kept).encode()


def test_importing_a_config_without_the_key_turns_the_rule_off_even_if_it_was_on():
    load, state = _app_yaml_loader()
    state[KEY] = True                       # the session had it ON
    res = load(_without_key_bytes())
    assert res["error"] is None
    assert state[KEY] is False
    # Item 31, decision (a): absence is FILLED with the 2.0.0 default (False)
    # and LISTED — no longer silently treated as "not missing".
    assert (f"phase_params.{KEY}", False) in res["filled"]
    assert f"phase_params.{KEY}" in res["missing"]


def test_importing_params_track_turns_the_rule_on():
    """POSITIVE CONTROL for the test above: the same loader does set True when
    the file says so, so the False above is the absence rule, not a loader that
    never writes the key."""
    load, state = _app_yaml_loader()
    state[KEY] = False
    res = load(_config_bytes("params-track"))
    assert res["error"] is None and state[KEY] is True
