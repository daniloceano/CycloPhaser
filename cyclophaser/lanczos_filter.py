
import numpy as np
from scipy.signal import convolve

# ---------------------------------------------------------------------------
# boundary_padding: "zero" (default) vs "reflect" / "edge"
# ---------------------------------------------------------------------------
# Both filters below convolve the input against a Lanczos kernel.  Historically
# that convolution was always ``scipy.signal.convolve(variable, weights,
# mode="same")``, which implicitly ZERO-PADS the input outside its own range.
#
# For vorticity that is quantitatively destructive.  Vorticity has a non-zero
# floor (order -5e-5 s^-1), so the "missing" samples the kernel sees outside the
# series are not a neutral continuation of the signal -- they are a jump to
# zero.  Two properties of this specific configuration amplify that:
#
#   * The kernel is about HALF the series length.  ``process_vorticity`` sets
#     ``window_length_lanczo = len(zeta) // 2`` for ``use_filter='auto'``, and
#     ``pass_weights``/``pass_weights_bandpass`` return roughly ``window`` taps.
#     Measured over the 51-track calibration set: kernel length / series length
#     has a median of 0.494, so the zero-padded boundary zone is M//2 ~ 24 % of
#     the series at EACH end -- about 48 % of every series in total.
#   * The bandpass kernel does not actually reject DC at these window lengths.
#     Measured on the same set, sum(weights) has a median of 0.629 and
#     |H(DC)|/|H|max a median of 0.79, so most of the (large) mean vorticity
#     passes through.  Convolving that against zeros therefore removes a large
#     constant, not a small one.
#
# The result is a step between the boundary value and the interior worth a
# median of 74 % of the cyclone's own peak-to-peak amplitude (q25 0.40,
# q75 1.29), spread as a ramp over the boundary zone.  Because the DC gain
# g(i) rises from the edge inward and mean(zeta) is negative, that ramp has the
# sign of a spurious DEEPENING.  On the 51-track calibration set the ramp alone
# accounts for >= 80 % of the slope measured at t0 in 51/51 tracks, and the
# delivered dz at t0 sits at a median 0.95 of the maximum deepening rate of the
# whole first deepening (against 0.29 for a lightly-smoothed finite difference
# of the raw series).
#
# ``boundary_padding`` selects the padding used instead:
#
#   "reflect" -- DEFAULT since the boundary-artifact fix.  Pads with the
#                reflection of the series about its edge samples.  Measured
#                effect on the calibration set: the normalised |dz| at t0 drops
#                from a median 0.95 to 0.42, and at the last sample from 0.98 to
#                0.35 (raw-signal reference: 0.29).
#   "zero"     -- The pre-fix behaviour, kept so it can be reproduced exactly.
#                Pass it explicitly to reproduce results from versions before
#                the default changed.
#   "edge"     -- Pads with the edge sample repeated.  Between the two on the
#                boundary metric (median 0.50 at t0) and marginally less
#                disruptive to detected phase sequences; useful for calibration
#                work where the smallest departure from "zero" is preferred.
#
# The DEFAULT IS NOW "reflect".  This is a deliberate behaviour change: leaving
# a documented, quantified artefact on by default was the larger cost.  Anyone
# who needs the old output must now pass ``boundary_padding="zero"``
# explicitly.
#
# Note on ``replace_endpoints_with_lowpass`` (in ``process_vorticity``): that
# option was introduced as a palliative for this same artefact, and it calls
# ``lanczos_filter`` -- i.e. it replaces zero-padded bandpass endpoints with
# zero-padded lowpass endpoints.  With ``boundary_padding="reflect"`` it loses
# its reason to exist and is a candidate for future deprecation.  It is
# deliberately left untouched here.
#
# The kernels themselves (``pass_weights``, ``pass_weights_bandpass``) are NOT
# modified by this option: the correction is purely a boundary condition.
# ---------------------------------------------------------------------------

PADDING_MODES = ("zero", "reflect", "edge")


def _validate_padding(boundary_padding):
    if boundary_padding not in PADDING_MODES:
        raise ValueError(
            f"boundary_padding must be one of {PADDING_MODES}, got {boundary_padding!r}."
        )


def _convolve_same(variable, weights, boundary_padding="reflect"):
    """Convolve *variable* with *weights*, returning an array of the same length.

    With "reflect" (the default) or "edge" the input is padded explicitly with
    ``np.pad`` and convolved in "valid" mode.  With ``boundary_padding="zero"``
    this delegates to ``scipy.signal.convolve(..., mode="same")`` unchanged, so
    the pre-fix output is reproduced exactly.

    The pad widths (``M//2`` on the left, ``M-1-M//2`` on the right) reproduce
    scipy's own "same" alignment exactly, so the ONLY difference between the
    modes is what the kernel sees beyond the ends of the series -- never a
    shift in time.

    Args:
        variable (array-like): input data.
        weights (array-like): filter kernel.
        boundary_padding (str): one of ``PADDING_MODES``. See the module
            comment above for the rationale and the measured effect.

    Returns:
        numpy.ndarray: filtered data, same length as *variable*.

    Raises:
        ValueError: if *boundary_padding* is not a recognised mode, or if the
            output length does not match the input length.
    """
    _validate_padding(boundary_padding)

    if boundary_padding == "zero":
        filtered = convolve(variable, weights, mode="same")
    else:
        data = np.asarray(variable, dtype=float)
        w = np.asarray(weights, dtype=float)
        n, m = data.size, w.size
        left = m // 2
        right = m - 1 - left
        if n < 2 and boundary_padding == "reflect":
            # np.pad's "reflect" is undefined for a single sample; "edge" is the
            # degenerate-but-defined equivalent there.
            padded = np.pad(data, (left, right), mode="edge")
        else:
            padded = np.pad(data, (left, right), mode=boundary_padding)
        filtered = np.convolve(padded, w, mode="valid")

    filtered = np.asarray(filtered)
    if filtered.shape[0] != np.asarray(variable).shape[0]:
        raise ValueError(
            "Filtered output length "
            f"({filtered.shape[0]}) does not match input length "
            f"({np.asarray(variable).shape[0]}); this is a bug in "
            "_convolve_same."
        )
    return filtered


def pass_weights(window, cutoff):
    """Calculate weights for a low pass Lanczos filter.

    Args:

    window: int
        The length of the filter window.

    cutoff: float
        The cutoff frequency in inverse time steps.

    """
    order = ((window - 1) // 2) + 1
    nwts = 2 * order + 1
    w = np.zeros([nwts])
    n = nwts // 2
    w[n] = 2 * cutoff
    k = np.arange(1.0, n)
    sigma = np.sin(np.pi * k / n) * n / (np.pi * k)
    firstfactor = np.sin(2.0 * np.pi * cutoff * k) / (np.pi * k)
    w[n - 1 : 0 : -1] = firstfactor * sigma
    w[n + 1 : -1] = firstfactor * sigma
    return w[1:-1]

def lanczos_filter(variable, window_length_lanczo, frequency, boundary_padding="reflect"):
    """
    Apply a low pass Lanczos filter to the input variable.

    Args:
        variable (array-like): The input data to be filtered.
        window_length_lanczo (int): The length of the Lanczos filter window.
        frequency (float): The cutoff frequency for the filter in time steps.
        boundary_padding (str, optional): How the series is extended beyond its
            own ends before convolution. ``"reflect"`` (default) and ``"edge"``
            remove most of the zero-padding boundary artefact; ``"zero"``
            reproduces the behaviour of versions before this default changed.
            See the module-level comment in ``cyclophaser/lanczos_filter.py``
            for the mechanism and the measured effect. The kernel itself is
            unaffected.

    Returns:
        numpy.ndarray: The filtered variable with noise reduced, same length as
        *variable*.

    Raises:
        ValueError: if *boundary_padding* is not one of ``PADDING_MODES``.
    """
    weights = pass_weights(window_length_lanczo, 1.0 / frequency)
    filtered_variable = _convolve_same(variable, weights, boundary_padding)
    return filtered_variable

def pass_weights_bandpass(window, cutoff_low, cutoff_high):
    """Calculate weights for a bandpass Lanczos filter.

    Args:
    window: int
        The length of the filter window.

    cutoff_low: float
        The low cutoff frequency in inverse time steps.

    cutoff_high: float
        The high cutoff frequency in inverse time steps.

    """
    order = ((window - 1) // 2) + 1
    nwts = 2 * order + 1
    w = np.zeros([nwts])
    n = nwts // 2
    w[n] = 2 * (cutoff_high - cutoff_low)
    k = np.arange(1.0, n)
    sigma = np.sin(np.pi * k / n) * n / (np.pi * k)
    firstfactor = (
        np.sin(2.0 * np.pi * cutoff_high * k) / (np.pi * k)
        - np.sin(2.0 * np.pi * cutoff_low * k) / (np.pi * k)
    )
    w[n - 1 : 0 : -1] = firstfactor * sigma
    w[n + 1 : -1] = firstfactor * sigma
    return w[1:-1]

def lanczos_bandpass_filter(variable, window_length_lanczo, cutoff_low, cutoff_high,
                            boundary_padding="reflect"):
    """
    Apply a bandpass Lanczos filter to the input variable.

    Args:
        variable (array-like): The input data to be filtered.
        window_length_lanczo (int): The length of the Lanczos filter window.
        cutoff_low (float): The low cutoff frequency for the filter in time steps.
        cutoff_high (float): The high cutoff frequency for the filter in time steps.
        boundary_padding (str, optional): How the series is extended beyond its
            own ends before convolution. ``"reflect"`` (default) and ``"edge"``
            remove most of the zero-padding boundary artefact; ``"zero"``
            reproduces the behaviour of versions before this default changed.
            See the module-level comment in ``cyclophaser/lanczos_filter.py``
            for the mechanism and the measured effect. The kernel itself is
            unaffected.

    Returns:
        numpy.ndarray: The filtered variable with the specified frequency range,
        same length as *variable*.

    Raises:
        ValueError: if *boundary_padding* is not one of ``PADDING_MODES``.
    """
    weights = pass_weights_bandpass(window_length_lanczo, cutoff_low, cutoff_high)
    filtered_variable = _convolve_same(variable, weights, boundary_padding)
    return filtered_variable