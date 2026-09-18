"""Pure machinery behind the Benchmark tab — no Streamlit, no globals mutated.

Why this module exists
----------------------
The calibration produced eleven configurations over two months and there was no
way to see, side by side, how phase detection moved between them. Comparing meant
swapping a config into the sidebar and remembering what the last one looked like.
This module turns a configuration into a COLUMN: a self-describing object that
carries its own provenance, runs the detector over a chosen set of cyclones, and
reports two named measurements over the result.

Three rules are structural here, not stylistic:

* **The running code's commit is the provenance, not the YAML's version field.**
  `metadata.cyclophaser_version` reads `2.0.0` in all eleven files and therefore
  distinguishes nothing. `git rev-parse HEAD` is what actually determines the
  behaviour a column displays.
* **`evaluation.bad_cases_count` is never a score.** Those marks were made in
  different weeks with different understanding of the problem (params-5 and -6
  record 0, params-9 records 6). It is carried as a labelled historical
  annotation and never as a comparison metric.
* **`item19_core.CONFIG` is never repointed.** It pins params-10 deliberately, as
  a frozen instrument. This module calls `pair_by_overlap` with a column's own
  output and leaves the module's configuration alone.

The two measurements are always reported together and always named, because they
are different instruments and the debt between them is not settled here:

* phase SEQUENCE — `labels_core.score_phase_sequences`, the same function
  `research/labels/evaluate_against_labels.py` calls: starts only, each boundary
  against its own `tolerance_idx`, and it refuses to pair boundaries at all when
  the sequence does not match.
* MATURE pairing — `item19_core.pair_by_overlap`: largest-overlap block, both
  ends, fixed margin 6.

Leakage rule
------------
Any AGGREGATE number is computed over the TRAIN split. Aggregates involving the
16 real cyclones of the frozen test split are returned in a separate block,
labelled test, and never added into the train one. Per-cyclone rows are display,
not aggregate, and may show either.
"""

from __future__ import annotations

import hashlib
import inspect
import re
import subprocess
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

_REPO = Path(__file__).resolve().parents[2]

# `research/labels` alone — never the repo root from here — keeps the import of
# labels_core from depending on a `cyclophaser` that may or may not be the one
# already imported. The package itself is imported by name below, normally.
for _p in (str(_REPO / "research" / "labels"),
           str(_REPO / "research" / "labels" / "diagnostics" / "item19"),
           str(_REPO)):
    if _p not in sys.path:
        sys.path.append(_p)

from cyclophaser.determine_periods import get_periods, process_vorticity  # noqa: E402
from labels_core import (load_real_series, load_synthetic_series,  # noqa: E402
                         normalize_phase, read_labels, read_split,
                         score_phase_sequences, series_sha256)

# Imported for its pairing rule ONLY. item19_core.CONFIG stays pointed at
# params-10; nothing here writes to it. See the module docstring.
from item19_core import MARGIN as MATURE_MARGIN  # noqa: E402
from item19_core import pair_by_overlap  # noqa: E402

CONFIGS_DIR = _REPO / "research" / "labels" / "configs"
SNAPSHOT_DIR = _REPO / "research" / "snapshots"

PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")

SEQUENCE_INSTRUMENT = "evaluate_against_labels.py / score_phase_sequences"
MATURE_INSTRUMENT = f"item19_core.pair_by_overlap (margin {MATURE_MARGIN})"

# The exact wording the header shows for a config written before the filter fix.
PRE_FILTER_FIX_WARNING = (
    "config anterior à correção do filtro — este YAML não traz `boundary_padding`. "
    "Ele foi exportado quando `use_filter: true` era lido como a janela inteira 1 "
    "(bool é subclasse de int), de modo que o filtro Lanczos NUNCA era aplicado. "
    "A mesma linha hoje aplica o filtro (janela = len(série)//2). Esta coluna "
    "mostra, portanto, um resultado que nunca foi visto na época — não é histórico."
)


# ── provenance ────────────────────────────────────────────────────────────────
def git_head(repo: Path | None = None) -> str:
    """Commit of the code actually running, or 'unknown'.

    This — not `metadata.cyclophaser_version` — is a column's code provenance.
    """
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             cwd=str(repo or _REPO), capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── the current signature, and what a YAML says about it ──────────────────────
def current_defaults() -> dict[str, dict]:
    """{'filter_params': {...}, 'phase_params': {...}} of the CURRENT signature."""
    def defaults(fn, drop):
        return {k: p.default
                for k, p in inspect.signature(fn).parameters.items()
                if k not in drop and p.default is not inspect.Parameter.empty}

    pv = defaults(process_vorticity, {"zeta_df"})
    gp = defaults(get_periods, {"vorticity", "plot", "plot_steps", "export_dict"})
    return {"filter_params": pv, "phase_params": gp}


def split_config(doc: dict) -> tuple[dict, dict]:
    """A config document → (process_vorticity kwargs, get_periods kwargs).

    Keys the current signature does not accept are dropped, exactly as
    `evaluate_against_labels.load_config` drops them, so a column runs the same
    way the evaluation script would run it.
    """
    gp_ok = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_ok}
    return pv, gp


def signature_audit(doc: dict) -> dict:
    """Items 3, 4 and 5 of a column header.

    * `ignored`  — keys the YAML carries that the current signature does not read
                   (`distance` is the one that matters historically).
    * `defaulted`— keys the signature has that the YAML omits, each with the value
                   that will therefore be used.
    * `pre_filter_fix` — True when `boundary_padding` is absent, which dates the
                   file to before the filter fix. See PRE_FILTER_FIX_WARNING.
    """
    cur = current_defaults()
    fp = dict(doc.get("filter_params") or {})
    pp = dict(doc.get("phase_params") or {})

    ignored, defaulted = [], {}
    for section, given, known in (("filter_params", fp, cur["filter_params"]),
                                  ("phase_params", pp, cur["phase_params"])):
        for k in sorted(given):
            if k not in known:
                ignored.append(f"{section}.{k}")
        for k in sorted(known):
            if k not in given:
                defaulted[f"{section}.{k}"] = known[k]

    return {
        "ignored": ignored,
        "defaulted": defaulted,
        "pre_filter_fix": "boundary_padding" not in fp,
        "pre_filter_fix_warning": PRE_FILTER_FIX_WARNING,
    }


def historical_bad_cases(doc: dict) -> dict | None:
    """The YAML's own `evaluation` block, as a LABELLED HISTORICAL ANNOTATION.

    Returned so a column can display what the author marked at the time and when.
    It is never a metric: these marks were made in different weeks with different
    understanding of the problem, and comparing two of them compares two
    inspections, not two configurations. Callers must render it as annotation.
    """
    ev = doc.get("evaluation")
    if not isinstance(ev, dict):
        return None
    return {
        "bad_cases": list(ev.get("bad_cases") or []),
        "bad_cases_count": ev.get("bad_cases_count"),
        "total_cyclones": ev.get("total_cyclones"),
        "timestamp": (doc.get("metadata") or {}).get("timestamp"),
        "note": "anotação histórica — marcação visual feita na época desta "
                "configuração, com outro conhecimento do problema. NÃO é métrica "
                "de comparação entre colunas.",
    }


# ── the column ────────────────────────────────────────────────────────────────
@dataclass
class ColumnSpec:
    """One benchmark column: a configuration plus where it came from."""
    name: str
    doc: dict
    origin: str                      # "sidebar" | "upload" | "configs" | "snapshot"
    origin_name: str = ""
    source_sha256: str | None = None  # sha256 of the ORIGINAL yaml text, if any
    edited: bool = False
    snapshot: dict | None = None      # set for a frozen published-version column

    def effective_sha256(self) -> str:
        """Hash of the config as it will actually run (post-edit)."""
        return sha256_text(yaml.safe_dump(self.doc, sort_keys=True))

    def header(self) -> dict:
        """The five mandatory header items."""
        if self.snapshot is not None:
            snap = self.snapshot["snapshot"]
            return {
                "config_sha256": self.source_sha256 or "—",
                "config_sha256_display": f"{(self.source_sha256 or '—')[:12]}"
                                         if self.source_sha256 else "—",
                "code_commit": f"published {snap['cyclophaser_version']} "
                               f"(PyPI wheel, not this checkout)",
                "ignored": [],
                "defaulted": {},
                "pre_filter_fix": True,
                "pre_filter_fix_warning": (
                    "coluna de referência congelada: "
                    f"cyclophaser {snap['cyclophaser_version']} publicada, rodada "
                    "com os DEFAULTS do pacote daquela versão, em ambiente isolado. "
                    "Aquela versão não tem `boundary_padding` — a convolução do "
                    "filtro preenche com zeros."),
                "historical": None,
                "frozen_snapshot": snap,
            }
        audit = signature_audit(self.doc)
        return {
            "config_sha256": ("editado na sessão" if self.edited
                              else (self.source_sha256 or "—")),
            "config_sha256_display": ("editado na sessão" if self.edited
                                      else (self.source_sha256 or "—")[:12]),
            "code_commit": git_head(),
            "ignored": audit["ignored"],
            "defaulted": audit["defaulted"],
            "pre_filter_fix": audit["pre_filter_fix"],
            "pre_filter_fix_warning": audit["pre_filter_fix_warning"],
            "historical": historical_bad_cases(self.doc),
            "frozen_snapshot": None,
        }


def load_config_text(text: str) -> dict:
    doc = yaml.safe_load(text) or {}
    if not isinstance(doc, dict):
        raise ValueError("YAML root must be a mapping.")
    return doc


def _config_order(path: Path):
    """Numeric order, so params-2 sorts before params-10 (lexicographic does not)."""
    m = re.search(r"(\d+)(?=\.yaml$)", path.name)
    return (int(m.group(1)) if m else 10**6, path.name)


def available_configs() -> list[Path]:
    """The calibration configurations, in the order they were produced."""
    if not CONFIGS_DIR.is_dir():
        return []
    return sorted(CONFIGS_DIR.glob("*.yaml"), key=_config_order)


def available_snapshots() -> list[Path]:
    return sorted(SNAPSHOT_DIR.glob("v*.json")) if SNAPSHOT_DIR.is_dir() else []


def load_snapshot(path: Path) -> dict:
    import json
    return json.loads(Path(path).read_text())


# ── running a column ──────────────────────────────────────────────────────────
def phase_runs_from_periods(periods) -> list[tuple[str, int, int]]:
    """[(phase, start, end_inclusive), ...] over normalised names."""
    names = [normalize_phase(str(x)) for x in periods]
    out, prev, start = [], None, 0
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append((prev, start, i - 1))
            prev, start = n, i
    if prev is not None:
        out.append((prev, start, len(names) - 1))
    return out


def run_series(pv: dict, gp: dict, values) -> dict:
    """Detector output for ONE series, reduced to what a cell needs.

    A raised exception is recorded, never swallowed: a column that cannot be
    computed on a series must say so in that cell rather than silently skip it.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            res = get_periods(vort, **gp)
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "runs": None,
                "z": None, "starts": None}
    runs = phase_runs_from_periods(res["periods"])
    return {
        "error": None,
        "runs": runs,
        "starts": [(p, a) for p, a, _ in runs],
        "z": pd.Series(vort.vorticity_smoothed2.values,
                       index=pd.RangeIndex(len(values))),
    }


def snapshot_series(snapshot: dict, sid: str) -> dict:
    """The same reduced shape as `run_series`, read from a frozen snapshot file."""
    rec = (snapshot.get("records") or {}).get(sid)
    if rec is None:
        return {"error": "not in snapshot", "runs": None, "starts": None, "z": None}
    if rec.get("error"):
        # Recorded as a failure at snapshot time, carried through as one.
        return {"error": f"falha registrada no snapshot: "
                         f"{rec['error'].splitlines()[-1]}",
                "runs": None, "starts": None, "z": None}
    runs = [(p, a, b) for p, a, b in rec["phases"]]
    return {"error": None, "runs": runs,
            "starts": [(p, a) for p, a, _ in runs], "z": None}


class ColumnRunner:
    """Runs columns over series, caching by (effective config sha256, series id).

    The cache is per-instance and keyed on the config's own hash, so two columns
    that happen to carry the same configuration share the work, and editing a
    column invalidates only that column.
    """

    def __init__(self):
        self._cache: dict[tuple[str, str], dict] = {}

    def run(self, spec: ColumnSpec, series: dict[str, pd.Series]) -> dict[str, dict]:
        if spec.snapshot is not None:
            return {sid: snapshot_series(spec.snapshot, sid) for sid in series}
        pv, gp = split_config(spec.doc)
        key0 = spec.effective_sha256()
        out = {}
        for sid, values in series.items():
            k = (key0, sid)
            if k not in self._cache:
                self._cache[k] = run_series(pv, gp, values)
            out[sid] = self._cache[k]
        return out


# ── series population ─────────────────────────────────────────────────────────
def load_all_series() -> tuple[dict[str, pd.Series], dict[str, str]]:
    """All 63 records: 51 real + 12 frozen synthetic. {id: Series}, {id: source}."""
    real = load_real_series()
    synth, _names = load_synthetic_series()
    source = {sid: "real" for sid in real}
    source.update({sid: "synthetic" for sid in synth})
    return {**real, **synth}, source


def split_membership() -> dict[str, str]:
    """{series_id: 'train'|'test'} from the frozen split."""
    sp = read_split()
    out = {sid: "train" for sid in sp["train"]}
    out.update({sid: "test" for sid in sp["test"]})
    return out


# ── the two measurements ──────────────────────────────────────────────────────
def sequence_metrics(results: dict[str, dict], labels: dict[str, dict],
                     ids) -> dict:
    """`score_phase_sequences` over the given ids. Named instrument, no blending."""
    records = [labels[s] for s in ids if s in labels]
    detected = {s: results[s]["starts"] for s in ids
                if s in results and results[s]["starts"] is not None}
    if not records:
        return {"instrument": SEQUENCE_INSTRUMENT, "n_series": 0,
                "n_sequence_match": 0, "sequence_match_rate": None,
                "n_boundaries": 0, "n_boundaries_hit": 0, "boundary_hit_rate": None,
                "per_phase": {}}
    m = score_phase_sequences(records, detected)
    m["instrument"] = SEQUENCE_INSTRUMENT
    return m


def mature_metrics(results: dict[str, dict], labels: dict[str, dict], ids) -> dict:
    """Mature-block pairing via item19_core.pair_by_overlap, fixed margin 6.

    Never reconfigures item19_core; only its pairing function is called, with
    this column's own detected blocks.
    """
    n = hit = 0
    rows = []
    for sid in ids:
        rec, res = labels.get(sid), results.get(sid)
        if rec is None or res is None or res["runs"] is None:
            continue
        lab_mat = [(p["start_idx"],
                    (rec["phases"][k + 1]["start_idx"] - 1)
                    if k + 1 < len(rec["phases"]) else rec["n_steps"] - 1)
                   for k, p in enumerate(rec["phases"])
                   if normalize_phase(p["phase"]) == "mature"]
        if not lab_mat:
            continue
        first = lab_mat[0]
        det = [(a, b) for p, a, b in res["runs"] if p == "mature"]
        paired, ov = pair_by_overlap(det, first)
        n += 1
        if paired is None:
            rows.append({"id": sid, "d_start": None, "d_end": None, "hit": False})
            continue
        ds, de = paired[0] - first[0], paired[1] - first[1]
        ok = abs(ds) <= MATURE_MARGIN and abs(de) <= MATURE_MARGIN
        hit += bool(ok)
        rows.append({"id": sid, "d_start": ds, "d_end": de, "hit": bool(ok),
                     "overlap": ov})
    return {
        "instrument": MATURE_INSTRUMENT,
        "margin": MATURE_MARGIN,
        "n": n,
        "n_hit": hit,
        "hit_rate": (hit / n) if n else None,
        "rows": rows,
    }


def metrics_by_split(results: dict[str, dict], labels: dict[str, dict],
                     selected_ids, membership: dict[str, str]) -> dict:
    """Both measurements, TRAIN and TEST kept in separate blocks.

    The leakage rule is enforced here rather than left to the caller: a test
    aggregate is computed into its own labelled block and is never added into
    the train one.
    """
    train_ids = [s for s in selected_ids if membership.get(s) == "train"]
    test_ids = [s for s in selected_ids if membership.get(s) == "test"]
    return {
        "train": {
            "ids": train_ids,
            "sequence": sequence_metrics(results, labels, train_ids),
            "mature": mature_metrics(results, labels, train_ids),
        },
        "test": {
            "ids": test_ids,
            "sequence": sequence_metrics(results, labels, test_ids),
            "mature": mature_metrics(results, labels, test_ids),
        },
    }


def labels_for_display() -> dict[str, dict]:
    try:
        return read_labels()
    except Exception:
        return {}


def label_runs_for(rec: dict) -> list[tuple[str, int, int]]:
    """A label record as [(phase, start, end_inclusive), ...]."""
    ph, n = rec["phases"], rec["n_steps"]
    out = []
    for k, p in enumerate(ph):
        s = p["start_idx"]
        e = (ph[k + 1]["start_idx"] - 1) if k + 1 < len(ph) else n - 1
        out.append((normalize_phase(p["phase"]), s, e))
    return out
