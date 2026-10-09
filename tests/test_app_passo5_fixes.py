"""Calibration app — the small fixes of the clean-up front's Passo 5.

* The track upload and the dataset choice live in the Calibration tab only: drawn
  above the tabs, they also showed in the Benchmark tab with a caption that is
  false there ("No file uploaded — using … as default"). Since the app redesign
  (I1) each page is its own, and this is checked on the Compare page (the
  Benchmark page was retired in the benchmark review, I3).
* (Until I3: the Benchmark preset buttons. Their defect — a selection kept apart
  from the multiselect, emptied by a second preset click — cannot occur on the
  Compare and Validate pages, whose selection IS the multiselect's key; their
  presets are tested in tests/test_compare_apptest.py and
  tests/test_validate_apptest.py.)
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


# ── AppTest: upload placement ─────────────────────────────────────────────────

def _app():
    pytest.importorskip("streamlit",
                        reason="AppTest drives the calibration app; the CI installs "
                               "only the wheel, pytest and pyyaml")
    from streamlit.testing.v1 import AppTest
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        at = AppTest.from_file(str(APP), default_timeout=300)
        at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _compare_app():
    at = _app()
    at.switch_page("app_pages/compare.py").run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_the_track_upload_and_its_caption_are_in_the_calibration_tab_only():
    """Since I2 the track upload is step 1 of the Calibrate sidebar, and the
    no-data screen is in Calibrate's main area; neither may show on Compare.
    (I3 replaced I2's one-line no-data text with the start screen, so the start
    screen's heading is what is looked for.)"""
    start = "Check CycloPhaser's phases on your cyclone tracks"
    cal = _app()
    assert "track_upload" in [w.key for w in cal.sidebar.get("file_uploader")]
    assert any(h.value == start for h in cal.main.subheader)
    other = _compare_app()
    assert [t.value for t in other.title] == ["Compare configurations"]   # control
    assert "track_upload" not in [w.key for w in other.get("file_uploader")]
    assert not any(h.value == start for h in other.main.subheader)
