#!/usr/bin/env python
"""Front A' step 1a gate: field-by-field comparison of regenerated vs versioned.

Deliberately NOT a whole-file sha256: a byte comparison would fail on a float
repr change or a column reorder that carries no measurement content, and would
pass a file that is byte-identical for the wrong reason. Every field is typed
and compared under the criterion declared in the commissioning brief BEFORE any
measurement was taken:

  * categorical and integer fields : identical
  * index-0 prominence             : exactly 0.0 on all 5 valley tracks
  * every other float              : |relative error| <= 1e-9
  * fix_eval                       : 8/17 and 14/16 exact

Run:
    python compare_1a.py --expected <dir> --actual <dir> --eval-log <file>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REL_TOL = 1e-9

# Columns that must match exactly (categorical or integer), per artifact.
EXACT_COLS = {
    "idx0_inventory.csv": ["track_id", "split", "idx0_tipo", "sinal_dz_filtrada",
                           "sinal_dz_bruta", "decai_no_idx0",
                           "decai_comprimento_passos"],
    "idx0_final_stage.csv": ["track_id", "periods_idx0_final",
                             "leading_incipient_len_final",
                             "first_non_incipient_phase_final"],
    "idx0b_prominence.csv": ["track_id", "prominence_relative_threshold_cfg",
                             "would_survive_relative_filter_on_its_own_merit",
                             "steps_to_next_surviving_extremum"],
    "final_output_check.csv": ["track_id", "split", "decai_comprimento_passos",
                               "incipient_boundary", "bloco_sobrevive",
                               "primeira_fase_nao_incipiente_saida_final",
                               "primeira_fase_nao_incipiente_rotulo"],
}
FLOAT_COLS = {
    "idx0_inventory.csv": ["decai_fracao_serie", "decai_fracao_amplitude"],
    "idx0_final_stage.csv": [],
    "idx0b_prominence.csv": ["idx0_prominence_computed_diagnostically",
                             "max_interior_prominence_z"],
    "final_output_check.csv": [],
}

failures: list[str] = []
checks = 0


def fail(msg: str) -> None:
    failures.append(msg)


def compare_csv(name: str, exp_p: Path, act_p: Path) -> None:
    global checks
    exp = pd.read_csv(exp_p, keep_default_na=False, dtype=str)
    act = pd.read_csv(act_p, keep_default_na=False, dtype=str)

    if list(exp.columns) != list(act.columns):
        fail(f"{name}: column set differs\n  expected {list(exp.columns)}\n  actual   {list(act.columns)}")
        return
    if len(exp) != len(act):
        fail(f"{name}: row count {len(exp)} -> {len(act)}")
        return

    key = "track_id"
    exp = exp.sort_values(key).reset_index(drop=True)
    act = act.sort_values(key).reset_index(drop=True)
    if not (exp[key] == act[key]).all():
        fail(f"{name}: track_id set differs")
        return

    for col in EXACT_COLS[name]:
        if col not in exp.columns:
            fail(f"{name}: declared exact column {col!r} absent")
            continue
        for i in range(len(exp)):
            checks += 1
            if exp.at[i, col] != act.at[i, col]:
                fail(f"{name}[{exp.at[i, key]}].{col}: {exp.at[i, col]!r} -> {act.at[i, col]!r}")

    for col in FLOAT_COLS[name]:
        if col not in exp.columns:
            fail(f"{name}: declared float column {col!r} absent")
            continue
        for i in range(len(exp)):
            checks += 1
            e_raw, a_raw = exp.at[i, col], act.at[i, col]
            if e_raw == "" or a_raw == "":
                if e_raw != a_raw:
                    fail(f"{name}[{exp.at[i, key]}].{col}: blank mismatch {e_raw!r} -> {a_raw!r}")
                continue
            e, a = float(e_raw), float(a_raw)
            rel = abs(a - e) / abs(e) if e != 0 else abs(a - e)
            if rel > REL_TOL:
                fail(f"{name}[{exp.at[i, key]}].{col}: {e!r} -> {a!r} (rel {rel:.3e})")


def check_idx0_prominence_zero(act_p: Path) -> None:
    """The brief's own criterion: prominence at index 0 is EXACTLY 0.0, all 5."""
    global checks
    df = pd.read_csv(act_p)
    col = "idx0_prominence_computed_diagnostically"
    if len(df) != 5:
        fail(f"idx0b_prominence.csv: expected 5 valley tracks, got {len(df)}")
    for _, r in df.iterrows():
        checks += 1
        v = float(r[col])
        if v != 0.0:
            fail(f"idx0b_prominence[{r['track_id']}]: prominence {v!r} is not exactly 0.0")


def compare_state_json(exp_p: Path, act_p: Path) -> None:
    global checks
    exp = json.loads(exp_p.read_text())
    act = json.loads(act_p.read_text())

    for block in ("config_pv", "config_gp"):
        checks += 1
        if exp[block] != act[block]:
            ek, ak = set(exp[block]), set(act[block])
            fail(f"fix_state_before.json/{block} differs; "
                 f"only-expected={sorted(ek - ak)} only-actual={sorted(ak - ek)}; "
                 f"value diffs={[k for k in ek & ak if exp[block][k] != act[block][k]]}")

    et, at = exp["tracks"], act["tracks"]
    if set(et) != set(at):
        fail(f"fix_state_before.json: track set differs "
             f"(only-expected={sorted(set(et) - set(at))}, only-actual={sorted(set(at) - set(et))})")
        return
    for sid in sorted(et):
        for field in ("n_steps", "periods", "z_peaks_valleys", "source", "error"):
            if field in et[sid] or field in at[sid]:
                checks += 1
                if et[sid].get(field) != at[sid].get(field):
                    fail(f"fix_state_before.json[{sid}].{field} differs")


def compare_eval(exp_p: Path, act_log: Path) -> None:
    """Compare the report body, and separately assert the two declared counts."""
    global checks
    exp_txt = exp_p.read_text()
    raw = act_log.read_text()
    # Drop this front's wrapper provenance block; keep the report verbatim.
    marker = "Incipient boundary vs manual labels"
    idx = raw.index(marker)
    start = raw.rindex("=" * 74, 0, idx)
    act_txt = raw[start:]

    exp_lines = [l.rstrip() for l in exp_txt.strip().splitlines()]
    act_lines = [l.rstrip() for l in act_txt.strip().splitlines()]
    checks += 1
    if exp_lines != act_lines:
        n = max(len(exp_lines), len(act_lines))
        for i in range(n):
            e = exp_lines[i] if i < len(exp_lines) else "<absent>"
            a = act_lines[i] if i < len(act_lines) else "<absent>"
            if e != a:
                fail(f"fix_eval line {i + 1}:\n  expected {e!r}\n  actual   {a!r}")

    # Declared criterion, asserted independently of the line diff.
    m = re.search(r"boundary labels\s+17\s+hit within margin\s+(\d+)", act_txt)
    checks += 1
    if not m or m.group(1) != "8":
        fail(f"fix_eval: TRAIN-real incipient hit is {m.group(1) if m else '<not found>'}, declared 8 of 17")
    m2 = re.search(r"label says none:\s+16, detector agreed on\s+(\d+)", act_txt)
    checks += 1
    if not m2 or m2.group(1) != "14":
        fail(f"fix_eval: TRAIN-real refusal agreement is {m2.group(1) if m2 else '<not found>'}, declared 14 of 16")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected", required=True, type=Path)
    ap.add_argument("--actual", required=True, type=Path)
    ap.add_argument("--eval-log", required=True, type=Path)
    a = ap.parse_args()

    for name in ("idx0_inventory.csv", "idx0_final_stage.csv",
                 "idx0b_prominence.csv", "final_output_check.csv"):
        compare_csv(name, a.expected / name, a.actual / name)
    check_idx0_prominence_zero(a.actual / "idx0b_prominence.csv")
    compare_state_json(a.expected / "fix_state_before.json",
                       a.actual / "fix_state_before.json")
    compare_eval(a.expected / "fix_eval_before.txt", a.eval_log)

    print(f"fields compared: {checks}")
    if failures:
        print(f"\nSTEP 1a: FAIL — {len(failures)} divergence(s)\n")
        for f in failures:
            print("  - " + f)
        return 1
    print("\nSTEP 1a: PASS — every compared field within the declared criterion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
