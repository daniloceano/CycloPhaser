"""Reading cyclone tracks for the calibration app — one reader, any extension.

Why this module exists
----------------------
The app used to read a track in three duplicated places, each a bare
``pd.read_csv(sep=";", index_col="time", parse_dates=True)``, and both upload
fields declared ``type=["csv"]``, so a ``.txt`` file with identical content was
turned away by the browser before any code saw it. Worse, that read call does
not fail on dates: ``parse_dates=True`` keeps an unrecognised column as text,
and infers the layout of a recognised one from its first value — so
``05/01/2015`` is read as 1 May, without a warning. A malformed track was
therefore either refused for its extension or accepted without any check.

Here the format is recognised by CONTENT, never by extension, and every path
ends in the same validation, so a file is either read correctly or refused with
a visible cause — never accepted silently.

The standard layout
-------------------
First line: ``';'``-separated column names including ``time`` and
``min_max_zeta_850``. Such a file is read by EXACTLY the call the app has always
used (``_read_standard``), so its values and index are bit-identical to before.
Its dates must be year-first (``YYYY-MM-DD…``), the only layout inference
cannot misread; every bundled track already is.

The custom layout (opt-in)
--------------------------
Any other delimited text file, described by a ``CustomFormat``. It is not read
by a second, parallel parser that the rest of the app would have to trust: it
is NORMALISED into standard-layout bytes (``normalize_track``) and those bytes
go through the standard reader and the same validation. The vorticity column
is carried across as its original text tokens, not re-formatted floats, so the
standard reader parses the very characters the file contains.

A file that has the standard header is always read as standard, even with a
custom format active: the standard header is unambiguous, and bundled tracks
must not change meaning because a checkbox for uploads is ticked.

No import of ``cyclophaser`` and no Streamlit here: this is pure I/O.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

STANDARD_SEP = ";"
TIME_COL = "time"
VORT_COL = "min_max_zeta_850"

# Separator choices offered by the custom format, in UI order.
SEPARATORS = {
    "auto": None,
    ";": ";",
    ",": ",",
    "tab": "\t",
    "whitespace": r"\s+",
}

# Dates whose format may be INFERRED: year first. pandas reads "05/01/2015" as
# 1 May without any warning (only "13/01/2015" makes it warn about dayfirst), so
# inference on any other layout can return wrong dates silently. A year-first
# date has one reading; anything else needs an explicit date format.
_YEAR_FIRST = re.compile(r"^\d{4}-\d{2}-\d{2}")

# A relative vorticity whose magnitude exceeds this is almost certainly the
# wrong column (a latitude, a pressure, a wind speed). Cyclone-scale 850 hPa
# relative vorticity is O(1e-5–1e-3) s⁻¹.
IMPLAUSIBLE_ABS_VORTICITY = 1e-2


class TrackFormatError(ValueError):
    """A track that cannot be used, with the cause in the message."""


@dataclass(frozen=True)
class CustomFormat:
    """How to read a non-standard track.

    Attributes:
        sep: One of ``SEPARATORS``' keys. ``"auto"`` inspects the first line
            (``;``, ``,``, tab — the most frequent wins — else whitespace).
        header: Whether the first line holds column names.
        date_col: Column name (with a header) or 1-based column number (without).
        vort_col: Same, for the vorticity column.
        date_format: Optional strftime pattern, e.g. ``"%d/%m/%Y %H:%M"``. Empty
            is allowed only for year-first dates (``YYYY-MM-DD…``); pandas then
            infers the rest from the first value and refuses the column if any
            other value does not match it.
    """

    sep: str = "auto"
    header: bool = True
    date_col: str = TIME_COL
    vort_col: str = VORT_COL
    date_format: str = ""


# ── detection ─────────────────────────────────────────────────────────────────
def _first_line(data: bytes) -> str:
    line = data.split(b"\n", 1)[0].decode("utf-8", errors="replace")
    return line.lstrip("﻿").rstrip("\r")


def is_standard(data: bytes) -> bool:
    """True when the first line is ``';'``-separated and names both columns."""
    cols = _first_line(data).split(STANDARD_SEP)
    return TIME_COL in cols and VORT_COL in cols


def describe_first_line(data: bytes) -> str:
    """The first line, shortened, for error messages."""
    line = _first_line(data)
    return line if len(line) <= 120 else line[:117] + "..."


# ── validation ────────────────────────────────────────────────────────────────
def validate_series(s: pd.Series) -> pd.Series:
    """Raise ``TrackFormatError`` unless ``s`` is a usable vorticity series.

    Required: a DatetimeIndex, strictly increasing (so no duplicates), float64
    values with no NaN, and at least 2 points.
    """
    idx = s.index
    if not isinstance(idx, pd.DatetimeIndex):
        first = idx[0] if len(idx) else "—"
        raise TrackFormatError(
            f"the '{TIME_COL}' column was not recognised as dates (first value: "
            f"{first!r}). Specify the date format in the custom track format.")
    if len(s) < 2:
        raise TrackFormatError(f"the track has {len(s)} point(s); at least 2 are needed.")
    if idx.hasnans:
        pos = int(np.flatnonzero(idx.isna())[0])
        raise TrackFormatError(f"missing date at row {pos + 1}.")
    dup = idx.duplicated()
    if dup.any():
        pos = int(np.flatnonzero(dup)[0])
        raise TrackFormatError(f"duplicate date {idx[pos]} at row {pos + 1}.")
    if not idx.is_monotonic_increasing:
        pos = int(np.flatnonzero(np.diff(idx.asi8) < 0)[0]) + 1
        raise TrackFormatError(
            f"dates are not in increasing order: {idx[pos]} (row {pos + 1}) comes "
            f"after {idx[pos - 1]}.")
    if s.dtype != np.float64:
        num = pd.to_numeric(s, errors="coerce")
        bad = num.isna() & s.notna()
        if bad.any():
            pos = int(np.flatnonzero(bad.to_numpy())[0])
            raise TrackFormatError(
                f"the vorticity column is not numeric: {s.iloc[pos]!r} at row "
                f"{pos + 1}.")
        raise TrackFormatError(
            f"the vorticity column is {s.dtype}, not float64 (e.g. whole numbers "
            "only). Relative vorticity is expected in s⁻¹, O(1e-5).")
    if s.isna().any():
        pos = int(np.flatnonzero(s.isna().to_numpy())[0])
        raise TrackFormatError(
            f"the vorticity column has {int(s.isna().sum())} missing value(s); "
            f"first at row {pos + 1} ({idx[pos]}).")
    return s


def plausibility_warnings(s: pd.Series) -> list[str]:
    """Non-fatal doubts about a VALID series, shown in the custom-format preview."""
    out = []
    v = s.to_numpy()
    nz = v[v != 0]
    if nz.size and (nz > 0).mean() > 0.5:
        out.append(
            f"The vorticity is predominantly positive ({(nz > 0).mean():.0%} of "
            "non-zero values). CycloPhaser assumes the SOUTHERN hemisphere, where "
            "cyclonic relative vorticity is NEGATIVE; a northern-hemisphere track "
            "will be read as an anticyclone. Check the column and its sign.")
    peak = float(np.max(np.abs(v)))
    if peak > IMPLAUSIBLE_ABS_VORTICITY:
        out.append(
            f"max |vorticity| is {peak:.3g}, far above cyclone-scale relative "
            "vorticity (≈1e-5 to 1e-3 s⁻¹). This may be the wrong column (a "
            "latitude, pressure or wind speed?).")
    return out


# ── reading ───────────────────────────────────────────────────────────────────
def _require_year_first(tokens, where: str) -> None:
    for i, tok in enumerate(tokens):
        if not _YEAR_FIRST.match(str(tok).strip()):
            raise TrackFormatError(
                f"date {str(tok)!r} at row {i + 1} does not start with "
                f"YYYY-MM-DD. {where} dates are read only year-first, because "
                "any other order can be misread without warning ('05/01/2015' "
                "becomes 1 May). Use the custom track format with an explicit "
                "date format, e.g. '%d/%m/%Y %H:%M'.")


def _read_standard(data: bytes) -> pd.Series:
    # EXACTLY the call app.py used before this module existed — keep it so:
    # bit-identity with the previous reader rests on this line.
    df = pd.read_csv(io.BytesIO(data), sep=STANDARD_SEP, index_col=TIME_COL,
                     parse_dates=True)
    raw = pd.read_csv(io.BytesIO(data), sep=STANDARD_SEP, usecols=[TIME_COL],
                      dtype=str, keep_default_na=False)[TIME_COL]
    _require_year_first(raw, "Standard-layout")
    return df[VORT_COL]


def _detect_sep(data: bytes) -> str:
    line = _first_line(data)
    counts = {c: line.count(c) for c in (";", ",", "\t")}
    best = max(counts, key=counts.get)
    if counts[best] > 0:
        return best
    if len(line.split()) > 1:
        return r"\s+"
    raise TrackFormatError(
        f"could not detect a separator in the first line {describe_first_line(data)!r}; "
        "choose one explicitly.")


def _pick(df: pd.DataFrame, col: str, header: bool, what: str) -> pd.Series:
    col = str(col).strip()
    if header:
        if col not in df.columns:
            raise TrackFormatError(
                f"{what} column {col!r} not found; the file has "
                f"{', '.join(map(repr, df.columns))}.")
        return df[col]
    if not col.isdigit() or not (1 <= int(col) <= df.shape[1]):
        raise TrackFormatError(
            f"{what} column must be a number from 1 to {df.shape[1]} for a file "
            f"without a header line (got {col!r}).")
    return df.iloc[:, int(col) - 1]


def normalize_track(data: bytes, fmt: CustomFormat | None = None) -> bytes:
    """Any accepted track → standard-layout bytes.

    A standard file is returned UNCHANGED, byte for byte (so caches keyed on the
    bytes, and every result derived from them, are untouched). A custom file is
    rewritten as ``time;min_max_zeta_850`` with its vorticity tokens verbatim.
    The result still has to pass ``read_track``; this function only reshapes.
    """
    if is_standard(data):
        return data
    if fmt is None:
        raise TrackFormatError(
            f"not the standard track layout. The first line is "
            f"{describe_first_line(data)!r}; the standard layout is ';'-separated "
            f"with columns '{TIME_COL}' and '{VORT_COL}'. For any other layout, "
            "enable 'Custom track format' and describe the file there.")
    if fmt.sep not in SEPARATORS:
        raise TrackFormatError(f"unknown separator option {fmt.sep!r}.")
    sep = SEPARATORS[fmt.sep] or _detect_sep(data)
    try:
        df = pd.read_csv(io.BytesIO(data), sep=sep,
                         header=0 if fmt.header else None, dtype=str,
                         keep_default_na=False, skipinitialspace=True,
                         engine="python" if sep == r"\s+" else "c")
    except Exception as exc:
        raise TrackFormatError(f"could not split the file with separator "
                               f"{fmt.sep!r}: {exc}") from exc
    if fmt.header:
        df.columns = [str(c).strip() for c in df.columns]
    dates = _pick(df, fmt.date_col, fmt.header, "date").astype(str).str.strip()
    vort = _pick(df, fmt.vort_col, fmt.header, "vorticity").astype(str).str.strip()
    if (dates == "").any():
        pos = int(np.flatnonzero((dates == "").to_numpy())[0])
        raise TrackFormatError(f"empty date at row {pos + 1}.")
    try:
        if fmt.date_format.strip():
            ts = pd.to_datetime(dates, format=fmt.date_format.strip())
        else:
            _require_year_first(dates, "Without a date format,")
            ts = pd.to_datetime(dates)
    except TrackFormatError:
        raise
    except Exception as exc:
        hint = ("" if fmt.date_format.strip()
                else " Set the date format (strftime), e.g. '%d/%m/%Y %H:%M'.")
        raise TrackFormatError(
            f"could not read the date column as dates: {exc}.{hint}") from exc
    # ISO text ("2000-01-01 03:00:00"), which the standard reader parses.
    stamps = [t.isoformat(sep=" ") for t in ts]
    if any(re.search(r"[;\r\n]", tok) for tok in vort):
        raise TrackFormatError("a vorticity value contains ';' or a line break.")
    body = "\n".join(f"{t};{v}" for t, v in zip(stamps, vort))
    return f"{TIME_COL};{VORT_COL}\n{body}\n".encode("utf-8")


def read_track(data: bytes, fmt: CustomFormat | None = None) -> pd.Series:
    """The one reader: bytes of any accepted layout → validated vorticity Series.

    Args:
        data: The file's raw bytes. The extension is never consulted.
        fmt: The custom format to use when the file is not standard. ``None``
            (the default) accepts the standard layout only.

    Returns:
        A float64 Series named ``min_max_zeta_850`` on a strictly increasing
        DatetimeIndex named ``time``.

    Raises:
        TrackFormatError: with the cause, for anything that cannot be used.
    """
    std = normalize_track(data, fmt)
    try:
        s = _read_standard(std)
    except Exception as exc:
        raise TrackFormatError(f"could not read the track: {exc}") from exc
    return validate_series(s)
