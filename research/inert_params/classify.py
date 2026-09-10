"""FRENTE F(iii) closeout, PASSO 3 — add a `category` column to the inertia
matrices. Three categories, defined in DATA_DEPENDENT_findings.md:

  POR_DESENHO          -- a citable line skips the parameter on this branch.
  DEPENDENTE_DOS_DADOS  -- parameter is read unconditionally; the branch's
                           result is flat because of THIS dataset, not the
                           code. No UI caption.
  INEXPLICADA           -- neither: read, real branch, no data-level story
                           traced yet. Backlog item, no UI caption.

CATEGORY below is a reviewed, hand-authored mapping from (parameter,
base_config) -> category, for every row measured INERT (True) in either
inertia_matrix.csv or inertia_matrix_full.csv. It is intentionally NOT
auto-derived -- classification requires citing an actual code line or an
actual dataset-level explanation, which cannot be inferred from the
measurement alone (that is the whole point of gate (b)). Rows not in this
mapping are left with an empty category and printed as a warning, so an
unclassified INERT row is visible, not silently blank.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

CATEGORY: dict[tuple[str, str], str] = {
    # --- already signalled in the UI before this front ---
    ("thr_mat_len", "mature_amplitude"): "POR_DESENHO",
    ("thr_mat_dist", "mature_amplitude"): "POR_DESENHO",
    ("thr_inc_len", "plateau_single_derivative"): "POR_DESENHO",
    ("mature_amplitude_fraction", "mature_derivative"): "POR_DESENHO",
    ("incipient_plateau_tau", "default"): "POR_DESENHO",
    ("incipient_plateau_signal", "default"): "POR_DESENHO",
    ("incipient_plateau_crossing", "default"): "POR_DESENHO",
    ("incipient_plateau_k", "default"): "POR_DESENHO",
    ("incipient_plateau_k", "plateau_single_derivative"): "POR_DESENHO",
    ("incipient_plateau_k", "plateau_single_vorticity"): "POR_DESENHO",
    ("incipient_smooth_window", "default"): "POR_DESENHO",
    ("incipient_smooth_window", "plateau_single_derivative"): "POR_DESENHO",
    ("incipient_smooth_polyorder", "default"): "POR_DESENHO",
    ("incipient_smooth_polyorder", "plateau_single_derivative"): "POR_DESENHO",
    # window pinned at its own UI default (0) -- a real, separate design
    # gate (find_stages.py probe smoother is skipped when window<=0), not
    # the same claim as "polyorder is inert whenever signal=derivative".
    ("incipient_smooth_polyorder", "plateau_single_vorticity"): "POR_DESENHO",

    # --- signalled THIS front (PASSO 0) ---
    ("cutoff_low", "nofilter"): "POR_DESENHO",
    ("cutoff_high", "nofilter"): "POR_DESENHO",
    ("boundary_padding", "nofilter"): "POR_DESENHO",
    ("savgol_poly", "nosmoothing"): "POR_DESENHO",

    # --- reclassified THIS closeout (PASSO 3), moved out of INEXPLICADA ---
    ("thr_int_gap", "default"): "DEPENDENTE_DOS_DADOS",
    ("incipient_plateau_crossing", "plateau_single_derivative"): "DEPENDENTE_DOS_DADOS",

    # --- resolved during the original measurement (not inert once the
    #     precondition -- prominence filtering -- is actually met); this
    #     row is the SUPERSEDED base config kept for audit trail, not a
    #     live finding. See REPORT_inertia_sweep.md, "Methodology
    #     corrections". prominence filtering off is itself a citable
    #     precondition (find_stages.py, the orphan-peak compensation the
    #     parameter's docstring describes never triggers without it).
    ("decay_tail_amplitude_fraction", "decay_tail_on"): "POR_DESENHO",

    # --- audited THIS closeout (PASSO 1), the reported gap and its sibling ---
    ("sm2_val", "nosmoothing"): "POR_DESENHO",
    ("replace_endpoints", "nofilter"): "POR_DESENHO",

    # --- derived-enumeration re-run (PASSO 1): every other TESTED_NEW row
    #     that came back INERT is the SAME already-known design gate,
    #     confirmed true under an additional pv-mode base that doesn't
    #     touch the controlling switch -- not a new, distinct UI case. ---

    # thr_int_gap: same DEPENDENTE_DOS_DADOS story as /default (no track
    # in this set ever produces >1 intensification block), confirmed
    # under every pv-mode base too.
    ("thr_int_gap", "nofilter"): "DEPENDENTE_DOS_DADOS",
    ("thr_int_gap", "nosmoothing"): "DEPENDENTE_DOS_DADOS",
    ("thr_int_gap", "manual_sm"): "DEPENDENTE_DOS_DADOS",
    ("thr_int_gap", "manual_sm2"): "DEPENDENTE_DOS_DADOS",

    # mature_amplitude_fraction: these 5 bases all leave mature_method at
    # its PHASE_DEFAULTS value ("derivative") -- identical controlling
    # condition to the already-signalled /mature_derivative case.
    ("mature_amplitude_fraction", "default"): "POR_DESENHO",
    ("mature_amplitude_fraction", "nofilter"): "POR_DESENHO",
    ("mature_amplitude_fraction", "nosmoothing"): "POR_DESENHO",
    ("mature_amplitude_fraction", "manual_sm"): "POR_DESENHO",
    ("mature_amplitude_fraction", "manual_sm2"): "POR_DESENHO",

    # incipient_plateau_* / incipient_smooth_*: these 4 bases (nofilter,
    # nosmoothing, manual_sm, manual_sm2) all leave incipient_method at its
    # PHASE_DEFAULTS value ("geometric") -- identical controlling condition
    # to the already-signalled /default case (whole plateau block
    # disabled).
    ("incipient_plateau_tau", "nofilter"): "POR_DESENHO",
    ("incipient_plateau_tau", "nosmoothing"): "POR_DESENHO",
    ("incipient_plateau_tau", "manual_sm"): "POR_DESENHO",
    ("incipient_plateau_tau", "manual_sm2"): "POR_DESENHO",
    ("incipient_plateau_signal", "nofilter"): "POR_DESENHO",
    ("incipient_plateau_signal", "nosmoothing"): "POR_DESENHO",
    ("incipient_plateau_signal", "manual_sm"): "POR_DESENHO",
    ("incipient_plateau_signal", "manual_sm2"): "POR_DESENHO",
    ("incipient_plateau_crossing", "nofilter"): "POR_DESENHO",
    ("incipient_plateau_crossing", "nosmoothing"): "POR_DESENHO",
    ("incipient_plateau_crossing", "manual_sm"): "POR_DESENHO",
    ("incipient_plateau_crossing", "manual_sm2"): "POR_DESENHO",
    ("incipient_plateau_k", "nofilter"): "POR_DESENHO",
    ("incipient_plateau_k", "nosmoothing"): "POR_DESENHO",
    ("incipient_plateau_k", "manual_sm"): "POR_DESENHO",
    ("incipient_plateau_k", "manual_sm2"): "POR_DESENHO",
    ("incipient_smooth_window", "nofilter"): "POR_DESENHO",
    ("incipient_smooth_window", "nosmoothing"): "POR_DESENHO",
    ("incipient_smooth_window", "manual_sm"): "POR_DESENHO",
    ("incipient_smooth_window", "manual_sm2"): "POR_DESENHO",
    ("incipient_smooth_polyorder", "nofilter"): "POR_DESENHO",
    ("incipient_smooth_polyorder", "nosmoothing"): "POR_DESENHO",
    ("incipient_smooth_polyorder", "manual_sm"): "POR_DESENHO",
    ("incipient_smooth_polyorder", "manual_sm2"): "POR_DESENHO",

    # decay_tail_amplitude_fraction: same "prominence filtering off, orphan
    # -peak precondition never triggers" story as /decay_tail_on, confirmed
    # under every pv-mode base too -- not a new condition.
    ("decay_tail_amplitude_fraction", "default"): "POR_DESENHO",
    ("decay_tail_amplitude_fraction", "nofilter"): "POR_DESENHO",
    ("decay_tail_amplitude_fraction", "nosmoothing"): "POR_DESENHO",
    ("decay_tail_amplitude_fraction", "manual_sm"): "POR_DESENHO",
    ("decay_tail_amplitude_fraction", "manual_sm2"): "POR_DESENHO",
}


def annotate(csv_name: str) -> None:
    path = OUT_DIR / csv_name
    if not path.exists():
        print(f"skip {csv_name}: not found")
        return
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if "category" not in fieldnames:
        fieldnames = list(fieldnames) + ["category"]
    unclassified = []
    for r in rows:
        inert = r.get("inert")
        if inert == "True":
            key = (r["parameter"], r["base_config"])
            cat = CATEGORY.get(key, "")
            r["category"] = cat
            if not cat:
                unclassified.append(key)
        else:
            r["category"] = ""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"annotated {csv_name} ({len(rows)} rows)")
    if unclassified:
        print(f"  ** UNCLASSIFIED INERT ROWS ({len(unclassified)}) -- visible, not silently blank:")
        for p, b in unclassified:
            print(f"     {p} / {b}")


if __name__ == "__main__":
    annotate("inertia_matrix.csv")
    annotate("inertia_matrix_full.csv")
