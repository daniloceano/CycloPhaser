"""Follow-up checks run AFTER the main sweep (sweep_inertia.py), to pin down
the EXACT gating condition for cases where code-reading suggested the brief's
stated condition might be imprecise.

savgol_poly: determine_periods.py:688 gates the DERIVATIVE Savgol pass on
`use_smoothing is False` alone -- NOT on `use_smoothing_twice`. Reading the
code, savgol_polynomial should therefore be used whenever use_smoothing is
truthy, REGARDLESS of use_smoothing_twice (lines 709/712/716/719 run in that
branch unconditionally on use_smoothing_twice). This predicts savgol_poly is
NOT inert under (use_smoothing="auto", use_smoothing_twice=False) -- contrary
to a naive "inert unless BOTH off" reading of the F(iii) brief's own
paraphrase. Recorded as a plain prediction before running, same discipline as
PREDICTION.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sweep_inertia as s

BASE_CONFIGS_EXTRA = {
    "sm2_off_only": dict(pv=dict(use_smoothing="auto", use_smoothing_twice=False), phase={}),
    "sm_off_only": dict(pv=dict(use_smoothing=False, use_smoothing_twice="auto"), phase={}),
}
s.BASE_CONFIGS.update(BASE_CONFIGS_EXTRA)

if __name__ == "__main__":
    for base in ("sm2_off_only", "sm_off_only"):
        print(f"PREDICTION for savgol_poly / {base}: "
             f"{'INERT' if base == 'sm_off_only' else 'NOT INERT'} "
             "(use_smoothing is False is the sole gate per determine_periods.py:688)")
        r = s.sweep_one("savgol_poly", base)
        verdict = "INERT" if r["inert"] else "not inert"
        print(f"  MEASURED: {verdict} (tracks changed: {r['n_tracks_changed']}/{len(s.TRACKS)})")
        print()
