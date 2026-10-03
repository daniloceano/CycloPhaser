"""pytest plugin: record which cyclophaser the test session actually used.

Loaded with `-p cp_import_probe` from a directory that holds only this file
(on PYTHONPATH). It changes nothing in the run. At collection end and at session
end it reads `sys.modules` — the modules the tests really imported, not a fresh
import — and writes every `cyclophaser*` module's `__file__`, the installed
distribution's version and the first sys.path entries to $CP_PROBE_OUT (JSON),
and prints one line into the pytest output.
"""

import json
import os
import sys


def _snapshot():
    mods = {n: getattr(m, "__file__", None) for n, m in sorted(sys.modules.items())
            if n == "cyclophaser" or n.startswith("cyclophaser.")}
    try:
        import importlib.metadata as md
        dist = md.distribution("cyclophaser")
        version, dist_path = dist.version, str(dist.locate_file(""))
    except Exception as e:  # noqa: BLE001
        version, dist_path = f"<{e!r}>", None
    return {"modules": mods, "dist_version": version, "dist_location": dist_path,
            "sys_path_head": sys.path[:6], "cwd": os.getcwd()}


_state = {}


def pytest_collection_finish(session):
    _state["at_collection_end"] = _snapshot()


def pytest_sessionfinish(session, exitstatus):
    _state["at_session_end"] = _snapshot()
    _state["exitstatus"] = int(exitstatus)
    out = os.environ.get("CP_PROBE_OUT")
    if out:
        with open(out, "w") as fh:
            json.dump(_state, fh, indent=1)


def pytest_terminal_summary(terminalreporter):
    snap = _state.get("at_session_end") or _snapshot()
    terminalreporter.write_line(
        f"CP_PROBE cyclophaser.__file__ = {snap['modules'].get('cyclophaser')}")
