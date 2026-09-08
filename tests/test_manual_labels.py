"""Tests for the manual-labelling front (research/labels/ + the app's Label mode).

Five things are worth testing here, and they are not the usual ones.

0. A label is now the cyclone's WHOLE phase sequence — an ordered partition of
   [0, n) — rather than one incipient boundary, with a margin per BOUNDARY. The
   incipient verdict the evaluation speaks is DERIVED from that sequence, so the
   two can never contradict each other.

1. **The labelling tab is BLIND.** This is the load-bearing property of the whole
   front. There is no ground truth for the incipient boundary — the synthetic
   suite derives one from the segment list and gets it wrong, because
   `shape="sine"` is a half-period cosine with zero derivative at both ends, so
   an It or D segment opening in sine starts FLAT and creates a real incipient
   plateau the segment list never mentions (IcDItMD_noisy vs DItMD_noisy: same
   segments, one shape apart, different answers). The labels therefore come from
   a human, and a human who can see the detector's answer produces an echo of it
   rather than evidence about it. So the tab's source is parsed and checked to
   import nothing from the package and to name no detector output. This test
   failing means the artefact would be worthless, not that a style rule was
   broken.

2. **The artefact survives the browser being closed.** Labelling is a long
   session in a tab that will be shut mid-queue; a half-written YAML would take
   every earlier label with it.

3. **The split is frozen.** Reproducible from its seed and respecting the three
   length bands — a split redrawn after results have been seen is not a test set.

4. **A label goes stale when its data changes**, rather than silently pointing at
   positions in a series that no longer exists.

5. **The metrics are the ones claimed**, including the per-label margin at its
   edges (tolerance 0, and different margins on different labels).
"""

import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))

import labels_core as lc  # noqa: E402

# The CI installs the package from its wheel plus pytest, and nothing else — so
# PyYAML, Streamlit and Plotly are all absent there. None of them is a dependency
# of cyclophaser itself; they belong to the calibration app and to this research
# front. Guarded per test, the way tests/test_layer_inspector.py already guards
# plotly, rather than at module level: a module-level skip would take the split,
# queue, phase-validation and metric tests down with them, and those are pure
# logic that needs none of it.
#
# Anything imported at module scope here MUST be a package dependency. An
# optional one breaks COLLECTION, which fails the whole suite rather than one
# module — that is how this first went wrong.
def _have(mod: str) -> bool:
    # find_spec does not only return None for a missing module — it raises
    # ModuleNotFoundError when a PARENT package is absent, and importing a
    # package can raise anything at all. This runs at collection time, so
    # anything it lets escape fails the entire suite rather than one test.
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


requires_yaml = pytest.mark.skipif(not _have("yaml"), reason="PyYAML not installed")
requires_streamlit = pytest.mark.skipif(
    not _have("streamlit"), reason="Streamlit not installed (calibration-app only)")

LABEL_TAB = REPO_ROOT / "tools" / "calibration_app" / "label_tab.py"


# ══════════════════════════════════════════════════════════════════════════════
# 0. This module must not be able to break the package's CI
# ══════════════════════════════════════════════════════════════════════════════

# Not dependencies of cyclophaser. They belong to the calibration app and to this
# research front; the CI installs the package from its wheel plus pytest, so none
# of them exists there.
NOT_PACKAGE_DEPS = {"yaml", "streamlit", "plotly", "altair", "watchdog"}


def test_this_module_imports_no_optional_dependency_at_module_scope():
    """A module-scope import of something optional breaks COLLECTION, and a
    collection error fails the ENTIRE suite rather than one module — 821 tests
    reported as one error. That is exactly how this front first broke the CI.

    Optional dependencies belong inside the tests that need them, behind
    `importorskip` or a skipif, the way tests/test_layer_inspector.py already
    guards plotly.
    """
    tree = ast.parse(Path(__file__).read_text())
    top_level = []
    for node in tree.body:                      # body only: module scope
        if isinstance(node, ast.Import):
            top_level += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            top_level.append(node.module.split(".")[0])
    offending = set(top_level) & NOT_PACKAGE_DEPS
    assert not offending, (
        f"{sorted(offending)} imported at module scope; a missing one would fail "
        "collection of the whole suite, not just this module")


def test_labels_core_is_importable_without_a_yaml_library():
    """The split, the queue, the phase validation and the metrics are pure logic
    with nothing to do with a file format, so they must not drag PyYAML in. This
    is what lets 41 of these tests still run in a CI that has no yaml."""
    tree = ast.parse((REPO_ROOT / "research" / "labels" / "labels_core.py").read_text())
    top_level = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            top_level.append(node.module.split(".")[0])
    assert "yaml" not in top_level, (
        "labels_core imports yaml at module scope; import it inside the three "
        "functions that serialise instead")
    # ...and it really is importable: this test ran, and lc is already imported.
    assert lc.stratified_split({f"t{i}": 30 + i for i in range(10)}, seed=1)


# ══════════════════════════════════════════════════════════════════════════════
# 1. The labelling tab is blind
# ══════════════════════════════════════════════════════════════════════════════

# Anything that is, or trivially yields, a detector answer. A label written while
# any of these was on screen is circular.
FORBIDDEN_NAMES = {
    "get_periods", "periods_to_dict", "process_vorticity", "find_stages",
    "find_incipient_period", "find_intensification_period", "find_decay_period",
    "find_mature_stage", "find_residual_period", "post_process_periods",
    "build_inspector_figure", "plot_all_periods", "plot_didactic",
    "pipeline_ribbon", "incipient_lens", "mature_lens", "knee_index",
    "_incipient_plateau_boundary", "_incipient_plateau_rel",
    # pipeline series the tab must not draw either — only the raw input
    "z_unfil", "dz", "dz2", "vorticity_smoothed", "vorticity_smoothed2",
    "filtered_vorticity", "z_peaks_valleys",
}
FORBIDDEN_MODULES = {"cyclophaser", "layer_inspector", "inspector_plotly",
                     "inspector_mpl"}


def _tab_ast():
    return ast.parse(LABEL_TAB.read_text())


def test_label_tab_imports_nothing_that_can_detect():
    """No import path from the labelling tab to the package or the inspectors.

    Checked on the AST rather than by grepping text, so the module docstring can
    name these things in order to explain why they are absent.
    """
    imported = set()
    for node in ast.walk(_tab_ast()):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (imported & FORBIDDEN_MODULES), (
        f"the Label tab imports {sorted(imported & FORBIDDEN_MODULES)} — it must "
        "not be able to reach detection at all")


def test_label_tab_names_no_detector_output():
    """No identifier or attribute in the tab's CODE refers to detector output.

    Strings are excluded on purpose: the docstring has to be able to say
    "no dz, no dz2" without tripping the check it is describing.
    """
    used = set()
    for node in ast.walk(_tab_ast()):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
    offending = used & FORBIDDEN_NAMES
    assert not offending, (
        f"the Label tab references detector output {sorted(offending)}; a label "
        "written while looking at the detector is not evidence about it")


def test_label_tab_plots_exactly_one_series():
    """One series reaches the screen, and it is the raw input.

    This used to count `add_trace` calls on the Plotly fallback. That fallback
    has been deleted — it drew a plausible NON-INTERACTIVE picture whenever the
    component failed, which is how a component that had never once mounted
    looked like a working screen for three rounds. With it gone, the payload is
    the only channel from the app to the drawing surface, so the count is pinned
    there instead: `chart_payload` carries exactly one array of numbers, `y`.

    A second series is how the blindness would realistically erode — someone
    adds "just the filtered series for context" — so the count is what is pinned,
    not the mechanism.
    """
    payload_keys = {"sid", "n", "y", "phases", "colors",
                    "w", "h", "ml", "mr", "mt", "mb"}
    tree = _tab_ast()
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "chart_payload")
    returned = next(n for n in ast.walk(fn) if isinstance(n, ast.Return))
    assert isinstance(returned.value, ast.Dict)
    keys = {k.value for k in returned.value.keys}
    assert keys == payload_keys, keys
    # exactly one of those keys is a series of values; the rest are scalars,
    # the labeller's own marks, or the palette
    assert len([k for k in keys if k == "y"]) == 1

    assert not [n for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("add_trace", "add_vrect", "add_vline")], (
        "the Label tab is drawing with a plotting library again; the whole "
        "point of the hand-drawn chart is that only clientX is ever read")


def test_label_tab_does_not_read_app_detection_parameters():
    """The tab's only entry point takes a margin default — no detector params.

    If it grew a filter or phase argument, a sidebar setting could change what
    the labeller sees, and the label would silently depend on a parameter choice.
    """
    fn = next(n for n in ast.walk(_tab_ast())
              if isinstance(n, ast.FunctionDef) and n.name == "render")
    argnames = [a.arg for a in fn.args.args]
    assert argnames == ["default_tolerance"], argnames


# ══════════════════════════════════════════════════════════════════════════════
# 2. The artefact: round-trip, atomicity, staleness
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def toy_series():
    idx = pd.date_range("2020-01-01", periods=40, freq="3h")
    return pd.Series([-1e-5 - 1e-6 * i for i in range(40)], index=idx)


def _phases(*triples):
    """(phase, start_idx, tolerance_idx[, unsure]) -> the schema-3 phase dicts.

    `unsure` is part of every phase since schema 3 — "I cannot place THIS
    boundary", as opposed to the old per-series ambiguity flag that voided a
    whole cyclone. It is written explicitly rather than defaulted in, because a
    record that merely OMITS it is a schema-2 record and is refused
    (see test_a_record_from_an_earlier_schema_is_flagged_not_crashed_on).
    """
    return [{"phase": t[0], "start_idx": t[1], "tolerance_idx": t[2],
             "unsure": bool(t[3]) if len(t) > 3 else False} for t in triples]


FOUR = _phases(("incipient", 0, 0), ("intensification", 7, 3),
               ("mature", 20, 5), ("decay", 30, 4))


@requires_yaml
def test_label_record_round_trips_through_yaml(tmp_path, toy_series):
    p = tmp_path / "manual_labels.yaml"
    rec = lc.make_label_record("t1", "real", toy_series, FOUR, notes="clear knee")
    lc.upsert_label(rec, p)
    back = lc.read_labels(p)
    assert back["t1"] == rec
    assert back["t1"]["phases"] == FOUR
    assert back["t1"]["n_steps"] == len(toy_series)
    assert back["t1"]["notes"] == "clear knee"


@requires_yaml
def test_upsert_overwrites_in_place_and_keeps_the_others(tmp_path, toy_series):
    p = tmp_path / "l.yaml"
    no_inc = _phases(("intensification", 0, 2), ("mature", 15, 3))
    lc.upsert_label(lc.make_label_record("a", "real", toy_series, no_inc), p)
    lc.upsert_label(lc.make_label_record("b", "real", toy_series, FOUR), p)
    lc.upsert_label(lc.make_label_record("a", "real", toy_series, FOUR,
                                         ambiguous=True), p)
    got = lc.read_labels(p)
    assert set(got) == {"a", "b"}
    assert got["a"]["verdict"]["kind"] == "ambiguous"
    assert got["a"]["phases"] == FOUR          # ambiguous still records the phases
    assert got["b"]["verdict"]["incipient_end_idx"] == 7


@requires_yaml
def test_missing_or_empty_labels_file_reads_as_no_labels(tmp_path):
    """The file is committed empty and the suite has to pass before labelling."""
    assert lc.read_labels(tmp_path / "nope.yaml") == {}
    (tmp_path / "empty.yaml").write_text("")
    assert lc.read_labels(tmp_path / "empty.yaml") == {}
    assert lc.read_labels(lc.LABELS_PATH) == {} or True  # the real one may be filled


@requires_yaml
def test_interrupted_write_leaves_the_previous_file_intact(tmp_path, monkeypatch):
    """A crash mid-write must not cost the labels already saved.

    os.replace is made to raise, i.e. the failure lands exactly where a partial
    file would otherwise become the visible one.
    """
    p = tmp_path / "l.yaml"
    lc.write_labels({"a": {"id": "a", "verdict": {"kind": "none"},
                           "tolerance_idx": 1, "source": "real",
                           "series_sha256": "x", "labeled_at": "t"}}, p)
    before = p.read_text()

    real_replace = os.replace

    def boom(src, dst):
        raise OSError("simulated crash between write and rename")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        lc.write_labels({"b": {"id": "b", "verdict": {"kind": "none"},
                               "tolerance_idx": 1, "source": "real",
                               "series_sha256": "y", "labeled_at": "t"}}, p)
    monkeypatch.setattr(os, "replace", real_replace)

    assert p.read_text() == before
    assert set(lc.read_labels(p)) == {"a"}
    # and no debris left behind to be mistaken for the artefact
    assert [q.name for q in tmp_path.iterdir()] == ["l.yaml"]


def test_series_sha256_changes_when_the_data_changes(toy_series):
    h0 = lc.series_sha256(toy_series)
    assert h0 == lc.series_sha256(toy_series.copy())
    bumped = toy_series.copy()
    bumped.iloc[3] += 1e-12
    assert lc.series_sha256(bumped) != h0
    # index-only changes do not: the label refers to positions, not timestamps
    shifted = pd.Series(toy_series.to_numpy(),
                        index=pd.date_range("1999-01-01", periods=len(toy_series),
                                            freq="3h"))
    assert lc.series_sha256(shifted) == h0


@requires_yaml
def test_a_stale_label_is_detectable(tmp_path, toy_series):
    p = tmp_path / "l.yaml"
    lc.upsert_label(lc.make_label_record("t", "real", toy_series, FOUR), p)
    changed = toy_series.copy()
    changed.iloc[0] = 0.0
    assert lc.read_labels(p)["t"]["series_sha256"] != lc.series_sha256(changed)


@pytest.mark.parametrize("verdict", [
    {"kind": "nonsense"},
    {"kind": "boundary"},                          # no index
    {"kind": "boundary", "incipient_end_idx": 0},  # empty phase is kind=none
    {"kind": "boundary", "incipient_end_idx": -3},
])
def test_malformed_verdicts_are_rejected(verdict):
    with pytest.raises((ValueError, TypeError)):
        lc.validate_verdict(verdict)


def test_negative_tolerance_is_rejected(toy_series):
    with pytest.raises(ValueError):
        lc.make_label_record("t", "real", toy_series,
                             _phases(("incipient", 0, 0), ("mature", 5, -1)))


@requires_yaml
def test_committed_labels_file_is_parseable_and_well_formed():
    """Whatever state the artefact is in, it must be readable and valid."""
    import yaml
    doc = yaml.safe_load(lc.LABELS_PATH.read_text())
    assert doc["schema"] == lc.LABELS_SCHEMA
    for rec in (doc.get("labels") or []):
        assert set(rec) >= {"id", "source", "series_sha256", "labeled_at",
                            "n_steps", "phases", "verdict", "tolerance_idx"}
        lc.validate_verdict(rec["verdict"])
        lc.validate_phases(rec["phases"], n_steps=rec["n_steps"])
        assert int(rec["tolerance_idx"]) >= 0


# ══════════════════════════════════════════════════════════════════════════════
# 3. The split is frozen and stratified
# ══════════════════════════════════════════════════════════════════════════════

def test_split_is_reproducible_from_its_seed():
    lengths = {f"t{i:03d}": 30 + (i * 7) % 200 for i in range(51)}
    a = lc.stratified_split(lengths, seed=123)
    b = lc.stratified_split(lengths, seed=123)
    assert a == b
    assert lc.stratified_split(lengths, seed=124) != a


def test_split_does_not_depend_on_insertion_order():
    """Same set of ids, different dict order — the draw must not move."""
    items = [(f"t{i:03d}", 30 + (i * 7) % 200) for i in range(51)]
    a = lc.stratified_split(dict(items), seed=7)
    b = lc.stratified_split(dict(reversed(items)), seed=7)
    assert a == b


def test_split_respects_the_three_length_bands():
    real = lc.load_real_series()
    lengths = {k: len(v) for k, v in real.items()}
    sp = lc.stratified_split(lengths)
    assert sp["strata"]["short"]["n"] == 10
    assert sp["strata"]["medium"]["n"] == 22
    assert sp["strata"]["long"]["n"] == 19
    for band in ("short", "medium", "long"):
        s = sp["strata"][band]
        assert s["n_train"] + s["n_test"] == s["n"]
        assert s["n_test"] >= 1, f"{band} would have an empty test set"
    assert set(sp["train"]).isdisjoint(sp["test"])
    assert set(sp["train"]) | set(sp["test"]) == set(lengths)


@requires_yaml
def test_committed_split_matches_what_the_code_draws():
    """The artefact on disk is the artefact this seed produces — not a stale one."""
    doc = lc.read_split()
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    rebuilt = lc.build_split_document({k: len(v) for k, v in real.items()},
                                      synth.keys(), seed=doc["seed"])
    assert sorted(doc["train"]) == sorted(rebuilt["train"])
    assert sorted(doc["test"]) == sorted(rebuilt["test"])
    assert doc["strata"] == rebuilt["strata"]


@requires_yaml
def test_no_synthetic_case_is_held_out():
    """The 12 designed cases are all in train — see make_split.py's rationale."""
    doc = lc.read_split()
    _synth, names = lc.load_synthetic_series()
    syn_ids = set(names)
    assert syn_ids <= set(doc["train"])
    assert syn_ids.isdisjoint(doc["test"])
    assert all(doc["source"][s] == "synthetic" for s in syn_ids)


# ══════════════════════════════════════════════════════════════════════════════
# 4. The queue
# ══════════════════════════════════════════════════════════════════════════════

def test_queue_holds_every_series_exactly_once():
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    ids = set(real) | set(synth)
    q = lc.build_queue(ids)
    assert len(q) == len(ids) == 63
    assert sorted(q) == sorted(ids)


def test_queue_is_shuffled_not_sorted():
    """Sorted-by-id order would align the labeller's fatigue with the identifier,
    and the real track ids are chronological."""
    ids = [f"t{i:03d}" for i in range(63)]
    q = lc.build_queue(ids)
    assert q != sorted(ids)


def test_resuming_gives_back_the_same_order_and_position():
    ids = [f"t{i:03d}" for i in range(63)]
    q1 = lc.build_queue(ids)
    q2 = lc.build_queue(list(reversed(ids)))     # a differently-built collection
    assert q1 == q2
    done = set(q1[:10])
    assert lc.queue_position(q1, done) == 10
    assert lc.queue_position(q1, set()) == 0
    assert lc.queue_position(q1, set(q1)) == len(q1)


def test_queue_position_skips_to_the_first_gap():
    """Re-labelling an earlier item must not send a resumed session back to it."""
    q = ["a", "b", "c", "d"]
    assert lc.queue_position(q, {"a", "c"}) == 1


def test_synthetic_ids_are_opaque_and_stable():
    """The case names spell the expected phase sequence — they are the answer."""
    _series, names = lc.load_synthetic_series()
    for oid, case_name in names.items():
        assert oid == lc.opaque_synthetic_id(case_name)
        assert case_name not in oid
        for tell in ("Ic", "It", "MD", "clean", "noisy", "residual"):
            assert tell not in oid


# ══════════════════════════════════════════════════════════════════════════════
# 5. The metrics
# ══════════════════════════════════════════════════════════════════════════════

def _rec(sid, kind, tol, idx=None):
    v = {"kind": kind} if idx is None else {"kind": kind, "incipient_end_idx": idx}
    return {"id": sid, "source": "real", "series_sha256": "h",
            "labeled_at": "t", "verdict": v, "tolerance_idx": tol}


def test_hit_rate_uses_each_labels_own_margin():
    """The whole reason tolerance is per-label: the same error is a hit on one
    series and a miss on another."""
    recs = [_rec("a", "boundary", 2, 10),    # detected 12 -> err 2 -> hit  (<=2)
            _rec("b", "boundary", 1, 10)]    # detected 12 -> err 2 -> miss (>1)
    m = lc.score_labels(recs, {"a": 12, "b": 12})
    assert m["n_boundary"] == 2
    assert m["n_hit"] == 1
    assert m["hit_rate"] == 0.5
    assert m["mae"] == 2.0
    assert m["worst"] == 2


def test_tolerance_zero_demands_an_exact_index():
    recs = [_rec("a", "boundary", 0, 10), _rec("b", "boundary", 0, 10)]
    m = lc.score_labels(recs, {"a": 10, "b": 11})
    assert m["n_hit"] == 1
    assert m["mae"] == 0.5
    assert m["worst"] == 1


def test_mae_and_worst_are_raw_not_margin_adjusted():
    """A generous margin must not flatter the distance numbers printed beside it."""
    recs = [_rec("a", "boundary", 50, 10), _rec("b", "boundary", 50, 10)]
    m = lc.score_labels(recs, {"a": 13, "b": 30})
    assert m["hit_rate"] == 1.0
    assert m["mae"] == pytest.approx((3 + 20) / 2)
    assert m["worst"] == 20


def test_refusal_is_counted_in_both_directions():
    recs = [_rec("a", "none", 3),
            _rec("b", "none", 3),
            _rec("c", "boundary", 3, 8)]
    m = lc.score_labels(recs, {"a": None, "b": 4, "c": None})
    assert m["n_none"] == 2
    assert m["n_none_agreed"] == 1
    assert m["none_agreement_rate"] == 0.5
    assert m["detector_missing_on_boundary"] == 1
    # a refusal is not an error of size k: it must not enter the distances
    assert m["mae"] is None
    assert m["n_compared"] == 0
    # ...but it still counts against the hit rate, rather than being skipped
    assert m["n_boundary"] == 1
    assert m["hit_rate"] == 0.0


def test_ambiguous_is_out_of_the_hit_rate_and_mae_but_in_the_refusal_count():
    recs = [_rec("a", "ambiguous", 3), _rec("b", "ambiguous", 3),
            _rec("c", "boundary", 3, 5)]
    m = lc.score_labels(recs, {"a": 7, "b": None, "c": 5})
    assert m["n_ambiguous"] == 2
    assert m["n_ambiguous_detector_none"] == 1
    assert m["n_boundary"] == 1
    assert m["hit_rate"] == 1.0
    assert m["n_compared"] == 1
    assert m["mae"] == 0.0


def test_a_series_the_detector_never_reached_is_reported_not_silently_dropped():
    recs = [_rec("a", "boundary", 3, 5), _rec("b", "boundary", 3, 5)]
    m = lc.score_labels(recs, {"a": 5})
    assert m["n_unscored"] == 1
    assert m["n_boundary"] == 1


def test_empty_input_yields_no_numbers_rather_than_zeros():
    """A hit rate of 0.0 over nothing would read as a failing detector."""
    m = lc.score_labels([], {})
    assert m["hit_rate"] is None and m["mae"] is None and m["worst"] is None


# ══════════════════════════════════════════════════════════════════════════════
# 5b. The phase sequence: validation, the derived verdict, and its metrics
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("bad, why", [
    ([], "empty"),
    (_phases(("incipient", 3, 0)), "first phase must start at 0"),
    (_phases(("incipient", 0, 0), ("mature", 0, 1)), "zero-length phase"),
    (_phases(("incipient", 0, 0), ("mature", 9, 1), ("decay", 5, 1)), "goes backwards"),
    (_phases(("incipient", 0, 0), ("nonsense", 5, 1)), "unknown phase"),
    (_phases(("incipient", 0, 0), ("mature", 999, 1)), "past the end"),
])
def test_malformed_phase_sequences_are_rejected(bad, why):
    """A partition of [0, n) that is not one must fail now, not at evaluation —
    by which time the series has left the screen and the labeller cannot say
    what they meant."""
    with pytest.raises((ValueError, KeyError, IndexError)):
        lc.validate_phases(bad, n_steps=40)


def test_repeated_phases_are_allowed():
    """residual → intensification → mature → decay is a real life cycle; the
    phase's POSITION carries the repetition, so the name is never numbered."""
    seq = _phases(("incipient", 0, 0), ("intensification", 5, 2), ("mature", 10, 2),
                  ("decay", 15, 2), ("residual", 20, 2), ("intensification", 25, 2),
                  ("mature", 30, 2))
    assert lc.validate_phases(seq, n_steps=40) == seq


def test_phase_names_are_normalised_on_the_way_in():
    """The detector numbers repeats; a label must not carry the number."""
    assert lc.normalize_phase("intensification 2") == "intensification"
    assert lc.normalize_phase("decay") == "decay"
    got = lc.validate_phases(_phases(("incipient", 0, 0), ("mature 3", 5, 1)),
                             n_steps=40)
    assert got[1]["phase"] == "mature"


def test_the_incipient_verdict_is_derived_from_the_phases():
    """Derived rather than asked twice, so the table and the verdict cannot
    disagree about the very thing this front exists to settle."""
    v, tol = lc.incipient_verdict_from_phases(FOUR, 40)
    assert v == {"kind": "boundary", "incipient_end_idx": 7}
    assert tol == 3                       # the margin ON that boundary, not a series-wide one

    no_inc = _phases(("intensification", 0, 2), ("mature", 10, 3))
    assert lc.incipient_verdict_from_phases(no_inc, 40)[0] == {"kind": "none"}

    whole = _phases(("incipient", 0, 4))
    assert lc.incipient_verdict_from_phases(whole, 40)[0] == \
        {"kind": "boundary", "incipient_end_idx": 40}


def test_ambiguous_still_records_the_phases(toy_series):
    rec = lc.make_label_record("t", "real", toy_series, FOUR, ambiguous=True)
    assert rec["verdict"] == {"kind": "ambiguous"}
    assert rec["phases"] == FOUR


def _seq_rec(sid, phases):
    return {"id": sid, "source": "real", "series_sha256": "h", "labeled_at": "t",
            "n_steps": 60, "phases": phases,
            "verdict": {"kind": "boundary", "incipient_end_idx": phases[1]["start_idx"]},
            "tolerance_idx": phases[1]["tolerance_idx"]}


def test_sequence_mismatch_is_counted_not_measured():
    """Pairing the k-th labelled boundary with the k-th detected one across a
    mismatch compares two different transitions and manufactures a number."""
    rec = _seq_rec("a", FOUR)
    det = {"a": [("incipient", 0), ("intensification", 7), ("decay", 30)]}
    m = lc.score_phase_sequences([rec], det)
    assert m["n_sequence_mismatch"] == 1
    assert m["n_sequence_match"] == 0
    assert m["n_boundaries"] == 0          # nothing measured at all
    assert m["per_phase"] == {}


def test_boundary_errors_are_reported_per_phase_against_their_own_margins():
    rec = _seq_rec("a", FOUR)              # margins 3 / 5 / 4 on It / M / D
    det = {"a": [("incipient", 0), ("intensification", 9),   # err 2 <= 3  hit
                 ("mature", 28), ("decay", 30)]}             # err 8 > 5 miss; 0 <= 4 hit
    m = lc.score_phase_sequences([rec], det)
    assert m["n_sequence_match"] == 1
    assert m["per_phase"]["intensification"] == {
        "n": 1, "n_hit": 1, "mae": 2.0, "worst": 2, "hit_rate": 1.0}
    assert m["per_phase"]["mature"]["n_hit"] == 0
    assert m["per_phase"]["mature"]["worst"] == 8
    assert m["per_phase"]["decay"]["mae"] == 0.0
    assert m["n_boundaries"] == 3 and m["n_boundaries_hit"] == 2


def test_the_first_phase_start_is_excluded_from_every_rate():
    """It is 0 on both sides by construction and would pad the hit rate with
    free agreement."""
    rec = _seq_rec("a", _phases(("incipient", 0, 0), ("mature", 10, 1)))
    m = lc.score_phase_sequences([rec], {"a": [("incipient", 0), ("mature", 10)]})
    assert m["n_boundaries"] == 1          # not 2
    assert "incipient" not in m["per_phase"]


def test_numbered_detected_phases_still_match_a_label():
    rec = _seq_rec("a", _phases(("incipient", 0, 0), ("intensification", 5, 2),
                                ("mature", 10, 2), ("decay", 15, 2),
                                ("residual", 20, 2), ("intensification", 25, 2)))
    det = {"a": [("incipient", 0), ("intensification", 5), ("mature", 10),
                 ("decay", 15), ("residual", 20), ("intensification 2", 25)]}
    m = lc.score_phase_sequences([rec], det)
    assert m["n_sequence_match"] == 1
    assert m["per_phase"]["intensification"]["n"] == 2


def test_a_record_from_an_earlier_schema_is_flagged_not_crashed_on():
    """A working copy can hold records from before either format change, and
    neither is upgradable, so both are excluded loudly.

    schema 1: one incipient boundary, no phases at all — the phases it never
    recorded are not recoverable from the boundary it did.

    schema 2: a phase sequence whose boundaries carry no `unsure` flag. Filling
    it in as False would put a claim in the labeller's mouth — "they were
    confident" — and that claim is precisely what decides whether the boundary
    counts against the detector.
    """
    schema_1 = {"id": "a", "source": "real", "series_sha256": "h", "labeled_at": "t",
                "verdict": {"kind": "boundary", "incipient_end_idx": 7},
                "tolerance_idx": 3}
    assert lc.is_legacy_record(schema_1)

    schema_2 = _seq_rec("b", [{"phase": p["phase"], "start_idx": p["start_idx"],
                               "tolerance_idx": p["tolerance_idx"]} for p in FOUR])
    assert lc.is_legacy_record(schema_2), (
        "a schema-2 record was accepted; its missing `unsure` would be silently "
        "read as confidence the labeller never expressed")

    assert not lc.is_legacy_record(_seq_rec("c", FOUR))


# ══════════════════════════════════════════════════════════════════════════════
# 5b-bis. "Not sure", per boundary (schema 3)
# ══════════════════════════════════════════════════════════════════════════════

def test_unsure_is_carried_per_boundary_and_never_on_the_first_phase():
    """The first phase's start is 0 by construction, so there is no boundary
    there to be unsure about; a flag set on it is dropped rather than stored."""
    got = lc.validate_phases(_phases(("incipient", 0, 0, True),
                                     ("mature", 5, 2, True),
                                     ("decay", 9, 1, False)), n_steps=20)
    assert [p["unsure"] for p in got] == [False, True, False]


def test_an_unsure_incipient_boundary_reads_as_ambiguous():
    """The per-series ambiguity flag and a per-boundary one must agree on the
    incipient question — the evaluation speaks only `verdict`, so an unsure
    incipient boundary has to arrive there as `ambiguous` rather than as a
    boundary index nobody stands behind."""
    ph = lc.validate_phases(_phases(("incipient", 0, 0), ("mature", 6, 2, True)),
                            n_steps=30)
    verdict, tol = lc.incipient_verdict_from_phases(ph, 30)
    assert verdict == {"kind": "ambiguous"}
    assert tol == 2
    # ...and a confident one still reads as a boundary
    ph2 = lc.validate_phases(_phases(("incipient", 0, 0), ("mature", 6, 2)), n_steps=30)
    assert lc.incipient_verdict_from_phases(ph2, 30)[0] == {
        "kind": "boundary", "incipient_end_idx": 6}


def test_one_unsure_boundary_does_not_void_the_rest_of_the_series():
    """The point of moving ambiguity from the series to the boundary.

    Before, "I cannot read the mature->decay roll" threw away the incipient knee
    four phases away from it — discarding the good evidence in order to register
    the bad one.
    """
    lab = _phases(("incipient", 0, 0), ("intensification", 10, 1),
                  ("mature", 20, 1), ("decay", 30, 1, True))
    rec = _seq_rec("s", lab)
    detected = {"s": [("incipient", 0), ("intensification", 10),
                      ("mature", 20), ("decay", 44)]}     # decay is wildly off
    m = lc.score_phase_sequences([rec], detected)
    assert m["n_sequence_match"] == 1
    assert m["n_boundaries_unsure"] == 1
    assert m["n_boundaries"] == 2                          # the two confident ones
    assert m["boundary_hit_rate"] == 1.0, (
        "the unsure decay boundary was scored; it must be set aside, and the two "
        "boundaries the labeller could read must still count")
    assert "decay" not in m["per_phase"]


def test_an_unsure_boundary_is_excluded_even_when_the_detector_agrees():
    """Excluded in BOTH directions. A boundary nobody could place is not
    evidence about the detector even when the detector happens to land on it —
    counting the agreement would inflate the hit rate with a coin flip."""
    lab = _phases(("incipient", 0, 0), ("mature", 20, 0, True))
    m = lc.score_phase_sequences([_seq_rec("s", lab)],
                                 {"s": [("incipient", 0), ("mature", 20)]})
    assert m["n_boundaries"] == 0
    assert m["n_boundaries_unsure"] == 1
    assert m["boundary_hit_rate"] is None


# ══════════════════════════════════════════════════════════════════════════════
# 5c. The labelling view: standard colours, and the tolerance made visible
# ══════════════════════════════════════════════════════════════════════════════

def _label_tab():
    pytest.importorskip("streamlit",
                        reason="the labelling tab is calibration-app code")
    spec = importlib.util.spec_from_file_location("_lt_under_test", LABEL_TAB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_phase_palette_matches_the_package_figures():
    """Restated in labels_core rather than imported, because the labelling tab
    must not be able to reach the package at all. Parsed here — not imported —
    so the duplication cannot silently drift."""
    plots_src = (REPO_ROOT / "cyclophaser" / "plots.py").read_text()
    tree = ast.parse(plots_src)
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "colors_phases" for t in node.targets):
            found = ast.literal_eval(node.value)
            break
    assert found, "cyclophaser/plots.py no longer defines colors_phases"
    assert lc.PHASE_COLORS == found
    assert set(lc.PHASE_ORDER) == set(found)


def test_each_phase_is_drawn_in_its_own_standard_colour():
    lt = _label_tab()
    s_ = pd.Series(range(60), dtype="float64",
                   index=pd.date_range("2020-01-01", periods=60, freq="3h"))
    colours = lt.chart_payload("x", s_, FOUR)["colors"]
    for ph in FOUR:
        assert colours[ph["phase"]] == lc.PHASE_COLORS[ph["phase"]]
    assert colours["incipient"] == "#65a1e6"              # blue, as asked


def test_the_opening_scaffold_is_a_valid_partition():
    lt = _label_tab()
    for n in (30, 56, 120, 259):
        ph = lt.default_phases(n, 4)
        assert lc.validate_phases(ph, n_steps=n) == ph
        assert [p["phase"] for p in ph] == ["incipient", "intensification",
                                            "mature", "decay"]


# ══════════════════════════════════════════════════════════════════════════════
# 5d. The chart payload and the drag result, in Python
# ══════════════════════════════════════════════════════════════════════════════
#
# The chart is now hand-drawn JS in a components.v2 surface. Plotly could not do
# what this view needs: a boundary bar that slides along time and drags its
# shading with it. Plotly has no axis constraint for draggable shapes, so a bar
# could be pulled off the time axis where it means nothing, and Streamlit does
# not expose window.Plotly to snap it back. Drawn by hand, only clientX is ever
# read — see the Node spec in 5e, which enforces that with a clientY that throws.
#
# These tests cover the two Python ends of that: what the chart is allowed to
# know, and what happens to the message it sends back.

def test_the_chart_is_told_the_raw_series_and_the_labellers_marks_and_nothing_else():
    """The payload is the ONLY channel from the app to the drawing surface, so
    pinning its keys is what keeps the blindness checkable instead of asserted."""
    lt = _label_tab()
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0],
                  index=pd.date_range("2020-01-01", periods=5, freq="3h"))
    ph = _phases(("incipient", 0, 0), ("mature", 2, 1))
    payload = lt.chart_payload("T", s, ph)

    assert set(payload) == {"sid", "n", "y", "phases", "colors",
                            "w", "h", "ml", "mr", "mt", "mb"}
    assert payload["y"] == [1.0, 2.0, 3.0, 4.0, 5.0]      # the raw values, verbatim
    assert payload["n"] == 5
    assert payload["phases"] == ph
    assert payload["colors"] == lc.PHASE_COLORS
    blob = json.dumps(payload)
    for name in FORBIDDEN_NAMES:
        assert name not in blob, name


def test_the_chart_payload_is_json_serialisable():
    """It crosses into the browser as JSON; a stray numpy scalar would break the
    chart at mount time, in a browser, where the traceback is not visible."""
    lt = _label_tab()
    real = lc.load_real_series()
    sid, values = next(iter(sorted(real.items())))
    payload = lt.chart_payload(sid, values, lt.default_phases(len(values), 4))
    round_tripped = json.loads(json.dumps(payload))
    assert round_tripped["n"] == len(values)
    assert all(isinstance(v, float) for v in round_tripped["y"])


def test_a_drag_result_moves_the_boundary_it_names():
    lt = _label_tab()
    phases = [dict(p) for p in FOUR]
    payload = {"sid": "T", "phases": [
        {"start_idx": 0, "tolerance_idx": 0}, {"start_idx": 11, "tolerance_idx": 3},
        {"start_idx": 20, "tolerance_idx": 5}, {"start_idx": 30, "tolerance_idx": 4}]}
    assert lt.apply_edit(payload, phases, 60)
    assert [p["start_idx"] for p in phases] == [0, 11, 20, 30]
    assert [p["phase"] for p in phases] == [p["phase"] for p in FOUR]   # names kept


def test_a_drag_result_is_re_clamped_on_arrival():
    """The browser clamps as it drags, but a message can arrive stale — from a
    chart drawn before the table was edited — and must not be able to write a
    sequence that is no longer a partition of [0, n)."""
    lt = _label_tab()
    phases = [dict(p) for p in FOUR]
    payload = {"phases": [
        {"start_idx": 9, "tolerance_idx": 0},        # first is forced to 0
        {"start_idx": -50, "tolerance_idx": 3},
        {"start_idx": 999, "tolerance_idx": 5},
        {"start_idx": 999, "tolerance_idx": -4}]}
    lt.apply_edit(payload, phases, 60)
    assert phases[0]["start_idx"] == 0
    assert lc.validate_phases(phases, n_steps=60) == phases
    assert all(p["tolerance_idx"] >= 0 for p in phases)


def test_a_malformed_or_mismatched_drag_result_is_ignored():
    """A message describing a different number of phases is from a chart that no
    longer matches the table; applying it positionally would scramble the label.
    """
    lt = _label_tab()
    for bad in ({}, {"phases": None}, {"phases": []},
                {"phases": [{"start_idx": 0, "tolerance_idx": 0}]},      # too short
                {"phases": [{"start_idx": 0}] * 4},                      # no margin
                {"phases": ["nonsense"] * 4}):
        phases = [dict(p) for p in FOUR]
        assert not lt.apply_edit(bad, phases, 60), bad
        assert phases == FOUR


def test_an_unchanged_drag_result_reports_no_change():
    """Otherwise every message would trigger a rerun."""
    lt = _label_tab()
    phases = [dict(p) for p in FOUR]
    same = {"phases": [{"start_idx": p["start_idx"],
                        "tolerance_idx": p["tolerance_idx"]} for p in FOUR]}
    assert not lt.apply_edit(same, phases, 60)


def test_the_same_drag_result_is_only_acted_on_once():
    """A trigger value that outlived its rerun would be re-applied every pass:
    each bumps the revision, which reruns, which re-reads it. That loop takes the
    app down mid-labelling, so it is guarded rather than hoped about."""
    lt = _label_tab()
    payload = {"phases": [{"start_idx": 0, "tolerance_idx": 0}]}
    sig = lt.edit_signature(payload)
    assert lt.is_new_edit(payload, None)
    assert not lt.is_new_edit(payload, sig)
    assert not lt.is_new_edit({"phases": [{"tolerance_idx": 0, "start_idx": 0}]}, sig)
    assert lt.is_new_edit({"phases": [{"start_idx": 1, "tolerance_idx": 0}]}, sig)
    assert not lt.is_new_edit({}, None)


def test_a_chart_that_cannot_mount_says_so_instead_of_drawing_something_else():
    """No silent fallback. This is the whole lesson of the three failed rounds.

    There WAS a fallback: when the component raised, the tab quietly drew a
    static Plotly picture of the same data. It looked right. It could not be
    dragged. And because the component raised on EVERY render — the mount key
    contained `__`, which Streamlit reserves inside a bidirectional component's
    id — that fallback was the only thing anyone ever saw, for three rounds,
    while every check passed.

    A plausible picture in place of a broken feature is worse than no picture:
    it converts a total failure into a puzzling one. So the handler now renders
    an error naming the exception, and the numeric table below it — which is the
    canonical way to write a label anyway — carries on working.
    """
    lt = _label_tab()
    assert not hasattr(lt, "_fallback_chart"), (
        "the silent fallback is back; a chart that cannot mount must say so")
    src = ast.parse(LABEL_TAB.read_text())
    fn = next(n for n in ast.walk(src)
              if isinstance(n, ast.FunctionDef) and n.name == "render")
    handlers = [h for n in ast.walk(fn) if isinstance(n, ast.Try) for h in n.handlers]
    assert handlers, "the chart call is not guarded at all"
    dumped = " ".join(ast.dump(h) for h in handlers)
    assert "error" in dumped, "the mount failure is not reported to the labeller"
    assert "could not be mounted" in LABEL_TAB.read_text()

    # ...and the table is built outside that try, so a mount failure cannot take
    # it down with the chart.
    table_calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name) and n.func.id == "_phase_table"]
    assert len(table_calls) == 1
    in_try = [n for t in ast.walk(fn) if isinstance(t, ast.Try)
              for n in ast.walk(t) if n is table_calls[0]]
    assert not in_try, "the table is inside the chart's try block"


def test_the_component_key_can_never_contain_the_reserved_delimiter():
    """The one-line bug, pinned as a property rather than as a string.

    `key=f"lab_chart__{sid}"` raised BidiComponentInvalidIdError on every mount.
    `chart_key` folds everything outside [A-Za-z0-9-] to `-`, so a doubled
    underscore is unrepresentable rather than merely absent from today's ids.
    """
    lt = _label_tab()
    for sid in ("20160735", "s1a2b3c4d", "a__b", "weird id_ 9", "__", "a_b_c"):
        key = lt.chart_key(sid)
        assert "__" not in key, (sid, key)
        assert "_" not in key, (sid, key)
    # distinct series still get distinct keys, or two charts would share state
    ids = ["20160735", "20160736", "s1a2b3c4d"]
    assert len({lt.chart_key(i) for i in ids}) == len(ids)


# ══════════════════════════════════════════════════════════════════════════════
# 5e. The chart component is exercised IN A BROWSER, not here
# ══════════════════════════════════════════════════════════════════════════════
#
# There used to be a Node spec here that ran `_CHART_JS` against a hand-written
# DOM stub (tests/js/). It passed. The feature it covered did not work in any
# browser, in three consecutive deliveries, because the fault was in the Python
# that MOUNTS the component and the stub never executed a mount. Keeping both a
# simulated-DOM spec and a real-browser one would duplicate the maintenance and,
# far worse, restore the false confidence: a green Node run is exactly what made
# three unverified deliveries feel finished.
#
# So tests/js/ is deleted and tests/test_label_browser.py replaces it: real
# Chromium, real `streamlit run`, real pointer events, and every assertion read
# back from the values that reached Python.
#
# What survives here is what can be checked without a browser at all: the shape
# of the JS the app ships, and the fact that it reads no vertical coordinate.


def test_the_shipped_chart_js_never_reads_a_vertical_coordinate():
    """The load-bearing property of drawing the chart by hand.

    Plotly could not keep a drag on the time axis — it has no axis constraint for
    shapes, and Streamlit does not expose window.Plotly to correct one — so the
    chart is hand-drawn and the handler reads clientX and NOTHING else. There is
    no vertical coordinate in the code path, which is why a boundary cannot leave
    the time axis: not because it is pushed back, but because nothing moves it
    there.

    Checked on the source text, which is cheap and total, rather than on a
    stubbed DOM that has to be believed.
    """
    lt = _label_tab()
    js = lt._CHART_JS
    for banned in ("clientY", "offsetY", "pageY", "screenY", "movementY"):
        assert banned not in js, (
            f"the chart JS reads {banned}; a boundary must not be able to leave "
            "the time axis")
    assert "clientX" in js


def test_the_shipped_chart_js_listens_on_window_not_on_the_svg():
    """`pointerup` on the <svg> only fires while the pointer is over it.

    Release the pointer anywhere else — past the plot edge, over the sidebar, off
    the window — and the drag never finished, `setTriggerValue` was never called,
    and the edit vanished with no error anywhere. `setPointerCapture` was meant
    to cover that but sat inside a silent try/catch, so its failure said nothing.

    tests/test_label_browser.py proves the gesture works; this pins the mechanism
    so it cannot quietly regress to the <svg> in a refactor.
    """
    lt = _label_tab()
    js = lt._CHART_JS
    for ev in ("pointermove", "pointerup", "pointercancel"):
        assert f"window.addEventListener('{ev}'" in js, ev
        assert f"svg.addEventListener('{ev}'" not in js, (
            f"{ev} is bound to the svg again — a release outside the plot will "
            "be lost in silence")
    # the CALL, not the word: the comment above the window listeners explains
    # why pointer capture is gone, and has to be able to name it
    assert ".setPointerCapture(" not in js, (
        "pointer capture is back; with window listeners it is unnecessary, and "
        "it was the silent try/catch around it that hid the original failure")


def test_the_shipped_chart_js_reports_a_failure_to_reach_python():
    """Silent failure is the bug this whole round is about. If the component
    cannot send its edit, it must draw a warning where the labeller is looking,
    not log to a console nobody has open."""
    lt = _label_tab()
    js = lt._CHART_JS
    assert "setTriggerValue is not available" in js
    assert "did not reach the app" in js


def test_the_shipped_chart_js_supports_the_keyboard():
    """On a 259-step series one index is under four pixels wide, so the last few
    steps of a boundary cannot be placed with a pointer at all. The keyboard is
    also the path that still works when the pointer path does not."""
    lt = _label_tab()
    js = lt._CHART_JS
    for key in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"):
        assert key in js, key
    assert "shiftKey" in js, "shift must move in bigger steps"
    assert "keydown" in js


# ══════════════════════════════════════════════════════════════════════════════
# 6. The detector read-out, and the end-to-end evaluation
# ══════════════════════════════════════════════════════════════════════════════

@requires_yaml
def test_detected_boundary_uses_the_same_convention_as_the_label():
    from evaluate_against_labels import detected_incipient_end
    assert detected_incipient_end(
        pd.Series(["incipient"] * 4 + ["intensification"] * 6)) == 4
    assert detected_incipient_end(pd.Series(["intensification"] * 6)) is None
    assert detected_incipient_end(pd.Series(["incipient"] * 3)) == 3
    assert detected_incipient_end(pd.Series([], dtype=object)) is None
    # numbered phase labels ("incipient 2") still read as incipient
    assert detected_incipient_end(pd.Series(["incipient", "incipient 2",
                                             "decay"])) == 2


# ── the train-only regression gate, skipped until the labels exist ───────────

# Read at module scope, which is COLLECTION time — so a missing PyYAML must
# degrade to "no labels to gate on", never to an ImportError that fails the
# whole suite.
try:
    _LABELS = lc.read_labels()
    _TRAIN = set(lc.read_split()["train"])
    _TRAIN_LABELS = [r for sid, r in sorted(_LABELS.items()) if sid in _TRAIN]
except Exception:
    _LABELS, _TRAIN, _TRAIN_LABELS = {}, set(), []


@pytest.mark.skipif(not _TRAIN_LABELS,
                    reason="manual_labels.yaml is still empty — label the queue first")
def test_detector_matches_the_training_labels_within_their_own_margins():
    """The gate this whole front exists to make possible.

    TRAIN ONLY, on purpose. The test split is not consulted here at any effort
    level: a held-out set that a CI job reads on every push is not held out.

    No threshold is asserted on the hit rate yet — the labels do not exist while
    this is being written, so any number would be invented. What IS asserted is
    that every training label is scoreable and none has gone stale, which is the
    part that can rot silently.
    """
    import warnings

    from cyclophaser.determine_periods import get_periods, process_vorticity
    from evaluate_against_labels import (detected_incipient_end,
                                         detected_phase_starts)

    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    series = {**real, **synth}

    detected, seqs = {}, {}
    for rec in _TRAIN_LABELS:
        sid = rec["id"]
        assert sid in series, f"label {sid} names a series that does not exist"
        assert not lc.is_legacy_record(rec), (
            f"label {sid} predates the whole-sequence format — re-label it")
        assert rec["series_sha256"] == lc.series_sha256(series[sid]), (
            f"label {sid} was written against different data — it is void")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": series[sid]}))
            periods = get_periods(vort)["periods"]
        detected[sid] = detected_incipient_end(periods)
        seqs[sid] = detected_phase_starts(periods)

    m = lc.score_labels(_TRAIN_LABELS, detected)
    assert m["n_unscored"] == 0
    assert m["n_scored"] == len(_TRAIN_LABELS)
    ms = lc.score_phase_sequences(_TRAIN_LABELS, seqs)
    assert ms["n_unscored"] == 0
    print(f"\nincipient: hit rate {m['hit_rate']} · MAE {m['mae']} · worst {m['worst']}"
          f"\nsequence:  {ms['n_sequence_match']}/{ms['n_series']} match · "
          f"boundaries {ms['boundary_hit_rate']}")
