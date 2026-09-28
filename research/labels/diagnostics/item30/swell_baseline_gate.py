"""Item 30, steps 1 and 2 — swell baseline under params-14, and the gate (0a)/(0b).

MEASUREMENT ONLY. The swell tracks live outside the repo and are given by
argument. Per-track tables are written to --out (outside the repo); this script
prints only aggregate counts and group ids.

Universe: the swell sample minus every TEST id (20203389 of the split, and the
batch's 19930748, 20111118, 19990549) — 196 tracks.

Step 1: for each track, under params-14 — boundary, peak, signal, the
pre-incipient and final maps, the symptom, and the bad/good mark. Each is
compared track by track with m1_baseline.csv (params-11, sha256-checked), and
params-11 is also recomputed here as a guard on P1.

Step 2 (the gate), on bad-with-signal and good-with-signal:

* (0a) Is there intensification in the pre-incipient map before the boundary?
  Where does it start and end relative to the boundary and the peak? Is its loss
  confined to step 6?
* (0b) Which blocks does step 6 erase, and which phase opens the final map at
  the boundary?
* Good tracks: does the intensification that leads to the global minimum vanish?
  That block is the last step-5 intensification block starting at or before the
  peak. It "vanishes" when none of its samples is intensification in the final
  map.

Run:
    python research/labels/diagnostics/item30/swell_baseline_gate.py \
        --swell <dir with {id}.txt> --m1 <m1_baseline.csv> --out <dir outside the repo>
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import item30_core as core  # noqa: E402
import track_io  # noqa: E402

M1_SHA256 = "a1aa56195c4823f7b998644e4d5673d8748bf1dd41e930fd319ad14b5c0ce51b"
GROUPS = core.REPO / "research" / "labels" / "swell_item30" / "groups_params11.yaml"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--swell", type=Path, required=True)
    ap.add_argument("--m1", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.resolve().is_relative_to(core.REPO), "per-track tables stay outside the repo"
    a.out.mkdir(parents=True, exist_ok=True)

    assert hashlib.sha256(a.m1.read_bytes()).hexdigest() == M1_SHA256
    m1 = pd.read_csv(a.m1, dtype={"track_id": str}).set_index("track_id")
    bad = set(yaml.safe_load(GROUPS.read_text())["bad_marks"])

    excl = core.excluded_ids()
    ids = sorted(p.stem for p in a.swell.glob("*.txt"))
    assert len(ids) == 200
    ids = [i for i in ids if i not in excl]
    assert len(ids) == 196, len(ids)
    print("environment:", json.dumps(core.environment()))
    print("excluded from the swell universe:", sorted(set(p.stem for p in a.swell.glob("*.txt")) & excl))

    cfg = {k: core.load_config(k) for k in ("params-14", "params-11")}
    rows, gate = [], {}
    for tid in ids:
        s = track_io.read_track((a.swell / f"{tid}.txt").read_bytes())
        r14 = core.run_series(s, *cfg["params-14"])
        r11 = core.run_series(s, *cfg["params-11"])
        rows.append({
            "track_id": tid, "bad": tid in bad, "n": r14["n"],
            "boundary14": r14["boundary"], "peak14": r14["peak"], "signal14": r14["signal"],
            "symptom14": r14["symptom"], "pre14": core.seq(r14["pre"]),
            "final14": core.seq(r14["final"]),
            "erased14": ";".join(f"{f}[{x}-{y}]" for f, x, y in r14["erased"]),
            "boundary11_recomputed": r11["boundary"], "peak11_recomputed": r11["peak"],
            "symptom11_recomputed": r11["symptom"],
            "boundary11_m1": int(m1.loc[tid, "plateau_boundary"]),
            "peak11_m1": int(m1.loc[tid, "peak_idx"]),
            "signal11_m1": bool(m1.loc[tid, "plateau_boundary"] > m1.loc[tid, "peak_idx"]),
            "symptom11_m1": bool(m1.loc[tid, "mature_sem_int"]),
        })
        if r14["signal"]:
            gate[tid] = gate_record(tid in bad, r14)

    d = pd.DataFrame(rows).set_index("track_id")
    d.to_csv(a.out / "swell_baseline_params14.csv")
    (a.out / "gate_params14.json").write_text(json.dumps(gate, indent=1))
    report(d, gate)


def gate_record(is_bad: bool, r: dict) -> dict:
    b, pk, pre, fin = r["boundary"], r["peak"], r["pre"], r["final"]
    pre_int = core.int_blocks(pre)
    before = [(x, y) for x, y in pre_int if x < b]
    fin_int_before_b = [i for i in range(b) if str(fin[i]).startswith("intensification")]
    lead = [(x, y) for x, y in pre_int if x <= pk]
    lead = lead[-1] if lead else None
    lead_left = (sum(str(fin[i]).startswith("intensification") for i in range(lead[0], lead[1] + 1))
                 if lead else None)
    return {
        "bad": is_bad, "n": r["n"], "boundary": b, "peak": pk,
        "pre_seq": core.seq(pre), "final_seq": core.seq(fin),
        "pre_int_blocks": pre_int,
        "a_int_before_boundary": bool(before),
        "a_blocks_before_boundary": [
            {"start": x, "end": y, "start_vs_boundary": x - b, "end_vs_boundary": y - b,
             "start_vs_peak": x - pk, "end_vs_peak": y - pk} for x, y in before],
        "a_int_left_before_boundary_final": len(fin_int_before_b),
        # the step-5 intensification samples in [0, b) are exactly the ones step 6 erases
        "a_lost_only_at_step6": (bool(before) and
                                 {i for x, y in before for i in range(x, min(y, b - 1) + 1)}
                                 == {i for f, x, y in r["erased"] if f.startswith("intensification")
                                     for i in range(x, y + 1)}),
        "b_erased": [{"phase": f, "start": x, "end": y} for f, x, y in r["erased"]],
        "b_final_phase_at_boundary": str(fin[b]) if b < r["n"] else None,
        "lead_block": lead, "lead_block_end_vs_peak": (lead[1] - pk) if lead else None,
        "lead_block_int_samples_left_final": lead_left,
        "lead_block_vanished": (lead_left == 0) if lead else None,
        "symptom": r["symptom"],
    }


def report(d: pd.DataFrame, gate: dict) -> None:
    B, G = d[d.bad], d[~d.bad]
    print(f"\nuniverse {len(d)}: bad {len(B)}, good {len(G)}")
    print("P1 boundary params-14 == params-11 (m1 csv):",
          int((d.boundary14 == d.boundary11_m1).sum()), "/", len(d),
          "| == params-11 recomputed:", int((d.boundary14 == d.boundary11_recomputed).sum()),
          "| peak14 == peak11 (m1):", int((d.peak14 == d.peak11_m1).sum()))
    print("P2 signal14: bad", int(B.signal14.sum()), "/", len(B), "| good", int(G.signal14.sum()), "/", len(G))
    print("   symptom14: bad", int(B.symptom14.sum()), "/", len(B), "| good", int(G.symptom14.sum()), "/", len(G))
    print("   symptom11 recomputed == m1 csv:", int((d.symptom11_recomputed == d.symptom11_m1).sum()), "/", len(d))
    for name, c14, c11 in (("signal", "signal14", "signal11_m1"), ("symptom", "symptom14", "symptom11_m1")):
        for lab, sub in (("bad", B), ("good", G)):
            ent = sorted(sub.index[sub[c14] & ~sub[c11]])
            out = sorted(sub.index[~sub[c14] & sub[c11]])
            print(f"   {name} {lab}: params-11 {int(sub[c11].sum())} -> params-14 {int(sub[c14].sum())}; "
                  f"entered {ent}; left {out}")
    for lab, want in (("bad", True), ("good", False)):
        g = {k: v for k, v in gate.items() if v["bad"] == want}
        print(f"\nGATE {lab} with signal ({len(g)}): {sorted(g)}")
        print("  (0a) intensification before boundary in pre map:", sum(v["a_int_before_boundary"] for v in g.values()),
              "| none left before boundary in final:", sum(v["a_int_left_before_boundary_final"] == 0 for v in g.values()),
              "| lost only at step 6:", sum(bool(v["a_lost_only_at_step6"]) for v in g.values()))
        print("  symptom (final):", sum(v["symptom"] for v in g.values()),
              "| lead block vanished:", sum(bool(v["lead_block_vanished"]) for v in g.values()),
              "| no lead block:", sorted(k for k, v in g.items() if v["lead_block"] is None))
        from collections import Counter
        print("  (0b) erased phases:", dict(Counter(e["phase"].split(" ")[0] for v in g.values() for e in v["b_erased"])),
              "| final phase at boundary:", dict(Counter(str(v["b_final_phase_at_boundary"]).split(" ")[0] for v in g.values())))


if __name__ == "__main__":
    main()
