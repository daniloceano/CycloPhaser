"""Follow-up sweep entries correcting two base-config design flaws found while
reviewing the main sweep's results (research/inert_params/sweep_inertia.py).
Both are METHODOLOGY fixes to this measurement tool, not changes to the
package, and both predictions are declared here BEFORE running, same
discipline as PREDICTION.md.

1. incipient_smooth_polyorder was swept under base configs that all leave
   incipient_smooth_window at its PHASE_DEFAULTS value (0) -- and
   `_smooth_incipient_probe` disables smoothing entirely when window<=0
   (see cyclophaser/find_stages.py, "window <= 0 disables it"). So EVERY
   polyorder sweep entry in the main run tested it against an already-inert
   window, guaranteeing INERT regardless of whether polyorder itself would
   matter with smoothing actually on. Corrected here with a base config that
   fixes incipient_smooth_window=9 (active).
   PREDICTION: NOT INERT under signal="vorticity" (window active, polyorder
   should shape the Savgol fit); INERT under signal="derivative" (window is
   irrelevant there regardless of value, per case #3 -- the derivative path
   never calls _smooth_incipient_probe on this parameter at all).

2. decay_tail_amplitude_fraction was swept with prominence filtering OFF
   (prominence_relative=None). Its own docstring (find_stages.py:514+) says
   it "compensates for an artifact of the prominence filter" -- the orphan
   peak that leaves a NaN tail after decay only tends to arise once
   prominence filtering is active. Corrected here with a base config that
   also turns prominence filtering on.
   PREDICTION: NOT INERT once prominence filtering creates the orphan-peak
   precondition the feature exists to compensate for.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sweep_inertia as s

s.BASE_CONFIGS.update({
    "plateau_single_vorticity_smoothed": dict(pv={}, phase=dict(
        incipient_method="plateau", incipient_plateau_crossing="single",
        incipient_plateau_signal="vorticity", incipient_smooth_window=9)),
    "plateau_single_derivative_smoothed": dict(pv={}, phase=dict(
        incipient_method="plateau", incipient_plateau_crossing="single",
        incipient_plateau_signal="derivative", incipient_smooth_window=9)),
    "decay_tail_on_with_prominence": dict(pv={}, phase=dict(
        decay_tail_amplitude_fraction=0.05, prominence_relative=0.10)),
})

CHECKS = [
    ("incipient_smooth_polyorder", "plateau_single_vorticity_smoothed", "NOT INERT"),
    ("incipient_smooth_polyorder", "plateau_single_derivative_smoothed", "INERT"),
    ("decay_tail_amplitude_fraction", "decay_tail_on_with_prominence", "NOT INERT"),
]

if __name__ == "__main__":
    for param, base, prediction in CHECKS:
        print(f"PREDICTION for {param} / {base}: {prediction}")
        r = s.sweep_one(param, base)
        if r["inert"] is None:
            verdict = "UNEVALUABLE"
        else:
            verdict = "INERT" if r["inert"] else "NOT INERT"
        print(f"  MEASURED: {verdict} (tracks changed: {r['n_tracks_changed']}/{len(s.TRACKS)}, "
             f"unevaluable: {r['n_unevaluable_tracks']}/{len(s.TRACKS)})")
        print()
