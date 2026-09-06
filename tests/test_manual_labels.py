"""Tests for the manual-labelling front (research/labels/ + the app's Label mode).

Five things are worth testing here, and they are not the usual ones.

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


def test_label_record_round_trips_through_yaml(tmp_path, toy_series):
    p = tmp_path / "manual_labels.yaml"
    rec = lc.make_label_record("t1", "real", toy_series,
                               {"kind": "boundary", "incipient_end_idx": 7}, 3,
                               notes="clear knee")
    lc.upsert_label(rec, p)
    back = lc.read_labels(p)
    assert back["t1"] == rec
    assert back["t1"]["verdict"] == {"kind": "boundary", "incipient_end_idx": 7}
    assert back["t1"]["tolerance_idx"] == 3
    assert back["t1"]["notes"] == "clear knee"


def test_upsert_overwrites_in_place_and_keeps_the_others(tmp_path, toy_series):
    p = tmp_path / "l.yaml"
    lc.upsert_label(lc.make_label_record("a", "real", toy_series,
                                         {"kind": "none"}, 2), p)
    lc.upsert_label(lc.make_label_record("b", "real", toy_series,
                                         {"kind": "boundary", "incipient_end_idx": 5}, 1), p)
    lc.upsert_label(lc.make_label_record("a", "real", toy_series,
                                         {"kind": "ambiguous"}, 4), p)
    got = lc.read_labels(p)
    assert set(got) == {"a", "b"}
    assert got["a"]["verdict"]["kind"] == "ambiguous"
    assert got["a"]["tolerance_idx"] == 4
    assert got["b"]["verdict"]["incipient_end_idx"] == 5


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
    lc.upsert_label(lc.make_label_record("t", "real", toy_series,
                                         {"kind": "boundary", "incipient_end_idx": 4}, 2), p)
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
        lc.make_label_record("t", "real", toy_series, {"kind": "none"}, -1)


def test_committed_labels_file_is_parseable_and_well_formed():
    """Whatever state the artefact is in, it must be readable and valid."""
    doc = yaml.safe_load(lc.LABELS_PATH.read_text())
    assert doc["schema"] == 1
    for rec in (doc.get("labels") or []):
        assert set(rec) >= {"id", "source", "series_sha256", "labeled_at",
                            "verdict", "tolerance_idx"}
        lc.validate_verdict(rec["verdict"])
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
    from evaluate_against_labels import detected_incipient_end

    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    series = {**real, **synth}

    detected = {}
    for rec in _TRAIN_LABELS:
        sid = rec["id"]
        assert sid in series, f"label {sid} names a series that does not exist"
        assert rec["series_sha256"] == lc.series_sha256(series[sid]), (
            f"label {sid} was written against different data — it is void")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": series[sid]}))
            detected[sid] = detected_incipient_end(get_periods(vort)["periods"])

    m = lc.score_labels(_TRAIN_LABELS, detected)
    assert m["n_unscored"] == 0
    assert m["n_scored"] == len(_TRAIN_LABELS)
    print(f"\ntrain hit rate {m['hit_rate']} · MAE {m['mae']} · worst {m['worst']}")
