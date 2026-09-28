"""Item 31, stage 0, task 4 — LABEL-ONLY census of the 16 TEST series. AGGREGATES ONLY.

THIS IS A DECLARED EXPOSURE of the test split's labels, at the level of counts.
It is run AFTER the stage-1 criterion's structure was committed (DESIGN.md §5,
commit recorded there), so the structure could not be tuned to these numbers;
only the reachability arithmetic of §5 reads them.

What is read: the manual-label records of the 16 ids under `test:` in
split.yaml, filtered by id right after `read_labels`. The 3 test ids of
`batches.swell_item30` are NOT read (their inclusion is Danilo's decision); the
DESIGN gives reachability for them by bounds instead.
What is NOT done: no detector is called, no series is processed. Series values
are loaded ONLY to check `series_sha256` (a stale label would drop out of the
evaluator's denominator), and only the count of mismatches leaves this script.

Nothing per series is printed or written: every output is a count or a
histogram over the 16. The script asserts that no test id string appears in its
own output before writing it.

Output: test_label_census.txt, test_label_census.json.
Run: python -P research/labels/diagnostics/item31/test_label_census.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

lc = core.lc
S_STAR = ("intensification", "mature", "decay")     # constant_train.txt, frozen before this run


def census(recs: list[dict]) -> dict:
    kinds = Counter(r["verdict"]["kind"] for r in recs)
    seqs = Counter(" > ".join(p for p, _ in lc.phase_sequence(r)) for r in recs)
    n_mat = [sum(lc.normalize_phase(p["phase"]) == "mature" for p in r["phases"]) for r in recs]
    unsure = sum(bool(p.get("unsure")) for r in recs for p in r["phases"])
    inc_unsure = sum(1 for r in recs if len(r["phases"]) > 1
                     and r["phases"][0]["phase"] == "incipient" and r["phases"][1].get("unsure"))
    return {
        "n": len(recs),
        "verdict_kinds": {k: kinds.get(k, 0) for k in lc.VERDICT_KINDS},
        "label_has_incipient_phase": sum(r["phases"][0]["phase"] == "incipient" for r in recs),
        "incipient_boundary_unsure": inc_unsure,
        "has_mature": sum(m > 0 for m in n_mat),
        "more_than_one_mature": sum(m > 1 for m in n_mat),
        "mature_phases_total": sum(n_mat),
        "boundaries_unsure_total": unsure,
        "sequence_distribution": dict(seqs.most_common()),
        "n_distinct_sequences": len(seqs),
        "equal_to_S_star": seqs.get(" > ".join(S_STAR), 0),
        "modal_count": seqs.most_common(1)[0][1] if seqs else 0,
    }


def main() -> None:
    env = core.assert_environment()
    sets = core.split_sets()
    test16 = set(sets["test"])
    assert len(test16) == 16 and test16.isdisjoint(sets["batch_test"])
    records = {sid: r for sid, r in lc.read_labels().items() if sid in test16}   # by id FIRST

    real = lc.load_real_series()
    present = sorted(records)
    stale = sum(lc.series_sha256(real[s]) != records[s].get("series_sha256") for s in present)
    legacy = sum(lc.is_legacy_record(records[s]) for s in present)
    adjudicated = sum(lc.is_adjudicated(records[s]) for s in present)
    usable = [records[s] for s in present
              if lc.series_sha256(real[s]) == records[s].get("series_sha256")
              and not lc.is_legacy_record(records[s])]

    fb = [lc.first_blind_record(r) for r in usable]
    fb_ok = [r for r in fb if r is not None]
    same = sum(1 for cur, b in zip(usable, fb) if b is not None
               and lc.phase_sequence(cur) == lc.phase_sequence(b)
               and cur["verdict"] == b["verdict"]
               and [p.get("tolerance_idx") for p in cur["phases"]]
               == [p.get("tolerance_idx") for p in b["phases"]]
               and [bool(p.get("unsure")) for p in cur["phases"]]
               == [bool(p.get("unsure")) for p in b["phases"]])
    out = {
        "environment": env,
        "population": "the 16 ids under split.yaml `test:` (batch test NOT read)",
        "records_present": len(present), "series_sha256_mismatch": stale,
        "legacy_schema": legacy, "adjudicated": adjudicated, "usable": len(usable),
        "current": census(usable),
        "first_blind": {"records_with_a_blind_version": len(fb_ok),
                        "identical_to_current_in_phases_verdict_tolerance_unsure": same,
                        **census(fb_ok)},
    }
    text = json.dumps(out, indent=2)
    for sid in test16:
        assert sid not in text, "a test id leaked into the census output"
    (HERE / "test_label_census.json").write_text(text)
    (HERE / "test_label_census.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
