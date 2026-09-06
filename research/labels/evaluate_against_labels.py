#!/usr/bin/env python
"""Score the detector's incipient boundary against the manual labels.

    python research/labels/evaluate_against_labels.py                 # TRAIN only
    python research/labels/evaluate_against_labels.py --config p.yaml # a calibration-app YAML
    python research/labels/evaluate_against_labels.py --test          # burns the test set

What is compared
----------------
A label now carries the cyclone's WHOLE phase sequence, so two things are scored
and reported side by side.

**The incipient boundary**, which is what this front was commissioned to settle.
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
* individual boundaries the labeller marked **not sure** are excluded the same
  way, and counted. Ambiguity is per BOUNDARY since schema 3: one unreadable
  mature->decay roll no longer voids the incipient knee four phases away from it.
  The count is printed because a phase that is routinely unreadable is a finding
  about the phase, not noise to be hidden.

**The whole sequence.** Sequence mismatch (the detector found different phases,
or in a different order) and boundary error are counted separately and never
averaged: pairing the 3rd labelled boundary with the 3rd detected one across a
mismatch compares two different transitions and manufactures a number. Boundary
errors are broken out per phase, each against its own margin, and the first
phase's start is excluded because it is 0 on both sides by construction.

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
    is_legacy_record, load_real_series, load_synthetic_series, normalize_phase,
    read_labels, read_split, score_labels, score_phase_sequences, series_sha256,
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


def detected_phase_starts(periods: pd.Series) -> list[tuple[str, int]]:
    """The detected sequence as [(phase, start_idx), ...], phase names normalised.

    The detector numbers repeated phases ("intensification 2"); a label carries
    the bare name and lets its position in the sequence express the repetition,
    so the names are normalised before the two are compared.
    """
    out: list[tuple[str, int]] = []
    prev = None
    for i, lab in enumerate(periods.astype(str)):
        name = normalize_phase(lab)
        if name != prev:
            out.append((name, i))
            prev = name
    return out


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


def run_detector(series: dict[str, pd.Series], pv: dict, gp: dict):
    """Returns ({id: incipient end index or None}, {id: full phase sequence})."""
    from cyclophaser.determine_periods import get_periods, process_vorticity
    inc: dict[str, int | None] = {}
    seqs: dict[str, list[tuple[str, int]]] = {}
    for sid, values in series.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                res = get_periods(vort, **gp)
            inc[sid] = detected_incipient_end(res["periods"])
            seqs[sid] = detected_phase_starts(res["periods"])
        except Exception as exc:  # a failed track is not a silent pass
            print(f"  !! {sid}: detection failed ({type(exc).__name__}: {exc})",
                  file=sys.stderr)
    return inc, seqs


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


def _fmt_phases(m: dict) -> str:
    def pct(x):
        return "—" if x is None else f"{100 * x:5.1f}%"

    def num(x, spec="6.2f"):
        return "—" if x is None else format(x, spec)

    lines = [
        f"    sequence          {m['n_sequence_match']} of {m['n_series']} match "
        f"({pct(m['sequence_match_rate'])}); "
        f"{m['n_sequence_mismatch']} differ in phases or order",
        f"    boundaries        {m['n_boundaries_hit']} of {m['n_boundaries']} within "
        f"their own margin ({pct(m['boundary_hit_rate'])})",
    ]
    if m.get("n_boundaries_unsure"):
        lines.append(
            f"    not sure          {m['n_boundaries_unsure']} boundary/ies the "
            f"labeller declined to place, excluded from the rate above")
    if m["per_phase"]:
        lines.append("      phase              n   hit    MAE  worst")
        for phase in ("incipient", "intensification", "mature", "decay", "residual"):
            v = m["per_phase"].get(phase)
            if not v:
                continue
            lines.append(f"      {phase:<16} {v['n']:>3}  {pct(v['hit_rate'])} "
                         f"{num(v['mae'])} {v['worst']:>6}")
    return "\n".join(lines)


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
    legacy = [sid for sid, r in records.items() if is_legacy_record(r)]
    if legacy:
        print(f"WARNING: {len(legacy)} label(s) were written against an earlier "
              f"schema and are EXCLUDED. Neither is upgradable: a schema-1 record "
              f"never stored the phase sequence, and a schema-2 record never "
              f"stored whether the labeller could place each boundary — assuming "
              f"they could is the one assumption that changes the score. "
              f"Re-label: {', '.join(sorted(legacy))}\n")
    usable = {sid: r for sid, r in records.items()
              if sid not in stale and sid not in missing and sid not in legacy}

    groups = ["train"] + (["test"] if args.test else [])
    wanted = {sid for sid in usable
              if (sid in train and "train" in groups) or (sid in test and "test" in groups)}
    detected, detected_seqs = run_detector(
        {k: series[k] for k in sorted(wanted)}, pv, gp)

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
            print("   ── incipient boundary ──")
            print(_fmt(m))
            print("   ── whole phase sequence ──")
            print(_fmt_phases(score_phase_sequences(sel, detected_seqs)))
        sel_all = [r for sid, r in sorted(usable.items()) if sid in ids]
        if sel_all:
            m = score_labels(sel_all, detected)
            print(f"\n  {grp.upper()} · ALL   ({m['n_scored']} labelled)")
            print("   ── incipient boundary ──")
            print(_fmt(m))
            print("   ── whole phase sequence ──")
            print(_fmt_phases(score_phase_sequences(sel_all, detected_seqs)))

    if not args.test:
        print(f"\n  TEST split held out ({len(test)} series). "
              "Pass --test to score it, once.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
