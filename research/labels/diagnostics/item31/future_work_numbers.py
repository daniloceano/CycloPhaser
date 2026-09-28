"""Item 31 — every number cited in docs/future_work.md item 31, regenerated.

Nothing here is typed from a brief: each figure is read from a committed output
of this front (param_table.json, reachability_train.json, test_label_census.json,
constant_train.json, exposure_table.json, stage1_output.json, recovery_table.json,
stale_scripts.json, gate_2b.json, fix_use_filter_false_*.json,
sidebar_table_2c.json, suite_*.txt), or measured here (defect I under the
current defaults). The item-31 entry of future_work.md cites this file's output.

Defect I (item 8(d)): sign(z_raw[1] - z_raw[0]) != sign(z[1] - z[0]), with z the
`z` column get_periods returns. Measured here under the CURRENT package defaults
(boundary_padding='edge' is now the default) over the 51 real tracks and the
35 real TRAIN tracks. Mechanical, no label read.

Output: future_work_numbers.json, printed.
Run: python -P research/labels/diagnostics/item31/future_work_numbers.py
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

J = lambda name: json.loads((HERE / name).read_text())  # noqa: E731


def suite(name: str) -> dict:
    t = (HERE / name).read_text()
    g = lambda w: int(m.group(1)) if (m := re.search(rf"(\d+) {w}", t)) else 0  # noqa: E731
    return {"passed": g("passed"), "failed": g("failed")}


def defect_i() -> dict:
    lc = core.lc
    real = lc.load_real_series()
    train = set(core.split_sets()["train"])
    members = []
    for sid, s in sorted(real.items()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = core.dp.get_periods(core.dp.process_vorticity(pd.DataFrame({"zeta": s})))
        zr, z = res["z_unfil"].to_numpy(float), res["z"].to_numpy(float)
        if np.sign(zr[1] - zr[0]) != np.sign(z[1] - z[0]):
            members.append(sid)
    return {"n_real": len(real), "members_all": len(members),
            "members_train": sorted(m for m in members if m in train),
            "n_train_real": len([s for s in real if s in train])}


def main() -> None:
    env = core.assert_environment()
    pt = J("param_table.json")["counts"]
    rt = J("reachability_train.json")
    cen = J("test_label_census.json")
    ct = J("constant_train.json")
    s1 = J("stage1_output.json")
    cur = s1["results"]["current"]["aggregate"]
    p15_train = ct["current"]["scores"]["params-15"]
    out = {
        "environment": env,
        "stage0": {
            "params15_keys": pt["params_15_keys"],
            "differ_strict_value_behaviour": [pt["differ_strict"], pt["differ_value"],
                                              pt["differ_behaviour"]],
            "reachability_p14_p15_sequence": rt["measured"],
            "census": {k: cen["current"][k] for k in ("n", "verdict_kinds", "has_mature",
                                                       "equal_to_S_star")},
            "first_blind_identical": cen["first_blind"][
                "identical_to_current_in_phases_verdict_tolerance_unsure"],
            "S_star": ct["current"]["S_star"],
            "S_star_train_count": ct["current"]["sequences"][" > ".join(ct["current"]["S_star"])],
            "exposure_events": len(J("exposure_table.json")["events"]),
        },
        "stage1": {
            "verdict": s1["verdict"], "failed": s1["failed"], "head": s1["head"][:7],
            "V_current": s1["results"]["current"]["V"],
            "V_first_blind": s1["results"]["first-blind"]["V"],
            "aggregates_current": {n: {k: a[k] for k in ("H", "B", "R", "N0", "C", "C_den",
                                                          "Q", "Q_den", "false_refusals")}
                                   | ({"MAT": a["MAT"], "M": a["M"]} if "MAT" in a else {})
                                   for n, a in cur.items()},
            "discordant": s1["results"]["current"]["discordant"],
            "p14_vs_p15_changed": s1["p14_vs_p15_changed"],
            "incipient_boundary_P15_test": [cur["P15"]["H"], cur["P15"]["B"]],
            "incipient_boundary_P15_train_real": [p15_train["incipient_hits"],
                                                  p15_train["n_boundary"]],
            "false_refusals_P15_test": [cur["P15"]["false_refusals"], cur["P15"]["B"]],
            "false_refusals_P15_train_real": [p15_train["false_refusals"],
                                              p15_train["n_boundary"]],
        },
        "stage2a": {
            "removed": len(J("recovery_table.json")["rows"]),
            "recovery_commit": J("recovery_table.json")["head"][:12],
            "stale_scripts": len(J("stale_scripts.json")),
            "suite": suite("suite_2a.txt"),
        },
        "stage2b": {
            "digests": {k: v["obtained"] for k, v in J("gate_2b.json")["digests"].items()},
            "eq3": J("gate_2b.json")["eq3"], "train_changes": J("gate_2b.json")["obtained"],
            "counts_only": J("gate_2b.json")["counts_only"],
            "suite_measure": suite("suite_2b_measure.txt"),
            "suite_prefix": suite("suite_2b_prefix.txt"),
            "suite_final": suite("suite_2b_final.txt"),
            "fix_crashes_before": {c: sum(v.startswith("CRASH") for v in r.values())
                                   for c, r in J("fix_use_filter_false_before.json")["results"].items()},
        },
        "stage2c": {
            "sidebar_keys": len(J("sidebar_table_2c.json")["rows"]),
            "sidebar_changed": sum(r["today"] != r["declared"]
                                   for r in J("sidebar_table_2c.json")["rows"]),
            "sidebar_obtained_match": sum(r.get("obtained") == r["declared"]
                                          for r in J("sidebar_table_2c.json")["rows"]),
        },
        "defect_I_current_defaults": defect_i(),
    }
    if (HERE / "suite_2c.txt").exists():
        out["stage2c"]["suite"] = suite("suite_2c.txt")
    (HERE / "future_work_numbers.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
