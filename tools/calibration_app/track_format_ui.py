"""Streamlit controls for uploading tracks: the custom format and its preview.

Shared by the Calibration page's uploader and the Benchmark tab's Exploration
uploader, so both accept exactly the same files and show the same messages. The
reading itself lives in ``track_io`` (no Streamlit there); this module only
draws the controls, the preview and the errors.

A file in the standard layout is validated and used. A file in any other layout
is refused with the reason unless the custom format is enabled; with it enabled,
the file is parsed, PREVIEWED, and used only after the user ticks a
confirmation whose key includes the file's bytes and the format, so changing
either clears it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st

import track_io as tio

# Widget keys of the custom-format controls (Calibration page). The Benchmark
# tab reads the same keys through `current_format`, so the two cannot diverge.
K_ON = "track_custom_on"
K_SEP = "track_custom_sep"
K_HEADER = "track_custom_header"
K_DATE = "track_custom_date_col"
K_VORT = "track_custom_vort_col"
K_DFMT = "track_custom_date_format"

UPLOAD_HELP = (
    "**Standard layout** — recognised from the file's content, not its "
    "extension (.csv and .txt are both accepted): the first line holds column "
    "names separated by `;`, including `time` and `min_max_zeta_850`. Other "
    "columns are ignored. Example:\n\n"
    "```\n"
    "time;min_max_zeta_850\n"
    "2015-01-27 04:00:00;-2.38483e-05\n"
    "2015-01-27 05:00:00;-2.589e-05\n"
    "```\n\n"
    "`min_max_zeta_850` is the 850 hPa relative vorticity in s⁻¹. CycloPhaser "
    "assumes the southern hemisphere, where cyclonic vorticity is negative.\n\n"
    "Every file is checked: the dates must be year-first (`YYYY-MM-DD…`), "
    "parse, strictly increase and have no duplicates; the vorticity must be numeric (float) with no missing "
    "values; at least 2 points. A file that fails is refused with the "
    "reason.\n\n"
    "**Any other layout** (another separator, other column names, no header "
    "line, another date format) is refused unless **Custom track format** "
    "below is enabled and describes it."
)

HELP_ON = (
    "For files that are not in the standard layout. Off by default. Describe "
    "the separator, whether there is a header line, which columns hold the date "
    "and the vorticity, and optionally the date format. Each file read this way "
    "is shown in a preview (parsed rows, first and last date, number of points, "
    "vorticity range) and is used only after you confirm it.\n\n"
    "Files in the standard layout are always read as standard, even with this "
    "on. The Benchmark tab's Exploration upload uses these same settings."
)
HELP_SEP = (
    "`auto` looks at the first line: the most frequent of `;`, `,` and tab; if "
    "none of them occurs, runs of spaces/tabs (`whitespace`)."
)
HELP_HEADER = (
    "Tick if the first line holds column names. Untick if the first line is "
    "already data; the columns are then given by number, starting at 1."
)
HELP_DATE = (
    "Name of the date/time column — or its number, starting at 1, when the "
    "file has no header line."
)
HELP_VORT = (
    "Name of the 850 hPa relative vorticity column (s⁻¹) — or its number, "
    "starting at 1, when the file has no header line. Sign convention: southern "
    "hemisphere, cyclonic = negative."
)
HELP_DFMT = (
    "Optional strftime pattern, e.g. `%Y-%m-%d-%H%M` for `1979-02-19-2100`, or "
    "`%d/%m/%Y %H:%M` for `19/02/1979 21:00`. May be left empty only for "
    "year-first dates (`YYYY-MM-DD…`): any other order can be misread without "
    "warning (`05/01/2015` would become 1 May), so it is refused without an "
    "explicit format."
)
HELP_CONFIRM = (
    "Nothing from this file is used until this is ticked. Changing the file or "
    "any custom-format setting clears it."
)


def format_controls() -> tio.CustomFormat | None:
    """Draw the custom-format controls; the active format, or None when off."""
    with st.expander("Custom track format (for files not in the standard layout)",
                     expanded=bool(st.session_state.get(K_ON, False))):
        on = st.checkbox("Enable custom track format", value=False, key=K_ON,
                         help=HELP_ON)
        if not on:
            return None
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Separator", options=list(tio.SEPARATORS), key=K_SEP,
                         help=HELP_SEP)
            st.text_input("Date column", value=tio.TIME_COL, key=K_DATE,
                          help=HELP_DATE)
            st.text_input("Date format (optional)", value="", key=K_DFMT,
                          help=HELP_DFMT)
        with c2:
            st.checkbox("First line is a header", value=True, key=K_HEADER,
                        help=HELP_HEADER)
            st.text_input("Vorticity column", value=tio.VORT_COL, key=K_VORT,
                          help=HELP_VORT)
    return current_format(st.session_state)


def current_format(state) -> tio.CustomFormat | None:
    """The custom format held in session state, or None when it is off."""
    if not state.get(K_ON, False):
        return None
    return tio.CustomFormat(
        sep=state.get(K_SEP, "auto"),
        header=bool(state.get(K_HEADER, True)),
        date_col=str(state.get(K_DATE, tio.TIME_COL)),
        vort_col=str(state.get(K_VORT, tio.VORT_COL)),
        date_format=str(state.get(K_DFMT, "")),
    )


def _preview(name: str, s: pd.Series) -> None:
    st.markdown(f"**Preview — `{name}`** (custom format)")
    st.dataframe(s.head(5).rename("vorticity").to_frame(), use_container_width=True)
    st.caption(
        f"First date **{s.index[0]}** · last date **{s.index[-1]}** · "
        f"**{len(s)}** points · vorticity min **{s.min():.4g}**, "
        f"max **{s.max():.4g}**")
    for msg in tio.plausibility_warnings(s):
        st.warning(f"{name}: {msg}")


def accept_uploads(uploads, fmt: tio.CustomFormat | None,
                   confirm_prefix: str) -> dict[str, bytes]:
    """Uploaded files → {name: standard-layout bytes} for the files accepted.

    Refused files get an ``st.error`` naming the file and the cause. A file read
    through the custom format is previewed and returned only once confirmed.

    Args:
        uploads: The ``st.file_uploader`` result (a list of uploaded files).
        fmt: The active custom format, or None.
        confirm_prefix: Key prefix for the confirmation checkboxes, distinct per
            uploader so the two pages never share a confirmation.
    """
    out: dict[str, bytes] = {}
    for f in uploads or []:
        name = Path(f.name).stem
        data = f.getvalue()
        standard = tio.is_standard(data)
        try:
            std_bytes = tio.normalize_track(data, None if standard else fmt)
            s = tio.read_track(std_bytes)
        except tio.TrackFormatError as exc:
            st.error(f"`{f.name}` refused: {exc}")
            continue
        if standard:
            out[name] = std_bytes
            continue
        _preview(f.name, s)
        digest = hashlib.sha256(data + repr(fmt).encode()).hexdigest()[:16]
        if st.checkbox(f"Use `{f.name}` as previewed", value=False,
                       key=f"{confirm_prefix}{digest}", help=HELP_CONFIRM):
            out[name] = std_bytes
    return out
