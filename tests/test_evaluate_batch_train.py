"""`evaluate_against_labels.py --batch-train`: the batch's TEST cases reach nothing.

The option adds the TRAIN part of a frozen split.yaml batch as its own scored
block. What must never happen is a TEST id — of the 47/16 split or of the batch —
entering any aggregate, or even having one of its fields read by a check. The
detector is stubbed: this pins WHICH ids flow where, not what the detector says.
"""

import sys
from pathlib import Path

import pytest

pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "research" / "labels"))
import evaluate_against_labels as ev  # noqa: E402
import labels_core as lc  # noqa: E402

BATCH = lc.SWELL_BATCH


def _test_ids() -> set:
    sp = lc.read_split()
    return set(sp["test"]) | {s for s, m in lc.batch_membership(BATCH).items() if m == "test"}


@pytest.fixture
def capture(monkeypatch):
    seen = {"detector": set(), "scored": set(), "checked": set()}

    def run_detector(series, pv, gp):
        seen["detector"] |= set(series)
        return {k: None for k in series}, {k: [] for k in series}

    def score(sel, detected):
        seen["scored"] |= {r["id"] for r in sel}
        return {"n_scored": len(sel)}

    real_legacy = ev.is_legacy_record

    def legacy(r):
        seen["checked"].add(r["id"])
        return real_legacy(r)

    monkeypatch.setattr(ev, "run_detector", run_detector)
    monkeypatch.setattr(ev, "score_labels", score)
    monkeypatch.setattr(ev, "score_phase_sequences", score)
    monkeypatch.setattr(ev, "_fmt", lambda m: "")
    monkeypatch.setattr(ev, "_fmt_phases", lambda m: "")
    monkeypatch.setattr(ev, "is_legacy_record", legacy)
    return seen


def test_batch_train_never_touches_a_test_id(capture, capsys):
    assert ev.main(["--batch-train", BATCH]) == 0
    test_ids = _test_ids()
    assert len(test_ids) == 16 + 3
    for where, ids in capture.items():
        assert ids.isdisjoint(test_ids), (where, sorted(ids & test_ids))
    train = {s for s, m in lc.batch_membership(BATCH).items() if m == "train"}
    labelled = set(lc.read_labels()) & train     # ids only
    assert labelled <= capture["scored"]
    assert f"BATCH {BATCH} · TRAIN" in capsys.readouterr().out


def test_batch_train_is_not_pooled_with_the_split(capture):
    ev.main(["--batch-train", BATCH])
    split_train = set(lc.read_split()["train"])
    train = {s for s, m in lc.batch_membership(BATCH).items() if m == "train"}
    assert split_train.isdisjoint(train)


def test_batch_train_refuses_test():
    with pytest.raises(SystemExit):
        ev.main(["--batch-train", BATCH, "--test"])


def test_unknown_batch_is_an_error():
    with pytest.raises(SystemExit):
        ev.main(["--batch-train", "no_such_batch"])
