#!/usr/bin/env python
"""Shared plumbing for Front A / item 28 stage 1 (measurement only).

Nothing here modifies `cyclophaser/`. The one behavioural variant this front
needs — index 0 forced from 'valley' to 'peak' — lives in `find_peaks_valleys_forced`
below, a local copy of the package function with the `6060c6d` block reinserted,
and is applied by an explicit REPLAY of `get_periods`' body, never by editing
the package.

Every replay is validated: with `force="none"` the replay's `periods` column must
equal what the real `get_periods` returns, field by field, or the run aborts.
That check is what licenses any per-step attribution made from the replay
(lesson of `attribute_blocks_via_verified_replay`).
"""

from __future__ import annotations

import functools
import hashlib
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[4]
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))

from scipy.signal import argrelextrema  # noqa: E402

from cyclophaser.determine_periods import (  # noqa: E402
    _collapse_plateaux, _refine_extrema, find_peaks_valleys, get_periods,
    post_process_periods, process_vorticity,
)
from cyclophaser.find_stages import (  # noqa: E402
    find_decay_period, find_incipient_period, find_intensification_period,
    find_mature_stage, find_residual_period,
)

A_TARGET_IDS = ["20180170", "20180608", "20190325", "20191014", "20206498"]

# The four synthetic cases that open with a genuine decay by construction.
A_SYNTHETIC_CASES = ["DItMD_noisy", "DItMD_residual_noisy",
                     "IcDItMD_noisy", "IcDItMD_residual_noisy"]

# Held out by research/labels/split.yaml. Examined mechanically, never scored.
TEST_ONLY_EXAMINE = {"20206498"}


def sha256_of(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def provenance() -> None:
    """Print, and hard-assert, which cyclophaser this process actually imported."""
    import cyclophaser
    dp = sys.modules["cyclophaser.determine_periods"]
    fs = sys.modules["cyclophaser.find_stages"]
    print("=" * 74)
    print("PROVENANCE (before any measurement)")
    print("=" * 74)
    print(f"  cwd                  : {Path(os.getcwd()).resolve()}")
    print(f"  sys.executable       : {sys.executable}")
    print(f"  sys.prefix           : {sys.prefix}")
    print(f"  cyclophaser.__file__ : {Path(cyclophaser.__file__).resolve()}")
    print(f"  version              : {getattr(cyclophaser, '__version__', '<none>')}")
    print(f"  determine_periods.py : {Path(dp.__file__).resolve()}")
    print(f"    sha256             : {sha256_of(dp.__file__)}")
    print(f"  find_stages.py       : {Path(fs.__file__).resolve()}")
    print(f"    sha256             : {sha256_of(fs.__file__)}")
    p = Path(cyclophaser.__file__).resolve()
    if REPO_ROOT not in p.parents:
        raise SystemExit(f"SHADOWED: cyclophaser at {p}, not under {REPO_ROOT}")
    print(f"  ASSERT OK: package loads from {REPO_ROOT}")
    print("=" * 74, flush=True)


# ── the Front A variant, as a local copy ─────────────────────────────────────

def find_peaks_valleys_forced(series, prominence=None, prominence_relative=None,
                              to="peak"):
    """`find_peaks_valleys` with index 0 forced to one type — commit 6060c6d.

    `to="peak"` is 6060c6d verbatim. `to="valley"` is its mirror image, needed
    only to measure what C2's `peak->valley` branch would do where it fires; no
    version of the package ever contained it.

    Byte-for-byte the tip's function except for the marked block, which is the
    diff `6060c6d` applied to `cyclophaser/determine_periods.py` and later
    reverted. Reinserted HERE, in the diagnostics tree, so the measurement can
    be taken without the package carrying a refuted change.

    Note the position: the force acts on the RAW argrelextrema output, i.e.
    before `_collapse_plateaux`, exactly as `6060c6d` placed it.
    """
    data = series.values
    N = len(data)

    peaks = argrelextrema(data, np.greater_equal)[0]
    valleys = argrelextrema(data, np.less_equal)[0]

    # ---- 6060c6d begins ----
    if to == "peak":
        if 0 in valleys:
            valleys = valleys[valleys != 0]
            if 0 not in peaks:
                peaks = np.sort(np.append(peaks, 0))
    elif to == "valley":                      # mirror, for C2's other branch
        if 0 in peaks:
            peaks = peaks[peaks != 0]
            if 0 not in valleys:
                valleys = np.sort(np.append(valleys, 0))
    else:
        raise ValueError(to)
    # ---- 6060c6d ends ----

    zeros = np.where(data == 0)[0]

    peaks = _collapse_plateaux(peaks)
    valleys = _collapse_plateaux(valleys)

    overlap = np.intersect1d(peaks, valleys)
    if len(overlap):
        peaks = peaks[~np.isin(peaks, overlap)]

    if prominence is not None or prominence_relative is not None:
        peaks = _refine_extrema(data, data, peaks, prominence, prominence_relative, N)
        valleys = _refine_extrema(data, -data, valleys, prominence, prominence_relative, N)

    result = pd.Series(index=series.index, dtype=object)
    result[:] = np.nan
    result.iloc[peaks] = 'peak'
    result.iloc[valleys] = 'valley'
    result.iloc[zeros] = 0
    return result


# ── the replay ───────────────────────────────────────────────────────────────

def replay(values: pd.Series, pv: dict, gp: dict, force: str = "none",
           verify: bool = True):
    """Replay `get_periods`' body (determine_periods.py:1064-1123), with hooks.

    Args:
        force: "none"   — the package's own `find_peaks_valleys` everywhere.
               "*_valley" — the mirror variants, forcing index 0 to 'valley'.
               "all"    — the forced copy on z, dz AND dz2. This is literally
                          what `6060c6d` did, since it patched the function.
               "z_only" — the forced copy on z alone. C2 is defined on the z
                          extrema list, so this isolates that channel.
        verify: when force == "none", assert the replay reproduces `get_periods`
                field by field. Skipped for the forced variants, which by
                construction differ from the package.

    Returns a dict of snapshots taken along the pipeline.
    """
    if force not in ("none", "all", "z_only", "all_valley", "z_only_valley"):
        raise ValueError(force)

    to = "valley" if force.endswith("_valley") else "peak"
    forced = functools.partial(find_peaks_valleys_forced, to=to)
    fpv_z = forced if force != "none" else find_peaks_valleys
    fpv_d = forced if force in ("all", "all_valley") else find_peaks_valleys

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vorticity = process_vorticity(pd.DataFrame({"zeta": values}), **pv)

    z = vorticity.vorticity_smoothed2
    df = z.to_dataframe().rename(columns={"vorticity_smoothed2": "z"})
    df["z_unfil"] = vorticity.zeta.to_dataframe()
    df["dz"] = vorticity.dz_dt_smoothed2.to_dataframe()
    df["dz2"] = vorticity.dz_dt2_smoothed2.to_dataframe()

    df["z_peaks_valleys"] = fpv_z(df["z"], prominence=gp.get("prominence"),
                                  prominence_relative=gp.get("prominence_relative"))
    df["dz_peaks_valleys"] = fpv_d(df["dz"])
    df["dz2_peaks_valleys"] = fpv_d(df["dz2"])

    df["periods"] = np.nan
    df["periods"] = df["periods"].astype("object")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = find_intensification_period(df, **gp)
        after_int = df["periods"].copy()
        df = find_decay_period(df, **gp)
        after_decay = df["periods"].copy()
        df = find_mature_stage(df, **gp)
        after_mature = df["periods"].copy()
        df = find_residual_period(df, **gp)
        after_residual = df["periods"].copy()
        df = post_process_periods(df)
        after_post = df["periods"].copy()          # state entering find_incipient_period
        df = find_incipient_period(df, **gp)

    out = {
        "df": df,
        "after_int": after_int,
        "after_decay": after_decay,
        "after_mature": after_mature,
        "after_residual": after_residual,
        "after_post": after_post,     # == the map BEFORE H (find_stages.py:1134)
        "final": df["periods"].copy(),
        "replay_ok": None,
    }

    if verify and force == "none":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort2 = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            real = get_periods(vort2, **gp)
        ok = ([str(a) for a in df["periods"]] == [str(b) for b in real["periods"]])
        out["replay_ok"] = bool(ok)
    return out


# ── small helpers shared by the scripts ──────────────────────────────────────

def phase_sequence(periods: pd.Series) -> list[str]:
    seq, prev = [], None
    for v in periods.astype(str):
        if v != prev:
            seq.append(v)
            prev = v
    return seq


def phase_starts(periods: pd.Series) -> list[tuple[str, int]]:
    from labels_core import normalize_phase
    out, prev = [], None
    for i, lab in enumerate(periods.astype(str)):
        name = normalize_phase(lab)
        if name != prev:
            out.append((name, i))
            prev = name
    return out


def seq_str(periods: pd.Series) -> str:
    return ">".join(phase_sequence(periods))
