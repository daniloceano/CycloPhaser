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
    monkeypatch.setattr(ev, "_fmt_baselines", lambda sel: "")   # passo5: constant baselines
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


# ══════════════════════════════════════════════════════════════════════════
# item 30 part 3 — adjudicated labels are never pooled with a train number
# ══════════════════════════════════════════════════════════════════════════

ADJ = {"20120297", "19940445", "19810854", "19860380", "19870927"}


@pytest.fixture
def calls(monkeypatch):
    """The id set of every scoring call, in order."""
    out = []

    def score(sel, detected):
        out.append({r["id"] for r in sel})
        return {"n_scored": len(sel)}

    monkeypatch.setattr(ev, "run_detector",
                        lambda s, pv, gp: ({k: None for k in s}, {k: [] for k in s}))
    monkeypatch.setattr(ev, "score_labels", score)
    monkeypatch.setattr(ev, "score_phase_sequences", score)
    monkeypatch.setattr(ev, "_fmt", lambda m: "")
    monkeypatch.setattr(ev, "_fmt_phases", lambda m: "")
    monkeypatch.setattr(ev, "_fmt_baselines", lambda sel: "")   # passo5: constant baselines
    return out


def test_the_five_carry_the_adjudication_note_and_no_other_train_label_does():
    """TRAIN records only — test records are dropped by id before any field is
    read. That no test block changed is proven by adjudicate_item30.py (68/68
    other blocks byte-identical)."""
    train = set(lc.read_split()["train"]) | {
        s for s, m in lc.batch_membership(BATCH).items() if m == "train"}
    recs = {s: r for s, r in lc.read_labels().items() if s in train}
    assert {s for s, r in recs.items() if lc.is_adjudicated(r)} == ADJ


@pytest.mark.parametrize("against", ["current", "first-blind"])
def test_adjudicated_labels_score_only_in_their_own_block(calls, capsys, against):
    ev.main(["--batch-train", BATCH, "--against", against])
    for ids in calls:
        assert ids <= ADJ or ids.isdisjoint(ADJ), sorted(ids)
    own = [ids for ids in calls if ids and ids <= ADJ]
    assert own, "no ADJUDICATED block was scored"
    assert "ADJUDICATED" in capsys.readouterr().out


def test_the_default_path_scores_no_adjudicated_label(calls, capsys):
    ev.main([])
    assert all(ids.isdisjoint(ADJ) for ids in calls)
    assert "ADJUDICATED" not in capsys.readouterr().out


def test_the_pooling_guard_would_catch_a_leak(calls, monkeypatch):
    """POSITIVE CONTROL: with the note ignored, the five fall into the batch's
    TRAIN block next to the two others — the pooling the tests above forbid."""
    monkeypatch.setattr(ev, "is_adjudicated", lambda r: False)
    ev.main(["--batch-train", BATCH])
    assert any(ids & ADJ and not ids <= ADJ for ids in calls)
