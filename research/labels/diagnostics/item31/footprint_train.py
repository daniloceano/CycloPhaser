"""Item 31, stage 0, task 6 support — TRAIN footprint of "params-15 as default".

TRAIN only (35 real + 12 synthetic + 7 batch). No label is read. No TEST series
is loaded into the working dict (`item31_core.train_series`).

Three things, all mechanical:

A. GENERATOR AGREEMENT (pre-check for the stage-2 equivalence gate). For every
   TRAIN series, with params-15 passed EXPLICITLY (defaults untouched):
       G1 = get_periods(process_vorticity(df, **pv15), **gp15)['periods']
       G2 = determine_periods(series, **pv15, **gp15)['periods']
   must be identical. If they are not, the stage-2 gate cannot use either as the
   reference for the other.

B. BEHAVIOUR-ONLY EQUIVALENCES of param_table.md, checked on data: params-15 with
   `use_filter='auto'` instead of True, and with `incipient_smooth_window=5`,
   `incipient_smooth_polyorder=3` as int instead of 5.0/3.0, must give identical
   final maps on every TRAIN series.

C. FOOTPRINT vs the current defaults (version string 2.0.0 in setup.py): per
   group, how many TRAIN series change final map / sequence / incipient end
   between package defaults and params-15. Per-series lines are printed (TRAIN).

Outputs: footprint_train.txt (via tee), footprint_train.json.

Run: python -P research/labels/diagnostics/item31/footprint_train.py | tee .../footprint_train.txt
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

dp = core.dp


def run_dp(values, pv, gp) -> list:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = dp.determine_periods(values, **pv, **gp)
    return res["periods"].astype(object).tolist()


def main() -> None:
    env = core.assert_environment()
    print("environment:", json.dumps(env))
    pv15, gp15 = core.load_config("params-15")
    pvD, gpD = core.load_config(None)
    assert (pvD, gpD) == ({}, {})
    pv15_auto = {**pv15, "use_filter": "auto"}
    gp15_int = {**gp15, "incipient_smooth_window": int(gp15["incipient_smooth_window"]),
                "incipient_smooth_polyorder": int(gp15["incipient_smooth_polyorder"])}
    assert pv15["use_filter"] is True and isinstance(gp15["incipient_smooth_window"], float)

    groups = core.train_series()
    counts, rows = {}, []
    agreeA = agreeB_filter = agreeB_int = 0
    total = 0
    for g, series in groups.items():
        c = {"n": len(series), "final_map": 0, "sequence": 0, "incipient_end": 0,
             "incipient_presence": 0}
        for sid, v in series.items():
            total += 1
            g1 = core.run(v, pv15, gp15)
            agreeA += g1 == run_dp(v, pv15, gp15)
            agreeB_filter += g1 == core.run(v, pv15_auto, gp15)
            agreeB_int += g1 == core.run(v, pv15, gp15_int)
            d = core.run(v, pvD, gpD)
            sd, s15 = core.sequence(d), core.sequence(g1)
            idd, i15 = core.incipient_end(d), core.incipient_end(g1)
            r = {"group": g, "id": sid, "map": d != g1, "seq": sd != s15,
                 "inc": idd != i15, "presence": (idd is None) != (i15 is None),
                 "seq_default": " > ".join(sd), "seq_p15": " > ".join(s15),
                 "inc_default": idd, "inc_p15": i15}
            for k, key in (("final_map", "map"), ("sequence", "seq"),
                           ("incipient_end", "inc"), ("incipient_presence", "presence")):
                c[k] += r[key]
            rows.append(r)
        counts[g] = c

    print(f"\nA. generator agreement G1 == G2 (params-15 explicit): {agreeA}/{total}")
    print(f"B. use_filter True ≡ 'auto' on data: {agreeB_filter}/{total}; "
          f"smooth window/polyorder float ≡ int on data: {agreeB_int}/{total}")
    print("\nC. footprint, package defaults → params-15")
    print(" group           n  final map  sequence  incipient end  incipient presence")
    for g, c in counts.items():
        print(f" {g:<14} {c['n']:>3}  {c['final_map']:>9}  {c['sequence']:>8}  "
              f"{c['incipient_end']:>13}  {c['incipient_presence']:>18}")
    tot = {k: sum(c[k] for c in counts.values()) for k in next(iter(counts.values()))}
    print(f" {'TOTAL':<14} {tot['n']:>3}  {tot['final_map']:>9}  {tot['sequence']:>8}  "
          f"{tot['incipient_end']:>13}  {tot['incipient_presence']:>18}")
    print("\nper series (TRAIN), sequence default → params-15, incipient end:")
    for r in rows:
        flag = "SEQ" if r["seq"] else ("map" if r["map"] else "  =")
        print(f"  {flag:>3} {r['group']:<14} {r['id']:<10} inc {str(r['inc_default']):>4} → "
              f"{str(r['inc_p15']):<4} | {r['seq_default']}  ⇒  {r['seq_p15']}")
    (HERE / "footprint_train.json").write_text(json.dumps(
        {"environment": env,
         "generator_agreement": f"{agreeA}/{total}",
         "use_filter_true_equiv_auto": f"{agreeB_filter}/{total}",
         "smooth_float_equiv_int": f"{agreeB_int}/{total}",
         "counts": counts, "total": tot, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
