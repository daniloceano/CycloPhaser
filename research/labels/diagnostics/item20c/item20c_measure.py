#!/usr/bin/env python
"""Front 20(c) stage 1 - MEASUREMENT ONLY. No line of cyclophaser/ is modified.

Question: does a PROPORTIONAL duration floor exist - a single ratio r such that
rejecting any mature block whose duration is below r times the duration of an
"anchor" block of the same series removes the spurious blocks without cutting
any block that matches a manual label?

This script answers that question by measurement. It implements nothing.

Method
------
The detector's own pipeline is replayed (determine_periods.get_periods) under
research/labels/configs/cyclophaser_params-12.yaml. To attribute a FINAL mature
block to the z_valley that generated it, the pipeline is re-run a second time
step by step with the real package functions, stopping to record the per-valley
amplitude window that find_mature_stage builds. The replay is then verified
against the single-call get_periods output: the two `periods` columns must be
identical on every series, otherwise the attribution is not trustworthy and the
script aborts.

TRAIN SPLIT ONLY. read_split()["test"] is never read here.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO / "research" / "labels" / "diagnostics" / "item19"))
sys.path.insert(0, str(REPO))

from labels_core import (load_real_series, load_synthetic_series, normalize_phase,
                         read_labels, read_split, series_sha256)
# pair_by_overlap is imported from the FROZEN item 19/20 instrument on purpose.
# item19_core's own CONFIG still points at params-10; it is never used here -
# params-12 is loaded independently below.
from item19_core import pair_by_overlap, phase_runs, label_runs, MARGIN

from cyclophaser.determine_periods import (get_periods, process_vorticity,
                                           find_peaks_valleys, post_process_periods)
from cyclophaser.find_stages import (_amplitude_mature_bounds, find_mature_stage,
                                     find_intensification_period, find_decay_period,
                                     find_residual_period, find_incipient_period)

CONFIG = REPO / "research" / "labels" / "configs" / "cyclophaser_params-12.yaml"
CONFIG_SHA = "39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3"
OUT = REPO / "research" / "labels" / "diagnostics" / "item20c"

PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")

# DURATION CONVENTION, declared once and used everywhere below:
#     duration = end_idx - start_idx + 1      (number of timesteps in the block)
# i.e. a block covering a single timestep has duration 1, never 0. The ratio of
# two durations is therefore always finite and strictly positive.
def duration(start, end):
    return end - start + 1


def sha256_of(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config(path=CONFIG):
    import inspect
    doc = yaml.safe_load(Path(path).read_text()) or {}
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def blocks_of(names, phase="mature"):
    """[(start_idx, end_inclusive), ...] positional, over a list of phase names."""
    return [(a, b) for p, a, b in phase_runs(names) if p == phase]


def replay(values, pv, gp):
    """Re-run the pipeline with the real package functions, recording the
    per-valley mature windows that find_mature_stage builds.

    Returns (periods_names, valley_windows, depth_by_valley, defect_rows, z).
    valley_windows: [{'valley_idx', 'win_start', 'win_end', 'eligible', 'D1'}]
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)

    z_series = vort.vorticity_smoothed2
    df = z_series.to_dataframe().rename(columns={"vorticity_smoothed2": "z"})
    df["z_unfil"] = vort.zeta.to_dataframe()
    df["dz"] = vort.dz_dt_smoothed2.to_dataframe()
    df["dz2"] = vort.dz_dt2_smoothed2.to_dataframe()
    df["z_peaks_valleys"] = find_peaks_valleys(
        df["z"], prominence=gp.get("prominence"),
        prominence_relative=gp.get("prominence_relative"))
    df["dz_peaks_valleys"] = find_peaks_valleys(df["dz"])
    df["dz2_peaks_valleys"] = find_peaks_valleys(df["dz2"])
    df["periods"] = np.nan
    df["periods"] = df["periods"].astype("object")

    args = dict(gp)
    args.setdefault("threshold_mature_distance", gp["threshold_mature_distance"])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = find_intensification_period(df, **args)
        df = find_decay_period(df, **args)

    # ---- record what find_mature_stage will do, without changing it ---------
    pos = {ts: i for i, ts in enumerate(df.index)}
    z_all = df["z"].to_numpy(dtype=float)
    z_max, z_min = np.nanmax(z_all), np.nanmin(z_all)
    z_range = z_max - z_min

    z_valleys_all = df[df["z_peaks_valleys"] == "valley"].index
    z_peaks = df[df["z_peaks_valleys"] == "peak"].index
    maf = args["mature_amplitude_fraction"]
    floor = args.get("mature_min_depth", 0.0)

    valley_windows = []
    defect_rows = []
    n_valleys_total = len(z_valleys_all)
    for zv in z_valleys_all:
        d1 = float((z_max - df.at[zv, "z"]) / z_range) if z_range > 0 else float("nan")
        prev_p = z_peaks[z_peaks < zv]
        next_p = z_peaks[z_peaks > zv]
        has_both = len(prev_p) > 0 and len(next_p) > 0
        eligible = bool(d1 >= floor) and has_both
        row = dict(valley_idx=pos[zv], D1=d1, eligible=eligible,
                   has_both_peaks=bool(has_both),
                   win_start=None, win_end=None)
        if has_both:
            pp, np_ = prev_p[-1], next_p[0]
            zval = float(df.at[zv, "z"])
            zpp = float(df.at[pp, "z"])
            znp = float(df.at[np_, "z"])
            # --- latent defect trigger conditions, recomputed, not inferred ---
            # find_stages.py:152-154  seg_prev = df.loc[prev_peak:z_valley]
            #   violations_prev[-1] + 1 indexes past the segment exactly when the
            #   LAST element of seg_prev (z at the valley itself) violates
            #   level_prev, i.e. z[valley] > level_prev.
            # find_stages.py:159-161  seg_next = df.loc[z_valley:next_peak]
            #   violations_next[0] - 1 wraps to index[-1] (silently returning
            #   next_z_peak) exactly when the FIRST element of seg_next (z at the
            #   valley itself) violates level_next, i.e. z[valley] > level_next.
            level_prev = zpp - maf * (zpp - zval)
            level_next = znp - maf * (znp - zval)
            defect_rows.append(dict(
                valley_idx=pos[zv], eligible=eligible,
                z_valley=zval, z_prev_peak=zpp, z_next_peak=znp,
                level_prev=level_prev, level_next=level_next,
                # margin > 0 would fire; how far from firing each valley is
                margin_152=float(zval - level_prev),
                margin_159=float(zval - level_next),
                # margin_152 == -(1-maf)*amplitude_prev identically, so with
                # maf < 1 the trigger reduces to a SIGN test on the amplitude:
                # the defect can fire only if amplitude <= 0, i.e. the valley's
                # z sits at or above its bounding peak's z.
                amp_prev=float(zpp - zval),
                amp_next=float(znp - zval),
                fires_152=bool(zval > level_prev),
                fires_159=bool(zval > level_next),
            ))
            if eligible:
                ms, me = _amplitude_mature_bounds(df, pp, zv, np_, maf)
                row["win_start"], row["win_end"] = pos[ms], pos[me]
        valley_windows.append(row)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = find_mature_stage(df, **args)
        post_mature = [normalize_phase(str(x)) for x in df["periods"]]
        df = find_residual_period(df, **args)
        df = post_process_periods(df)
        df = find_incipient_period(df, **args)

    names = [normalize_phase(str(x)) for x in df["periods"]]
    return names, valley_windows, defect_rows, z_all, post_mature, n_valleys_total


def attribute(block, valley_windows):
    """Which eligible valley's own amplitude window best explains this final
    mature block? Largest overlap wins; ties broken by the deeper valley."""
    bs, be = block
    best, best_ov = None, 0
    for vw in valley_windows:
        if vw["win_start"] is None:
            continue
        ov = min(be, vw["win_end"]) - max(bs, vw["win_start"]) + 1
        if ov > best_ov or (ov == best_ov and ov > 0 and best is not None
                            and vw["D1"] > best["D1"]):
            best, best_ov = vw, ov
    return best, best_ov


def main():
    sha = sha256_of(CONFIG)
    assert sha == CONFIG_SHA, f"params-12 sha256 mismatch: {sha}"
    pv, gp = load_config()
    print(f"params-12 sha256 VERIFIED: {sha}")
    print(f"mature_amplitude_fraction={gp['mature_amplitude_fraction']}  "
          f"mature_min_depth={gp['mature_min_depth']}  "
          f"prominence_relative={gp['prominence_relative']}")

    split = read_split()
    train = set(split["train"])
    labels = read_labels()
    real = {s: v for s, v in load_real_series().items() if s in train}
    synth = {s: v for s, v in load_synthetic_series()[0].items() if s in train}
    print(f"train: {len(real)} real + {len(synth)} synthetic = {len(real)+len(synth)}")
    assert len(real) + len(synth) == 47, "train split is not 47 series"

    rows = []
    defect_fire = {"152": [], "159": []}
    n_valleys_checked = 0
    n_valleys_eligible = 0
    n_valleys_all = 0
    worst = {"152": -float("inf"), "159": -float("inf")}
    near_rows = []
    amp_min = {"prev": float("inf"), "next": float("inf")}
    ident_max = [0.0]
    replay_mismatch = []
    baseline = dict(mature_within_margin=0, seq_match=0, synth_seq_match=0,
                    incipient={}, sha_ok=0, sha_checked=0)

    for pop, series in (("real", real), ("synthetic", synth)):
        for sid in sorted(series):
            values = series[sid]
            rec = labels.get(sid)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                res = get_periods(vort, **gp)
            ref_names = [normalize_phase(str(x)) for x in res["periods"]]

            names, vws, drows, z_all, post_mature, n_vtot = replay(values, pv, gp)
            if names != ref_names:
                replay_mismatch.append(sid)

            n_valleys_all += n_vtot
            n_valleys_checked += len(drows)
            for d in drows:
                near_rows.append((sid, d["valley_idx"], d["eligible"],
                                  d["margin_152"], d["margin_159"],
                                  d["z_valley"], d["z_prev_peak"], d["z_next_peak"]))
                worst["152"] = max(worst["152"], d["margin_152"])
                worst["159"] = max(worst["159"], d["margin_159"])
                amp_min["prev"] = min(amp_min["prev"], d["amp_prev"])
                amp_min["next"] = min(amp_min["next"], d["amp_next"])
                ident = abs(d["margin_152"] + (1 - gp["mature_amplitude_fraction"]) * d["amp_prev"])
                ident_max[0] = max(ident_max[0], ident / max(abs(d["amp_prev"]), 1e-30))
            n_valleys_eligible += sum(1 for d in drows if d["eligible"])
            for d in drows:
                if d["fires_152"]:
                    defect_fire["152"].append((sid, d))
                if d["fires_159"]:
                    defect_fire["159"].append((sid, d))

            det_mat = blocks_of(ref_names)
            lab = label_runs(rec) if rec else []
            lab_mat = [(a, b) for p, a, b, _, _ in lab if p == "mature"]
            lab_unsure = [bool(u) for p, a, b, _, u in lab if p == "mature"]
            det_seq = [p for p, _, _ in phase_runs(ref_names)]
            lab_seq = [p for p, _, _, _, _ in lab]

            if rec:
                baseline["sha_checked"] += 1
                if series_sha256(values) == rec["series_sha256"]:
                    baseline["sha_ok"] += 1
            first_lab = lab_mat[0] if lab_mat else None
            paired, ov = pair_by_overlap(det_mat, first_lab)
            if paired and first_lab:
                if abs(paired[0]-first_lab[0]) <= MARGIN and abs(paired[1]-first_lab[1]) <= MARGIN:
                    baseline["mature_within_margin"] += 1
            if det_seq == lab_seq:
                baseline["seq_match"] += 1
                if pop == "synthetic":
                    baseline["synth_seq_match"] += 1
            r0 = phase_runs(ref_names)
            baseline["incipient"][sid] = (r0[0][2] + 1) if r0 and r0[0][0] == "incipient" else None

            # --- per-block facts -------------------------------------------
            blocks = []
            for b in det_mat:
                vw, bov = attribute(b, vws)
                # pair THIS block against every labelled mature, both ends,
                # fixed margin 6 (item 19/20 instrument)
                match_i, d_s, d_e = None, None, None
                near_i, near_ds, near_de, near_ov = None, None, None, 0
                for k, lm in enumerate(lab_mat):
                    ds, de = b[0] - lm[0], b[1] - lm[1]
                    overlap = min(b[1], lm[1]) - max(b[0], lm[0]) + 1
                    if overlap > near_ov:
                        near_i, near_ds, near_de, near_ov = k, ds, de, overlap
                    if overlap > 0 and abs(ds) <= MARGIN and abs(de) <= MARGIN:
                        match_i, d_s, d_e = k, ds, de
                        break
                blocks.append(dict(
                    start=b[0], end=b[1], duration=duration(*b),
                    valley_idx=(vw["valley_idx"] if vw else None),
                    D1=(round(vw["D1"], 4) if vw else None),
                    attrib_overlap=bov,
                    matched_label=match_i,
                    d_start=d_s, d_end=d_e,
                    # best-overlapping label regardless of the margin, so a
                    # near-miss is visible instead of reading as "no label"
                    near_label=near_i, near_d_start=near_ds,
                    near_d_end=near_de, near_overlap=near_ov,
                ))
            rows.append(dict(id=sid, pop=pop, n=len(values), n_blocks=len(det_mat),
                             blocks=blocks, n_labels=len(lab_mat),
                             lab_mature=[list(x) for x in lab_mat],
                             lab_unsure=lab_unsure,
                             seq_match=(det_seq == lab_seq)))

    if replay_mismatch:
        print("FATAL: replay does not reproduce get_periods on:", replay_mismatch)
        sys.exit(2)
    print(f"replay == get_periods on all {len(rows)}/47 series: attribution is sound")

    out = dict(
        config_sha256=sha,
        numpy=np.__version__, scipy=__import__("scipy").__version__,
        pandas=pd.__version__,
        duration_convention="end - start + 1",
        baseline=dict(mature_within_margin=baseline["mature_within_margin"],
                      seq_match=baseline["seq_match"],
                      synth_seq_match=baseline["synth_seq_match"],
                      sha_ok=f"{baseline['sha_ok']}/{baseline['sha_checked']}"),
        incipient=baseline["incipient"],
        defects=dict(
            valleys_in_series=n_valleys_all,
            valleys_checked=n_valleys_checked,
            valleys_eligible=n_valleys_eligible,
            worst_margin_152=worst["152"],
            worst_margin_159=worst["159"],
            min_amp_prev=amp_min["prev"],
            min_amp_next=amp_min["next"],
            identity_max_rel_error=ident_max[0],
            fires_152=[(s, d["valley_idx"]) for s, d in defect_fire["152"]],
            fires_159=[(s, d["valley_idx"]) for s, d in defect_fire["159"]],
        ),
        series=rows,
    )
    out["defects"]["closest_to_firing"] = dict(
        by_152=sorted(near_rows, key=lambda r: -r[3])[:8],
        by_159=sorted(near_rows, key=lambda r: -r[4])[:8])
    (OUT / "item20c_facts.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {OUT/'item20c_facts.json'}")
    print("\nclosest valleys to firing defect 152 (sid, valley, eligible, m152, m159):")
    for r in out["defects"]["closest_to_firing"]["by_152"][:6]:
        print("   ", r[0], f"v{r[1]}", f"elig={r[2]}", f"m152={r[3]:.3e}", f"m159={r[4]:.3e}")
    print("closest valleys to firing defect 159/160:")
    for r in out["defects"]["closest_to_firing"]["by_159"][:6]:
        print("   ", r[0], f"v{r[1]}", f"elig={r[2]}", f"m152={r[3]:.3e}", f"m159={r[4]:.3e}")

    multi = [r for r in rows if r["n_blocks"] > 1]
    print(f"\nseries with >1 mature block under params-12: {len(multi)}")
    for r in multi:
        print(f"  {r['id']} ({r['pop']}): {r['n_blocks']} blocks, "
              f"{[(b['start'], b['end'], b['duration'], b['D1'], b['matched_label']) for b in r['blocks']]}")
    print("\nbaseline:", out["baseline"])
    nomatch = [r for r in rows if r["n_blocks"] > 0 and
               all(b["matched_label"] is None for b in r["blocks"])]
    noblock = [r for r in rows if r["n_blocks"] == 0]
    nolabel = [r for r in rows if r["n_labels"] == 0]
    out["no_match_census"] = dict(
        blocks_but_no_match=[r["id"] for r in nomatch],
        no_detected_block=[r["id"] for r in noblock],
        no_labelled_mature=[r["id"] for r in nolabel])
    (OUT / "item20c_facts.json").write_text(json.dumps(out, indent=2, default=str))
    print("\nno block matched any label:", [r["id"] for r in nomatch])
    print("no detected mature block at all:", [r["id"] for r in noblock])
    print("no labelled mature:", [r["id"] for r in nolabel])
    print("defects:", out["defects"]["valleys_checked"], "valleys checked;",
          "152 fires:", len(out["defects"]["fires_152"]),
          "159/160 fires:", len(out["defects"]["fires_159"]))
    print(f"  valleys in the 47 series: {n_valleys_all}; reaching the window code: "
          f"{n_valleys_checked}; eligible after the depth floor: {n_valleys_eligible}")
    print(f"  worst margin toward firing (positive would fire): "
          f"152 -> {worst['152']:.6g}, 159/160 -> {worst['159']:.6g}")
    print(f"  identity margin_152 == -(1-maf)*amp_prev holds to rel. "
          f"{ident_max[0]:.2e} over all {n_valleys_checked} valleys")
    print(f"  min amplitude_prev = {amp_min['prev']:.6g}; "
          f"min amplitude_next = {amp_min['next']:.6g} "
          f"(both > 0 => neither defect can fire)")


if __name__ == "__main__":
    main()
