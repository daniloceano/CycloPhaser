"""Item 31, stage 2b — proof that the use_filter=False fix changes nothing but crashes.

The defect (found while regenerating tests/expected_no_filter.csv, DESIGN §11.3):
`process_vorticity(..., use_filter=False)` keeps the raw series on the input
index's own dimension ("index" when the index is unnamed), and with
`use_smoothing=False` nothing rebuilds it on "time", so `differentiate('time')`
raises. Reachable in 2.0.0 only with use_smoothing=False passed explicitly;
reachable with use_filter=False alone under the new defaults.

This script is run TWICE — before the fix (`--phase before`) and after it
(`--phase after`) — over the 54 TRAIN series and the packaged example, each in
two index flavours (the loader's own index, and the same values on an UNNAMED
DatetimeIndex, as tests/test_determine_periods.py builds it), under three
configurations:

  new      : package defaults + use_filter=False
  v200     : the 2.0.0 table + use_filter=False            (smoothing 'auto')
  v200_nos : the 2.0.0 table + use_filter=False + use_smoothing(_twice)=False

It stores, per (config, series, flavour), either the periods column's sha256 or
"CRASH: <error>". The `after` run asserts: every entry that was an output
before is byte-identical after; entries that were CRASH may become outputs.

Outputs: fix_use_filter_false_before.json / _after.json, and the comparison
printed (tee fix_use_filter_false_equivalence.txt).
Run: python -P research/labels/diagnostics/item31/fix_use_filter_false_equivalence.py --phase before|after
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

sys.path.insert(0, str(core.REPO / "tests"))
from legacy_defaults import ALL_2_0_0  # noqa: E402

dp = core.dp
CONFIGS = {
    "new": {"use_filter": False},
    "v200": {**ALL_2_0_0, "use_filter": False},
    "v200_nos": {**ALL_2_0_0, "use_filter": False, "use_smoothing": False,
                 "use_smoothing_twice": False},
}


def outcome(values: pd.Series, kw: dict) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = dp.determine_periods(values, **kw)
        return hashlib.sha256("|".join(res["periods"].astype(str)).encode()).hexdigest()
    except Exception as e:  # recorded, never swallowed silently
        return f"CRASH: {type(e).__name__}: {str(e)[:80]}"


def population() -> dict[str, pd.Series]:
    g = core.train_series()
    pop = {**g["original_real"], **g["synthetic"], **g["batch_train"]}
    from cyclophaser import example_file
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    pop["example"] = track["min_max_zeta_850"]
    out = {}
    for sid, s in pop.items():
        out[f"{sid}|own"] = s
        idx = s.index if isinstance(s.index, pd.DatetimeIndex) else \
            pd.date_range("2000-01-01", periods=len(s), freq="h")
        out[f"{sid}|unnamed"] = pd.Series(s.to_numpy(), index=list(idx))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("before", "after"), required=True)
    a = ap.parse_args()
    env = core.assert_environment()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=core.REPO,
                          capture_output=True, text=True).stdout.strip()
    pop = population()
    res = {c: {k: outcome(v, kw) for k, v in pop.items()} for c, kw in CONFIGS.items()}
    (HERE / f"fix_use_filter_false_{a.phase}.json").write_text(
        json.dumps({"environment": env, "head": head, "results": res}, indent=2))
    for c in CONFIGS:
        n_crash = sum(v.startswith("CRASH") for v in res[c].values())
        print(f"[{a.phase} @ {head}] {c:<9} {len(res[c])} runs, {n_crash} CRASH")
    if a.phase == "after":
        before = json.loads((HERE / "fix_use_filter_false_before.json").read_text())
        ok = True
        for c in CONFIGS:
            b, n = before["results"][c], res[c]
            same = sum(b[k] == n[k] for k in b if not b[k].startswith("CRASH"))
            outputs = sum(not b[k].startswith("CRASH") for k in b)
            fixed = sum(b[k].startswith("CRASH") and not n[k].startswith("CRASH") for k in b)
            still = sum(n[k].startswith("CRASH") for k in n)
            ok &= same == outputs and still == 0
            print(f"  {c:<9} outputs before identical after: {same}/{outputs}; "
                  f"crashes fixed: {fixed}; crashes remaining: {still}")
        print(f"FIX EQUIVALENCE (no output changed, no crash left): {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    main()
