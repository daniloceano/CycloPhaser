"""Diagnosis only (I3 intermittent failure): on the app SERVER started by the
diagnosis plugin, log every script EXECUTION with wall-clock times.

Active only when DIAG_RUNLOG is set; that variable and this directory on
PYTHONPATH are given to the server process by diag_paged_grid_plugin.py, never
to the app's normal runs. The app's code is not touched.

Why two hooks. `ScriptRunner._run_script` is one call per rerun REQUEST, but a
request that arrives while the script is running interrupts it and the next
execution runs INSIDE the same call (a `while True` loop in streamlit 1.56 and
1.63). Timing `_run_script` alone therefore counts "interrupted + rerun" as one.
`_on_script_finished` is called once per execution, with how it ended, so:

  START <t> <thread>                 a `_run_script` call begins (= 1st execution)
  FIN <t> <thread> <event> <premature>   an execution ends; if the event is
                                     SCRIPT_STOPPED_FOR_RERUN the next execution
                                     of the same call begins at <t>
  END <t> <thread>                   the `_run_script` call returns
"""
import os
import threading
import time

_log = os.environ.get("DIAG_RUNLOG")


def _w(line: str) -> None:
    with open(_log, "a") as f:
        f.write(line + "\n")


if _log:
    try:
        from streamlit.runtime.scriptrunner import script_runner as _sr

        _orig_run = _sr.ScriptRunner._run_script
        _orig_fin = _sr.ScriptRunner._on_script_finished

        def _run(self, rerun_data):
            _w(f"START {time.time():.3f} {threading.get_ident()}")
            try:
                return _orig_run(self, rerun_data)
            finally:
                _w(f"END {time.time():.3f} {threading.get_ident()}")

        def _fin(self, ctx, event, premature_stop):
            _w(f"FIN {time.time():.3f} {threading.get_ident()} "
               f"{getattr(event, 'name', event)} {premature_stop}")
            return _orig_fin(self, ctx, event, premature_stop)

        _sr.ScriptRunner._run_script = _run
        _sr.ScriptRunner._on_script_finished = _fin
    except Exception as exc:  # pragma: no cover - diagnosis must not break the app
        _w(f"SITECUSTOMIZE-ERROR {exc!r}")
