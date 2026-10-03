"""Release v2.1, part A, passo 2 — compare the post-relabel measurement with passo 1.

Reads only the committed outputs of passo1/ and passo2/ (no detector run):
  * detection (sequence, phase starts, incipient end) identical on all 54 series;
  * which rows of scores_per_series_train.csv / boundaries_per_series_train.csv
    changed (expected: only the 3 re-labelled ids), with every changed column;
  * before/after table of the aggregates;
  * the prediction declared BEFORE the measurement, item by item (bate / não bate).
    The predicted values are written here as they were declared and not adjusted.

Writes comparison.txt next to this file. Run:
  conda run -n cyclophaser python -P research/release_v21/passo2/compare_passo1.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent / "passo1"
IDS = ("20150656", "20170409", "20170154")
DET_COLS = ("det_incipient_end_idx", "det_sequence", "det_phase_starts")
DET_BCOLS = ("det_start_idx_same_slot", "det_first_start_idx_same_phase", "sequence_match")


def rows(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    out, fails = [], []
    s1, s2 = rows(P1 / "scores_per_series_train.csv"), rows(HERE / "scores_per_series_train.csv")
    b1, b2 = rows(P1 / "boundaries_per_series_train.csv"), rows(HERE / "boundaries_per_series_train.csv")
    j1 = json.loads((P1 / "baseline_train.json").read_text())
    j2 = json.loads((HERE / "baseline_train.json").read_text())
    a1, a2 = j1["aggregate"], j2["aggregate"]

    out.append("RELEASE v2.1 — PART A — PASSO 2 — comparison with passo 1")
    out.append(f"passo 1: HEAD {j1['head']} manual_labels sha256 {j1['manual_labels_sha256']}")
    out.append(f"passo 2: HEAD {j2['head']} manual_labels sha256 {j2['manual_labels_sha256']}")
    same_setup = all(j1[k] == j2[k] for k in ("config", "config_sha256", "scorer",
                                               "cyclophaser_file", "environment"))
    out.append(f"same config/scorer/cyclophaser.__file__/environment: {same_setup}")
    if not same_setup:
        fails.append("setup differs")

    # detection
    d1 = {r["id"]: tuple(r[c] for c in DET_COLS) for r in s1}
    d2 = {r["id"]: tuple(r[c] for c in DET_COLS) for r in s2}
    bd1 = [(r["id"], r["k"], *(r[c] for c in DET_BCOLS)) for r in b1]
    bd2 = [(r["id"], r["k"], *(r[c] for c in DET_BCOLS)) for r in b2]
    det_diff = sorted(s for s in set(d1) | set(d2) if d1.get(s) != d2.get(s))
    out.append(f"\ndetection: {len(d2)} series; differing (sequence, starts, incipient end): "
               f"{det_diff or 'none'}; per-boundary detected fields identical: {bd1 == bd2}")
    if len(d1) != 54 or len(d2) != 54 or det_diff or bd1 != bd2:
        fails.append("detection changed")

    # csv rows
    out.append("\nscores_per_series_train.csv — rows that changed:")
    by1, by2 = {r["id"]: r for r in s1}, {r["id"]: r for r in s2}
    ch_s = sorted(s for s in by1 if by1[s] != by2.get(s))
    for s in ch_s:
        cols = [c for c in by1[s] if by1[s][c] != by2[s][c]]
        out.append(f"  {s}: " + "; ".join(f"{c} {by1[s][c]!r} -> {by2[s][c]!r}" for c in cols))
    out.append("boundaries_per_series_train.csv — rows that changed:")
    key = lambda r: (r["id"], r["k"])  # noqa: E731
    bb1, bb2 = {key(r): r for r in b1}, {key(r): r for r in b2}
    ch_b = sorted(k for k in bb1 if bb1[k] != bb2.get(k))
    for k in ch_b:
        cols = [c for c in bb1[k] if bb1[k][c] != bb2[k][c]]
        out.append(f"  {k[0]} k{k[1]}: " +
                   "; ".join(f"{c} {bb1[k][c]!r} -> {bb2[k][c]!r}" for c in cols))
    changed_ids = sorted(set(ch_s) | {k[0] for k in ch_b})
    out.append(f"ids with any changed CSV row: {changed_ids}")
    if set(bb1) != set(bb2) or set(by1) != set(by2) or not set(changed_ids) <= set(IDS):
        fails.append(f"other series changed: {sorted(set(changed_ids) - set(IDS))}")

    # aggregates
    def fmt(a):
        return {"H/B": f"{a['H']}/{a['B']}", "R/N0": f"{a['R']}/{a['N0']}",
                "C": f"{a['C']}/{a['C_den']}", "Q": f"{a['Q']}/{a['Q_den']}",
                "MAT": f"{a['MAT']}/{a['M']}", "false refusals": str(a["false_refusals"]),
                "ambiguous (refused)": f"{a['ambiguous']} ({a['ambiguous_refused']})",
                "boundaries hit/scored": str(a["boundaries_hit"]),
                "unsure excluded": str(a["boundaries_unsure"])}

    out.append("\naggregates, before (passo 1) -> after (passo 2):")
    for pop in ("original_real", "all_train", "synthetic", "batch_train"):
        f1, f2 = fmt(a1[pop]), fmt(a2[pop])
        out.append(f"  {pop}")
        for m in f1:
            mark = "" if f1[m] == f2[m] else "   *"
            out.append(f"    {m:<22} {f1[m]:>8} -> {f2[m]:<8}{mark}")

    def phase_sums(j, pop_ids):
        res = {}
        for b in j["per_boundary"]:
            if b["id"] in pop_ids and b["scored"]:
                r = res.setdefault(b["phase"], {"n": 0, "hit": 0, "sum_err": 0})
                r["n"] += 1
                r["hit"] += bool(b["hit"])
                r["sum_err"] += b["abs_error"]
        return res

    real = {r["id"] for r in s2 if r["population"] == "original_real"}
    ps1, ps2 = phase_sums(j1, real), phase_sums(j2, real)
    out.append("  per phase, original_real (sequence-matched, sure boundaries): n / hit / sum|err|")
    for ph in ps1:
        out.append(f"    {ph:<16} {ps1[ph]['n']}/{ps1[ph]['hit']}/{ps1[ph]['sum_err']} -> "
                   f"{ps2[ph]['n']}/{ps2[ph]['hit']}/{ps2[ph]['sum_err']}   "
                   f"(stage1_run MAE {a1['original_real']['per_phase'][ph]['mae']:.3f} -> "
                   f"{a2['original_real']['per_phase'][ph]['mae']:.3f})")
    # cross-check own sums against the scorer's per-phase numbers
    for ph in ps2:
        pp = a2["original_real"]["per_phase"][ph]
        assert pp["n"] == ps2[ph]["n"] and pp["n_hit"] == ps2[ph]["hit"], ph
        assert abs(pp["mae"] * pp["n"] - ps2[ph]["sum_err"]) < 1e-9, ph

    # prediction, as declared before the measurement
    out.append("\nprediction (declared before measuring; not adjusted):")
    R1, R2 = a1["original_real"], a2["original_real"]
    T1, T2 = a1["all_train"], a2["all_train"]
    bd = lambda j, s: {b["phase"]: b for b in j["per_boundary"] if b["id"] == s}  # noqa: E731

    def item(name, ok):
        out.append(f"  [{'bate' if ok else 'NÃO BATE'}] {name}")
        if not ok:
            fails.append(f"prediction: {name}")

    x1, x2 = by1["20150656"], by2["20150656"]
    score_cols = ("C", "Q", "MAT", "incipient_abs_error", "n_boundaries_scored",
                  "n_boundaries_hit", "boundary_abs_errors", "boundary_mae")
    item("20150656: nenhum escore muda", all(x1[c] == x2[c] for c in score_cols))

    x1, x2 = by1["20170409"], by2["20170409"]
    item("20170409: erro do decay 7 -> 4, continua erro (tolerância 3)",
         bd(j1, "20170409")["decay"]["abs_error"] == 7 and bd(j2, "20170409")["decay"]["abs_error"] == 4
         and bd(j2, "20170409")["decay"]["hit"] is False
         and bd(j2, "20170409")["decay"]["label_tolerance_idx"] == 3)
    item("20170409: fronteiras 1/3 inalterado",
         (x1["n_boundaries_hit"], x1["n_boundaries_scored"]) == ("1", "3")
         == (x2["n_boundaries_hit"], x2["n_boundaries_scored"]))
    item("20170409: MAE da série 4,0 -> 3,0", (x1["boundary_mae"], x2["boundary_mae"]) == ("4.0", "3.0"))
    item("20170409: MAT False -> True", (x1["MAT"], x2["MAT"]) == ("False", "True"))
    item("20170409: C e Q inalterados", (x1["C"], x1["Q"]) == (x2["C"], x2["Q"]))

    x1, x2 = by1["20170154"], by2["20170154"]
    item("20170154: sai de H e de C (C True -> None; H 8/17 -> 7/16 com B -1)",
         x1["C"] == "True" and x2["C"] == "" and R2["B"] == R1["B"] - 1 and R2["H"] == R1["H"] - 1
         and R2["C_den"] == R1["C_den"] - 1 and R2["C"] == R1["C"] - 1)
    item("20170154: ambíguos 2 -> 3, recusados continuam 1",
         (R1["ambiguous"], R2["ambiguous"], R1["ambiguous_refused"], R2["ambiguous_refused"])
         == (2, 3, 1, 1))
    item("20170154: Q, MAT e erros de fronteira inalterados",
         all(x1[c] == x2[c] for c in ("Q", "MAT", "n_boundaries_scored", "n_boundaries_hit",
                                      "boundary_abs_errors", "boundary_mae")))

    item("35 reais: H 8/17 -> 7/16", (R1["H"], R1["B"], R2["H"], R2["B"]) == (8, 17, 7, 16))
    item("35 reais: C 22/33 -> 21/32", (R1["C"], R1["C_den"], R2["C"], R2["C_den"]) == (22, 33, 21, 32))
    item("35 reais: Q 19/35 igual", (R1["Q"], R1["Q_den"], R2["Q"], R2["Q_den"]) == (19, 35, 19, 35))
    item("35 reais: MAT 27/33 -> 28/33", (R1["MAT"], R1["M"], R2["MAT"], R2["M"]) == (27, 33, 28, 33))
    item("35 reais: fronteiras 33/42 igual",
         R1["boundaries_hit"] == R2["boundaries_hit"] == "33/42")
    others_same = all(ps1[p] == ps2[p] for p in ps1 if p != "decay")
    item("35 reais: por fase, decay com mesmos acertos e soma de erros -3 (outras fases iguais)",
         ps1["decay"]["n"] == ps2["decay"]["n"] and ps1["decay"]["hit"] == ps2["decay"]["hit"]
         and ps2["decay"]["sum_err"] - ps1["decay"]["sum_err"] == -3 and others_same)

    item("54 de treino: H 19/30 -> 18/29", (T1["H"], T1["B"], T2["H"], T2["B"]) == (19, 30, 18, 29))
    item("54 de treino: C 39/52 -> 38/51", (T1["C"], T1["C_den"], T2["C"], T2["C_den"]) == (39, 52, 38, 51))
    item("54 de treino: Q 37/54 igual", (T1["Q"], T1["Q_den"], T2["Q"], T2["Q_den"]) == (37, 54, 37, 54))
    item("54 de treino: MAT 44/50 -> 45/50", (T1["MAT"], T1["M"], T2["MAT"], T2["M"]) == (44, 50, 45, 50))
    item("54 de treino: fronteiras 92/104 igual",
         T1["boundaries_hit"] == T2["boundaries_hit"] == "92/104")

    out.append(f"\nRESULT: {'PASS' if not fails else 'FAIL'}"
               f"{'' if not fails else ' — ' + '; '.join(fails)}")
    text = "\n".join(out) + "\n"
    (HERE / "comparison.txt").write_text(text)
    print(text)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
