"""Pure machinery behind the Compare page — no Streamlit, and no labels.

The Compare page answers one question: what changes in the phases of the user's
own tracks when the configuration changes. Nothing on it is measured against a
manual label, so nothing here reads one: this module calls only the label-free
parts of `benchmark_core` (`split_config`, `signature_audit`, `run_series`,
`reference_metrics`, `refused_incipient`) and `config_defaults.fill_missing`.
tests/test_compare_apptest.py makes the label readers raise and runs the page.

Two identities matter here:

* **A track is its content, not its name.** Two files with the same name and
  different values are two tracks; the cache key of a result is the sha256 of the
  series' time index and values (`series_key`).
* **A configuration is what actually runs, not its text.** The key is the
  sha256 of the arguments passed to the package (`config_key`), after the same
  filling and dropping benchmark_core and the evaluator apply, and after the
  app's `use_filter` translation — so a key order, a missing key the filling
  restores, or `use_filter: true` against `'auto'` do not make two keys.

The tracks are read with `track_io.read_track`, the reader the Calibrate page
uses, so each keeps its time index. `process_vorticity` picks the 'auto'
smoothing window from the length of that index (benchmark review, A11).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import benchmark_core as bc  # noqa: E402
import track_io  # noqa: E402
from config_defaults import fill_missing  # noqa: E402  (research/labels, via benchmark_core)
from package_args import package_use_filter  # noqa: E402

SECTIONS = ("filter_params", "phase_params")


# ── tracks ────────────────────────────────────────────────────────────────────
def read_series(data: bytes) -> pd.Series:
    """Standard-layout track bytes → the validated vorticity Series (time index)."""
    return track_io.read_track(data)


def series_key(series: pd.Series) -> str:
    """sha256 of the series' content: its time index and its values."""
    h = hashlib.sha256()
    idx = series.index
    h.update(str(idx.dtype).encode())
    h.update(idx.asi8.tobytes() if hasattr(idx, "asi8") else
             pd.Index(idx).astype("int64").to_numpy().tobytes())
    h.update(series.to_numpy(dtype="float64").tobytes())
    return h.hexdigest()


# ── configurations ────────────────────────────────────────────────────────────
def parameter_sections(doc: dict) -> dict:
    """Only the two parameter sections of a configuration document.

    A saved file also carries `metadata` and possibly a developer `evaluation`
    section; neither changes detection, and neither is shown on this page.
    """
    return {sec: dict(doc.get(sec) or {}) for sec in SECTIONS}


def check_document(doc) -> str | None:
    """Why `doc` cannot be a column, or None. Same rules as the Calibrate import."""
    if not isinstance(doc, dict):
        return "YAML root must be a mapping."
    missing = [s for s in SECTIONS if s not in doc]
    if missing:
        return f"Missing required sections: {', '.join(missing)}"
    return None


def effective_config(doc: dict) -> tuple[dict, dict]:
    """(process_vorticity kwargs, get_periods kwargs) as they will run.

    `benchmark_core.split_config` (fill the absent keys, drop the ones the
    package does not read), then the app's `use_filter` translation.
    """
    pv, gp = bc.split_config(parameter_sections(doc))
    if "use_filter" in pv:
        pv = {**pv, "use_filter": package_use_filter(pv["use_filter"])}
    return pv, gp


def config_key(doc: dict) -> str:
    """sha256 of the effective configuration (see `effective_config`)."""
    pv, gp = effective_config(doc)
    blob = json.dumps({"filter_params": pv, "phase_params": gp},
                      sort_keys=True, default=repr)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def effective_document(doc: dict) -> dict:
    """The configuration as it runs, in the YAML's own shape: the given values,
    the filled ones, and nothing the package does not read."""
    filled, _ = fill_missing(parameter_sections(doc))
    pv, gp = bc.split_config(parameter_sections(doc))
    return {"filter_params": {k: filled["filter_params"][k]
                              for k in filled["filter_params"] if k in pv},
            "phase_params": {k: filled["phase_params"][k]
                             for k in filled["phase_params"] if k in gp}}


def audit(doc: dict) -> dict:
    """What the page says about a column's file: keys not applied, keys filled.

    `ignored` is `benchmark_core.signature_audit`'s (keys the current package
    signature does not read); `filled` is `config_defaults.fill_missing`'s, the
    rule the Calibrate import applies, as [(\"section.key\", value), ...].
    """
    sections = parameter_sections(doc)
    _doc, filled = fill_missing(sections)
    return {"ignored": list(bc.signature_audit(sections)["ignored"]),
            "filled": list(filled)}


def _same(a, b) -> bool:
    if (isinstance(a, float) or isinstance(b, float)) and \
            isinstance(a, (int, float)) and isinstance(b, (int, float)) and \
            not isinstance(a, bool) and not isinstance(b, bool):
        return abs(a - b) <= 1e-12 * max(1.0, abs(a), abs(b))
    return a == b


def config_differences(doc: dict, ref_doc: dict) -> dict[str, tuple]:
    """{'section.key': (this value, reference value)} for parameters whose
    EFFECTIVE value differs (see `effective_document`).

    Floats are compared with the tolerance the Calibrate page's "edited" check
    uses, so a slider's 0.30000000000000004 is not reported against 0.3.
    """
    a, b = effective_document(doc), effective_document(ref_doc)
    out: dict[str, tuple] = {}
    for sec in SECTIONS:
        for k in sorted(set(a[sec]) | set(b[sec])):
            va, vb = a[sec].get(k, "—"), b[sec].get(k, "—")
            if not _same(va, vb):
                out[f"{sec}.{k}"] = (va, vb)
    return out


# ── running ───────────────────────────────────────────────────────────────────
def run_cell(doc: dict, series: pd.Series) -> dict:
    """One configuration on one track: {"error", "runs", "z"}.

    `runs` is [(phase, start, end_inclusive), ...] over normalised phase names;
    `z` the smoothed series the phases were detected on, as a tuple of floats.
    A failure is recorded as the cell's error, never skipped.
    """
    pv, gp = effective_config(doc)
    res = bc.run_series(pv, gp, series)
    z = res.get("z")
    return {"error": res["error"],
            "runs": None if res["runs"] is None else [tuple(r) for r in res["runs"]],
            "z": None if z is None else tuple(float(v) for v in z.values)}


# ── measures ──────────────────────────────────────────────────────────────────
def sequence(res: dict | None):
    """The phase sequence of a cell, or None when it has none."""
    if not res or res.get("runs") is None:
        return None
    return [p for p, _a, _b in res["runs"]]


def sequence_differs(res: dict | None, ref: dict | None) -> bool:
    """True when both cells have phases and their sequences differ."""
    a, b = sequence(res), sequence(ref)
    return a is not None and b is not None and a != b


def relative(col: dict[str, dict], ref: dict[str, dict], ids) -> dict:
    """One column against the reference column, over `ids` — distances only.

    `benchmark_core.reference_metrics`, without its fourth measure, which is a
    count of the column's own and not a distance (benchmark review, A2; see
    `incipient_absent`).
    """
    m = bc.reference_metrics({s: _as_bc(col.get(s)) for s in ids},
                             {s: _as_bc(ref.get(s)) for s in ids}, ids)
    return {k: m[k] for k in ("n_compared", "n_sequence_changed",
                              "n_boundaries_compared", "shift_median",
                              "shift_max", "appeared", "disappeared")}


def incipient_absent(col: dict[str, dict], ids) -> tuple[int, int]:
    """(tracks whose first phase is not incipient, tracks the column ran on)."""
    ran = [s for s in ids if col.get(s) and col[s].get("runs") is not None]
    return sum(1 for s in ran if bc.refused_incipient(col[s]["runs"])), len(ran)


def _as_bc(res: dict | None) -> dict | None:
    if res is None:
        return None
    return {"runs": res.get("runs")}
