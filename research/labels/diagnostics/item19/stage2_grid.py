#!/usr/bin/env python
"""Item 19/20 part 1, STAGE 2 - the 45-cell grid, TRAIN split only.

prominence_relative   {0.20, 0.25, ..., 0.60}   (9 values)
mature_amplitude_fraction {0.80, 0.85, ..., 1.00}  (5 values)
every other parameter held at params-10.

Each cell is scored against the params-10 reference on the six declared gate
criteria (a'), (b), (c), (d), (e), (f). Writes:
  stage2_grid.md        the 9x5 table, the long per-cell table, PASS cells
  stage2_losses.md      where each lost mature disappears (A/B/C/D)
  stage2_cells.json     raw per-cell results
"""
from __future__ import annotations

import json, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import item19_core as C
from item19_core import OUT, MARGIN
from labels_core import read_labels
from cyclophaser.determine_periods import process_vorticity
from cyclophaser.find_stages import _amplitude_mature_bounds

TARGET = "20160735"
WATCH = ("20191014", "20203947")
LAB_START, LAB_END_EXCL = 145, 178          # as the brief states them

PROMS = [round(0.20 + 0.05 * i, 2) for i in range(9)]
MAFS = [round(0.80 + 0.05 * i, 2) for i in range(5)]


# --------------------------------------------------------------------------- #
def attribute_loss(values, pv, gp):
    """Why does this series have no mature in this cell? -> (code, detail).

    A  the generating z valley, or a flanking z peak, was cut by the relative
       prominence filter, so no mature candidate is even formed
       (determine_periods.py:203-208 / find_stages.py:261-262)
    B  a candidate forms, but the amplitude window collapses to the valley alone
       (<= 1 step) - find_stages.py:135-160. The empty-window guard at
       find_stages.py:284-285 can never fire, because the window always contains
       z_valley itself, so a degenerate window is cleared one step later by the
       neighbour check. Reported as B because the amplitude window is the cause.
    C  the threshold_mature_length duration check discarded it
       (find_stages.py:304-312) - UNREACHABLE under mature_method='amplitude'
    D  candidates survived and produced windows, but the neighbour check cleared
       them (find_stages.py:340-352)
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
    z = np.asarray(vort.vorticity_smoothed2.values, dtype=float)
    df = pd.DataFrame({"z": z}, index=vort.vorticity_smoothed2.to_dataframe().index)
    rel = C.extrema_with_prominence(z)
    kp = C.surviving(rel["peak"], gp["prominence_relative"])
    kv = C.surviving(rel["valley"], gp["prominence_relative"])

    wins = []
    for v in kv:
        prev = [p for p in kp if p < v]
        nxt = [p for p in kp if p > v]
        if not prev or not nxt:
            continue
        try:
            ms, me = _amplitude_mature_bounds(df, df.index[prev[-1]], df.index[v],
                                              df.index[nxt[0]],
                                              gp["mature_amplitude_fraction"])
        except Exception as exc:
            return "D", f"_amplitude_mature_bounds raised: {type(exc).__name__}: {exc}"
        wins.append((df.index.get_loc(ms), df.index.get_loc(me)))
    if not wins:
        return "A", "no surviving z valley with a flanking z peak on each side"
    lens = [b - a + 1 for a, b in wins]
    if max(lens) <= 1:
        return "B", (f"{len(wins)} candidate(s), every amplitude window collapsed to "
                     f"the valley alone (lengths {lens})")
    return "D", (f"{len(wins)} candidate window(s) formed (lengths {lens}), all "
                 f"cleared by the intensification/decay neighbour check")


def evaluate_cell(facts, ref, real, synth):
    """The six declared criteria, each PASS/FAIL, against the params-10 reference."""
    res, why = {}, {}

    lost = [s for s in ref if ref[s]["n_det_mature"] > 0 and facts[s]["n_det_mature"] == 0]
    res["a'"] = not lost
    why["a'"] = f"{len(lost)} series lost their mature" + (f": {lost}" if lost else "")

    t = facts[TARGET]
    dstart = t["paired"][0] - LAB_START if t["paired"] else None
    dend = (t["paired"][1] + 1) - LAB_END_EXCL if t["paired"] else None
    res["b"] = bool(t["n_det_mature"] == 1 and dstart is not None
                    and abs(dstart) <= MARGIN and abs(dend) <= MARGIN)
    why["b"] = (f"n_mature={t['n_det_mature']}, "
                f"Dstart={dstart}, Dend={dend}")

    broke = [s for s in ref if ref[s]["seq_match"] and not facts[s]["seq_match"]]
    res["c"] = not broke
    why["c"] = f"{len(broke)} series stopped matching" + (f": {broke}" if broke else "")

    d_bad = []
    for s in WATCH:
        worse_seq = ref[s]["seq_match"] and not facts[s]["seq_match"]
        a, b = ref[s]["abs_sum"], facts[s]["abs_sum"]
        worse_bnd = (b is None) if a is not None else False
        if a is not None and b is not None:
            worse_bnd = b > a
        if worse_seq or worse_bnd:
            d_bad.append(f"{s}(seq {ref[s]['seq_match']}->{facts[s]['seq_match']}, "
                         f"sum|D| {a}->{b})")
    res["d"] = not d_bad
    why["d"] = "; ".join(d_bad) if d_bad else "neither worsened"

    moved = [s for s in ref if facts[s]["incip_end"] != ref[s]["incip_end"]]
    res["e"] = not moved
    why["e"] = f"{len(moved)} series moved" + (f": {moved[:6]}" if moved else "")

    syn_ref = sum(ref[s]["seq_match"] for s in synth)
    syn_new = sum(facts[s]["seq_match"] for s in synth)
    res["f"] = syn_new >= syn_ref
    why["f"] = f"synthetic sequence {syn_ref} -> {syn_new}"
    return res, why


def main():
    pv, gp0 = C.load_config()
    real, synth = C.load_train_series()
    series = {**real, **synth}
    labels = read_labels()
    print(f"config : {C.CONFIG.name}   train: {len(real)}+{len(synth)}={len(series)}")

    ref = C.facts_for_config(series, labels, pv, gp0)
    print(f"reference: sequence {sum(f['seq_match'] for f in ref.values())}/{len(series)}, "
          f"{TARGET} has {ref[TARGET]['n_det_mature']} mature block(s)")

    cells, losses = [], []
    for pr in PROMS:
        for maf in MAFS:
            gp = dict(gp0, prominence_relative=pr, mature_amplitude_fraction=maf)
            facts = C.facts_for_config(series, labels, pv, gp)
            res, why = evaluate_cell(facts, ref, real, synth)
            errs = [s for s in series if facts[s].get("error")]
            if errs:
                res = {k: False for k in res}
                why = dict(why, error=f"detector raised on {len(errs)} series: {errs}")
            n_ok = sum(res.values())
            cells.append(dict(pr=pr, maf=maf, res=res, why=why, n_ok=n_ok, errors=errs,
                              seq=sum(f["seq_match"] for f in facts.values()),
                              syn_seq=sum(facts[s]["seq_match"] for s in synth),
                              tgt_n=facts[TARGET]["n_det_mature"],
                              no_mature=[s for s in series if facts[s]["n_det_mature"] == 0]))
            for s in series:
                if facts[s].get("error"):
                    continue
                if ref[s]["n_det_mature"] > 0 and facts[s]["n_det_mature"] == 0:
                    code, detail = attribute_loss(series[s], pv, gp)
                    losses.append(dict(pr=pr, maf=maf, id=s,
                                       src="real" if s in real else "syn",
                                       code=code, detail=detail))
            print(f"  pr={pr:.2f} maf={maf:.2f}  {n_ok}/6  "
                  f"{''.join(k if v else '.' for k, v in res.items())}  "
                  f"seq={cells[-1]['seq']}  tgt_mat={cells[-1]['tgt_n']}", flush=True)

    (OUT / "stage2_cells.json").write_text(json.dumps(cells, indent=1, default=str))

    # ---------------------------------------------------------------- 9x5 table
    grid = {(c["pr"], c["maf"]): c for c in cells}
    L = ["# Stage 2 - the 45-cell grid (TRAIN only)", "",
         "Base config: `research/labels/configs/cyclophaser_params-10.yaml`. Only",
         "`prominence_relative` and `mature_amplitude_fraction` vary; every other",
         "parameter is held at params-10. Reference for every comparison is the",
         "params-10 cell itself.", "",
         f"Reference: sequence {sum(f['seq_match'] for f in ref.values())}/{len(series)}, "
         f"`{TARGET}` has {ref[TARGET]['n_det_mature']} mature blocks, "
         f"{sum(1 for f in ref.values() if f['n_det_mature'] == 0)} series with no mature.",
         "",
         "## Criteria met, out of 6", "",
         "| prom_rel \\ maf | " + " | ".join(f"{m:.2f}" for m in MAFS) + " |",
         "|---|" + "---|" * len(MAFS)]
    for pr in PROMS:
        L.append(f"| **{pr:.2f}** | " +
                 " | ".join(str(grid[(pr, m)]["n_ok"]) for m in MAFS) + " |")

    L += ["", "## Per-cell detail", "",
          "Letters show which criteria PASS; `.` marks a failure in that slot, in the",
          "order (a') (b) (c) (d) (e) (f).", "",
          "| prom_rel | maf | met | flags | train seq | syn seq | mature blocks in "
          f"`{TARGET}` | series with no mature |",
          "|---|---|---|---|---|---|---|---|"]
    for c in cells:
        flags = "".join(k if v else "." for k, v in c["res"].items())
        L.append(f"| {c['pr']:.2f} | {c['maf']:.2f} | {c['n_ok']}/6 | `{flags}` | "
                 f"{c['seq']}/{len(series)} | {c['syn_seq']}/{len(synth)} | "
                 f"{c['tgt_n']} | {len(c['no_mature'])}"
                 f"{' **ERR**' if c['errors'] else ''} |")

    winners = [c for c in cells if c["n_ok"] == 6]
    L += ["", "## Cells meeting all six criteria", "",
          ("**None.**" if not winners else
           "\n".join(f"* `prominence_relative={c['pr']}`, "
                     f"`mature_amplitude_fraction={c['maf']}`" for c in winners))]

    # per-criterion failure counts, and why (b) fails where it does
    L += ["", "## How often each criterion fails, over the 45 cells", "",
          "| criterion | cells failing |", "|---|---|"]
    for k in ("a'", "b", "c", "d", "e", "f"):
        L.append(f"| ({k}) | {sum(1 for c in cells if not c['res'][k])}/45 |")

    L += ["", f"## Criterion (b) - `{TARGET}` cell by cell", "",
          f"Label: mature starts 145, ends 178 (exclusive), 33 steps. `Dend` compares the",
          "detected block's exclusive end with 178, exactly as the gate states it; the",
          "value is the same either way as long as both sides use the same convention.", "",
          "| prom_rel | maf | n mature | Dstart | Dend |", "|---|---|---|---|---|"]
    for c in cells:
        L.append(f"| {c['pr']:.2f} | {c['maf']:.2f} | {c['tgt_n']} | "
                 f"{c['why']['b'].split('Dstart=')[1].split(',')[0]} | "
                 f"{c['why']['b'].split('Dend=')[1]} |")
    (OUT / "stage2_grid.md").write_text("\n".join(L) + "\n")
    print("wrote stage2_grid.md")

    # ---------------------------------------------------------------- losses
    by_series = {}
    for r in losses:
        by_series.setdefault(r["id"], []).append(r)
    M = ["# Stage 2 - where a lost mature disappears (A/B/C/D)", "",
         "Every (cell, series) pair in which a series that HAS a mature under params-10",
         "ends up with none. Attribution is recomputed from the package's own",
         "`_amplitude_mature_bounds` and the same extrema filter the detector runs.", "",
         "| code | mechanism | file:line |", "|---|---|---|",
         "| A | generating z valley or a flanking z peak cut by the relative prominence "
         "filter, so no candidate forms | `determine_periods.py:203-208`, "
         "`find_stages.py:261-262` |",
         "| B | a candidate forms but the amplitude window collapses to the valley "
         "alone (<= 1 step), and is cleared one step later | `find_stages.py:135-160` |",
         "| C | `threshold_mature_length` duration check | `find_stages.py:304-312` "
         "- **unreachable under `mature_method='amplitude'`** |",
         "| D | window formed, neighbour check cleared it | `find_stages.py:340-352` |",
         ""]
    if not losses:
        M.append("**No series loses its mature in any of the 45 cells.**")
    else:
        deg = [r for r in losses if r["maf"] == 1.00]
        live = [r for r in losses if r["maf"] != 1.00]
        M += [f"**{len(losses)} (cell, series) losses over "
              f"{len({r['id'] for r in losses})} distinct series.**", "",
              f"{len(deg)} of them are the degenerate `mature_amplitude_fraction=1.00`",
              "column, where the level equals `z` at the valley and every window",
              "collapses to a single step. That column is reported separately: it says",
              "nothing about the trade-off under investigation.", ""]
        for name, rs_all in (("`mature_amplitude_fraction` < 1.00 - the informative cells", live),
                             ("`mature_amplitude_fraction` = 1.00 - the degenerate column", deg)):
            counts = {k: len({r["id"] for r in rs_all if r["code"] == k}) for k in "ABCD"}
            M += [f"### {name}", "",
                  f"{len(rs_all)} (cell, series) losses over "
                  f"{len({r['id'] for r in rs_all})} distinct series. Distinct series by "
                  "code: " + ", ".join(f"**{k}** {counts[k]}" for k in "ABCD"), ""]
            if not rs_all:
                M += ["_none_", ""]
                continue
            M += ["| series | src | code | cells | prom_rel range | maf range | detail |",
                  "|---|---|---|---|---|---|---|"]
            grp = {}
            for r in rs_all:
                grp.setdefault(r["id"], []).append(r)
            for sid, rs in sorted(grp.items()):
                codes = sorted({r["code"] for r in rs})
                prs = sorted({r["pr"] for r in rs})
                mfs = sorted({r["maf"] for r in rs})
                M.append(f"| `{sid}` | {rs[0]['src']} | {'/'.join(codes)} | {len(rs)} | "
                         f"{min(prs):.2f}-{max(prs):.2f} | {min(mfs):.2f}-{max(mfs):.2f} | "
                         f"{rs[-1]['detail']} |")
            M.append("")
    (OUT / "stage2_losses.md").write_text("\n".join(M) + "\n")
    print("wrote stage2_losses.md")
    print(f"\nPASS cells: {len(winners)}/45 "
          f"{[(c['pr'], c['maf']) for c in winners] if winners else ''}")


if __name__ == "__main__":
    main()
