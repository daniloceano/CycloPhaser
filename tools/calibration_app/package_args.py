"""Translate the app's widget/YAML values into the package's call arguments.

The app keeps ``use_filter`` as a bool everywhere it is shown or stored — the
"Apply Lanczos filter" checkbox, the YAML export and import, the Benchmark's
configuration files — because that is what those surfaces mean: filter on or
off. The package, however, warns on ``use_filter=True`` ("interpreted as
'auto'"), a warning addressed to a caller who typed ``True``. Passed straight
through, it reached the grid once per cyclone, asking the user to change a value
they never typed.

So the translation happens here, at the call into the package, and nowhere
else: ``True`` becomes ``'auto'``, which the package maps to the very same
window (``len(series)//2``), so results are unchanged. The warning itself stays
in the package for anyone calling it directly with ``True``.
"""

from __future__ import annotations


def package_use_filter(value):
    """``True`` → ``'auto'``; anything else (``False``, ``'auto'``, an int) unchanged.

    Args:
        value: The app-side ``use_filter`` value.

    Returns:
        The value to pass to ``process_vorticity``/``determine_periods``.
    """
    return "auto" if value is True else value
