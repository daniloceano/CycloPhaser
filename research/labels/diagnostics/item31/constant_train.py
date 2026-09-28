"""Item 31, stage 0, task 5 support — the CONSTANT comparator, derived from TRAIN only.

Population the constant is derived from: the 35 REAL series of the original
TRAIN split — the same source and the same split draw as the 16 TEST series it
will be scored against in stage 1. Excluded from the derivation, on purpose:
the 12 synthetics (a different population, built from segment lists) and the 7
batch train series (drawn from signal-enriched groups R/S/C, not representative;
5 of them are adjudicated). Labels of any TEST id are never read: records are
filtered by id right after `read_labels`, before any field is touched.

The constant ignores the series. It is fully specified by two numbers derived
here, and they are frozen by this file's output:

* S*  — the modal phase SEQUENCE of the 35 labels (ties → report all and stop).
* INC* — the constant's incipient answer, coherent with S*:
         S* opens without incipient  → "no incipient phase" (None);
         S* opens with incipient     → the N that maximises boundary hits on the
                                       35 (front D's rule, `frontD/constant_baseline.py`:
                                       max hits, tie → lower MAE, tie → lower N).

Printed for information, on the same 35, under the SAME ruler (score_labels /
score_phase_sequences): params-15, package defaults and the constant — plus,
for task 7 only, params-15's phase parameters on the current default filter. These are
TRAIN numbers; they calibrate nothing in stage 1's criterion except the
reachability discussion in DESIGN.md, which says so where it uses them.

Both label versions are reported: `current` (vigente record) and `first-blind`.

Outputs: constant_train.txt (via tee), constant_train.json.

Run: python -P research/labels/diagnostics/item31/constant_train.py | tee .../constant_train.txt
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

lc = core.lc
sys.path.insert(0, str(core.LABELS / "diagnostics" / "item19"))
from item19_core import MARGIN, pair_by_overlap  # noqa: E402


def train_real_records(version: str) -> dict[str, dict]:
    ids = set(core.split_sets()["train"]) & {
        k for k, v in core.split_sets()["source"].items() if v == "real"}
    recs = {sid: r for sid, r in lc.read_labels().items() if sid in ids}   # by id FIRST
    assert len(recs) == 35 and set(recs).isdisjoint(core.test_ids())
    assert not any(lc.is_adjudicated(r) for r in recs.values())
    if version == "first-blind":
        recs = {sid: lc.first_blind_record(r) for sid, r in recs.items()
                if lc.first_blind_record(r) is not None}
    return recs


def label_seq(rec) -> tuple[str, ...]:
    return tuple(p for p, _ in lc.phase_sequence(rec))


def mature_hits(records, runs_by_id) -> tuple[int, int]:
    """benchmark_core.mature_metrics' rule: first labelled mature, largest overlap, margin 6."""
    n = hit = 0
    for sid, rec in records.items():
        ph = rec["phases"]
        lab = [(p["start_idx"], (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph)
                else rec["n_steps"] - 1)
               for k, p in enumerate(ph) if lc.normalize_phase(p["phase"]) == "mature"]
        if not lab:
            continue
        n += 1
        det = [(a, b) for p, a, b in runs_by_id[sid] if p == "mature"]
        paired, _ = pair_by_overlap(det, lab[0])
        if paired is not None and abs(paired[0] - lab[0][0]) <= MARGIN \
                and abs(paired[1] - lab[0][1]) <= MARGIN:
            hit += 1
    return hit, n


def runs(periods) -> list[tuple[str, int, int]]:
    out, prev, s = [], None, 0
    labs = [lc.normalize_phase(str(x)) for x in periods]
    for i, x in enumerate(labs):
        if x != prev:
            if i:
                out.append((prev, s, i - 1))
            prev, s = x, i
    if labs:
        out.append((prev, s, len(labs) - 1))
    return out


def summarise(name, records, inc, seqs, runs_by_id=None) -> dict:
    m = lc.score_labels(list(records.values()), inc)
    q = lc.score_phase_sequences(list(records.values()), seqs)
    d = {"incipient_hits": m["n_hit"], "n_boundary": m["n_boundary"],
         "none_agreed": m["n_none_agreed"], "n_none": m["n_none"],
         "false_refusals": m["detector_missing_on_boundary"],
         "ambiguous": m["n_ambiguous"], "ambiguous_detector_none": m["n_ambiguous_detector_none"],
         "incipient_correct": m["n_hit"] + m["n_none_agreed"],
         "incipient_decidable": m["n_boundary"] + m["n_none"],
         "sequence_match": q["n_sequence_match"], "n_series": q["n_series"],
         "mae": m["mae"]}
    if runs_by_id is not None:
        d["mature_hits"], d["n_mature"] = mature_hits(records, runs_by_id)
    print(f"  {name:<20} incipient hits {d['incipient_hits']:>2}/{d['n_boundary']:<2} "
          f"none agreed {d['none_agreed']:>2}/{d['n_none']:<2} "
          f"false refusals {d['false_refusals']:>2}  "
          f"correct {d['incipient_correct']:>2}/{d['incipient_decidable']:<2}  "
          f"sequence {d['sequence_match']:>2}/{d['n_series']:<2}"
          + (f"  mature {d['mature_hits']:>2}/{d['n_mature']}" if runs_by_id else ""))
    return d


def main() -> None:
    env = core.assert_environment()
    print("environment:", json.dumps(env))
    series = core.train_series()["original_real"]
    p15 = core.load_config("params-15")
    # Task 7 support, INFORMATION ONLY: params-15's phase parameters on the CURRENT
    # default filter — the hybrid a "phase-only" default change would ship.
    cfgs = {"params-15": p15, "defaults": core.load_config(None),
            "p15-phase|def-filter": ({}, p15[1])}
    det = {}
    for name, cfg in cfgs.items():
        maps = {sid: core.run(v, *cfg) for sid, v in series.items()}
        det[name] = ({sid: core.incipient_end(p) for sid, p in maps.items()},
                     {sid: [(ph, i) for ph, i in core.ev.detected_phase_starts(
                         core.pd.Series(p, dtype=object))] for sid, p in maps.items()},
                     {sid: runs(p) for sid, p in maps.items()})

    out = {"environment": env}
    for version in ("current", "first-blind"):
        recs = train_real_records(version)
        print(f"\n=== TRAIN real, labels {version}: {len(recs)} records ===")
        kinds = Counter(r["verdict"]["kind"] for r in recs.values())
        seqc = Counter(" > ".join(label_seq(r)) for r in recs.values())
        print("verdict kinds:", dict(kinds))
        print("sequence distribution:")
        for s, c in seqc.most_common():
            print(f"  {c:>2}  {s}")
        top = seqc.most_common()
        ties = [s for s, c in top if c == top[0][1]]
        assert len(ties) == 1, f"modal sequence tied: {ties} — STOP, declare a rule"
        s_star = tuple(ties[0].split(" > "))
        if s_star[0] != "incipient":
            inc_star, best = None, None
        else:
            best = None
            for n in range(1, 61):
                m = lc.score_labels(list(recs.values()), {sid: n for sid in recs})
                key = (m["n_hit"], -(m["mae"] or 1e9), -n)
                if best is None or key > best[0]:
                    best = (key, n)
            inc_star = best[1]
        print(f"S* = {' > '.join(s_star)}  ({top[0][1]}/{len(recs)})   INC* = "
              f"{'no incipient' if inc_star is None else inc_star}")
        const_inc = {sid: inc_star for sid in recs}
        const_seq = {sid: [(p, i) for i, p in enumerate(s_star)] for sid in recs}
        print("scores on these TRAIN labels (same ruler):")
        res = {"constant": summarise("constant", recs, const_inc, const_seq)}
        for name in cfgs:
            inc, seqs, rb = det[name]
            res[name] = summarise(name, recs, {k: inc[k] for k in recs},
                                  {k: seqs[k] for k in recs}, {k: rb[k] for k in recs})
        # Sequence matches broken down by the LABEL's sequence class (TRAIN), so a
        # class-mix shift between TRAIN and TEST can be reasoned about in DESIGN §5.
        by_class = {}
        for name in cfgs:
            seqs = det[name][1]
            for sid, r in recs.items():
                cls = " > ".join(label_seq(r))
                hit = [p for p, _ in seqs[sid]] == list(label_seq(r))
                by_class.setdefault(cls, {}).setdefault(name, 0)
                by_class[cls][name] += hit
        print("sequence matches by label class (TRAIN):")
        for cls, v in sorted(by_class.items(), key=lambda kv: -seqc[kv[0]]):
            print(f"  {seqc[cls]:>2}  {cls:<70} " + "  ".join(f"{k} {v[k]}" for k in cfgs))
        res["by_class"] = by_class
        out[version] = {"n": len(recs), "kinds": dict(kinds), "sequences": dict(seqc),
                        "S_star": list(s_star), "INC_star": inc_star, "scores": res}
    (HERE / "constant_train.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
