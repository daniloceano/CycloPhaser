"""The calibration app's one track reader (`tools/calibration_app/track_io.py`).

What is pinned here, and why:

* **The standard path is the old path.** A standard file must come out of
  `read_track` bit-identical (values AND index) to the bare `read_csv` the app
  used before, on every bundled series — otherwise every result the app has
  produced would silently shift.
* **A custom layout reproduces the original exactly.** A non-standard file is
  built from a real calibration track — separator ',', columns reordered
  (lat, vor, lon, date), dates in a non-ISO format — and read through a
  `CustomFormat`; it must equal the same track read the standard way.
* **Nothing is accepted silently.** `parse_dates=True` keeps unparseable dates
  as text without a word, and reads day-first dates month-first without one
  (`05/01/2015` → 1 May), so each failure mode gets its own negative test and
  must raise `TrackFormatError` with the cause.
* **`package_use_filter`** maps only `True` to `'auto'`; in particular the
  integer 1 is a literal window and must stay 1.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))
import track_io as tio  # noqa: E402
from package_args import package_use_filter  # noqa: E402

CAL = REPO_ROOT / "tests" / "calibration_data"
SYN = REPO_ROOT / "tests" / "synthetic" / "data"
EXAMPLE = REPO_ROOT / "cyclophaser" / "example_data" / "example_file.csv"
SOURCE = CAL / "20150069.csv"

ALL_SERIES = sorted(CAL.glob("*.csv")) + sorted(SYN.glob("*.csv")) + [EXAMPLE]


def _old_read(data: bytes) -> pd.Series:
    """The reader app.py used before track_io existed, verbatim."""
    df = pd.read_csv(io.BytesIO(data), sep=";", index_col="time", parse_dates=True)
    return df["min_max_zeta_850"]


def _identical(a: pd.Series, b: pd.Series) -> bool:
    return (np.array_equal(a.to_numpy(), b.to_numpy())
            and np.array_equal(a.index.to_numpy(), b.index.to_numpy())
            and a.dtype == b.dtype and type(a.index) is type(b.index))


def _custom_file(source: Path = SOURCE, date_fmt: str = "%d/%m/%Y %Hh%M",
                 sign: int = 1) -> bytes:
    """`source` rewritten as ',' + lat,vor,lon,date + non-ISO dates.

    The vorticity is carried as the ORIGINAL text token, so the comparison is
    about the reader, not about float formatting.
    """
    lines = source.read_text().splitlines()[1:]
    rows = ["lat,vor,lon,date"]
    for i, line in enumerate(lines):
        t, v = line.split(";")
        if sign < 0:
            v = v[1:] if v.startswith("-") else "-" + v
        rows.append(f"{-30 - i * 0.1:.2f},{v},{-45 + i * 0.1:.2f},"
                    f"{pd.Timestamp(t).strftime(date_fmt)}")
    return ("\n".join(rows) + "\n").encode()


FMT = tio.CustomFormat(sep=",", header=True, date_col="date", vort_col="vor",
                       date_format="%d/%m/%Y %Hh%M")


# ── the standard path is the old path ─────────────────────────────────────────
@pytest.mark.parametrize("path", ALL_SERIES, ids=lambda p: p.stem)
def test_standard_read_is_bit_identical_to_the_old_reader(path):
    data = path.read_bytes()
    assert tio.is_standard(data)
    assert _identical(tio.read_track(data), _old_read(data))


def test_the_bundled_population_is_the_one_the_gate_counts():
    # 51 real + 12 synthetic + example_file = 64 series.
    assert len(ALL_SERIES) == 64


def test_normalize_returns_a_standard_file_unchanged():
    data = SOURCE.read_bytes()
    assert tio.normalize_track(data) is data


def test_standard_content_is_accepted_whatever_the_extension():
    # The reader never sees a name; the app's .txt acceptance is covered by
    # tests/test_track_upload_apptest.py. Here: the same bytes, the same series.
    data = SOURCE.read_bytes()
    assert _identical(tio.read_track(data), _old_read(data))


def test_standard_header_wins_even_with_a_custom_format_active():
    data = SOURCE.read_bytes()
    assert _identical(tio.read_track(data, FMT), _old_read(data))


# ── custom layout ─────────────────────────────────────────────────────────────
def test_custom_layout_reproduces_the_original_track():
    data = _custom_file()
    assert not tio.is_standard(data)
    original = _old_read(SOURCE.read_bytes())
    got = tio.read_track(data, FMT)
    assert _identical(got, original)


def test_custom_layout_with_auto_separator_and_inferred_iso_dates():
    lines = SOURCE.read_text().splitlines()[1:]
    data = ("date\tvor\n" + "\n".join(l.replace(";", "\t") for l in lines)
            + "\n").encode()
    got = tio.read_track(data, tio.CustomFormat(sep="auto", date_col="date",
                                                vort_col="vor"))
    assert _identical(got, _old_read(SOURCE.read_bytes()))


def test_custom_layout_without_header_uses_1_based_column_numbers():
    lines = SOURCE.read_text().splitlines()[1:]
    data = "\n".join(f"x  {v}   {pd.Timestamp(t):%Y%m%d%H}"
                     for t, v in (l.split(";") for l in lines)).encode()
    fmt = tio.CustomFormat(sep="whitespace", header=False, date_col="3",
                           vort_col="2", date_format="%Y%m%d%H")
    assert _identical(tio.read_track(data, fmt), _old_read(SOURCE.read_bytes()))


# ── negative: nothing accepted silently ───────────────────────────────────────
def test_non_standard_file_without_custom_format_is_refused_with_a_pointer():
    with pytest.raises(tio.TrackFormatError, match="Custom track format"):
        tio.read_track(_custom_file())


def test_unparseable_date_is_an_error():
    data = _custom_file().replace(b"27/01/2015 04h00", b"not a date", 1)
    with pytest.raises(tio.TrackFormatError, match="dates"):
        tio.read_track(data, FMT)


def test_date_not_matching_the_given_format_is_an_error():
    with pytest.raises(tio.TrackFormatError, match="dates"):
        tio.read_track(_custom_file(), tio.CustomFormat(
            sep=",", date_col="date", vort_col="vor", date_format="%Y-%m-%d"))


def test_non_numeric_vorticity_column_is_an_error():
    lines = _custom_file().decode().splitlines()
    parts = lines[5].split(",")
    parts[1] = "abc"
    lines[5] = ",".join(parts)
    with pytest.raises(tio.TrackFormatError, match="not numeric: 'abc'"):
        tio.read_track(("\n".join(lines) + "\n").encode(), FMT)


def test_picking_a_non_numeric_column_as_vorticity_is_an_error():
    with pytest.raises(tio.TrackFormatError, match="not numeric"):
        tio.read_track(_custom_file(), tio.CustomFormat(
            sep=",", date_col="date", vort_col="date",
            date_format="%d/%m/%Y %Hh%M"))


def test_missing_column_names_the_available_ones():
    with pytest.raises(tio.TrackFormatError, match="'lat', 'vor', 'lon', 'date'"):
        tio.read_track(_custom_file(), tio.CustomFormat(
            sep=",", date_col="date", vort_col="zeta"))


def test_standard_layout_with_text_dates_is_an_error():
    # parse_dates=True alone would keep these as text without a word.
    lines = SOURCE.read_text().splitlines()
    body = [f"step {i};{l.split(';')[1]}" for i, l in enumerate(lines[1:])]
    data = ("\n".join([lines[0]] + body) + "\n").encode()
    with pytest.raises(tio.TrackFormatError, match="YYYY-MM-DD"):
        tio.read_track(data)


AMBIGUOUS = b"time;min_max_zeta_850\n05/01/2015 00:00;-1e-5\n06/01/2015 00:00;-2e-5\n"


def test_day_first_dates_are_misread_silently_by_bare_parse_dates():
    # The hazard the year-first rule exists for: 5 and 6 January come back as
    # 1 May and 1 June, increasing, with no warning — validation alone passes.
    s = _old_read(AMBIGUOUS)
    assert list(s.index.month) == [5, 6]


def test_day_first_dates_are_refused_on_the_standard_path():
    with pytest.raises(tio.TrackFormatError, match="05/01/2015"):
        tio.read_track(AMBIGUOUS)


def test_day_first_dates_need_an_explicit_format_on_the_custom_path():
    data = AMBIGUOUS.replace(b"time;min_max_zeta_850", b"t;z")
    with pytest.raises(tio.TrackFormatError, match="YYYY-MM-DD"):
        tio.read_track(data, tio.CustomFormat(sep=";", date_col="t", vort_col="z"))
    s = tio.read_track(data, tio.CustomFormat(sep=";", date_col="t", vort_col="z",
                                              date_format="%d/%m/%Y %H:%M"))
    assert list(s.index.day) == [5, 6] and list(s.index.month) == [1, 1]


@pytest.mark.parametrize("body, match", [
    ("2000-01-01 00:00:00;-1e-5\n2000-01-01 00:00:00;-2e-5\n", "duplicate date"),
    ("2000-01-01 03:00:00;-1e-5\n2000-01-01 00:00:00;-2e-5\n", "increasing order"),
    ("2000-01-01 00:00:00;-1e-5\n2000-01-01 03:00:00;\n", "missing value"),
    ("2000-01-01 00:00:00;-1e-5\n", "at least 2"),
    ("2000-01-01 00:00:00;-1\n2000-01-01 03:00:00;-2\n", "not float64"),
], ids=["duplicate", "decreasing", "nan", "one_point", "integer"])
def test_validation_refuses(body, match):
    with pytest.raises(tio.TrackFormatError, match=match):
        tio.read_track(("time;min_max_zeta_850\n" + body).encode())


# ── preview warnings ──────────────────────────────────────────────────────────
def test_positive_vorticity_warns_about_the_southern_hemisphere():
    s = tio.read_track(_custom_file(sign=-1), FMT)
    assert any("SOUTHERN hemisphere" in w for w in tio.plausibility_warnings(s))
    s = tio.read_track(_custom_file(), FMT)
    assert tio.plausibility_warnings(s) == []      # positive control


def test_a_latitude_picked_as_vorticity_warns_about_its_magnitude():
    s = tio.read_track(_custom_file(), tio.CustomFormat(
        sep=",", date_col="date", vort_col="lat", date_format="%d/%m/%Y %Hh%M"))
    assert any("wrong column" in w for w in tio.plausibility_warnings(s))


# ── use_filter translation ────────────────────────────────────────────────────
@pytest.mark.parametrize("value, expected", [
    (True, "auto"), (False, False), ("auto", "auto"), (1, 1), (24, 24)])
def test_package_use_filter(value, expected):
    out = package_use_filter(value)
    assert out == expected and type(out) is type(expected)
