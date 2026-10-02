#!/usr/bin/env python
"""Score the detector's incipient boundary against the manual labels.

    python research/labels/evaluate_against_labels.py                 # TRAIN only
    python research/labels/evaluate_against_labels.py --config p.yaml # a calibration-app YAML
    python research/labels/evaluate_against_labels.py --test          # burns the test set
    python research/labels/evaluate_against_labels.py --batch-train swell_item30  # + the batch's TRAIN, own block

Adjudicated labels (item 30 part 3: `labels_core.is_adjudicated`, the vigente
record's `notes`) are the item-30 counterfactual's own output. They are never
pooled with any train number: whatever block they would have fallen in, they
are reported in a block of their own, ADJUDICATED.

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

Each block ends with the two CONSTANT BASELINES, on the same labels and the
same ruler: "always answer incipient end N" (N from 0 to 40, or no incipient
phase; front D's definition) and "always answer the modal labelled phase
sequence" (item 19's). Both choose their constant on the block's own labels,
so they are optimistic. The detector should beat them.

Only the labels and series of the groups being scored are used: without
--test, the test split's labels are dropped before any check and its files are
never opened (clean-up front, Passo 5).

Why --test is not the default
-----------------------------
A test set is spent the first time a parameter choice is made after looking at
it. This script defaults to train and prints a warning on --test for that reason.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
import warnings
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from labels_core import (  # noqa: E402
    batch_membership, first_blind_record, is_adjudicated, is_legacy_record,
    load_batch_series,
    load_real_series, load_synthetic_series, normalize_phase, phase_sequence, read_labels,
    read_split, score_labels, score_phase_sequences, series_sha256,
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
    parameter.

    Keys the file does NOT carry are filled with the frozen pre-item-31
    defaults (`config_defaults.fill_missing`, item 31 decision (a)), never with
    whatever the signature says today, and every filled key is listed on stderr.
    `path=None` still means package defaults: nothing is filled.
    """
    if path is None:
        return {}, {}
    from config_defaults import fill_missing, fill_warning
    doc, filled = fill_missing(yaml.safe_load(Path(path).read_text()) or {})
    if filled:
        print(f"NOTE ({Path(path).name}): {fill_warning(filled)}", file=sys.stderr)
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


# The constant baselines: what "ignore the series and always answer the same"
# scores on the same labels, on the same ruler (score_labels /
# score_phase_sequences). Made a standing output by the clean-up front
# (Passo 5) — proposal 8(b) of front D, docs/future_work.md item 25; the
# definitions are those of front D (incipient end) and item 19 (sequence).
BASELINE_CONSTANTS = [None] + list(range(0, 41))   # None = "no incipient phase"


def _fmt_baselines(sel) -> str:
    """Both constant baselines on the selection `sel`, the best constant chosen
    ON that selection (an optimistic baseline: it has seen the answers)."""
    ids = [r["id"] for r in sel]
    best = None
    for const in BASELINE_CONSTANTS:
        m = score_labels(sel, {sid: const for sid in ids})
        key = (m["n_hit"], -(m["mae"] if m["mae"] is not None else 1e9))
        if best is None or key > best[0]:
            best = (key, const, m)
    _, const, m = best
    hit = "—" if m["hit_rate"] is None else f"{100 * m['hit_rate']:.1f}%"
    mae = "—" if m["mae"] is None else f"{m['mae']:.2f}"
    seqs = Counter(tuple(p for p, _ in phase_sequence(r)) for r in sel)
    modal, k = seqs.most_common(1)[0]
    return "\n".join([
        "   ── constant baselines (ignore the series; best constant chosen on this selection) ──",
        f"     incipient end, always {'no incipient' if const is None else const}: "
        f"hit {m['n_hit']}/{m['n_boundary']} ({hit}), MAE {mae}, worst {m['worst']}; "
        f"none agreed {m['n_none_agreed']}/{m['n_none']}",
        f"     phase sequence, always the modal labelled one "
        f"({' -> '.join(modal)}): {k}/{len(sel)} exact"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=None,
                    help="calibration-app YAML; omitted means package defaults")
    ap.add_argument("--test", action="store_true",
                    help="also score the held-out test split (see the warning)")
    ap.add_argument("--against", choices=("current", "first-blind"), default="current",
                    help="'current' (default) scores the vigente record, i.e. the "
                         "most recent save for each case, whether or not an overlay "
                         "was on screen when it was written. 'first-blind' scores "
                         "the EARLIEST version of each case's label that was saved "
                         "with no overlay shown (schema-3 records qualify: overlays "
                         "did not exist yet) — cases where every saved version had "
                         "an overlay on screen are excluded, the same way a stale "
                         "or legacy one is.")
    ap.add_argument("--batch-train", metavar="BATCH", default=None,
                    help="also score the TRAIN part of this frozen batch of "
                         "split.yaml (e.g. swell_item30), in its own block, never "
                         "pooled with the 47. Every label that is not TRAIN (of "
                         "the split or of the batch) is dropped by id right after "
                         "reading, before any check reads it. Not combinable "
                         "with --test.")
    args = ap.parse_args(argv)
    if args.batch_train and args.test:
        ap.error("--batch-train is train-only; it cannot be combined with --test")

    records = read_labels()
    if not records:
        print("manual_labels.yaml holds no labels yet — nothing to score.\n"
              "Label the queue first: streamlit run tools/calibration_app/app.py, "
              "then choose the 'Label' display mode.")
        return 0

    batch_train: set[str] = set()
    if args.batch_train:
        membership = batch_membership(args.batch_train)
        if not membership:
            ap.error(f"split.yaml has no batch {args.batch_train!r}")
        batch_train = {sid for sid, m in membership.items() if m == "train"}
        keep = set(read_split()["train"]) | batch_train
        records = {sid: r for sid, r in records.items() if sid in keep}

    # Scope first. Only the labels and series of the groups being scored are
    # used, and before anything could name them: the test split is spent, so
    # without --test its labels are dropped here and its files are never opened.
    split = read_split()
    train, test = set(split["train"]), set(split["test"])
    in_scope = train | (test if args.test else set()) | batch_train
    records = {sid: r for sid, r in records.items() if sid in in_scope}

    # Read from the VIGENTE record, before --against first-blind can swap in an
    # older version that does not carry the note.
    adjudicated = {sid for sid, r in records.items() if is_adjudicated(r)}

    if args.against == "first-blind":
        never_blind = sorted(sid for sid, r in records.items()
                             if first_blind_record(r) is None)
        records = {sid: (first_blind_record(r) or r) for sid, r in records.items()
                  if sid not in never_blind}
        if never_blind:
            print(f"WARNING: {len(never_blind)} label(s) have no blind version on "
                  f"file (an overlay was already shown by the first save) and are "
                  f"EXCLUDED from --against first-blind: "
                  f"{', '.join(never_blind)}\n")

    pv, gp = load_config(args.config)

    real = load_real_series(ids=in_scope)
    synth, _names = load_synthetic_series()
    synth = {k: v for k, v in synth.items() if k in in_scope}
    series = {**real, **synth}
    sources = {k: "real" for k in real} | {k: "synthetic" for k in synth}
    if batch_train:
        batch = load_batch_series(args.batch_train, ids=batch_train)
        series |= {k: v for k, v in batch.items() if k in batch_train}
        sources |= {k: "real" for k in batch_train}

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
    wanted |= {sid for sid in usable if sid in batch_train}
    detected, detected_seqs = run_detector(
        {k: series[k] for k in sorted(wanted)}, pv, gp)

    print("=" * 74)
    print(f"Incipient boundary vs manual labels   ({len(usable)} usable label(s))")
    print(f"config: {args.config if args.config else 'package defaults'}")
    print(f"against: {args.against}")
    print("=" * 74)

    if args.test:
        print("\n*** --test: you are scoring the HELD-OUT split. It burns on use. ***")
        print("*** Any parameter chosen after reading these numbers makes this  ***")
        print("*** set a second training set, and there is no third.            ***\n")

    for grp, ids in (("train", train - adjudicated), ("test", test - adjudicated)):
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
            print(_fmt_baselines(sel))
        sel_all = [r for sid, r in sorted(usable.items()) if sid in ids]
        if sel_all:
            m = score_labels(sel_all, detected)
            print(f"\n  {grp.upper()} · ALL   ({m['n_scored']} labelled)")
            print("   ── incipient boundary ──")
            print(_fmt(m))
            print("   ── whole phase sequence ──")
            print(_fmt_phases(score_phase_sequences(sel_all, detected_seqs)))
            print(_fmt_baselines(sel_all))

    if batch_train:
        sel = [r for sid, r in sorted(usable.items())
               if sid in batch_train and sid not in adjudicated]
        if sel:
            m = score_labels(sel, detected)
            print(f"\n  BATCH {args.batch_train} · TRAIN   ({m['n_scored']} labelled; "
                  "its own block, never pooled with the split)")
            print("   ── incipient boundary ──")
            print(_fmt(m))
            print("   ── whole phase sequence ──")
            print(_fmt_phases(score_phase_sequences(sel, detected_seqs)))
            print(_fmt_baselines(sel))

    sel = [r for sid, r in sorted(usable.items()) if sid in wanted and sid in adjudicated]
    if sel:
        m = score_labels(sel, detected)
        print(f"\n  ADJUDICATED   ({m['n_scored']} labelled; label = the item-30 "
              "counterfactual, its own block, never pooled with any train number)")
        print("   ── incipient boundary ──")
        print(_fmt(m))
        print("   ── whole phase sequence ──")
        print(_fmt_phases(score_phase_sequences(sel, detected_seqs)))
        print(_fmt_baselines(sel))

    if not args.test:
        print(f"\n  TEST split held out ({len(test)} series). "
              "Pass --test to score it, once.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
