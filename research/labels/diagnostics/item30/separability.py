"""Item 30, part 2 — does any quantity of the pre-incipient map separate L from K?

MEASUREMENT ONLY. No rule and no parameter is proposed; no threshold is swept
beyond reporting the valid interval. Predictions: PREDICTIONS_part2.md, committed
before this script was run.

All definitions use params-14, and the pre-incipient map is step 5 of the
ribbon.

* E: the first intensification block of step 5 that STARTS before the plateau
  boundary. If there is none, the series has no value.
* c1: the depth of E. It uses the same arithmetic as `intensification_min_depth`,
  as transcribed in the item-30a ledger: (z[start] − z[end]) / (z_max − z_min),
  on the filtered `z`, with the z range from `layer_inspector._z_range`.
* c2: c1 / duration of E in steps. The duration is counted in samples,
  end + 1 − start, the same length c3 uses.
* c3: the fraction of E that lies before the boundary,
  (min(end + 1, boundary) − start) / (end + 1 − start).

Groups (TRAIN, labelled):

* L (late boundary): 20120297, 19940445, 19810854.
* K (right boundary): 19790612, 19860380, 19870927.
* P: every train series outside the signal (boundary ≤ peak) in which E exists.

Criterion, declared before the run. A candidate passes if some threshold t
satisfies all three:

* (i) all 3 of L lie strictly on one side of t;
* (ii) every K with a defined value lies strictly on the other side;
* (iii) no P case lies on L's side.

Both orientations are checked.

Step 2 (external check, reporting only) covers the 17 swell tracks with the
signal. It needs --swell, and its per-track table goes to --out, outside the
repo.

Run:
    python research/labels/diagnostics/item30/separability.py [--swell DIR --out DIR]
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item30_core as core  # noqa: E402

lc, li = core.lc, core.li

L = ["20120297", "19940445", "19810854"]
K = ["19790612", "19860380", "19870927"]
CANDIDATES = ("c1", "c2", "c3")


def candidates(r: dict, df0_z: pd.Series) -> dict:
    """E and c1, c2, c3 for one run of `item30_core.run_series`."""
    b = r["boundary"]
    E = next(((x, y) for x, y in core.int_blocks(r["pre"]) if x < b), None)
    out = {"E_start": None, "E_end": None, "c1": None, "c2": None, "c3": None}
    if E is None:
        return out
    x, y = E
    zr = li._z_range(pd.DataFrame({"z": df0_z}))
    z = df0_z.to_numpy(float)
    c1 = None if zr is None else (z[x] - z[y]) / zr
    n = y + 1 - x
    out.update(E_start=x, E_end=y, c1=c1, c2=None if c1 is None else c1 / n,
               c3=(min(y + 1, b) - x) / n)
    return out


def run(values, pv, gp) -> dict:
    r = core.run_series(values, pv, gp)
    return {**r, **candidates(r, pd.Series(r["z"]))}


def criterion(vals: dict[str, dict], groups: dict[str, str], c: str) -> dict:
    """Both orientations of (i)(ii)(iii); the valid interval and the tightest margin."""
    def v(g):
        return [vals[s][c] for s in vals if groups[s] == g and vals[s][c] is not None]
    Lv, Kv, Pv = v("L"), v("K"), v("P")
    res = {"L_defined": len(Lv), "K_defined": len(Kv), "P_defined": len(Pv)}
    if len(Lv) < 3:
        res.update(passes=False, why="an L case has no value")
        return res
    for orient in ("L_high", "L_low"):
        if orient == "L_high":            # L > t ; K < t ; P <= t
            lo_strict = max(Kv) if Kv else float("-inf")
            lo_incl = max(Pv) if Pv else float("-inf")
            hi = min(Lv)
            ok_i_ii = lo_strict < hi
            ok_iii = lo_incl < hi
            interval = (max(lo_strict, lo_incl), hi)
            margin = hi - max(Kv + Pv) if (Kv or Pv) else None
            viol = sorted(s for s in vals if groups[s] in ("K", "P")
                          and vals[s][c] is not None and vals[s][c] >= hi)
        else:                              # L < t ; K > t ; P >= t
            hi_strict = min(Kv) if Kv else float("inf")
            hi_incl = min(Pv) if Pv else float("inf")
            lo = max(Lv)
            ok_i_ii = lo < hi_strict
            ok_iii = lo < hi_incl
            interval = (lo, min(hi_strict, hi_incl))
            margin = min(Kv + Pv) - lo if (Kv or Pv) else None
            viol = sorted(s for s in vals if groups[s] in ("K", "P")
                          and vals[s][c] is not None and vals[s][c] <= lo)
        rec = {"orientation": orient, "i_ii": bool(ok_i_ii), "iii": bool(ok_iii),
               "passes": bool(ok_i_ii and ok_iii),
               "interval": [float(interval[0]), float(interval[1])],
               "interval_empty": bool(interval[0] >= interval[1]),
               "margin": None if margin is None else float(margin),
               "cases_on_or_past_L_edge": viol}
        res[orient] = rec
    res["passes"] = bool(res["L_high"]["passes"] or res["L_low"]["passes"])
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--swell", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    print("environment:", json.dumps(core.environment()))
    pv, gp = core.load_config("params-14")

    sets = core.split_sets()
    excl = core.excluded_ids()
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    batch = lc.load_batch_series()
    train = {k: v for k, v in {**real, **synth}.items() if k in sets["train"]}
    train |= {k: v for k, v in batch.items() if k in sets["batch_train"]}
    assert set(train).isdisjoint(excl) and set(L + K) <= set(train)
    labels = core.train_labels()

    vals, groups, src = {}, {}, {}
    for sid in sorted(train):
        r = run(train[sid], pv, gp)
        if sid in L or sid in K:
            groups[sid] = "L" if sid in L else "K"
        elif not r["signal"] and r["E_start"] is not None:
            groups[sid] = "P"
        else:
            continue
        vals[sid] = r
        src[sid] = "synthetic" if sid in synth else ("batch" if sid in batch else "split")

    P = [s for s in vals if groups[s] == "P"]
    n_split = sum(src[s] == "split" for s in P)
    n_syn = sum(src[s] == "synthetic" for s in P)
    print(f"\nP: {len(P)} = {n_split} split real + {n_syn} synthetic "
          f"+ {len(P) - n_split - n_syn} batch")

    rows = []
    for sid in sorted(vals, key=lambda s: ("LKP".index(groups[s]), s)):
        r = vals[sid]
        row = {"id": sid, "group": groups[sid], "source": src[sid], "n": r["n"],
               "boundary": r["boundary"], "peak": r["peak"], "signal": r["signal"],
               "E_start": r["E_start"], "E_end": r["E_end"],
               "c1": r["c1"], "c2": r["c2"], "c3": r["c3"],
               "P_erasure": ("" if groups[sid] != "P" else
                             ("total" if r["c3"] == 1 else "partial"))}
        rec = labels.get(sid)
        if rec is not None:
            m = core.label_marks(rec)
            row.update(label_incipient_end=m["label_incipient_end"],
                       label_int_start=m["label_int_start"])
        rows.append(row)
    t = pd.DataFrame(rows).set_index("id")
    t.to_csv(HERE / "separability_train_params14.csv")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(t.to_string())
    print("\nP erasure:", t[t.group == "P"].P_erasure.value_counts().to_dict(),
          "| total ids:", sorted(t.index[(t.group == "P") & (t.P_erasure == "total")]))

    crit = {}
    for c in CANDIDATES:
        crit[c] = criterion(vals, groups, c)
        order = sorted((vals[s][c], groups[s], s) for s in vals if vals[s][c] is not None)
        print(f"\n== {c}: passes={crit[c]['passes']}  (defined: L {crit[c]['L_defined']}, "
              f"K {crit[c]['K_defined']}, P {crit[c]['P_defined']})")
        print("   ordered:", " ".join(f"{g}:{s}={x:.4g}" for x, g, s in order))
        for o in ("L_high", "L_low"):
            if o in crit[c]:
                print(f"   {o}: {crit[c][o]}")
    (HERE / "separability_criterion.json").write_text(json.dumps(crit, indent=1, default=str))

    if a.swell:
        swell_check(a, pv, gp, crit)


def swell_check(a, pv, gp, crit) -> None:
    """Step 2: the 17 swell tracks with the signal. Reporting only."""
    import track_io
    assert a.out and not a.out.resolve().is_relative_to(core.REPO)
    a.out.mkdir(parents=True, exist_ok=True)
    bad = set(yaml.safe_load((core.REPO / "research/labels/swell_item30/groups_params11.yaml")
                             .read_text())["bad_marks"])
    excl = core.excluded_ids()
    drawn = set(core.split_sets()["batch_train"]) | set(core.split_sets()["batch_test"])
    ids = [p.stem for p in sorted(a.swell.glob("*.txt")) if p.stem not in excl]
    assert len(ids) == 196
    rows = []
    for tid in ids:
        s = track_io.read_track((a.swell / f"{tid}.txt").read_bytes())
        r = run(s, pv, gp)
        if not r["signal"]:
            continue
        row = {"track_id": tid, "mark": "bad" if tid in bad else "good",
               "drawn": tid in drawn, "boundary": r["boundary"], "peak": r["peak"],
               "E_start": r["E_start"], "E_end": r["E_end"],
               "c1": r["c1"], "c2": r["c2"], "c3": r["c3"]}
        for c in CANDIDATES:
            for o in ("L_high", "L_low"):
                rec = crit[c].get(o)
                if rec and rec["passes"]:
                    lo, hi = rec["interval"]
                    x = r[c]
                    # L_high: every valid t is in (lo, hi) with t < hi, so x >= hi is on
                    # L's side for all of them and x <= lo on none. L_low mirrors it.
                    if x is None:
                        side = None
                    elif o == "L_high":
                        side = "L" if x >= hi else "not L" if x <= lo else "inside valid interval"
                    else:
                        side = "L" if x <= lo else "not L" if x >= hi else "inside valid interval"
                    row[f"{c}_{o}_side"] = side
        rows.append(row)
    d = pd.DataFrame(rows).set_index("track_id")
    assert len(d) == 17, len(d)
    d.to_csv(a.out / "separability_swell17_params14.csv")
    print("\nSWELL 17 with the signal:", len(d), "| bad", int((d.mark == "bad").sum()),
          "| good", int((d.mark == "good").sum()))
    print("  not drawn for the batch (11?):", len(d[~d.drawn]), sorted(d.index[~d.drawn]))
    print("  E defined:", int(d.E_start.notna().sum()), "| undefined:", sorted(d.index[d.E_start.isna()]))
    side_cols = [c for c in d.columns if c.endswith("_side")]
    print("  valid-threshold side columns:", side_cols or "none (no candidate passes)")
    for c in side_cols:
        print("   ", c, d.groupby(["mark", c]).size().to_dict())


if __name__ == "__main__":
    main()
