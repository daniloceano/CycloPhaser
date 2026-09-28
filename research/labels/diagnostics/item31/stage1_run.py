"""Item 31, stage 1 — THE single scoring run of params-15 against the 16 TEST labels.

*** RUN ONCE. *** The criterion is DESIGN.md §5 (structure frozen in e42da8b,
decisions in §8, framing in §5.2). This script implements it; it does not
choose anything. Stage 1 is NOT out-of-sample validation (§5.2): a PASS is weak
evidence, a FAIL is strong evidence.

Single-execution lock
---------------------
If `stage1_output.txt` or `stage1_output.json` exists, the script aborts BEFORE
doing anything else — no label is read, no detector runs, nothing is scored.
The .txt is created EXCLUSIVELY (mode 'x') immediately before the first TEST
series is processed, and everything after that is appended to it. A run that
crashes after that point therefore still blocks a second run: whether the
crashed run's partial output counts is a decision for the maintainer, not for
a retry. Every check that reads no test output (environment, git state, the
DEF digest, configs, the label census) runs BEFORE the lock, so a failure there
leaves nothing behind and the run can be repeated once fixed.

What runs, in one process, at one commit
----------------------------------------
* Population: the 16 ids under `test:` in split.yaml (Option A, §8.1). The 3
  batch TEST ids are NOT read. The 16 labels must reproduce the stage-0 census
  (n 16, B 9, N0 6, M 15, K* 5; first-blind identical to current) or the run
  aborts before the lock: the reachability arithmetic of §5.1 assumes them.
* Comparators (§8.2):
    P15   — research/labels/configs/cyclophaser_params-15.yaml via
            evaluate_against_labels.load_config (the evaluator's own loader);
    DEF   — package defaults. Before DEF is scored, the front_b default digest
            over the 47 TRAIN ids must still be b500d2e0… (asserted);
    CONST — S* = intensification > mature > decay, INC* = no incipient
            (constant_train.txt; asserted equal to its JSON).
  params-14 runs ONLY for the mechanical count "final map P14 ≠ P15 on the 16",
  outside the verdict.
* Both label versions, `current` and `first-blind`, in the same process.

Metrics (§5): C = H + R (incipient decisions correct, over B + N0),
Q = full sequence (over n), MAT = first labelled mature paired by
item19_core.pair_by_overlap within 6 at both ends (over M; P15 and DEF only).

Verdict (§5), per label version:
    V1 C(P15) > C(DEF)   V2 Q(P15) > Q(DEF)   V3 C(P15) > C(CONST)
    V4 Q(P15) > Q(CONST) V5 MAT(P15) >= MAT(DEF)
PASS iff V1–V5 all hold under BOTH versions; otherwise FAIL, naming every
failed condition.

Also reported (outside the verdict): per-series table, false refusals,
ambiguous labels the detector refused, discordant pairs P15 vs DEF for C and Q,
the evaluator's per-phase boundary numbers, and the P14-vs-P15 count.

Outputs: stage1_output.txt, stage1_output.json (both in this folder).
Run (once): python -P research/labels/diagnostics/item31/stage1_run.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_TXT = HERE / "stage1_output.txt"
OUT_JSON = HERE / "stage1_output.json"

N_EXPECTED = {"n": 16, "B": 9, "N0": 6, "M": 15, "K_star": 5}      # test_label_census.txt
FRONT_B_DEFAULT = "b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5"
S_STAR = ("intensification", "mature", "decay")


def _abort(msg: str, code: int = 2):
    print(f"ABORT: {msg}", file=sys.stderr)
    raise SystemExit(code)


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=HERE.parents[3], capture_output=True,
                          text=True, check=True).stdout.strip()


class Out:
    """Lines go to stdout and, once the lock is taken, to stage1_output.txt."""

    def __init__(self):
        self.pending, self.fh = [], None

    def __call__(self, line: str = "") -> None:
        print(line)
        if self.fh is None:
            self.pending.append(line)
        else:
            self.fh.write(line + "\n")
            self.fh.flush()

    def take_lock(self) -> None:
        self.fh = open(OUT_TXT, "x")         # exclusive: fails if another run got here
        for ln in self.pending:
            self.fh.write(ln + "\n")
        self.fh.flush()
        self.pending = []


# ── scoring helpers (module level so the TRAIN smoke test can import them; ─────
#    importing this module runs no scoring — only main() does) ─────────────────

def label_seq(lc, r) -> tuple:
    return tuple(p for p, _ in lc.phase_sequence(r))


def census(lc, recs: dict) -> dict:
    k = [r["verdict"]["kind"] for r in recs.values()]
    return {"n": len(recs), "B": k.count("boundary"), "N0": k.count("none"),
            "M": sum(any(lc.normalize_phase(p["phase"]) == "mature" for p in r["phases"])
                     for r in recs.values()),
            "K_star": sum(label_seq(lc, r) == S_STAR for r in recs.values())}


REQUIRED_KEYS = ("verdict", "phases", "tolerance_idx", "n_steps", "id")


def check_record_fields(recs: dict) -> list:
    """Missing fields the scorer reads — checked BEFORE the lock, never after."""
    bad = []
    for s, r in recs.items():
        miss = [k for k in REQUIRED_KEYS if k not in r]
        if r.get("verdict", {}).get("kind") == "boundary" and \
                "incipient_end_idx" not in r.get("verdict", {}):
            miss.append("verdict.incipient_end_idx")
        if miss:
            bad.append((s, miss))
    return bad


def phase_runs(lc, periods) -> list:
    o, prev, st = [], None, 0
    labs = [lc.normalize_phase(str(x)) for x in periods]
    for i, x in enumerate(labs):
        if x != prev:
            if i:
                o.append((prev, st, i - 1))
            prev, st = x, i
    if labs:
        o.append((prev, st, len(labs) - 1))
    return o


def build_det(core, maps: dict, ids) -> dict:
    """Detector outputs → the three views the metrics read; CONST added."""
    import pandas as pd
    det = {}
    for name in ("P15", "DEF"):
        det[name] = {
            "inc": {s: core.incipient_end(maps[name][s]) for s in ids},
            "seq": {s: core.ev.detected_phase_starts(pd.Series(maps[name][s], dtype=object))
                    for s in ids},
            "runs": {s: phase_runs(core.lc, maps[name][s]) for s in ids}}
    det["CONST"] = {"inc": {s: None for s in ids},
                    "seq": {s: [(p, i) for i, p in enumerate(S_STAR)] for s in ids},
                    "runs": None}
    return det


def per_series(lc, recs: dict, det: dict, name: str, pair_by_overlap, margin) -> dict:
    rows = {}
    for s, r in recs.items():
        kind = r["verdict"]["kind"]
        di = det[name]["inc"][s]
        if kind == "boundary":
            c_ok = di is not None and abs(di - r["verdict"]["incipient_end_idx"]) <= int(
                r["tolerance_idx"])
        elif kind == "none":
            c_ok = di is None
        else:
            c_ok = None
        q_ok = [lc.normalize_phase(p) for p, _ in det[name]["seq"][s]] == list(label_seq(lc, r))
        mat = None
        if det[name]["runs"] is not None:
            ph = r["phases"]
            lab = [(p["start_idx"], (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph)
                    else r["n_steps"] - 1)
                   for k, p in enumerate(ph) if lc.normalize_phase(p["phase"]) == "mature"]
            if lab:
                dm = [(a, b) for p, a, b in det[name]["runs"][s] if p == "mature"]
                paired, _ = pair_by_overlap(dm, lab[0])
                mat = bool(paired is not None and abs(paired[0] - lab[0][0]) <= margin
                           and abs(paired[1] - lab[0][1]) <= margin)
        rows[s] = {"C": c_ok, "Q": q_ok, "MAT": mat, "det_inc": di,
                   "det_seq": " > ".join(p for p, _ in det[name]["seq"][s])}
    return rows


def score_version(lc, recs: dict, det: dict, pair_by_overlap, margin) -> dict:
    """All comparators on one label version: aggregates, rows, V1–V5, discordant pairs."""
    res = {}
    for name in ("P15", "DEF", "CONST"):
        rows = per_series(lc, recs, det, name, pair_by_overlap, margin)
        m = lc.score_labels(list(recs.values()), det[name]["inc"])
        q = lc.score_phase_sequences(list(recs.values()), det[name]["seq"])
        agg = {"H": m["n_hit"], "B": m["n_boundary"], "R": m["n_none_agreed"],
               "N0": m["n_none"], "C": m["n_hit"] + m["n_none_agreed"],
               "C_den": m["n_boundary"] + m["n_none"],
               "false_refusals": m["detector_missing_on_boundary"],
               "ambiguous": m["n_ambiguous"],
               "ambiguous_refused": m["n_ambiguous_detector_none"],
               "mae": m["mae"], "worst": m["worst"],
               "Q": q["n_sequence_match"], "Q_den": q["n_series"]}
        # the per-series rows must reproduce the evaluator's own counts
        assert agg["C"] == sum(x["C"] is True for x in rows.values()), name
        assert agg["Q"] == sum(x["Q"] for x in rows.values()), name
        if name != "CONST":
            mats = [x["MAT"] for x in rows.values() if x["MAT"] is not None]
            agg["MAT"], agg["M"] = sum(mats), len(mats)
            agg["per_phase"] = q["per_phase"]
            agg["boundaries_hit"] = f"{q['n_boundaries_hit']}/{q['n_boundaries']}"
            agg["boundaries_unsure"] = q["n_boundaries_unsure"]
        res[name] = {"agg": agg, "rows": rows}
    P, D, K = (res[x]["agg"] for x in ("P15", "DEF", "CONST"))
    V = {"V1": P["C"] > D["C"], "V2": P["Q"] > D["Q"], "V3": P["C"] > K["C"],
         "V4": P["Q"] > K["Q"], "V5": P["MAT"] >= D["MAT"]}
    disc = {}
    for met in ("C", "Q"):
        pr, dr = res["P15"]["rows"], res["DEF"]["rows"]
        ids = [s for s in recs if pr[s][met] is not None]
        disc[met] = {"P15_right_DEF_wrong": sum(bool(pr[s][met] and not dr[s][met]) for s in ids),
                     "DEF_right_P15_wrong": sum(bool(dr[s][met] and not pr[s][met]) for s in ids)}
    return {"res": res, "V": V, "discordant": disc, "pass": all(V.values())}


def report(out, lc, versions: dict, results: dict, ids, p14_vs_p15) -> tuple:
    """Section 8 of main(): every printed line of the result. Returns (overall, failed)."""
    ok = lambda x: "—" if x is None else ("✓" if x else "✗")   # noqa: E731
    for v, R in results.items():
        recs, res = versions[v], R["res"]
        out(f"\n{'─' * 78}\nLABELS: {v}   (n = {len(recs)})\n{'─' * 78}")
        out("per series:  id | label kind (end±tol) | label sequence\n"
            "             P15: inc C Q MAT seq | DEF: inc C Q MAT seq | CONST: C Q")
        for s in ids:
            r = recs[s]
            k = r["verdict"]["kind"]
            lab = (f"{k} {r['verdict']['incipient_end_idx']}±{r['tolerance_idx']}"
                   if k == "boundary" else k)
            out(f"  {s} | {lab} | {' > '.join(label_seq(lc, r))}")
            for name in ("P15", "DEF"):
                x = res[name]["rows"][s]
                out(f"      {name:<4} inc {str(x['det_inc']):>4}  C {ok(x['C'])}  Q {ok(x['Q'])}  "
                    f"MAT {ok(x['MAT'])}  {x['det_seq']}")
            x = res["CONST"]["rows"][s]
            out(f"      CONST            C {ok(x['C'])}  Q {ok(x['Q'])}")
        out("\naggregate:")
        out("  comparator   H/B    R/N0   C/(B+N0)  Q/n     MAT/M   false-refusals  "
            "ambiguous-refused")
        for name in ("P15", "DEF", "CONST"):
            a = res[name]["agg"]
            mat = f"{a['MAT']}/{a['M']}" if "MAT" in a else "—"
            out(f"  {name:<10} {a['H']:>2}/{a['B']:<2}  {a['R']:>2}/{a['N0']:<2}  "
                f"{a['C']:>3}/{a['C_den']:<4}  {a['Q']:>2}/{a['Q_den']:<3}  {mat:>6}  "
                f"{a['false_refusals']:>14}  {a['ambiguous_refused']}/{a['ambiguous']}")
        out("\nevaluator per-phase boundary numbers (sequence-matched series only; "
            "denominators differ by comparator — reported, not in the verdict):")
        for name in ("P15", "DEF"):
            a = res[name]["agg"]
            out(f"  {name}: boundaries {a['boundaries_hit']} within own margin; "
                f"unsure excluded {a['boundaries_unsure']}")
            for ph, pv in a["per_phase"].items():
                out(f"      {ph:<16} n {pv['n']:>2}  hit {pv['n_hit']:>2}  MAE "
                    f"{pv['mae'] if pv['mae'] is None else round(pv['mae'], 2)}  worst {pv['worst']}")
        out("\ndiscordant pairs P15 vs DEF:")
        for met, dd in R["discordant"].items():
            out(f"  {met}: P15 right & DEF wrong {dd['P15_right_DEF_wrong']}; "
                f"DEF right & P15 wrong {dd['DEF_right_P15_wrong']}")
        P, D, K = (res[x]["agg"] for x in ("P15", "DEF", "CONST"))
        out("\nconditions:")
        rows = [("V1", f"C(P15) {P['C']} > C(DEF) {D['C']}"),
                ("V2", f"Q(P15) {P['Q']} > Q(DEF) {D['Q']}"),
                ("V3", f"C(P15) {P['C']} > C(CONST) {K['C']}"),
                ("V4", f"Q(P15) {P['Q']} > Q(CONST) {K['Q']}"),
                ("V5", f"MAT(P15) {P['MAT']} >= MAT(DEF) {D['MAT']}")]
        for vid, txt in rows:
            out(f"  {vid}  {txt:<34} {'PASS' if R['V'][vid] else 'FAIL'}")
        out(f"  {v}: {'PASS' if R['pass'] else 'FAIL'}")

    overall = all(R["pass"] for R in results.values())
    failed = sorted({f"{vid} ({v})" for v, R in results.items()
                     for vid, x in R["V"].items() if not x})
    out(f"\n{'=' * 78}")
    out(f"mechanical count (outside the verdict): final map P14 ≠ P15 on "
        f"{len(p14_vs_p15)}/{len(ids)}" + (f": {', '.join(p14_vs_p15)}" if p14_vs_p15 else ""))
    out(f"VERDICT: {'PASS' if overall else 'FAIL'}"
        + ("" if overall else f" — failed: {', '.join(failed)}"))
    out("Reading (DESIGN §5.2): not out-of-sample validation; PASS = weak evidence, "
        "FAIL = strong evidence.")
    out("=" * 78)

    return overall, failed


def main() -> None:
    # ── 0. single-execution lock: checked before ANYTHING else ─────────────────
    if OUT_TXT.exists() or OUT_JSON.exists():
        _abort(f"{OUT_TXT.name} / {OUT_JSON.name} already exists — stage 1 has run. "
               "Nothing was read or scored.")

    sys.path.insert(0, str(HERE))
    import item31_core as core
    import p15_expected_digest as ped
    lc = core.lc
    sys.path.insert(0, str(core.LABELS / "diagnostics" / "item19"))
    from item19_core import MARGIN, pair_by_overlap

    out = Out()
    out("=" * 78)
    out("ITEM 31 — STAGE 1 — single scoring run (DESIGN.md §5, §8)")
    out("=" * 78)

    # ── 1. environment and git state (no test data) ────────────────────────────
    env = core.assert_environment()
    head = _git("rev-parse", "HEAD")
    me = Path(__file__).resolve().relative_to(core.REPO)
    design = me.parent / "DESIGN.md"
    dirty = _git("status", "--porcelain", "--untracked-files=no", "--",
                 "cyclophaser", "research/labels", "tools/calibration_app")
    if dirty:
        _abort(f"tracked changes present — the run must be one commit:\n{dirty}")
    if subprocess.run(["git", "ls-files", "--error-unmatch", str(me)], cwd=core.REPO,
                      capture_output=True).returncode:
        _abort(f"{me} is not committed")
    freeze = {"stage1_run.py": _git("log", "-1", "--format=%H", "--", str(me)),
              "DESIGN.md": _git("log", "-1", "--format=%H", "--", str(design))}
    diff_cp = _git("diff", "--stat", "develop-v2.1", "--", "cyclophaser")
    out(f"environment: {json.dumps(env)}")
    out(f"HEAD: {head}")
    out(f"last commit touching stage1_run.py: {freeze['stage1_run.py']}")
    out(f"last commit touching DESIGN.md:     {freeze['DESIGN.md']}")
    out(f"cyclophaser/ diff vs develop-v2.1: {'EMPTY' if not diff_cp else diff_cp}")

    # ── 2. DEF is the current default behaviour (TRAIN only) ───────────────────
    tr = core.train_series()
    train47 = {**tr["original_real"], **tr["synthetic"]}
    tlab = {s: r for s, r in lc.read_labels().items() if s in train47}
    assert all(lc.series_sha256(v) == tlab[s]["series_sha256"] for s, v in train47.items())
    d = ped.digest(train47, {}, {})
    if d != FRONT_B_DEFAULT:
        _abort(f"front_b default digest is {d}, not b500d2e0… — DEF is not the "
               "default behaviour the design froze")
    out(f"front_b default digest (47 TRAIN, package defaults) = {d}  == b500d2e0…: True")

    # ── 3. configs ────────────────────────────────────────────────────────────
    cfg = {"P15": core.load_config("params-15"), "DEF": core.load_config(None),
           "P14": core.load_config("params-14")}
    assert cfg["DEF"] == ({}, {})
    assert cfg["P14"][0] == cfg["P15"][0]
    assert cfg["P15"][1] == {**cfg["P14"][1], "incipient_plateau_spare_intensification": True}
    for name in ("params-15", "params-14"):
        h = hashlib.sha256(core.config_path(name).read_bytes()).hexdigest()
        out(f"config {name}: {core.config_path(name).relative_to(core.REPO)} sha256 {h}")
    cj = json.loads((HERE / "constant_train.json").read_text())
    assert tuple(cj["current"]["S_star"]) == S_STAR and cj["current"]["INC_star"] is None
    assert tuple(cj["first-blind"]["S_star"]) == S_STAR and cj["first-blind"]["INC_star"] is None
    out(f"CONST: S* = {' > '.join(S_STAR)}, INC* = no incipient (constant_train.json)")

    # ── 4. population and label census re-check (labels only, before the lock) ─
    sets = core.split_sets()
    test16 = sorted(sets["test"])
    assert len(test16) == 16 and set(test16).isdisjoint(sets["batch_test"])
    raw = {s: r for s, r in lc.read_labels().items() if s in set(test16)}   # by id FIRST
    real = lc.load_real_series()
    series = {s: real[s] for s in test16}
    usable = {s: r for s, r in raw.items()
              if lc.series_sha256(series[s]) == r.get("series_sha256")
              and not lc.is_legacy_record(r) and not lc.is_adjudicated(r)}
    versions = {"current": usable,
                "first-blind": {s: lc.first_blind_record(r) for s, r in usable.items()
                                if lc.first_blind_record(r) is not None}}

    for v, recs in versions.items():
        bad = check_record_fields(recs)
        if bad:
            _abort(f"{v}: label records miss fields the scorer reads: {bad}")
        c = census(lc, recs)
        if c != N_EXPECTED:
            _abort(f"{v} labels no longer match the stage-0 census: {c} != {N_EXPECTED}")
    out(f"population: the 16 split TEST ids (Option A); census re-check {N_EXPECTED} "
        "under current AND first-blind: OK")

    # ── 5. THE LOCK — from here on, test output exists ────────────────────────
    out.take_lock()
    out(f"lock taken: {OUT_TXT.name} created exclusively; a second run will abort.")

    # ── 6. detector runs on the 16 ────────────────────────────────────────────
    maps = {name: {s: core.run(series[s], *cfg[name]) for s in test16} for name in cfg}

    det = build_det(core, maps, test16)
    p14_vs_p15 = sorted(s for s in test16 if maps["P14"][s] != maps["P15"][s])

    # ── 7. scoring, per label version ─────────────────────────────────────────
    results = {}
    for v, recs in versions.items():
        results[v] = score_version(lc, recs, det, pair_by_overlap, MARGIN)
        assert results[v]["res"]["CONST"]["agg"]["C"] == N_EXPECTED["N0"]
        assert results[v]["res"]["CONST"]["agg"]["Q"] == N_EXPECTED["K_star"]

    # ── 8. report ─────────────────────────────────────────────────────────────
    overall, failed = report(out, lc, versions, results, test16, p14_vs_p15)

    doc = {"environment": env, "head": head, "freeze": freeze, "front_b_default_digest": d,
           "population": test16, "p14_vs_p15_changed": p14_vs_p15,
           "results": {v: {"V": R["V"], "pass": R["pass"], "discordant": R["discordant"],
                           "aggregate": {n: R["res"][n]["agg"] for n in R["res"]},
                           "rows": {n: R["res"][n]["rows"] for n in R["res"]}}
                       for v, R in results.items()},
           "verdict": "PASS" if overall else "FAIL", "failed": failed}
    with open(OUT_JSON, "x") as fh:
        json.dump(doc, fh, indent=2, default=str)
    out.fh.close()


if __name__ == "__main__":
    main()
