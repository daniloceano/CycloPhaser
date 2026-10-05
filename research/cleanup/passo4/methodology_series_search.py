#!/usr/bin/env python
"""Passo 4, 4c — how the synthetic series of docs/figures/make_methodology_figure.py
was chosen (read-only; writes methodology_series_search.txt next to it).

    <cyclophaser env python> -P research/cleanup/passo4/methodology_series_search.py

Requirements (Danilo, rounds 0 and 1): a flat start, one full peak-valley-peak
cycle, a weak extremum discarded by the prominence filter and lying inside the
decay, a final stretch where the residual is visible, and realistic
durations as DESIGN TARGETS (not thresholds): decay the longest phase (near half
of the series), intensification near a quarter, incipient, mature and residual
short (about a tenth or less each). Under the package defaults this is checked
as: the extrema that find_peaks_valleys finds without the prominence filter but
the defaults discard are exactly ONE weak oscillation (a valley and the peak
next to it), both inside the decay block; the phase sequence
incipient, intensification, mature, decay, residual; and the phase fractions in
the target windows below.

Why a pair and not a single extremum: inside a stretch that keeps rising, a weak
oscillation is a valley followed by a peak. If only one of the two is discarded,
the surviving one splits the decay (measured in round 0: the surviving peak ended
the decay and the rest became residual). So a weak extremum inside an intact
decay is discarded together with its partner.

Shape (hourly, n steps): a flat start, a half-cosine deepening, a longer
half-cosine recovery with a weak ripple, and a short half-cosine re-deepening
at the end. Stage 1 scans the noise-free shape; stage 2 adds seeded
high-frequency noise (random-phase sinusoids, periods 2.5-8 h, well below the
18 h high cutoff of the default filter) and keeps the seeds that preserve every
condition. Flat or slowly varying stretches turn any leaked noise into tiny
extrema the prominence filter discards, so few seeds qualify.
"""
import importlib
import itertools
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.simplefilter("ignore")
importlib.import_module("cyclophaser.determine_periods")
DP = sys.modules["cyclophaser.determine_periods"]
OUT = Path(__file__).with_name("methodology_series_search.txt")
TARGET = {"decay": (0.40, 0.60), "intensification": (0.18, 0.32),
          "incipient": (0.0, 0.12), "mature": (0.0, 0.12), "residual": (0.0, 0.12)}


def halfcos(t, a, b):
    """0 before a, 1 after b, half-cosine in between."""
    x = np.clip((t - a) / (b - a), 0, 1)
    return 0.5 - 0.5 * np.cos(np.pi * x)


def shape(n, fi, fd, fr, ra, rw, tail_a, onset):
    """Fractions of n: the deepening starts at 0.05 n and lasts fi n; the
    recovery lasts fd n; the ripple sits at fr of the recovery, amplitude ra,
    width rw n; the end re-deepens by tail_a; `onset` is a small bump at the start
    of the deepening (the peak the intensification starts from)."""
    t = np.arange(n, dtype=float)
    t0 = 0.05 * n
    tv = t0 + fi * n
    t3 = min(tv + fd * n, n - 1)
    deep = halfcos(t, t0, tv) * (1 - halfcos(t, tv, t3))
    rc = tv + fr * (t3 - tv)
    z = (-1e-5 - 6e-5 * deep + ra * np.exp(-((t - rc) / (rw * n)) ** 2)
         - tail_a * halfcos(t, t3, n + 5) + onset * np.exp(-((t - t0) / (0.04 * n)) ** 2))
    return t, z


def hf_noise(t, seed, amp, k=40, pmin=2.5, pmax=8.0):
    r = np.random.default_rng(seed)
    p, ph, a = r.uniform(pmin, pmax, k), r.uniform(0, 2 * np.pi, k), r.standard_normal(k)
    x = (a[:, None] * np.sin(2 * np.pi * t[None, :] / p[:, None] + ph[:, None])).sum(0)
    return amp * x / x.std()


def evaluate(z):
    s = pd.Series(z, index=pd.date_range("2000-01-01", periods=len(z), freq="h"))
    df = DP.determine_periods(s)
    kept = set(np.flatnonzero(df["z_peaks_valleys"].notna()))
    allx = sorted(np.flatnonzero(DP.find_peaks_valleys(df["z"], None, None, False).notna()))
    dropped = sorted(set(allx) - kept)
    p = df["periods"]
    seq = [x for i, x in enumerate(p) if i == 0 or x != p.iloc[i - 1]]
    frac = {k: float((p == k).mean()) for k in TARGET}
    pair = (len(dropped) == 2 and all(p.iloc[i] == "decay" for i in dropped)
            and allx.index(dropped[1]) == allx.index(dropped[0]) + 1)
    ok = (pair and seq == ["incipient", "intensification", "mature", "decay", "residual"]
          and all(lo <= frac[k] <= hi for k, (lo, hi) in TARGET.items()))
    return ok, dropped, frac


if __name__ == "__main__":
    lines, shapes = [], []
    grid = itertools.product([240], [0.26, 0.28, 0.30], [0.58, 0.6, 0.62], [0.4, 0.55, 0.7],
                             [0.3e-5, 0.5e-5, 0.8e-5], [0.03, 0.05], [1.0e-5, 1.2e-5, 1.5e-5],
                             [0, 0.3e-5, 0.6e-5])
    for p in grid:
        if evaluate(shape(*p)[1])[0]:
            shapes.append(p)
    lines.append(f"stage 1: {len(shapes)} noise-free shapes qualify "
                 "(n, deepening fraction, recovery fraction, ripple position, ripple amplitude, "
                 "ripple width, tail amplitude, onset bump)")
    for p in shapes:
        t, z = shape(*p)
        for amp in (0.3e-5, 0.6e-5):
            seeds = [s for s in range(30) if evaluate(z + hf_noise(t, s, amp))[0]]
            if seeds:
                lines.append(f"shape={p} noise={amp:.1e}: seeds {seeds}")
                for sd in seeds:
                    ok, d, f = evaluate(z + hf_noise(t, sd, amp))
                    lines.append(f"  seed {sd}: discarded {d}; fractions "
                                 + ", ".join(f"{k} {v:.3f}" for k, v in f.items()))
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
