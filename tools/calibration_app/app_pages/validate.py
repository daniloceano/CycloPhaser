"""Validate against labels page (developer key only) — configurations measured
against the manual labels of the train split.

All of it lives in validate_tab.py (the Streamlit surface) and validate_core.py
(the logic). Only in the menu with the developer key (app.py, `_developer_mode`).
Run by app.py's navigation; never run directly.
"""

import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import validate_tab  # noqa: E402

validate_tab.render()
