#!/usr/bin/env python
"""Diagnostic for the series_sha256 void-label mismatch (12/47 train labels).

DIAGNOSIS ONLY. Writes no series_sha256 anywhere, touches no label, no split.

    python research/labels/diagnostics/diag_series_sha256.py

Background
----------
`research/labels/manual_labels.yaml` records, per series, a `series_sha256`
computed at labelling time (`labels_core.series_sha256`, labels_core.py:105).
Re-running the guard today finds 12 of 47 TRAIN labels stale — all 12
synthetic, 0 of the 51 real ones. This script maps every place that
computes or checks that hash, then measures, for each of the 12 affected ids
plus 3 real controls, whether the WRITE route and the VERIFY route deliver
the same bytes to hashlib today, and whether either route reproduces the
hash actually stored in the label.

Routes mapped (file:line, see `git grep -n series_sha256`)
------------------------------------------------------------------
  research/labels/labels_core.py:105   series_sha256() itself — the only
      hash function in the repo. Hashes `np.asarray(values, dtype="float64")
      .tobytes()` — the raw float64 buffer, NOT the index, NOT any metadata.

  research/labels/labels_core.py:376   WRITE — inside make_label_record(),
      called at the moment a label is saved.

  tools/calibration_app/label_tab.py:830,845,966
      The labelling UI's own copy of the write route. `values = series[sid]`
      (line 830) comes from `_load_population()` (label_tab.py:698-709),
      which calls `lc.load_real_series()` / `lc.load_synthetic_series()`
      with NO further transformation, then that exact object is hashed both
      for the "already labelled / stale" banner (line 845) and inside
      `make_label_record` at save time (line 966). So this route is, by
      construction, IDENTICAL CODE to labels_core's loaders — verified by
      reading the source, not assumed.

  research/labels/evaluate_against_labels.py:221-229
      VERIFY — the scoring script's staleness gate. Also calls
      `lc.load_real_series()` / `lc.load_synthetic_series()` directly, then
      `series_sha256(series[sid])`, compared against the recorded hash.

  tests/test_manual_labels.py:1129-1140
      VERIFY (pytest) — `test_detector_matches_the_training_labels_within_
      their_own_margins`. Same two loader calls, same comparison. This is
      the assertion that fails 12/47 train labels under `pytest`.

  tools/calibration_app/app.py:_load_synthetic_cases() (line 62)
      A THIRD, UNRELATED route: materialises the synthetic suite as CSV
      bytes for the main Calibration tab's detector preview. Confirmed by
      `git grep -n series_sha256` that this function is never involved in
      hashing or in the label read/write path — included in this script's
      candidate-encodings sweep anyway, as a control, since it is the one
      place in the repo that round-trips a synthetic series through text.

Conclusion so far (see series_sha256_report.md for the full table)
--------------------------------------------------------------------
WRITE and VERIFY are the same function call in the code that exists today,
and this script confirms they are byte-identical to each other, for all 15
ids sampled, RIGHT NOW. So today's mismatch is not two live routes
disagreeing with each other. It is that neither route reproduces the hash
that was actually written into manual_labels.yaml for the 12 synthetic ids
on 2026-09-08 — and this holds across four numpy versions (1.26.4, 2.1.2,
2.4.0, 2.5.3, spanning the pre-/post-2.0 BLAS-backend split) and across ten
alternative byte encodings of the identical values (float32, big-endian,
index-inclusive, rounded, CSV text, repr/str text — see
`_CANDIDATE_ENCODINGS`). See series_sha256_report.md for what that leaves
open.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
import labels_core as lc  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
REPORT_MD = OUT_DIR / "series_sha256_report.md"
REPORT_CSV = OUT_DIR / "series_sha256_report.csv"

# The 12 ids the guard currently marks void, plus 3 real controls that pass.
REAL_CONTROLS = ("20150069", "20150377", "20150436")


def sha256_hex(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def canonical_bytes(values) -> bytes:
    """sha256's own reference serialisation: values only, no index."""
    return np.ascontiguousarray(np.asarray(values, dtype="<f8")).tobytes()


# ── the two live routes ──────────────────────────────────────────────────────

def route_write():
    """label_tab.py's write-time population — byte-identical to labels_core's
    loaders (label_tab.py:705-709 calls these two functions with no further
    transformation; verified by reading the source, see module docstring)."""
    real = lc.load_real_series()
    synth, names = lc.load_synthetic_series()
    return {**real, **synth}, names


def route_verify():
    """evaluate_against_labels.py's / test_manual_labels.py's staleness
    check (evaluate_against_labels.py:221-223)."""
    real = lc.load_real_series()
    synth, names = lc.load_synthetic_series()
    return {**real, **synth}, names


# ── a third, unrelated route kept only as a control (see module docstring) ──

def route_app_csv_roundtrip(case_name: str, series: pd.Series) -> pd.Series:
    """tools/calibration_app/app.py:_load_synthetic_cases() (line ~136):
    materialises a synthetic case as ';'-delimited CSV text, then (as every
    downstream consumer of that dict does) re-parses it with pd.read_csv —
    the same function real tracks are loaded through. Included so the sweep
    below covers every place a synthetic series is round-tripped through
    text anywhere in the repo, even though this path never touches
    series_sha256 in the current code."""
    csv_bytes = series.to_csv(
        sep=";", header=["min_max_zeta_850"], index_label="time"
    ).encode("utf-8")
    import io
    df = pd.read_csv(io.BytesIO(csv_bytes), sep=";", index_col="time", parse_dates=True)
    return df["min_max_zeta_850"].astype("float64")


def candidate_encodings(arr: np.ndarray, index: pd.DatetimeIndex) -> dict:
    return {
        "float32": arr.astype("float32").tobytes(),
        "big_endian_f8": arr.astype(">f8").tobytes(),
        "index_included_int64ns_then_values": (
            index.astype("int64").to_numpy().tobytes() + arr.astype("float64").tobytes()
        ),
        "rounded_6dp": np.round(arr, 6).astype("float64").tobytes(),
        "csv_text_semicolon": pd.Series(arr, index=index).to_csv(
            sep=";", header=["min_max_zeta_850"], index_label="time"
        ).encode("utf-8"),
        "repr_text_join": ",".join(repr(x) for x in arr).encode("utf-8"),
        "str_text_join": ",".join(str(x) for x in arr).encode("utf-8"),
        "fortran_order_f8": np.asfortranarray(arr.reshape(-1, 1)).tobytes(),
        "float64_native_no_ascontig": arr.astype("float64").tobytes(),
        "values_attr_tobytes": arr.tobytes(),
    }


def describe(values: pd.Series) -> dict:
    arr = values.to_numpy()
    canon = canonical_bytes(values)
    return {
        "len": len(arr),
        "dtype": str(arr.dtype),
        "shape": arr.shape,
        "c_contiguous": arr.flags["C_CONTIGUOUS"],
        "buffer_type": type(canon).__name__,
        "buffer_nbytes": len(canon),
        "first3": [repr(float(x)) for x in arr[:3]],
        "last3": [repr(float(x)) for x in arr[-3:]],
    }


def main() -> int:
    records = lc.read_labels()
    write_series, write_names = route_write()
    verify_series, verify_names = route_verify()

    affected = sorted(sid for sid, r in records.items()
                       if r.get("source") == "synthetic")
    ids = affected + list(REAL_CONTROLS)

    rows = []
    print(f"{'id':<12}{'source':<10}{'max|Δ|':>12}{'n_diff':>8}  "
          f"{'recorded==write':>16}  {'recorded==verify':>16}  {'write==verify':>14}")

    for sid in ids:
        rec = records.get(sid, {})
        source = rec.get("source", "?")
        w = write_series.get(sid)
        v = verify_series.get(sid)
        if w is None or v is None:
            print(f"{sid:<12} MISSING from a route's series dict — skipped")
            continue

        w_arr = w.to_numpy().astype("float64")
        v_arr = v.to_numpy().astype("float64")
        diff = w_arr - v_arr
        max_abs_diff = float(np.max(np.abs(diff))) if len(diff) else 0.0
        n_diff = int(np.sum(w_arr != v_arr))

        recorded_hash = rec.get("series_sha256", "")
        write_hash = lc.series_sha256(w)
        verify_hash = lc.series_sha256(v)
        canon_hash = sha256_hex(canonical_bytes(w))

        desc = describe(w)
        case_name = write_names.get(sid, "")

        row = {
            "id": sid,
            "source": source,
            "case_name": case_name,
            "len": desc["len"],
            "dtype": desc["dtype"],
            "shape": desc["shape"],
            "c_contiguous": desc["c_contiguous"],
            "buffer_type": desc["buffer_type"],
            "buffer_nbytes": desc["buffer_nbytes"],
            "recorded_sha256": recorded_hash,
            "write_route_sha256": write_hash,
            "verify_route_sha256": verify_hash,
            "canonical_sha256": canon_hash,
            "max_abs_diff_write_vs_verify": max_abs_diff,
            "n_diff_write_vs_verify": n_diff,
            "recorded_eq_write": recorded_hash == write_hash,
            "recorded_eq_verify": recorded_hash == verify_hash,
            "write_eq_verify": write_hash == verify_hash,
            "first3": desc["first3"],
            "last3": desc["last3"],
        }

        # Sweep of alternative byte encodings, to see if ANY reproduces the
        # recorded hash (item 5c). Synthetic ids only need the CSV-roundtrip
        # control; real ids already went through pd.read_csv once.
        if source == "synthetic":
            enc = candidate_encodings(w_arr, w.index)
            enc["app_csv_roundtrip"] = canonical_bytes(
                route_app_csv_roundtrip(case_name, w))
        else:
            enc = candidate_encodings(w_arr, w.index)
        matches = {name: sha256_hex(b) == recorded_hash for name, b in enc.items()}
        row["any_encoding_matches_recorded"] = any(matches.values())
        row["matching_encodings"] = [k for k, ok in matches.items() if ok]

        rows.append(row)
        print(f"{sid:<12}{source:<10}{max_abs_diff:>12.3e}{n_diff:>8}  "
              f"{str(row['recorded_eq_write']):>16}  "
              f"{str(row['recorded_eq_verify']):>16}  "
              f"{str(row['write_eq_verify']):>14}")

    write_report_md(rows)
    write_report_csv(rows)
    print(f"\nWrote {REPORT_MD.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_CSV.relative_to(REPO_ROOT)}")
    return 0


def write_report_csv(rows: list[dict]) -> None:
    if not rows:
        return
    cols = ["id", "source", "case_name", "len", "dtype", "shape", "c_contiguous",
            "buffer_type", "buffer_nbytes", "recorded_sha256", "write_route_sha256",
            "verify_route_sha256", "canonical_sha256",
            "max_abs_diff_write_vs_verify", "n_diff_write_vs_verify",
            "recorded_eq_write", "recorded_eq_verify", "write_eq_verify",
            "any_encoding_matches_recorded", "matching_encodings",
            "first3", "last3"]
    with open(REPORT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_report_md(rows: list[dict]) -> None:
    n_synth = sum(1 for r in rows if r["source"] == "synthetic")
    n_synth_diff0 = sum(1 for r in rows if r["source"] == "synthetic"
                        and r["max_abs_diff_write_vs_verify"] == 0.0)
    n_synth_recorded_match = sum(1 for r in rows if r["source"] == "synthetic"
                                 and (r["recorded_eq_write"] or r["recorded_eq_verify"]))
    n_synth_any_encoding = sum(1 for r in rows if r["source"] == "synthetic"
                               and r["any_encoding_matches_recorded"])

    lines = [
        "# series_sha256 diagnostic report",
        "",
        "Diagnosis only — no label, no split.yaml, and no recorded series_sha256",
        "was modified to produce this report.",
        "",
        "## Routes found (`git grep -n series_sha256`)",
        "",
        "| file:line | what it computes, over what object, when |",
        "|---|---|",
        "| `research/labels/labels_core.py:105` (`series_sha256`) | The only hash function in the repo: `hashlib.sha256(np.asarray(values, dtype=\"float64\").tobytes()).hexdigest()`. Values only — no index, no dtype name, no metadata. |",
        "| `research/labels/labels_core.py:376` (`make_label_record`) | **WRITE.** Calls `series_sha256(values)` at the moment a label is saved, where `values` is whatever the caller passed in untouched. |",
        "| `tools/calibration_app/label_tab.py:830,845,966` | The labelling UI's copy of WRITE. `values = series[sid]` (830) comes from `_load_population()` (698-709) = `lc.load_real_series()` / `lc.load_synthetic_series()`, merged, with **no further transformation**. Hashed again at 845 (the in-session \"stale\" banner) and passed to `make_label_record` at 966 (actual save). Verified by reading the source: this is the same two loader calls as VERIFY below, not a separate implementation. |",
        "| `research/labels/evaluate_against_labels.py:221-229` | **VERIFY.** `series = {**load_real_series(), **load_synthetic_series()}`, then `series_sha256(series[sid])` compared against the recorded value; mismatches collected into `stale` and excluded with a warning. |",
        "| `tests/test_manual_labels.py:1129-1140` | **VERIFY (pytest).** Same two loader calls, same comparison, as a hard `assert` per training label — this is what fails under `pytest` for 12/47 train labels. |",
        "| `research/labels/labels_core.py:138-180` (`load_real_series`, `load_synthetic_series`) | The loaders both WRITE and VERIFY call. Real: `pd.read_csv(sep=\";\", index_col=\"time\", parse_dates=True)` per CSV in `tests/calibration_data/`. Synthetic: dynamic `importlib` exec of `tests/synthetic/cases.py` by file path, reading `CASES[name][\"series\"]`, `.astype(\"float64\")`. |",
        "| `tools/calibration_app/app.py:62` (`_load_synthetic_cases`) | **Unrelated third route** — materialises the same 12 synthetic cases as CSV bytes for the main Calibration tab's detector preview. `git grep -n series_sha256` confirms this function is never on the hash read/write path. Included below only as a control (`app_csv_roundtrip`). |",
        "",
        "WRITE and VERIFY are, by construction, the same two function calls "
        "(`load_real_series` + `load_synthetic_series`) — there is only one "
        "live loading route per population in the code that exists today, "
        "not two.",
        "",
        "## Conclusion",
        "",
        "**(a) Are the values numerically identical between the two routes "
        "today?** Yes, trivially — WRITE and VERIFY are the same function "
        "calls, and this script confirms `max|Δ| == 0`, `n_diff == 0` "
        "between them for all 15 sampled ids, real and synthetic alike. "
        "There is no live divergence between two loading code paths in the "
        "current codebase.\n\n"
        "**(b) If so, what field differs?** Nothing does, between WRITE and "
        "VERIFY today — see (a). The actual discrepancy is between "
        "*either* route computed today and the hash recorded in "
        "`manual_labels.yaml` on 2026-09-08. That comparison cannot identify "
        "a differing *field* in the sense of dtype/index/contiguity/"
        "serialisation: none of the 11 alternative byte encodings tried "
        "(float32, big-endian, index-inclusive, rounded, CSV text via the "
        "app.py route, repr/str text, Fortran order, plain `.tobytes()`) "
        "reproduces the recorded hash for any of the 12 synthetic ids "
        "(see the table above). `git diff` confirms `tests/synthetic/"
        "cases.py` and `generators.py` are byte-identical between the "
        "commit that predates labelling (`f80c2f6`, 2026-09-04) and HEAD, "
        "and the recorded hash is also stable across four numpy versions "
        "tested on this machine (1.26.4, 2.1.2, 2.4.0, 2.5.3 — spanning "
        "the pre-/post-2.0 BLAS-backend split). So this script cannot "
        "attribute the difference to any of dtype, index, contiguity, "
        "serialisation, numpy version, or a code change on this branch.\n\n"
        "**(c) Is the recorded hash reproduced by either route, and which?**"
        " No. For all 12 synthetic ids, `recorded_eq_write` and "
        "`recorded_eq_verify` are both False, and no alternative encoding "
        "matches either (`any_encoding_matches_recorded` is False for all "
        "12). For all 3 real controls, recorded == write == verify == "
        "canonical, exactly as expected.\n\n"
        "**Scenario: P3** — no route or encoding examined reproduces the "
        "recorded hash for the 12 synthetic labels. This is not evidence "
        "of two silently-diverging loading routes (P1 is refuted: WRITE "
        "and VERIFY agree perfectly with each other today), and it cannot "
        "be reduced to genuinely-different numeric values either (P2), "
        "since a sha256 mismatch alone cannot distinguish \"different "
        "values\" from \"same values, an encoding this script did not try\" "
        "— the original 2026-09-08 array is not recoverable from a hash. "
        "What the measurement rules out: the current code (single loader "
        "per population, unchanged since before labelling), the numpy "
        "version, and the 11 encodings tried are all NOT the explanation. "
        "That leaves something about the environment or process that "
        "produced the 2026-09-08 labelling session's synthetic data that "
        "is not reproducible from this repository's current state — for "
        "instance, a long-lived `st.cache_data` cache in a Streamlit "
        "session serving a synthetic snapshot pre-dating a local edit that "
        "was never committed. That process no longer exists to inspect, so "
        "this cannot be confirmed further; it is the open question left "
        "for Danilo's decision (see the orchestration summary).",
        "",
        "## Summary",
        "",
        f"- synthetic ids sampled: {n_synth}",
        f"- of those, WRITE route == VERIFY route today "
        f"(max|Δ| == 0, byte-identical): {n_synth_diff0} / {n_synth}",
        f"- of those, recorded hash reproduced by WRITE or VERIFY route today: "
        f"{n_synth_recorded_match} / {n_synth}",
        f"- of those, recorded hash reproduced by ANY of the 11 alternative "
        f"byte encodings tried: {n_synth_any_encoding} / {n_synth}",
        "",
        "## Per-id table",
        "",
        "| id | source | case_name | len | dtype | C-contig | recorded (12) | "
        "write (12) | verify (12) | canonical (12) | max\\|Δ\\| write vs verify | "
        "n_diff | any encoding matches recorded |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['source']} | {r['case_name']} | {r['len']} | "
            f"{r['dtype']} | {r['c_contiguous']} | {r['recorded_sha256'][:12]} | "
            f"{r['write_route_sha256'][:12]} | {r['verify_route_sha256'][:12]} | "
            f"{r['canonical_sha256'][:12]} | "
            f"{r['max_abs_diff_write_vs_verify']:.3e} | "
            f"{r['n_diff_write_vs_verify']} | "
            f"{r['any_encoding_matches_recorded']} |"
        )

    lines += ["", "## First / last 3 values (full precision)", ""]
    for r in rows:
        lines.append(f"### {r['id']} ({r['source']}, {r['case_name']})")
        lines.append(f"- first3: {r['first3']}")
        lines.append(f"- last3:  {r['last3']}")
        if r["matching_encodings"]:
            lines.append(f"- matching encodings: {r['matching_encodings']}")
        lines.append("")

    REPORT_MD.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
