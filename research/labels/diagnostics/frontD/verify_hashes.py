#!/usr/bin/env python
"""Front D, stage 0 — hash verification, run before any measurement.

Two things are checked, and nothing is measured until both pass:

1. `research/labels/configs/cyclophaser_params-13.yaml` against the sha256 the
   commissioning brief declares.
2. every frozen synthetic series in `tests/synthetic/data/*.csv` against the
   `series_sha256` recorded in `research/labels/manual_labels.yaml` — the
   repo's own registry of what each label was written against. The real
   calibration tracks are checked the same way, since the census reads them too.

The file sha256 of a CSV is printed alongside, but the label registry hashes
the parsed float64 VALUES, not the file bytes (labels_core.series_sha256), so
the value hash is the one that decides.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))

from labels_core import (  # noqa: E402
    load_real_series, load_synthetic_series, read_labels, series_sha256,
)

DECLARED_PARAMS13 = "c1ab8ce02631f1270b3a633cff2ef43fb5caff64dd492642f56cf5a96e483973"
CONFIG = REPO / "research/labels/configs/cyclophaser_params-13.yaml"


def file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ok = True

    got = file_sha256(CONFIG)
    match = got == DECLARED_PARAMS13
    ok &= match
    print("=" * 74)
    print("1. params-13 config, file sha256")
    print("=" * 74)
    print(f"  declared  {DECLARED_PARAMS13}")
    print(f"  measured  {got}")
    print(f"  -> {'MATCH' if match else 'MISMATCH'}\n")

    records = read_labels()
    real = load_real_series()
    synth, names = load_synthetic_series()

    for title, pop in (("2. frozen synthetic series (tests/synthetic/data/*.csv)", synth),
                       ("3. real calibration tracks (tests/calibration_data/*.csv)", real)):
        print("=" * 74)
        print(title)
        print("=" * 74)
        n_ok = n_bad = n_unlabelled = 0
        for sid in sorted(pop):
            vh = series_sha256(pop[sid])
            rec = records.get(sid)
            if rec is None:
                n_unlabelled += 1
                print(f"  {sid:<12} value {vh[:16]}…  NO LABEL ON FILE")
                continue
            same = rec.get("series_sha256") == vh
            n_ok += same
            n_bad += (not same)
            print(f"  {sid:<12} value {vh[:16]}…  vs label "
                  f"{str(rec.get('series_sha256'))[:16]}…  "
                  f"{'MATCH' if same else 'MISMATCH'}")
        print(f"  -> {n_ok} match, {n_bad} mismatch, {n_unlabelled} unlabelled\n")
        ok &= (n_bad == 0)

    print("=" * 74)
    print(f"OVERALL: {'PASS — safe to measure' if ok else 'FAIL — STOP'}")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
