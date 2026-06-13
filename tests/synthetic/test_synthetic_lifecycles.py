"""Synthetic lifecycle tests for CycloPhaser.

Each test runs determine_periods on a known synthetic vorticity series and
verifies:
  1. The sequence of detected phases matches the expected lifecycle order.
  2. The start of each phase is within *tolerance* timesteps of the segment
     boundary (ground-truth) defined in cases.py.

These tests are not regression tests (they do not compare byte-for-byte to a
frozen baseline).  They verify that CycloPhaser produces physically sensible
phase sequences and approximately correct timing on controlled synthetic inputs.

Test modes (set via CASES[id]['test_mode']):
  'standard'          — assert sequence == expected AND timing within tolerance.
  'observational'     — run and log detected sequence only; no assertions.
  'property_no_mature'— log whether 'mature' appears; never fail.
"""

import warnings

import pandas as pd
import pytest

from cyclophaser.determine_periods import determine_periods, periods_to_dict

from tests.synthetic.cases import CASES


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

    if test_mode == "property_no_mature":
        if "mature" in seq:
            print(f"\n[{case_id}] PROPERTY OBSERVATION: 'mature' was detected "
                  f"despite no M segment — full sequence: {seq}")
        else:
            print(f"\n[{case_id}] PROPERTY OK: 'mature' correctly absent — "
                  f"sequence: {seq}")
        return  # never fail for property tests

    # standard
    exp_seq = case["expected_phases"]
    assert seq == exp_seq, (
        f"[{case_id}] Phase sequence mismatch\n"
        f"  expected : {exp_seq}\n"
        f"  detected : {seq}"
    )


@pytest.mark.parametrize("case_id", list(CASES))
def test_lifecycle_phase_timing(case_id):
    """Each phase start must be within tolerance timesteps of the segment boundary."""
    case      = CASES[case_id]
    test_mode = case.get("test_mode", "standard")

    if test_mode in ("observational", "property_no_mature"):
        pytest.skip(f"Timing not checked for test_mode='{test_mode}'")

    series  = case["series"]
    exp_idx = case.get("expected_starts_idx", {})
    tol     = case.get("tolerance", 6)

    _, _, raw_starts, _ = _run(series)

    failures   = []
    deviations = []
    for phase, gt_step in exp_idx.items():
        ts = raw_starts.get(phase)
        if ts is None:
            failures.append(f"  {phase}: not detected (gt={gt_step})")
            continue
        detected_step = _ts_to_idx(series, ts)
        diff = abs(detected_step - gt_step)
        flag = "  *** FLAG (diff >= tol-1)" if diff >= tol - 1 else ""
        fail = "  ← FAIL" if diff > tol else ""
        deviations.append(
            f"  {phase}: detected={detected_step} gt={gt_step} "
            f"diff={diff} tol={tol}{flag}{fail}"
        )
        if diff > tol:
            failures.append(
                f"  {phase}: detected step {detected_step} "
                f"(expected ~{gt_step} ±{tol}, off by {diff})"
            )

    # Always print deviations for visibility even when all pass
    print(f"\n[{case_id}] timing deviations:")
    for line in deviations:
        print(line)

    if failures:
        pytest.fail(
            f"[{case_id}] Phase start timing outside tolerance:\n"
            + "\n".join(failures)
        )
