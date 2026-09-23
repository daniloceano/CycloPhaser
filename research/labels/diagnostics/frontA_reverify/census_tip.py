#!/usr/bin/env python
"""Front A' steps 1b and 2: the (M) and (V) census at the develop-v2.1 tip.

Measures the same two quantities Front A defined, against the CURRENT package:

  (M) mechanical — the type of `z_peaks_valleys` at index 0, and that extremum's
      prominence, on all 51 real tracks. Same columns as A's idx0_inventory.csv
      and idx0b_prominence.csv.
  (V) visible — whether the first non-incipient phase of the FINAL get_periods
      output is `decay`. Measured on A's 5 tracks only.

Config handling is delegated to `evaluate_against_labels.load_config`, i.e. the
same instrument the gates use, rather than a private copy: it filters
`phase_params` through `inspect.signature(get_periods)`. At the tip `distance`
is no longer a get_periods parameter (front B removed it), so feeding params-9
here drops `distance` IN MEMORY through that existing filter — the YAML on disk
is never touched. The script prints exactly which keys were dropped.

The pipeline is replayed step by step so `periods` can be snapshotted right
after `find_decay_period`. A replay is only worth as much as its fidelity, so
every track additionally runs the real `get_periods` and the two final `periods`
columns are compared; any mismatch is recorded per track and reported loudly.

Run:
    python census_tip.py --config <yaml> --tag <name> --outdir <dir>
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))

from labels_core import load_real_series, read_split  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

from cyclophaser.determine_periods import (  # noqa: E402
    process_vorticity, find_peaks_valleys, post_process_periods, get_periods,
)
from cyclophaser.find_stages import (  # noqa: E402
    find_intensification_period, find_decay_period, find_mature_stage,
    find_residual_period, find_incipient_period,
)
from scipy.signal import peak_prominences  # noqa: E402

# The 5 tracks Front A identified as idx0_tipo == "valley".
A_TARGET_IDS = ["20180170", "20180608", "20190325", "20191014", "20206498"]


def sha256_of(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def provenance() -> None:
    import cyclophaser
    dp = sys.modules["cyclophaser.determine_periods"]
    fs = sys.modules["cyclophaser.find_stages"]
    print("=" * 74)
    print("PROVENANCE")
    print("=" * 74)
    print(f"  cwd                  : {Path(os.getcwd()).resolve()}")
    print(f"  sys.executable       : {sys.executable}")
    print(f"  sys.prefix           : {sys.prefix}")
    print(f"  cyclophaser.__file__ : {Path(cyclophaser.__file__).resolve()}")
    print(f"  determine_periods.py : {Path(dp.__file__).resolve()}")
    print(f"    sha256             : {sha256_of(dp.__file__)}")
    print(f"  find_stages.py       : {Path(fs.__file__).resolve()}")
    print(f"    sha256             : {sha256_of(fs.__file__)}")
    expected_root = REPO_ROOT
    p = Path(cyclophaser.__file__).resolve()
    if expected_root not in p.parents:
        raise SystemExit(f"SHADOWED: cyclophaser at {p}, not under {expected_root}")
    print(f"  ASSERT OK: package loads from {expected_root}")
    print("=" * 74, flush=True)


def sign_str(x: float) -> str:
    return "+" if x > 0 else ("-" if x < 0 else "0")


def leading_run_len(periods: pd.Series, phase: str) -> int:
    n = 0
    for v in periods.astype(str):
        if v == phase:
            n += 1
        else:
            break
    return n


def replay(values: pd.Series, pv: dict, gp: dict):
    """Replay get_periods' body (determine_periods.py:1068-1123) with a snapshot
    of df['periods'] taken right after find_decay_period.

    Note the tip's find_peaks_valleys takes no `distance`: front B removed it.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vorticity = process_vorticity(pd.DataFrame({"zeta": values}), **pv)

    z = vorticity.vorticity_smoothed2
    df = z.to_dataframe().rename(columns={"vorticity_smoothed2": "z"})
    df["z_unfil"] = vorticity.zeta.to_dataframe()
    df["dz"] = vorticity.dz_dt_smoothed2.to_dataframe()
    df["dz2"] = vorticity.dz_dt2_smoothed2.to_dataframe()

    df["z_peaks_valleys"] = find_peaks_valleys(
        df["z"], prominence=gp.get("prominence"),
        prominence_relative=gp.get("prominence_relative"))
    df["dz_peaks_valleys"] = find_peaks_valleys(df["dz"])
    df["dz2_peaks_valleys"] = find_peaks_valleys(df["dz2"])

    df["periods"] = np.nan
    df["periods"] = df["periods"].astype("object")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = find_intensification_period(df, **gp)
        df = find_decay_period(df, **gp)
        after_decay = df["periods"].copy()
        df = find_mature_stage(df, **gp)
        df = find_residual_period(df, **gp)
        df = post_process_periods(df)
        df = find_incipient_period(df, **gp)

    # Fidelity check: the replay must equal what get_periods actually produces.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort2 = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        real = get_periods(vort2, **gp)
    match = [str(a) for a in df["periods"]] == [str(b) for b in real["periods"]]
    return df, after_decay, match, real


def first_non_incipient(periods: pd.Series):
    for v in periods.astype(str):
        if v != "incipient":
            return v
    return None


def phase_sequence(periods: pd.Series) -> str:
    seq, prev = [], None
    for v in periods.astype(str):
        if v != prev:
            seq.append(v)
            prev = v
    return ">".join(seq)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()

    pv, gp = load_config(a.config)
    raw = yaml.safe_load(a.config.read_text()) or {}
    raw_phase = set((raw.get("phase_params") or {}))
    dropped = sorted(raw_phase - set(gp))
    print(f"config: {a.config}")
    print(f"  sha256: {sha256_of(a.config)}")
    print(f"  process_vorticity kwargs: {pv}")
    print(f"  get_periods kwargs ({len(gp)}): {gp}")
    print(f"  phase_params keys DROPPED in memory by the signature filter: {dropped}")

    split_of = {}
    sp = read_split()
    for sid in sp.get("train", []):
        split_of[sid] = "treino"
    for sid in sp.get("test", []):
        split_of[sid] = "teste"

    series = load_real_series()
    print(f"loaded {len(series)} real tracks\n", flush=True)

    rows, final_rows, prom_rows, v_rows = [], [], [], []
    mismatches = []

    for sid in sorted(series):
        values = series[sid]
        n_steps = len(values)
        df, after_decay, replay_ok, real = replay(values, pv, gp)
        if not replay_ok:
            mismatches.append(sid)

        z, z_unfil = df["z"], df["z_unfil"]
        raw_t = df["z_peaks_valleys"].iloc[0]
        idx0_tipo = raw_t if isinstance(raw_t, str) else "nenhum"

        decai = bool(str(after_decay.iloc[0]) == "decay")
        decai_len = leading_run_len(after_decay, "decay") if decai else 0
        if decai:
            amp = float(z.max() - z.min())
            span = float(abs(z.iloc[decai_len - 1] - z.iloc[0]))
            frac_serie = decai_len / n_steps
            frac_amp = (span / amp) if amp > 0 else float("nan")
        else:
            frac_serie = frac_amp = 0.0

        rows.append({
            "track_id": sid, "split": split_of.get(sid, "nao_determinado"),
            "idx0_tipo": idx0_tipo,
            "sinal_dz_filtrada": sign_str(z.iloc[1] - z.iloc[0]),
            "sinal_dz_bruta": sign_str(z_unfil.iloc[1] - z_unfil.iloc[0]),
            "decai_no_idx0": "sim" if decai else "nao",
            "decai_comprimento_passos": decai_len,
            "decai_fracao_serie": round(frac_serie, 4),
            "decai_fracao_amplitude": (round(frac_amp, 4) if not np.isnan(frac_amp) else ""),
            "replay_equals_get_periods": "sim" if replay_ok else "NAO",
        })

        fp = df["periods"]
        final_rows.append({
            "track_id": sid,
            "periods_idx0_final": str(fp.iloc[0]),
            "leading_incipient_len_final": leading_run_len(fp, "incipient"),
            "first_non_incipient_phase_final": first_non_incipient(fp),
        })

        if idx0_tipo == "valley":
            data = z.values
            N = len(data)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                idx0_prom = float(peak_prominences(-data, [0])[0][0])
            surv = df["z_peaks_valleys"].dropna()
            surv_i = sorted(i for i in (df.index.get_loc(k) for k in surv.index) if i != 0)
            unf = find_peaks_valleys(z)
            vc = np.array([df.index.get_loc(i) for i in unf[unf == "valley"].index])
            pc = np.array([df.index.get_loc(i) for i in unf[unf == "peak"].index])
            iv = np.array([i for i in vc if i not in (0, N - 1)])
            ip = np.array([i for i in pc if i not in (0, N - 1)])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pv_ = peak_prominences(-data, iv)[0] if len(iv) else np.array([])
                pp_ = peak_prominences(data, ip)[0] if len(ip) else np.array([])
            allp = np.concatenate([pv_, pp_])
            maxp = float(allp.max()) if len(allp) else float("nan")
            thr = gp.get("prominence_relative")
            merit = ((idx0_prom >= thr * maxp)
                     if (thr is not None and not np.isnan(maxp) and maxp > 0) else None)
            prom_rows.append({
                "track_id": sid,
                "idx0_prominence_computed_diagnostically": round(idx0_prom, 6),
                "max_interior_prominence_z": (round(maxp, 6) if not np.isnan(maxp) else ""),
                "prominence_relative_threshold_cfg": thr,
                "would_survive_relative_filter_on_its_own_merit": merit,
                "steps_to_next_surviving_extremum": (surv_i[0] if surv_i else None),
            })

        if sid in A_TARGET_IDS:
            fni = first_non_incipient(fp)
            v_rows.append({
                "track_id": sid, "split": split_of.get(sid, "nao_determinado"),
                "idx0_tipo": idx0_tipo,
                "idx0_prominence": (round(float(peak_prominences(-z.values, [0])[0][0]), 6)
                                    if idx0_tipo == "valley" else ""),
                "decai_comprimento_passos": decai_len,
                "leading_incipient_len_final": leading_run_len(fp, "incipient"),
                "sequencia_fases_final": phase_sequence(fp),
                "primeira_fase_nao_incipiente_saida_final": fni,
                "V_ocorre": "sim" if fni == "decay" else "nao",
                "replay_equals_get_periods": "sim" if replay_ok else "NAO",
            })

    t = a.tag
    pd.DataFrame(rows).to_csv(a.outdir / f"{t}_idx0_inventory.csv", index=False)
    pd.DataFrame(final_rows).to_csv(a.outdir / f"{t}_idx0_final_stage.csv", index=False)
    pd.DataFrame(prom_rows).to_csv(a.outdir / f"{t}_idx0b_prominence.csv", index=False)
    vdf = pd.DataFrame(v_rows).set_index("track_id").loc[A_TARGET_IDS].reset_index()
    vdf.to_csv(a.outdir / f"{t}_V_table.csv", index=False)

    inv = pd.DataFrame(rows)
    print("idx0_tipo counts:", dict(inv["idx0_tipo"].value_counts()))
    print("decai_no_idx0 counts:", dict(inv["decai_no_idx0"].value_counts()))
    print(f"\n(V) table for A's 5 tracks:\n{vdf.to_string(index=False)}")
    print(f"\n(V) occurs on {sum(r['V_ocorre'] == 'sim' for r in v_rows)} of 5")
    if mismatches:
        print(f"\n!! REPLAY MISMATCH on {len(mismatches)} track(s): {mismatches}")
        print("   Per-block attribution from this replay is NOT trustworthy.")
    else:
        print(f"\nreplay == get_periods on all {len(rows)} tracks")
    print(f"\nwrote 4 files to {a.outdir} with tag {t!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
