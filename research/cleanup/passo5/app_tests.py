#!/usr/bin/env python
"""Passo 5, E2 — the app's tests: every tracked tests/*.py that imports
streamlit.testing or the code of tools/calibration_app/ (read-only).

    python research/cleanup/passo5/app_tests.py   # writes app_tests.txt next to it
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAT = re.compile(r"streamlit\.testing|tools[\"'/ ,)]*calibration_app|calibration_app")
files = [f for f in subprocess.check_output(["git", "ls-files", "tests"], cwd=ROOT, text=True).split()
         if re.match(r"tests/test_.*\.py$", f) and PAT.search((ROOT / f).read_text())]
untracked = [str(p.relative_to(ROOT)) for p in (ROOT / "tests").glob("test_*.py")
             if str(p.relative_to(ROOT)) not in files and PAT.search(p.read_text())
             and subprocess.run(["git", "ls-files", "--error-unmatch", str(p.relative_to(ROOT))], cwd=ROOT,
                                capture_output=True).returncode != 0]
files = sorted(files + untracked)
(Path(__file__).with_name("app_tests.txt")).write_text("\n".join(files) + "\n")
print(len(files), "files"); print("\n".join(files))
