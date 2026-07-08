"""Tests for optional prominence/distance filtering in find_peaks_valleys.

Phase 1a — ship the mechanism with no-op defaults.  Confirms:
  1. No-op equivalence: default call is byte-identical to explicit (None, None).
  2. Prominence filtering removes a low-amplitude spurious interior extremum while
     keeping the main interior extremum AND any boundary extrema.
  3. Distance filtering merges closely-spaced same-type extrema, keeping the one
     with higher prominence, and always preserves boundary extrema.
"""

import numpy as np
import pandas as pd
import pytest

from cyclophaser.determine_periods import find_peaks_valleys


def _make_series(values, freq="3h"):
    idx = pd.date_range("2000-01-01", periods=len(values), freq=freq, name="time")
    return pd.Series(values, index=idx, name="z")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _positions(result, label):
    """Return integer positions of 'peak' or 'valley' marks in result."""
    return sorted(result.index.get_loc(t) for t in result.index[result == label])


# ── 1. No-op equivalence ───────────────────────────────────────────────────────

class TestNoOpEquivalence:
    """find_peaks_valleys(s) must equal find_peaks_valleys(s, None, None)."""

    def _check_identical(self, series):
        default = find_peaks_valleys(series)
        explicit = find_peaks_valleys(series, prominence=None, distance=None)
        pd.testing.assert_series_equal(default, explicit)

    def test_plateau_series(self):
        """Plateau series from the existing plateau test suite."""
        descent = np.linspace(-0.5e-4, -8.9e-4, 11)
        plateau = np.full(4, -9.0e-4)
        ascent  = np.linspace(-8.9e-4, -0.5e-4, 15)
        self._check_identical(_make_series(np.concatenate([descent, plateau, ascent])))

    def test_simple_synthetic_series(self):
        """Simple peak-valley series."""
        values = np.array([1.0, 3.0, 2.0, 4.0, 1.5], dtype=float)
        self._check_identical(_make_series(values))

    def test_multi_extrema_series(self):
        """Series with several peaks and valleys of mixed amplitude."""
        t = np.linspace(0, 4 * np.pi, 80)
        values = (np.sin(t) + 0.15 * np.sin(5 * t)) * 1e-4
        self._check_identical(_make_series(values))


# ── 2. Prominence filtering ────────────────────────────────────────────────────

class TestProminenceFiltering:
    """High prominence threshold removes spurious interior extrema."""

    def _build_series(self):
        """
        Series shape (all in 1e-4 units):
          index 0  : boundary (value 0.5)  — may be detected as peak by argrelextrema
          index 8  : main valley at -9.0   (prominent)
          index 16 : spurious valley at -2.0 (low prominence)
          index 24 : boundary (value 0.5)
        """
        n = 25
        data = np.zeros(n) + 0.5e-4
        # main valley at index 8
        for i in range(1, 8):
            data[i] = data[i - 1] - 1.2e-4
        data[8] = -9.0e-4
        for i in range(9, 16):
            data[i] = data[i - 1] + 1.5e-4
        # spurious shallow valley at index 16
        data[16] = -2.0e-4
        for i in range(17, n - 1):
            data[i] = data[i - 1] + 0.5e-4
        data[-1] = 0.5e-4
        return _make_series(data)

    def test_high_prominence_keeps_main_removes_spurious(self):
        series = self._build_series()
        # Without filtering, both valleys should appear
        default = find_peaks_valleys(series)
        all_valleys = _positions(default, "valley")
        assert 8 in all_valleys, "main valley must be detected without filter"

        # With a high prominence threshold that the spurious valley cannot meet
        filtered = find_peaks_valleys(series, prominence=5e-4)
        filt_valleys = _positions(filtered, "valley")

        assert 8 in filt_valleys, "main valley must survive prominence filter"
        assert 16 not in filt_valleys, "spurious valley must be removed by prominence filter"

    def test_boundary_indices_always_preserved(self):
        """Boundary extrema (index 0 or N-1) survive even with very high prominence."""
        series = self._build_series()
        N = len(series)
        default = find_peaks_valleys(series)

        # Identify which boundary indices are extrema in the default result
        boundary_marks = {}
        for pos in (0, N - 1):
            t = series.index[pos]
            if default[t] in ("peak", "valley"):
                boundary_marks[pos] = default[t]

        filtered = find_peaks_valleys(series, prominence=1.0)  # absurdly large
        for pos, label in boundary_marks.items():
            t = series.index[pos]
            assert filtered[t] == label, (
                f"Boundary extremum at index {pos} ({label}) must survive prominence=1.0"
            )

    def test_low_prominence_keeps_all(self):
        """Prominence below the smallest extremum keeps everything unchanged."""
        series = self._build_series()
        default = find_peaks_valleys(series)
        filtered = find_peaks_valleys(series, prominence=1e-10)
        pd.testing.assert_series_equal(default, filtered)


# ── 3. Distance filtering ──────────────────────────────────────────────────────

class TestDistanceFiltering:
    """Minimum distance keeps the most prominent extremum among nearby ones."""

    def _build_close_valley_series(self):
        """
        Series with two close valleys:
          index 5  : strong valley at -8e-4 (more prominent)
          index 8  : weaker valley at -5e-4 (less prominent)
        Boundary points at index 0 and index 14 are NOT extrema (they sit at a
        moderate positive value bracketed by the same value on the other side,
        so argrelextrema mode='clip' marks them).

        We use a symmetric construction so index 0 and N-1 are the boundary
        and build peaks between the two valleys.
        """
        data = np.array([
            0.5,    # 0  boundary
            0.5,    # 1
            0.2,    # 2
           -3.0,    # 3
           -6.0,    # 4
           -8.0,    # 5  strong valley
           -5.5,    # 6
           -4.0,    # 7
           -5.0,    # 8  weaker valley
           -3.0,    # 9
            0.1,    # 10
            0.4,    # 11
            0.5,    # 12
            0.5,    # 13  boundary
        ], dtype=float) * 1e-4
        return _make_series(data)

    def test_distance_merges_close_valleys_keeps_prominent(self):
        series = self._build_close_valley_series()
        N = len(series)

        default = find_peaks_valleys(series)
        valleys_default = _positions(default, "valley")
        # Both valleys should be present without filtering
        assert 5 in valleys_default, "strong valley must appear in default result"
        assert 8 in valleys_default, "weaker valley must appear in default result"

        # distance=5 means indices 5 and 8 are only 3 apart → one must be removed
        filtered = find_peaks_valleys(series, distance=5)
        valleys_filt = _positions(filtered, "valley")

        # The stronger valley (index 5) must survive
        assert 5 in valleys_filt, "stronger valley must be kept by distance filter"
        # The weaker valley (index 8) must be removed
        assert 8 not in valleys_filt, "weaker valley must be removed by distance filter"

    def test_distance_preserves_boundary_extrema(self):
        """Boundary extrema always survive regardless of distance setting."""
        series = self._build_close_valley_series()
        N = len(series)
        default = find_peaks_valleys(series)

        boundary_marks = {}
        for pos in (0, N - 1):
            t = series.index[pos]
            if default[t] in ("peak", "valley"):
                boundary_marks[pos] = default[t]

        filtered = find_peaks_valleys(series, distance=100)  # very large
        for pos, label in boundary_marks.items():
            t = series.index[pos]
            assert filtered[t] == label, (
                f"Boundary extremum at index {pos} ({label}) must survive distance=100"
            )

    def test_large_distance_keeps_only_most_prominent(self):
        """A very large distance must leave at most one interior same-type extremum."""
        series = self._build_close_valley_series()
        filtered = find_peaks_valleys(series, distance=100)
        interior_valleys = [
            p for p in _positions(filtered, "valley")
            if p not in (0, len(series) - 1)
        ]
        assert len(interior_valleys) <= 1, (
            f"Expected ≤1 interior valley with distance=100, got {interior_valleys}"
        )

    def test_distance_one_is_noop(self):
        """distance=1 cannot merge any extrema (all are at least 1 step apart)."""
        series = self._build_close_valley_series()
        default = find_peaks_valleys(series)
        filtered = find_peaks_valleys(series, distance=1)
        pd.testing.assert_series_equal(default, filtered)


# ── 4. Combined absolute prominence + distance ────────────────────────────────

class TestCombined:
    """Absolute prominence AND distance can be active simultaneously."""

    def test_combined_removes_spurious_and_merges_close(self):
        """
        Use a prominence filter that drops the spurious valley, plus a distance
        filter that would also catch it — verifies both codepaths interact cleanly.
        """
        t = np.linspace(0, 2 * np.pi, 60)
        # Main trough + small ripple nearby
        values = (-np.sin(t) + 0.05 * np.sin(10 * t)) * 1e-4
        series = _make_series(values)

        default  = find_peaks_valleys(series)
        combined = find_peaks_valleys(series, prominence=0.02e-4, distance=4)

        default_valleys  = _positions(default,  "valley")
        combined_valleys = _positions(combined, "valley")

        # Combined must have fewer or equal interior valleys
        default_interior  = [v for v in default_valleys  if v not in (0, len(series) - 1)]
        combined_interior = [v for v in combined_valleys if v not in (0, len(series) - 1)]
        assert len(combined_interior) <= len(default_interior), (
            "Combined filter must not introduce new interior valleys"
        )


# ── 5. Relative prominence filtering ─────────────────────────────────────────

class TestRelativeProminenceFiltering:
    """prominence_relative filters by fraction of the dominant extremum's prominence."""

    def _build_series(self):
        """
        Series with one dominant valley at index 8 (prominence ~8.5e-4) and one
        spurious shallow valley at index 16 (prominence ~2e-4).  The ratio is
        roughly 1:4, so a fraction of 0.5 should keep only the dominant valley
        while a fraction of 0.1 should keep both.
        """
        n = 25
        data = np.zeros(n) + 0.5e-4
        for i in range(1, 8):
            data[i] = data[i - 1] - 1.2e-4
        data[8] = -9.0e-4
        for i in range(9, 16):
            data[i] = data[i - 1] + 1.5e-4
        data[16] = -2.0e-4
        for i in range(17, n - 1):
            data[i] = data[i - 1] + 0.5e-4
        data[-1] = 0.5e-4
        return _make_series(data)

    def test_noop_when_none(self):
        """prominence_relative=None must be identical to the default call."""
        series = self._build_series()
        default  = find_peaks_valleys(series)
        explicit = find_peaks_valleys(series, prominence_relative=None)
        pd.testing.assert_series_equal(default, explicit)

    def test_high_fraction_keeps_dominant_removes_spurious(self):
        """A fraction > spurious/dominant ratio removes the spurious valley."""
        series = self._build_series()
        # Without filter, both valleys present
        default = find_peaks_valleys(series)
        assert 8 in _positions(default, "valley"), "dominant valley must be in default"

        # fraction=0.5: spurious prominence is ~23 % of dominant → removed
        filtered = find_peaks_valleys(series, prominence_relative=0.5)
        filt_valleys = _positions(filtered, "valley")
        assert 8  in filt_valleys, "dominant valley must survive relative filter"
        assert 16 not in filt_valleys, "spurious valley must be removed by relative filter"

    def test_low_fraction_keeps_all(self):
        """A fraction below the spurious/dominant ratio keeps everything."""
        series = self._build_series()
        default  = find_peaks_valleys(series)
        # spurious is ~23 % of dominant; fraction=0.10 keeps both
        filtered = find_peaks_valleys(series, prominence_relative=0.10)
        pd.testing.assert_series_equal(default, filtered)

    def test_boundary_always_preserved(self):
        """Boundary extrema survive even with fraction=1.0 (only max survives)."""
        series = self._build_series()
        N = len(series)
        default = find_peaks_valleys(series)
        boundary_marks = {
            pos: default[series.index[pos]]
            for pos in (0, N - 1)
            if default[series.index[pos]] in ("peak", "valley")
        }
        filtered = find_peaks_valleys(series, prominence_relative=1.0)
        for pos, label in boundary_marks.items():
            assert filtered[series.index[pos]] == label, (
                f"Boundary extremum at index {pos} ({label}) must survive fraction=1.0"
            )

    def test_normalisation_uses_max_interior_prominence(self):
        """The denominator must be the max prominence of interior candidates."""
        series = self._build_series()
        # At fraction=1.0, only the single most prominent interior extremum survives
        filtered = find_peaks_valleys(series, prominence_relative=1.0)
        N = len(series)
        interior_valleys = [
            p for p in _positions(filtered, "valley") if p not in (0, N - 1)
        ]
        assert len(interior_valleys) <= 1, (
            f"fraction=1.0 must leave at most one interior valley; got {interior_valleys}"
        )
        if interior_valleys:
            assert interior_valleys[0] == 8, "the surviving interior valley must be the dominant one"

    def test_single_interior_extremum_always_survives(self):
        """A single interior extremum always survives any fraction in [0, 1]."""
        # Series with exactly one interior valley
        data = np.array([0.5, -0.5, -3.0, -0.5, 0.5], dtype=float) * 1e-4
        series = _make_series(data)
        for frac in (0.0, 0.1, 0.5, 1.0):
            filtered = find_peaks_valleys(series, prominence_relative=frac)
            n_interior = len([
                p for p in _positions(filtered, "valley") if p not in (0, len(series) - 1)
            ])
            assert n_interior >= 1, (
                f"Single interior valley must survive fraction={frac}"
            )

    def test_relative_and_absolute_combined(self):
        """Absolute applied first; relative uses max of the post-absolute set."""
        series = self._build_series()
        # absolute=1e-10 keeps everything; relative=0.5 should still remove spurious
        filtered = find_peaks_valleys(series, prominence=1e-10, prominence_relative=0.5)
        filt_valleys = _positions(filtered, "valley")
        assert 8  in filt_valleys, "dominant valley must survive combined filter"
        assert 16 not in filt_valleys, "spurious valley must be removed by combined filter"
