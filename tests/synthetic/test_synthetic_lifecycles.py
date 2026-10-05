"""Synthetic lifecycle tests for CycloPhaser.

Each test runs determine_periods on a known synthetic vorticity series and
verifies:
  1. The sequence of detected phases matches the expected lifecycle order.
  2. The start of each phase is within *tolerance* timesteps of the boundary
     in Danilo's manual label for that case (research/labels/manual_labels.yaml).

Source of truth for timing (front G, 2026-09-15)
------------------------------------------------
The timing test used to read `expected_starts_idx` from cases.py -- boundaries
typed by hand from the segment list used to BUILD the series. That source is
systematically wrong for mature: the designed plateau is 4 steps, but the
neighbouring `sine` segments enter and leave with zero derivative, so the region
that is actually flat is 7-16 steps long, and the manual labels (reviewed by
Danilo with the filtered/smoothed curves visible) mark it so. Per
docs/future_work.md items 15 and 17, the manual label is the truth.

`expected_starts_idx` is no longer read by this module (it stays in cases.py
until its own clean-up front). `expected_phases` is still read by the SEQUENCE
test -- that front has not been opened.

The timing test runs on the FROZEN series (tests/synthetic/data/<id>.csv), not
on `case["series"]`: a label is only valid for the exact values it was written
against, and its `series_sha256` is checked before any boundary is compared.
`case["series"]` is regenerated at import and is not bit-stable across
environments (docs/future_work.md item 14); measured on 2026-09-15 it differed
from the frozen files by <= 1.1e-19 in one environment -- no phase assignment
changed, but the hash does, so the label would not certify it.

Boundaries are paired by POSITION, and only when the detected phase sequence
equals the labelled one (same rule as labels_core.score_phase_sequences):
across a sequence mismatch "the k-th boundary" names two different transitions.
The first phase is not a boundary (both sides pin it at index 0) and is skipped.
Boundaries the labeller marked `unsure` are skipped and printed.

The tolerance section below predates front G and describes deviations from the
OLD, segment-derived source; the current per-boundary table is in
research/labels/front_g/front_g_synthetic_deviations.md.

These tests are not regression tests (they do not compare byte-for-byte to a
frozen baseline).  They verify that CycloPhaser produces physically sensible
phase sequences and approximately correct timing on controlled synthetic inputs.

Test modes (set via CASES[id]['test_mode']):
  'standard'      — assert sequence == expected AND timing within tolerance.
                    This is the default.
  'observational' — run and log detected sequence only; no assertions.
                    Used for truncated or ambiguous series where no ground
                    truth can be defined.

Tolerance and detection lag (item #15)
---------------------------------------
The per-case tolerance is set to 6 timesteps (18 h at 3-hourly resolution).
This value is NOT arbitrary: it reflects an inherent phase-detection lag
observed empirically across this synthetic suite.

Across the 12 cases, 5 touched the tolerance boundary (diff ≥ tol−1 = 5):

  Case                    Phase              Diff
  ItMD_clean              decay              5
  ItMD_noisy              intensification    6
  IcItMD_residual_noisy   residual           6
  DItMD_residual_noisy    residual           5
  IcItMD_residual_clean   residual           6

The 'residual' lag is the most systematic: in all three cases with a residual
segment, the detected start was 15–18 h (5–6 steps) after the designed segment
boundary.  This is caused by the Lanczos + Savgol filtering chain needing
several timesteps to build up enough amplitude to identify the re-intensification.

The remaining two cases (ItMD_clean/decay and ItMD_noisy/intensification) may
reflect the same phenomenon or a separate boundary effect; root cause has not
been investigated (see item #15 in project notes).

Practical implication: when interpreting CycloPhaser output, apply a margin of
at least 18 h around detected phase start times, especially for 'residual'.
"""

import sys
import warnings
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pytest

from cyclophaser.determine_periods import determine_periods, periods_to_dict

from tests.synthetic.cases import CASES

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_LABELS_DIR = _REPO_ROOT / "research" / "labels"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """Strip trailing numeric suffix: 'intensification 2' → 'intensification'."""
    return name.rstrip(" 0123456789").strip()


def _run(series: pd.Series):
    """Run determine_periods with default parameters and return results.

    Returns
    -------
    seq        : list[str]  normalized phase sequence (suffixes stripped)
    norm_starts: dict[str, pd.Timestamp]  first occurrence of each normalized phase
    raw_starts : dict[str, pd.Timestamp]  ALL phases keyed by full name
                 (e.g. 'intensification 2') — use for timing checks in two-cycle
                 cases
    df         : pd.DataFrame  raw determine_periods output
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = determine_periods(series, x=series.index)
    d = periods_to_dict(df)
    seq = [_normalize(ph) for ph in d]
    norm_starts: dict[str, pd.Timestamp] = {}
    raw_starts:  dict[str, pd.Timestamp] = {}
    for ph, (st, _) in d.items():
        raw_starts[ph] = st
        key = _normalize(ph)
        if key not in norm_starts:
            norm_starts[key] = st
    return seq, norm_starts, raw_starts, df


def _ts_to_idx(series: pd.Series, ts: pd.Timestamp) -> int:
    """Convert a Timestamp to its integer position in the series index."""
    return int(series.index.get_loc(ts))


@lru_cache(maxsize=1)
def _labels_core():
    """research/labels/labels_core.py, imported by path (it is not a package)."""
    if str(_LABELS_DIR) not in sys.path:
        sys.path.insert(0, str(_LABELS_DIR))
    import labels_core
    return labels_core


@lru_cache(maxsize=1)
def _synthetic_labels() -> dict:
    """{opaque_id: label record} for the synthetic cases in manual_labels.yaml.

    yaml is imported here, not at module scope: an optional dependency imported
    at collection time fails the whole suite (see tests/conftest.py). It is NOT
    guarded by a skip: if it is missing, the timing test must fail, not quietly
    stop checking against the ground truth.
    """
    import yaml
    lc = _labels_core()
    doc = yaml.safe_load(lc.LABELS_PATH.read_text())
    return {r["id"]: r for r in doc["labels"] if r.get("source") == "synthetic"}


@lru_cache(maxsize=1)
def _frozen_synthetic_series() -> dict:
    series, _names = _labels_core().load_synthetic_series()
    return series


def labelled_case(case_id: str):
    """(frozen series, label record) for one synthetic case, hash-checked.

    Raises AssertionError if the case has no label or the label was written
    against different values than the frozen file holds.
    """
    lc = _labels_core()
    oid = lc.opaque_synthetic_id(case_id)
    rec = _synthetic_labels().get(oid)
    assert rec is not None, f"[{case_id}] no manual label for id {oid}"
    series = _frozen_synthetic_series()[oid]
    got = lc.series_sha256(series.values)
    assert got == rec["series_sha256"], (
        f"[{case_id}] label {oid} is stale: series_sha256 {got} != "
        f"{rec['series_sha256']} recorded in manual_labels.yaml")
    return series, rec


def boundary_deviations(case_id: str, tol: int):
    """Compare detected boundaries with the manual label, position by position.

    Returns (rows, problem). `rows` has one dict per labelled boundary (phase
    index k >= 1): phase, labelled idx, detected idx, signed deviation
    (detected - label), tol, slack (tol - |dev|), the label's own
    tolerance_idx, and unsure. `problem` is None, or a string when the detected
    sequence differs from the labelled one -- then no deviation is computed.
    """
    series, rec = labelled_case(case_id)
    _, _, raw_starts, _ = _run(series)
    det = [(_normalize(ph), _ts_to_idx(series, ts)) for ph, ts in raw_starts.items()]
    lab = rec["phases"]
    lab_seq = [p["phase"] for p in lab]
    det_seq = [p for p, _ in det]
    if lab_seq != det_seq:
        return [], (f"sequence mismatch: label {lab_seq} vs detected {det_seq}")
    rows = []
    for k in range(1, len(lab)):
        dev = det[k][1] - int(lab[k]["start_idx"])
        rows.append({
            "k": k, "phase": lab[k]["phase"],
            "label": int(lab[k]["start_idx"]), "detected": det[k][1],
            "dev": dev, "tol": tol, "slack": tol - abs(dev),
            "label_tol": int(lab[k]["tolerance_idx"]),
            "unsure": bool(lab[k].get("unsure", False)),
        })
    return rows, None


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("case_id", list(CASES))
def test_lifecycle_phase_sequence(case_id):
    """Detected phase sequence must match the expected order."""
    case      = CASES[case_id]
    series    = case["series"]
    test_mode = case.get("test_mode", "standard")

    seq, _, _, _ = _run(series)

    if test_mode == "observational":
        print(f"\n[{case_id}] OBSERVATIONAL — detected sequence: {seq}")
        return  # no assertion

    # standard
    exp_seq = case["expected_phases"]
    assert seq == exp_seq, (
        f"[{case_id}] Phase sequence mismatch\n"
        f"  expected : {exp_seq}\n"
        f"  detected : {seq}"
    )


@pytest.mark.parametrize("case_id", list(CASES))
def test_lifecycle_phase_timing(case_id):
    """Each boundary must be within tolerance of Danilo's manual label."""
    case      = CASES[case_id]
    test_mode = case.get("test_mode", "standard")

    if test_mode == "observational":
        pytest.skip("Timing not checked for observational cases")

    tol = case.get("tolerance", 6)
    rows, problem = boundary_deviations(case_id, tol)

    print(f"\n[{case_id}] timing deviations vs manual label (detected - label):")
    if problem:
        print(f"  {problem}")
        pytest.fail(f"[{case_id}] {problem}")

    failures = []
    for r in rows:
        if r["unsure"]:
            print(f"  {r['k']} {r['phase']}: label marked unsure -- not scored")
            continue
        flag = "  *** FLAG (slack <= 1)" if r["slack"] <= 1 else ""
        fail = "  <- FAIL" if r["slack"] < 0 else ""
        print(f"  {r['k']} {r['phase']}: detected={r['detected']} "
              f"label={r['label']} dev={r['dev']:+d} tol={tol} "
              f"slack={r['slack']}{flag}{fail}")
        if r["slack"] < 0:
            failures.append(
                f"  {r['phase']} (boundary {r['k']}): detected {r['detected']}, "
                f"label {r['label']} +-{tol}, off by {r['dev']:+d}")

    if failures:
        pytest.fail(
            f"[{case_id}] Phase start timing outside tolerance:\n"
            + "\n".join(failures)
        )
