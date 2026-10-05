#!/usr/bin/env python
"""Passo 4, D3 — count warnings and errors of a sphinx-build log (read-only).

    python research/cleanup/passo4/count_build.py build_before_raw.txt

A warning is a line with "WARNING:"; an error a line with "ERROR:" or
"CRITICAL:". Writes <log stem>.json next to it.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
log = HERE / sys.argv[1]
lines = log.read_text().splitlines()
warn = [l for l in lines if "WARNING:" in l]
err = [l for l in lines if re.search(r"ERROR:|CRITICAL:", l)]
exit_line = next((l for l in reversed(lines) if l.startswith("EXIT ")), "EXIT ?")
out = dict(log=log.name, warnings=len(warn), errors=len(err), exit=exit_line, warning_lines=warn, error_lines=err)
log.with_suffix(".json").write_text(json.dumps(out, indent=1))
print(f"{log.name}: warnings {len(warn)}, errors {len(err)}, {exit_line}")
