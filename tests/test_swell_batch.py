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
