"""The frozen cyclophaser 2.0.0 defaults, for tests (item 31).

Item 31 moved the package defaults to params-15. Tests whose assertions were
MEASURED under the 2.0.0 defaults (reference counts, per-track behaviours, the
develop-v2.1 cross-version baseline) now pass those defaults explicitly, so
what they assert is unchanged. The values are read from the frozen table
`research/labels/defaults_2.0.0.json` — never typed here.

Tests that are about the CURRENT package defaults do not use this module.
"""

from __future__ import annotations

import json
from pathlib import Path

_TABLE = json.loads((Path(__file__).resolve().parent.parent / "research" / "labels"
                     / "defaults_2.0.0.json").read_text())

#: process_vorticity keyword arguments of 2.0.0
FILTER_2_0_0: dict = dict(_TABLE["filter_params"])
#: get_periods keyword arguments of 2.0.0
PHASE_2_0_0: dict = dict(_TABLE["phase_params"])
#: the three that shape the working frame (layer_inspector.build_working_frame)
FRAME_2_0_0: dict = {k: PHASE_2_0_0[k]
                     for k in ("prominence", "prominence_relative", "reclassify_index0")}
#: what get_periods forwards to the stage functions (layer_inspector.build_args_periods)
ARGS_2_0_0: dict = {k: v for k, v in PHASE_2_0_0.items() if k not in FRAME_2_0_0}
#: determine_periods keyword arguments of 2.0.0 (filter + phase)
ALL_2_0_0: dict = {**FILTER_2_0_0, **PHASE_2_0_0}
