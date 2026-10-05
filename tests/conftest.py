"""Marker registration, plus the CI's installed-package lock.

Deliberately minimal. The package's CI installs the wheel plus pytest and
nothing else, and a conftest is imported at COLLECTION time — anything it tries
to import that is not a package dependency would fail the entire suite rather
than one module, which is how this research front broke the package's CI once
already. So nothing outside the package is imported here.

The lock. With CYCLOPHASER_REQUIRE_INSTALLED=1 the session refuses to run unless
`cyclophaser` resolves to a site-packages copy (the wheel CI just installed), and
fails at the end if any `cyclophaser*` module the tests imported came from
elsewhere. Without it, `python -m pytest` from the repo root silently tests the
source tree instead of the wheel. Unset, the variable changes nothing: no
import, no check. In every run the terminal summary prints the
`cyclophaser.__file__` the session actually used (read from sys.modules, never
imported for the purpose).
"""

import os
import sys
from pathlib import Path

import pytest

_LOCK_ENV = "CYCLOPHASER_REQUIRE_INSTALLED"


def _lock_on():
    return os.environ.get(_LOCK_ENV, "") not in ("", "0")


def _installed(path):
    return path is not None and "site-packages" in Path(path).resolve().parts


def _loaded_cyclophaser_files():
    return {n: getattr(m, "__file__", None) for n, m in sorted(sys.modules.items())
            if n == "cyclophaser" or n.startswith("cyclophaser.")}


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "browser: drives a real Chromium against a real `streamlit run` of the "
        "calibration app. Skipped unless playwright and its Chromium are "
        "installed (pip install playwright && python -m playwright install "
        "chromium). Deselect with -m 'not browser'.",
    )
    config.addinivalue_line(
        "markers",
        "source_tree: needs the repository's own cyclophaser/ by design (it "
        "imports research code that refuses an installed copy). CI runs it in a "
        "separate step against the source, without the installed-package lock. "
        "Deselect with -m 'not source_tree'.",
    )
    if _lock_on():
        import cyclophaser
        if not _installed(cyclophaser.__file__):
            raise pytest.UsageError(
                f"{_LOCK_ENV} is set but cyclophaser was imported from "
                f"{cyclophaser.__file__}, not from site-packages")


def pytest_report_header(config):
    if _lock_on():
        import cyclophaser
        return f"{_LOCK_ENV}: cyclophaser.__file__ = {cyclophaser.__file__}"


def pytest_sessionfinish(session, exitstatus):
    if _lock_on():
        bad = {n: f for n, f in _loaded_cyclophaser_files().items()
               if f is not None and not _installed(f)}
        if bad:
            session.config._cyclophaser_lock_bad = bad
            session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter, config):
    files = _loaded_cyclophaser_files()
    terminalreporter.write_line(
        f"cyclophaser.__file__ (in session) = {files.get('cyclophaser')}")
    for n, f in getattr(config, "_cyclophaser_lock_bad", {}).items():
        terminalreporter.write_line(
            f"{_LOCK_ENV}: FAIL — {n} imported from {f}, not from site-packages",
            red=True)
