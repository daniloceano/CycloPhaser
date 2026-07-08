"""Integration tests: prominence/distance impact on the full phase-detection pipeline.

These tests complement the unit tests in test_prominence_distance.py (which cover
find_peaks_valleys in isolation) by verifying how prominence/distance interact with
the complete determine_periods pipeline on synthetic lifecycle series.

Tests are split into three groups:

1. NoOpEquivalence — prominence=None, prominence_relative=None, distance=None must
   produce byte-identical results to the default determine_periods call for every
   synthetic case in CASES.

2. ConservativeFiltering (absolute) — with small, conservative prominence/distance
   values that should not affect clean, well-formed synthetic signals:
   a) Core phase sequence must be preserved for cases that have expected_phases.
   b) The number of z_peaks_valleys can only decrease or stay the same.
   c) Phase detection does not crash or emit unexpected exceptions.

3. ConservativeRelativeFiltering — same checks using prominence_relative instead:
   a) No-op when prominence_relative=None.
   b) Small relative fraction preserves expected core phases.
   c) Filtering never adds extrema.
"""

import warnings

import pandas as pd
import pytest

from cyclophaser.determine_periods import determine_periods, find_peaks_valleys, process_vorticity, get_periods
from tests.synthetic.cases import CASES

# Conservative values chosen to minimally perturb clean synthetic signals.
# These are NOT calibrated for production use — purpose is to verify mechanics.
_PROM     = 1e-5    # s^-1, small relative to synthetic peak amplitude (~9e-4)
_DIST     = 3       # steps (9 h at 3 h/step)
_PROM_REL = 0.05    # 5 % of max interior prominence — very conservative


def _normalize(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


def _detected_sequence(df: pd.DataFrame) -> list[str]:
    """Return ordered unique normalized phase names from a periods DataFrame."""
    return list(dict.fromkeys(
        _normalize(v) for v in df["periods"].dropna()
    ))


# ── 1. No-op equivalence ──────────────────────────────────────────────────────

class TestNoOpEquivalence:
    """prominence=None, prominence_relative=None, distance=None → identical to default."""

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_full_pipeline_identical(self, case_name):
        """determine_periods with explicit None args equals the default call."""
        series = CASES[case_name]["series"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_default  = determine_periods(series)
            df_explicit = determine_periods(series, prominence=None,
                                            prominence_relative=None, distance=None)
        pd.testing.assert_frame_equal(df_default, df_explicit,
                                      check_like=False,
                                      obj=f"{case_name}: default vs explicit None")

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_get_periods_identical(self, case_name):
        """get_periods with explicit None args equals the default call."""
        series = CASES[case_name]["series"]
        zeta_df = pd.DataFrame({"zeta": series})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(zeta_df)
            df_default  = get_periods(vort)
            df_explicit = get_periods(vort, prominence=None,
                                      prominence_relative=None, distance=None)
        pd.testing.assert_frame_equal(df_default, df_explicit,
                                      obj=f"{case_name}: get_periods default vs None")

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_relative_none_identical(self, case_name):
        """prominence_relative=None alone must be identical to the default call."""
        series = CASES[case_name]["series"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_default  = determine_periods(series)
            df_explicit = determine_periods(series, prominence_relative=None)
        pd.testing.assert_frame_equal(df_default, df_explicit,
                                      check_like=False,
                                      obj=f"{case_name}: relative None vs default")


# ── 2. Conservative filtering ─────────────────────────────────────────────────

class TestConservativeFiltering:
    """Small prominence/distance values on clean signals preserve correct detection."""

    @pytest.mark.parametrize("case_name", [
        cn for cn, c in CASES.items()
        if c.get("test_mode", "standard") == "standard" and "expected_phases" in c
    ])
    def test_core_phases_preserved(self, case_name):
        """Conservative filtering does not drop expected phases from detection."""
        case = CASES[case_name]
        series = case["series"]
        expected = case["expected_phases"]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = determine_periods(series, prominence=_PROM, distance=_DIST)

        detected = _detected_sequence(df)
        for phase in expected:
            assert phase in detected, (
                f"{case_name}: expected phase '{phase}' missing with "
                f"prominence={_PROM:.1e}, distance={_DIST}"
            )

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_filtering_never_adds_extrema(self, case_name):
        """prominence/distance can only remove or keep extrema, never add them."""
        series = CASES[case_name]["series"]
        zeta_df = pd.DataFrame({"zeta": series})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(zeta_df)

        z = pd.Series(vort["vorticity_smoothed2"].values, index=series.index)
        base    = find_peaks_valleys(z)
        filtered = find_peaks_valleys(z, prominence=_PROM, distance=_DIST)

        n_base     = (base    == "peak").sum() + (base    == "valley").sum()
        n_filtered = (filtered == "peak").sum() + (filtered == "valley").sum()

        assert n_filtered <= n_base, (
            f"{case_name}: filtering introduced new extrema "
            f"({n_filtered} > {n_base})"
        )

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_no_crash(self, case_name):
        """determine_periods with prominence/distance must not raise."""
        series = CASES[case_name]["series"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = determine_periods(series, prominence=_PROM, distance=_DIST)
        assert df is not None
        assert "periods" in df.columns


# ── 3. Conservative relative filtering ───────────────────────────────────────

class TestConservativeRelativeFiltering:
    """prominence_relative at small fraction on clean signals behaves conservatively."""

    @pytest.mark.parametrize("case_name", [
        cn for cn, c in CASES.items()
        if c.get("test_mode", "standard") == "standard" and "expected_phases" in c
    ])
    def test_core_phases_preserved(self, case_name):
        """Conservative relative fraction does not drop expected phases."""
        case = CASES[case_name]
        series = case["series"]
        expected = case["expected_phases"]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = determine_periods(series, prominence_relative=_PROM_REL)

        detected = _detected_sequence(df)
        for phase in expected:
            assert phase in detected, (
                f"{case_name}: expected phase '{phase}' missing with "
                f"prominence_relative={_PROM_REL}"
            )

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_filtering_never_adds_extrema(self, case_name):
        """prominence_relative can only remove or keep extrema, never add them."""
        series = CASES[case_name]["series"]
        zeta_df = pd.DataFrame({"zeta": series})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(zeta_df)

        z = pd.Series(vort["vorticity_smoothed2"].values, index=series.index)
        base     = find_peaks_valleys(z)
        filtered = find_peaks_valleys(z, prominence_relative=_PROM_REL)

        n_base     = (base     == "peak").sum() + (base     == "valley").sum()
        n_filtered = (filtered == "peak").sum() + (filtered == "valley").sum()

        assert n_filtered <= n_base, (
            f"{case_name}: relative filter introduced new extrema "
            f"({n_filtered} > {n_base})"
        )

    @pytest.mark.parametrize("case_name", list(CASES.keys()))
    def test_no_crash(self, case_name):
        """determine_periods with prominence_relative must not raise."""
        series = CASES[case_name]["series"]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = determine_periods(series, prominence_relative=_PROM_REL)
        assert df is not None
        assert "periods" in df.columns
