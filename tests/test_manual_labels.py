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
import os
import re
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))

import labels_core as lc  # noqa: E402

LABEL_TAB = REPO_ROOT / "tools" / "calibration_app" / "label_tab.py"


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
    """Exactly one trace is added to the figure, and it is the raw input.

    A second trace is how the blindness would realistically erode — someone adds
    "just the filtered series for context" — so the count itself is pinned.
    """
    tree = _tab_ast()
    add_trace = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "add_trace"]
    assert len(add_trace) == 1, (
        f"the Label figure adds {len(add_trace)} traces; it must show the raw "
        "input series and nothing else")


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
    return [{"phase": p, "start_idx": i, "tolerance_idx": t} for p, i, t in triples]


FOUR = _phases(("incipient", 0, 0), ("intensification", 7, 3),
               ("mature", 20, 5), ("decay", 30, 4))


def test_label_record_round_trips_through_yaml(tmp_path, toy_series):
    p = tmp_path / "manual_labels.yaml"
    rec = lc.make_label_record("t1", "real", toy_series, FOUR, notes="clear knee")
    lc.upsert_label(rec, p)
    back = lc.read_labels(p)
    assert back["t1"] == rec
    assert back["t1"]["phases"] == FOUR
    assert back["t1"]["n_steps"] == len(toy_series)
    assert back["t1"]["notes"] == "clear knee"


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


def test_missing_or_empty_labels_file_reads_as_no_labels(tmp_path):
    """The file is committed empty and the suite has to pass before labelling."""
    assert lc.read_labels(tmp_path / "nope.yaml") == {}
    (tmp_path / "empty.yaml").write_text("")
    assert lc.read_labels(tmp_path / "empty.yaml") == {}
    assert lc.read_labels(lc.LABELS_PATH) == {} or True  # the real one may be filled


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


def test_committed_labels_file_is_parseable_and_well_formed():
    """Whatever state the artefact is in, it must be readable and valid."""
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


def test_a_legacy_schema_1_record_is_flagged_not_crashed_on():
    """A working copy can hold single-boundary records from before the format
    changed; the phases they never recorded are not recoverable from the
    boundary they did, so they must be excluded loudly."""
    legacy = {"id": "a", "source": "real", "series_sha256": "h", "labeled_at": "t",
              "verdict": {"kind": "boundary", "incipient_end_idx": 7},
              "tolerance_idx": 3}
    assert lc.is_legacy_record(legacy)
    assert not lc.is_legacy_record(_seq_rec("b", FOUR))


# ══════════════════════════════════════════════════════════════════════════════
# 5c. The labelling view: standard colours, and the tolerance made visible
# ══════════════════════════════════════════════════════════════════════════════

def _label_tab():
    import importlib.util
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


def test_each_phase_is_shaded_in_its_own_standard_colour():
    lt = _label_tab()
    s = pd.Series(range(60), dtype="float64",
                  index=pd.date_range("2020-01-01", periods=60, freq="3h"))
    fig = lt._fig("x", s, FOUR)
    fills = [sh.fillcolor for sh in fig.layout.shapes if sh.type == "rect"]
    for ph in FOUR:
        assert lc.PHASE_COLORS[ph["phase"]] in fills, ph["phase"]
    assert lc.PHASE_COLORS["incipient"] == "#65a1e6"      # blue, as asked


def test_the_tolerance_is_drawn_as_a_double_headed_arrow():
    """The margin is the part of a label easiest to set carelessly: a number in a
    table gives no sense of how much curve it forgives."""
    lt = _label_tab()
    s = pd.Series(range(60), dtype="float64",
                  index=pd.date_range("2020-01-01", periods=60, freq="3h"))
    fig = lt._fig("x", s, FOUR)
    arrows = [a for a in fig.layout.annotations if a.showarrow]
    assert arrows, "no tolerance arrow drawn"
    assert all(a.arrowside == "end+start" for a in arrows)
    # one arrow per boundary with a non-zero margin (the first phase has none)
    assert len(arrows) == sum(1 for k, p in enumerate(FOUR)
                              if k >= 1 and p["tolerance_idx"] > 0)
    # and it spans exactly [start-tol, start+tol]
    it = next(a for a in arrows if a.x == 7 + 3)
    assert it.ax == 7 - 3


def test_a_zero_margin_draws_no_band_and_no_arrow():
    lt = _label_tab()
    s = pd.Series(range(60), dtype="float64",
                  index=pd.date_range("2020-01-01", periods=60, freq="3h"))
    fig = lt._fig("x", s, _phases(("incipient", 0, 0), ("mature", 20, 0)))
    assert not [a for a in fig.layout.annotations if a.showarrow]


def test_the_view_still_plots_exactly_one_series():
    """Phase shading is shapes, not traces: the one trace is still the raw input."""
    lt = _label_tab()
    s = pd.Series(range(60), dtype="float64",
                  index=pd.date_range("2020-01-01", periods=60, freq="3h"))
    fig = lt._fig("x", s, FOUR)
    assert len(fig.data) == 1
    assert (fig.data[0].y == s.to_numpy()).all()


def test_the_opening_scaffold_is_a_valid_partition():
    lt = _label_tab()
    for n in (30, 56, 120, 259):
        ph = lt.default_phases(n, 4)
        assert lc.validate_phases(ph, n_steps=n) == ph
        assert [p["phase"] for p in ph] == ["incipient", "intensification",
                                            "mature", "decay"]


# ══════════════════════════════════════════════════════════════════════════════
# 5d. Dragging boundaries and tolerance arrows
# ══════════════════════════════════════════════════════════════════════════════
#
# st.plotly_chart cannot deliver a drag — its own docs say "Only selection events
# are supported at this time" — so a small components.v2 bridge forwards
# plotly_relayout instead. Whether the browser really emits those keys on a drag
# is the ONE thing that cannot be checked from here. Everything downstream of the
# payload is pure Python, and that is what these tests pin: given the message,
# the phases move correctly, and the two sides agree on the message's shape.

def _toy_fig(phases, n=60):
    lt = _label_tab()
    s = pd.Series(range(n), dtype="float64",
                  index=pd.date_range("2020-01-01", periods=n, freq="3h"))
    return lt, lt._fig("x", s, phases)


def test_drag_map_finds_the_boundaries_by_name_not_by_counting():
    """Plotly reports a drag POSITIONALLY. If the map were built by counting the
    calls in _fig, adding one decoration would silently reroute a drag onto the
    wrong boundary."""
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    assert sorted(dm["shapes"].values()) == [1, 2, 3]     # not the first phase
    assert sorted(dm["annotations"].values()) == [1, 2, 3]
    for i, k in dm["shapes"].items():
        assert fig.layout.shapes[i].name == f"bnd{k}"
        assert fig.layout.shapes[i].editable is True


def test_only_the_boundary_lines_are_draggable():
    """edits.shapePosition is global, so every band must be pinned shut or the
    phase shading itself would drag."""
    _lt, fig = _toy_fig(FOUR)
    for sh in fig.layout.shapes:
        if sh.name and sh.name.startswith("bnd"):
            assert sh.editable is True
        else:
            assert sh.editable is False, f"{sh.type} band is draggable"


def test_dragging_a_boundary_moves_that_phase():
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    idx = next(i for i, k in dm["shapes"].items() if k == 2)   # the mature start
    phases = [dict(p) for p in FOUR]
    assert lt.apply_drag({f"shapes[{idx}].x0": 23.7}, phases, dm, 60)
    assert phases[2]["start_idx"] == 24                        # rounded
    assert [p["start_idx"] for p in phases] == [0, 7, 24, 30]   # nothing else moved


def test_a_boundary_cannot_be_dragged_past_its_neighbours():
    """A partition has to stay a partition; a drag that would cross is clamped
    rather than rejected, because a line that refuses to move reads as broken."""
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    idx = next(i for i, k in dm["shapes"].items() if k == 2)
    phases = [dict(p) for p in FOUR]
    lt.apply_drag({f"shapes[{idx}].x0": -400}, phases, dm, 60)
    assert phases[2]["start_idx"] == 8            # one past the boundary before it
    lt.apply_drag({f"shapes[{idx}].x0": 999}, phases, dm, 60)
    assert phases[2]["start_idx"] == 29           # one before the boundary after it
    assert lc.validate_phases(phases, n_steps=60)


def test_dragging_an_arrow_tail_sets_that_boundarys_margin():
    """The arrow is drawn symmetric, so its tail is one half: the margin is the
    tail's distance from the boundary, whichever side it was pulled to."""
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    idx = next(i for i, k in dm["annotations"].items() if k == 1)   # It @ 7, ±3
    phases = [dict(p) for p in FOUR]
    assert lt.apply_drag({f"annotations[{idx}].ax": 1.0}, phases, dm, 60)
    assert phases[1]["tolerance_idx"] == 6          # |7 - 1|
    # pulled to the other side, same margin
    lt.apply_drag({f"annotations[{idx}].ax": 13.0}, phases, dm, 60)
    assert phases[1]["tolerance_idx"] == 6
    assert phases[1]["start_idx"] == 7              # the boundary itself is untouched


def test_a_margin_dragged_onto_its_boundary_becomes_zero_not_negative():
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    idx = next(i for i, k in dm["annotations"].items() if k == 1)
    phases = [dict(p) for p in FOUR]
    lt.apply_drag({f"annotations[{idx}].ax": 7.0}, phases, dm, 60)
    assert phases[1]["tolerance_idx"] == 0
    assert lc.validate_phases(phases, n_steps=60)


def test_a_boundary_and_its_margin_moving_together_measure_against_the_new_place():
    """A tolerance arrives as an absolute tail position and only becomes a ±
    once measured against its boundary — which may have moved in the same gesture,
    so the order of application is load-bearing."""
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    sh = next(i for i, k in dm["shapes"].items() if k == 1)
    an = next(i for i, k in dm["annotations"].items() if k == 1)
    phases = [dict(p) for p in FOUR]
    lt.apply_drag({f"shapes[{sh}].x0": 12.0, f"annotations[{an}].ax": 8.0},
                  phases, dm, 60)
    assert phases[1]["start_idx"] == 12
    assert phases[1]["tolerance_idx"] == 4          # |12 - 8|, not |7 - 8|


def test_unrelated_relayout_keys_are_ignored():
    """plotly_relayout also fires for autorange, zoom and legend moves."""
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    phases = [dict(p) for p in FOUR]
    assert not lt.apply_drag(
        {"xaxis.range[0]": 3, "yaxis.autorange": True, "shapes[0].x1": 9,
         "annotations[0].y": 2}, phases, dm, 60)
    assert phases == FOUR


def test_a_drag_that_changes_nothing_reports_no_movement():
    """Otherwise every stray relayout would trigger a rerun loop."""
    lt, fig = _toy_fig(FOUR)
    dm = lt.drag_map(fig)
    idx = next(i for i, k in dm["shapes"].items() if k == 1)
    phases = [dict(p) for p in FOUR]
    assert not lt.apply_drag({f"shapes[{idx}].x0": 7.0}, phases, dm, 60)


def test_the_browser_filter_and_the_python_parser_accept_the_same_keys():
    """The JS forwards a subset of relayout keys and Python parses them. They are
    written in two languages in two places; if they drift, drags vanish silently.
    """
    lt = _label_tab()
    js_patterns = re.findall(r"/([^/]+)/\.test", lt._DRAG_JS)
    assert len(js_patterns) == 2, js_patterns
    for pattern in js_patterns:
        compiled = re.compile(pattern)
        # every key the browser would forward, Python must also route
        for key in ("shapes[7].x0", "annotations[2].ax"):
            if compiled.match(key):
                assert lt._SHAPE_KEY.match(key) or lt._ANN_KEY.match(key), key
        # and nothing else gets through either side
        for key in ("xaxis.range[0]", "shapes[7].x1", "annotations[2].y"):
            assert not compiled.match(key)
            assert not (lt._SHAPE_KEY.match(key) or lt._ANN_KEY.match(key))


def test_the_drag_bridge_reads_nothing_and_draws_nothing():
    """It exists only to forward coordinates. If it ever grew a `data=` payload
    it could start showing something, and the tab's blindness is not negotiable.
    """
    lt = _label_tab()
    assert "data=" not in lt._DRAG_JS
    assert "setTriggerValue" in lt._DRAG_JS
    # no detector name can reach the browser either
    for name in FORBIDDEN_NAMES:
        assert name not in lt._DRAG_JS


def test_a_missing_drag_bridge_does_not_break_labelling(monkeypatch):
    """Drag is a convenience; the table is the contract. An older Streamlit, or a
    changed component API, must cost nothing."""
    lt = _label_tab()
    monkeypatch.setattr(lt, "_drag_component",
                        lambda: (_ for _ in ()).throw(RuntimeError("no v2")))
    assert lt._read_drag() is None


# ══════════════════════════════════════════════════════════════════════════════
# 6. The detector read-out, and the end-to-end evaluation
# ══════════════════════════════════════════════════════════════════════════════

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

_LABELS = lc.read_labels()
_TRAIN = set(lc.read_split()["train"])
_TRAIN_LABELS = [r for sid, r in sorted(_LABELS.items()) if sid in _TRAIN]


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
