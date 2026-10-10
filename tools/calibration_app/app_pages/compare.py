"""Compare page — several configurations over the tracks loaded in Calibrate.

All of it lives in compare_tab.py (the Streamlit surface) and compare_core.py
(the logic). Run by app.py's navigation; never run directly.
"""

import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import compare_tab  # noqa: E402

compare_tab.render()
