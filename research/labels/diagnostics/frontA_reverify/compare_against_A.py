#!/usr/bin/env python
"""Front A' steps 1b/2: per-track diff of a tip census against Front A's artifacts.

Reports every field that differs, per track, between a census produced by
census_tip.py and the artifacts committed with Front A at 6060c6d. This is a
DIAGNOSTIC, not a gate: no pass/fail verdict is emitted, only the differences.

Run:
    python compare_against_A.py --a-dir <dir with A's csvs> \
        --tip-prefix <outputs/<tag>> --label <name>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

INV_COLS = ["split", "idx0_tipo", "sinal_dz_filtrada", "sinal_dz_bruta",
            "decai_no_idx0", "decai_comprimento_passos", "decai_fracao_serie",
            "decai_fracao_amplitude"]
PROM_COLS = ["idx0_prominence_computed_diagnostically", "max_interior_prominence_z",
             "prominence_relative_threshold_cfg",
             "would_survive_relative_filter_on_its_own_merit",
             "steps_to_next_surviving_extremum"]
FINAL_COLS = ["periods_idx0_final", "leading_incipient_len_final",
              "first_non_incipient_phase_final"]


def diff_table(name, a_p: Path, t_p: Path, cols):
    a = pd.read_csv(a_p, keep_default_na=False, dtype=str).set_index("track_id")
    t = pd.read_csv(t_p, keep_default_na=False, dtype=str).set_index("track_id")
    a.index = a.index.astype(str)
    t.index = t.index.astype(str)

    out = []
    only_a = sorted(set(a.index) - set(t.index))
    only_t = sorted(set(t.index) - set(a.index))
    if only_a or only_t:
        out.append(f"  track set differs: only-in-A={only_a} only-in-tip={only_t}")
    for sid in sorted(set(a.index) & set(t.index)):
        for c in cols:
            if c not in a.columns or c not in t.columns:
                continue
            av, tv = a.at[sid, c], t.at[sid, c]
            if av != tv:
                out.append(f"  {sid}.{c}: A={av!r} -> tip={tv!r}")
    print(f"\n--- {name} ---")
    if out:
        print(f"  {len(out)} difference(s):")
        for line in out:
            print(line)
    else:
        print(f"  no differences across {len(set(a.index) & set(t.index))} track(s) "
              f"x {len([c for c in cols if c in a.columns])} field(s)")
    return len(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a-dir", required=True, type=Path)
    ap.add_argument("--tip-prefix", required=True, type=Path)
    ap.add_argument("--label", required=True)
    a = ap.parse_args()

    print("=" * 74)
    print(f"PER-TRACK DIFF vs FRONT A (6060c6d artifacts) — {a.label}")
    print("=" * 74)

    n = 0
    n += diff_table("idx0_inventory (M: idx0 type + leading decay block)",
                    a.a_dir / "idx0_inventory.csv",
                    Path(str(a.tip_prefix) + "_idx0_inventory.csv"), INV_COLS)
    n += diff_table("idx0b_prominence (M: prominence of the index-0 extremum)",
                    a.a_dir / "idx0b_prominence.csv",
                    Path(str(a.tip_prefix) + "_idx0b_prominence.csv"), PROM_COLS)
    n += diff_table("idx0_final_stage (final-output cross-check, all 51)",
                    a.a_dir / "idx0_final_stage.csv",
                    Path(str(a.tip_prefix) + "_idx0_final_stage.csv"), FINAL_COLS)

    print(f"\nTOTAL differences vs A: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
