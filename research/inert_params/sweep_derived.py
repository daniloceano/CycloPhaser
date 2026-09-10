"""FRENTE F(iii) audit — DERIVED enumeration, not hand-written.

sweep_inertia.py's SWEEP_PLAN was a hand-written list of (parameter,
base_config) pairs. A hand-written list has no way to make an omission
visible: it was missing (use_smoothing_twice, base where use_smoothing=False)
entirely, which is exactly the same class of gap as the two guards already
signalled in app.py (cutoff_low/cutoff_high/boundary_padding under
use_filter=False; savgol_poly under use_smoothing=False).

This script computes the FULL cartesian product of every parameter in
PARAMS x every base_config in BASE_CONFIGS, and classifies EVERY pair into
exactly one status -- so an un-run pair is a visible row, not a silent gap:

  TESTED_CURATED  -- was already in sweep_inertia.SWEEP_PLAN
  TESTED_NEW      -- newly added by the derived rule below, not previously run
  SKIPPED_REDUNDANT -- provably identical to (parameter, "default"): the
                       parameter is pv-kind (consumed only by
                       process_vorticity, which takes no phase kwargs at
                       all) and this base_config only overrides phase-kind
                       keys, so pv_kwargs are byte-identical to "default".
                       This is a proof, not a guess -- process_vorticity's
                       signature does not accept threshold_*/mature_*/
                       incipient_*/prominence/distance/decay_tail_* kwargs.
  SKIPPED_DEFERRED -- NOT provably redundant (this base_config changes pv
                      kwargs, which change the vorticity signal fed into
                      get_periods, or changes an unrelated phase kwarg while
                      the parameter is phase-kind) but not run this pass,
                      for combinatorial cost. Listed explicitly, not hidden.

Derived inclusion rule (the ONLY hand-written part is which base_configs
change which kind of kwarg -- BASE_CONFIGS itself, already in
sweep_inertia.py; membership below is computed from it, not chosen per
parameter):

  base == "default"                                -> TESTED (baseline)
  kind == "pv"    and BASE_CONFIGS[base]["pv"]      -> TESTED (same-kind
                                                        mode switch: the
                                                        exact class of the
                                                        missed pair)
  kind == "pv"    and not BASE_CONFIGS[base]["pv"]  -> SKIPPED_REDUNDANT
  kind == "phase" and BASE_CONFIGS[base]["pv"]      -> TESTED (generalizes
                                                        the same risk class
                                                        to phase-kind params:
                                                        a pv-mode switch
                                                        could change the
                                                        vorticity signal a
                                                        phase-kind parameter
                                                        is evaluated against)
  kind == "phase" and not BASE_CONFIGS[base]["pv"]
      and (parameter, base) in original SWEEP_PLAN  -> TESTED_CURATED
  kind == "phase" and not BASE_CONFIGS[base]["pv"]
      and (parameter, base) not in SWEEP_PLAN        -> SKIPPED_DEFERRED

Run: python research/inert_params/sweep_derived.py
Output: research/inert_params/inertia_matrix_full.csv (ALL pairs, every
status), research/inert_params/sweep_derived_summary.txt.
"""
from __future__ import annotations

import csv
import sys
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sweep_inertia import (  # noqa: E402
    BASE_CONFIGS, PARAMS, SWEEP_PLAN, KNOWN_INERT_CASES,
    sweep_one, TRACKS,
)

OUT_DIR = Path(__file__).resolve().parent

CURATED = {(p, b) for p, bases in SWEEP_PLAN for b in bases}

ALL_PAIRS = []
for param_name, (kind, kwarg, values) in PARAMS.items():
    for base_name in BASE_CONFIGS:
        ALL_PAIRS.append((param_name, base_name, kind))


def classify(param_name: str, base_name: str, kind: str) -> str:
    if base_name == "default":
        return "TESTED_CURATED" if (param_name, base_name) in CURATED else "TESTED_NEW"
    base_pv = BASE_CONFIGS[base_name]["pv"]
    if kind == "pv":
        if base_pv:
            return "TESTED_CURATED" if (param_name, base_name) in CURATED else "TESTED_NEW"
        return "SKIPPED_REDUNDANT"
    else:  # kind == "phase"
        if base_pv:
            return "TESTED_CURATED" if (param_name, base_name) in CURATED else "TESTED_NEW"
        if (param_name, base_name) in CURATED:
            return "TESTED_CURATED"
        return "SKIPPED_DEFERRED"


def main():
    rows = []
    n_by_status = {}
    for param_name, base_name, kind in ALL_PAIRS:
        status = classify(param_name, base_name, kind)
        n_by_status[status] = n_by_status.get(status, 0) + 1
        row = {
            "parameter": param_name, "base_config": base_name, "kind": kind,
            "status": status,
        }
        if status in ("TESTED_CURATED", "TESTED_NEW"):
            print(f"[{status}] sweeping {param_name!r} under base={base_name!r} "
                  f"({len(PARAMS[param_name][2])} values x {len(TRACKS)} tracks)...",
                  flush=True)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = sweep_one(param_name, base_name)
            row.update(result)
            if result["inert"] is None:
                verdict = "UNEVALUABLE"
            else:
                verdict = "INERT" if result["inert"] else "not inert"
            print(f"  -> {verdict} (tracks changed: {result['n_tracks_changed']}/{len(TRACKS)})")
        else:
            row.update({"kwarg": PARAMS[param_name][1], "n_values_swept": None,
                        "n_skipped_observations": None, "n_unevaluable_tracks": None,
                        "inert": None, "n_tracks_changed": None, "changed_tracks": [],
                        "n_changed_observations": None})
        rows.append(row)

    csv_path = OUT_DIR / "inertia_matrix_full.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["parameter", "base_config", "kind", "status", "kwarg",
                          "n_values_swept", "inert", "n_tracks_changed",
                          "n_changed_observations", "n_skipped_observations",
                          "n_unevaluable_tracks", "changed_tracks"])
        for r in rows:
            writer.writerow([r["parameter"], r["base_config"], r["kind"], r["status"],
                              r["kwarg"], r["n_values_swept"], r["inert"],
                              r["n_tracks_changed"], r["n_changed_observations"],
                              r["n_skipped_observations"], r["n_unevaluable_tracks"],
                              ";".join(r["changed_tracks"]) if r["changed_tracks"] else ""])
    print(f"\nwrote {csv_path}")

    tested_rows = [r for r in rows if r["status"] in ("TESTED_CURATED", "TESTED_NEW")]
    lookup = {(r["parameter"], r["base_config"]): r["inert"] for r in tested_rows}
    gate_a_failures = []
    for param_name, base_name in KNOWN_INERT_CASES:
        found_inert = lookup.get((param_name, base_name))
        if found_inert is not True:
            gate_a_failures.append((param_name, base_name, found_inert))

    new_inert = [r for r in tested_rows
                 if r["status"] == "TESTED_NEW" and r["inert"] is True]
    new_not_inert = [r for r in tested_rows
                     if r["status"] == "TESTED_NEW" and r["inert"] is False]
    deferred = [r for r in rows if r["status"] == "SKIPPED_DEFERRED"]

    summary_path = OUT_DIR / "sweep_derived_summary.txt"
    with open(summary_path, "w") as f:
        f.write(f"Full cartesian enumeration: {len(ALL_PAIRS)} (parameter, base_config) "
                f"pairs ({len(PARAMS)} parameters x {len(BASE_CONFIGS)} base configs).\n\n")
        f.write("Status counts:\n")
        for status, n in sorted(n_by_status.items()):
            f.write(f"  {status:18s}: {n}\n")
        f.write(f"\nGATE (a) — known-inert self-test on the full re-run:\n")
        if gate_a_failures:
            f.write("  FAILED. The sweep did not detect inertia for:\n")
            for p, b, found in gate_a_failures:
                f.write(f"    {p} / {b}: found inert={found}\n")
        else:
            f.write(f"  PASSED — all {len(KNOWN_INERT_CASES)} known (parameter, base) "
                    "pairs correctly flagged inert.\n")

        f.write(f"\nTESTED_NEW pairs found INERT (candidate new POR DESENHO cases, "
                f"{len(new_inert)}):\n")
        for r in new_inert:
            f.write(f"  {r['parameter']:32s} / {r['base_config']:24s} -> INERT "
                    f"(changed 0/{len(TRACKS)}, unevaluable {r['n_unevaluable_tracks']}/{len(TRACKS)})\n")

        f.write(f"\nTESTED_NEW pairs found NOT inert ({len(new_not_inert)}):\n")
        for r in new_not_inert:
            f.write(f"  {r['parameter']:32s} / {r['base_config']:24s} -> not inert "
                    f"(changed {r['n_tracks_changed']}/{len(TRACKS)})\n")

        f.write(f"\nSKIPPED_DEFERRED pairs ({len(deferred)}) — phase-kind parameter, "
                f"phase-only base_config, not in the original curated plan; NOT run this "
                f"pass for combinatorial cost, listed here rather than absent:\n")
        for r in deferred:
            f.write(f"  {r['parameter']:32s} / {r['base_config']:24s}\n")

        f.write(f"\nFull TESTED matrix:\n")
        for r in tested_rows:
            if r["inert"] is None:
                verdict = "UNEVALUABLE"
            else:
                verdict = "INERT" if r["inert"] else "not inert"
            f.write(f"  [{r['status']:14s}] {r['parameter']:32s} / {r['base_config']:24s} -> "
                    f"{verdict:11s} (changed {r['n_tracks_changed']}/{len(TRACKS)} tracks, "
                    f"unevaluable {r['n_unevaluable_tracks']}/{len(TRACKS)})\n")
    print(f"wrote {summary_path}")
    print(open(summary_path).read())


if __name__ == "__main__":
    main()
