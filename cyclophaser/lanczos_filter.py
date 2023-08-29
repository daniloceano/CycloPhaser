
import numpy as np
from scipy.signal import convolve

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

def lanczos_filter(variable, window_length_lanczo, frequency):
    weights = pass_weights(window_length_lanczo, 1.0 / frequency)
    filtered_variable = convolve(variable, weights, mode="same")
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

def lanczos_bandpass_filter(variable, window_length_lanczo, cutoff_low, cutoff_high):
    weights = pass_weights_bandpass(window_length_lanczo, cutoff_low, cutoff_high)
    filtered_variable = convolve(variable, weights, mode="same")
    return filtered_variable