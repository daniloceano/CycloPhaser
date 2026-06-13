"""Synthetic tests for find_peaks_valleys plateau-collapse behaviour (fix #10).

Verifies that consecutive indices returned by argrelextrema for a flat plateau
are collapsed to a single representative midpoint, and that no index appears
simultaneously as both 'peak' and 'valley' after the collapse.
"""

import numpy as np
import pandas as pd
import pytest

from cyclophaser.determine_periods import find_peaks_valleys


def _make_series(values):
    idx = pd.date_range("2000-01-01", periods=len(values), freq="3h", name="time")
    return pd.Series(values, index=idx, name="z")


# ── Plateau at minimum (true valley) ─────────────────────────────────────────

def test_plateau_at_minimum_collapsed_to_single_valley():
    """A flat-bottom plateau must produce exactly one 'valley' mark."""
    # descent → 4-point plateau → ascent, all strictly separated
    descent = np.linspace(-0.5e-4, -8.9e-4, 11)
    plateau = np.full(4, -9.0e-4)
    ascent  = np.linspace(-8.9e-4, -0.5e-4, 15)
    series  = _make_series(np.concatenate([descent, plateau, ascent]))

    result = find_peaks_valleys(series)
    valleys = result[result == "valley"]
    peaks   = result[result == "peak"]

    # Exactly one valley mark inside the plateau region
    plat_idx = np.where(series.values == -9.0e-4)[0]
    valley_positions = [series.index.get_loc(t) for t in valleys.index]
    plateau_valleys = [p for p in valley_positions if p in plat_idx]
    assert len(plateau_valleys) == 1, (
        f"Expected 1 valley in plateau, got {len(plateau_valleys)}: {plateau_valleys}"
    )

    # No peak inside the plateau region
    peak_positions = [series.index.get_loc(t) for t in peaks.index]
    plateau_peaks = [p for p in peak_positions if p in plat_idx]
    assert len(plateau_peaks) == 0, (
        f"Expected 0 peaks in plateau, got {len(plateau_peaks)}: {plateau_peaks}"
    )


def test_no_peak_valley_overlap():
    """No index should be simultaneously 'peak' and 'valley'."""
    descent = np.linspace(-0.5e-4, -8.9e-4, 11)
    plateau = np.full(4, -9.0e-4)
    ascent  = np.linspace(-8.9e-4, -0.5e-4, 15)
    series  = _make_series(np.concatenate([descent, plateau, ascent]))

    result = find_peaks_valleys(series)
    peak_idx   = set(result.index[result == "peak"])
    valley_idx = set(result.index[result == "valley"])
    overlap = peak_idx & valley_idx
    assert not overlap, f"Indices appear as both peak and valley: {overlap}"


# ── Floor-midpoint convention for even-length plateau ─────────────────────────

def test_even_plateau_midpoint_is_floor():
    """A 4-point plateau → midpoint index is floor(mean) of the run.

    Plateau at indices 5-8 (value -5e-4, non-zero to avoid the zeros branch).
    floor(mean([5,6,7,8])) = floor(6.5) = 6.
    """
    values = np.array([3, 2, 1, 0.5, 0.1, -5, -5, -5, -5, 0.1, 0.5, 1, 2, 3], dtype=float) * 1e-4
    series = _make_series(values)

    result = find_peaks_valleys(series)
    valley_positions = sorted(series.index.get_loc(t) for t in result.index[result == "valley"])
    # plateau at indices 5,6,7,8; floor(mean) = floor(6.5) = 6
    assert 6 in valley_positions, (
        f"Expected valley at index 6 (floor midpoint of [5,6,7,8]), got {valley_positions}"
    )
    plateau_valleys = [p for p in valley_positions if 5 <= p <= 8]
    assert len(plateau_valleys) == 1, (
        f"Expected exactly 1 valley in plateau region [5-8], got {plateau_valleys}"
    )


# ── Odd-length plateau ─────────────────────────────────────────────────────────

def test_odd_plateau_midpoint_is_exact_center():
    """A 3-point plateau → midpoint index is the exact centre.

    Plateau at indices 4,5,6 (value -5e-4, non-zero to avoid the zeros branch).
    floor(mean([4,5,6])) = floor(5.0) = 5.
    """
    values = np.array([3, 2, 1, 0.1, -5, -5, -5, 0.1, 1, 2, 3], dtype=float) * 1e-4
    series = _make_series(values)

    result = find_peaks_valleys(series)
    valley_positions = sorted(series.index.get_loc(t) for t in result.index[result == "valley"])
    # floor(mean([4,5,6])) = floor(5.0) = 5
    assert 5 in valley_positions, (
        f"Expected valley at index 5 (centre of [4,5,6]), got {valley_positions}"
    )
    plateau_valleys = [p for p in valley_positions if 4 <= p <= 6]
    assert len(plateau_valleys) == 1


# ── Non-plateau series is unaffected ──────────────────────────────────────────

def test_no_plateau_series_unaffected():
    """When all values are distinct, collapse is a no-op."""
    values = np.array([1.0, 3.0, 2.0, 4.0, 1.5], dtype=float)
    series = _make_series(values)
    result = find_peaks_valleys(series)
    peaks   = list(result[result == "peak"])
    valleys = list(result[result == "valley"])
    # index 1 (value 3) is a peak, index 3 (value 4) is a peak, index 0/2/4 valleys
    assert len(peaks) >= 1
    assert len(valleys) >= 1
    overlap = set(result.index[result == "peak"]) & set(result.index[result == "valley"])
    assert not overlap
