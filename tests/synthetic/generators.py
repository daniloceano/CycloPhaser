"""Synthetic vorticity series generator for CycloPhaser lifecycle tests.

Each series is built from an ordered list of lifecycle *segments*, each
described by a type, duration, and shape.  The generator connects segments
at their endpoints and, optionally, adds Gaussian noise.

Southern Hemisphere convention: vorticity is negative; more negative = more
intense cyclone (peak intensity at the global minimum).
"""

import numpy as np
import pandas as pd

# Default amplitude levels (Southern Hemisphere, s⁻¹)
_BASELINE: float = -1.0e-4   # weak vorticity — used for Ic and as start/end of It/D
_PEAK:     float = -9.0e-4   # peak intensity — used for M and as the target of It/start of D


def _ramp_sine(n: int, v_start: float, v_end: float) -> np.ndarray:
    """Half-period cosine ramp: v_start at index 0, v_end at index n-1."""
    t = np.linspace(0.0, np.pi, n)
    return v_start + (v_end - v_start) * (1.0 - np.cos(t)) / 2.0


def _constant(n: int, v: float) -> np.ndarray:
    return np.full(n, float(v))


def make_lifecycle_series(
    segments,
    start: str = "2000-01-01",
    freq: str = "3h",
    noise_frac: float = 0.0,
    seed=None,
    baseline: float = _BASELINE,
    peak: float = _PEAK,
    start_value: float | None = None,
) -> pd.Series:
    """Build a synthetic Southern Hemisphere vorticity time series.

    Parameters
    ----------
    segments : list[dict]
        Ordered lifecycle segments.  Each dict must contain:
          'type'  : 'Ic' | 'It' | 'M' | 'D' | 'residual'
          'n'     : int — number of timesteps
          'shape' : 'sine' | 'plateau' | 'linear'
                    Ramp shape for It, D, and residual segments:
                      'sine'    — half-period cosine (smooth, zero derivative at
                                  both endpoints); default for It/D/residual.
                      'linear'  — constant-slope ramp (non-zero dz from the
                                  first timestep; prevents CycloPhaser from
                                  misidentifying the onset as 'incipient').
                      'plateau' — constant value at the segment target;
                                  default for M; produces an exact flat top.
        Optional per-segment override:
          'amp'   : float — target end-value for sine/linear ramps; level for
                    plateau; partial-intensification target for 'residual'.

    Segment semantics
    -----------------
    Ic       Quasi-constant near *baseline* (weak, incipient phase).
    It       Smooth sine ramp descending toward *peak* (intensification).
    M        At *peak* level: exact plateau ('plateau') or near-plateau with
             small sinusoidal variation ('sine').
    D        Smooth sine ramp ascending from *peak* back toward *baseline* (decay).
    residual Partial re-intensification from *baseline* toward a midpoint
             between baseline and peak — not followed by another M.

    Parameters
    ----------
    noise_frac : float
        Gaussian noise std expressed as a fraction of |peak - baseline|.
        0.0 = clean series.  0.02 = 2 % noise.
    seed : int | None
        RNG seed for reproducible noise.
    baseline : float
        Weak-vorticity reference level (negative, e.g. -1e-4).
    peak : float
        Peak-intensity reference level (most negative, e.g. -9e-4).
    start_value : float | None
        Override for the running vorticity level before the first segment is
        processed.  Defaults to *baseline*.  Pass *peak* for series that start
        at maximum intensity (e.g. 'DItMD' scenarios where decay precedes the
        observed cycle).

    Returns
    -------
    pd.Series
        Vorticity values with a DatetimeIndex (index.name == 'time').
    """
    current: float = start_value if start_value is not None else baseline
    parts: list[np.ndarray] = []

    for seg in segments:
        stype: str = seg["type"]
        n:     int = int(seg["n"])
        shape: str = seg.get("shape", "plateau" if stype == "M" else "sine")

        if stype == "Ic":
            arr     = _constant(n, baseline)
            current = baseline

        elif stype == "It":
            target  = float(seg.get("amp", peak))
            arr     = (_ramp_sine(n, current, target) if shape == "sine"
                       else np.linspace(current, target, n) if shape == "linear"
                       else _constant(n, target))
            current = float(arr[-1])

        elif stype == "M":
            if shape == "plateau":
                arr = _constant(n, peak)
            else:
                # Near-plateau: small sinusoidal excursion below peak (more negative = briefly
                # more intense), starting and ending at peak.
                half_amp = float(seg.get("amp", abs(peak - baseline) * 0.03))
                arr = peak - half_amp * np.sin(np.linspace(0.0, np.pi, n))
            current = float(arr[-1])

        elif stype == "D":
            target  = float(seg.get("amp", baseline))
            arr     = (_ramp_sine(n, current, target) if shape == "sine"
                       else np.linspace(current, target, n) if shape == "linear"
                       else _constant(n, target))
            current = float(arr[-1])

        elif stype == "residual":
            # Partial re-intensification: goes partway toward peak without completing a cycle.
            target = float(seg.get("amp", (baseline + peak) / 2.0))
            arr    = (_ramp_sine(n, current, target) if shape == "sine"
                      else np.linspace(current, target, n) if shape == "linear"
                      else _constant(n, target))
            current = float(arr[-1])

        else:
            raise ValueError(f"Unknown segment type: {stype!r}.  "
                             f"Valid types: 'Ic', 'It', 'M', 'D', 'residual'.")

        parts.append(arr)

    values = np.concatenate(parts)

    if noise_frac > 0.0:
        rng    = np.random.default_rng(seed)
        std    = noise_frac * abs(peak - baseline)
        values = values + rng.normal(0.0, std, size=len(values))

    idx = pd.date_range(start, periods=len(values), freq=freq, name="time")
    return pd.Series(values, index=idx, name="synthetic_zeta")
