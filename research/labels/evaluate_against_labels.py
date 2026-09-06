#!/usr/bin/env python
"""Score the detector's incipient boundary against the manual labels.

    python research/labels/evaluate_against_labels.py                 # TRAIN only
    python research/labels/evaluate_against_labels.py --config p.yaml # a calibration-app YAML
    python research/labels/evaluate_against_labels.py --test          # burns the test set

What is compared
----------------
The label says where the incipient phase ENDS: the incipient phase is [0, N).
The detector's answer is read the same way — the number of leading `incipient`
entries in the `periods` column, or "no incipient phase" when step 0 is already
something else. Nothing else about the detection is looked at.

What is reported, and why separately
------------------------------------
* **hit rate within each label's own tolerance_idx** — the headline number. The
  margin is per-label because the subjectivity is not uniform: some knees are
  unmistakable, some ramps are gentle enough that ten indices would do.
* **MAE and worst case, raw**, alongside. A hit rate under a per-label margin
  can be inflated by wide margins and says nothing about the size of the misses,
  so the undecorated distance is always printed next to it.
* **refusal, both directions** — the detector agreeing there is no incipient
  phase, and the detector refusing where the label says there is a boundary.
  Refusing is a different failure from being off by k steps and averaging the
  two would hide both.
* `kind=ambiguous` labels are excluded from the hit rate and the MAE — there is
  nothing to be near — but kept in the refusal accounting, where "the detector
  also declined" is still worth knowing.

Everything is broken down by split (train/test) and by source (real/synthetic).

Why --test is not the default
-----------------------------
A test set is spent the first time a parameter choice is made after looking at
it. This script defaults to train and prints a warning on --test for that reason.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from labels_core import (  # noqa: E402
    load_real_series, load_synthetic_series, read_labels, read_split,
    score_labels, series_sha256,
)

# get_periods' own defaults for everything the config YAML may omit.
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")


def detected_incipient_end(periods: pd.Series) -> int | None:
    """Number of leading `incipient` steps, or None if there is no incipient phase.

    Mirrors the label's own convention exactly — the incipient phase is [0, N) —
    so the two numbers are directly subtractable.
    """
    labels = list(periods.astype(str))
    if not labels or not labels[0].startswith("incipient"):
        return None
    n = 0
    for lab in labels:
        if not lab.startswith("incipient"):
            break
        n += 1
    return n


def load_config(path: Path | None):
    """Split a calibration-app YAML into (process_vorticity kwargs, get_periods kwargs).

    Unknown keys are dropped rather than raising: the app's export also carries a
    `metadata` and an `evaluation` block, neither of which is a detector
    parameter, and old exports legitimately lack keys added since.
    """
    if path is None:
        return {}, {}
    doc = yaml.safe_load(Path(path).read_text()) or {}
    import inspect

    from cyclophaser.determine_periods import get_periods
    gp_accepted = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_accepted}
    return pv, gp


def run_detector(series: dict[str, pd.Series], pv: dict, gp: dict) -> dict[str, int | None]:
    from cyclophaser.determine_periods import get_periods, process_vorticity
    out: dict[str, int | None] = {}
    for sid, values in series.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                res = get_periods(vort, **gp)
            out[sid] = detected_incipient_end(res["periods"])
        except Exception as exc:  # a failed track is not a silent pass
            print(f"  !! {sid}: detection failed ({type(exc).__name__}: {exc})",
                  file=sys.stderr)
    return out


def _fmt(m: dict) -> str:
    def pct(x):
        return "—" if x is None else f"{100 * x:5.1f}%"

    def num(x, spec="6.2f"):
        return "—" if x is None else format(x, spec)

    return (
        f"    boundary labels   {m['n_boundary']:>3}   "
        f"hit within margin {m['n_hit']:>3}  ({pct(m['hit_rate'])})\n"
        f"    raw distance      MAE {num(m['mae'])}   worst "
        f"{num(m['worst'], '3d') if m['worst'] is not None else '—':>6}   "
        f"(over {m['n_compared']} comparable)\n"
        f"    refusal           detector found no incipient phase on "
        f"{m['detector_missing_on_boundary']} of those {m['n_boundary']}\n"
        f"                      label says none: {m['n_none']:>3}, "
        f"detector agreed on {m['n_none_agreed']} ({pct(m['none_agreement_rate'])})\n"
        f"                      label ambiguous: {m['n_ambiguous']:>3}, "
        f"detector found none on {m['n_ambiguous_detector_none']}"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=None,
                    help="calibration-app YAML; omitted means package defaults")
    ap.add_argument("--test", action="store_true",
                    help="also score the held-out test split (see the warning)")
    args = ap.parse_args(argv)

    records = read_labels()
    if not records:
        print("manual_labels.yaml holds no labels yet — nothing to score.\n"
              "Label the queue first: streamlit run tools/calibration_app/app.py, "
              "then choose the 'Label' display mode.")
        return 0

    split = read_split()
    train, test = set(split["train"]), set(split["test"])
    pv, gp = load_config(args.config)

    real = load_real_series()
    synth, _names = load_synthetic_series()
    series = {**real, **synth}
    sources = {k: "real" for k in real} | {k: "synthetic" for k in synth}

    # A label written against different data is void, not merely suspect: the
    # boundary index refers to positions in a series that no longer exists.
    stale = [sid for sid, r in records.items()
             if sid in series and r.get("series_sha256") != series_sha256(series[sid])]
    missing = [sid for sid in records if sid not in series]
    if stale:
        print(f"WARNING: {len(stale)} label(s) were written against different "
              f"data and are EXCLUDED: {', '.join(sorted(stale))}\n")
    if missing:
        print(f"WARNING: {len(missing)} label(s) name a series that no longer "
              f"exists and are EXCLUDED: {', '.join(sorted(missing))}\n")
    usable = {sid: r for sid, r in records.items()
              if sid not in stale and sid not in missing}

    groups = ["train"] + (["test"] if args.test else [])
    wanted = {sid for sid in usable
              if (sid in train and "train" in groups) or (sid in test and "test" in groups)}
    detected = run_detector({k: series[k] for k in sorted(wanted)}, pv, gp)

    print("=" * 74)
    print(f"Incipient boundary vs manual labels   ({len(usable)} usable label(s))")
    print(f"config: {args.config if args.config else 'package defaults'}")
    print("=" * 74)

    if args.test:
        print("\n*** --test: you are scoring the HELD-OUT split. It burns on use. ***")
        print("*** Any parameter chosen after reading these numbers makes this  ***")
        print("*** set a second training set, and there is no third.            ***\n")

    for grp, ids in (("train", train), ("test", test)):
        if grp not in groups:
            continue
        for src in ("real", "synthetic"):
            sel = [r for sid, r in sorted(usable.items())
                   if sid in ids and sources.get(sid) == src]
            if not sel:
                continue
            m = score_labels(sel, detected)
            print(f"\n  {grp.upper()} · {src}   ({m['n_scored']} labelled)")
            print(_fmt(m))
        sel_all = [r for sid, r in sorted(usable.items()) if sid in ids]
        if sel_all:
            m = score_labels(sel_all, detected)
            print(f"\n  {grp.upper()} · ALL   ({m['n_scored']} labelled)")
            print(_fmt(m))

    if not args.test:
        print(f"\n  TEST split held out ({len(test)} series). "
              "Pass --test to score it, once.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
