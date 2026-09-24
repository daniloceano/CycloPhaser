#!/usr/bin/env python
"""Per-series fingerprint of the detector's output, for a NAMED cyclophaser tree.

Stage 2 has to answer two different questions with the same instrument:

  Q1  does `reclassify_index0=False` reproduce develop-v2.1 @ c714451 exactly?
  Q2  under the new default, which series move — and do the other 58 stay put?

Both are answered by hashing the `periods` column per series and comparing
fingerprints, so the comparison is byte-level and not a sequence summary that
could hide a one-step shift.

Q1 needs the OLD code, which no longer exists in the working tree, so this
script takes `--worktree`: it puts that path at `sys.path[0]`, imports
`cyclophaser` from it, and HARD-ASSERTS the loaded package lives inside it
before hashing anything (the lesson of items 5, 12 and 27 — asserting the conda
env is not enough). Point it at a `git worktree` of c714451 for the reference
and at the working tree for the current code; the rest of the code path is
identical, so the only variable is which package answered.

`--set-flag` is how the same tree is measured both ways: `off` forces
`reclassify_index0=False`, `on` forces True, `config` leaves whatever the YAML
says. It is dropped automatically when the loaded package does not accept it
(which is the case for c714451).

Run:
    python stage2_reference.py --worktree <path> --config <yaml> \
        --set-flag off --out <json>
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import sys
import warnings
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--set-flag", choices=["off", "on", "config"], default="config")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()

    worktree = a.worktree.resolve()
    sys.path.insert(0, str(worktree))
    sys.path.insert(1, str(worktree / "research" / "labels"))

    import cyclophaser  # noqa: E402
    pkg = Path(cyclophaser.__file__).resolve()
    dp = sys.modules.get("cyclophaser.determine_periods")

    print("=" * 74)
    print("PROVENANCE (before any measurement)")
    print("=" * 74)
    print(f"  cwd            : {Path(os.getcwd()).resolve()}")
    print(f"  worktree       : {worktree}")
    print(f"  sys.executable : {sys.executable}")
    print(f"  sys.prefix     : {sys.prefix}")
    print(f"  cyclophaser    : {pkg}")
    if worktree not in pkg.parents:
        raise SystemExit(f"SHADOWED: cyclophaser at {pkg}, not under {worktree}")

    import pandas as pd  # noqa: E402
    import yaml  # noqa: E402
    from cyclophaser.determine_periods import get_periods, process_vorticity  # noqa: E402

    det = Path(sys.modules["cyclophaser.determine_periods"].__file__).resolve()
    print(f"  determine_periods.py : {det}")
    print(f"    sha256             : {hashlib.sha256(det.read_bytes()).hexdigest()}")
    print("  ASSERT OK: package loads from the named worktree.")
    print("=" * 74, flush=True)

    from labels_core import load_real_series, load_synthetic_series  # noqa: E402

    doc = yaml.safe_load(a.config.read_text()) or {}
    PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
               "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
               "cutoff_high", "boundary_padding")
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    dropped = sorted(set(doc.get("phase_params") or {}) - set(gp))

    accepts_flag = "reclassify_index0" in gp_ok
    if a.set_flag != "config":
        if accepts_flag:
            gp["reclassify_index0"] = (a.set_flag == "on")
        elif a.set_flag == "on":
            raise SystemExit("this tree's get_periods has no reclassify_index0")

    print(f"config: {a.config}")
    print(f"  sha256: {hashlib.sha256(a.config.read_bytes()).hexdigest()}")
    print(f"  keys dropped by the signature filter: {dropped}")
    print(f"  get_periods accepts reclassify_index0: {accepts_flag}")
    print(f"  reclassify_index0 in this run: {gp.get('reclassify_index0', '<absent>')}")

    real = load_real_series()
    synth, names = load_synthetic_series()
    series = [(k, real[k], "real") for k in sorted(real)] + \
             [(k, synth[k], "sintetico") for k in sorted(synth)]
    print(f"loaded {len(series)} series\n", flush=True)

    records = {}
    for sid, values, source in series:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            res = get_periods(vort, **gp)
        labels = [str(v) for v in res["periods"]]
        seq, prev = [], None
        for v in labels:
            if v != prev:
                seq.append(v)
                prev = v
        records[sid] = {
            "fonte": source,
            "caso": names.get(sid, ""),
            "n_steps": len(values),
            "periods_sha256": hashlib.sha256("\n".join(labels).encode()).hexdigest(),
            "sequencia": ">".join(seq),
        }

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        "worktree": str(worktree),
        "cyclophaser": str(pkg),
        "determine_periods_sha256": hashlib.sha256(det.read_bytes()).hexdigest(),
        "config": str(a.config),
        "config_sha256": hashlib.sha256(a.config.read_bytes()).hexdigest(),
        "set_flag": a.set_flag,
        "accepts_flag": accepts_flag,
        "records": records,
    }, indent=1))
    print(f"wrote {a.out} ({len(records)} series)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
