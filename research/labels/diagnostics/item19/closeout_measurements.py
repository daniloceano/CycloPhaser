#!/usr/bin/env python
"""Item 19/20 closeout - the three measurements the review asked for. TRAIN only.

1a  what happens to 20205386 at prominence_relative=0.60
1c  the width of 20160735's SPURIOUS mature blocks as mature_amplitude_fraction
    widens, next to the correct-mature length distribution in the same cell
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import item19_core as C
from item19_core import OUT, MARGIN
from labels_core import read_labels

TARGET = "20160735"
SUBJECT = "20205386"
MAFS = [0.95, 0.90, 0.85, 0.80]


def main():
    pv, gp0 = C.load_config()
    real, synth = C.load_train_series()
    series = {**real, **synth}
    labels = read_labels()
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("=" * 78)
    say(f"1a. {SUBJECT} as prominence_relative rises (mature_amplitude_fraction "
        f"held at {gp0['mature_amplitude_fraction']})")
    say("=" * 78)
    sub = {SUBJECT: series[SUBJECT]}
    ref = C.facts_for_config(sub, labels, pv, gp0, want_z=True)[SUBJECT]
    lab = ref["lab_mature"]
    say(f"label mature      : {lab[0]}-{lab[1]}")
    say(f"labelled sequence : {' -> '.join(ref['lab_seq'])}")
    say("")
    say("| prom_rel | surviving valleys (rel prom) | mature blocks | paired | Dstart | Dend "
        "| within +-6 | seq match |")
    say("|---|---|---|---|---|---|---|---|")
    for pr in (0.30, 0.45, 0.50, 0.55, 0.60):
        gp = dict(gp0, prominence_relative=pr)
        f = C.facts_for_config(sub, labels, pv, gp, want_z=True)[SUBJECT]
        rel = C.extrema_with_prominence(f["z"])
        kv = C.surviving(rel["valley"], pr)
        vtxt = ", ".join(f"{v}({'bnd' if rel['valley'][v] is None else f'{rel[chr(39)+chr(39)] if False else rel[chr(118)+chr(97)+chr(108)+chr(108)+chr(101)+chr(121)][v]:.4f}'})"
                         for v in kv)
        gen = None
        if f["paired"]:
            inside = [v for v in kv if f["paired"][0] <= v <= f["paired"][1]]
            gen = min(inside, key=lambda v: f["z"][v]) if inside else None
        say(f"| {pr:.2f} | {vtxt} | {f['det_matures']} | "
            f"{f['paired']}{f' from valley {gen}' if gen is not None else ''} | "
            f"{f['d_start']} | {f['d_end']} | {'YES' if f['matches_label'] else 'no'} | "
            f"{'yes' if f['seq_match'] else 'NO'} |")
        if pr == 0.60:
            say("")
            say(f"  detected sequence at pr=0.60 : {' -> '.join(f['det_seq'])}")
            say(f"  detected sequence at params-10: {' -> '.join(ref['det_seq'])}")

    say("")
    say("=" * 78)
    say(f"1c. {TARGET}: spurious mature blocks as maf widens "
        f"(prominence_relative={gp0['prominence_relative']})")
    say("=" * 78)
    tgt = {TARGET: series[TARGET]}
    tlab = C.facts_for_config(tgt, labels, pv, gp0)[TARGET]["lab_mature"]
    say(f"label mature: {tlab[0]}-{tlab[1]} ({tlab[1]-tlab[0]+1} steps)")
    say("")
    say("| maf | all blocks (len) | overlapping the label | SPURIOUS blocks (len) | "
        "correct matures in split | of those, < 7 steps | < 9 | median len |")
    say("|---|---|---|---|---|---|---|---|")
    for maf in MAFS:
        gp = dict(gp0, mature_amplitude_fraction=maf)
        f = C.facts_for_config(tgt, labels, pv, gp)[TARGET]
        blocks = f["det_matures"]
        spur = [b for b in blocks if min(b[1], tlab[1]) - max(b[0], tlab[0]) + 1 <= 0]
        keep = [b for b in blocks if b not in spur]
        allf = C.facts_for_config(series, labels, pv, gp)
        m = [x for x in allf.values() if x["matches_label"]]
        lens = sorted(x["paired"][1] - x["paired"][0] + 1 for x in m)
        say(f"| {maf:.2f} | {[(a,b,b-a+1) for a,b in blocks]} | "
            f"{[(a,b,b-a+1) for a,b in keep]} | {[(a,b,b-a+1) for a,b in spur]} | "
            f"{len(m)} | {sum(1 for L in lens if L < 7)} | "
            f"{sum(1 for L in lens if L < 9)} | {lens[len(lens)//2]} |")

    say("")
    say("=" * 78)
    say("1c (continued). What a pure DURATION floor would cost at each maf")
    say("=" * 78)
    say("")
    say("| maf | spurious block lengths | floor needed to remove them all | correct "
        "matures | min/median/max | correct matures that floor kills |")
    say("|---|---|---|---|---|---|")
    for maf in MAFS:
        gp = dict(gp0, mature_amplitude_fraction=maf)
        f = C.facts_for_config(tgt, labels, pv, gp)[TARGET]
        spur = [b[1] - b[0] + 1 for b in f["det_matures"]
                if min(b[1], tlab[1]) - max(b[0], tlab[0]) + 1 <= 0]
        allf = C.facts_for_config(series, labels, pv, gp)
        lens = sorted(x["paired"][1] - x["paired"][0] + 1
                      for x in allf.values() if x["matches_label"])
        need = max(spur) + 1
        say(f"| {maf:.2f} | {spur} | >= {need} | {len(lens)} | "
            f"{lens[0]}/{lens[len(lens)//2]}/{lens[-1]} | "
            f"**{sum(1 for L in lens if L < need)} of {len(lens)}** |")

    (OUT / "closeout_measurements.txt").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT/'closeout_measurements.txt'}")


if __name__ == "__main__":
    main()
