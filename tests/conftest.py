"""Marker registration only.

Deliberately minimal. The package's CI installs the wheel plus pytest and
nothing else, and a conftest is imported at COLLECTION time — anything it tries
to import that is not a package dependency would fail the entire suite rather
than one module, which is how this research front broke the package's CI once
already. So nothing is imported here and nothing is configured beyond a name.
"""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "browser: drives a real Chromium against a real `streamlit run` of the "
        "calibration app. Skipped unless playwright and its Chromium are "
        "installed (pip install playwright && python -m playwright install "
        "chromium). Deselect with -m 'not browser'.",
    )
