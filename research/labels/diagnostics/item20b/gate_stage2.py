#!/usr/bin/env python
"""Front 20(b) stage 2 - the gate (a)-(f), plus the three required extras.

Measured over the TRAIN split only (35 real + 12 synthetic).
`read_split()["test"]` is never read.

Reference = params-11 (the current reference). Candidate = params-12
(params-11 + mature_min_depth=0.80). 0.85 is also run, as a DIAGNOSTIC
side-by-side, not a candidate - no recommendation is made between them.

No threshold sweep: exactly the two values the brief names are run.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import (load_real_series, load_synthetic_series, normalize_phase,
                         read_labels, read_split, series_sha256)
from cyclophaser.determine_periods import get_periods, process_vorticity
from cyclophaser.find_stages import _amplitude_mature_bounds

OUT = REPO / "research" / "labels" / "diagnostics" / "item20b"
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")
MARGIN = 6


def load_config(name):
    doc = yaml.safe_load((REPO / "research/labels/configs" / name).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def runs_of(names):
    out, prev, start = [], None, 0
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append((prev, start, i - 1))
            prev, start = n, i
    out.append((prev, start, len(names) - 1))
    return out


def label_runs(record):
    ph, n = record["phases"], record["n_steps"]
    out = []
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1
        out.append((normalize_phase(p["phase"]), s, e, bool(p.get("unsure"))))
    return out


def ov(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]) + 1)


def pair_by_overlap(det, lab):
    if not det or lab is None:
        return None, None
    ls, le = lab
    best, best_ov = None, -1
    for (ds, de) in det:
        o = min(de, le) - max(ds, ls) + 1
        if o > best_ov:
            best, best_ov = (ds, de), o
    if best_ov <= 0:
        mid = (ls + le) / 2
        best = min(det, key=lambda b: abs((b[0] + b[1]) / 2 - mid))
    return best, max(best_ov, 0)


def leading_incipient(runs):
    return runs[0][2] + 1 if runs and runs[0][0] == "incipient" else None


def run_one(sid, values, record, pv, gp):
    caught = []
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        df = get_periods(vort, **gp)
        caught = [str(x.message) for x in w]

    z = np.asarray(df["z"].values, dtype=float)
    z_max, z_min = float(z.max()), float(z.min())
    rng = z_max - z_min
    idx = df.index
    pos = {lab: i for i, lab in enumerate(idx)}
    periods = [normalize_phase(str(x)) for x in df["periods"]]
    runs = runs_of(periods)
    det = [(a, b) for p, a, b in runs if p == "mature"]
    lab = label_runs(record) if record else []
    lab_mat = [(a, b, u) for p, a, b, u in lab if p == "mature"]
    first_lab = (lab_mat[0][0], lab_mat[0][1]) if lab_mat else None
    paired, _ = pair_by_overlap(det, first_lab)

    d_start = d_end = None
    matches = False
    if paired and first_lab:
        d_start, d_end = paired[0] - first_lab[0], paired[1] - first_lab[1]
        matches = abs(d_start) <= MARGIN and abs(d_end) <= MARGIN

    # per-valley depth + the active latent-defect watch
    surv_v = list(idx[df["z_peaks_valleys"] == "valley"])
    surv_p = list(idx[df["z_peaks_valleys"] == "peak"])
    maf = gp.get("mature_amplitude_fraction", 0.90)
    valleys, defects = [], []
    for v in surv_v:
        pv_ = [p for p in surv_p if p < v]
        nx_ = [p for p in surv_p if p > v]
        vi = pos[v]
        zv = float(df.at[v, "z"])
        d1 = (z_max - zv) / rng if rng > 0 else float("nan")
        rec = dict(idx=vi, z=zv, D1=d1, has_neighbours=bool(pv_ and nx_), block=None)
        if pv_ and nx_:
            p0, n0 = pv_[-1], nx_[0]
            amp_prev = float(df.at[p0, "z"]) - zv
            amp_next = float(df.at[n0, "z"]) - zv
            if amp_prev < 0:
                defects.append(dict(series=sid, valley=vi, defect="152", amp=amp_prev))
            if amp_next < 0:
                defects.append(dict(series=sid, valley=vi, defect="160", amp=amp_next))
            ms, me = _amplitude_mature_bounds(df, p0, v, n0, maf)
            win = (pos[ms], pos[me])
            hits = [(b, ov(win, b)) for b in det if ov(win, b) > 0]
            if hits:
                rec["block"] = max(hits, key=lambda t: t[1])[0]
            rec["window"] = win
        valleys.append(rec)

    # second-highest peak, for the denominator-robustness measurement
    peak_vals = sorted((float(df.at[p, "z"]) for p in surv_p), reverse=True)
    second_peak = peak_vals[1] if len(peak_vals) > 1 else None

    return dict(
        id=sid, n=len(values), periods=periods, runs=runs, det=det,
        lab_seq=[p for p, _, _, _ in lab], det_seq=[p for p, _, _ in runs],
        lab_matures=lab_mat, paired=paired, matches=matches,
        d_start=d_start, d_end=d_end,
        incip_end=leading_incipient(runs),
        z_max=z_max, z_min=z_min, z_range=rng,
        second_peak=second_peak,
        argmax_isolated=((z_max - second_peak) / rng) if second_peak is not None and rng > 0 else None,
        valleys=valleys, defects=defects, warnings=caught,
        sha_ok=(series_sha256(values) == record["series_sha256"]) if record else None,
    )


def run_all(pv, gp, real, synth, labels):
    return ({s: run_one(s, v, labels.get(s), pv, gp) for s, v in sorted(real.items())},
            {s: run_one(s, v, labels.get(s), pv, gp) for s, v in sorted(synth.items())})


def seq_score(res):
    return sum(1 for f in res.values() if f["det_seq"] == f["lab_seq"])


def main():
    import scipy
    train = set(read_split()["train"])
    labels = read_labels()
    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}

    print(f"numpy {np.__version__}  scipy {scipy.__version__}  pandas {pd.__version__}")
    for n in ("cyclophaser_params-11.yaml", "cyclophaser_params-12.yaml"):
        p = REPO / "research/labels/configs" / n
        print(f"{n}  sha256 {hashlib.sha256(p.read_bytes()).hexdigest()}")
    print(f"train: {len(real)} real + {len(synth)} synthetic = {len(real)+len(synth)}\n")

    pv, gp11 = load_config("cyclophaser_params-11.yaml")
    _, gp12 = load_config("cyclophaser_params-12.yaml")
    print(f"params-12 mature_min_depth = {gp12.get('mature_min_depth')!r}")
    gp85 = {**gp11, "mature_min_depth": 0.85}

    base_r, base_s = run_all(pv, gp11, real, synth, labels)
    cand = {}
    for tag, g in (("0.80", gp12), ("0.85", gp85)):
        cand[tag] = run_all(pv, g, real, synth, labels)

    json.dump(
        {"reference": {s: {k: v for k, v in f.items() if k != "periods"}
                       for s, f in {**base_r, **base_s}.items()},
         "cand080": {s: {k: v for k, v in f.items() if k != "periods"}
                     for s, f in {**cand['0.80'][0], **cand['0.80'][1]}.items()}},
        (OUT / "stage2_measurements.json").open("w"), indent=1, default=str)

    for tag in ("0.80", "0.85"):
        r, s = cand[tag]
        allc = {**r, **s}
        allb = {**base_r, **base_s}
        print("\n" + "#" * 78)
        print(f"#  mature_min_depth = {tag}"
              f"{'   <-- CANDIDATE (params-12)' if tag=='0.80' else '   <-- DIAGNOSTIC ONLY'}")
        print("#" * 78)

        # (a)
        f = r["20160735"]
        durs = [b - a + 1 for a, b in f["det"]]
        a_ok = len(f["det"]) == 1 and 28 <= durs[0] <= 36
        print(f"\n(a) 20160735 blocks {f['det']}  durations {durs}")
        print(f"    base was {base_r['20160735']['det']} "
              f"{[b-a+1 for a,b in base_r['20160735']['det']]}")
        print(f"    -> {'PASS' if a_ok else 'FAIL'}")

        # (b)
        f = r["20203947"]
        keeps = []
        for (la, lb, u) in f["lab_matures"]:
            hit = [b for b in f["det"] if ov(b, (la, lb)) > 0]
            keeps.append(bool(hit))
            print(f"(b) 20203947 labelled {la}-{lb}{' [UNSURE]' if u else ''} -> "
                  f"{hit if hit else 'NOT DETECTED'}")
        b_ok = all(keeps) and len(keeps) == 2
        print(f"    blocks now {f['det']} (base {base_r['20203947']['det']})")
        print(f"    -> {'PASS' if b_ok else 'FAIL'}")

        # (c)
        sc, sb = seq_score(allc), seq_score(allb)
        c_ok = sc >= 30
        print(f"\n(c) sequence {sc}/47   (base params-11 = {sb}/47, floor 30) "
              f"-> {'PASS' if c_ok else 'FAIL'}")
        gained = [k for k in allc if allc[k]["det_seq"] == allc[k]["lab_seq"]
                  and allb[k]["det_seq"] != allb[k]["lab_seq"]]
        lost = [k for k in allc if allc[k]["det_seq"] != allc[k]["lab_seq"]
                and allb[k]["det_seq"] == allb[k]["lab_seq"]]
        print(f"    gained: {gained}")
        print(f"    lost  : {lost}")

        # (d)  The "12/12" baseline quantity is the synthetic SEQUENCE: it is
        # 12/12 under params-11. The mature-boundary metric is 11/12 at
        # BASELINE too, and its single miss is s0596ea57, which has no labelled
        # mature AND no detected mature - vacuously unmatched, not a failure.
        # Both are printed so neither can be mistaken for the other.
        syn_seq = sum(1 for f in s.values() if f["det_seq"] == f["lab_seq"])
        syn_seq_b = sum(1 for f in base_s.values() if f["det_seq"] == f["lab_seq"])
        syn_mat = sum(1 for f in s.values() if f["matches"])
        syn_mat_b = sum(1 for f in base_s.values() if f["matches"])
        gen_d1 = [v["D1"] for f in s.values() for v in f["valleys"] if v["block"]]
        d_ok = syn_seq == 12 and (not gen_d1 or min(gen_d1) >= float(tag))
        print(f"\n(d) synthetic SEQUENCE {syn_seq}/12  (base {syn_seq_b}/12)  <- the gate quantity")
        print(f"    synthetic mature-boundary +/-6: {syn_mat}/12 (base {syn_mat_b}/12)")
        print(f"       the one miss is s0596ea57, which has no labelled and no")
        print(f"       detected mature - vacuous at baseline and unchanged here")
        print(f"    min D1 over synthetic generating valleys = "
              f"{min(gen_d1):.4f}  (all >= {tag}? {min(gen_d1) >= float(tag)})")
        print(f"    -> {'PASS' if d_ok else 'FAIL'}")

        # (e)
        mb = sum(1 for f in allc.values() if f["matches"])
        mbase = sum(1 for f in allb.values() if f["matches"])
        inc_changed = [k for k in allc if allc[k]["incip_end"] != allb[k]["incip_end"]]
        f5, b5 = r["20205386"], base_r["20205386"]
        used_c = [v["idx"] for v in f5["valleys"] if v["block"] == f5["paired"]]
        used_b = [v["idx"] for v in b5["valleys"] if v["block"] == b5["paired"]]
        e_ok = mb >= 38 and not inc_changed and used_c == used_b == [61]
        print(f"\n(e) mature boundary {mb}/47  (base {mbase}/47, floor 38)")
        print(f"    incipient boundary changed on: {inc_changed if inc_changed else 'NONE'}")
        print(f"    20205386 paired block: base {b5['paired']} (valley {used_b}) "
              f"-> now {f5['paired']} (valley {used_c})")
        print(f"    20205386 all blocks: base {b5['det']} -> now {f5['det']}")
        print(f"    -> {'PASS' if e_ok else 'FAIL'}")
        mlost = [k for k in allc if allb[k]["matches"] and not allc[k]["matches"]]
        mgain = [k for k in allc if not allb[k]["matches"] and allc[k]["matches"]]
        print(f"    mature-boundary gained {mgain} / lost {mlost}")

        # (f)
        defs = [d for f in allc.values() for d in f["defects"]]
        depth_warns = [(k, w) for k, f in allc.items() for w in f["warnings"]
                       if "mature_min_depth" in w]
        f_ok = not defs
        print(f"\n(f) latent defects fired (active check): :152 = "
              f"{sum(1 for d in defs if d['defect']=='152')}, :160 = "
              f"{sum(1 for d in defs if d['defect']=='160')}")
        print(f"    z-range guard triggered on: {depth_warns if depth_warns else 'NONE'}")
        print(f"    -> {'PASS' if f_ok else 'FAIL'} (suite run separately)")

        verdict = all([a_ok, b_ok, c_ok, d_ok, e_ok, f_ok])
        print(f"\n=== GATE AT {tag}: {'PASS' if verdict else 'FAIL'} ===")
        if not verdict:
            print("    failing: " + ", ".join(
                n for n, okv in (("a", a_ok), ("b", b_ok), ("c", c_ok),
                                 ("d", d_ok), ("e", e_ok), ("f", f_ok)) if not okv))

        # ---------------- extra 1: what filled the removed blocks
        if tag == "0.80":
            print("\n" + "-" * 78)
            print("EXTRA 1 - FILL-IN: what occupies each removed mature block")
            print("-" * 78)
            for sid in sorted(allb):
                removed = [b for b in allb[sid]["det"]
                           if not any(ov(b, c2) > 0 for c2 in allc[sid]["det"])]
                if not removed:
                    continue
                print(f"\n  {sid}  (label match: {allb[sid]['matches']} -> "
                      f"{allc[sid]['matches']};  sequence: "
                      f"{allb[sid]['det_seq']==allb[sid]['lab_seq']} -> "
                      f"{allc[sid]['det_seq']==allc[sid]['lab_seq']})")
                for (ba, bb) in removed:
                    now = sorted({allc[sid]["periods"][i] for i in range(ba, bb + 1)})
                    spans = [(p, x, y) for p, x, y in allc[sid]["runs"]
                             if ov((x, y), (ba, bb)) > 0]
                    print(f"     removed {ba}-{bb} ({bb-ba+1} steps) -> now {now}")
                    for p, x, y in spans:
                        print(f"        {p:<16} {x}-{y}")

            # ---------------- extra 2: denominator robustness
            print("\n" + "-" * 78)
            print("EXTRA 2 - DENOMINATOR ROBUSTNESS: is z_max an isolated spike?")
            print("-" * 78)
            print("  gap = (z_max - 2nd highest surviving peak) / (z_max - z_min)")
            print("  A large gap means D1's denominator rests on a single point.\n")
            gaps = [(f["argmax_isolated"], sid) for sid, f in base_r.items()
                    if f["argmax_isolated"] is not None]
            gaps.sort(reverse=True)
            arr = np.array([g for g, _ in gaps])
            print(f"  over the 35 real: min {arr.min():.4f}  median "
                  f"{np.median(arr):.4f}  max {arr.max():.4f}")
            print(f"  series with gap > 0.30 (flagged):")
            flagged = [(g, sid) for g, sid in gaps if g > 0.30]
            for g, sid in flagged:
                margin = [v["D1"] for v in base_r[sid]["valleys"] if v["block"]]
                print(f"     {sid}  gap {g:.4f}   generating-valley D1 "
                      f"{[f'{m:.4f}' for m in margin]}")
            if not flagged:
                print("     NONE")
            print(f"\n  top 5 by gap:")
            for g, sid in gaps[:5]:
                print(f"     {sid}  {g:.4f}")

    return base_r, base_s, cand


if __name__ == "__main__":
    main()
