"""Item 31, stage 0, task 2 — which TRAIN series change phase SEQUENCE, params-14 → params-15.

TRAIN only: 35 real of the original split, 12 synthetic, 7 of `batches.swell_item30`.
TEST ids (16 of the split + 3 of the batch) are dropped by `item31_core.train_series`
before anything is loaded into the working dict. No label is read here at all.

DECLARED PREDICTION (Claude, in the brief, before this script existed):
    0 in the 35 original real + 0 in the 12 synthetic; 5 in the batch.
If the measurement differs, stage 0 STOPS and reports before any later task.

"Sequence" is the evaluator's ruler: `detected_phase_starts` (normalised names,
consecutive repeats merged). Final-map and incipient-end changes are reported
alongside, never in place of it: a sequence can stay while the map moves.

Outputs: reachability_train.txt (via tee), reachability_train.json.

Run: python research/labels/diagnostics/item31/reachability_train.py | tee .../reachability_train.txt
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

PREDICTION = {"original_real": 0, "synthetic": 0, "batch_train": 5}


def main() -> int:
    env = core.assert_environment()
    print("environment:", json.dumps(env))
    cfg14, cfg15 = core.load_config("params-14"), core.load_config("params-15")
    assert cfg14[0] == cfg15[0], "filter params differ between params-14 and params-15"
    assert cfg15[1] == {**cfg14[1], "incipient_plateau_spare_intensification": True}
    print("config diff params-14 → params-15: phase_params."
          "incipient_plateau_spare_intensification False → True, nothing else")

    groups = core.train_series()
    rows, counts = [], {}
    for g, series in groups.items():
        c = {"n": len(series), "sequence": 0, "final_map": 0, "incipient_end": 0}
        for sid, values in series.items():
            f14, f15 = core.run(values, *cfg14), core.run(values, *cfg15)
            s14, s15 = core.sequence(f14), core.sequence(f15)
            i14, i15 = core.incipient_end(f14), core.incipient_end(f15)
            r = {"group": g, "id": sid, "seq14": " > ".join(s14), "seq15": " > ".join(s15),
                 "seq_changed": s14 != s15, "map_changed": f14 != f15,
                 "inc14": i14, "inc15": i15, "inc_changed": i14 != i15}
            c["sequence"] += r["seq_changed"]
            c["final_map"] += r["map_changed"]
            c["incipient_end"] += r["inc_changed"]
            rows.append(r)
        counts[g] = c

    print("\n group           n  sequence changed  final map changed  incipient end changed")
    for g, c in counts.items():
        print(f" {g:<14} {c['n']:>3}  {c['sequence']:>16}  {c['final_map']:>17}  "
              f"{c['incipient_end']:>21}")
    print("\nTRAIN series whose final map changes (TRAIN only — per-series is allowed):")
    for r in rows:
        if r["map_changed"]:
            print(f"  {r['group']:<14} {r['id']}  seq changed={r['seq_changed']}  "
                  f"incipient end {r['inc14']} → {r['inc15']}\n"
                  f"      p14: {r['seq14']}\n      p15: {r['seq15']}")

    measured = {g: counts[g]["sequence"] for g in PREDICTION}
    match = measured == PREDICTION
    print(f"\nPREDICTION {PREDICTION}\nMEASURED   {measured}\n"
          f"VERDICT: {'MATCH — continue' if match else 'MISMATCH — STOP and report'}")
    (HERE / "reachability_train.json").write_text(json.dumps(
        {"environment": env, "prediction": PREDICTION, "measured": measured,
         "match": match, "counts": counts, "rows": rows}, indent=2))
    return 0 if match else 1


if __name__ == "__main__":
    raise SystemExit(main())
