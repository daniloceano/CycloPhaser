"""Release v2.1, part A, passo 1 — TRAIN baseline under the CURRENT labels.

Read-only with respect to the package and to `manual_labels.yaml`: this script
reads labels and runs the detector; it writes only into this folder.

What it measures
----------------
params-track (`research/labels/configs/cyclophaser_params-track.yaml`, sha256
asserted to be 5aa61f2d…) on every TRAIN series of `split.yaml`:
35 original real + 12 synthetic + 7 swell_item30 batch TRAIN = 54. No TEST id
(split or batch) is labelled-read or run: labels are filtered by TRAIN id first.

The scorer is front 31's, not a new one. `stage1_run_5075e49.py` is a verbatim
copy of `research/labels/diagnostics/item31/stage1_run.py` at its freeze commit
`5075e49` (git blob b6fae997…; removed from the tree by the clean-up `2912b79`,
still under the tag `archive/research-diagnostics-pre-cleanup`). The copy is
compared byte for byte with `git show 5075e49:<path>` at run time. Only its
definitions are imported — `main()` is never called — exactly as front 31's
`stage1_smoke_train.py` did on TRAIN:
`build_det` → `score_version` → per-series rows (C, Q, MAT) and aggregates (H/B,
R/N0, C, Q, MAT, false refusals, per-phase boundary numbers), all of which go
through `labels_core.score_labels` / `labels_core.score_phase_sequences`.

`score_version` scores three comparator slots (P15, DEF, CONST). Only P15 is
measured here; the DEF slot is filled with the params-track maps as an inert
placeholder so the frozen function runs unchanged, and DEF/CONST/V1–V5 are
neither saved nor reported.

Per-series boundary errors (not part of stage1_run's rows) are obtained by
calling the same `labels_core` scorers on ONE record at a time.

Outputs (this folder): baseline_train.txt, baseline_train.json,
scores_per_series_train.csv, boundaries_per_series_train.csv.

Run: conda run -n cyclophaser python -P research/release_v21/passo1/baseline_train.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXPECTED_BRANCH = "fix/relabel-recovery"
CONFIG = REPO / "research" / "labels" / "configs" / "cyclophaser_params-track.yaml"
CONFIG_SHA256 = "5aa61f2dec710029b46a47668812d14e6d552517b7bca8912a8e00fd130ccf04"
SCORER_COPY = HERE / "stage1_run_5075e49.py"
SCORER_SRC = ("5075e49", "research/labels/diagnostics/item31/stage1_run.py")
FOCUS = {"20150656": "residual", "20170409": "decay", "20170154": "incipient boundary (verdict)"}


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True,
                          check=True).stdout


# ── 0. environment: which cyclophaser is this, BEFORE anything else ─────────────
sys.path.insert(0, str(REPO))
import cyclophaser  # noqa: E402

CP_FILE = Path(cyclophaser.__file__).resolve()
print(f"cyclophaser.__file__ = {CP_FILE}")
assert CP_FILE.is_relative_to(REPO), f"cyclophaser resolves outside this checkout: {CP_FILE}"
assert Path(sys.prefix).name == "cyclophaser", f"sys.prefix = {sys.prefix}"
BRANCH = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
assert BRANCH == EXPECTED_BRANCH, f"checked out branch is {BRANCH}"

sys.path.insert(0, str(REPO / "research" / "labels" / "diagnostics" / "item31"))
sys.path.insert(0, str(REPO / "research" / "labels" / "diagnostics" / "item19"))
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402
from item19_core import MARGIN, pair_by_overlap  # noqa: E402

assert SCORER_COPY.read_text() == _git("show", f"{SCORER_SRC[0]}:{SCORER_SRC[1]}"), \
    "stage1_run_5075e49.py is not a verbatim copy of the frozen scorer"
import stage1_run_5075e49 as s1  # noqa: E402  (definitions only; main() is never called)

lc = core.lc


def boundary_rows(rec: dict, det_seq: list) -> list[dict]:
    """One row per labelled boundary k >= 1, scored by labels_core on this record alone."""
    sid = rec["id"]
    q = lc.score_phase_sequences([rec], {sid: det_seq})
    matched = q["n_sequence_match"] == 1
    det_norm = [(lc.normalize_phase(p), int(i)) for p, i in det_seq]
    rows = []
    for k in range(1, len(rec["phases"])):
        ph = rec["phases"][k]
        name = lc.normalize_phase(ph["phase"])
        same_slot = det_norm[k][1] if matched else None
        # first detected start of the same phase name, reported whatever the sequence
        first_named = next((i for p, i in det_norm if p == name), None)
        err = abs(same_slot - int(ph["start_idx"])) if same_slot is not None else None
        rows.append({
            "id": sid, "k": k, "phase": name, "label_start_idx": int(ph["start_idx"]),
            "label_tolerance_idx": int(ph["tolerance_idx"]), "label_unsure": bool(ph.get("unsure")),
            "sequence_match": matched,
            "det_start_idx_same_slot": same_slot,
            "det_first_start_idx_same_phase": first_named,
            "abs_error": err,
            "scored": matched and not ph.get("unsure"),
            "hit": (err <= int(ph["tolerance_idx"])) if (matched and not ph.get("unsure")) else None,
        })
    return rows


def main() -> None:
    env = core.assert_environment()
    head = _git("rev-parse", "HEAD").strip()
    dirty = _git("status", "--porcelain", "--untracked-files=no", "--",
                 "cyclophaser", "research/labels").strip()
    assert not dirty, f"tracked changes in cyclophaser/ or research/labels/:\n{dirty}"

    cfg_sha = hashlib.sha256(CONFIG.read_bytes()).hexdigest()
    assert cfg_sha == CONFIG_SHA256, cfg_sha
    labels_sha = hashlib.sha256((REPO / "research/labels/manual_labels.yaml").read_bytes()).hexdigest()
    pv, gp = core.ev.load_config(CONFIG)

    tr = core.train_series()                          # TRAIN only, asserted inside
    pops = {s: g for g, d in tr.items() for s in d}
    series = {s: v for d in tr.values() for s, v in d.items()}
    ids = sorted(series)
    assert len(ids) == 54 and set(ids).isdisjoint(core.test_ids())
    labels = {s: r for s, r in lc.read_labels().items() if s in set(ids)}   # by TRAIN id FIRST
    assert set(labels) == set(ids), sorted(set(ids) - set(labels))
    sha_ok = {s: lc.series_sha256(series[s]) == labels[s]["series_sha256"] for s in ids}
    legacy = sorted(s for s in ids if lc.is_legacy_record(labels[s]))
    adjud = sorted(s for s in ids if lc.is_adjudicated(labels[s]))
    bad_fields = s1.check_record_fields(labels)
    assert bad_fields == [], bad_fields

    maps = {s: core.run(series[s], pv, gp) for s in ids}
    det = s1.build_det(core, {"P15": maps, "DEF": maps}, ids)   # DEF slot: inert placeholder

    agg_by_pop, rows_all = {}, {}
    for pop in ("original_real", "synthetic", "batch_train", "all_train"):
        sub = {s: labels[s] for s in ids if pop == "all_train" or pops[s] == pop}
        res = s1.score_version(lc, sub, det, pair_by_overlap, MARGIN)["res"]["P15"]
        agg_by_pop[pop] = res["agg"]
        if pop == "all_train":
            rows_all = res["rows"]

    per_series, per_boundary = [], []
    for s in ids:
        r, x = labels[s], rows_all[s]
        inc = lc.score_labels([r], {s: det["P15"]["inc"][s]})
        brows = boundary_rows(r, det["P15"]["seq"][s])
        per_boundary += brows
        scored = [b for b in brows if b["scored"]]
        kind = r["verdict"]["kind"]
        per_series.append({
            "id": s, "population": pops[s], "series_sha256_ok": sha_ok[s],
            "label_verdict": kind,
            "label_incipient_end_idx": r["verdict"].get("incipient_end_idx"),
            "label_tolerance_idx": int(r["tolerance_idx"]),
            "label_sequence": " > ".join(s1.label_seq(lc, r)),
            "det_incipient_end_idx": x["det_inc"],
            "det_sequence": x["det_seq"],
            "det_phase_starts": " ".join(f"{p}@{i}" for p, i in det["P15"]["seq"][s]),
            "C": x["C"], "Q": x["Q"], "MAT": x["MAT"],
            "incipient_abs_error": inc["mae"] if kind == "boundary" else None,
            "n_boundaries_scored": len(scored),
            "n_boundaries_hit": sum(bool(b["hit"]) for b in scored),
            "boundary_abs_errors": ";".join(f"{b['phase']}:{b['abs_error']}" for b in scored),
            "boundary_mae": (sum(b["abs_error"] for b in scored) / len(scored)) if scored else None,
        })

    with open(HERE / "scores_per_series_train.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_series[0]))
        w.writeheader()
        w.writerows(per_series)
    with open(HERE / "boundaries_per_series_train.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_boundary[0]))
        w.writeheader()
        w.writerows(per_boundary)

    out = []
    out.append("RELEASE v2.1 — PART A — PASSO 1 — TRAIN baseline under CURRENT labels")
    out.append(f"cyclophaser.__file__: {CP_FILE}")
    out.append(f"environment: {json.dumps(env)}")
    out.append(f"branch {BRANCH} HEAD {head}")
    out.append(f"scorer: {SCORER_SRC[1]}@{SCORER_SRC[0]} (verbatim copy {SCORER_COPY.name}, "
               "definitions only)")
    out.append(f"config: {CONFIG.relative_to(REPO)} sha256 {cfg_sha}")
    out.append(f"manual_labels.yaml sha256 {labels_sha}")
    out.append(f"population: {len(ids)} TRAIN "
               f"({', '.join(f'{g} {len(d)}' for g, d in tr.items())}); no TEST id read")
    out.append(f"series_sha256 mismatches: {sorted(s for s in ids if not sha_ok[s]) or 'none'}")
    out.append(f"legacy records: {legacy or 'none'}; adjudicated records: {adjud or 'none'} "
               "(kept, as stage1_smoke_train.py kept every TRAIN record)")
    out.append("")
    out.append("aggregate (params-track):  H/B  R/N0  C/(B+N0)  Q/n  MAT/M  false-refusals  "
               "ambiguous(refused)  boundaries hit/scored  unsure-excluded")
    for pop, a in agg_by_pop.items():
        out.append(f"  {pop:<14} {a['H']}/{a['B']}  {a['R']}/{a['N0']}  {a['C']}/{a['C_den']}  "
                   f"{a['Q']}/{a['Q_den']}  {a['MAT']}/{a['M']}  {a['false_refusals']}  "
                   f"{a['ambiguous']}({a['ambiguous_refused']})  {a['boundaries_hit']}  "
                   f"{a['boundaries_unsure']}")
    out.append("")
    out.append("per-phase boundary numbers, original_real (sequence-matched series only):")
    for ph, pv_ in agg_by_pop["original_real"]["per_phase"].items():
        out.append(f"  {ph:<16} n {pv_['n']:>2} hit {pv_['n_hit']:>2} MAE "
                   f"{None if pv_['mae'] is None else round(pv_['mae'], 3)} worst {pv_['worst']}")
    out.append("")
    out.append("the three relabel series (CURRENT labels):")
    for s, what in FOCUS.items():
        row = next(p for p in per_series if p["id"] == s)
        out.append(f"  {s}  [{what}]")
        out.append(f"    label: verdict {row['label_verdict']} "
                   f"inc_end {row['label_incipient_end_idx']} ±{row['label_tolerance_idx']} | "
                   f"{row['label_sequence']}")
        out.append(f"    det:   inc_end {row['det_incipient_end_idx']} | {row['det_phase_starts']}")
        out.append(f"    C {row['C']}  Q {row['Q']}  MAT {row['MAT']}  "
                   f"incipient |err| {row['incipient_abs_error']}  boundaries "
                   f"{row['n_boundaries_hit']}/{row['n_boundaries_scored']} "
                   f"[{row['boundary_abs_errors']}] MAE {row['boundary_mae']}")
        for b in (b for b in per_boundary if b["id"] == s):
            out.append(f"      k{b['k']} {b['phase']:<16} label {b['label_start_idx']:>3} "
                       f"±{b['label_tolerance_idx']:<2} unsure {b['label_unsure']!s:<5} | det "
                       f"same-slot {b['det_start_idx_same_slot']}  first-{b['phase']} "
                       f"{b['det_first_start_idx_same_phase']} | |err| {b['abs_error']} "
                       f"scored {b['scored']} hit {b['hit']}")
    text = "\n".join(out) + "\n"
    (HERE / "baseline_train.txt").write_text(text)
    (HERE / "baseline_train.json").write_text(json.dumps(
        {"head": head, "branch": BRANCH, "cyclophaser_file": str(CP_FILE), "environment": env,
         "config": str(CONFIG.relative_to(REPO)), "config_sha256": cfg_sha,
         "manual_labels_sha256": labels_sha,
         "scorer": f"{SCORER_SRC[1]}@{SCORER_SRC[0]}",
         "aggregate": agg_by_pop, "per_series": per_series, "per_boundary": per_boundary},
        indent=1, default=str))
    print(text)


if __name__ == "__main__":
    main()
