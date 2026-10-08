"""Benchmark page — N configurations over the same cyclones, aligned in columns.

All of it lives in benchmark_tab.py (the Streamlit surface) and benchmark_core.py
(the logic). Run by app.py's navigation; never run directly.
"""

import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import benchmark_tab  # noqa: E402

benchmark_tab.render()
