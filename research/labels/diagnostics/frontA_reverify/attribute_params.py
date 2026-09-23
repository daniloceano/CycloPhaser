#!/usr/bin/env python
"""Front A' step 2: attribute any params-9 -> params-13 change on A's 5 tracks
to a single parameter, by flipping ONE key at a time.

Only three phase_params differ between the two configs in a way the tip can
see (`distance` is a fourth, but it is no longer a get_periods parameter, so it
is inert at the tip and cannot be flipped):

    mature_amplitude_fraction   0.95 -> 0.90
    mature_min_depth            <get_periods default> -> 0.80
    intensification_min_depth   <get_periods default> -> 0.05

Baseline is params-9 as the tip sees it. Each variant changes exactly one key.
The last row applies all three, and must reproduce the params-13 census — that
equality is what licenses reading the single-key rows as attribution.

This is attribution only. It proposes no correction.

Run:
    python attribute_params.py --outdir <dir>
"""

from __future__ import annotations

import argparse
import inspect
import sys
import warnings
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
sys.path.insert(0, str(REPO_ROOT))

from labels_core import load_real_series  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402
from cyclophaser.determine_periods import process_vorticity, get_periods  # noqa: E402

A_TARGET_IDS = ["20180170", "20180608", "20190325", "20191014", "20206498"]
CFG_DIR = REPO_ROOT / "research" / "labels" / "configs"


def sequence(periods) -> str:
    seq, prev = [], None
    for v in [str(p) for p in periods]:
        if v != prev:
            seq.append(v)
            prev = v
    return ">".join(seq)


def first_non_incipient(periods):
    for v in [str(p) for p in periods]:
        if v != "incipient":
            return v
    return None


def run(values, pv, gp):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        df = get_periods(vort, **gp)
    return df["periods"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    pv9, gp9 = load_config(CFG_DIR / "cyclophaser_params-9.yaml")
    pv13, gp13 = load_config(CFG_DIR / "cyclophaser_params-13.yaml")
    assert pv9 == pv13, "filter_params must be identical between params-9 and params-13"

    defaults = {k: v.default for k, v in inspect.signature(get_periods).parameters.items()}
    deltas = {}
    for k in ("mature_amplitude_fraction", "mature_min_depth", "intensification_min_depth"):
        frm = gp9.get(k, defaults[k])
        to = gp13.get(k, defaults[k])
        deltas[k] = (frm, to)
        print(f"delta {k}: {frm} -> {to}"
              f"{'  (params-9 omits it; get_periods default shown)' if k not in gp9 else ''}")

    variants = [("params-9 baseline", dict(gp9))]
    for k, (_frm, to) in deltas.items():
        g = dict(gp9)
        g[k] = to
        variants.append((f"only {k}={to}", g))
    variants.append(("all three (== params-13)", dict(gp13)))

    series = load_real_series()
    rows = []
    for sid in A_TARGET_IDS:
        for name, gp in variants:
            per = run(series[sid], pv9, gp)
            fni = first_non_incipient(per)
            rows.append({
                "track_id": sid, "variant": name,
                "sequencia_fases": sequence(per),
                "primeira_fase_nao_incipiente": fni,
                "V_ocorre": "sim" if fni == "decay" else "nao",
            })

    df = pd.DataFrame(rows)
    out = a.outdir / "step2_attribution.csv"
    df.to_csv(out, index=False)

    # Fidelity: the all-three variant must equal the params-13 census.
    cens = pd.read_csv(a.outdir / "step2_params13_V_table.csv", dtype=str)
    cens_seq = dict(zip(cens["track_id"].astype(str), cens["sequencia_fases_final"]))
    allthree = df[df["variant"] == "all three (== params-13)"]
    bad = [r["track_id"] for _, r in allthree.iterrows()
           if cens_seq.get(str(r["track_id"])) != r["sequencia_fases"]]
    print(f"\nall-three variant reproduces the params-13 census: "
          f"{'YES on all 5' if not bad else 'NO — ' + str(bad)}")

    for sid in A_TARGET_IDS:
        sub = df[df["track_id"] == sid]
        base = sub.iloc[0]["sequencia_fases"]
        changed = sub[sub["sequencia_fases"] != base]
        flag = "" if changed.empty else "   <-- CHANGES"
        print(f"\n{sid}{flag}")
        for _, r in sub.iterrows():
            mark = " *" if r["sequencia_fases"] != base else "  "
            print(f"  {mark} {r['variant']:<38} {r['sequencia_fases']}  (V={r['V_ocorre']})")

    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
