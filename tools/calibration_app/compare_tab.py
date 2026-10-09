"""The Compare page — several configurations over the tracks loaded in Calibrate.

The question it answers: what changes in the phases of my tracks when the
configuration changes? It is the public half of the old Benchmark page (benchmark
review, I1; the decisions and the control-by-control inventory are in
research/benchmark_review/stage0/DECISIONS.md). The logic is in compare_core.py;
this file is the Streamlit surface over it. Nothing here reads a manual label.

Where things come from
----------------------
* **Tracks** — the ones the Calibrate page is running on (sample, example,
  uploads), published by app.py as `_compare_live_tracks` next to the files the
  detection reads. This page has no uploader of its own. Without tracks it shows
  an empty state that links to Calibrate.
* **"Current settings"** — `_bench_live_config`, the Calibrate sidebar as
  published by app.py next to the values the detection receives. Taken when the
  column is added.
* **"Defaults"** — `_compare_defaults_config`, published by app.py from the same
  values the Calibrate "Defaults" button puts in the sidebar.
* **"Upload YAML"** — a saved configuration; only its two parameter sections are
  kept. Absent keys are filled by the rule of the Calibrate import and reported
  in the same words (config_text.py).

Nothing recomputes on edit
--------------------------
Results come from an explicit **Run**. A fingerprint of the configurations and
of the selected tracks' contents is stored with them; when it stops matching,
the results are flagged out of date rather than silently recomputed. Changing
the reference is not a change of either: it only re-reads the stored results.

Results are cached ACROSS runs, by (effective configuration, track content) —
see compare_core's module docstring — with a bounded cache, so running again
after one change recomputes only the cells that changed. (The old Benchmark's
cache lived for one Run only; finding A3.)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

import compare_core as cc  # noqa: E402
import config_text  # noqa: E402
import layer_inspector as li  # noqa: E402
import phase_figures as pf  # noqa: E402

PAGE_TITLE = "Compare configurations"
FIGURE_LAYOUTS = ["Side by side", "Stacked"]
PAGE_SIZES = [12, 24, 48]
CARDS_PER_ROW = 4
# Danilo's decision at the I1 checkpoint (2026-10-08), from the measured Run
# cost (~2.8 s per column on 51 tracks) and from readability: four cards per
# row, and four figures side by side per track.
MAX_COLUMNS = 4
LIMIT_REASON = (f"{MAX_COLUMNS} configurations is the limit: remove one to add "
                "another.")
INVERT_HELP = "Selects the tracks that are not selected and clears the ones that are."
# Bounded caches. A cell is a few kB (phases + the smoothed series), so 2048
# cells hold, for example, 4 configurations x 51 tracks ten times over.
CELL_CACHE_ENTRIES = 2048
PNG_CACHE_ENTRIES = 512

# Published by app.py's Calibrate page.
LIVE_TRACKS = "_compare_live_tracks"
LIVE_CONFIG = "_bench_live_config"
DEFAULTS_CONFIG = "_compare_defaults_config"

# session_state keys of this page
K_COLUMNS = "cmp_columns"
K_NEXT_ID = "cmp_next_id"
K_TRACKS = "cmp_tracks"                # the track multiselect
K_TRACKSET = "_cmp_trackset"           # the loaded track names last seen
K_REFERENCE = "cmp_reference"
K_LAYOUT = "cmp_figure_layout"
K_ONLY_DIFF = "cmp_only_differing"
K_PAGE_SIZE = "cmp_page_size"
K_FIRST = "_cmp_first"
K_SHOWN = "_cmp_shown"
K_RESULTS = "_cmp_results"
K_UPLOAD = "cmp_yaml_upload"
K_UPLOAD_SEEN = "_cmp_yaml_seen"
K_UPLOAD_ERROR = "_cmp_yaml_error"
EDIT_PREFIX = "cmp_edit_"
EDIT_ERROR_PREFIX = "_cmp_edit_error_"

# The widget keys app.py shields from Streamlit's clean-up while another page is
# open (app.py, `_PAGE_WIDGET_STATE`). Buttons and the uploader are left out:
# their values cannot be written back through session_state.
WIDGET_STATE_KEYS = frozenset({K_TRACKS, K_REFERENCE, K_LAYOUT, K_ONLY_DIFF,
                               K_PAGE_SIZE})
WIDGET_STATE_PREFIXES = (EDIT_PREFIX,)

# A plain-key copy of every widget value above. Measured in Chromium on
# streamlit 1.63.0, on a trip Compare → Calibrate → Compare: a value the user
# changed in a widget of this page does not survive the switch. The reference
# was already gone from session_state when the first run on Calibrate started,
# so the shield in app.py had nothing to write back; the figure layout came back
# as the value `setdefault` first gave it, not as the user's choice. AppTest,
# which has no browser side, keeps both. Plain keys are never cleaned up, so the
# copy follows each widget after it is drawn (`_remember`), and each widget is
# set from its copy on the first run after arriving on this page and whenever
# its own key is missing (`_restore`) — the rule the old Benchmark page
# followed for its column state.
KEEP_PREFIX = "_cmp_kept_"
ARRIVED = "_app_arrived"         # set by app.py on every run

CURRENT = "Current settings"
DEFAULTS = "Defaults"


# ── cached work ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, max_entries=1024)
def _parsed(data: bytes) -> tuple[pd.Series | None, str | None, str | None]:
    """(series, content key, error) of one published track."""
    try:
        series = cc.read_series(data)
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"
    return series, cc.series_key(series), None


@st.cache_data(show_spinner=False, max_entries=CELL_CACHE_ENTRIES)
def _cell(config_key: str, series_key: str, _doc: dict, _series: pd.Series) -> dict:
    """One configuration on one track. The cache key is (config_key, series_key)
    ONLY: Streamlit does not hash arguments whose name starts with '_'."""
    return cc.run_cell(_doc, _series)


@st.cache_data(show_spinner=False, max_entries=PNG_CACHE_ENTRIES)
def _cell_png(values: tuple, runs: tuple, title: str, z: tuple | None) -> bytes:
    return pf.png(pf.cell_figure(values, runs, title, z, li.PHASE_COLORS))


@st.cache_data(show_spinner=False, max_entries=PNG_CACHE_ENTRIES)
def _stacked_png(values: tuple, panels: tuple) -> bytes:
    return pf.png(pf.stacked_figure(values, panels, li.PHASE_COLORS))


# ── state ─────────────────────────────────────────────────────────────────────
def _restore(key: str, default) -> None:
    """Set a widget's value from its plain copy: on the first run after arriving
    on this page, and whenever the widget's own key is missing."""
    kept = KEEP_PREFIX + key
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(kept, default)
    elif st.session_state.get(ARRIVED) and kept in st.session_state:
        st.session_state[key] = st.session_state[kept]


def _remember(key: str) -> None:
    """Copy a widget's value to its plain key (see KEEP_PREFIX)."""
    if key in st.session_state:
        st.session_state[KEEP_PREFIX + key] = st.session_state[key]


def _init_state() -> None:
    st.session_state.setdefault(K_COLUMNS, [])
    st.session_state.setdefault(K_NEXT_ID, 1)
    _restore(K_LAYOUT, FIGURE_LAYOUTS[0])
    _restore(K_ONLY_DIFF, False)
    _restore(K_PAGE_SIZE, PAGE_SIZES[0])


def _columns() -> list[dict]:
    return st.session_state[K_COLUMNS]


def _unique_name(base: str) -> str:
    names = {c["name"] for c in _columns()}
    if base not in names:
        return base
    k = 2
    while f"{base} ({k})" in names:
        k += 1
    return f"{base} ({k})"


def _append(base: str, origin: str, doc: dict, origin_name: str = "") -> None:
    if len(_columns()) >= MAX_COLUMNS:          # the controls are disabled too
        return
    cid = st.session_state[K_NEXT_ID]
    st.session_state[K_NEXT_ID] = cid + 1
    _columns().append({"cid": cid, "name": _unique_name(base), "origin": origin,
                       "origin_name": origin_name,
                       "doc": cc.parameter_sections(doc), "edited": False})


def _add_current() -> None:
    _append(CURRENT, "current", st.session_state[LIVE_CONFIG])


def _add_defaults() -> None:
    _append(DEFAULTS, "defaults", st.session_state[DEFAULTS_CONFIG])


def _remove(cid: int) -> None:
    st.session_state[K_COLUMNS] = [c for c in _columns() if c["cid"] != cid]
    st.session_state.pop(EDIT_PREFIX + str(cid), None)
    st.session_state.pop(KEEP_PREFIX + EDIT_PREFIX + str(cid), None)
    st.session_state.pop(EDIT_ERROR_PREFIX + str(cid), None)


def _apply_edit(cid: int) -> None:
    text = st.session_state.get(EDIT_PREFIX + str(cid), "")
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        st.session_state[EDIT_ERROR_PREFIX + str(cid)] = f"Invalid YAML: {exc}"
        return
    why = cc.check_document(doc)
    if why:
        st.session_state[EDIT_ERROR_PREFIX + str(cid)] = why
        return
    st.session_state.pop(EDIT_ERROR_PREFIX + str(cid), None)
    for c in _columns():
        if c["cid"] == cid:
            new = cc.parameter_sections(doc)
            if new != c["doc"]:
                c["doc"], c["edited"] = new, True


def _select(which: str, names: list[str]) -> None:
    cur = set(st.session_state.get(K_TRACKS) or [])
    st.session_state[K_TRACKS] = (list(names) if which == "all" else
                                  [] if which == "clear" else
                                  [n for n in names if n not in cur])


def _step_page(delta: int) -> None:
    size = st.session_state.get(K_PAGE_SIZE, PAGE_SIZES[0])
    st.session_state[K_FIRST] = max(0, st.session_state.get(K_FIRST, 0) + delta * size)


def _fingerprint(cols: list[dict], ids: list[str], keys: dict[str, str]) -> str:
    blob = json.dumps({"columns": [[c["cid"], cc.config_key(c["doc"])] for c in cols],
                       "tracks": [[s, keys.get(s)] for s in ids]})
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ── pieces of the page ────────────────────────────────────────────────────────
def _empty_state() -> None:
    st.info("No tracks are loaded. Load tracks on the Calibrate page — the sample "
            "data, the example or your own files — and come back: this page "
            "compares configurations on those same tracks.")
    st.page_link("app_pages/calibrate.py", label="Go to Calibrate",
                 icon=":material/tune:")


def _origin_text(col: dict) -> str:
    if col["origin"] == "current":
        return "Calibrate's settings at the moment this column was added."
    if col["origin"] == "defaults":
        return "The package defaults — what Calibrate's **Defaults** button sets."
    return f"From the file `{col['origin_name']}`."


def _render_card(col: dict, ref: dict | None) -> None:
    is_ref = ref is not None and col["cid"] == ref["cid"]
    st.markdown(f"**{col['name']}**" + ("  ·  reference" if is_ref else ""))
    st.caption(_origin_text(col))
    if col["origin"] == "current" and LIVE_CONFIG in st.session_state and \
            cc.config_differences(col["doc"], st.session_state[LIVE_CONFIG]):
        st.caption("Calibrate's settings have changed since; add **Current "
                   "settings** again to compare the new ones.")
    if col["edited"]:
        st.caption("Edited on this page.")

    if is_ref:
        st.caption("Reference — the other configurations are compared with this one.")
    elif ref is not None:
        diffs = cc.config_differences(col["doc"], ref["doc"])
        if not diffs:
            st.caption(f"Same parameters as **{ref['name']}**.")
        else:
            st.caption(f"Differs from **{ref['name']}** in {len(diffs)} parameter(s):")
            st.markdown(_differences_html(diffs), unsafe_allow_html=True)

    audit = cc.audit(col["doc"])
    # `warning_html`: a key name may break after "." or "_" (<wbr>), never
    # mid-word, in a narrow card (I1 checkpoint, pending item 2); no invisible
    # character is added, so a copied key is the key (I2 round 2, R1).
    if audit["ignored"]:
        st.markdown(config_text.warning_html(
            config_text.ignored_keys_sentence(audit["ignored"])),
            unsafe_allow_html=True)
    filled = config_text.filled_keys_sentence(audit["filled"])
    if filled:
        st.markdown(config_text.warning_html(filled), unsafe_allow_html=True)

    with st.expander("Full configuration (YAML)", expanded=False):
        st.code(yaml.safe_dump(cc.effective_document(col["doc"]), sort_keys=False,
                               allow_unicode=True), language="yaml")
    with st.expander("Edit", expanded=False):
        key = EDIT_PREFIX + str(col["cid"])
        _restore(key, yaml.safe_dump(col["doc"], sort_keys=False, allow_unicode=True))
        st.text_area("Configuration (YAML)", key=key, height=220,
                     label_visibility="collapsed")
        _remember(key)
        st.button("Apply", key=f"cmp_apply_{col['cid']}", on_click=_apply_edit,
                  args=(col["cid"],))
        err = st.session_state.get(EDIT_ERROR_PREFIX + str(col["cid"]))
        if err:
            st.error(f"Not applied: {err}")
    st.button("Remove", key=f"cmp_remove_{col['cid']}", on_click=_remove,
              args=(col["cid"],))


def _differences_html(diffs: dict[str, tuple]) -> str:
    """One line per parameter, "`section.key`: this (reference: that)" — the
    wording and the line breaking are `config_text.differences_html`'s, shared
    with the Validate page."""
    return config_text.differences_html(diffs)


def _legend() -> None:
    """Phase colour key and curve key, next to the figures they explain."""
    st.markdown(
        "<div style='margin:2px 0 6px 0'>"
        + " ".join(
            f"<span style='background:{c};padding:2px 9px;border-radius:3px;"
            f"font-size:11px;color:#111;margin-right:4px'>{p}</span>"
            for p, c in li.PHASE_COLORS.items())
        + "</div>",
        unsafe_allow_html=True)
    st.caption(
        f"<span style='color:{pf.RAW_COLOR}'>━</span> vorticity as loaded (left "
        f"axis) · <span style='color:{pf.FILTERED_COLOR}'>━</span> the smoothed "
        "series each configuration detects phases on, from its own filtering "
        "(own axis, as in Calibrate's Grid)",
        unsafe_allow_html=True)


def _fmt_counts(d: dict) -> str:
    return ", ".join(f"{k} +{v}" for k, v in sorted(d.items())) or "—"


def _render_relative(run_cols, cells, ids, ref) -> None:
    n = len(ids)
    others = [c for c in run_cols if c["cid"] != ref["cid"]]
    st.markdown(f"#### Relative to {ref['name']}")
    if not others:
        st.caption(f"Only **{ref['name']}** was run. Add another configuration "
                   "and press **Run** to compare.")
        return
    st.caption(f"Over the {n} selected track(s) of the last run. Each configuration "
               f"is compared with **{ref['name']}**: these are differences, not "
               "scores.")
    data = {}
    for c in others:
        m = cc.relative(cells[c["cid"]], cells[ref["cid"]], ids)
        nc = m["n_compared"]
        data[c["name"]] = {
            "Tracks compared": f"{nc} of {n}",
            "Sequence changed": f"{m['n_sequence_changed']} of {nc}",
            "Boundary shift, median (steps)": ("—" if m["shift_median"] is None
                                               else f"{m['shift_median']:.1f}"),
            "Boundary shift, max (steps)": ("—" if m["shift_max"] is None
                                            else str(m["shift_max"])),
            "Phases appeared": _fmt_counts(m["appeared"]),
            "Phases disappeared": _fmt_counts(m["disappeared"]),
        }
    st.dataframe(pd.DataFrame(data), width="stretch")
    st.caption(f"\"Tracks compared\": tracks on which both this configuration and "
               f"{ref['name']} produced phases. Boundary shift is measured only on "
               f"tracks whose phase sequence is the same as with {ref['name']} — "
               "across a sequence change, boundaries would pair two different "
               "transitions.")


def _render_per_column(run_cols, cells, ids, ref_name: str | None,
                       missing: dict | None = None) -> None:
    """The per-configuration counts. `missing` ({cid: [id, ...]}, the Validate
    page only) names the tracks a published release never ran on: they get a
    row of their own and are not counted as failed detections."""
    n = len(ids)
    missing = missing or {}
    st.markdown("#### Per configuration")
    st.caption(f"Over the {n} selected track(s) of the last run; each configuration "
               "on its own"
               + (f", not relative to {ref_name}." if ref_name else "."))
    data = {}
    for c in run_cols:
        k, ran = cc.incipient_absent(cells[c["cid"]], ids)
        m = len(missing.get(c["cid"], []))
        data[c["name"]] = {
            "Incipient absent (first phase is not incipient)": f"{k} of {ran}",
            "Detection failed": f"{n - ran - m} of {n}",
        }
        if any(missing.values()):
            data[c["name"]]["Not in this snapshot (not counted)"] = f"{m} of {n}"
    st.dataframe(pd.DataFrame(data), width="stretch")


def _render_tracks(res: dict, ref: dict | None) -> None:
    run_cols, cells, ids = res["columns"], res["cells"], res["ids"]
    n = len(ids)
    st.markdown("#### Per track")
    c1, c2, c3 = st.columns([2, 3, 1], vertical_alignment="bottom")
    with c1:
        st.radio("Figure layout", options=FIGURE_LAYOUTS, key=K_LAYOUT,
                 horizontal=True,
                 help="Same data either way. **Stacked** puts the configurations "
                      "on one shared time axis and one shared scale, so a boundary "
                      "that moved is read straight down the figure.")
    with c2:
        st.checkbox("Show only cyclones whose sequence differs from the reference",
                    key=K_ONLY_DIFF, disabled=ref is None)
    with c3:
        st.selectbox("Tracks per page", options=PAGE_SIZES, key=K_PAGE_SIZE)
    for key in (K_LAYOUT, K_ONLY_DIFF, K_PAGE_SIZE):
        _remember(key)

    ref_cells = cells.get(ref["cid"]) if ref is not None else None

    def _differs(sid) -> list[str]:
        if ref_cells is None:
            return []
        return [c["name"] for c in run_cols if c["cid"] != ref["cid"]
                and cc.sequence_differs(cells[c["cid"]].get(sid), ref_cells.get(sid))]

    differing = {sid: _differs(sid) for sid in ids}
    only = bool(st.session_state.get(K_ONLY_DIFF)) and ref_cells is not None
    shown = [s for s in ids if differing[s]] if only else list(ids)
    if only:
        st.caption(f"{len(shown)} of the {n} selected track(s) have, in at least "
                   "one configuration, a phase sequence that differs from the one "
                   f"with {ref['name']}.")
    else:
        st.caption(f"All {n} selected track(s) of the last run.")
    if not shown:
        return

    size = int(st.session_state.get(K_PAGE_SIZE) or PAGE_SIZES[0])
    if st.session_state.get(K_SHOWN) != shown:
        st.session_state[K_SHOWN] = list(shown)
        st.session_state[K_FIRST] = 0
    n_pages = max(1, -(-len(shown) // size))
    page = min(max(st.session_state.get(K_FIRST, 0) // size + 1, 1), n_pages)
    first = (page - 1) * size
    st.session_state[K_FIRST] = first
    page_ids = shown[first:first + size]

    if n_pages > 1:
        p1, p2, p3 = st.columns([1, 3, 1], vertical_alignment="center")
        p1.button("◀ Previous", key="cmp_prev", on_click=_step_page, args=(-1,),
                  disabled=page <= 1, width="stretch")
        p2.markdown(f"<div style='text-align:center'>Page <b>{page}</b> of "
                    f"{n_pages} · tracks {first + 1}–{first + len(page_ids)} of "
                    f"{len(shown)}</div>", unsafe_allow_html=True)
        p3.button("Next ▶", key="cmp_next", on_click=_step_page, args=(1,),
                  disabled=page >= n_pages, width="stretch")
    _legend()

    stacked = st.session_state.get(K_LAYOUT) == "Stacked"
    for sid in page_ids:
        st.markdown(f"**{sid}**")
        values = res["values"].get(sid)
        if values is None:
            st.error(f"{sid}: {res['read_errors'].get(sid, 'could not be read')}")
            st.divider()
            continue
        if stacked:
            panels = tuple((c["name"], tuple(cells[c["cid"]][sid]["runs"]),
                            cells[c["cid"]][sid]["z"])
                           for c in run_cols if not cells[c["cid"]][sid]["error"])
            if panels:
                st.image(_stacked_png(values, panels), width="stretch")
            for c in run_cols:
                if cells[c["cid"]][sid]["error"]:
                    st.error(f"{c['name']}: {cells[c['cid']][sid]['error']}")
            if differing[sid]:
                st.caption(f"Sequence differs from reference ({ref['name']}): "
                           + ", ".join(differing[sid]))
        else:
            row = st.columns(len(run_cols))
            for i, c in enumerate(run_cols):
                cell = cells[c["cid"]][sid]
                with row[i]:
                    if cell["error"]:
                        st.error(f"{c['name']}: {cell['error']}")
                        continue
                    st.image(_cell_png(values, tuple(cell["runs"]), c["name"],
                                       cell["z"]), width="stretch")
                    if c["name"] in differing[sid]:
                        st.caption("sequence differs from reference")
        st.divider()


# ── the page ──────────────────────────────────────────────────────────────────
def render() -> None:
    _init_state()
    st.title(PAGE_TITLE)
    st.markdown(
        "What changes in the phases of your tracks when the configuration "
        "changes? Run two or more configurations over the tracks loaded in "
        "Calibrate and see where the detected phases differ.")

    tracks: dict[str, bytes] = st.session_state.get(LIVE_TRACKS) or {}
    if not tracks:
        _empty_state()
        return

    # ── 1 · Tracks ────────────────────────────────────────────────────────────
    names = list(tracks)
    if st.session_state.get(K_TRACKSET) != names:
        # A different set loaded in Calibrate: start again from all of it.
        st.session_state[K_TRACKSET] = list(names)
        st.session_state[K_TRACKS] = list(names)
    else:
        _restore(K_TRACKS, list(names))
        st.session_state[K_TRACKS] = [s for s in st.session_state[K_TRACKS]
                                      if s in tracks]
    selected = list(st.session_state[K_TRACKS])

    st.subheader("1 · Tracks")
    st.markdown(f"**{len(selected)} of {len(names)}** track(s) selected — the "
                "tracks loaded in Calibrate.")
    b1, b2, b3, _sp = st.columns([1, 1.5, 1, 2.5])
    b1.button("All", key="cmp_all", on_click=_select, args=("all", names),
              width="stretch")
    b2.button("Invert selection", key="cmp_invert", on_click=_select,
              args=("invert", names), width="stretch", help=INVERT_HELP)
    b3.button("Clear", key="cmp_clear", on_click=_select, args=("clear", names),
              width="stretch")
    with st.expander("Choose individually", expanded=False):
        st.multiselect("Tracks", options=names, key=K_TRACKS)
    _remember(K_TRACKS)
    selected = list(st.session_state[K_TRACKS])

    # ── 2 · Configurations ────────────────────────────────────────────────────
    st.subheader("2 · Configurations")
    st.caption("Each configuration is a column. Add Calibrate's current settings, "
               "the package defaults, or a saved YAML file.")
    full = len(_columns()) >= MAX_COLUMNS
    a1, a2, a3 = st.columns([1, 1, 2])
    a1.button(f"Add {CURRENT}", key="cmp_add_current", on_click=_add_current,
              width="stretch",
              disabled=full or LIVE_CONFIG not in st.session_state)
    a2.button(f"Add {DEFAULTS}", key="cmp_add_defaults", on_click=_add_defaults,
              width="stretch",
              disabled=full or DEFAULTS_CONFIG not in st.session_state)
    with a3:
        up = st.file_uploader("Upload YAML", type=["yaml", "yml"], key=K_UPLOAD,
                              disabled=full,
                              help="A configuration saved with Calibrate's **Save "
                                   "results**. Each new file adds one column.")
    if full:
        st.info(LIMIT_REASON)
    if up is not None:
        data = up.getvalue()
        h = hashlib.sha256(data).hexdigest()
        if st.session_state.get(K_UPLOAD_SEEN) != h:
            st.session_state[K_UPLOAD_SEEN] = h
            try:
                doc = yaml.safe_load(data)
            except yaml.YAMLError as exc:
                why = f"Invalid YAML: {exc}"
            else:
                why = cc.check_document(doc)
            if why:
                st.session_state[K_UPLOAD_ERROR] = (up.name, why)
            elif full:
                st.session_state[K_UPLOAD_ERROR] = (up.name, LIMIT_REASON)
            else:
                st.session_state.pop(K_UPLOAD_ERROR, None)
                _append(Path(up.name).stem, "upload", doc, up.name)
                st.rerun()      # draw the add controls with the new count
    else:
        st.session_state.pop(K_UPLOAD_SEEN, None)
        st.session_state.pop(K_UPLOAD_ERROR, None)
    if st.session_state.get(K_UPLOAD_ERROR):
        fname, why = st.session_state[K_UPLOAD_ERROR]
        st.error(f"`{fname}` was not added: {why}")

    cols = _columns()
    col_names = [c["name"] for c in cols]
    ref = None
    if cols:
        # Resolved here, because the cards below measure their differences from
        # it; the selector itself is drawn at the top of "4 · Results", next to
        # the numbers it changes. A change there reruns the page from the top,
        # so the cards follow it in the same run.
        _restore(K_REFERENCE, col_names[0])
        if st.session_state.get(K_REFERENCE) not in col_names:
            st.session_state[K_REFERENCE] = col_names[0]
        ref = next(c for c in cols if c["name"] == st.session_state[K_REFERENCE])
        for start in range(0, len(cols), CARDS_PER_ROW):
            row = st.columns(CARDS_PER_ROW)
            for i, col in enumerate(cols[start:start + CARDS_PER_ROW]):
                with row[i]:
                    with st.container(border=True):
                        _render_card(col, ref)
    else:
        st.caption("No configurations yet.")

    # ── 3 · Run ───────────────────────────────────────────────────────────────
    st.subheader("3 · Run")
    parsed = {s: _parsed(tracks[s]) for s in selected}
    keys = {s: p[1] for s, p in parsed.items()}
    fp = _fingerprint(cols, selected, keys)
    res = st.session_state.get(K_RESULTS)
    blockers = []
    if not cols:
        blockers.append("add at least one configuration")
    if not selected:
        blockers.append("select at least one track")
    why = ("To run, " + " and ".join(blockers) + ".") if blockers else None

    r1, r2 = st.columns([1, 3])
    run_clicked = r1.button("Run", key="cmp_run", type="primary",
                            disabled=bool(blockers), width="stretch")
    with r2:
        if why:
            st.info(why)
        elif res is not None and res["fingerprint"] != fp:
            st.warning("Results out of date — the configurations or the selected "
                       "tracks changed since the last run. Press **Run** to "
                       "update them.")
        elif res is None:
            st.caption(f"{len(cols)} configuration(s) × {len(selected)} track(s). "
                       "Nothing runs until you press **Run**.")
        else:
            # Always an element in this slot (benchmark review I2, F2): with
            # nothing here, AppTest on streamlit 1.56.0 kept the out-of-date
            # warning of the click's own pass after st.rerun().
            st.caption(f"Results are current: {len(res['columns'])} configuration(s) "
                       f"× {len(res['ids'])} track(s).")
    st.caption("Results are kept per configuration and track content, so running "
               "again after a change recomputes only what changed.")

    if run_clicked:
        total = len(cols) * len(selected)
        bar = st.progress(0.0, text=f"Running 0 of {total}…")
        cells: dict[int, dict] = {}
        done = 0
        for c in cols:
            ckey = cc.config_key(c["doc"])
            out = {}
            for s in selected:
                series, skey, err = parsed[s]
                out[s] = ({"error": err, "runs": None, "z": None} if err else
                          _cell(ckey, skey, c["doc"], series))
                done += 1
                bar.progress(done / total,
                             text=f"Running {done} of {total}: {c['name']} on {s}")
            cells[c["cid"]] = out
        bar.empty()
        st.session_state[K_RESULTS] = {
            "fingerprint": fp,
            "columns": [{"cid": c["cid"], "name": c["name"]} for c in cols],
            "ids": list(selected),
            "values": {s: (None if parsed[s][0] is None else
                           tuple(float(v) for v in parsed[s][0].values))
                       for s in selected},
            "read_errors": {s: parsed[s][2] for s in selected if parsed[s][2]},
            "cells": cells,
        }
        # The Run section above was drawn with the pre-run state; draw the page
        # once more so it agrees with the results (nothing is recomputed).
        st.rerun()

    # ── 4 · Results ───────────────────────────────────────────────────────────
    st.subheader("4 · Results")
    if cols:
        st.selectbox("Reference", options=col_names, key=K_REFERENCE,
                     help="Every difference on this page — on the cards and in "
                          "the results — is measured from this configuration. "
                          "Changing it does not run detection again.")
        _remember(K_REFERENCE)
    if res is None:
        st.info("No results yet — add configurations, then press **Run**.")
        return
    run_cols, cells, ids = res["columns"], res["cells"], res["ids"]
    # The reference is chosen among the CURRENT columns; its results exist only
    # if it was part of the last run.
    ref_run = (next((c for c in run_cols if c["cid"] == ref["cid"]), None)
               if ref is not None else None)
    if ref is not None and ref_run is None:
        st.info(f"**{ref['name']}** was not part of the last run. Press **Run** to "
                "compare against it.")
    if ref_run is not None:
        ref_run = {**ref_run, "name": ref["name"]}
        _render_relative(run_cols, cells, ids, ref_run)
    _render_per_column(run_cols, cells, ids, ref_run["name"] if ref_run else None)
    _render_tracks(res, ref_run)
