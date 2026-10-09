"""validate_core — the label-side logic behind the Validate page (benchmark review, I2).

Gated on streamlit like every other test of the calibration app: the CI recipe
installs only the wheel, pytest and PyYAML, and app tests stay out of it.

Controls: the instruments are checked against direct calls of the Benchmark's
own functions; the disagreement lists against the instruments' counts; the
figures without the new option against the module as it was at f3008fc, and
with it against themselves (the option must change the PNG).
"""

from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "tools" / "calibration_app"

pytest.importorskip("streamlit")
pytest.importorskip("yaml")
sys.path.insert(0, str(APP_DIR))
import benchmark_core as bc  # noqa: E402
import labels_core as lc  # noqa: E402
import layer_inspector as li  # noqa: E402
import phase_figures as pf  # noqa: E402
import validate_core as vc  # noqa: E402

REC = {"id": "x", "n_steps": 40, "phases": [
    {"phase": "incipient", "start_idx": 0, "tolerance_idx": 0},
    {"phase": "intensification", "start_idx": 10, "tolerance_idx": 2},
    {"phase": "mature", "start_idx": 20, "tolerance_idx": 2},
    {"phase": "decay", "start_idx": 30, "tolerance_idx": 3, "unsure": True}]}


def _cell(runs):
    return {"error": None, "runs": [tuple(r) for r in runs], "z": None}


def _read_paths(monkeypatch) -> list[str]:
    """Every CSV path labels_core opens from now on."""
    seen: list[str] = []
    real = lc.pd.read_csv

    def spy(path, *a, **k):
        seen.append(str(path))
        return real(path, *a, **k)
    monkeypatch.setattr(lc.pd, "read_csv", spy)
    return seen


def _perfect(pop) -> dict:
    """Cells that reproduce every offered label exactly."""
    return {s: _cell(vc.label_runs(r)) for s, r in pop["labels"].items()}


def test_population_offers_train_only_and_withholds_test_labels(monkeypatch):
    seen = _read_paths(monkeypatch)
    pop = vc.load_population(False)
    split = lc.read_split()
    spent = vc.spent_ids()
    assert len(spent) == 19 and set(map(str, split["test"])) <= spent
    assert sorted(pop["series"]) == sorted(map(str, split["train"]))
    assert len(pop["series"]) == 47
    assert sum(1 for s in pop["source"].values() if s == "real") == 35
    assert sum(1 for s in pop["source"].values() if s == "synthetic") == 12
    assert set(pop["labels"]) == set(pop["series"])
    assert not spent & (set(pop["series"]) | set(pop["labels"]))
    # the test files are never opened, not merely dropped after reading
    stems = {Path(p).stem for p in seen}
    assert stems and not stems & spent, stems & spent
    assert pop["adjudicated"] == [] and pop["batch_ids"] == []


def test_batch_adds_seven_train_tracks_and_never_its_test_ones(monkeypatch):
    seen = _read_paths(monkeypatch)
    pop = vc.load_population(True)
    batch = lc.batch_membership(vc.BATCH)
    b_train = sorted(s for s, m in batch.items() if m == "train")
    b_test = {s for s, m in batch.items() if m == "test"}
    assert len(b_train) == 7 and len(b_test) == 3
    assert pop["batch_ids"] == b_train and pop["batch_error"] is None
    assert len(pop["series"]) == 54
    assert not b_test & set(pop["series"]) and not b_test & set(pop["labels"])
    assert not {Path(p).stem for p in seen} & b_test
    assert len(pop["adjudicated"]) == 5 and set(pop["adjudicated"]) <= set(b_train)


def test_blocks_train_and_adjudicated_are_disjoint_and_never_summed():
    pop = vc.load_population(True)
    ids = list(pop["series"])
    m = vc.agreement(_perfect(pop), pop["labels"], ids, pop["adjudicated"])
    assert set(m) == {vc.TRAIN, vc.ADJUDICATED}
    train, adj = m[vc.TRAIN], m[vc.ADJUDICATED]
    assert len(train["ids"]) == 49 and len(adj["ids"]) == 5
    assert not set(train["ids"]) & set(adj["ids"])
    assert sorted(adj["ids"]) == pop["adjudicated"]
    # control: a configuration that reproduces the labels agrees everywhere
    for blk, n in ((train, 49), (adj, 5)):
        assert blk["sequence"]["n_series"] == n
        assert blk["sequence"]["n_sequence_match"] == n
        assert blk["sequence"]["n_boundaries_hit"] == blk["sequence"]["n_boundaries"]
        assert blk["mature"]["n_hit"] == blk["mature"]["n"]
    # batch off: no adjudicated id at all
    pop0 = vc.load_population(False)
    m0 = vc.agreement(_perfect(pop0), pop0["labels"], list(pop0["series"]),
                      pop0["adjudicated"])
    assert len(m0[vc.TRAIN]["ids"]) == 47 and m0[vc.ADJUDICATED]["ids"] == []


def _shifted(pop) -> dict:
    """Every other label with its mature start moved 3 steps later, and every
    third with its last phase dropped (a sequence difference)."""
    cells = {}
    for k, (s, rec) in enumerate(sorted(pop["labels"].items())):
        runs = [list(r) for r in vc.label_runs(rec)]
        if k % 3 == 0 and len(runs) > 1:
            runs[-2][2] = runs[-1][2]
            runs = runs[:-1]
        elif k % 2 == 0:
            for i, r in enumerate(runs):
                if r[0] == "mature" and i > 0 and r[1] + 3 <= r[2]:
                    runs[i - 1][2] += 3
                    r[1] += 3
        cells[s] = _cell(runs)
    return cells


def test_agreement_uses_the_two_benchmark_instruments_unchanged():
    pop = vc.load_population(False)
    ids = list(pop["series"])
    cells = _shifted(pop)
    m = vc.agreement(cells, pop["labels"], ids, [])[vc.TRAIN]
    res = vc.as_results(cells)
    assert m["sequence"] == bc.sequence_metrics(res, pop["labels"], ids)
    assert m["mature"] == bc.mature_metrics(res, pop["labels"], ids)
    direct = lc.score_phase_sequences([pop["labels"][s] for s in ids],
                                      {s: res[s]["starts"] for s in ids})
    for k in ("n_series", "n_sequence_match", "n_boundaries", "n_boundaries_hit",
              "n_boundaries_unsure"):
        assert m["sequence"][k] == direct[k], k
    assert m["sequence"]["instrument"] == bc.SEQUENCE_INSTRUMENT
    assert m["mature"]["instrument"] == bc.MATURE_INSTRUMENT
    # control: the perturbation is visible to both instruments
    assert m["sequence"]["n_sequence_match"] < m["sequence"]["n_series"]
    assert m["mature"]["n_hit"] <= m["mature"]["n"]


def test_track_notes_sequence_and_mature_offsets():
    ok = vc.track_note(_cell(vc.label_runs(REC)), REC)
    assert ok == {"sequence": "agrees", "outside": 0, "scored": 2,
                  "mature": {"d_start": 0, "d_end": 0, "within": True}}
    late = [("incipient", 0, 9), ("intensification", 10, 22), ("mature", 23, 29),
            ("decay", 30, 39)]
    n = vc.track_note(_cell(late), REC)
    # mature starts 3 late (tolerance 2): one of the two compared boundaries is
    # outside; the decay boundary is unsure and not compared
    assert (n["sequence"], n["outside"], n["scored"]) == ("agrees", 1, 2)
    assert n["mature"] == {"d_start": 3, "d_end": 0, "within": True}
    short = [("incipient", 0, 9), ("intensification", 10, 19), ("mature", 20, 39)]
    n = vc.track_note(_cell(short), REC)
    assert (n["sequence"], n["outside"], n["scored"]) == ("differs", 0, 0)
    assert n["mature"]["d_end"] == 10 and not n["mature"]["within"]
    none = vc.track_note({"error": "boom", "runs": None, "z": None}, REC)
    assert none["sequence"] is None and none["mature"] is None


def test_disagreement_lists_per_instrument():
    pop = vc.load_population(False)
    ids = list(pop["series"])
    cells = _shifted(pop)
    cells[ids[0]] = {"error": "boom", "runs": None, "z": None}
    d = vc.disagreements(cells, pop["labels"], ids)
    m = vc.agreement(cells, pop["labels"], ids, [])[vc.TRAIN]
    seq, mat = m["sequence"], m["mature"]
    assert d["failed"] == [ids[0]]
    assert len(d["sequence_differs"]) == seq["n_series"] - seq["n_sequence_match"]
    assert sum(k for _s, k, _m in d["outside_tolerance"]) == \
        seq["n_boundaries"] - seq["n_boundaries_hit"]
    assert len(d["mature"]) == mat["n"] - mat["n_hit"]
    assert d["sequence_differs"] and d["outside_tolerance"]       # controls
    per_col = [d, vc.disagreements(_perfect(pop), pop["labels"], ids)]
    assert vc.disagrees(per_col, ids[0])
    clean = [s for s in ids if not vc.disagrees([per_col[0]], s)]
    assert clean and not any(vc.disagrees(per_col[1:], s) for s in ids)


def test_tolerance_spans_from_a_label():
    assert vc.tolerance_spans(REC) == ((8, 12, 10, False), (18, 22, 20, False),
                                       (27, 33, 30, True))
    wide = {**REC, "phases": [REC["phases"][0],
                              {"phase": "mature", "start_idx": 3, "tolerance_idx": 9},
                              {"phase": "decay", "start_idx": 36, "tolerance_idx": 9}]}
    assert vc.tolerance_spans(wide) == ((0, 12, 3, False), (27, 39, 36, False))


def test_figures_without_tolerances_are_byte_identical_and_with_them_differ(tmp_path):
    try:
        old_src = subprocess.run(
            ["git", "show", "f3008fc:tools/calibration_app/phase_figures.py"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    except Exception as exc:                            # no git, or no history
        pytest.skip(f"f3008fc not available: {exc}")
    path = tmp_path / "old_phase_figures.py"
    path.write_text(old_src)
    try:
        spec = importlib.util.spec_from_file_location("old_phase_figures", path)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
    finally:
        path.unlink()
    v = tuple(math.sin(i / 7) * 1e-5 for i in range(90))
    z = tuple(math.sin(i / 9) * 4e-6 for i in range(90))
    runs = (("incipient", 0, 10), ("intensification", 11, 30), ("mature", 31, 45),
            ("decay", 46, 80), ("residual", 81, 89))
    panels = (("a", runs, z), ("b", runs[1:], None))
    import benchmark_tab
    for colors in (li.PHASE_COLORS, benchmark_tab.PHASE_COLORS):
        assert pf.png(pf.cell_figure(v, runs, "a", z, colors)) == \
            old.png(old.cell_figure(v, runs, "a", z, colors))
        assert pf.png(pf.cell_figure(v, runs, "a", None, colors)) == \
            old.png(old.cell_figure(v, runs, "a", None, colors))
        assert pf.png(pf.stacked_figure(v, panels, colors)) == \
            old.png(old.stacked_figure(v, panels, colors))
    spans = ((9, 13, 11, False), (40, 50, 46, True))
    plain = pf.png(pf.cell_figure(v, runs, "label", None, li.PHASE_COLORS))
    assert pf.png(pf.cell_figure(v, runs, "label", None, li.PHASE_COLORS,
                                 tolerances=spans)) != plain
    assert pf.png(pf.stacked_figure(v, panels, li.PHASE_COLORS,
                                    tolerances=(spans, None))) != \
        pf.png(pf.stacked_figure(v, panels, li.PHASE_COLORS))
    assert not path.exists()


def test_a_label_whose_series_hash_differs_is_not_used(monkeypatch):
    pop = vc.load_population(False)
    victim = sorted(pop["series"])[0]
    assert victim in pop["labels"]                      # control: used when it matches
    real = bc.labels_for_display

    def tampered():
        labels = real()
        labels[victim] = {**labels[victim], "series_sha256": "0" * 64}
        return labels
    monkeypatch.setattr(bc, "labels_for_display", tampered)
    pop2 = vc.load_population(False)
    assert victim not in pop2["series"] and victim not in pop2["labels"]
    assert "series_sha256" in pop2["not_offered"][victim]
    assert len(pop2["series"]) == 46


def test_snapshot_missing_tracks_are_not_failures():
    """I2 round 2, R3: a published release never ran on the batch tracks; those
    cells are `missing`, never a failed detection and never a disagreement."""
    snap = bc.load_snapshot(bc.SNAPSHOT_DIR / "v2.0.0.json")
    pop = vc.load_population(True)
    ids = list(pop["series"])
    cells = {s: vc.snapshot_cell(snap, s) for s in ids}
    miss = vc.missing(cells, ids)
    assert sorted(miss) == pop["batch_ids"] and len(miss) == 7
    assert all(cells[s]["error"] == vc.NOT_IN_SNAPSHOT for s in miss)
    d = vc.disagreements(cells, pop["labels"], ids)
    assert d["not_in_snapshot"] == miss and not set(miss) & set(d["failed"])
    assert not any(vc.disagrees([d], s) for s in miss)
    # control: the bundled tracks are in the snapshot and carry phases
    assert all(cells[s]["runs"] for s in ids if s not in miss)
    m = vc.agreement(cells, pop["labels"], ids, pop["adjudicated"])
    assert m[vc.TRAIN]["sequence"]["n_series"] == 49 - 2       # 2 batch train ids
    assert m[vc.ADJUDICATED]["sequence"]["n_series"] == 0
