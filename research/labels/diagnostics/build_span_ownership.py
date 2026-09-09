#!/usr/bin/env python
"""TAREFA 7 (rodada 3) diagnostic: span_ownership.csv for the 4 affected TRAIN tracks.

READ-ONLY. Does not modify the cyclophaser package. Reuses
build_idx0_inventory.run_pipeline_with_snapshots to get the same df the
earlier rounds used, and reads `idx_primeiro_peak_sobrevivente` directly off
df['z_peaks_valleys'] (the first surviving 'peak' position after index 0) --
not inferred from decai_comprimento_passos-1, though the two are cross-checked
and printed together.

Label values (rotulo_incipiente_start_idx / end_idx / tolerance_idx /
primeira_fase_nao_incipiente) are transcribed from
research/labels/diagnostics/labels_affected.md (already produced, itself a
literal transcription of research/labels/manual_labels.yaml), not re-read from
manual_labels.yaml here -- per the round-3 instruction not to redo
measurement. detector_incipient_boundary is transcribed from
final_output_check.csv (already produced).

Run:
    ~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python \
        research/labels/diagnostics/build_span_ownership.py

Writes (unversioned, not committed):
    research/labels/diagnostics/span_ownership.csv
"""

import sys
import csv
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(DIAG_DIR))

from labels_core import load_real_series  # noqa: E402
from build_idx0_inventory import (  # noqa: E402
    load_config, run_pipeline_with_snapshots, leading_run_len, CONFIG_PATH,
)

# Transcribed literally from labels_affected.md (itself a literal transcription
# of manual_labels.yaml, schema 3). Not re-read from the yaml in this script.
LABELS = {
    "20180170": {
        "incipient_start_idx": 0, "incipient_tolerance_idx": 5,
        "first_non_incipient_phase": "intensification",
        "first_non_incipient_start_idx": 20,
    },
    "20180608": {
        "incipient_start_idx": 0, "incipient_tolerance_idx": 5,
        "first_non_incipient_phase": "intensification",
        "first_non_incipient_start_idx": 37,
    },
    "20190325": {
        "incipient_start_idx": 0, "incipient_tolerance_idx": 5,
        "first_non_incipient_phase": "intensification",
        "first_non_incipient_start_idx": 10,
    },
    "20191014": {
        # No `phase: incipient` entry in the label -- sequence starts directly
        # at intensification, start_idx 0. incipient_tolerance_idx: not
        # determined (no incipient phase to carry a tolerance_idx).
        "incipient_start_idx": None, "incipient_tolerance_idx": None,
        "first_non_incipient_phase": "intensification",
        "first_non_incipient_start_idx": 0,
    },
}

# detector_incipient_boundary, transcribed from final_output_check.csv (already produced)
DETECTOR_BOUNDARY = {}
with open(DIAG_DIR / "final_output_check.csv") as f:
    for row in csv.DictReader(f):
        DETECTOR_BOUNDARY[row["track_id"]] = int(row["incipient_boundary"])


def main():
    pv, gp, _ = load_config(CONFIG_PATH)
    series = load_real_series()

    rows = []
    for sid in ["20180170", "20180608", "20190325", "20191014"]:
        df, after_decay_period = run_pipeline_with_snapshots(series[sid], pv, gp)
        n = len(df)

        decai_len = leading_run_len(after_decay_period, "decay")

        # First surviving 'peak' at a position > 0 (the peak that ends the
        # leading spurious decay block in find_decay_period, find_stages.py:469).
        zpv = df["z_peaks_valleys"]
        peak_positions = [i for i, v in enumerate(zpv) if v == "peak" and i > 0]
        idx_primeiro_peak = peak_positions[0] if peak_positions else None

        # Cross-check: find_decay_period marks df.loc[decay_start:decay_end]
        # INCLUSIVE of decay_end (find_stages.py:482), so the leading decay
        # run should end exactly at idx_primeiro_peak (decai_len - 1 == idx_primeiro_peak).
        cross_check_ok = (idx_primeiro_peak is not None) and (decai_len - 1 == idx_primeiro_peak)

        lab = LABELS[sid]
        rows.append({
            "track_id": sid,
            "idx_primeiro_peak_sobrevivente": idx_primeiro_peak,
            "rotulo_incipiente_start_idx": lab["incipient_start_idx"],
            "rotulo_incipiente_end_idx": lab["first_non_incipient_start_idx"],
            "rotulo_incipiente_tolerance_idx": lab["incipient_tolerance_idx"],
            "rotulo_primeira_fase_nao_incipiente": lab["first_non_incipient_phase"],
            "detector_incipient_boundary": DETECTOR_BOUNDARY[sid],
            "serie_comprimento_total": n,
        })

        print(f"{sid}: idx_primeiro_peak_sobrevivente={idx_primeiro_peak}  "
              f"decai_len-1={decai_len - 1}  cross_check_ok={cross_check_ok}  n={n}")

    fieldnames = ["track_id", "idx_primeiro_peak_sobrevivente",
                  "rotulo_incipiente_start_idx", "rotulo_incipiente_end_idx",
                  "rotulo_incipiente_tolerance_idx",
                  "rotulo_primeira_fase_nao_incipiente",
                  "detector_incipient_boundary", "serie_comprimento_total"]
    out_path = DIAG_DIR / "span_ownership.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
