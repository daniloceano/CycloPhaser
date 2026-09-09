#!/usr/bin/env python
"""TAREFA 5 diagnostic: final_output_check.csv for the 5 idx0_tipo=valley tracks.

READ-ONLY. Does not modify the cyclophaser package. Reuses
build_idx0_inventory.py's pipeline reimplementation (same function calls, same
order as get_periods, determine_periods.py:1073-1083) and additionally calls
cyclophaser.find_stages._incipient_plateau_rel /
cyclophaser.find_stages._incipient_plateau_boundary directly -- the exact
functions find_incipient_period itself calls at find_stages.py:969-978 -- to
report `boundary` without inferring it from the final periods column.

Run:
    ~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python \
        research/labels/diagnostics/build_final_output_check.py

Writes (unversioned, not committed):
    research/labels/diagnostics/final_output_check.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"

sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(DIAG_DIR))

from labels_core import load_real_series, read_split  # noqa: E402
from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_rel,
    _incipient_plateau_boundary,
)
from build_idx0_inventory import (  # noqa: E402
    load_config, run_pipeline_with_snapshots, leading_run_len, CONFIG_PATH,
)

TARGET_IDS = ["20180170", "20180608", "20190325", "20191014", "20206498"]

# Task 2b / labels_affected.md, transcribed literally -- only for the 4
# TRAIN tracks. The test track (20206498) is intentionally left blank: its
# label file is not opened by this script.
LABEL_FIRST_NON_INCIPIENT = {
    "20180170": "intensification",
    "20180608": "intensification",
    "20190325": "intensification",
    "20191014": "intensification",
}


def main():
    pv, gp, _ = load_config(CONFIG_PATH)

    split_doc = read_split()
    split_of = {}
    for sid in split_doc.get("train", []):
        split_of[sid] = "treino"
    for sid in split_doc.get("test", []):
        split_of[sid] = "teste"

    series = load_real_series()

    rows = []
    for sid in TARGET_IDS:
        values = series[sid]
        df, after_decay_period = run_pipeline_with_snapshots(values, pv, gp)

        decai_len = leading_run_len(after_decay_period, "decay")

        # Directly reproduce find_stages.py:969-978 (the exact calls
        # find_incipient_period makes) to get `boundary` without inferring it
        # from the final periods column.
        rel = _incipient_plateau_rel(
            df, gp.get("incipient_plateau_signal", "derivative"),
            gp.get("incipient_smooth_window", 0),
            gp.get("incipient_smooth_polyorder", 3))
        boundary = _incipient_plateau_boundary(
            rel,
            gp.get("incipient_plateau_tau", 0.20),
            gp.get("incipient_plateau_crossing", "single"),
            gp.get("incipient_plateau_k", 3),
        )

        bloco_sobrevive = "sim" if boundary < decai_len else "nao"

        final_periods = df["periods"]
        first_non_incipient_final = None
        for v in final_periods.astype(str):
            if v != "incipient":
                first_non_incipient_final = v
                break

        split = split_of.get(sid, "nao_determinado")
        label_val = LABEL_FIRST_NON_INCIPIENT.get(sid, "") if split == "treino" else ""

        rows.append({
            "track_id": sid,
            "split": split,
            "decai_comprimento_passos": decai_len,
            "incipient_boundary": int(boundary),
            "bloco_sobrevive": bloco_sobrevive,
            "primeira_fase_nao_incipiente_saida_final": first_non_incipient_final,
            "primeira_fase_nao_incipiente_rotulo": label_val,
        })

    out = pd.DataFrame(rows)
    out.to_csv(DIAG_DIR / "final_output_check.csv", index=False)
    print(out.to_string(index=False))
    print(f"\nwrote {DIAG_DIR / 'final_output_check.csv'}")


if __name__ == "__main__":
    main()
