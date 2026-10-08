"""Pending item for I2: a bad-case mark is lost on Grid -> Inspector -> Grid.

    python research/app_redesign/i1/check_badmark_loss.py <checkout root>

One checkout per process: two app checkouts in one process clash on the
imports of their sibling modules.

For each checkout given, AppTest (public API) on its tools/calibration_app/app.py:
mark the first cyclone as bad in Grid, switch Display mode to Inspector, then back
to Grid, and print whether the mark survived each step. Run on a develop worktree
and on the branch to show the loss predates I1 (the checkboxes are drawn only in
Grid, so Streamlit cleans their state up while Inspector is shown).
"""
import subprocess
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

for root in map(Path, sys.argv[1:]):
    root = root.resolve()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                          capture_output=True, text=True).stdout.strip()
    at = AppTest.from_file(str(root / "tools/calibration_app/app.py"), default_timeout=300)
    at.run()
    mark = next(cb.key for cb in at.checkbox if cb.key and cb.key.startswith("badcase__"))
    at.checkbox(key=mark).check()
    at.run()
    marked = mark in at.session_state and at.session_state[mark] is True
    next(r for r in at.radio if r.key == "view_mode").set_value("Inspector")
    at.run()
    in_inspector = mark in at.session_state and at.session_state[mark] is True
    next(r for r in at.radio if r.key == "view_mode").set_value("Grid")
    at.run()
    back = at.checkbox(key=mark).value
    print(f"{root.name} @ {head}: marked in Grid={marked} | still marked in "
          f"Inspector={in_inspector} | still marked back in Grid={back}")
