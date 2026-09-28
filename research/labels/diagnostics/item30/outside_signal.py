"""Item 30, part 3 checkpoint — the 5 swell tracks the rule changes WITHOUT the signal,
and a narrow variant of the rule (measured, not adopted).

DIAGNOSTIC ONLY; nothing in cyclophaser/ changes.

Step 1. R3 found 15 swell tracks changed by `incipient_plateau_spare_intensification`
where 10 were predicted; 5 carry no item-30 signal (plateau boundary > argmin of the
filtered z). This identifies them, checks that none is TEST or VALIDATION, and
tabulates per track — boundary, peak, E, the mature after E in the pre-incipient
map, the bad/good mark, the z extrema between E and the boundary — with one figure
per track (params-14 | params-15) and a board. The per-track table and every
figure go to --out, OUTSIDE the repo; the repo keeps the 5 ids and aggregates.

Step 2. The narrow variant acts only when E ends before the boundary AND the
boundary lies after the argmin of the filtered z (the part-1 signal). It is a
REPLICA from the pre-incipient map, outside the package: the final map is the
counterfactual of 1a3ad76 when the condition holds, and params-14's otherwise.
Before it is trusted, the same replica WITHOUT the extra condition must reproduce
params-15 on every track (TRAIN and swell), which is checked.

BLIND VALIDATION: the 5 validation tracks are inside the swell 196. None of them
is printed, tabulated or drawn: everything about the swell outside the 5 ids of
step 1 is a count.

Run: python research/labels/diagnostics/item30/outside_signal.py \
        --swell <.../standard> --out <.../diag_item30>
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figs_cf  # noqa: E402
import item30_core as core  # noqa: E402
import part3_measure as pm  # noqa: E402

lc, li, dp = core.lc, core.li, core.dp
import cyclophaser  # noqa: E402

LABELS = HERE.parent.parent


def analyse(values, cfg14, cfg15) -> dict:
    r14 = core.run_series(values, *cfg14)
    cand = figs_cf.sep.candidates(r14, pd.Series(r14["z"]))
    cf, fires = figs_cf.counterfactual(r14, cand)        # fires <=> E exists and c3 == 1
    return {"r14": r14, "cand": cand, "cf": cf, "fires": fires,
            "final15": core.run_series(values, *cfg15)["final"]}


def replica(a: dict, narrow: bool) -> list:
    ok = a["fires"] and (a["r14"]["signal"] or not narrow)
    return a["cf"] if ok else a["r14"]["final"]


def detail(sid, values, a, cfg14, mark, group) -> dict:
    r, cand = a["r14"], a["cand"]
    with np.errstate(all="ignore"):
        v = dp.process_vorticity(pd.DataFrame({"zeta": values}), **cfg14[0])
    df0 = li.build_working_frame(v, **core._frame_kwargs(cfg14[1]))
    pv = df0["z_peaks_valleys"].to_numpy(object)
    z = df0["z"].to_numpy(float)
    ext = [(i, str(pv[i])) for i in range(cand["E_start"], r["boundary"])
           if isinstance(pv[i], str) and pv[i] in ("peak", "valley")]
    mat = next(((a0, b0) for ph, a0, b0 in core.runs(r["pre"])
                if ph.startswith("mature") and a0 > cand["E_end"]), None)
    return {
        "track_id": sid, "mark": mark, "group_params11": group, "n": r["n"],
        "boundary": r["boundary"], "peak_argmin_z": r["peak"], "signal": r["signal"],
        "E_start": cand["E_start"], "E_end": cand["E_end"], "c3": cand["c3"],
        "mature_after_E_pre": None if mat is None else f"{mat[0]}-{mat[1]}",
        "z_extrema_E_to_boundary": "; ".join(f"{t}@{i}" for i, t in ext),
        "z_at_E_end_over_global_min": float(z[cand["E_end"]] / z[r["peak"]]),
        "params14_seq": core.seq(r["final"]), "params15_seq": core.seq(a["final15"]),
    }


def draw(sid, values, a, cfg14, title) -> dict:
    with np.errstate(all="ignore"):
        v = dp.process_vorticity(pd.DataFrame({"zeta": values}), **cfg14[0])
    return {"id": sid, "group": title, "r14": a["r14"], "cand": a["cand"],
            "same_13_14": False,
            "maps": {"params-14": figs_cf.norm_runs(a["r14"]["final"]),
                     "params-15": figs_cf.norm_runs(a["final15"])},
            "raw01": li.rescaler([v["zeta"].values], True)(v["zeta"].values),
            "smooth01": li.rescaler([v[n].values for n in figs_cf.LAYERS], True)(
                v["vorticity_smoothed2"].values)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--swell", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    assert not a.out.resolve().is_relative_to(core.REPO), "--out must be outside the repo"
    a.out.mkdir(parents=True, exist_ok=True)
    print("cyclophaser.__file__ =", cyclophaser.__file__)
    print("layer_inspector.__file__ =", li.__file__)
    assert Path(cyclophaser.__file__).resolve().is_relative_to(core.REPO)
    assert Path(li.__file__).resolve().is_relative_to(core.REPO)
    cfg14, cfg15 = core.load_config("params-14"), core.load_config("params-15")

    sets = core.split_sets()
    val = set(lc.batch_membership(lc.VALIDATION_BATCH))
    excl = core.excluded_ids() | pm.EXCLUDED_SWELL
    ids = [p.stem for p in sorted(a.swell.glob("*.txt")) if p.stem not in excl]
    assert len(ids) == 196
    groups = yaml.safe_load((LABELS / "swell_item30/groups_params11.yaml").read_text())
    bad = set(groups["bad_marks"])
    group_of = {t: g for g, members in groups["groups"].items() for t in members}
    predicted = (set(groups["groups"]["R"]) & set(ids)) | {"19810854", "19861089"}

    import track_io
    swell = {t: track_io.read_track((a.swell / f"{t}.txt").read_bytes()) for t in ids}
    res = {t: analyse(swell[t], cfg14, cfg15) for t in ids}

    # replica fidelity: the full rule, replicated, equals params-15 on every track
    fid_swell = sum(replica(res[t], False) == res[t]["final15"] for t in ids)
    changed = {t for t in ids if res[t]["final15"] != res[t]["r14"]["final"]}
    extra = sorted(changed - predicted)
    assert len(changed) == 15 and len(extra) == 5
    assert not set(extra) & (excl | val | sets["batch_train"]), "an extra is TEST/VAL/batch"

    # step 1 — per track, OUTSIDE the repo
    rows = [detail(t, swell[t], res[t], cfg14, "bad" if t in bad else "good",
                   group_of.get(t, "—")) for t in extra]
    pd.DataFrame(rows).set_index("track_id").to_csv(a.out / "outside_signal_5_params14_15.csv")
    cases = [draw(t, swell[t], res[t], cfg14,
                  f"outside signal · marked {r['mark']}") for t, r in zip(extra, rows)]
    figdir = a.out / "figs_outside_signal"
    figdir.mkdir(exist_ok=True)
    for c in cases:
        figs_cf.figure([c], figdir / f"{c['id']}.png")
    figs_cf.figure(cases, figdir / "board_5_outside_signal.png")

    print(f"STEP 1: the {len(extra)} changed outside the prediction: {', '.join(extra)}")
    print(f"STEP 1: none is TEST ({len(set(extra) & excl) == 0}), VALIDATION "
          f"({len(set(extra) & val) == 0}) or in a labelled batch "
          f"({len(set(extra) & sets['batch_train']) == 0})")
    print(f"STEP 1 (aggregate): marked bad {sum(r['mark'] == 'bad' for r in rows)}/5; "
          f"signal {sum(r['signal'] for r in rows)}/5; c3 = 1 in "
          f"{sum(r['c3'] == 1 for r in rows)}/5; a z valley between E and the "
          f"boundary in {sum('valley' in r['z_extrema_E_to_boundary'] for r in rows)}/5")

    # step 2 — the narrow variant
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    batch = lc.load_batch_series()
    train = {k: v for k, v in {**real, **synth}.items() if k in sets["train"]}
    train |= {k: v for k, v in batch.items() if k in sets["batch_train"]}
    assert len(train) == 54
    tres = {t: analyse(train[t], cfg14, cfg15) for t in train}
    fid_train = sum(replica(tres[t], False) == tres[t]["final15"] for t in train)
    print(f"STEP 2 replica fidelity (full rule replicated == params-15): TRAIN "
          f"{fid_train}/54, swell {fid_swell}/196")
    assert fid_train == 54 and fid_swell == 196

    n_train = sorted(t for t in train if replica(tres[t], True) != tres[t]["r14"]["final"])
    full_train = sorted(t for t in train if tres[t]["final15"] != tres[t]["r14"]["final"])
    n_swell = {t for t in ids if replica(res[t], True) != res[t]["r14"]["final"]}
    print(f"STEP 2 TRAIN: narrow variant changes {len(n_train)}: {', '.join(n_train)} | "
          f"same set as the rule (R1): {n_train == full_train}")
    print(f"STEP 2 swell: narrow variant changes {len(n_swell)} | == the 10 predicted: "
          f"{n_swell == predicted} | of the 5 outside the signal: "
          f"{len(n_swell & set(extra))}")


if __name__ == "__main__":
    main()
