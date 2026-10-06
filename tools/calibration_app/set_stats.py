"""Set statistics for the Calibrate page: descriptive numbers about the phases
detected on every loaded track.

Everything here is computed from detection results the page has ALREADY
computed (the `periods_dict` of each track); nothing calls the detector. The
numbers describe what was detected — they are not a quality score and compare
with no label.

Phases are counted by the package's own keys. A phase that occurs again in a
track gets a numbered key from `cyclophaser.determine_periods.periods_to_dict`
("intensification", "intensification 2", …), the same name its figure and its
CSV carry; each key is counted on its own, never merged with the others.

Kept apart from app.py for two reasons: the computation is a pure function that
can be read and tested on its own, and the whole block is one call
(`render_set_stats`), so its cost can be measured by wrapping that call.
"""

from __future__ import annotations

import html
import statistics
from collections import Counter

import pandas as pd

PHASE_ORDER = ("incipient", "intensification", "mature", "decay", "residual")
CYCLE = "whole cycle"
CAPTION = "Descriptive statistics of the detected phases — not a quality score."
TOP_SEQUENCES = 5
_FALLBACK_COLOR = "#555555"
# The whole cycle is not a phase: a neutral slate of its own, mid-luminance so it
# reads on the light and on the dark theme (#555 vanished on the dark one).
_CYCLE_COLOR = "#7a809c"


def base_phase(key: str) -> str:
    """'intensification 2' → 'intensification'."""
    return key.rstrip(" 0123456789").strip()


def occurrence(key: str) -> int:
    """'intensification 2' → 2; 'intensification' → 1."""
    tail = key[len(base_phase(key)):].strip()
    return int(tail) if tail.isdigit() else 1


def _key_order(key: str) -> tuple:
    b = base_phase(key)
    return (PHASE_ORDER.index(b) if b in PHASE_ORDER else len(PHASE_ORDER), b,
            occurrence(key))


def _hours(delta) -> float:
    return delta.total_seconds() / 3600.0


def compute_set_stats(results: dict) -> dict:
    """Descriptive statistics of a set of detection results.

    Args:
        results: track name → {"ok": bool, "periods_dict": {phase key: (start, end)}}.
            A track with ``ok`` false counts as failed.

    Returns:
        A dict with:
        ``n_analysed`` and ``failed`` (names);
        ``phases``: the phase keys seen, base phases in life-cycle order and,
        within one, by occurrence ("decay", "decay 2", …);
        ``presence``: key → number of analysed tracks that have it;
        ``durations``: key → hours from its start to its end, one value per
        dated track that has it, plus ``CYCLE`` → hours from the start of the
        first phase to the end of the last;
        ``n_dated`` and ``n_undated``: tracks whose phase bounds are, or are
        not, dates (only dated ones have durations);
        ``sequences``: the ``TOP_SEQUENCES`` most common sequences of keys as
        (tuple of keys, count), most common first, ties in alphabetical order
        of the " → "-joined text.
    """
    ok = [(n, r["periods_dict"]) for n, r in results.items() if r.get("ok")]
    failed = [n for n, r in results.items() if not r.get("ok")]

    presence: Counter = Counter()
    durations: dict[str, list[float]] = {}
    cycle: list[float] = []
    sequences: Counter = Counter()
    n_undated = 0
    for _name, periods in ok:
        sequences[tuple(periods)] += 1
        presence.update(periods.keys())
        bounds = [b for se in periods.values() for b in se]
        if not bounds or not all(isinstance(b, pd.Timestamp) for b in bounds):
            n_undated += 1
            continue
        for key, (start, end) in periods.items():
            durations.setdefault(key, []).append(_hours(end - start))
        cycle.append(_hours(max(e for _s, e in periods.values())
                            - min(s for s, _e in periods.values())))

    if cycle:
        durations[CYCLE] = cycle
    top = sorted(sequences.items(), key=lambda kv: (-kv[1], " → ".join(kv[0])))
    return {
        "n_analysed": len(ok),
        "failed": failed,
        "phases": sorted(presence, key=_key_order),
        "presence": dict(presence),
        "durations": durations,
        "n_dated": len(ok) - n_undated,
        "n_undated": n_undated,
        "sequences": top[:TOP_SEQUENCES],
    }


def phase_table(stats: dict) -> pd.DataFrame:
    """One row per phase key: how many tracks have it (n and %), and the median
    of its duration over the n dated tracks that have it."""
    n = stats["n_analysed"]
    rows = []
    for key in stats["phases"]:
        hours = stats["durations"].get(key, [])
        rows.append({
            "Phase": key,
            "Tracks with it (n)": stats["presence"][key],
            "Tracks with it (%)": round(100.0 * stats["presence"][key] / n, 1) if n else 0.0,
            "Median duration (h)": round(statistics.median(hours), 1) if hours else None,
            "Durations (n)": len(hours),
        })
    return pd.DataFrame(rows, columns=["Phase", "Tracks with it (n)", "Tracks with it (%)",
                                       "Median duration (h)", "Durations (n)"])


def cycle_median(stats: dict) -> float | None:
    hours = stats["durations"].get(CYCLE)
    return round(statistics.median(hours), 1) if hours else None


def phase_color(key: str, colors: dict) -> str:
    """A repeated phase takes its base phase's colour."""
    return colors.get(base_phase(key), _FALLBACK_COLOR)


def duration_figure(stats: dict, colors: dict):
    """Box per phase key (and the whole cycle), every track a point, n in the name."""
    import plotly.graph_objects as go

    fig = go.Figure()
    for key in [*stats["phases"], CYCLE]:
        hours = stats["durations"].get(key)
        if not hours:
            continue
        colour = _CYCLE_COLOR if key == CYCLE else phase_color(key, colors)
        fig.add_trace(go.Box(
            y=hours, name=f"{key}<br>n={len(hours)}", boxpoints="all", jitter=0.4,
            pointpos=0, marker={"color": colour, "size": 4}, line={"color": colour},
            showlegend=False, hovertemplate="%{y:.0f} h<extra>" + key + "</extra>"))
    fig.update_layout(height=380, margin={"l": 10, "r": 10, "t": 30, "b": 10},
                      yaxis_title="Duration (hours)",
                      title={"text": "Duration per track", "font": {"size": 14}})
    return fig


# ── sequences: one coloured square per phase ─────────────────────────────────
def _luminance(colour: str) -> float:
    """Relative luminance (WCAG) of '#rrggbb' or 'gray'."""
    hexes = {"gray": "#808080", "grey": "#808080"}
    c = hexes.get(colour, colour).lstrip("#")
    rgb = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def number_colour(fill: str) -> str:
    """Black or white, whichever contrasts more with the square's fill."""
    lum = _luminance(fill)
    return "#111111" if (lum + 0.05) / 0.05 >= 1.05 / (lum + 0.05) else "#ffffff"


def square(key: str, colors: dict) -> str:
    """The square of one phase: its base phase's colour; a repeat shows its
    number inside. A mid-grey outline keeps the light fills visible on a light
    background and the dark ones on a dark background."""
    fill = phase_color(key, colors)
    num = occurrence(key)
    return (f'<span class="seq-sq" title="{html.escape(key)}" style="display:inline-block;'
            f"width:1.25em;height:1.25em;line-height:1.25em;margin-right:2px;"
            f"border-radius:3px;border:1px solid rgba(128,128,128,0.75);"
            f"background:{fill};color:{number_colour(fill)};text-align:center;"
            f'font-size:0.75em;font-weight:700;vertical-align:middle">'
            f"{num if num > 1 else ''}</span>")


def sequences_html(stats: dict, colors: dict) -> str:
    """The most common sequences as an HTML table: squares, then the names in
    text, then the number of tracks. Text colour is left to the theme."""
    rows = []
    for keys, count in stats["sequences"]:
        squares = "".join(square(k, colors) for k in keys)
        names = html.escape(" → ".join(keys))
        rows.append(
            f'<tr><td style="white-space:nowrap">{squares}</td>'
            f'<td><span class="seq-names">{names}</span></td>'
            f'<td class="seq-n" style="text-align:right">{count}</td></tr>')
    return ('<table class="seq-table" style="width:100%">'
            "<thead><tr><th></th><th>Phase sequence</th>"
            '<th style="text-align:right">Tracks</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table>")


def render_set_stats(results: dict, colors: dict) -> None:
    """The whole statistics block of the Calibrate page."""
    import streamlit as st

    stats = compute_set_stats(results)
    st.divider()
    st.subheader("Set statistics")
    st.caption(CAPTION)
    c1, c2, c3, _c4 = st.columns([1, 1, 1, 2])
    c1.metric("Analysed", stats["n_analysed"])
    c2.metric("Failed", len(stats["failed"]))
    cyc = cycle_median(stats)
    n_cyc = len(stats["durations"].get(CYCLE, []))
    c3.metric("Whole cycle, median (h)", "—" if cyc is None else f"{cyc:.1f}",
              help=f"From the start of the first phase to the end of the last, "
                   f"over the {n_cyc} tracks with dates.")
    if stats["failed"]:
        st.caption("Failed: " + ", ".join(stats["failed"]))
    if not stats["n_analysed"]:
        return
    table = phase_table(stats)
    # tall enough for every row: no scrolling inside the table
    st.dataframe(table, hide_index=True, use_container_width=True,
                 height=36 * (len(table) + 1) + 3)
    st.caption(
        "A phase that occurs again in a track is counted under its own name "
        "(\"intensification 2\"), as in the figures and the CSV files. "
        "Durations: hours from the start to the end of the phase; the whole "
        "cycle runs from the start of the first phase to the end of the last. "
        f"{stats['n_dated']} track(s) with dates are in the durations; "
        f"{stats['n_undated']} left out because their time axis has no dates.")
    if stats["n_dated"]:
        st.plotly_chart(duration_figure(stats, colors), use_container_width=True,
                        key="set_stats_durations")
    st.markdown(f"**{TOP_SEQUENCES} most common phase sequences**")
    st.markdown(sequences_html(stats, colors), unsafe_allow_html=True)
