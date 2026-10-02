"""Calibration app — the small fixes of the clean-up front's Passo 5.

* The track upload and the dataset choice live in the Calibration tab only: drawn
  above the tabs, they also showed in the Benchmark tab with a caption that is
  false there ("No file uploaded — using … as default").
* The Benchmark preset buttons (All real, All synthetic, Train, Test, Invert,
  Clear) keep the "Choose individually" multiselect in step with the selection:
  before, any second preset click emptied the selection (e.g. Train, then Test).
* A binary upload (Parquet, zip, netCDF/HDF5, GRIB, gzip, or anything with a NUL
  byte) is refused with a message that says so, instead of a decoder error.

Only counts and equalities of selections are asserted; no test prints or pins a
track id, and nothing here runs the detector on the test split.
"""
import sys
import warnings
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP = REPO_ROOT / "tools" / "calibration_app" / "app.py"
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))

import track_io as tio  # noqa: E402


# ── binary uploads ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("data, kind", [
    (b"PAR1\x15\x04\x15\x00\x15", "Parquet"),
    (b"PK\x03\x04\x14\x00\x00", "zip"),
    (b"\x89HDF\r\n\x1a\n\x00\x00", "HDF5"),
    (b"CDF\x01\x00\x00\x00\x00", "netCDF"),
    (b"GRIB\x00\x00\x00\x00", "GRIB"),
    (b"\x1f\x8b\x08\x00", "gzip"),
    (b"time;min_max_zeta_850\n2015-01-01 00:00:00;\x00\x00", "unrecognised binary"),
])
@pytest.mark.parametrize("fmt", [None, tio.CustomFormat()])
def test_a_binary_upload_is_refused_with_a_clear_message(data, kind, fmt):
    with pytest.raises(tio.TrackFormatError) as err:
        tio.read_track(data, fmt)
    msg = str(err.value)
    assert "binary file" in msg and kind in msg
    assert "codec" not in msg


def test_a_text_track_is_not_taken_for_binary():
    data = (REPO_ROOT / "docs" / "data" / "example_track_hourly.csv").read_bytes()
    assert tio.binary_kind(data) is None
    assert len(tio.read_track(data)) > 2


# ── AppTest: upload placement and the Benchmark selection ─────────────────────

def _app():
    from streamlit.testing.v1 import AppTest
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        at = AppTest.from_file(str(APP), default_timeout=300)
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _tab(at, label):
    return next(t for t in at.tabs if t.label == label)


def test_the_track_upload_and_its_caption_are_in_the_calibration_tab_only():
    at = _app()
    cal, bench = _tab(at, "Calibration"), _tab(at, "Benchmark")
    assert [w.key for w in cal.get("file_uploader")] == ["track_upload"]
    assert "track_upload" not in [w.key for w in bench.get("file_uploader")]
    assert any("No file uploaded" in c.value for c in cal.caption)
    assert not any("No file uploaded" in c.value for c in bench.caption)


def _click(at, key):
    next(b for b in at.button if b.key == key).click()
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    widget = next(w for w in at.multiselect if w.key == "bench_ids_widget")
    selected = list(at.session_state["bench_selected_ids"])
    # the multiselect shows exactly the selection
    assert len(widget.indices) == len(selected)
    return selected


@pytest.mark.parametrize("first, second", [
    ("bench_pick_train", "bench_pick_test"),
    ("bench_pick_test", "bench_pick_train"),
    ("bench_pick_real", "bench_pick_synth"),
    ("bench_pick_train", "bench_pick_train"),
    ("bench_pick_train", "bench_pick_invert"),
])
def test_a_second_preset_click_gives_what_the_button_gives_on_its_own(first, second):
    fresh = _click(_app(), second)
    at = _app()
    after_first = _click(at, first)
    assert after_first, "the first preset selected nothing"
    after_second = _click(at, second)
    if second == "bench_pick_invert":
        # from an empty selection Invert offers everything; after the first
        # preset it must give everything except that preset's records
        assert set(after_second) == set(fresh) - set(after_first) and after_second
    else:
        assert set(after_second) == set(fresh) and after_second, (
            "the second preset did not give its own selection")


def test_clear_empties_both_the_selection_and_the_widget():
    at = _app()
    assert _click(at, "bench_pick_train")
    assert _click(at, "bench_pick_none") == []
