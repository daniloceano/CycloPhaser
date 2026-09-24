#!/usr/bin/env python
"""M1 + M2 — the index-0 extremum census over all 63 series (measurement only).

M1  How is the prominence of index 0 computed? Answer read off the code and
    then MEASURED: `_refine_extrema` (determine_periods.py:180-181) puts 0 and
    N-1 in `boundary` and never passes them to `peak_prominences`, so the
    package computes no prominence for index 0 at all. The number that Front A
    reported as "prominence 0.0" is what `peak_prominences(signed, [0])` returns
    when asked anyway — and scipy's base search cannot cross the array edge, so
    the left base IS index 0 and the value is 0.0 for ANY data. This script
    recomputes it on all 63 series, in both sign conventions, to confirm or
    refute the "by construction" claim as a measured fact.

M2  For every series: the type of index 0 in the FINAL z extremum list (the one
    `find_stages` consumes, i.e. after the prominence filter and the boundary
    exception), the index/type/value of the next extremum E1 in that same list,
    z[0], z[E1]-z[0], and whether rule C2 would fire (and on which branch).

Writes outputs/m2_c2_table.csv (63 rows) and prints a summary.

Run (from the repo root, in the dedicated `cyclophaser` env):
    python research/labels/diagnostics/frontA_idx0_c2/m1_m2_census.py \
        --config research/labels/configs/cyclophaser_params-13.yaml \
        --outdir research/labels/diagnostics/frontA_idx0_c2/outputs
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    A_TARGET_IDS, LABELS_DIR, REPO_ROOT, provenance, replay, seq_str, sha256_of,
)

from labels_core import load_real_series, load_synthetic_series, read_split  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

from scipy.signal import argrelextrema, peak_prominences  # noqa: E402


def boundary_prominence(signed: np.ndarray, idx: int) -> float:
    """What `peak_prominences` returns at `idx`, warnings silenced."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(peak_prominences(signed, [idx])[0][0])


def c2_decision(type0, e1_type, z0, z_e1):
    """The exact C2 rule of the brief. Returns (fires: bool, branch: str)."""
    if type0 is None or e1_type is None:
        return False, "no_E1" if e1_type is None else "no_idx0"
    if type0 == "valley" and e1_type == "valley":
        if z_e1 < z0:
            return True, "valley->peak"
        return False, "valley/valley, E1 not strictly deeper"
    if type0 == "peak" and e1_type == "peak":
        if z_e1 > z0:
            return True, "peak->valley"
        return False, "peak/peak, E1 not strictly higher"
    return False, "alternating types"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    pv, gp = load_config(a.config)
    raw = yaml.safe_load(a.config.read_text()) or {}
    dropped = sorted(set(raw.get("phase_params") or {}) - set(gp))
    print(f"config: {a.config}")
    print(f"  sha256: {sha256_of(a.config)}")
    print(f"  process_vorticity kwargs: {pv}")
    print(f"  get_periods kwargs ({len(gp)}): {gp}")
    print(f"  phase_params keys dropped in memory by the signature filter: {dropped}\n",
          flush=True)

    split = read_split()
    split_of = {sid: "treino" for sid in split.get("train", [])}
    split_of.update({sid: "teste" for sid in split.get("test", [])})

    real = load_real_series()
    synth, case_names = load_synthetic_series()
    print(f"loaded {len(real)} real tracks + {len(synth)} synthetic series\n", flush=True)

    rows = []
    replay_failures = []

    for sid, values in [(k, real[k]) for k in sorted(real)] + \
                       [(k, synth[k]) for k in sorted(synth)]:
        source = "real" if sid in real else "sintetico"
        out = replay(values, pv, gp, force="none", verify=True)
        if out["replay_ok"] is not True:
            replay_failures.append(sid)
        df = out["df"]

        zser = df["z"]
        zvals = np.asarray(zser, dtype=float)
        pv_col = df["z_peaks_valleys"]
        types = list(pv_col)

        # --- M1: prominence of index 0, in both sign conventions -------------
        prom0_peak = boundary_prominence(zvals, 0)
        prom0_valley = boundary_prominence(-zvals, 0)

        # Also record whether index 0 is even a candidate before the collapse,
        # since _collapse_plateaux can move a boundary plateau's representative.
        raw_peaks = argrelextrema(zvals, np.greater_equal)[0]
        raw_valleys = argrelextrema(zvals, np.less_equal)[0]
        idx0_raw = ("peak" if 0 in raw_peaks else "") + \
                   ("valley" if 0 in raw_valleys else "")

        # --- M2: final-list type of index 0 and of E1 ------------------------
        t0 = types[0] if isinstance(types[0], str) and types[0] in ("peak", "valley") else None
        e1_idx, e1_type = None, None
        for i in range(1, len(types)):
            if isinstance(types[i], str) and types[i] in ("peak", "valley"):
                e1_idx, e1_type = i, types[i]
                break

        z0 = float(zvals[0])
        z_e1 = float(zvals[e1_idx]) if e1_idx is not None else float("nan")
        diff = (z_e1 - z0) if e1_idx is not None else float("nan")
        fires, branch = c2_decision(t0, e1_type, z0, z_e1)

        rows.append({
            "id": sid,
            "fonte": source,
            "caso": case_names.get(sid, ""),
            "split": split_of.get(sid, "?"),
            "alvo_A": sid in A_TARGET_IDS,
            "n_steps": len(values),
            "replay_ok": out["replay_ok"],
            "idx0_tipo_bruto": idx0_raw,          # before _collapse_plateaux
            "idx0_tipo_final": t0 if t0 else "ausente",
            "prom_idx0_conv_peak": prom0_peak,    # M1
            "prom_idx0_conv_valley": prom0_valley,  # M1
            "z0": z0,
            "E1_idx": e1_idx if e1_idx is not None else -1,
            "E1_tipo": e1_type if e1_type else "ausente",
            "z_E1": z_e1,
            "z_E1_menos_z0": diff,
            "sinal_z1_menos_z0": float(zvals[1] - zvals[0]) if len(zvals) > 1 else float("nan"),
            "C2_dispara": fires,
            "C2_ramo": branch,
            "seq_fases_params13": seq_str(df["periods"]),
        })

    tab = pd.DataFrame(rows)
    out_csv = a.outdir / "m2_c2_table.csv"
    tab.to_csv(out_csv, index=False)
    print(f"wrote {out_csv} ({len(tab)} rows)\n")

    # ── summary ─────────────────────────────────────────────────────────────
    print("=" * 74)
    print("M1 — prominence of index 0")
    print("=" * 74)
    n_zero_peak = int((tab["prom_idx0_conv_peak"] == 0.0).sum())
    n_zero_valley = int((tab["prom_idx0_conv_valley"] == 0.0).sum())
    print(f"  peak_prominences(z, [0])   == 0.0 in {n_zero_peak}/{len(tab)} series")
    print(f"  peak_prominences(-z, [0])  == 0.0 in {n_zero_valley}/{len(tab)} series")
    print(f"  max |value| observed       : "
          f"{max(tab['prom_idx0_conv_peak'].abs().max(), tab['prom_idx0_conv_valley'].abs().max()):.3e}")
    print("  (the package itself computes NO prominence for index 0: see")
    print("   determine_periods.py:180-181 — `boundary` is excluded from `interior`,")
    print("   and only `interior` reaches peak_prominences at :188)")

    print()
    print("=" * 74)
    print("M2 — where C2 fires")
    print("=" * 74)
    print(tab["idx0_tipo_final"].value_counts().to_string())
    print()
    fired = tab[tab["C2_dispara"]]
    print(f"  C2 fires in {len(fired)}/{len(tab)} series")
    print(tab["C2_ramo"].value_counts().to_string())
    print()
    if len(fired):
        cols = ["id", "fonte", "caso", "split", "idx0_tipo_final", "E1_idx", "E1_tipo",
                "z0", "z_E1", "z_E1_menos_z0", "C2_ramo"]
        print(fired[cols].to_string(index=False))
    print()
    print("  the 5 Front A targets:")
    cols = ["id", "split", "idx0_tipo_final", "E1_idx", "E1_tipo", "z0", "z_E1",
            "z_E1_menos_z0", "C2_dispara", "C2_ramo"]
    print(tab[tab["alvo_A"]][cols].to_string(index=False))
    print()
    print("  the 12 synthetic series:")
    print(tab[tab["fonte"] == "sintetico"][
        ["id", "caso", "idx0_tipo_final", "E1_idx", "E1_tipo", "z_E1_menos_z0",
         "C2_dispara", "C2_ramo"]].to_string(index=False))

    print()
    if replay_failures:
        print(f"!! REPLAY MISMATCH on {len(replay_failures)}: {replay_failures}")
        return 1
    print(f"replay == get_periods on {len(tab)}/{len(tab)} series (field by field).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
