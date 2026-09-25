"""Item 30, step 3c — census of the TRAIN series under params-14.

MEASUREMENT ONLY. Universe: the split's TRAIN (35 real + 12 synthetic) plus the
batch's TRAIN (7 swell tracks) — 42 real + 12 synthetic. Every TEST id is
excluded by id, and labels are read through `item30_core.train_labels`, which
drops non-train records before any field is touched.

Per series:

* the signal, `boundary > peak`;
* the blocks step 6 (H) erases, restricted to phases other than incipient;
* for labelled series, the label's intensification start and incipient end,
  each compared with the plateau boundary and the peak.

Writes census_train_params14.csv next to this file. It covers training series
only, all of which are in the repo.

Run: python research/labels/diagnostics/item30/census_train.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item30_core as core  # noqa: E402

lc = core.lc


def main() -> None:
    print("environment:", json.dumps(core.environment()))
    sets = core.split_sets()
    excl = core.excluded_ids()
    real = lc.load_real_series()
    synth, _names = lc.load_synthetic_series()
    batch = lc.load_batch_series()
    series = {k: v for k, v in {**real, **synth}.items() if k in sets["train"]}
    series |= {k: v for k, v in batch.items() if k in sets["batch_train"]}
    source = {k: ("synthetic" if k in synth else "real") for k in series}
    origin = {k: ("batch" if k in sets["batch_train"] else "split") for k in series}
    assert set(series).isdisjoint(excl)
    n_real = sum(v == "real" for v in source.values())
    assert (n_real, len(series) - n_real) == (42, 12), (n_real, len(series) - n_real)
    group = lc.read_split()["batches"][lc.SWELL_BATCH]["group"]
    labels = core.train_labels()
    pv, gp = core.load_config("params-14")

    rows = []
    for sid in sorted(series):
        r = core.run_series(series[sid], pv, gp)
        row = {"id": sid, "source": source[sid], "origin": origin[sid],
               "group": group.get(sid, ""), "n": r["n"], "boundary": r["boundary"],
               "peak": r["peak"], "signal": r["signal"], "symptom": r["symptom"],
               "pre": core.seq(r["pre"]), "final": core.seq(r["final"]),
               "erased_non_incipient": ";".join(f"{f}[{a}-{b}]" for f, a, b in r["erased"]
                                                if not f.startswith("incipient"))}
        rec = labels.get(sid)
        row["labelled"] = rec is not None
        if rec is not None:
            assert rec["series_sha256"] == lc.series_sha256(series[sid]), sid
            m = core.label_marks(rec)
            row |= m
            s = m["label_int_start"]
            row["label_int_start_lt_boundary"] = None if s is None else s < r["boundary"]
            row["label_int_start_lt_peak"] = None if s is None else s < r["peak"]
            e = m["label_incipient_end"]
            num = isinstance(e, int)
            row["label_inc_end_minus_boundary"] = e - r["boundary"] if num else None
            row["label_inc_end_minus_peak"] = e - r["peak"] if num else None
        rows.append(row)

    d = pd.DataFrame(rows).set_index("id")
    d.to_csv(HERE / "census_train_params14.csv")
    summarize(d)


def summarize(d: pd.DataFrame) -> None:
    er = d.erased_non_incipient.fillna("").astype(str).str.len() > 0
    for name, sub in (("split real (35)", d[(d.origin == "split") & (d.source == "real")]),
                      ("batch (7)", d[d.origin == "batch"]),
                      ("real train (42)", d[d.source == "real"]),
                      ("synthetic (12)", d[d.source == "synthetic"])):
        e = er[sub.index]
        print(f"\n{name}: n={len(sub)} labelled={int(sub.labelled.sum())} "
              f"signal={int(sub.signal.sum())} {sorted(sub.index[sub.signal])} | "
              f"H erases a non-incipient block: {int(e.sum())} | "
              f"erases intensification: {int(sub.erased_non_incipient.fillna('').str.contains('intensification').sum())} | "
              f"symptom: {int(sub.symptom.sum())}")
    for sid, row in d[(d.origin == "batch") | d.signal].iterrows():
        print(f"  {sid} {row.source} {row.origin} {row.group or '-':1} b={row.boundary} pk={row.peak} "
              f"signal={row.signal} | pre: {row.pre} | final: {row.final} | erased: {row.erased_non_incipient or '-'}"
              + (f" | label int_start={row.label_int_start} (<b {row.label_int_start_lt_boundary}, <pk {row.label_int_start_lt_peak}) "
                 f"inc_end={row.label_incipient_end} (−b {row.label_inc_end_minus_boundary}, −pk {row.label_inc_end_minus_peak}) "
                 f"seq: {row.label_seq}" if row.labelled else ""))


if __name__ == "__main__":
    main()
