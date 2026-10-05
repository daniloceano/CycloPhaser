"""Tests for optional prominence filtering in find_peaks_valleys.

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
        explicit = find_peaks_valleys(series, prominence=None)
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


# ── 3. `distance` is gone ─────────────────────────────────────────────────────

class TestDistanceRemoved:
    """`distance` was removed; passing it must raise the ordinary TypeError.

    It was a third extrema filter (minimum separation between surviving
    same-type extrema) added after v2.0.0 and never published. Measured over the
    47 training series it removed nothing at any value up to 14 and changed no
    phase until 20, against a calibrated value of 5 — redundant with
    `prominence_relative` throughout the calibrated range. There is deliberately
    NO compatibility shim: a caller still passing it should fail loudly.
    See research/inert_params/REPORT_inertia_sweep.md.
    """

    def test_find_peaks_valleys_rejects_distance(self):
        series = _make_series(np.sin(np.linspace(0, 4 * np.pi, 40)) * 1e-4)
        with pytest.raises(TypeError, match="distance"):
            find_peaks_valleys(series, distance=5)

    def test_get_periods_rejects_distance(self):
        from cyclophaser.determine_periods import get_periods, process_vorticity
        df = pd.DataFrame({"zeta": np.sin(np.linspace(0, 4 * np.pi, 80)) * 1e-4})
        with pytest.raises(TypeError, match="distance"):
            get_periods(process_vorticity(df), distance=5)

    def test_signatures_carry_no_distance(self):
        import inspect

        from cyclophaser.determine_periods import (_refine_extrema,
                                                   determine_periods, get_periods)
        for fn in (find_peaks_valleys, _refine_extrema, get_periods,
                   determine_periods):
            assert "distance" not in inspect.signature(fn).parameters, fn.__name__


# ── 4. Absolute prominence, combined with the relative mode ───────────────────

class TestCombined:
    """Absolute and relative prominence can be active simultaneously."""

    def test_combined_absolute_then_relative(self):
        """Absolute runs first; relative is applied to the survivors."""
        t = np.linspace(0, 2 * np.pi, 60)
        # Main trough + small ripple nearby
        values = (-np.sin(t) + 0.05 * np.sin(10 * t)) * 1e-4
        series = _make_series(values)

        default  = find_peaks_valleys(series)
        combined = find_peaks_valleys(series, prominence=0.02e-4,
                                      prominence_relative=0.10)

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
