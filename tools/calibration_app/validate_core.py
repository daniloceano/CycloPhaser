"""Pure machinery behind the Validate page — no Streamlit.

The Validate page (benchmark review, I2; developer key only) measures how
closely configurations agree with the manual labels of the TRAIN split. The
labels are one labeller's evidence, not a ground truth, and the page's numbers
are agreements with them. This module decides three things the page must not
get wrong, so they live here, where tests reach them without a browser:

* **Which tracks are offered, and which labels exist at all.** The test split
  is spent (CLAUDE.md). Its ids — the 16 of `split.yaml` and the test ids of
  the swell_item30 batch — are taken from the split FIRST, their series files
  are never opened (the loaders' `ids=`), and their labels are dropped from the
  label dictionary right after it is read, before anything else touches it:
  the rule the retired Benchmark page followed, applied here to every test id
  whether or not the batch is on. A label whose `series_sha256` does not match the series
  read from disk was written against other data; it is not used and its track
  is not offered.
* **Which block a number belongs to.** TRAIN and ADJUDICATED (the item-30
  counterfactual's own labels, which a configuration reproducing it would agree
  with by construction) are kept apart by `benchmark_core.metrics_by_split`,
  called unchanged. No test block exists: a test id never reaches it, and
  `agreement` raises if one ever did.
* **The instruments.** Both are benchmark_core's, called unchanged: the sequence
  instrument (`benchmark_core.SEQUENCE_INSTRUMENT`) and the mature instrument
  (`benchmark_core.MATURE_INSTRUMENT`). They have different definitions and are
  never added together (research/labels/README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import benchmark_core as bc  # noqa: E402
import labels_core as lc  # noqa: E402  (research/labels, via benchmark_core)

BATCH = lc.SWELL_BATCH
TRAIN, ADJUDICATED = "train", "adjudicated"


# ── the population ────────────────────────────────────────────────────────────
def spent_ids(split_doc: dict | None = None) -> frozenset[str]:
    """Every spent id: the split's test list and the batch's test ids."""
    doc = split_doc if split_doc is not None else lc.read_split()
    batch = lc.batch_membership(BATCH, doc)
    return frozenset(map(str, doc["test"])) | frozenset(
        s for s, m in batch.items() if m == "test")


def load_population(include_batch: bool) -> dict:
    """The labelled train tracks this page offers, read from disk.

    Returns:
        {"series": {id: Series}, "source": {id: "real"|"synthetic"},
         "batch_ids": [id, ...], "labels": {id: record},
         "adjudicated": [id, ...], "not_offered": {id: reason},
         "batch_error": str | None}

        `labels` holds exactly the offered ids; no test id is anywhere in it.
    """
    doc = lc.read_split()
    spent = spent_ids(doc)
    train = [str(s) for s in doc["train"]]
    # Labels first, test labels withheld before anything reads the dictionary.
    labels = {sid: rec for sid, rec in bc.labels_for_display().items()
              if sid not in spent}

    real = lc.load_real_series(ids=[s for s in train if s.isdigit()])
    synth, _names = lc.load_synthetic_series()
    synth = {s: v for s, v in synth.items() if s in set(train)}
    series = {**real, **synth}
    source = {**{s: "real" for s in real}, **{s: "synthetic" for s in synth}}

    batch_ids: list[str] = []
    batch_error = None
    if include_batch:
        membership = lc.batch_membership(BATCH, doc)
        wanted = [s for s, m in membership.items() if m == "train"]
        try:
            b = lc.load_batch_series(BATCH, doc, ids=wanted)
        except Exception as exc:
            batch_error = f"{type(exc).__name__}: {exc}"
        else:
            clash = sorted(set(b) & set(series))
            if clash:
                batch_error = f"batch ids already in the population: {clash}"
            else:
                series.update(b)
                source.update({s: "real" for s in b})
                batch_ids = sorted(b)

    offered: dict[str, pd.Series] = {}
    not_offered: dict[str, str] = {}
    for sid, ser in series.items():
        assert sid not in spent, sid                    # by construction
        rec = labels.get(sid)
        if rec is None:
            not_offered[sid] = "no manual label"
        elif rec.get("series_sha256") != lc.series_sha256(ser.values):
            not_offered[sid] = ("the label was written against different data "
                                "(series_sha256 does not match the file)")
        else:
            offered[sid] = ser
    labels = {sid: labels[sid] for sid in offered}
    return {
        "series": offered,
        "source": {s: source[s] for s in offered},
        "batch_ids": [s for s in batch_ids if s in offered],
        "labels": labels,
        "adjudicated": sorted(s for s, r in labels.items() if lc.is_adjudicated(r)),
        "not_offered": not_offered,
        "batch_error": batch_error,
    }


# ── cells, in benchmark_core's shape ──────────────────────────────────────────
def as_results(cells: dict[str, dict]) -> dict[str, dict]:
    """A column's cells ({id: {"error", "runs", ...}}) in the shape the
    instruments of benchmark_core read: `runs` and the `starts` derived from them."""
    out = {}
    for sid, c in cells.items():
        runs = None if c is None else c.get("runs")
        out[sid] = {"error": None if c is None else c.get("error"),
                    "runs": None if runs is None else [tuple(r) for r in runs],
                    "starts": None if runs is None else [(p, a) for p, a, _ in runs]}
    return out


# ── the two instruments, in two blocks ────────────────────────────────────────
def agreement(cells: dict[str, dict], labels: dict[str, dict], ids,
              adjudicated) -> dict:
    """Both instruments over the TRAIN and ADJUDICATED blocks of `ids`.

    `benchmark_core.metrics_by_split`, with every id given membership "train":
    the function itself moves the adjudicated ones into their own block. Its
    test block must come back empty; anything else raises.

    Returns:
        {"train": block, "adjudicated": block}; block = {"ids", "sequence",
        "mature"} as `metrics_by_split` returns them.
    """
    ids = [s for s in ids if s in labels]
    adj = set(adjudicated)
    assert all((s in adj) == lc.is_adjudicated(labels[s]) for s in ids)
    m = bc.metrics_by_split(as_results(cells), labels, ids,
                            {s: "train" for s in ids})
    if m["test"]["ids"]:
        raise AssertionError(f"a test block appeared: {m['test']['ids']}")
    return {TRAIN: m["train"], ADJUDICATED: m["adjudicated"]}


NOT_IN_SNAPSHOT = "not in this snapshot"


def snapshot_cell(snapshot: dict, sid: str) -> dict:
    """A published release's cell, read from its file (`benchmark_core.snapshot_series`).

    A track the release never ran on (the swell_item30 batch: snapshots cover the
    51 + 12 bundled series only, finding A7) is marked `missing`: it is neither a
    detection nor a failed one, and every count on the page says so apart.
    """
    r = bc.snapshot_series(snapshot, sid)
    if (snapshot.get("records") or {}).get(sid) is None:
        return {"error": NOT_IN_SNAPSHOT, "runs": None, "z": None, "missing": True}
    return {"error": r["error"], "runs": r["runs"], "z": None}


def missing(cells: dict[str, dict], ids) -> list[str]:
    """The ids of `ids` whose cell is `missing` (see `snapshot_cell`)."""
    return [s for s in ids if (cells.get(s) or {}).get("missing")]


def disagreements(cells: dict[str, dict], labels: dict[str, dict], ids) -> dict:
    """The tracks of `ids` on which one column disagrees with the label, per
    instrument, with the same definitions the instruments count by.

    Returns:
        {"failed": [id], "not_in_snapshot": [id], "sequence_differs": [id],
         "outside_tolerance": [(id, n outside, n scored)],
         "mature": [(id, d_start or None, d_end or None)]}
        `mature` lists the tracks whose label has a mature phase and whose
        detected mature is not paired within the margin (None: no pair).
    """
    res = as_results({s: cells.get(s) for s in ids})
    out = {"failed": [], "not_in_snapshot": [], "sequence_differs": [],
           "outside_tolerance": [], "mature": []}
    for sid in ids:
        rec, r = labels.get(sid), res.get(sid)
        if rec is None:
            continue
        if (cells.get(sid) or {}).get("missing"):
            out["not_in_snapshot"].append(sid)          # never a disagreement
            continue
        if r is None or r["runs"] is None:
            out["failed"].append(sid)
            continue
        note = track_note(cells[sid], rec)
        if note["sequence"] == "differs":
            out["sequence_differs"].append(sid)
        elif note["outside"]:
            out["outside_tolerance"].append((sid, note["outside"], note["scored"]))
        mat = note["mature"]
        if mat is not None and not mat["within"]:
            out["mature"].append((sid, mat["d_start"], mat["d_end"]))
    return out


def disagrees(per_column: list[dict], sid: str) -> bool:
    """True when `sid` is in any list of any column's `disagreements`."""
    for d in per_column:
        if sid in d["failed"] or sid in d["sequence_differs"]:
            return True
        if any(x[0] == sid for x in d["outside_tolerance"] + d["mature"]):
            return True
    return False


# ── one track ─────────────────────────────────────────────────────────────────
def track_note(cell: dict | None, rec: dict) -> dict:
    """What a cell says about one labelled track.

    Returns:
        {"sequence": "agrees"|"differs"|None (no phases),
         "outside": boundaries outside their tolerance (same sequence only),
         "scored": boundaries the sequence instrument compares,
         "mature": None (the label has no mature phase) or
                   {"d_start", "d_end", "within"} — offsets of the paired
                   detected mature block from the label's (None: no pair)}
    """
    r = as_results({rec["id"]: cell})[rec["id"]]
    note = {"sequence": None, "outside": 0, "scored": 0, "mature": None}
    if r["runs"] is None:
        return note
    # Exactly the comparison `labels_core.score_phase_sequences` makes.
    lab = lc.phase_sequence(rec)
    det = [(lc.normalize_phase(p), int(i)) for p, i in r["starts"]]
    same = [p for p, _ in lab] == [p for p, _ in det]
    note["sequence"] = "agrees" if same else "differs"
    if same:
        for k in range(1, len(lab)):
            ph = rec["phases"][k]
            if ph.get("unsure"):
                continue
            note["scored"] += 1
            if abs(det[k][1] - lab[k][1]) > int(ph["tolerance_idx"]):
                note["outside"] += 1
    mm = bc.mature_metrics({rec["id"]: r}, {rec["id"]: rec}, [rec["id"]])
    if mm["rows"]:
        row = mm["rows"][0]
        note["mature"] = {"d_start": row["d_start"], "d_end": row["d_end"],
                          "within": bool(row["hit"])}
    return note


def tolerance_spans(rec: dict) -> tuple:
    """((lo, hi, start, unsure), ...) for each boundary of a label but the first
    (which is 0 on both sides and never compared): start_idx ± tolerance_idx,
    clipped to the series."""
    n = int(rec["n_steps"])
    out = []
    for ph in rec["phases"][1:]:
        s, t = int(ph["start_idx"]), int(ph["tolerance_idx"])
        out.append((max(0, s - t), min(n - 1, s + t), s, bool(ph.get("unsure"))))
    return tuple(out)


def label_runs(rec: dict) -> tuple:
    """The label as ((phase, start, end_inclusive), ...)."""
    return tuple(bc.label_runs_for(rec))
