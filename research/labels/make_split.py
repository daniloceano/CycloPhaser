#!/usr/bin/env python
"""Draw the frozen train/test split over the 51 calibration tracks.

    python research/labels/make_split.py            # writes split.yaml, refuses to clobber
    python research/labels/make_split.py --force    # overwrite (see the warning below)

The draw is stratified by series length into three bands (n<60: 10 tracks,
60<=n<120: 22, n>=120: 19) because those bands are not interchangeable — a
30-step track gives the incipient detector far less to work with than a 259-step
one, and an unstratified 70/30 draw over 51 items can leave a band nearly empty
in the test set.

The 12 synthetic cases are not drawn at all: they all go to train, tagged
source: synthetic. They are a designed population rather than a sample, so
holding a few out would buy no evidence about generalisation while costing a
quarter of the only series whose construction is actually known.

REFUSING TO OVERWRITE IS THE POINT. Redrawing the split after seeing how the
detector scored on it turns the test set into a second training set — the split
must be decided once, before any result is looked at. --force exists only for
the case where the split has never been used.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels_core import (  # noqa: E402
    SPLIT_PATH, SPLIT_SEED, build_split_document,
    load_real_series, load_synthetic_series,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=SPLIT_PATH)
    ap.add_argument("--seed", type=int, default=SPLIT_SEED)
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing split.yaml (invalidates the test set)")
    args = ap.parse_args(argv)

    if args.out.exists() and not args.force:
        print(f"refusing to overwrite {args.out}\n"
              "  A split redrawn after results have been seen is not a test set.\n"
              "  Pass --force only if this split has never been used.", file=sys.stderr)
        return 1

    real = load_real_series()
    synth, _names = load_synthetic_series()
    if not real:
        print("no calibration tracks found", file=sys.stderr)
        return 1

    doc = build_split_document({k: len(v) for k, v in real.items()},
                               synth.keys(), seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.safe_dump(doc, sort_keys=False, default_flow_style=False))

    n_syn = len(synth)
    print(f"wrote {args.out}")
    print(f"  seed        {doc['seed']}")
    for label, s in doc["strata"].items():
        print(f"  {label:<7} n={s['n']:>3}  train={s['n_train']:>3}  test={s['n_test']:>3}")
    print(f"  synthetic   n={n_syn:>3}  train={n_syn:>3}  test=  0  (never held out)")
    print(f"  TOTAL train={len(doc['train'])}  test={len(doc['test'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
