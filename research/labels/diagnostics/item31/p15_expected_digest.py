"""Item 31, stage 0, task 6 support — the digest the stage-2 default MUST produce.

This is NOT a second default-behaviour generator. The default-behaviour digest
has one generator, `research/labels/diagnostics/front_b/default_behaviour_hash.py`
(section 3 of its docstring is the definition). This script computes, TODAY and
with the defaults untouched, what that generator must print AFTER stage 2 makes
params-15 the default:

    same 47 TRAIN ids, same order, same "<id>:<p0>|<p1>|..." lines joined by
    "\\n", same sha256 — but with params-15 passed EXPLICITLY:
    get_periods(process_vorticity(df, **pv15), **gp15)

Positive control, asserted: the same function with NO kwargs reproduces the
digest front_b's generator has on record for the current defaults
(b500d2e0…, default_behaviour_sha256.txt). If it does not, the layout here is
not front_b's and the expected digest below means nothing.

TRAIN only (47 ids of the split). No label is read except `series_sha256`, which
is verified for every series before hashing, as front_b does.

SECOND DIGEST, same layout, over 54 = the 47 + the 7 batch TRAIN ids. Reason
(item 30's R2 lesson: "a default-unchanged guard must exercise the changed
branch"): spare_intensification changes 0 of the 47 (reachability_train.txt),
so the 47-id digest is identical under params-14 and params-15 and cannot see
the rule. On the 54 it must differ between the two — asserted as a control.

Output: p15_expected_digest.txt.
Run: python -P research/labels/diagnostics/item31/p15_expected_digest.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

lc, dp = core.lc, core.dp
FRONT_B_DEFAULT = "b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5"


def digest(series: dict, pv: dict, gp: dict) -> str:
    recs = []
    for sid in sorted(series):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = dp.get_periods(dp.process_vorticity(pd.DataFrame({"zeta": series[sid]}), **pv),
                                 **gp)
        recs.append(sid + ":" + "|".join(res["periods"].astype(str)))
    return hashlib.sha256("\n".join(recs).encode()).hexdigest()


def main() -> None:
    env = core.assert_environment()
    g = core.train_series()
    series = {**g["original_real"], **g["synthetic"]}
    assert set(series) == set(lc.read_split()["train"]) and len(series) == 47
    labels = {sid: r for sid, r in lc.read_labels().items() if sid in series}
    stale = [s for s, v in series.items() if lc.series_sha256(v) != labels[s]["series_sha256"]]
    assert not stale, stale
    pv15, gp15 = core.load_config("params-15")
    pv15 = {**pv15, "use_filter": "auto"}     # ≡ True (param_table.md, footprint_train B)

    batch = g["batch_train"]
    blabels = {sid: r for sid, r in lc.read_labels().items() if sid in batch}
    assert all(lc.series_sha256(v) == blabels[s]["series_sha256"] for s, v in batch.items())
    s54 = {**series, **batch}
    pv14, gp14 = core.load_config("params-14")
    pv14 = {**pv14, "use_filter": "auto"}
    control = digest(series, {}, {})
    ok = control == FRONT_B_DEFAULT
    expected = digest(series, pv15, gp15)
    e47_14 = digest(series, pv14, gp14)
    e54, e54_14 = digest(s54, pv15, gp15), digest(s54, pv14, gp14)
    lines = [
        "Item 31 — expected default-behaviour digest after stage 2 (front_b layout)",
        f"environment: {json.dumps(env)}",
        "series: 47 TRAIN ids of split.yaml, sorted; series_sha256 verified",
        f"positive control (no kwargs) = {control}",
        f"  == front_b record b500d2e0… : {ok}",
        f"EXPECTED after stage 2 (params-15 explicit, use_filter='auto') = {expected}",
        f"  same 47 under params-14 = {e47_14}  (identical to params-15: {e47_14 == expected}"
        " — the 47 do NOT exercise spare_intensification)",
        f"EXPECTED over 54 (47 + 7 batch TRAIN, same layout), params-15 = {e54}",
        f"  same 54 under params-14 = {e54_14}  (differs: {e54 != e54_14} — the 54 DO exercise it)",
    ]
    assert e54 != e54_14, "the 54-id digest does not see the rule"
    assert ok, "layout differs from front_b's generator — the expected digest is void"
    (HERE / "p15_expected_digest.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
