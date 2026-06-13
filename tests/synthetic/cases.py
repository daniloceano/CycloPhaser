"""Synthetic lifecycle test cases for CycloPhaser.

Each entry in CASES describes one synthetic scenario:
  'segments'            — segment list passed to make_lifecycle_series
  'kwargs'              — extra kwargs for make_lifecycle_series (noise, seed,
                          start_value)
  'series'              — pre-built pd.Series (generated at import time)
  'expected_phases'     — ordered list of normalized phase names (no numeric
                          suffixes); absent for 'observational'/'property_*'
                          test modes
  'expected_starts_idx' — dict {phase_name: expected_start_step_in_series}
                          Keys match the FULL phase names returned by
                          periods_to_dict (e.g. 'intensification 2', 'decay 2')
                          so that all phases in two-cycle cases can be checked.
                          Derived from segment boundary positions (ground truth).
                          Absent for observational / property cases.
  'tolerance'           — max allowed deviation in timesteps for start-timing
                          checks.  6 timesteps = 18 h at 3 h resolution.
  'test_mode'           — 'standard' (default): assert sequence + timing.
                          'observational': run and log detected sequence only,
                          no assertions.
                          'property_no_mature': log whether 'mature' appears in
                          the detected sequence; never fail.
  'notes'               — optional free-text rationale.

Series design rationale
-----------------------
66 points at 3 h/step → total duration 65×3h = 195h > 192h (8 days).
This crosses the threshold in process_vorticity that selects a shorter Savgol
window (n//4|1 = 17) instead of the half-series window (n//2|1 = 33) used for
≤8-day series.  The smaller window is less distorting for these compact synthetic
segments.

Tolerance of 6 timesteps (18 h) accounts for the fact that Lanczos+Savgol
filtering rounds off sharp segment boundaries; the algorithm detects phase onset
after the signal has built up in the smoothed z/dz, typically 2–6 steps after
the segment boundary.
"""

from .generators import _PEAK, make_lifecycle_series

_P = _PEAK   # peak intensity = -9e-4  (most negative)

CASES: dict = {}

# ── (a) ItMD_clean ────────────────────────────────────────────────────────────
# Compact cycle, no noise.  M uses 'plateau' shape for the fix-#10 plateau test.
# Segments: Ic(3) It(22) M(4,plateau) D(37) → 66 points
# Segment boundaries (ground-truth starts):
#   incipient        step 0   (Ic:  0-2)
#   intensification  step 3   (It:  3-24)
#   mature           step 25  (M:  25-28)
#   decay            step 29  (D:  29-65)
_SEG_A = [
    {"type": "Ic", "n": 3,  "shape": "plateau"},
    {"type": "It", "n": 22, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 37, "shape": "sine"},
]
CASES["ItMD_clean"] = {
    "segments": _SEG_A,
    "kwargs":   {"noise_frac": 0.0},
    "series":   make_lifecycle_series(_SEG_A),
    "expected_phases":     ["incipient", "intensification", "mature", "decay"],
    "expected_starts_idx": {
        "incipient":       0,
        "intensification": 3,
        "mature":          25,
        "decay":           29,
    },
    "tolerance": 6,
    "notes": (
        "Clean (no noise) Ic-It-M-D cycle.  M is a 4-step plateau (minimum ≥4 "
        "identical z_unfil values required to exercise the fix-#10 collapse). "
        "66 points → Savgol window = 17 (n//4|1, >8D threshold)."
    ),
}

# ── (b) IcItMD_residual_noisy ─────────────────────────────────────────────────
# Full five-phase cycle with 2% noise.  M uses 'sine' (no exact plateau).
# Segments: Ic(3) It(17) M(4,sine) D(17) residual(25) → 66 points
# Segment boundaries:
#   incipient        step 0   (Ic:  0-2)
#   intensification  step 3   (It:  3-19)
#   mature           step 20  (M:  20-23)
#   decay            step 24  (D:  24-40)
#   residual         step 41  (residual: 41-65)
_SEG_B = [
    {"type": "Ic",       "n": 3,  "shape": "plateau"},
    {"type": "It",       "n": 17, "shape": "sine"},
    {"type": "M",        "n": 4,  "shape": "sine"},
    {"type": "D",        "n": 17, "shape": "sine"},
    {"type": "residual", "n": 25, "shape": "sine"},
]
CASES["IcItMD_residual_noisy"] = {
    "segments": _SEG_B,
    "kwargs":   {"noise_frac": 0.02, "seed": 42},
    "series":   make_lifecycle_series(_SEG_B, noise_frac=0.02, seed=42),
    "expected_phases":     ["incipient", "intensification", "mature", "decay", "residual"],
    "expected_starts_idx": {
        "incipient":       0,
        "intensification": 3,
        "mature":          20,
        "decay":           24,
        "residual":        41,
    },
    "tolerance": 6,
    "notes": (
        "Five-phase cycle with 2% Gaussian noise.  M uses a sine shape (no exact "
        "float plateau) to test near-plateau mature detection without identical "
        "values.  Residual goes halfway toward peak over 25 steps."
    ),
}

# ── (1) ItMD_noisy ────────────────────────────────────────────────────────────
# It→M→D with noise, no Ic.  CycloPhaser still detects a brief 'incipient' at
# the slow-start of the cosine ramp; IT segment boundary is at idx 0.
# Segments: It(25,sine) M(4,plateau) D(37,sine) → 66 points
# GT: intensification GT=0 (segment boundary), detected ~6 steps later (at tol).
_SEG_1 = [
    {"type": "It", "n": 25, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 37, "shape": "sine"},
]
CASES["ItMD_noisy"] = {
    "segments": _SEG_1,
    "kwargs":   {"noise_frac": 0.02, "seed": 0},
    "series":   make_lifecycle_series(_SEG_1, noise_frac=0.02, seed=0),
    "expected_phases":     ["incipient", "intensification", "mature", "decay"],
    "expected_starts_idx": {
        "incipient":       0,
        "intensification": 0,   # It segment boundary; CycloPhaser detects ~6 steps later
        "mature":          25,
        "decay":           29,
    },
    "tolerance": 6,
    "notes": (
        "It-M-D cycle, no Ic segment, 2% noise.  CycloPhaser adds an 'incipient' "
        "phase at the slow cosine start of the It ramp.  'intensification' start "
        "is expected at idx 0 (segment boundary) but detected at ~6 — exactly at "
        "tolerance. *** FLAG: intensification diff=6 at tolerance boundary."
    ),
}

# ── (2) IcDItMD_noisy ────────────────────────────────────────────────────────
# Series starts at PEAK intensity; the slow cosine onset of D is detected by
# CycloPhaser as a brief 'incipient' before the real decay begins.
# Uses start_value=_P.  D initial ramp is a cosine (sine shape) — its near-zero
# derivative at t=0 creates the apparent stability window.
# Segments: D(18,sine) It(20,sine) M(4,plateau) D(24,sine) → 66 points
# Segment boundaries:
#   decay starts at idx 0 (from peak, GT=0; CycloPhaser detects at ~3)
#   intensification  step 18  (It: 18-37)
#   mature           step 38  (M:  38-41)
#   decay 2          step 42  (D:  42-65)
_SEG_IcD2 = [
    {"type": "D",  "n": 18, "shape": "sine"},
    {"type": "It", "n": 20, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 24, "shape": "sine"},
]
CASES["IcDItMD_noisy"] = {
    "segments": _SEG_IcD2,
    "kwargs":   {"noise_frac": 0.02, "seed": 1, "start_value": _P},
    "series":   make_lifecycle_series(_SEG_IcD2, noise_frac=0.02, seed=1, start_value=_P),
    "expected_phases":     ["incipient", "decay", "intensification", "mature", "decay"],
    "expected_starts_idx": {
        "incipient":       0,
        "decay":           0,
        "intensification": 18,
        "mature":          38,
        "decay 2":         42,
    },
    "tolerance": 6,
    "notes": (
        "Starts at peak intensity with a cosine D ramp.  The near-zero derivative "
        "at the cosine start looks like 'incipient' to CycloPhaser (3-step window). "
        "Retained as an example of Ic+D lifecycle onset (IcDItMD pattern)."
    ),
}

# ── (3) IcDItMD_residual_noisy ────────────────────────────────────────────────
# Same as IcDItMD_noisy but with a residual re-intensification at the end.
# Segments: D(16,sine) It(16) M(4) D(16) residual(14) → 66 points
_SEG_IcD3 = [
    {"type": "D",        "n": 16, "shape": "sine"},
    {"type": "It",       "n": 16, "shape": "sine"},
    {"type": "M",        "n": 4,  "shape": "plateau"},
    {"type": "D",        "n": 16, "shape": "sine"},
    {"type": "residual", "n": 14, "shape": "sine"},
]
CASES["IcDItMD_residual_noisy"] = {
    "segments": _SEG_IcD3,
    "kwargs":   {"noise_frac": 0.02, "seed": 2, "start_value": _P},
    "series":   make_lifecycle_series(_SEG_IcD3, noise_frac=0.02, seed=2, start_value=_P),
    "expected_phases": [
        "incipient", "decay", "intensification", "mature", "decay", "residual"
    ],
    "expected_starts_idx": {
        "incipient":       0,
        "decay":           0,
        "intensification": 16,
        "mature":          32,
        "decay 2":         36,
        "residual":        52,
    },
    "tolerance": 6,
    "notes": (
        "Six-phase decay-first cycle with residual and cosine D onset.  Same "
        "incipient artifact as IcDItMD_noisy.  Tests residual detection after a "
        "second decay in a decay-first lifecycle."
    ),
}

# ── (2b) DItMD_noisy ─────────────────────────────────────────────────────────
# Series starts at PEAK intensity and decays abruptly (linear ramp) from step 0.
# The linear D has constant dz from the first timestep — no stability window —
# so CycloPhaser correctly starts with 'decay' and never detects 'incipient'.
# Segments: D(10,linear) It(20,sine) M(4,plateau) D(32,sine) → 66 points
# Segment boundaries:
#   decay            step 0  (D: 0-9)
#   intensification  step 10 (It: 10-29)
#   mature           step 30 (M:  30-33)
#   decay 2          step 34 (D:  34-65)
_SEG_D2 = [
    {"type": "D",  "n": 10, "shape": "linear"},
    {"type": "It", "n": 20, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 32, "shape": "sine"},
]
CASES["DItMD_noisy"] = {
    "segments": _SEG_D2,
    "kwargs":   {"noise_frac": 0.02, "seed": 1, "start_value": _P},
    "series":   make_lifecycle_series(_SEG_D2, noise_frac=0.02, seed=1, start_value=_P),
    "expected_phases":     ["decay", "intensification", "mature", "decay"],
    "expected_starts_idx": {
        "decay":           0,
        "intensification": 10,
        "mature":          30,
        "decay 2":         34,
    },
    "tolerance": 6,
    "notes": (
        "Abrupt-onset decay-first lifecycle.  Linear D ramp ensures dz > 0 from "
        "step 0, preventing CycloPhaser from prepending an 'incipient' phase."
    ),
}

# ── (3b) DItMD_residual_noisy ────────────────────────────────────────────────
# Same as DItMD_noisy but with a residual re-intensification at the end.
# Segments: D(10,linear) It(16,sine) M(4,plateau) D(16,sine) residual(20,sine)
#           → 66 points
# Segment boundaries:
#   decay            step 0  (D: 0-9)
#   intensification  step 10 (It: 10-25)
#   mature           step 26 (M:  26-29)
#   decay 2          step 30 (D:  30-45)
#   residual         step 46 (residual: 46-65)
_SEG_D3 = [
    {"type": "D",        "n": 10, "shape": "linear"},
    {"type": "It",       "n": 16, "shape": "sine"},
    {"type": "M",        "n": 4,  "shape": "plateau"},
    {"type": "D",        "n": 16, "shape": "sine"},
    {"type": "residual", "n": 20, "shape": "sine"},
]
CASES["DItMD_residual_noisy"] = {
    "segments": _SEG_D3,
    "kwargs":   {"noise_frac": 0.02, "seed": 2, "start_value": _P},
    "series":   make_lifecycle_series(_SEG_D3, noise_frac=0.02, seed=2, start_value=_P),
    "expected_phases": ["decay", "intensification", "mature", "decay", "residual"],
    "expected_starts_idx": {
        "decay":           0,
        "intensification": 10,
        "mature":          26,
        "decay 2":         30,
        "residual":        46,
    },
    "tolerance": 6,
    "notes": (
        "Abrupt-onset decay-first lifecycle with residual.  Linear D ramp removes "
        "the incipient artifact present in IcDItMD_residual_noisy."
    ),
}

# ── (4) IcItMD_ItMD_noisy ────────────────────────────────────────────────────
# Two complete Ic-It-M-D cycles.  Tests that periods_to_dict produces correct
# numeric suffixes ('intensification 2', 'mature 2', 'decay 2') and that the
# full two-cycle sequence is detected.
# Segments: Ic(3) It(13) M(4) D(13) It(13) M(4) D(16) → 66 points
# Segment boundaries (first cycle):
#   incipient step 0, intensification step 3, mature step 16, decay step 20
# Segment boundaries (second cycle):
#   intensification 2 step 33, mature 2 step 46, decay 2 step 50
_SEG_4 = [
    {"type": "Ic", "n": 3,  "shape": "plateau"},
    {"type": "It", "n": 13, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 13, "shape": "sine"},
    {"type": "It", "n": 13, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 16, "shape": "sine"},
]
CASES["IcItMD_ItMD_noisy"] = {
    "segments": _SEG_4,
    "kwargs":   {"noise_frac": 0.02, "seed": 3},
    "series":   make_lifecycle_series(_SEG_4, noise_frac=0.02, seed=3),
    "expected_phases": [
        "incipient", "intensification", "mature", "decay",
        "intensification", "mature", "decay",
    ],
    "expected_starts_idx": {
        "incipient":           0,
        "intensification":     3,
        "mature":              16,
        "decay":               20,
        "intensification 2":   33,
        "mature 2":            46,
        "decay 2":             50,
    },
    "tolerance": 6,
    "notes": (
        "Two complete Ic-It-M-D cycles with 2% noise.  Validates numeric-suffix "
        "convention ('intensification 2', etc.) and end-to-end two-cycle timing."
    ),
}

# ── (5) ItMD_ItMD_noisy ───────────────────────────────────────────────────────
# Two It-M-D cycles without a leading Ic.  CycloPhaser adds 'incipient' at the
# slow cosine start of the first It ramp.
# Segments: It(14) M(4) D(14) It(14) M(4) D(16) → 66 points
# Segment boundaries (first cycle):
#   (It starts at 0), mature step 14, decay step 18
# Segment boundaries (second cycle):
#   intensification 2 step 32, mature 2 step 46, decay 2 step 50
_SEG_5 = [
    {"type": "It", "n": 14, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 14, "shape": "sine"},
    {"type": "It", "n": 14, "shape": "sine"},
    {"type": "M",  "n": 4,  "shape": "plateau"},
    {"type": "D",  "n": 16, "shape": "sine"},
]
CASES["ItMD_ItMD_noisy"] = {
    "segments": _SEG_5,
    "kwargs":   {"noise_frac": 0.02, "seed": 4},
    "series":   make_lifecycle_series(_SEG_5, noise_frac=0.02, seed=4),
    "expected_phases": [
        "incipient", "intensification", "mature", "decay",
        "intensification", "mature", "decay",
    ],
    "expected_starts_idx": {
        "incipient":           0,
        "intensification":     0,   # It segment boundary; detected ~3 steps later
        "mature":              14,
        "decay":               18,
        "intensification 2":   32,
        "mature 2":            46,
        "decay 2":             50,
    },
    "tolerance": 6,
    "notes": (
        "Two It-M-D cycles, no leading Ic, 2% noise.  CycloPhaser adds an "
        "'incipient' at the slow cosine ramp start, identical to the ItMD_noisy "
        "case."
    ),
}

# ── (6) IcIt_observational ────────────────────────────────────────────────────
# Truncated lifecycle: only Ic + partial It, never reaching M.
# Represents a cyclone still actively intensifying at the end of the record.
# Segments: Ic(6) It(60, amp=-7e-4) → 66 points
# amp = (baseline + peak) * 0.7 ≈ -7e-4 — reaches ~87% of peak, never full M.
# OBSERVATIONAL: no assert on sequence or timing.  Test only logs what is found.
_SEG_6 = [
    {"type": "Ic", "n": 6,  "shape": "plateau"},
    {"type": "It", "n": 60, "shape": "sine", "amp": (_PEAK + -1e-4) * 0.7},
]
CASES["IcIt_observational"] = {
    "segments": _SEG_6,
    "kwargs":   {"noise_frac": 0.0},
    "series":   make_lifecycle_series(_SEG_6, noise_frac=0.0),
    "test_mode": "observational",
    "notes": (
        "Truncated series: Ic followed by It that never reaches peak intensity. "
        "Represents a cyclone whose record ends mid-intensification.  No lifecycle "
        "sequence is asserted — only the detected sequence is logged."
    ),
}

# ── (7) quase_ItD ────────────────────────────────────────────────────────────
# It→D with no explicit M segment.
#
# THEORETICAL CONCLUSION (not a bug):
#   For any smooth vorticity curve, a transition from intensification (dz < 0,
#   vorticity becoming more negative) to decay (dz > 0) MUST pass through a
#   local minimum — i.e., a point where dz = 0.  That minimum IS the mature
#   phase by definition.  There is no smooth path from It directly to D that
#   avoids a mature state; "ItD without M" is theoretically impossible for a
#   continuous signal.  The Savgol-smoothed curve has exactly this minimum at
#   the cusp, and CycloPhaser correctly identifies it as 'mature'.
#
#   The detection of 'mature' here is therefore the EXPECTED and CORRECT
#   behaviour, not an artefact of the smoother or a limitation of the
#   algorithm.  This case exists to document and assert that property.
#
# Segments: It(33,sine) D(33,sine) → 66 points
# Peak at the It→D transition (idx 32–33); Savgol smoothes this into a brief
# minimum window that CycloPhaser detects as 'mature' (idx ~29–37).
# No expected_starts_idx: timing of the cusp is not a segment boundary.
_SEG_7 = [
    {"type": "It", "n": 33, "shape": "sine"},
    {"type": "D",  "n": 33, "shape": "sine"},
]
CASES["quase_ItD"] = {
    "segments": _SEG_7,
    "kwargs":   {"noise_frac": 0.0},
    "series":   make_lifecycle_series(_SEG_7, noise_frac=0.0),
    "expected_phases": ["incipient", "intensification", "mature", "decay"],
    "notes": (
        "It→D with no explicit M segment.  Asserts that CycloPhaser detects "
        "'mature' at the cusp — the correct theoretical outcome, since any smooth "
        "It→D transition must pass through a local vorticity minimum (dz=0), which "
        "is the mature phase by definition.  No timing check (the cusp has no "
        "designed segment boundary)."
    ),
}

# ── (8) IcItMD_residual_clean ─────────────────────────────────────────────────
# Clean (no noise) version of pilot case (b) 'IcItMD_residual_noisy'.
# Same segment structure; validates that the five-phase detection is not
# noise-dependent.
# Segments: Ic(3) It(17,sine) M(4,sine) D(17,sine) residual(25,sine) → 66 points
# Segment boundaries: same as IcItMD_residual_noisy.
_SEG_8 = [
    {"type": "Ic",       "n": 3,  "shape": "plateau"},
    {"type": "It",       "n": 17, "shape": "sine"},
    {"type": "M",        "n": 4,  "shape": "sine"},
    {"type": "D",        "n": 17, "shape": "sine"},
    {"type": "residual", "n": 25, "shape": "sine"},
]
CASES["IcItMD_residual_clean"] = {
    "segments": _SEG_8,
    "kwargs":   {"noise_frac": 0.0},
    "series":   make_lifecycle_series(_SEG_8, noise_frac=0.0),
    "expected_phases":     ["incipient", "intensification", "mature", "decay", "residual"],
    "expected_starts_idx": {
        "incipient":       0,
        "intensification": 3,
        "mature":          20,
        "decay":           24,
        "residual":        41,
    },
    "tolerance": 6,
    "notes": (
        "Clean (no noise) version of IcItMD_residual_noisy.  'residual' start is "
        "detected ~6 steps after the segment boundary — exactly at tolerance. "
        "*** FLAG: residual diff=6 at tolerance boundary."
    ),
}
