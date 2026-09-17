#!/usr/bin/env python
"""Item 19/20 part 1, STAGE 1 - descriptive, params-10, TRAIN split only.

Produces, under research/labels/diagnostics/item19/:
  stage1_per_series.md              per-series scoring (step 2.1)
  stage1_baseline.txt               constant modal-sequence baseline (step 2.2)
  stage1_prominence.md              tables (i) (ii) (iii) (step 2.3)
  fig_prominence_distributions.png  (iii) the two distributions
  fig_20160735_params10.png         (step 2.4)

Read-only: no package code is touched, and the test split is never read.
"""
from __future__ import annotations

import sys, warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import item19_core as C
from item19_core import OUT, MARGIN
from labels_core import read_labels, normalize_phase
from cyclophaser.determine_periods import process_vorticity
from cyclophaser.find_stages import _amplitude_mature_bounds

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TARGET = "20160735"


def fmt(x, w=5):
    return ("-" if x is None else str(x)).rjust(w)


# ---------------------------------------------------------------- candidates
def mature_candidates(values, pv, gp):
    """Every z valley that reaches find_mature_stage's window sizing, with the
    amplitude window it produces.

    A candidate needs a SURVIVING z valley plus a surviving z peak on each side
    (find_stages.py:247-265); the window then comes from _amplitude_mature_bounds
    (find_stages.py:135-160), the package function itself.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
    z = np.asarray(vort.vorticity_smoothed2.values, dtype=float)
    df = pd.DataFrame({"z": z}, index=vort.vorticity_smoothed2.to_dataframe().index)
    rel = C.extrema_with_prominence(z)
    pr = gp["prominence_relative"]
    kp = C.surviving(rel["peak"], pr)
    kv = C.surviving(rel["valley"], pr)

    rows = []
    for v in kv:
        prev = [p for p in kp if p < v]
        nxt = [p for p in kp if p > v]
        if not prev or not nxt:
            rows.append(dict(valley=v, rel=rel["valley"][v], prev_peak=None,
                             next_peak=None, win=None, reason="no flanking z peak"))
            continue
        pp, np_ = prev[-1], nxt[0]
        ms, me = _amplitude_mature_bounds(df, df.index[pp], df.index[v], df.index[np_],
                                          gp["mature_amplitude_fraction"])
        a, b = df.index.get_loc(ms), df.index.get_loc(me)
        rows.append(dict(valley=v, rel=rel["valley"][v], prev_peak=pp, next_peak=np_,
                         win=(a, b), reason=""))
    return rows, rel, kp, kv, z, np.asarray(vort.zeta.values, dtype=float)


def generating_valley(block, kv, z):
    """The surviving z valley that produced a detected mature block."""
    inside = [v for v in kv if block[0] <= v <= block[1]]
    if not inside:
        return None
    return min(inside, key=lambda v: z[v])


def main():
    pv, gp = C.load_config()
    real, synth = C.load_train_series()
    series = {**real, **synth}
    labels = read_labels()
    print(f"config  : {C.CONFIG}")
    print(f"train   : {len(real)} real + {len(synth)} synthetic = {len(series)}")

    facts = C.facts_for_config(series, labels, pv, gp, want_z=True)
    bad_sha = [s for s, f in facts.items() if f["sha_ok"] is False]
    print("sha256 mismatches:", bad_sha or "none")

    # ------------------------------------------------ step 2.1 per-series table
    lines = ["# Stage 1 - per-series scoring under `params-10` (TRAIN only)", "",
             f"Config: `research/labels/configs/cyclophaser_params-10.yaml` "
             f"(`prominence_relative={gp['prominence_relative']}`, "
             f"`mature_amplitude_fraction={gp['mature_amplitude_fraction']}`).",
             "",
             "`seq` = detected phase sequence equals the labelled one. `incip` = number of",
             "leading `incipient` steps the detector produced (`-` = step 0 is not incipient),",
             "next to the label's own incipient end. `n_mat` = contiguous detected mature",
             "blocks. `Dstart`/`Dend` = detected minus labelled mature boundary, in steps,",
             "for the detected block with the largest overlap with the labelled mature.",
             f"`hit` = both within the fixed margin of {MARGIN} (item 17(d)).", "",
             "| series | src | n | seq | incip det/lab | n_mat | Dstart | Dend | hit |",
             "|---|---|---|---|---|---|---|---|---|"]
    for sid in sorted(series, key=lambda s: (facts[s]["id"] not in real, s)):
        f = facts[sid]
        rec = labels.get(sid)
        lab_inc = None
        if rec:
            lr = C.label_runs(rec)
            lab_inc = (lr[0][2] + 1) if lr and lr[0][0] == "incipient" else None
        lines.append(
            f"| `{sid}` | {'real' if sid in real else 'syn'} | {f['n']} | "
            f"{'yes' if f['seq_match'] else 'NO'} | "
            f"{f['incip_end'] if f['incip_end'] is not None else '-'} / "
            f"{lab_inc if lab_inc is not None else '-'} | "
            f"{f['n_det_mature']} | "
            f"{f['d_start'] if f['d_start'] is not None else '-'} | "
            f"{f['d_end'] if f['d_end'] is not None else '-'} | "
            f"{'yes' if f['matches_label'] else 'no'} |")

    def tot(ids):
        ids = list(ids)
        seq = sum(facts[s]["seq_match"] for s in ids)
        hit = sum(facts[s]["matches_label"] for s in ids)
        nom = sum(facts[s]["n_det_mature"] == 0 for s in ids)
        frag = sum(facts[s]["n_det_mature"] > 1 for s in ids)
        return len(ids), seq, hit, nom, frag

    lines += ["", "## Totals by source", "",
              "| set | n | sequence match | mature within +-6 both ends | no mature at all | >1 mature block |",
              "|---|---|---|---|---|---|"]
    for name, ids in (("real", real), ("synthetic", synth), ("ALL", series)):
        n, seq, hit, nom, frag = tot(ids)
        lines.append(f"| {name} | {n} | {seq}/{n} | {hit}/{n} | {nom} | {frag} |")
    (OUT / "stage1_per_series.md").write_text("\n".join(lines) + "\n")
    print("wrote stage1_per_series.md")

    # ------------------------------------------------ step 2.2 constant baseline
    lab_seqs = {s: tuple(facts[s]["lab_seq"]) for s in series}
    counts = Counter(lab_seqs.values())
    modal, modal_n = counts.most_common(1)[0]
    bl = [f"Stage 1 step 2 - constant baseline (TRAIN, same metric as the table above)",
          f"config: params-10 is irrelevant here - the baseline ignores the detector",
          "",
          f"modal labelled phase sequence over the 47 training labels:",
          f"  {' -> '.join(modal)}",
          f"  held by {modal_n} of {len(series)} series",
          "",
          "A constant predictor that emits that sequence for every series scores, on the",
          "same 'whole sequence matches' metric:",
          f"  ALL        {modal_n}/{len(series)}  ({100*modal_n/len(series):.1f}%)",
          f"  real       {sum(1 for s in real if lab_seqs[s]==modal)}/{len(real)}",
          f"  synthetic  {sum(1 for s in synth if lab_seqs[s]==modal)}/{len(synth)}",
          "",
          f"The detector under params-10 scores "
          f"{sum(facts[s]['seq_match'] for s in series)}/{len(series)} on the same metric",
          f"  real       {sum(facts[s]['seq_match'] for s in real)}/{len(real)}",
          f"  synthetic  {sum(facts[s]['seq_match'] for s in synth)}/{len(synth)}",
          "",
          "All labelled sequences by frequency:"]
    for seq, k in counts.most_common():
        bl.append(f"  {k:3d}  {' -> '.join(seq)}")
    (OUT / "stage1_baseline.txt").write_text("\n".join(bl) + "\n")
    print("wrote stage1_baseline.txt")

    # ------------------------------------------------ step 2.3 prominence
    rows_t, rel_t, kp_t, kv_t, z_t, zu_t = mature_candidates(series[TARGET], pv, gp)
    lab_t = facts[TARGET]["lab_mature"]
    det_t = facts[TARGET]["det_matures"]

    p = ["# Stage 1 step 3 - relative prominence (TRAIN only, `params-10`)", "",
         "**The quantity.** `scipy.signal.peak_prominences(signed_data, interior)[0]`,",
         "computed at `cyclophaser/determine_periods.py:188` on the FILTERED vorticity",
         "(`vorticity_smoothed2`, `determine_periods.py:1012`/`:1017`), and compared at",
         "`determine_periods.py:203-208` against",
         "`prominence_relative x max(prom_vals of the surviving interior set)`.",
         "The denominator is per series **and per extremum type** - peaks are refined on",
         "`data`, valleys on `-data` (`determine_periods.py:135-136`) - so every number",
         "below is a fraction of its own series' own valley maximum, never a vorticity",
         "unit. Indices 0 and N-1 are exempt from the filter",
         "(`determine_periods.py:180-181`) and are shown as `bnd`.", "",
         f"## (i) `{TARGET}` - every z valley that generates a mature candidate", "",
         f"Label: mature {lab_t[0]} -> {lab_t[1]}. Detected mature blocks under params-10: "
         f"{det_t if det_t else 'none'}.", "",
         "A candidate needs a surviving valley plus a surviving z peak on each side",
         "(`find_stages.py:247-265`); the window is `_amplitude_mature_bounds`",
         "(`find_stages.py:135-160`) called directly. `in label?` asks whether the valley",
         "position falls inside 145-178. `survived?` asks whether the window is still",
         "`mature` in the output, i.e. whether the neighbour check",
         "(`find_stages.py:340-352`) kept it.", "",
         "| valley idx | rel prominence | prev/next peak | amplitude window | len | in label? | survived? |",
         "|---|---|---|---|---|---|---|"]
    spurious, true_in_target = [], []
    for r in rows_t:
        v, rl, w = r["valley"], r["rel"], r["win"]
        rels = "bnd" if rl is None else f"{rl:.4f}"
        inlab = lab_t[0] <= v <= lab_t[1]
        surv = any(w and ds <= w[0] and w[1] <= de for ds, de in det_t) if w else False
        surv = surv or (w is not None and any(max(ds, w[0]) <= min(de, w[1]) for ds, de in det_t))
        p.append(f"| {v} | {rels} | "
                 f"{r['prev_peak'] if r['prev_peak'] is not None else '-'}/"
                 f"{r['next_peak'] if r['next_peak'] is not None else '-'} | "
                 f"{f'{w[0]}-{w[1]}' if w else r['reason']} | "
                 f"{(w[1]-w[0]+1) if w else '-'} | {'YES' if inlab else 'no'} | "
                 f"{'yes' if surv else 'no'} |")
        if rl is not None and w is not None:
            (true_in_target if inlab else spurious).append(rl)

    p += ["", "## (ii) every train series whose detected mature matches its label",
          "", f"Matching = |Dstart| <= {MARGIN} and |Dend| <= {MARGIN} against the labelled",
          "mature. The prominence shown is that of the surviving z valley inside the",
          "matching block (the deepest one, when a merged block holds more than one).", "",
          "| series | src | detected mature | label | Dstart | Dend | valley idx | rel prominence |",
          "|---|---|---|---|---|---|---|---|"]
    true_rels = []
    for sid in sorted(series, key=lambda s: (s not in real, s)):
        f = facts[sid]
        if not f["matches_label"]:
            continue
        rel = C.extrema_with_prominence(f["z"])
        kv = C.surviving(rel["valley"], gp["prominence_relative"])
        gv = generating_valley(f["paired"], kv, f["z"])
        rl = rel["valley"].get(gv) if gv is not None else None
        rels = "bnd" if rl is None else f"{rl:.4f}"
        if rl is not None:
            true_rels.append(rl)
        p.append(f"| `{sid}` | {'real' if sid in real else 'syn'} | "
                 f"{f['paired'][0]}-{f['paired'][1]} | {f['lab_mature'][0]}-{f['lab_mature'][1]} | "
                 f"{f['d_start']} | {f['d_end']} | {gv if gv is not None else '-'} | {rels} |")

    # (iii) the comparison
    sp = np.array(spurious, dtype=float)
    tr = np.array(true_rels, dtype=float)
    overlap = bool(len(sp) and len(tr) and max(sp.min(), tr.min()) <= min(sp.max(), tr.max()))
    p += ["", "## (iii) do the two distributions overlap?", "",
          f"* spurious - `{TARGET}` candidate valleys OUTSIDE the labelled mature: "
          f"n={len(sp)}, range **{sp.min():.4f} - {sp.max():.4f}**"
          if len(sp) else "* spurious: none",
          f"* true - valleys generating a label-matching mature across the train split: "
          f"n={len(tr)}, range **{tr.min():.4f} - {tr.max():.4f}**"
          if len(tr) else "* true: none", "",
          f"**The two distributions {'OVERLAP' if overlap else 'DO NOT overlap'}.**"]
    if overlap:
        lo, hi = max(sp.min(), tr.min()), min(sp.max(), tr.max())
        n_tr_in = int(((tr >= lo) & (tr <= hi)).sum())
        n_sp_in = int(((sp >= lo) & (sp <= hi)).sum())
        p += ["", f"Overlapping band **{lo:.4f} - {hi:.4f}**: it contains {n_sp_in} of the "
              f"{len(sp)} spurious values and {n_tr_in} of the {len(tr)} true ones.",
              "", f"A single threshold placed above the worst spurious value "
              f"({sp.max():.4f}) would also reject {int((tr <= sp.max()).sum())} of the "
              f"{len(tr)} true mature-generating valleys.",
              "", f"See `fig_prominence_distributions.png`."]
    (OUT / "stage1_prominence.md").write_text("\n".join(p) + "\n")
    print("wrote stage1_prominence.md")

    # ---- (iii) figure
    fig, ax = plt.subplots(figsize=(8, 4))
    bins = np.linspace(0, 1, 41)
    ax.hist(tr, bins=bins, alpha=.6, label=f"true mature-generating valleys (train, n={len(tr)})",
            color="#2c7fb8")
    ax.hist(sp, bins=bins, alpha=.6, label=f"spurious candidates in {TARGET} (n={len(sp)})",
            color="#d95f0e")
    ax.axvline(gp["prominence_relative"], color="k", ls="--", lw=1.2,
               label=f"params-10 prominence_relative = {gp['prominence_relative']}")
    if len(sp):
        ax.axvline(sp.max(), color="#d95f0e", ls=":", lw=1.2,
                   label=f"worst spurious = {sp.max():.3f}")
    ax.set_xlabel("relative prominence  (prominence / max valley prominence of that series)")
    ax.set_ylabel("count")
    ax.set_title("Stage 1(iii) - spurious vs true mature-generating z valleys, params-10")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig_prominence_distributions.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------ step 2.4 target figure
    f = facts[TARGET]
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]})
    ax = axes[0]
    ax.plot(zu_t, color="0.72", lw=.9, label="raw vorticity (zeta)")
    ax.plot(z_t, color="k", lw=1.4, label="filtered vorticity (vorticity_smoothed2)")
    for v in kv_t:
        ax.plot(v, z_t[v], "v", color="#d95f0e", ms=5)
    for k in kp_t:
        ax.plot(k, z_t[k], "^", color="#2c7fb8", ms=5)
    ax.plot([], [], "v", color="#d95f0e", ms=5, label="surviving z valleys")
    ax.plot([], [], "^", color="#2c7fb8", ms=5, label="surviving z peaks")
    ax.axvspan(lab_t[0], lab_t[1], color="#31a354", alpha=.18,
               label=f"labelled mature {lab_t[0]}-{lab_t[1]}")
    for i, (a, b) in enumerate(det_t):
        ax.axvspan(a, b, color="#de2d26", alpha=.30,
                   label="detected mature" if i == 0 else None)
    ax.set_ylabel("vorticity")
    ax.set_title(f"{TARGET} under params-10 "
                 f"(prominence_relative={gp['prominence_relative']}, "
                 f"mature_amplitude_fraction={gp['mature_amplitude_fraction']})")
    ax.legend(fontsize=7, loc="lower left")

    ax = axes[1]
    order = ["incipient", "intensification", "mature", "decay", "residual"]
    col = {"incipient": "#9ecae1", "intensification": "#fdae6b",
           "mature": "#de2d26", "decay": "#a1d99b", "residual": "#bcbddc"}
    for lane, (name, runs) in enumerate((
            ("detected", C.phase_runs(f["periods"])),
            ("labelled", [(r[0], r[1], r[2]) for r in f["lab_runs"]]))):
        for ph, a, b in runs:
            if ph in col:
                ax.barh(lane, b - a + 1, left=a, height=.6, color=col[ph])
                if b - a > 8:
                    ax.text((a + b) / 2, lane, ph[:5], ha="center", va="center", fontsize=6)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["detected", "labelled"])
    ax.set_xlabel("index"); ax.set_ylim(-.6, 1.6)
    fig.tight_layout()
    fig.savefig(OUT / "fig_20160735_params10.png", dpi=150)
    plt.close(fig)
    print("wrote figures")

    print(f"\nSUMMARY  sequence {sum(facts[s]['seq_match'] for s in series)}/{len(series)} "
          f"(real {sum(facts[s]['seq_match'] for s in real)}/{len(real)}, "
          f"syn {sum(facts[s]['seq_match'] for s in synth)}/{len(synth)})")
    print(f"         baseline (modal constant) {modal_n}/{len(series)}")
    print(f"         {TARGET}: {f['n_det_mature']} mature block(s) {det_t}")
    print(f"         spurious range {sp.min():.4f}-{sp.max():.4f}  "
          f"true range {tr.min():.4f}-{tr.max():.4f}  overlap={overlap}")


if __name__ == "__main__":
    main()
