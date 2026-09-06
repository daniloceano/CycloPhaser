"""Pure helpers for the manual-labelling front — no Streamlit, no I/O side effects
beyond the two explicit file writers at the bottom.

Everything the labelling tab, the split builder and the evaluation script share
lives here so all three agree by construction and so each piece is testable
without launching a browser.

Why this module exists at all
-----------------------------
There is no ground truth for the incipient boundary. The synthetic suite derives
one from the segment list, and that derivation is wrong: `shape="sine"` is a
half-period cosine ramp with ZERO derivative at both ends, so an It or D segment
opening in sine *starts flat* and produces a real incipient plateau that the
segment list does not express. IcDItMD_noisy (D in sine) and DItMD_noisy (D in
linear) have the same segments and different answers. Four cases put the
incipient phase and the phase after it both at index 0, which is not a boundary
at all. The 51 real tracks carry no label whatsoever.

So the labels come from a human. This module is the plumbing around that.
"""

from __future__ import annotations

import hashlib
import os
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CALIBRATION_DATA_DIR = REPO_ROOT / "tests" / "calibration_data"
SYNTHETIC_DIR = REPO_ROOT / "tests" / "synthetic"
LABELS_DIR = Path(__file__).resolve().parent
SPLIT_PATH = LABELS_DIR / "split.yaml"
LABELS_PATH = LABELS_DIR / "manual_labels.yaml"

# Seeds are frozen in code AND written into the artefacts they produce. Changing
# either number invalidates the corresponding artefact, which is the point: a
# split redrawn after seeing results is not a test set any more.
SPLIT_SEED = 20260905
QUEUE_SEED = 20260905

# Bumped from 1 when a label stopped being a single incipient boundary and
# became the cyclone's whole phase sequence. The artefact was still empty at the
# bump, so there is nothing to migrate — but a working copy can hold schema-1
# records from a session that predates it, and those are excluded loudly rather
# than silently skipped (see `is_legacy_record`).
LABELS_SCHEMA = 2

VERDICT_KINDS = ("boundary", "none", "ambiguous")

# The five phases, and the palette the rest of the project already draws them in.
# Duplicated here rather than imported from `cyclophaser.plots` on purpose: the
# labelling tab must not be able to reach the package at all (see the module
# docstring of tools/calibration_app/label_tab.py), and a five-entry colour dict
# is a cheap thing to restate. tests/test_manual_labels.py parses plots.py and
# fails if the two ever drift apart, so the duplication cannot rot.
PHASE_ORDER = ("incipient", "intensification", "mature", "decay", "residual")
PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "gray",
}


def normalize_phase(name: str) -> str:
    """'intensification 2' -> 'intensification'.

    The detector numbers repeated phases; a label records the phase and lets its
    POSITION in the sequence carry the repetition, so the two have to be compared
    on the bare name.
    """
    return str(name).rstrip(" 0123456789").strip()

# Length strata for the stratified split, as (label, lo_inclusive, hi_exclusive).
# Measured on tests/calibration_data: 10 / 22 / 19 tracks respectively.
STRATA = (("short", 0, 60), ("medium", 60, 120), ("long", 120, 10**9))

TRAIN_FRACTION = 0.70


# ── series identity ──────────────────────────────────────────────────────────

def series_sha256(values) -> str:
    """Content hash of the RAW series values, for staleness detection.

    Hashes the float64 bytes of the values only — not the index, not the dtype
    name, not any metadata — so the hash answers exactly one question: "is this
    the data that was looked at when the label was written?". If the underlying
    CSV or the synthetic generator changes, the stored label becomes visibly
    stale instead of silently wrong.
    """
    import numpy as np
    arr = np.asarray(values, dtype="float64")
    return hashlib.sha256(arr.tobytes()).hexdigest()


def opaque_synthetic_id(case_name: str) -> str:
    """Stable, answer-free id for a synthetic case.

    `ItMD_clean`, `IcDItMD_noisy` and friends spell the expected phase sequence
    in the name — showing that name in the labelling queue would hand the
    labeller the answer and make the label circular. A hash of the name is
    stable across runs (so labels stay matched to their case) and carries none
    of it.

    Derived rather than stored in research/labels/ on purpose: a mapping file
    sitting next to manual_labels.yaml would be the answer key, one directory
    listing away from the person who must not see it. The evaluation script
    recomputes this from tests/synthetic/cases.py when it needs to resolve an id.
    """
    return "s" + hashlib.sha256(case_name.encode("utf-8")).hexdigest()[:8]


# ── loading the series populations ───────────────────────────────────────────

def load_real_series(data_dir: Path | None = None) -> dict[str, pd.Series]:
    """The 51 calibration tracks, as {track_id: raw vorticity Series}."""
    d = Path(data_dir) if data_dir is not None else CALIBRATION_DATA_DIR
    out = {}
    for p in sorted(d.glob("*.csv")):
        df = pd.read_csv(p, sep=";", index_col="time", parse_dates=True)
        out[p.stem] = df["min_max_zeta_850"].astype("float64")
    return out


def load_synthetic_series(synthetic_dir: Path | None = None):
    """The synthetic suite as {opaque_id: Series}, plus {opaque_id: case_name}.

    Loaded BY FILE PATH under a private package name for the same reason
    tools/calibration_app/app.py does it: `import tests.synthetic.cases` depends
    on a top-level name as generic as `tests` resolving to this repo, which is
    not guaranteed once anything else leaks a `tests` package into the
    environment.
    """
    import importlib.util
    import sys
    import types

    d = Path(synthetic_dir) if synthetic_dir is not None else SYNTHETIC_DIR
    cases_py = d / "cases.py"
    if not cases_py.is_file():
        return {}, {}

    pkg_name = "_cyclophaser_labels_synthetic"
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(d)]
    sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(f"{pkg_name}.cases", cases_py)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    series, names = {}, {}
    for case_name, case in mod.CASES.items():
        oid = opaque_synthetic_id(case_name)
        series[oid] = case["series"].astype("float64")
        names[oid] = case_name
    return series, names


# ── Piece 1: the frozen, stratified split ────────────────────────────────────

def stratum_of(n: int) -> str:
    for label, lo, hi in STRATA:
        if lo <= n < hi:
            return label
    raise ValueError(f"length {n} falls in no stratum")


def stratified_split(lengths: dict[str, int], seed: int = SPLIT_SEED,
                     train_fraction: float = TRAIN_FRACTION) -> dict:
    """Split ids into train/test, stratified by series length.

    Stratified because the three length bands are not interchangeable: a 30-step
    track and a 259-step track give the incipient detector very different amounts
    of signal to work with, and an unstratified 70/30 draw over 51 items can
    easily leave a band nearly empty in the test set.

    Deterministic given (lengths, seed): the ids are sorted before shuffling, so
    the result does not depend on dict insertion order.
    """
    rng = random.Random(seed)
    strata: dict[str, list[str]] = {label: [] for label, _, _ in STRATA}
    for sid in sorted(lengths):
        strata[stratum_of(lengths[sid])].append(sid)

    train, test, summary = [], [], {}
    for label, _, _ in STRATA:
        members = list(strata[label])
        rng.shuffle(members)
        n_train = round(len(members) * train_fraction)
        tr, te = members[:n_train], members[n_train:]
        train += tr
        test += te
        summary[label] = {"n": len(members), "n_train": len(tr), "n_test": len(te)}
    return {"train": sorted(train), "test": sorted(test), "strata": summary}


def build_split_document(real_lengths: dict[str, int], synthetic_ids,
                         seed: int = SPLIT_SEED) -> dict:
    """The full split.yaml payload.

    The 12 synthetic series are NOT drawn: they all go to train, tagged
    source: synthetic. They are a designed population, not a sample of anything,
    and holding three of them out would buy no generalisation evidence while
    costing a quarter of the only series whose construction is known.
    """
    sp = stratified_split(real_lengths, seed=seed)
    return {
        "seed": seed,
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "train_fraction": TRAIN_FRACTION,
        "strata": sp["strata"],
        "synthetic_in_train": True,
        "train": sp["train"] + sorted(synthetic_ids),
        "test": sp["test"],
        "source": ({sid: "real" for sid in sp["train"] + sp["test"]}
                   | {sid: "synthetic" for sid in sorted(synthetic_ids)}),
    }


def read_split(path: Path | None = None) -> dict:
    p = Path(path) if path is not None else SPLIT_PATH
    with open(p) as fh:
        return yaml.safe_load(fh)


# ── Piece 2: the labels artefact ─────────────────────────────────────────────

def validate_verdict(verdict: dict) -> dict:
    """Normalise and check one verdict, raising on anything malformed.

    Rejecting early matters more here than usual: a silently mistyped verdict
    would not fail until evaluation, by which time the series is no longer on
    screen and the labeller cannot say what they meant.
    """
    if not isinstance(verdict, dict):
        raise TypeError(f"verdict must be a mapping, got {type(verdict).__name__}")
    kind = verdict.get("kind")
    if kind not in VERDICT_KINDS:
        raise ValueError(f"verdict kind must be one of {VERDICT_KINDS}, got {kind!r}")
    if kind == "boundary":
        if "incipient_end_idx" not in verdict:
            raise ValueError("kind=boundary requires incipient_end_idx")
        idx = int(verdict["incipient_end_idx"])
        if idx < 1:
            # [0, N) with N == 0 is the empty incipient phase, which is what
            # kind=none says; allowing both spellings would split the same
            # judgement across two verdicts and corrupt the refusal counts.
            raise ValueError(
                "incipient_end_idx must be >= 1 (the incipient phase is [0, N); "
                "an empty one is kind=none, not N=0)")
        return {"kind": "boundary", "incipient_end_idx": idx}
    return {"kind": kind}


def validate_phases(phases, n_steps: int | None = None) -> list[dict]:
    """Normalise and check a whole labelled phase sequence.

    A labelled series is an ordered PARTITION of [0, n): phase i runs from its
    own `start_idx` up to the next one's, and the last runs to the end. So:

      * the first phase starts at 0 — the series has to begin in some phase;
      * `start_idx` is strictly increasing, which also forbids the zero-length
        phases the old single-boundary format could express by accident;
      * repeats are allowed (residual -> intensification -> mature -> decay is a
        real life cycle), and the phase's POSITION carries the repetition rather
        than a number in its name.

    Checked eagerly, because a malformed sequence would not fail until evaluation
    — long after the series has left the screen and the labeller could still say
    what they meant.
    """
    if not phases:
        raise ValueError("a labelled series needs at least one phase")
    out, prev = [], None
    for i, ph in enumerate(phases):
        name = normalize_phase(ph.get("phase", ""))
        if name not in PHASE_ORDER:
            raise ValueError(f"unknown phase {ph.get('phase')!r}; expected one of {PHASE_ORDER}")
        idx = int(ph["start_idx"])
        if i == 0 and idx != 0:
            raise ValueError(f"the first phase must start at 0, got {idx}")
        if prev is not None and idx <= prev:
            raise ValueError(
                f"phase starts must strictly increase; {idx} follows {prev}")
        if n_steps is not None and idx >= n_steps:
            raise ValueError(f"start_idx {idx} is past the end of a {n_steps}-step series")
        tol = int(ph.get("tolerance_idx", 0))
        if tol < 0:
            raise ValueError("tolerance_idx must be >= 0")
        out.append({"phase": name, "start_idx": idx, "tolerance_idx": tol})
        prev = idx
    return out


def incipient_verdict_from_phases(phases, n_steps: int) -> tuple[dict, int]:
    """Reduce a phase sequence to the incipient question, and its own margin.

    The full sequence is now the artefact, but the incipient boundary is still
    what this whole front was commissioned to settle, so it is derived back out
    into the same `verdict` shape the evaluation already speaks — rather than
    asked twice and allowed to disagree with the table.

    Returns (verdict, tolerance_idx). The margin is the one attached to the
    boundary that actually ends the incipient phase, not a series-wide number.
    """
    if not phases or phases[0]["phase"] != "incipient":
        return {"kind": "none"}, 0
    if len(phases) == 1:
        # the whole series is incipient; the boundary is its end
        return {"kind": "boundary", "incipient_end_idx": int(n_steps)}, \
            int(phases[0]["tolerance_idx"])
    return ({"kind": "boundary", "incipient_end_idx": int(phases[1]["start_idx"])},
            int(phases[1]["tolerance_idx"]))


def make_label_record(series_id: str, source: str, values, phases,
                      notes: str | None = None, labeled_at: str | None = None,
                      ambiguous: bool = False) -> dict:
    """One labels-file record: the whole phase sequence for one series.

    `values` is the raw series the labeller saw. `verdict` and the top-level
    `tolerance_idx` are DERIVED from `phases` (except `ambiguous`, which is a
    judgement the table cannot express) so that the incipient-specific evaluation
    keeps working without the two ever being able to contradict each other.
    """
    if source not in ("real", "synthetic"):
        raise ValueError(f"source must be 'real' or 'synthetic', got {source!r}")
    n = len(values)
    checked = validate_phases(phases, n_steps=n)
    verdict, tol = incipient_verdict_from_phases(checked, n)
    if ambiguous:
        verdict = {"kind": "ambiguous"}
    rec = {
        "id": str(series_id),
        "source": source,
        "series_sha256": series_sha256(values),
        "labeled_at": labeled_at or datetime.now(timezone.utc)
                        .replace(microsecond=0).isoformat(),
        "n_steps": int(n),
        "phases": checked,
        # Derived from `phases`; kept in the file so the artefact answers the
        # incipient question without every reader having to re-derive it.
        "verdict": validate_verdict(verdict),
        # Per-BOUNDARY rather than per-series, because the subjectivity is not
        # uniform even within one cyclone: an incipient knee can be unmistakable
        # on a track whose mature->decay transition is a long gentle roll.
        "tolerance_idx": int(tol),
    }
    if notes:
        rec["notes"] = str(notes)
    return rec


def read_labels(path: Path | None = None) -> dict[str, dict]:
    """{id: record}. A missing or empty file reads as no labels, not an error —
    the file is committed empty and the suite must pass before any labelling."""
    p = Path(path) if path is not None else LABELS_PATH
    if not p.is_file():
        return {}
    doc = yaml.safe_load(p.read_text()) or {}
    return {r["id"]: r for r in (doc.get("labels") or [])}


def is_legacy_record(rec: dict) -> bool:
    """True for a schema-1 record — one incipient boundary, no phase sequence.

    Such a record cannot be upgraded automatically: the phases it never recorded
    are not recoverable from the boundary it did. It is excluded from scoring and
    named, so the series simply goes back in the queue.
    """
    return "phases" not in rec


def labels_document(records: dict[str, dict]) -> dict:
    return {
        "schema": LABELS_SCHEMA,
        "updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "n_labels": len(records),
        "labels": [records[k] for k in sorted(records)],
    }


def atomic_write_text(path: Path, text: str) -> None:
    """Write via tmp file in the SAME directory + os.replace.

    The labelling session is a browser tab that will be closed mid-queue, and a
    partially written YAML would take every earlier label with it. Same
    directory so the rename stays within one filesystem (os.replace is only
    atomic there); fsync before the rename so a crash cannot leave the new name
    pointing at unflushed bytes.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_labels(records: dict[str, dict], path: Path | None = None) -> None:
    p = Path(path) if path is not None else LABELS_PATH
    atomic_write_text(p, yaml.safe_dump(labels_document(records), sort_keys=False,
                                        default_flow_style=False, allow_unicode=True))


def upsert_label(record: dict, path: Path | None = None) -> dict[str, dict]:
    """Save one label immediately, rewriting the whole file atomically.

    Rewriting everything on every save is O(n) in a file of at most 63 short
    records — irrelevant — and buys the guarantee that the file on disk is always
    a complete, parseable document.
    """
    p = Path(path) if path is not None else LABELS_PATH
    records = read_labels(p)
    records[record["id"]] = record
    write_labels(records, p)
    return records


# ── Piece 3: the labelling queue ─────────────────────────────────────────────

def build_queue(series_ids, seed: int = QUEUE_SEED) -> list[str]:
    """Shuffled, reproducible presentation order.

    Shuffled rather than sorted by id because the ids are chronological for the
    real tracks: labelling them in order would align the labeller's fatigue and
    drifting criteria with the identifier, and any systematic drift would then
    look like a real time-dependent effect in the evaluation.

    Sorted before shuffling so the order depends only on the seed and the set of
    ids, never on how the caller happened to build the collection.
    """
    ids = sorted(series_ids)
    rng = random.Random(seed)
    rng.shuffle(ids)
    return ids


def queue_position(queue: list[str], labeled_ids) -> int:
    """Index of the first unlabelled item — where a resumed session picks up.

    Returns len(queue) when everything is labelled.
    """
    done = set(labeled_ids)
    for i, sid in enumerate(queue):
        if sid not in done:
            return i
    return len(queue)


# ── Piece 4: metrics ─────────────────────────────────────────────────────────

def _boundary_idx(verdict: dict):
    return verdict.get("incipient_end_idx") if verdict.get("kind") == "boundary" else None


def score_labels(records, detected: dict[str, int | None]) -> dict:
    """Compare detector output against manual labels.

    `detected[id]` is the index where the detected incipient phase ENDS (i.e. the
    incipient phase is [0, N)), or None when the detector produced no incipient
    phase at all. `records` is an iterable of label records.

    Reported separately rather than folded into one number:

    * hit rate within each label's OWN tolerance_idx — the headline;
    * MAE and worst case on the raw |detected - labelled| distance, alongside,
      because a hit rate under a per-label margin can be gamed by wide margins
      and says nothing about how wrong the misses are;
    * refusal, both directions — the detector agreeing there is no incipient
      phase, and the detector refusing where the label says there is a boundary.
      These are a different kind of error from being off by k steps and must not
      be averaged with them.

    kind=ambiguous is excluded from the hit rate and the MAE (there is nothing to
    be near) but kept in the refusal accounting, where "the detector also
    declined" is still informative.
    """
    n_boundary = n_hit = 0
    errors: list[int] = []
    detector_missing_on_boundary = 0       # label says boundary, detector says none
    n_none = n_none_agreed = 0             # label says none, detector agrees
    n_ambiguous = n_ambiguous_detector_none = 0
    n_unscored = 0                          # labelled but the detector had no entry

    for rec in records:
        sid = rec["id"]
        if sid not in detected:
            n_unscored += 1
            continue
        det = detected[sid]
        kind = rec["verdict"]["kind"]
        if kind == "boundary":
            n_boundary += 1
            if det is None:
                detector_missing_on_boundary += 1
                continue
            err = abs(int(det) - int(rec["verdict"]["incipient_end_idx"]))
            errors.append(err)
            if err <= int(rec["tolerance_idx"]):
                n_hit += 1
        elif kind == "none":
            n_none += 1
            if det is None:
                n_none_agreed += 1
        else:
            n_ambiguous += 1
            if det is None:
                n_ambiguous_detector_none += 1

    return {
        "n_scored": n_boundary + n_none + n_ambiguous,
        "n_unscored": n_unscored,
        # hit rate is over ALL boundary verdicts, so a detector that refuses
        # instead of answering is penalised rather than skipped
        "n_boundary": n_boundary,
        "n_hit": n_hit,
        "hit_rate": (n_hit / n_boundary) if n_boundary else None,
        "mae": (sum(errors) / len(errors)) if errors else None,
        "worst": max(errors) if errors else None,
        "n_compared": len(errors),
        "detector_missing_on_boundary": detector_missing_on_boundary,
        "n_none": n_none,
        "n_none_agreed": n_none_agreed,
        "none_agreement_rate": (n_none_agreed / n_none) if n_none else None,
        "n_ambiguous": n_ambiguous,
        "n_ambiguous_detector_none": n_ambiguous_detector_none,
    }


def phase_sequence(record) -> list[tuple[str, int]]:
    """A label's sequence as [(phase, start_idx), ...]."""
    return [(p["phase"], int(p["start_idx"])) for p in record["phases"]]


def score_phase_sequences(records, detected: dict[str, list[tuple[str, int]]]) -> dict:
    """Compare whole labelled phase sequences against detected ones.

    Two failures live here and they are NOT commensurable, so they are never
    averaged together:

    * **Sequence mismatch** — the detector found a different set of phases in a
      different order (an extra residual, a missing mature). No boundary-by-
      boundary distance is meaningful across a mismatch: pairing the 3rd labelled
      boundary with the 3rd detected one when the sequences differ compares two
      different transitions and manufactures a number. These series are counted
      and set aside.
    * **Boundary error** — same sequence, boundaries in the wrong place. Only
      these produce distances, per phase, each against its own tolerance.

    The first phase's start is excluded throughout: it is 0 by construction on
    both sides and would pad every hit rate with free agreement.
    """
    per_phase: dict[str, dict] = {}
    n_series = n_match = n_mismatch = n_unscored = 0

    for rec in records:
        sid = rec["id"]
        if sid not in detected:
            n_unscored += 1
            continue
        n_series += 1
        lab = phase_sequence(rec)
        det = [(normalize_phase(p), int(i)) for p, i in detected[sid]]
        if [p for p, _ in lab] != [p for p, _ in det]:
            n_mismatch += 1
            continue
        n_match += 1
        for k in range(1, len(lab)):
            phase, lidx = lab[k]
            didx = det[k][1]
            tol = int(rec["phases"][k]["tolerance_idx"])
            err = abs(didx - lidx)
            slot = per_phase.setdefault(
                phase, {"n": 0, "n_hit": 0, "errors": []})
            slot["n"] += 1
            slot["errors"].append(err)
            if err <= tol:
                slot["n_hit"] += 1

    for slot in per_phase.values():
        errs = slot.pop("errors")
        slot["mae"] = (sum(errs) / len(errs)) if errs else None
        slot["worst"] = max(errs) if errs else None
        slot["hit_rate"] = (slot["n_hit"] / slot["n"]) if slot["n"] else None

    all_n = sum(v["n"] for v in per_phase.values())
    all_hit = sum(v["n_hit"] for v in per_phase.values())
    return {
        "n_series": n_series,
        "n_unscored": n_unscored,
        "n_sequence_match": n_match,
        "n_sequence_mismatch": n_mismatch,
        "sequence_match_rate": (n_match / n_series) if n_series else None,
        "per_phase": per_phase,
        "n_boundaries": all_n,
        "n_boundaries_hit": all_hit,
        "boundary_hit_rate": (all_hit / all_n) if all_n else None,
    }
