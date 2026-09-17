import sys, warnings, yaml, inspect
from pathlib import Path
import pandas as pd
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO/"research/labels")); sys.path.insert(0, str(REPO))
from labels_core import load_real_series, normalize_phase
from cyclophaser.determine_periods import get_periods, process_vorticity

PV_KEYS = ("use_filter","replace_endpoints_with_lowpass","use_smoothing",
           "use_smoothing_twice","savgol_polynomial","cutoff_low","cutoff_high","boundary_padding")
doc = yaml.safe_load((REPO/"research/labels/configs/cyclophaser_params-9.yaml").read_text())
gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
PV = {k:v for k,v in doc["filter_params"].items() if k in PV_KEYS}
GP = {k:v for k,v in doc["phase_params"].items() if k in gp_ok}

# ---------------------------------------------------------------------------
# HISTORICAL — does not run against the current package, by design.
#
# This script sweeps `distance`, the extrema filter that front B measured and
# that was REMOVED as a result (it was redundant with `prominence_relative`
# throughout the calibrated range). Against the current package every call
# below raises TypeError, which is the intended post-removal behaviour: there
# is no compatibility shim.
#
# It is kept as the evidence that justified the removal. Its frozen output
# alongside this file was produced on the pre-removal code
# (develop-v2.1 @ ab7f244, diagnostics commit 491a5d0) in the conda
# `cyclophaser` environment. To re-run it, check out that commit.
# ---------------------------------------------------------------------------
import sys as _sys


def _refuse_if_distance_is_gone():
    import inspect

    from cyclophaser.determine_periods import get_periods
    if "distance" not in inspect.signature(get_periods).parameters:
        _sys.exit(
            "HISTORICAL SCRIPT: `distance` was removed from cyclophaser, so this "
            "sweep cannot run against the current package. Its frozen output is "
            "next to this file; re-run it against develop-v2.1 @ ab7f244 if you "
            "need to reproduce it. See research/inert_params/REPORT_inertia_sweep.md."
        )


_refuse_if_distance_is_gone()
real = load_real_series()
LAB = {"20160735": [(145,177)], "20203947": [(122,144),(178,188)]}

def runs(periods, want="mature"):
    out, prev, st = [], None, 0
    names=[normalize_phase(str(x)) for x in periods]
    for i,n in enumerate(names):
        if n!=prev:
            if prev is not None: out.append((prev,st,i-1))
            prev,st=n,i
    out.append((prev,st,len(names)-1))
    return [(a,b,b-a+1) for p,a,b in out if p==want]

def go(tid, **over):
    gp = dict(GP); gp.update(over)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = get_periods(process_vorticity(pd.DataFrame({"zeta": real[tid]}), **PV), **gp)
    return runs(res["periods"])

lines=[]
def P(s=""):
    print(s); lines.append(s)

P("FRONT B - part 1 - causal sensitivity probe (diagnosis only, nothing changed)")
P("="*90)
for tid in ("20160735","20203947"):
    P(f"\n{tid}   labelled mature: {LAB[tid]}")
    P(f"  reference (distance=5, mature_amplitude_fraction=0.95):")
    P(f"      {go(tid)}")
    P(f"  --- vary `distance` (the front's suspected cause) ---")
    for d in (None, 1, 3, 5, 10, 14, 20, 30):
        P(f"      distance={str(d):>4} : {go(tid, distance=d)}")
    P(f"  --- vary `mature_amplitude_fraction` (distance fixed at 5) ---")
    for f in (0.95, 0.90, 0.80, 0.70, 0.50, 0.30):
        P(f"      fraction={f:.2f} : {go(tid, mature_amplitude_fraction=f)}")
    P(f"  --- vary `prominence_relative` (distance fixed at 5) ---")
    for pr in (0.3, 0.4, 0.5, 0.6, 0.8):
        P(f"      prom_rel={pr:.1f} : {go(tid, prominence_relative=pr)}")
    P(f"  --- mature_method='derivative' (the only branch that reads length_scale) ---")
    for ls in ("local","global"):
        P(f"      length_scale={ls:<7}: {go(tid, mature_method='derivative', length_scale=ls)}")

out = REPO/"research/labels/diagnostics/front_b/sensitivity.txt"
out.write_text("\n".join(lines)+"\n")
print(f"\nwrote {out}")
