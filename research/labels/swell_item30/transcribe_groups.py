"""Transcribe the three swell groups of item 30 from the maturation diagnostic's CSV.

Front 30, selection part. This script reads NO series and runs NO detector: it
only copies a partition that already exists in a saved output into a committed
file, so the seeded draw (`draw_batch.py`) depends on nothing outside the repo.

Input: `m1_baseline.csv` — Measurement 1 of the maturation diagnostic of
2026-09-24 (200 swell tracks, repo `params-11`, package code of develop-v2.1 @
d45ae49 via baaf595; see `README.md` in this folder for the full provenance).
Its sha256 is checked before anything is read.

Definitions — exactly those of the diagnostic's `m1_baseline.py`:

  * peak of intensity: `peak_idx = argmin(z)`, `z` the FILTERED vorticity that
    `get_periods` returns (vorticity is negative in the SH, so the most intense
    instant is the minimum);
  * end of the incipient plateau: `plateau_boundary =
    _incipient_plateau_boundary(_incipient_plateau_rel(...), tau, crossing, k)`,
    the first index of the first run of k=5 consecutive samples with
    rel >= tau=0.2 ("sustained"), rel = |d(zeta_raw smoothed)/dt| / max;
  * the signal: `plateau_boundary > peak_idx` (the plateau ends after the peak);
  * bad / good: Danilo's 15 marks (column `bad`).

Groups: R = bad AND signal (9) · S = good AND signal (10) · C = good AND NOT
signal (175). The 6 bad tracks without the signal belong to no group.

Run:
    python research/labels/swell_item30/transcribe_groups.py --csv <path to m1_baseline.csv>
"""

import argparse
import hashlib
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
OUT = HERE / "groups_params11.yaml"
CSV_SHA256 = "a1aa56195c4823f7b998644e4d5673d8748bf1dd41e930fd319ad14b5c0ce51b"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    args = ap.parse_args()

    raw = args.csv.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != CSV_SHA256:
        raise SystemExit(f"m1_baseline.csv sha256 {got} != expected {CSV_SHA256}")

    d = pd.read_csv(args.csv, dtype={"track_id": str}).set_index("track_id")
    assert len(d) == 200 and int(d.bad.sum()) == 15, (len(d), int(d.bad.sum()))
    signal = d.plateau_boundary > d.peak_idx
    groups = {
        "R": sorted(d.index[d.bad & signal]),
        "S": sorted(d.index[~d.bad & signal]),
        "C": sorted(d.index[~d.bad & ~signal]),
    }
    doc = {
        "source_csv": "m1_baseline.csv (maturation diagnostic, 2026-09-24; not in the repo)",
        "source_csv_sha256": CSV_SHA256,
        "signal": "plateau_boundary > peak_idx",
        "n_tracks": len(d),
        "bad_marks": sorted(d.index[d.bad]),
        "n": {g: len(v) for g, v in groups.items()},
        "groups": groups,
    }
    OUT.write_text(yaml.safe_dump(doc, sort_keys=False, default_flow_style=False),
                   encoding="utf-8")
    print({g: len(v) for g, v in groups.items()}, "->", OUT)


if __name__ == "__main__":
    main()
