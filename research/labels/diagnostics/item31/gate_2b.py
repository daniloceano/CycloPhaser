"""Item 31, stage 2b — the equivalence gate of DESIGN.md §6, after the defaults moved.

CHECKPOINT branch `research/item31-stage2b-checkpoint`, pending Danilo's approval.
Predictions are DESIGN §6 (a21bca2) and the stage-2 brief; they are restated
below and compared, not chosen here.

EQ1  front_b's default digest over the 47 TRAIN ids — computed with the same
     layout (`p15_expected_digest.digest`, layout proven equal to front_b's at
     stage 0); front_b's own generator is run separately to APPEND its record.
     Predicted 3a6de265….
EQ2  the same layout over the 54 (47 + 7 batch TRAIN), no kwargs.
     Predicted 923e1a03…. Control: params-15 with
     incipient_plateau_spare_intensification=False passed explicitly (params-14
     no longer exists; stage 0 asserted it was exactly that) → predicted 3756392e….
EQ3  determine_periods(s) == G(s) with no arguments == G(s, params-15 explicit),
     element for element, where G(s; pv, gp) = get_periods(process_vorticity(
     DataFrame({'zeta': s}), **pv), **gp)['periods']. On: 54 TRAIN, example_file,
     16 split TEST, 3 batch TEST, 5 validation. TEST / validation / example_file:
     counts only.
EQ4  the OLD (2.0.0) defaults passed explicitly — the frozen table
     research/labels/defaults_2.0.0.json, never hand-typed — reproduce b500d2e0…
     on the 47.
EQ5  determine_periods(s) with no arguments emits no warning mentioning use_filter.

Declared changes vs 2.0.0 (TRAIN): final map 54/54; sequence 32 (25 real / 1
synthetic / 6 batch); incipient presence flips 24 — recomputed here from the
2.0.0 table vs the new defaults, per series.

Output: gate_2b.txt (via tee), gate_2b.json (TRAIN per-series table; other
populations as counts only).
Run: python -P research/labels/diagnostics/item31/gate_2b.py
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402
import p15_expected_digest as ped  # noqa: E402

lc, dp = core.lc, core.dp
sys.path.insert(0, str(core.LABELS))
import config_defaults as cdef  # noqa: E402

PRED = {"EQ1": "3a6de26501c6fed05091025480cacf7502fe2d7d0076ba8479a9ecca81703b99",
        "EQ2": "923e1a0389ae1fb627172564ea35063791523ae035d867b3a01d18a0546ac97a",
        "EQ2_control": "3756392e9b4ad26a33af33d93166118dd75616928cc0c9ce22d9be79a21c3e54",
        "EQ4": "b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5"}
DECLARED = {"final_map": 54, "sequence": 32,
            "sequence_by_group": {"original_real": 25, "synthetic": 1, "batch_train": 6},
            "incipient_presence": 24}


def G(values, pv=None, gp=None) -> list:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        v = dp.process_vorticity(pd.DataFrame({"zeta": values}), **(pv or {}))
        return dp.get_periods(v, **(gp or {}))["periods"].astype(object).tolist()


def D(values) -> tuple[list, list]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = dp.determine_periods(values)
    return res["periods"].astype(object).tolist(), [str(w.message) for w in caught]


def main() -> None:
    env = core.assert_environment()
    print("environment:", json.dumps(env))
    pv15, gp15 = core.load_config("params-15")
    pv15 = {**pv15, "use_filter": "auto"}
    old = cdef.defaults_2_0_0()
    pv_old, gp_old = old["filter_params"], old["phase_params"]
    out = {}

    g = core.train_series()
    t47 = {**g["original_real"], **g["synthetic"]}
    t54 = {**t47, **g["batch_train"]}
    got = {"EQ1": ped.digest(t47, {}, {}),
           "EQ2": ped.digest(t54, {}, {}),
           "EQ2_control": ped.digest(t54, pv15,
                                     {**gp15, "incipient_plateau_spare_intensification": False}),
           "EQ4": ped.digest(t47, pv_old, gp_old)}
    for k in PRED:
        out[k] = {"predicted": PRED[k][:8] + "…", "obtained": got[k][:8] + "…",
                  "match": got[k] == PRED[k]}
        print(f"{k:<12} predicted {PRED[k][:12]}…  obtained {got[k][:12]}…  "
              f"{'MATCH' if got[k] == PRED[k] else 'MISMATCH'}")

    # populations for EQ3 / EQ5 (TEST ids enter only as counts)
    sets = core.split_sets()
    real = lc.load_real_series()
    batch = lc.load_batch_series(lc.SWELL_BATCH)
    val = lc.load_batch_series(lc.VALIDATION_BATCH)
    from cyclophaser import example_file
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    pops = {
        "train_54": t54,
        "example_file": {"example": track["min_max_zeta_850"]},
        "test_16": {s: real[s] for s in sorted(sets["test"])},
        "batch_test_3": {s: batch[s] for s in sorted(sets["batch_test"])},
        "validation_5": dict(sorted(val.items())),
    }
    assert [len(p) for p in pops.values()] == [54, 1, 16, 3, 5]

    eq3, eq5, counts, rows = {}, {}, {}, []
    for name, pop in pops.items():
        ok3 = ok5 = 0
        c = {"n": len(pop), "final_map": 0, "sequence": 0, "incipient_presence": 0}
        for sid, v in pop.items():
            d, warns = D(v)
            g0, gx = G(v), G(v, pv15, gp15)
            ok3 += (d == g0 == gx)
            ok5 += not any("use_filter" in w for w in warns)
            o = G(v, pv_old, gp_old)                       # the 2.0.0 behaviour
            so, sn = core.sequence(o), core.sequence(g0)
            io, i_n = core.incipient_end(o), core.incipient_end(g0)
            c["final_map"] += o != g0
            c["sequence"] += so != sn
            c["incipient_presence"] += (io is None) != (i_n is None)
            if name == "train_54":
                grp = next(k for k, dd in g.items() if sid in dd)
                rows.append({"group": grp, "id": sid, "seq_2_0_0": " > ".join(so),
                             "seq_new": " > ".join(sn), "inc_2_0_0": io, "inc_new": i_n,
                             "map_changed": o != g0, "seq_changed": so != sn})
        eq3[name] = f"{ok3}/{len(pop)}"
        eq5[name] = f"{ok5}/{len(pop)}"
        counts[name] = c
    print("\nEQ3 determine_periods == G() == G(params-15):",
          ", ".join(f"{k} {v}" for k, v in eq3.items()))
    print("EQ5 no use_filter warning:", ", ".join(f"{k} {v}" for k, v in eq5.items()))

    by_group = {grp: sum(r["seq_changed"] for r in rows if r["group"] == grp)
                for grp in ("original_real", "synthetic", "batch_train")}
    tr = counts["train_54"]
    obtained = {"final_map": tr["final_map"], "sequence": tr["sequence"],
                "sequence_by_group": by_group, "incipient_presence": tr["incipient_presence"]}
    print(f"\nDeclared changes vs 2.0.0 (TRAIN): {DECLARED}\nObtained:                          "
          f"{obtained}\n  match: {obtained == DECLARED}")
    print("\nCounts only (vs 2.0.0 defaults): " + "; ".join(
        f"{k}: map {c['final_map']}/{c['n']}, sequence {c['sequence']}/{c['n']}, "
        f"incipient presence {c['incipient_presence']}/{c['n']}"
        for k, c in counts.items() if k != "train_54"))

    all_ok = (all(v["match"] for v in out.values())
              and all(a == b for a, b in ((v.split("/")[0], v.split("/")[1]) for v in eq3.values()))
              and all(a == b for a, b in ((v.split("/")[0], v.split("/")[1]) for v in eq5.values()))
              and obtained == DECLARED)
    print(f"\nGATE 2b (equivalence): {'PASS' if all_ok else 'FAIL'}")
    (HERE / "gate_2b.json").write_text(json.dumps(
        {"environment": env, "digests": out, "eq3": eq3, "eq5": eq5,
         "declared": DECLARED, "obtained": obtained,
         "counts_only": {k: c for k, c in counts.items() if k != "train_54"},
         "train_rows": rows, "pass": all_ok}, indent=2))


if __name__ == "__main__":
    main()
