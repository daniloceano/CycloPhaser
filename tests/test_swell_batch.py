"""The item-30 swell batch of research/labels/split.yaml — frozen, and additive only.

Guards two things. The batch on disk is the batch its declared seed and rule
draw from the committed groups (a batch edited by hand is not a draw). And the
batch changes nothing about the 63 series every other reader already sees: the
51 real series stay 51, and no batch id collides with the frozen 47/16 split.
"""

import hashlib
import sys
from pathlib import Path

import pytest

pytest.importorskip("yaml")
import yaml  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
sys.path.insert(0, str(REPO_ROOT / "research" / "labels" / "swell_item30"))
import labels_core as lc  # noqa: E402
import draw_batch  # noqa: E402


def _block():
    return lc.read_split()["batches"][lc.SWELL_BATCH]


def test_groups_file_is_the_pinned_one():
    got = hashlib.sha256(draw_batch.GROUPS_FILE.read_bytes()).hexdigest()
    assert got == draw_batch.GROUPS_SHA256 == _block()["groups_file_sha256"]


def test_committed_batch_is_what_the_seed_draws():
    blk = _block()
    groups = yaml.safe_load(draw_batch.GROUPS_FILE.read_text())["groups"]
    assignment, sizes = draw_batch.draw(groups)
    assert blk["seed"] == draw_batch.SEED == 20260925
    assert sizes == blk["group_sizes_after_exclusion"]
    assert blk["group"] == {s: g for s, (g, _) in assignment.items()}
    assert blk["train"] == sorted(s for s, (_, m) in assignment.items() if m == "train")
    assert blk["test"] == sorted(s for s, (_, m) in assignment.items() if m == "test")


def test_batch_shape_7_train_3_test_by_group():
    blk = _block()
    assert len(blk["train"]) == 7 and len(blk["test"]) == 3
    assert set(blk["train"]).isdisjoint(blk["test"])
    per = {g: [0, 0] for g in "RSC"}
    for sid, g in blk["group"].items():
        per[g][0 if sid in blk["train"] else 1] += 1
    assert per == {"R": [4, 1], "S": [2, 1], "C": [1, 1]}


def test_batch_is_disjoint_from_the_63_and_leaves_them_alone():
    doc = lc.read_split()
    blk = doc["batches"][lc.SWELL_BATCH]
    old = set(doc["train"]) | set(doc["test"])
    new = set(blk["train"]) | set(blk["test"])
    assert len(old) == 63 and new.isdisjoint(old)
    assert set(blk["excluded_overlap"]) <= old
    assert len(lc.load_real_series()) == 51


def test_batch_series_load_with_their_recorded_hashes():
    series = lc.load_batch_series()
    blk = _block()
    assert sorted(series) == sorted(blk["train"] + blk["test"])
    for sid, s in series.items():
        assert len(s) > 0 and (s < 0).all(), sid        # SH cyclone: negative zeta


# ══════════════════════════════════════════════════════════════════════════
# item 30 part 3 — the VALIDATION batch: frozen, in no default path
# ══════════════════════════════════════════════════════════════════════════

VAL = {"19900808", "19940737", "19960808", "20000821", "19861089"}


def _val_block():
    return lc.read_split()["batches"][lc.VALIDATION_BATCH]


def test_validation_block_is_validation_only():
    blk = _val_block()
    assert blk["role"] == "validation" and blk["frozen"] is True
    assert blk["train"] == [] and blk["test"] == []
    assert set(blk["validation"]) == VAL
    assert lc.batch_membership(lc.VALIDATION_BATCH) == {s: "validation" for s in VAL}


def test_validation_files_carry_their_recorded_hashes():
    blk = _val_block()
    d = REPO_ROOT / blk["data_dir"]
    assert sorted(p.stem for p in d.glob("*.csv")) == sorted(VAL)
    for sid in VAL:
        got = hashlib.sha256((d / f"{sid}.csv").read_bytes()).hexdigest()
        assert got == blk["file_sha256"][sid], sid
    assert set(lc.load_batch_series(lc.VALIDATION_BATCH)) == VAL


def test_validation_is_disjoint_from_everything_else():
    doc = lc.read_split()
    others = (set(doc["train"]) | set(doc["test"])
              | set(lc.batch_membership(lc.SWELL_BATCH)))
    assert VAL.isdisjoint(others)


def test_validation_is_in_no_default_loader():
    assert VAL.isdisjoint(lc.load_real_series())
    assert VAL.isdisjoint(lc.load_batch_series())            # the default batch
    split = lc.read_split()
    assert VAL.isdisjoint(set(split["train"]) | set(split["test"]))


def test_validation_is_not_in_the_benchmark_even_with_the_batch_on():
    sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
    import benchmark_core as bc
    series, _ = bc.load_all_series()
    b_series, b_membership = bc.load_batch(series)
    assert VAL.isdisjoint(series) and VAL.isdisjoint(b_series)
    assert VAL.isdisjoint(bc.split_membership()) and VAL.isdisjoint(b_membership)


def test_the_evaluator_never_reaches_the_validation_batch(monkeypatch):
    import evaluate_against_labels as ev
    seen = set()

    def run_detector(series, pv, gp):
        seen.update(series)
        return {k: None for k in series}, {k: [] for k in series}

    monkeypatch.setattr(ev, "run_detector", run_detector)
    monkeypatch.setattr(ev, "score_labels", lambda sel, d: {"n_scored": len(sel)})
    monkeypatch.setattr(ev, "score_phase_sequences", lambda sel, d: {})
    monkeypatch.setattr(ev, "_fmt", lambda m: "")
    monkeypatch.setattr(ev, "_fmt_phases", lambda m: "")
    for argv in ([], ["--batch-train", lc.SWELL_BATCH],
                 ["--batch-train", lc.VALIDATION_BATCH]):
        ev.main(argv)
    assert seen, "the detector stub was never called — the check proves nothing"
    assert VAL.isdisjoint(seen)
