#!/usr/bin/env python
"""Front 20(b) stage 1 - the report's numbers, from measure_20b's table.

Reads nothing new: it calls measure_20b.main() and reduces its output. Prints
the sanity check, the sign guard, measurements B and C, the separability test
and the state of the two latent defects.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from measure_20b import analyse, overlaps, main as measure_main


def hr(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


def main():
    res_real, res_syn, rows, pv, gp, sha = measure_main()

    # ---------------------------------------------------------------- sanity
    hr("SANITY CHECK - 20160735 must emit four mature blocks of 5, 12, 32, 12")
    f = res_real["20160735"]
    durs = [b - a + 1 for a, b in f["det_blocks"]]
    print(f"blocks     {f['det_blocks']}")
    print(f"durations  {durs}")
    print(f"labelled   {[(a,b,b-a+1) for a,b,_ in f['lab_matures']]}")
    print(f"series_sha256 verified against the label: {f['sha_ok']}")
    ok = durs == [5, 12, 32, 12]
    print(f"VERDICT: {'REPRODUCED' if ok else 'NOT REPRODUCED - STOP'}")
    if not ok:
        sys.exit("premise not reproduced")

    # ------------------------------------------------- series used + its mean
    hr("SERIES FEEDING MATURE DETECTION")
    print("determine_periods.py:1017  df['z'] = vorticity.vorticity_smoothed2   (FILTERED)")
    print("find_stages._amplitude_mature_bounds reads df.at[..., 'z'] only.")
    print("find_peaks_valleys is also called on df['z'], so the valleys are the")
    print("filtered series' valleys too.")
    print(f"\nfilter: use_filter={pv['use_filter']} cutoff_low={pv['cutoff_low']} "
          f"cutoff_high={pv['cutoff_high']} use_smoothing={pv['use_smoothing']}"
          f" -> band-pass, the mean level is removed\n")
    mf = np.array([f["z_mean"] for f in res_real.values()])
    mu = np.array([f["z_unfil_mean"] for f in res_real.values()])
    print(f"mean of FILTERED z, over the 35 real train series:")
    print(f"   min {mf.min():+.6e}   max {mf.max():+.6e}   mean {mf.mean():+.6e}")
    print(f"   max |mean| {np.abs(mf).max():.6e}")
    print(f"mean of RAW zeta (df['z_unfil']), same 35, for contrast:")
    print(f"   min {mu.min():+.6e}   max {mu.max():+.6e}   mean {mu.mean():+.6e}")
    scale = np.array([f["z_max"] - f["z_min"] for f in res_real.values()])
    print(f"\n|mean of filtered z| / series range, worst case: "
          f"{(np.abs(mf)/scale).max():.4%}")

    # ------------------------------------------------------------ sign guard
    hr("SIGN GUARD")
    pos_min = [(s, f["z_min"]) for s, f in res_real.items() if f["z_min"] >= 0]
    pos_val = [(r["series"], r["valley_idx"], r["z_valley"]) for r in rows if r["z_valley"] > 0]
    print(f"series with z_min >= 0 : {len(pos_min)}  {pos_min}")
    print(f"generating valleys with z_valley > 0 : {len(pos_val)}")
    for s, i, z in pos_val:
        print(f"   {s} valley {i}  z = {z:+.6e}")
    if pos_val:
        print("\nD2 = |z_valley|/|z_min| is NOT well defined for these: a positive")
        print("valley gets a positive ratio that says nothing about depth. Reported")
        print("as a result, not worked around.")

    # ----------------------------------------------------------- latent bugs
    hr("LATENT DEFECTS OF _amplitude_mature_bounds (active check)")
    defects = [d for f in {**res_real, **res_syn}.values() for d in f["defects"]]
    d152 = [d for d in defects if d["defect"] == "152"]
    d160 = [d for d in defects if d["defect"] == "160"]
    print("check performed: the triggering CONDITION is recomputed for every")
    print("valley (amp_prev < 0 / amp_next < 0), not inferred from 'no exception'")
    print("- the :160 one returns a wrong window silently and would never raise.")
    print(f"\n:152 (violations_prev[-1]+1 overruns -> IndexError)  fired: {len(d152)}")
    print(f":160 (violations_next[0]-1 wraps to index[-1])        fired: {len(d160)}")
    for d in d152 + d160:
        print(f"   {d}")
    print("\n(checked over all 47 train series, real + synthetic, every valley that")
    print(" find_mature_stage evaluates - not only the generating ones.)")

    # ----------------------------------------------------- measurement A/out
    hr("MEASUREMENT A - the generating-valley table")
    true = [r for r in rows if r["classification"] == "TRUE"]
    spur = [r for r in rows if r["classification"] == "SPURIOUS"]
    print(f"generating valleys measured : {len(rows)}  over {len(res_real)} real train series")
    print(f"   TRUE     (block overlaps a labelled mature) : {len(true)}")
    print(f"   SPURIOUS (block overlaps none)              : {len(spur)}")
    nb = {}
    for r in rows:
        nb[r["series"]] = nb.get(r["series"], 0) + 1
    multi = {s: n for s, n in nb.items() if n > 1}
    print(f"   series emitting more than one block: {len(multi)}  {multi}")
    nolab = [s for s, f in res_real.items() if not f["lab_matures"]]
    noblk = [s for s, f in res_real.items() if not f["det_blocks"]]
    print(f"   series with NO labelled mature : {len(nolab)} {nolab}")
    print(f"   series with NO detected block  : {len(noblk)} {noblk}")

    # -------------------------------------------------------- separability
    def sep(sub, key):
        t = [r[key] for r in sub if r["classification"] == "TRUE" and r[key] == r[key]]
        s = [r[key] for r in sub if r["classification"] == "SPURIOUS" and r[key] == r[key]]
        if not t or not s:
            return None, None, None
        return min(t), max(s), min(t) > max(s)

    hr("SEPARABILITY TEST")
    for scope, sub in (("GLOBAL (35 real train series)", rows),
                       ("20160735 ALONE", [r for r in rows if r["series"] == "20160735"])):
        print(f"\n--- {scope}: {len(sub)} valleys "
              f"({sum(r['classification']=='TRUE' for r in sub)} true / "
              f"{sum(r['classification']=='SPURIOUS' for r in sub)} spurious)")
        for key in ("D1", "D2"):
            mn, mx, s = sep(sub, key)
            if mn is None:
                print(f"  {key}: one class empty - not evaluable")
                continue
            print(f"  {key}: min(TRUE) = {mn:.4f}   max(SPURIOUS) = {mx:.4f}   "
                  f"separates? {'YES' if s else 'NO'}   (gap {mn-mx:+.4f})")

    hr("THE VALLEYS THAT CAUSE THE OVERLAP (named)")
    for key in ("D1", "D2"):
        t = [r for r in rows if r["classification"] == "TRUE"]
        s = [r for r in rows if r["classification"] == "SPURIOUS"]
        lo = min(t, key=lambda r: r[key])
        print(f"\n{key}: lowest TRUE is {lo['series']} valley {lo['valley_idx']} "
              f"at {lo[key]:.4f}")
        bad = sorted([r for r in s if r[key] >= lo[key]], key=lambda r: -r[key])
        print(f"     SPURIOUS at or above it: {len(bad)}")
        for r in bad:
            print(f"       {r['series']:>10} v{r['valley_idx']:<4} {key}={r[key]:.4f} "
                  f"block {r['block_start']}-{r['block_end']} ({r['block_len']} steps) "
                  f"relprom={r['prominence_relative']}")

    # ------------------------------------------------------- measurement B
    hr("MEASUREMENT B - baseline for the multi-mature cases")
    claimed = ["20203947", "s6b542eee", "sbd6c6920"]
    actual = sorted(s for s, f in res_real.items() if len(f["lab_matures"]) > 1)
    print(f"claimed by the prompt : {claimed}")
    print(f"actually >1 labelled mature among the 35 REAL train series : {actual}")
    for c in claimed:
        where = ("real train" if c in res_real else
                 "synthetic train" if c in res_syn else "NOT in the train split")
        print(f"   {c}: {where}")
    for s in sorted(set(actual) | {c for c in claimed if c in res_real}):
        f = res_real[s]
        print(f"\n   {s}  detected blocks {f['det_blocks']}")
        for k, (a, b, unsure) in enumerate(f["lab_matures"], 1):
            hit = [blk for blk in f["det_blocks"] if overlaps(blk, (a, b)) > 0]
            print(f"     labelled mature #{k}: {a}-{b} ({b-a+1} steps)"
                  f"{'  [UNSURE]' if unsure else ''}"
                  f"  ->  {'DETECTED by ' + str(hit) if hit else 'NOT DETECTED'}")

    # ------------------------------------------------------- measurement C
    hr("MEASUREMENT C - is the generating valley the series' deepest valley?")
    allres = {**res_real, **res_syn}
    matched = {s: f for s, f in allres.items() if f["matches_label"]}
    print(f"cases whose mature matches the label (+/-{6} both ends, params-11):")
    print(f"   over all 47 train series      : {len(matched)}")
    print(f"   over the 35 real train series : "
          f"{sum(1 for s,f in res_real.items() if f['matches_label'])}")

    for scope, pool in (("all 47 train", matched),
                        ("35 real train only",
                         {s: f for s, f in res_real.items() if f["matches_label"]})):
        deep_all = deep_surv = relprom1 = unknown = 0
        exceptions = []
        for s, f in sorted(pool.items()):
            g = f["gen_for_paired"]
            if g is None:
                unknown += 1
                exceptions.append((s, None))
                continue
            is_deep_all = g["valley_idx"] == f["deepest_valley_all"]
            is_deep_surv = g["valley_idx"] == f["deepest_valley_surviving"]
            deep_all += is_deep_all
            deep_surv += is_deep_surv
            relprom1 += (g["prominence_relative"] is not None
                         and abs(g["prominence_relative"] - 1.0) < 1e-9)
            if not is_deep_all:
                exceptions.append((s, g))
        print(f"\n--- {scope}: {len(pool)} cases")
        print(f"   generating valley is the deepest of ALL valley candidates : {deep_all}")
        print(f"   ... the deepest of the SURVIVING valleys                  : {deep_surv}")
        print(f"   ... at relative prominence exactly 1.0000 (item 19's proxy): {relprom1}")
        print(f"   generating valley could not be attributed                 : {unknown}")
        print(f"   EXCEPTIONS (not on the deepest valley): {len(exceptions)}")
        for s, g in exceptions:
            if g is None:
                print(f"     {s:>10}  no generating valley attributable to the paired block")
                continue
            f = pool[s]
            print(f"     {s:>10}  valley {g['valley_idx']}  D1={g['D1']:.4f}  "
                  f"D2={g['D2']:.4f}  relprom={g['prominence_relative']}"
                  f"  (deepest valley is {f['deepest_valley_all']})")

    print("\nnote: item 19 reported '30 of 32' using relative prominence == 1.0000")
    print("as the stand-in for 'deepest valley'. Both columns are given above")
    print("because they are not the same quantity - prominence is the SMALLER of")
    print("the two climbs out of a valley, not the valley's depth.")

    hr("SIX ENTRIES NEW SINCE 20a (named in the brief), one line each")
    for s in ["20150436", "20160735", "20170342", "20180628", "20180733", "20207822"]:
        f = allres.get(s)
        if f is None:
            print(f"   {s}: not in the train split")
            continue
        g = f["gen_for_paired"]
        print(f"   {s}: matches_label={f['matches_label']}  d=({f['d_start']},{f['d_end']})"
              f"  gen valley={g['valley_idx'] if g else None}"
              f"  deepest={f['deepest_valley_all']}"
              f"  {'DEEPEST' if g and g['valley_idx']==f['deepest_valley_all'] else 'EXCEPTION'}")


if __name__ == "__main__":
    main()
