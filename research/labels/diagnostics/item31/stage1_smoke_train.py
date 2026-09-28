"""Item 31, stage 1 part A — TRAIN-only smoke test of stage1_run.py's scoring code.

Why: stage1_run.py is single-shot. Anything that crashes AFTER its lock burns the
run. So the code that runs after the lock — `build_det`, `score_version`,
`report` and the JSON dump — is exercised here, on TRAIN, BEFORE the freeze.

What this is NOT: it does not call `stage1_run.main()`, reads no TEST label, and
runs no TEST series. It imports stage1_run as a module (definitions only).

Population: the 35 real series of the original TRAIN split — the population
`constant_train.py` scored at stage 0. The scorer must reproduce those numbers
exactly (P15 / DEF / CONST: C, Q; P15 / DEF: MAT), under current and first-blind.

Output: stage1_smoke_train.txt. Asserts stage1_output.* do not exist, before
and after.

Run: python -P research/labels/diagnostics/item31/stage1_smoke_train.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402
import stage1_run as s1  # noqa: E402  (definitions only; main() is never called)

lc = core.lc
sys.path.insert(0, str(core.LABELS / "diagnostics" / "item19"))
from item19_core import MARGIN, pair_by_overlap  # noqa: E402

NAMES = {"P15": "params-15", "DEF": "defaults", "CONST": "constant"}


def main() -> None:
    assert not s1.OUT_TXT.exists() and not s1.OUT_JSON.exists()
    env = core.assert_environment()
    series = core.train_series()["original_real"]
    ids = sorted(series)
    assert len(ids) == 35 and set(ids).isdisjoint(core.test_ids())
    raw = {s: r for s, r in lc.read_labels().items() if s in set(ids)}     # by id FIRST
    versions = {"current": raw,
                "first-blind": {s: lc.first_blind_record(r) for s, r in raw.items()
                                if lc.first_blind_record(r) is not None}}
    for v, recs in versions.items():
        assert s1.check_record_fields(recs) == [], v

    cfg = {"P15": core.load_config("params-15"), "DEF": core.load_config(None),
           "P14": core.load_config("params-14")}
    maps = {n: {s: core.run(series[s], *cfg[n]) for s in ids} for n in cfg}
    det = s1.build_det(core, maps, ids)
    p14_vs_p15 = sorted(s for s in ids if maps["P14"][s] != maps["P15"][s])

    cj = json.loads((HERE / "constant_train.json").read_text())
    results, lines = {}, []
    for v, recs in versions.items():
        results[v] = s1.score_version(lc, recs, det, pair_by_overlap, MARGIN)
        for short, long_ in NAMES.items():
            got = results[v]["res"][short]["agg"]
            ref = cj[v]["scores"][long_]
            assert got["C"] == ref["incipient_correct"], (v, short, got["C"], ref)
            assert got["Q"] == ref["sequence_match"], (v, short, got["Q"], ref)
            if short != "CONST":
                assert got["MAT"] == ref["mature_hits"] and got["M"] == ref["n_mature"], (v, short)
            lines.append(f"{v:<12} {short:<5} C {got['C']}/{got['C_den']}  Q {got['Q']}/"
                         f"{got['Q_den']}"
                         + (f"  MAT {got['MAT']}/{got['M']}" if short != "CONST" else "")
                         + "  == constant_train.json: True")

    captured = []
    overall, failed = s1.report(captured.append, lc, versions, results, ids, p14_vs_p15)
    doc = {"results": {v: {"V": R["V"], "pass": R["pass"], "discordant": R["discordant"],
                           "aggregate": {n: R["res"][n]["agg"] for n in R["res"]},
                           "rows": {n: R["res"][n]["rows"] for n in R["res"]}}
                       for v, R in results.items()},
           "verdict": "PASS" if overall else "FAIL", "failed": failed}
    json.dumps(doc, default=str)                     # the JSON dump must not raise

    text = ["Item 31 — stage-1 scorer smoke test on TRAIN (35 real, original split)",
            f"environment: {json.dumps(env)}",
            "stage1_run.main() NOT called; no TEST label read; no TEST series run.",
            "", "scorer reproduces constant_train.json (stage 0):", *lines,
            "", f"report(): {len(captured)} lines produced without error; JSON dump OK",
            f"P14 ≠ P15 final maps on these 35: {len(p14_vs_p15)} (stage 0 said 0)",
            "(The TRAIN verdict line printed by report() is not a result of anything: "
            "the criterion is defined on the 16 TEST series only.)"]
    assert len(p14_vs_p15) == 0
    assert not s1.OUT_TXT.exists() and not s1.OUT_JSON.exists()
    text.append("stage1_output.txt / .json: absent before and after — OK")
    (HERE / "stage1_smoke_train.txt").write_text("\n".join(text) + "\n")
    print("\n".join(text))


if __name__ == "__main__":
    main()
