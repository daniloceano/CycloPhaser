#!/usr/bin/env python
"""TAREFA 6 (rodada 3) diagnostic: z[0]/z[1] raw and filtered values for the 5
idx0_tipo=valley tracks.

READ-ONLY. Reuses build_idx0_inventory.run_pipeline_with_snapshots (same
process_vorticity/find_*_period calls, unmodified) to read df['z'] (filtered,
the series that feeds extrema detection) and df['z_unfil'] (raw vorticity) at
indices 0 and 1.

Run:
    ~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python \
        research/labels/diagnostics/build_task6_values.py
"""

import sys
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(DIAG_DIR))

from labels_core import load_real_series
from build_idx0_inventory import load_config, run_pipeline_with_snapshots, CONFIG_PATH

pv, gp, _ = load_config(CONFIG_PATH)
series = load_real_series()

targets = ["20180170", "20180608", "20190325", "20191014", "20206498"]
for sid in targets:
    df, _ = run_pipeline_with_snapshots(series[sid], pv, gp)
    z0, z1 = df["z"].iloc[0], df["z"].iloc[1]
    zu0, zu1 = df["z_unfil"].iloc[0], df["z_unfil"].iloc[1]
    print(f"{sid}: z[0]={z0!r} z[1]={z1!r} |dz_filt|={abs(z1-z0)!r}   "
          f"z_unfil[0]={zu0!r} z_unfil[1]={zu1!r} |dz_bruta|={abs(zu1-zu0)!r}")
