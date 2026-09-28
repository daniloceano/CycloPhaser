"""Item 31, stage 2c — the app sidebar's start-up values: declared, then obtained.

Danilo's decision (2026-09-28, DESIGN §8.2): the sidebar opens with the PACKAGE
defaults and "Reset to defaults" returns to them; one source, the signature.

`--declare` (before the app is changed) writes `sidebar_table_2c.md` with, per
sidebar widget key: the value `app._DEFAULTS` holds TODAY (read from app.py by
`ast`, not by running Streamlit) and the value the DECLARED RULE derives from
`inspect.signature(process_vorticity / get_periods)`:

* scalar parameter → its signature default, in the widget's own type
  (int widgets: cutoff_low, cutoff_high, replace_endpoints, savgol_poly,
  incipient_plateau_k, incipient_smooth_window, incipient_smooth_polyorder;
  use_filter: 'auto'/True → True, False → False);
* use_smoothing / use_smoothing_twice: 'auto' → mode 'auto'; False → 'off';
  an int n → 'manual' with value n (the value widget keeps the app's fallback
  otherwise);
* prominence group: enabled iff prominence_relative or prominence is not None;
  mode 'relative' if prominence_relative is not None, else 'absolute' if
  prominence is not None, else 'relative'; each value widget takes its
  parameter's default when that is not None, the app's fallback otherwise;
* decay tail: enabled iff the default is not None; value = the default, or the
  app's fallback.

Keys that are not package parameters (view state, fallbacks of value widgets
whose check is OFF) are listed and marked "app-own, unchanged".

`--obtained` (after the change) starts the real app with AppTest and reads every
widget key's value from session_state, adding the "obtained" column.

Run: python -P research/labels/diagnostics/item31/sidebar_table_2c.py --declare | --obtained
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

APP = core.REPO / "tools" / "calibration_app" / "app.py"
dp = core.dp
INT_KEYS = {"cutoff_low", "cutoff_high", "replace_endpoints", "savgol_poly",
            "incipient_plateau_k", "incipient_smooth_window", "incipient_smooth_polyorder"}
SCALAR = {  # widget key -> package parameter
    "use_filter": "use_filter", "cutoff_low": "cutoff_low", "cutoff_high": "cutoff_high",
    "replace_endpoints": "replace_endpoints_with_lowpass", "savgol_poly": "savgol_polynomial",
    "boundary_padding": "boundary_padding",
    "thr_int_len": "threshold_intensification_length",
    "thr_int_gap": "threshold_intensification_gap",
    "intensification_min_depth": "intensification_min_depth",
    "thr_mat_dist": "threshold_mature_distance", "thr_mat_len": "threshold_mature_length",
    "thr_dec_len": "threshold_decay_length", "thr_dec_gap": "threshold_decay_gap",
    "thr_inc_len": "threshold_incipient_length", "length_scale": "length_scale",
    "mature_method": "mature_method", "mature_amplitude_fraction": "mature_amplitude_fraction",
    "mature_min_depth": "mature_min_depth", "reclassify_index0": "reclassify_index0",
    "incipient_method": "incipient_method", "incipient_plateau_tau": "incipient_plateau_tau",
    "incipient_plateau_signal": "incipient_plateau_signal",
    "incipient_plateau_crossing": "incipient_plateau_crossing",
    "incipient_plateau_k": "incipient_plateau_k",
    "incipient_smooth_window": "incipient_smooth_window",
    "incipient_smooth_polyorder": "incipient_smooth_polyorder",
    "incipient_plateau_spare_intensification": "incipient_plateau_spare_intensification",
}
GROUP_KEYS = ("sm_mode", "sm_val", "sm2_mode", "sm2_val",
              "extrema_prominence_enabled", "extrema_prominence_mode",
              "extrema_prominence_rel_val", "extrema_prominence_val",
              "decay_tail_enabled", "decay_tail_fraction_val")


def signature_defaults() -> dict:
    out = {}
    for fn in (dp.process_vorticity, dp.get_periods):
        for k, p in inspect.signature(fn).parameters.items():
            if p.default is not inspect.Parameter.empty:
                out[k] = p.default
    return out


def today_defaults() -> dict:
    """app._DEFAULTS as a literal, read from app.py (the pre-2c dict)."""
    tree = ast.parse(APP.read_text())
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "_DEFAULTS":
            return ast.literal_eval(node.value)
    raise AssertionError("no `_DEFAULTS: dict = {...}` literal in app.py")


def declared(sig: dict, fallback: dict) -> dict:
    """The declared rule (module docstring), from the signature alone."""
    out = {}
    for w, p in SCALAR.items():
        v = sig[p]
        if w == "use_filter":
            v = v in ("auto", True) or (isinstance(v, int) and not isinstance(v, bool) and v > 0)
        elif w in INT_KEYS:
            v = int(v)
        out[w] = v
    for mode_k, val_k, p in (("sm_mode", "sm_val", "use_smoothing"),
                             ("sm2_mode", "sm2_val", "use_smoothing_twice")):
        v = sig[p]
        if v == "auto":
            out[mode_k], out[val_k] = "auto", fallback[val_k]
        elif v is False:
            out[mode_k], out[val_k] = "off", fallback[val_k]
        else:
            out[mode_k], out[val_k] = "manual", int(v)
    pr, pa = sig["prominence_relative"], sig["prominence"]
    out["extrema_prominence_enabled"] = pr is not None or pa is not None
    out["extrema_prominence_mode"] = ("relative" if pr is not None
                                      else "absolute" if pa is not None else "relative")
    out["extrema_prominence_rel_val"] = pr if pr is not None else fallback["extrema_prominence_rel_val"]
    out["extrema_prominence_val"] = pa if pa is not None else fallback["extrema_prominence_val"]
    dt = sig["decay_tail_amplitude_fraction"]
    out["decay_tail_enabled"] = dt is not None
    out["decay_tail_fraction_val"] = dt if dt is not None else fallback["decay_tail_fraction_val"]
    return out


def obtained() -> dict:
    sys.path.insert(0, str(APP.parent))
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return {k: at.session_state[k] for k in list(SCALAR) + list(GROUP_KEYS)
            if k in at.session_state}


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--declare", action="store_true")
    g.add_argument("--obtained", action="store_true")
    a = ap.parse_args()
    core.assert_environment()
    js = HERE / "sidebar_table_2c.json"
    if a.declare:
        today = today_defaults()
        sig = signature_defaults()
        new = declared(sig, today)
        rows = [{"key": k, "parameter": SCALAR.get(k, "(group)"), "today": today.get(k),
                 "declared": new[k]} for k in list(SCALAR) + list(GROUP_KEYS)]
        own = {k: v for k, v in today.items() if k not in new}
        js.write_text(json.dumps({"rows": rows, "app_own": own}, indent=2, default=repr))
    else:
        doc = json.loads(js.read_text())
        got = obtained()
        for r in doc["rows"]:
            r["obtained"] = got.get(r["key"], "(not rendered at start-up)")
        js.write_text(json.dumps(doc, indent=2, default=repr))
        rows, own = doc["rows"], doc["app_own"]
    md = ["| widget key | package parameter | today (2.0.0) | declared (signature) | "
          + ("obtained | match |" if a.obtained else "changes? |"),
          "|---|---|---|---|---|" + ("---|" if a.obtained else "")]
    for r in rows:
        tail = (f"`{r['obtained']!r}` | {'yes' if r['obtained'] == r['declared'] else '**NO**'} |"
                if a.obtained else f"{'**yes**' if r['today'] != r['declared'] else 'no'} |")
        md.append(f"| `{r['key']}` | `{r['parameter']}` | `{r['today']!r}` | `{r['declared']!r}` | {tail}")
    md += ["", "App-own keys, not package parameters (unchanged): "
           + ", ".join(f"`{k}`" for k in own)]
    (HERE / "sidebar_table_2c.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
