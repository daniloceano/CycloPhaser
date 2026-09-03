# Tests for the ``boundary_padding`` opt-in parameter.
#
# Background
# ----------
# ``lanczos_filter`` and ``lanczos_bandpass_filter`` have always convolved via
# ``scipy.signal.convolve(variable, weights, mode="same")``, which implicitly
# ZERO-PADS the input beyond its own ends.  Vorticity has a non-zero floor
# (order -5e-5 s^-1), so those "missing" samples are a jump to zero rather than
# a neutral continuation of the signal, and two properties of this
# configuration amplify the damage:
#
#   * The kernel is about HALF the series length (``process_vorticity`` sets
#     ``window_length_lanczo = len(zeta) // 2`` under ``use_filter='auto'``;
#     measured kernel/series length ratio has a median of 0.494 over the
#     51-track calibration set), so the contaminated zone is ~24% of the series
#     at EACH end -- about 48% of every series.
#   * The bandpass kernel does not actually reject DC at these window lengths
#     (``sum(weights)`` median 0.629), so most of the large mean vorticity
#     passes through and convolving it against zeros removes a large constant.
#
# The result is a step between the boundary value and the interior worth a
# median of 74% of the cyclone's own peak-to-peak amplitude, spread as a ramp
# with the sign of a spurious DEEPENING.  On the calibration set that ramp alone
# accounts for >= 80% of the slope measured at t0 in 51/51 tracks
# (research/boundary-artifacts branch diagnostic).
#
# ``boundary_padding`` (opt-in; default "zero" reproduces prior behaviour
# exactly) selects the padding used instead.  The kernels themselves are NOT
# touched -- the correction is purely a boundary condition on the convolution.
#
# What this module locks in
# -------------------------
#   1. ZERO REGRESSION at the default: "zero" is byte-identical to omitting the
#      parameter entirely, at the filter level and end-to-end.
#   2. Output length is preserved in every mode, for odd and even kernels and
#      for degenerate series lengths.
#   3. The pad widths reproduce scipy's own "same" alignment exactly, so the
#      only difference between modes is what lies beyond the ends -- never a
#      shift in time.
#   4. The artefact is actually reduced: with "reflect", the normalised |dz| at
#      the first sample falls from a median ~0.95 to ~0.42 over the 51 tracks.
#   5. Invalid modes raise, at both the filter and the process_vorticity level.

import glob
import os
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.signal import convolve

from cyclophaser import example_file
from cyclophaser.determine_periods import (
    determine_periods,
    get_periods,
    process_vorticity,
)
from cyclophaser.lanczos_filter import (
    PADDING_MODES,
    lanczos_bandpass_filter,
    lanczos_filter,
    pass_weights,
    pass_weights_bandpass,
)

_CALIBRATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "calibration_data")

# IMPORTANT -- two filter configurations are used below, and the difference
# between them is not cosmetic.
#
# ``use_filter`` is documented as "'auto', or an integer window length".  Python
# bools ARE ints, so ``use_filter=True`` is read as **window length 1**, not as
# "filtering enabled".  A 1-tap Lanczos kernel is a scalar multiply (0.0714 for
# cutoff_low=168 / cutoff_high=24), so with ``use_filter=True`` the Lanczos
# filter performs no convolution at all, there is no boundary zone, and
# ``boundary_padding`` is a NO-OP.
#
# The author's validated 51-track calibration uses ``use_filter=True`` (it is
# what tools/calibration_app/app.py's "Apply Lanczos filter" checkbox sends, and
# what tests/test_decay_tail_amplitude_fraction.py records).  The artefact this
# option corrects therefore lives on the ``use_filter='auto'`` path -- the
# PACKAGE DEFAULT, i.e. what a bare ``determine_periods(series)`` call does --
# where the kernel is ``len(series)//2`` taps.
#
# So: _FILTER_PARAMS_CALIB pins the author's calibration (where the option must
# be a verified no-op), and _FILTER_PARAMS_ACTIVE pins the path where the
# Lanczos filter genuinely runs (where the artefact and its reduction are
# measured).
_FILTER_PARAMS_CALIB = dict(
    use_filter=True,
    cutoff_low=168,
    cutoff_high=24,
    replace_endpoints_with_lowpass=0,
    use_smoothing=31,
    use_smoothing_twice=False,
    savgol_polynomial=3,
)
_FILTER_PARAMS_ACTIVE = dict(_FILTER_PARAMS_CALIB, use_filter="auto")

_PHASE_PARAMS = dict(
    threshold_mature_distance=0.18,
    threshold_mature_length=0.15,
    prominence_relative=0.3,
    distance=3,
    mature_amplitude_fraction=0.95,
    decay_tail_amplitude_fraction=0.05,
    length_scale="local",
    mature_method="amplitude",
)

_ALL_TRACK_IDS = sorted(
    os.path.basename(f)[:-4] for f in glob.glob(f"{_CALIBRATION_DATA_DIR}/*.csv")
)


def _load_track(cyclone_id: str) -> pd.Series:
    path = f"{_CALIBRATION_DATA_DIR}/{cyclone_id}.csv"
    df = pd.read_csv(path, sep=";", index_col="time", parse_dates=True)
    return df["min_max_zeta_850"]


def _edge_dz_ratio(series: pd.Series, boundary_padding: str) -> float:
    """|dz| at the first sample, normalised by the maximum deepening rate of the
    first deepening (t0 -> first interior z_valley).

    This is the metric the research/boundary-artifacts diagnostic used: 1.0
    means the very first sample already sits at the strongest deepening rate the
    cyclone ever reaches on its way to the first vorticity minimum, which is
    what the zero-padding ramp produces.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(
            pd.DataFrame({"zeta": series.rename("zeta")}),
            boundary_padding=boundary_padding,
            **_FILTER_PARAMS_ACTIVE,
        )
        df = get_periods(vort, **_PHASE_PARAMS)
    dz = vort.dz_dt_smoothed2.values
    zpv = df["z_peaks_valleys"].values
    valleys = np.where(zpv == "valley")[0]
    interior = valleys[valleys > 0]
    end = int(interior.min()) if interior.size else len(dz) - 1
    denom = np.abs(dz[: end + 1]).max()
    return float(abs(dz[0]) / denom) if denom > 0 else float("nan")


# ── 1. Zero regression at the default ────────────────────────────────────────

def test_padding_modes_constant():
    assert PADDING_MODES == ("zero", "reflect", "edge")


@pytest.mark.parametrize("n", [30, 66, 113, 259])
def test_zero_mode_is_byte_identical_to_scipy_same(n):
    """The default path must still be exactly scipy's convolve(mode='same')."""
    rng = np.random.default_rng(n)
    x = rng.normal(-5e-5, 1e-5, n)
    window = n // 2
    weights_bp = pass_weights_bandpass(window, 1 / 168, 1 / 24)
    weights_lp = pass_weights(window, 1 / 24)

    np.testing.assert_array_equal(
        np.asarray(lanczos_bandpass_filter(x, window, 1 / 168, 1 / 24, "zero")),
        np.asarray(convolve(x, weights_bp, mode="same")),
    )
    np.testing.assert_array_equal(
        np.asarray(lanczos_filter(x, window, 24.0, "zero")),
        np.asarray(convolve(x, weights_lp, mode="same")),
    )


@pytest.mark.parametrize("n", [30, 66, 113, 259])
def test_default_argument_equals_explicit_zero(n):
    """Omitting the parameter must equal passing 'zero' explicitly."""
    rng = np.random.default_rng(n + 1)
    x = rng.normal(-5e-5, 1e-5, n)
    window = n // 2
    np.testing.assert_array_equal(
        np.asarray(lanczos_bandpass_filter(x, window, 1 / 168, 1 / 24)),
        np.asarray(lanczos_bandpass_filter(x, window, 1 / 168, 1 / 24, "zero")),
    )
    np.testing.assert_array_equal(
        np.asarray(lanczos_filter(x, window, 24.0)),
        np.asarray(lanczos_filter(x, window, 24.0, "zero")),
    )


@pytest.mark.parametrize("filter_params", [_FILTER_PARAMS_CALIB, _FILTER_PARAMS_ACTIVE],
                         ids=["calib", "active"])
@pytest.mark.parametrize("cyclone_id", _ALL_TRACK_IDS)
def test_process_vorticity_default_is_byte_identical(cyclone_id, filter_params):
    """process_vorticity: default vs boundary_padding='zero', every array.

    Checked on both the author's calibration (``use_filter=True``) and the
    package-default path (``use_filter='auto'``), because only the latter runs
    a real convolution.
    """
    series = _load_track(cyclone_id)
    zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        base = process_vorticity(zeta_df.copy(), **filter_params)
        explicit = process_vorticity(
            zeta_df.copy(), boundary_padding="zero", **filter_params
        )
    for var in base.data_vars:
        np.testing.assert_array_equal(
            base[var].values, explicit[var].values, err_msg=f"{cyclone_id}: {var}"
        )


@pytest.mark.parametrize("cyclone_id", _ALL_TRACK_IDS)
def test_determine_periods_default_is_byte_identical(cyclone_id):
    """End-to-end phases: default vs boundary_padding='zero'."""
    series = _load_track(cyclone_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        base = determine_periods(series, **_FILTER_PARAMS_CALIB, **_PHASE_PARAMS)
        explicit = determine_periods(
            series, boundary_padding="zero", **_FILTER_PARAMS_CALIB, **_PHASE_PARAMS
        )
    pd.testing.assert_frame_equal(base, explicit)


def test_package_defaults_unchanged_end_to_end():
    """A bare determine_periods() call on the shipped example is unchanged by
    the presence of the new parameter (guards the all-defaults path, including
    replace_endpoints_with_lowpass=24, which the calibration above disables)."""
    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    series = track["min_max_zeta_850"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        base = determine_periods(series, x=track.index)
        explicit = determine_periods(series, x=track.index, boundary_padding="zero")
    pd.testing.assert_frame_equal(base, explicit)


# ── 2. Output length is preserved in every mode ──────────────────────────────

@pytest.mark.parametrize("mode", PADDING_MODES)
@pytest.mark.parametrize("n", [1, 2, 3, 5, 30, 31, 66, 99, 100, 259])
def test_output_length_preserved(mode, n):
    rng = np.random.default_rng(n * 7)
    x = rng.normal(-5e-5, 1e-5, n)
    window = max(1, n // 2)
    assert len(lanczos_bandpass_filter(x, window, 1 / 168, 1 / 24, mode)) == n
    assert len(lanczos_filter(x, window, 24.0, mode)) == n


@pytest.mark.parametrize("mode", PADDING_MODES)
@pytest.mark.parametrize("window", [3, 8, 9, 30, 31, 200])
def test_output_length_preserved_for_odd_and_even_kernels(mode, window):
    """Kernel length parity and kernels LONGER than the series must both be
    handled without changing the output length."""
    n = 40
    rng = np.random.default_rng(window)
    x = rng.normal(-5e-5, 1e-5, n)
    assert len(lanczos_bandpass_filter(x, window, 1 / 168, 1 / 24, mode)) == n
    assert len(lanczos_filter(x, window, 24.0, mode)) == n


@pytest.mark.parametrize("cyclone_id", _ALL_TRACK_IDS)
@pytest.mark.parametrize("mode", PADDING_MODES)
def test_process_vorticity_length_preserved(cyclone_id, mode):
    series = _load_track(cyclone_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(
            pd.DataFrame({"zeta": series.rename("zeta")}),
            boundary_padding=mode,
            **_FILTER_PARAMS_ACTIVE,
        )
    for var in vort.data_vars:
        assert len(vort[var].values) == len(series), f"{cyclone_id}/{mode}: {var}"


# ── 3. No time shift: pad widths reproduce scipy's 'same' alignment ──────────

@pytest.mark.parametrize("m", [1, 2, 3, 4, 8, 9, 31])
@pytest.mark.parametrize("n", [7, 20, 101])
def test_pad_widths_reproduce_same_alignment(n, m):
    """Padding with zeros through the np.pad/'valid' route must reproduce
    scipy's 'same' output exactly.  This is what guarantees that switching mode
    changes only what lies beyond the ends of the series, never the alignment
    in time.
    """
    rng = np.random.default_rng(n * 100 + m)
    x = rng.normal(size=n)
    h = rng.normal(size=m)
    left, right = m // 2, m - 1 - m // 2
    manual = np.convolve(np.pad(x, (left, right), mode="constant"), h, mode="valid")
    np.testing.assert_allclose(manual, convolve(x, h, mode="same"), atol=1e-12)


# ── 4. The artefact is actually reduced ──────────────────────────────────────

def test_reflect_reduces_edge_dz_artifact_across_calibration_set():
    """Median normalised |dz| at the first sample over the 51 calibration
    tracks.  Reference measurement from the research/boundary-artifacts
    diagnostic: 0.95 with 'zero', 0.42 with 'reflect', 0.50 with 'edge'.
    Bounds are deliberately loose so the test locks in the EFFECT, not the
    third decimal of a smoothing chain that may legitimately be retuned.
    """
    zero, reflect, edge = [], [], []
    for cyclone_id in _ALL_TRACK_IDS:
        series = _load_track(cyclone_id)
        zero.append(_edge_dz_ratio(series, "zero"))
        reflect.append(_edge_dz_ratio(series, "reflect"))
        edge.append(_edge_dz_ratio(series, "edge"))

    med_zero = float(np.median(zero))
    med_reflect = float(np.median(reflect))
    med_edge = float(np.median(edge))

    # The artefact is present at the default.
    assert med_zero > 0.85, med_zero
    # 'reflect' roughly halves it.
    assert med_reflect < 0.55, med_reflect
    assert med_reflect < 0.6 * med_zero, (med_reflect, med_zero)
    # 'edge' also reduces it, and is the more conservative of the two.
    assert med_edge < 0.60, med_edge
    assert med_reflect <= med_edge + 1e-9, (med_reflect, med_edge)
    # It is a broad improvement, not one or two tracks dragging the median.
    improved = sum(1 for a, b in zip(zero, reflect) if b < a)
    assert improved >= 45, improved


def test_reflect_changes_the_signal_only_where_expected():
    """The correction must act on the boundary zone.  The kernel is ~half the
    series, so the contaminated half-width is M//2; the middle of the series
    should be far less affected than the edges.
    """
    series = _load_track("20160735")
    zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = process_vorticity(zeta_df.copy(), **_FILTER_PARAMS_ACTIVE)
        b = process_vorticity(
            zeta_df.copy(), boundary_padding="reflect", **_FILTER_PARAMS_ACTIVE
        )
    za, zb = a.vorticity_smoothed2.values, b.vorticity_smoothed2.values
    n = len(za)
    half = len(pass_weights_bandpass(n // 2, 1 / 168, 1 / 24)) // 2
    scale = np.abs(za).max()
    edge_err = np.abs(za[:half] - zb[:half]).max() / scale
    core = slice(half, n - half)
    core_err = np.abs(za[core] - zb[core]).max() / scale
    assert edge_err > core_err, (edge_err, core_err)
    assert edge_err > 0.05, edge_err


def test_option_is_a_noop_under_the_authors_calibration():
    """``use_filter=True`` means window length 1 (bools are ints in Python), so
    the Lanczos "filter" is a scalar multiply with no convolution and therefore
    no boundary zone.  Every padding mode must produce byte-identical output
    there.

    This is locked in deliberately: the author's validated 51-track calibration
    uses ``use_filter=True``, so ``boundary_padding`` cannot change those
    results, and the artefact it corrects only exists on the ``use_filter='auto'``
    (package-default) path.  If this test ever starts failing, ``use_filter``'s
    bool handling has changed and the calibration's meaning has changed with it.
    """
    for cyclone_id in _ALL_TRACK_IDS[:8]:
        series = _load_track(cyclone_id)
        zeta_df = pd.DataFrame({"zeta": series.rename("zeta")})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ref = process_vorticity(zeta_df.copy(), **_FILTER_PARAMS_CALIB)
            for mode in PADDING_MODES:
                got = process_vorticity(
                    zeta_df.copy(), boundary_padding=mode, **_FILTER_PARAMS_CALIB
                )
                for var in ref.data_vars:
                    np.testing.assert_array_equal(
                        ref[var].values, got[var].values,
                        err_msg=f"{cyclone_id}/{mode}: {var}",
                    )


# ── 5. Invalid modes raise ───────────────────────────────────────────────────

def test_invalid_mode_raises_in_filters():
    x = np.zeros(20)
    with pytest.raises(ValueError, match="boundary_padding"):
        lanczos_filter(x, 10, 24.0, "bogus")
    with pytest.raises(ValueError, match="boundary_padding"):
        lanczos_bandpass_filter(x, 10, 1 / 168, 1 / 24, "bogus")


def test_invalid_mode_raises_in_process_vorticity():
    series = _load_track(_ALL_TRACK_IDS[0])
    with pytest.raises(ValueError, match="boundary_padding"):
        process_vorticity(
            pd.DataFrame({"zeta": series.rename("zeta")}), boundary_padding="bogus"
        )


def test_invalid_mode_raises_in_determine_periods():
    series = _load_track(_ALL_TRACK_IDS[0])
    with pytest.raises(ValueError, match="boundary_padding"):
        determine_periods(series, boundary_padding="bogus")


def test_invalid_mode_raises_even_when_filter_is_off():
    """Validation happens up front, so a typo is reported rather than silently
    ignored on the use_filter=False path."""
    series = _load_track(_ALL_TRACK_IDS[0])
    with pytest.raises(ValueError, match="boundary_padding"):
        process_vorticity(
            pd.DataFrame({"zeta": series.rename("zeta")}),
            use_filter=False,
            boundary_padding="bogus",
        )
