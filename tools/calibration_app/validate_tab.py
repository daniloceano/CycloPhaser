"""The Validate page — configurations measured against the manual labels.

Developer key only (app.py, `_developer_mode`): the developer half of the old
Benchmark page, retired in I3 (benchmark review, I2; the decisions and the
control-by-control inventory are in research/benchmark_review/stage0/DECISIONS.md).
It answers: how closely does each configuration agree with the manual labels
of the TRAIN split? The labels are one labeller's evidence, not a ground truth,
so every number here is an AGREEMENT with them — never called a hit rate, an
accuracy or a score.

What is decided where
---------------------
* validate_core.py — which tracks are offered and which labels exist (the test
  split's are withheld before anything reads them, and its files are never
  opened), the TRAIN / ADJUDICATED blocks, and the two instruments, which are
  benchmark_core's functions, called unchanged.
* compare_tab.py — the cached detection (`_cell`, keyed by configuration and
  track content), the figures of each configuration, the "relative to" table
  and the per-configuration block: this page calls them, so the two pages
  cannot drift apart.
* config_text.py — the card's list of differences and its warnings.

The reference is chosen among the COLUMNS only. The old Benchmark also offered
the manual label as a reference, a third, unnamed instrument against the labels
that pooled adjudicated labels with train ones (finding A1); here the label is
drawn as a panel and measured by the two named instruments, never used as a
reference.

Nothing recomputes on edit; results come from an explicit Run, are flagged out
of date when the configurations or the selection change, and are cached across
runs. Widget values survive a trip to another page by the same plain-key copies
the Compare page uses (finding A12; see compare_tab.KEEP_PREFIX).
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

import benchmark_core as bc  # noqa: E402
import compare_core as cc  # noqa: E402
import compare_tab as ct  # noqa: E402
import config_text  # noqa: E402
import layer_inspector as li  # noqa: E402
import phase_figures as pf  # noqa: E402
import validate_core as vc  # noqa: E402

PAGE_TITLE = "Validate against labels"
FIGURE_LAYOUTS = ct.FIGURE_LAYOUTS
PAGE_SIZES = ct.PAGE_SIZES
CARDS_PER_ROW = 3
MAX_COLUMNS = 6
LIMIT_REASON = (f"{MAX_COLUMNS} configurations is the limit: remove one to add "
                "another.")
INSTRUMENTS_NOTE = (
    "The two instruments have different definitions and their numbers are never "
    "added together (research/labels/README.md). **Sequence**: starts only; each "
    "boundary but the first is compared with the label's own `tolerance_idx`, and "
    "only on tracks whose phase sequence agrees with the label's — across a "
    "sequence difference no boundary is paired. **Mature**: the detected mature "
    "block with the largest overlap with the label's first mature block, both "
    "ends, fixed margin of 6 steps.")
FILTER_LABEL = "Show only tracks that disagree with the label (any column)"
SHOW_LABEL = "Show the label panel"

# Published by app.py's Calibrate page (the same sources as the Compare page).
LIVE_CONFIG = ct.LIVE_CONFIG
DEFAULTS_CONFIG = ct.DEFAULTS_CONFIG

# session_state keys of this page
K_COLUMNS = "val_columns"
K_NEXT_ID = "val_next_id"
K_TRACKS = "val_tracks"
K_TRACKSET = "_val_trackset"
K_BATCH = "val_include_batch"
K_REFERENCE = "val_reference"
K_LAYOUT = "val_figure_layout"
K_SHOW_LABEL = "val_show_label"
K_ONLY = "val_only_disagreeing"
K_PAGE_SIZE = "val_page_size"
K_PICK_CONFIG = "val_pick_config"
K_PICK_SNAPSHOT = "val_pick_snapshot"
K_FIRST = "_val_first"
K_SHOWN = "_val_shown"
K_RESULTS = "_val_results"
K_UPLOAD = "val_yaml_upload"
K_UPLOAD_SEEN = "_val_yaml_seen"
K_UPLOAD_ERROR = "_val_yaml_error"
EDIT_PREFIX = "val_edit_"
EDIT_ERROR_PREFIX = "_val_edit_error_"

WIDGET_STATE_KEYS = frozenset({K_TRACKS, K_BATCH, K_REFERENCE, K_LAYOUT,
                               K_SHOW_LABEL, K_ONLY, K_PAGE_SIZE, K_PICK_CONFIG,
                               K_PICK_SNAPSHOT})
WIDGET_STATE_PREFIXES = (EDIT_PREFIX,)
KEEP_PREFIX = "_val_kept_"           # see compare_tab.KEEP_PREFIX (finding A12)
ARRIVED = ct.ARRIVED

CURRENT, DEFAULTS = ct.CURRENT, ct.DEFAULTS
NONE = "—"


# ── cached work ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, max_entries=4)
def _population(include_batch: bool) -> dict:
    """validate_core.load_population, plus each offered track's content key."""
    pop = vc.load_population(include_batch)
    pop["keys"] = {s: cc.series_key(v) for s, v in pop["series"].items()}
    return pop


@st.cache_data(show_spinner=False, max_entries=8)
def _snapshot(path: str) -> dict:
    return bc.load_snapshot(Path(path))


@st.cache_data(show_spinner=False, max_entries=ct.PNG_CACHE_ENTRIES)
def _label_png(values: tuple, runs: tuple, spans: tuple) -> bytes:
    return pf.png(pf.cell_figure(values, runs, "label", None, li.PHASE_COLORS,
                                 tolerances=spans))


@st.cache_data(show_spinner=False, max_entries=ct.PNG_CACHE_ENTRIES)
def _stacked_png(values: tuple, panels: tuple, tolerances: tuple) -> bytes:
    return pf.png(pf.stacked_figure(values, panels, li.PHASE_COLORS,
                                    tolerances=tolerances))


# ── state ─────────────────────────────────────────────────────────────────────
def _restore(key: str, default) -> None:
    """compare_tab._restore, with this page's plain-key copies."""
    kept = KEEP_PREFIX + key
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(kept, default)
    elif st.session_state.get(ARRIVED) and kept in st.session_state:
        st.session_state[key] = st.session_state[kept]


def _remember(key: str) -> None:
    if key in st.session_state:
        st.session_state[KEEP_PREFIX + key] = st.session_state[key]


def _mark(key: str) -> None:
    """Write a widget's value back, in the run that draws it.

    The per-track controls are drawn only once there are results, many runs
    after `_init_state` set their values. Measured in Chromium (1.63.0): a
    widget drawn for the first time is drawn by the browser from its OWN default
    unless its value was set in that same run, and the next interaction sends
    that default back. The Compare page never shows this because its defaults
    are the widgets' own; here "Show the label panel" starts on, which a toggle
    does not. Re-assigning the value right before the widget marks it as set in
    this run (the pattern app.py's `_keep_page_state` uses); the value itself is
    the user's latest, so nothing changes on the server.
    """
    if key in st.session_state:
        st.session_state[key] = st.session_state[key]


def _init_state() -> None:
    st.session_state.setdefault(K_COLUMNS, [])
    st.session_state.setdefault(K_NEXT_ID, 1)
    _restore(K_BATCH, False)
    _restore(K_LAYOUT, FIGURE_LAYOUTS[0])
    _restore(K_SHOW_LABEL, True)
    _restore(K_ONLY, False)
    _restore(K_PAGE_SIZE, PAGE_SIZES[0])
    _restore(K_PICK_CONFIG, NONE)
    _restore(K_PICK_SNAPSHOT, NONE)


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


def _append(base: str, origin: str, doc: dict, origin_name: str = "",
            source_sha256: str | None = None, snapshot_path: str | None = None
            ) -> None:
    if len(_columns()) >= MAX_COLUMNS:          # the controls are disabled too
        return
    cid = st.session_state[K_NEXT_ID]
    st.session_state[K_NEXT_ID] = cid + 1
    doc = doc or {}
    _columns().append({
        "cid": cid, "name": _unique_name(base), "origin": origin,
        "origin_name": origin_name,
        "doc": {} if snapshot_path else cc.parameter_sections(doc),
        # A saved file's own record of itself, for provenance only.
        "extra": {k: doc[k] for k in ("metadata", "evaluation") if k in doc},
        "source_sha256": source_sha256, "edited": False,
        "snapshot_path": snapshot_path})


def _sha_of_doc(doc: dict) -> str:
    return bc.sha256_text(yaml.safe_dump(doc, sort_keys=True))


def _add_current() -> None:
    doc = st.session_state[LIVE_CONFIG]
    _append(CURRENT, "current", doc, "Calibrate's settings", _sha_of_doc(doc))


def _add_defaults() -> None:
    doc = st.session_state[DEFAULTS_CONFIG]
    _append(DEFAULTS, "defaults", doc, "the package defaults", _sha_of_doc(doc))


def _add_config() -> None:
    pick = st.session_state.get(K_PICK_CONFIG)
    path = next((p for p in bc.available_configs() if p.name == pick), None)
    if path is None:
        return
    text = path.read_text()
    _append(path.stem.replace("cyclophaser_params-", "params-"), "configs",
            bc.load_config_text(text), path.name, bc.sha256_text(text))


def _add_snapshot() -> None:
    pick = st.session_state.get(K_PICK_SNAPSHOT)
    path = next((p for p in bc.available_snapshots() if p.stem == pick), None)
    if path is None:
        return
    _append(f"published {path.stem}", "snapshot", {}, path.name,
            bc.sha256_text(path.read_text()), str(path))


def _remove(cid: int) -> None:
    st.session_state[K_COLUMNS] = [c for c in _columns() if c["cid"] != cid]
    for k in (EDIT_PREFIX + str(cid), KEEP_PREFIX + EDIT_PREFIX + str(cid),
              EDIT_ERROR_PREFIX + str(cid)):
        st.session_state.pop(k, None)


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


def _select(which: str, names: list[str], source: dict[str, str]) -> None:
    cur = set(st.session_state.get(K_TRACKS) or [])
    st.session_state[K_TRACKS] = (
        [n for n in names if source[n] == "real"] if which == "real" else
        [n for n in names if source[n] == "synthetic"] if which == "synthetic" else
        [] if which == "clear" else
        [n for n in names if n not in cur])


def _step_page(delta: int) -> None:
    size = st.session_state.get(K_PAGE_SIZE, PAGE_SIZES[0])
    st.session_state[K_FIRST] = max(0, st.session_state.get(K_FIRST, 0) + delta * size)


def _column_key(col: dict) -> str:
    if col.get("snapshot_path"):
        return f"snapshot:{col['source_sha256']}"
    return cc.config_key(col["doc"])


def _fingerprint(cols: list[dict], ids: list[str], keys: dict[str, str]) -> str:
    blob = json.dumps({"columns": [[c["cid"], _column_key(c)] for c in cols],
                       "tracks": [[s, keys.get(s)] for s in ids]})
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _spec(col: dict) -> bc.ColumnSpec:
    snap = _snapshot(col["snapshot_path"]) if col.get("snapshot_path") else None
    return bc.ColumnSpec(name=col["name"], doc={**col["doc"], **col["extra"]},
                         origin=col["origin"], origin_name=col["origin_name"],
                         source_sha256=col["source_sha256"],
                         edited=bool(col["edited"]), snapshot=snap)


# ── the configuration card ────────────────────────────────────────────────────
def _origin_text(col: dict) -> str:
    if col["origin"] == "current":
        return "Calibrate's settings at the moment this column was added."
    if col["origin"] == "defaults":
        return "The package defaults — what Calibrate's **Defaults** button sets."
    if col["origin"] == "configs":
        return f"From `research/labels/configs/{col['origin_name']}`."
    if col["origin"] == "snapshot":
        return (f"A published release as frozen in "
                f"`research/snapshots/{col['origin_name']}` — read from the file, "
                "not run here.")
    return f"From the uploaded file `{col['origin_name']}`."


def _short(x: str) -> str:
    return x[:12] if x and len(x) in (40, 64) else (x or NONE)


def _render_card(col: dict, ref: dict | None) -> None:
    spec = _spec(col)
    h = spec.header()
    is_ref = ref is not None and col["cid"] == ref["cid"]
    snap = col.get("snapshot_path")
    st.markdown(f"**{col['name']}**" + ("  ·  reference" if is_ref else ""))
    st.caption(_origin_text(col))
    st.caption(f"`{_short(h['config_sha256'])}` · code `{_short(h['code_commit'])}`")
    if col["origin"] == "current" and LIVE_CONFIG in st.session_state and \
            cc.config_differences(col["doc"], st.session_state[LIVE_CONFIG]):
        st.caption("Calibrate's settings have changed since; add **Current "
                   "settings** again to compare the new ones.")
    if col["edited"]:
        st.caption("Edited on this page.")
    if h["pre_filter_fix"]:
        st.warning(h.get("pre_filter_fix_short") or h["pre_filter_fix_warning"])

    if is_ref:
        st.caption("Reference — the other configurations are compared with this one.")
    elif snap:
        st.caption("A published release: no parameters of its own to compare.")
    elif ref is not None and ref.get("snapshot_path"):
        st.caption(f"**{ref['name']}** is a published release, with no parameters "
                   "to compare with.")
    elif ref is not None:
        diffs = cc.config_differences(col["doc"], ref["doc"])
        if not diffs:
            st.caption(f"Same parameters as **{ref['name']}**.")
        else:
            st.caption(f"Differs from **{ref['name']}** in {len(diffs)} parameter(s):")
            st.markdown(config_text.differences_html(diffs), unsafe_allow_html=True)

    if not snap:
        audit = cc.audit(col["doc"])
        if audit["ignored"]:
            st.markdown(config_text.warning_html(
                config_text.ignored_keys_sentence(audit["ignored"])),
                unsafe_allow_html=True)
        filled = config_text.filled_keys_sentence(audit["filled"])
        if filled:
            st.markdown(config_text.warning_html(filled), unsafe_allow_html=True)

    with st.expander("Provenance", expanded=False):
        _render_provenance(col, h)
    with st.expander("Full configuration (YAML)", expanded=False):
        if snap:
            st.code(yaml.safe_dump(h["frozen_snapshot"].get("parameters") or {},
                                   sort_keys=False), language="yaml")
        else:
            st.code(yaml.safe_dump(cc.effective_document(col["doc"]),
                                   sort_keys=False, allow_unicode=True),
                    language="yaml")
    if not snap:
        with st.expander("Edit", expanded=False):
            key = EDIT_PREFIX + str(col["cid"])
            _restore(key, yaml.safe_dump(col["doc"], sort_keys=False,
                                         allow_unicode=True))
            st.text_area("Configuration (YAML)", key=key, height=220,
                         label_visibility="collapsed")
            _remember(key)
            st.button("Apply", key=f"val_apply_{col['cid']}", on_click=_apply_edit,
                      args=(col["cid"],))
            err = st.session_state.get(EDIT_ERROR_PREFIX + str(col["cid"]))
            if err:
                st.error(f"Not applied: {err}")
    st.button("Remove", key=f"val_remove_{col['cid']}", on_click=_remove,
              args=(col["cid"],))


def _render_provenance(col: dict, h: dict) -> None:
    sha = h["config_sha256"]
    what = ("the file" if col["origin"] in ("configs", "upload", "snapshot")
            else "the configuration as added")
    st.caption(f"**1 · sha256 of {what}** — " +
               ("edited in session" if sha == "edited in session" else f"`{sha}`"))
    st.caption(f"**2 · running code commit** — `{h['code_commit']}`",
               help="The commit of the code actually running, not "
                    "`metadata.cyclophaser_version` (2.0.0 in every calibration "
                    "file, so it distinguishes nothing).")
    if col.get("snapshot_path"):
        snap = h["frozen_snapshot"]
        st.caption("**3 · published release** — " + h["pre_filter_fix_warning"])
        st.caption(f"{snap['label']} · generated {snap['generated']} · python "
                   f"{snap['python']}")
        st.caption(f"parameters: {snap['parameters']}")
        return
    st.caption("**3 · keys the running code does not read** — "
               + (", ".join(f"`{k}`" for k in h["ignored"]) if h["ignored"]
                  else "none"))
    filled = cc.audit(col["doc"])["filled"]
    differ = {k for k, _v, _d in config_text.filled_keys_that_matter(filled)}
    current = bc.current_defaults()
    if filled:
        st.caption(f"**4 · keys absent, filled by the rule of Calibrate's YAML "
                   f"import** ({len(filled)})")
        lines = []
        for k, v in filled:
            sec, name = k.split(".", 1)
            d = current.get(sec, {}).get(name, NONE)
            lines.append(f"- `{k}` = {v!r} (package default {d!r})"
                         + (" — differs" if k in differ else ""))
        st.markdown("\n".join(lines))
    else:
        st.caption("**4 · keys absent, filled by the rule of Calibrate's YAML "
                   "import** — none")
    if h["pre_filter_fix"]:
        st.caption("**5 · pre-filter-fix warning** — " + h["pre_filter_fix_warning"])
    else:
        st.caption("**5 · pre-filter-fix warning** — not applicable "
                   "(`boundary_padding` is present)")
    hist = h.get("historical")
    if hist:
        st.caption("**Historical annotation — not a score**",
                   help=hist["note"])
        st.caption(f"`evaluation.bad_cases_count` = {hist['bad_cases_count']} of "
                   f"{hist['total_cyclones']} · {hist['timestamp']} — a visual "
                   "mark made at the time, never a measure on this page.")


# ── the agreement blocks ──────────────────────────────────────────────────────
def _of(k, n) -> str:
    return f"{k} of {n}" if n else NONE


def _render_agreement(res: dict) -> None:
    run_cols, cells, ids = res["columns"], res["cells"], res["ids"]
    labels, adj = res["labels"], res["adjudicated"]
    st.markdown("#### Agreement with manual labels")
    st.caption(INSTRUMENTS_NOTE)
    per_col = {c["cid"]: vc.agreement(cells[c["cid"]], labels, ids, adj)
               for c in run_cols}
    blocks = [(vc.TRAIN, "Train")]
    if res["batch"]:
        blocks.append((vc.ADJUDICATED, "Adjudicated"))
    for block, title in blocks:
        b_ids = per_col[run_cols[0]["cid"]][block]["ids"] if run_cols else []
        n = len(b_ids)
        tag = f"{block}, n = {n}"
        st.markdown(f"##### {title} — n = {n}")
        if block == vc.TRAIN:
            st.caption(f"The selected tracks of the train split in the last run "
                       f"({n}); tracks with an adjudicated label are not in this "
                       "block. Every number in it is over this set.")
        else:
            st.caption(f"The {n} selected tracks whose label was adjudicated to the "
                       "item-30 counterfactual (Danilo, 27 Sept 2026): a "
                       "configuration that reproduces it agrees by construction, so "
                       "these are kept apart and never added to the train block.")
        if not n:
            st.caption("No selected track in this block.")
            continue
        seq_rows, mat_rows = {}, {}
        for c in run_cols:
            seq = per_col[c["cid"]][block]["sequence"]
            mat = per_col[c["cid"]][block]["mature"]
            seq_rows[c["name"]] = {
                f"Sequence agrees with label ({tag})":
                    _of(seq["n_sequence_match"], seq["n_series"]),
                f"Boundaries within the label's tolerance ({tag})":
                    _of(seq["n_boundaries_hit"], seq["n_boundaries"]),
                f"Boundaries the label marks unsure, not compared ({tag})":
                    str(seq.get("n_boundaries_unsure", 0)),
            }
            mat_rows[c["name"]] = {
                f"Mature paired within margin {bc.MATURE_MARGIN} ({tag})":
                    _of(mat["n_hit"], mat["n"]),
            }
        notes = _missing_notes(run_cols, cells, b_ids)
        st.markdown(f"**Sequence** · instrument `{bc.SEQUENCE_INSTRUMENT}` · {tag}")
        st.dataframe(pd.DataFrame(seq_rows), width="stretch")
        st.caption("\"Sequence agrees\": of the tracks on which the configuration "
                   "produced phases. \"Boundaries\": on the tracks whose sequence "
                   "agrees, every boundary but the first.")
        for note in notes:
            st.caption(note)
        st.markdown(f"**Mature** · instrument `{bc.MATURE_INSTRUMENT}` · {tag}")
        st.dataframe(pd.DataFrame(mat_rows), width="stretch")
        st.caption("Of the tracks whose label has a mature phase and on which the "
                   "configuration produced phases.")
        for note in notes:
            st.caption(note)
        for c in run_cols:
            d = vc.disagreements(cells[c["cid"]], labels, b_ids)
            with st.expander(_disagreement_header(c["name"], tag, d), expanded=False):
                _render_disagreements(d)


def _missing_notes(run_cols, cells, ids) -> list[str]:
    """One line per published-release column that never ran on some of `ids`
    (finding F3): those tracks are out of its denominators, and this says so."""
    out = []
    for c in run_cols:
        m = vc.missing(cells[c["cid"]], ids)
        if m:
            out.append(f"{c['name']}: {len(m)} of {len(ids)} tracks are {vc.NOT_IN_SNAPSHOT} "
                       "(published releases cover the 51 + 12 bundled series) and are "
                       "not counted.")
    return out


def _disagreement_header(name: str, tag: str, d: dict) -> str:
    """Counts per instrument, never a number that pools the two (R2)."""
    parts = [f"sequence: {len(d['sequence_differs'])} tracks differ, "
             f"{len(d['outside_tolerance'])} tracks with a boundary outside its "
             "tolerance",
             f"mature: {len(d['mature'])} tracks not within the margin"]
    if d["failed"]:
        parts.append(f"detection failed: {len(d['failed'])}")
    if d["not_in_snapshot"]:
        parts.append(f"{vc.NOT_IN_SNAPSHOT}: {len(d['not_in_snapshot'])}")
    return f"Tracks that disagree with the label — {name} ({tag}) · " + " · ".join(parts)


def _render_disagreements(d: dict) -> None:
    def ids(xs):
        return ", ".join(f"`{x}`" for x in xs) or "none"
    st.markdown(
        f"**Sequence instrument**\n\n"
        f"- sequence differs from label: {ids(d['sequence_differs'])}\n"
        "- same sequence, boundaries outside the label's tolerance: "
        + (", ".join(f"`{s}` ({k} of {m})" for s, k, m in d["outside_tolerance"])
           or "none")
        + f"\n- detection failed: {ids(d['failed'])}\n"
        + (f"- {vc.NOT_IN_SNAPSHOT} (not compared): {ids(d['not_in_snapshot'])}\n"
           if d["not_in_snapshot"] else "")
        + "\n"
        f"**Mature instrument** (margin {bc.MATURE_MARGIN})\n\n"
        "- mature not paired within the margin: "
        + (", ".join(f"`{s}` ({_mature_offsets(a, b)})" for s, a, b in d["mature"])
           or "none"))


def _mature_offsets(ds, de) -> str:
    if ds is None:
        return "no detected mature block pairs with the label's"
    return f"start {ds:+d}, end {de:+d} steps"


# ── per track ─────────────────────────────────────────────────────────────────
def _cell_notes(cell: dict, rec: dict) -> list[str]:
    note = vc.track_note(cell, rec)
    if note["sequence"] is None:
        return []
    out = ["sequence agrees with label" if note["sequence"] == "agrees"
           else "sequence differs from label"]
    if note["outside"]:
        out.append(f"{note['outside']} of {note['scored']} boundaries outside the "
                   "label's tolerance")
    m = note["mature"]
    if m is not None:
        out.append(f"mature {_mature_offsets(m['d_start'], m['d_end'])} vs label "
                   f"(margin {bc.MATURE_MARGIN})")
    return out


def _tolerance_legend() -> None:
    st.caption("Label panel: hatched band — the label's tolerance at each boundary "
               "(start_idx ± tolerance_idx, the detected boundaries the sequence "
               "instrument accepts), solid line at the label's boundary; dashed "
               "line — a boundary the labeller marked unsure, not compared.")


def _render_tracks(res: dict, pop: dict) -> None:
    run_cols, cells, ids = res["columns"], res["cells"], res["ids"]
    labels, adj = res["labels"], set(res["adjudicated"])
    n = len(ids)
    st.markdown("#### Per track")
    for key in (K_LAYOUT, K_SHOW_LABEL, K_ONLY, K_PAGE_SIZE):
        _mark(key)
    c1, c2, c3, c4 = st.columns([2, 1.4, 2.6, 1], vertical_alignment="bottom")
    with c1:
        st.radio("Figure layout", options=FIGURE_LAYOUTS, key=K_LAYOUT,
                 horizontal=True,
                 help="Same data either way. **Stacked** puts the label and the "
                      "configurations on one shared time axis and one shared "
                      "scale, so a boundary is read straight down the figure.")
    with c2:
        st.toggle(SHOW_LABEL, key=K_SHOW_LABEL)
    with c3:
        st.checkbox(FILTER_LABEL, key=K_ONLY)
    with c4:
        st.selectbox("Tracks per page", options=PAGE_SIZES, key=K_PAGE_SIZE)
    for key in (K_LAYOUT, K_SHOW_LABEL, K_ONLY, K_PAGE_SIZE):
        _remember(key)

    per_col = [vc.disagreements(cells[c["cid"]], labels, ids) for c in run_cols]
    only = bool(st.session_state.get(K_ONLY))
    shown = [s for s in ids if vc.disagrees(per_col, s)] if only else list(ids)
    if only:
        st.caption(f"{len(shown)} of the {n} selected track(s) disagree with the "
                   "label in at least one configuration: sequence differs, a "
                   "boundary outside its tolerance, mature not paired within the "
                   "margin, or detection failed.")
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
        p1.button("◀ Previous", key="val_prev", on_click=_step_page, args=(-1,),
                  disabled=page <= 1, width="stretch")
        p2.markdown(f"<div style='text-align:center'>Page <b>{page}</b> of "
                    f"{n_pages} · tracks {first + 1}–{first + len(page_ids)} of "
                    f"{len(shown)}</div>", unsafe_allow_html=True)
        p3.button("Next ▶", key="val_next", on_click=_step_page, args=(1,),
                  disabled=page >= n_pages, width="stretch")
    ct._legend()
    show_label = bool(st.session_state.get(K_SHOW_LABEL))
    if show_label:
        _tolerance_legend()

    stacked = st.session_state.get(K_LAYOUT) == "Stacked"
    for sid in page_ids:
        batch = sid in res["batch_ids"]
        if batch and sid not in pop["series"]:
            st.caption(f"**{sid}** — no longer loaded (swell_item30 batch "
                       "excluded); run again to refresh.")
            continue
        st.markdown(f"**{sid}** · {res['source'].get(sid, NONE)} · "
                    + ("adjudicated" if sid in adj else "train")
                    + (" · swell_item30" if batch else ""))
        values, rec = res["values"][sid], labels[sid]
        lab_runs, spans = vc.label_runs(rec), vc.tolerance_spans(rec)
        if stacked:
            panels, tols = [], []
            if show_label:
                panels.append(("label", lab_runs, None))
                tols.append(spans)
            for c in run_cols:
                cell = cells[c["cid"]][sid]
                if not cell["error"]:
                    panels.append((c["name"], tuple(cell["runs"]), cell.get("z")))
                    tols.append(None)
            if panels:
                st.image(_stacked_png(values, tuple(panels), tuple(tols)),
                         width="stretch")
            for c in run_cols:
                cell = cells[c["cid"]][sid]
                if cell.get("missing"):
                    st.caption(f"**{c['name']}** — {vc.NOT_IN_SNAPSHOT}")
                    continue
                if cell["error"]:
                    st.error(f"{c['name']}: {cell['error']}")
                    continue
                notes = _cell_notes(cell, rec)
                if notes:
                    st.caption(f"**{c['name']}** — " + "; ".join(notes))
        else:
            row = st.columns(len(run_cols) + (1 if show_label else 0))
            off = 0
            if show_label:
                with row[0]:
                    st.image(_label_png(values, lab_runs, spans), width="stretch")
                off = 1
            for i, c in enumerate(run_cols):
                cell = cells[c["cid"]][sid]
                with row[i + off]:
                    if cell.get("missing"):
                        st.caption(f"{c['name']}: {vc.NOT_IN_SNAPSHOT}")
                        continue
                    if cell["error"]:
                        st.error(f"{c['name']}: {cell['error']}")
                        continue
                    st.image(ct._cell_png(values, tuple(cell["runs"]), c["name"],
                                          cell.get("z")), width="stretch")
                    for line in _cell_notes(cell, rec):
                        st.caption(line)
        st.divider()


# ── the page ──────────────────────────────────────────────────────────────────
def render() -> None:
    _init_state()
    st.title(PAGE_TITLE)
    st.markdown(
        "How closely does each configuration agree with the manual labels of the "
        "train split? The labels are one labeller's evidence, not a ground truth: "
        "the numbers below are agreements with them, measured by two named "
        "instruments.")

    pop = _population(bool(st.session_state.get(K_BATCH)))
    offered = list(pop["series"])
    source = pop["source"]

    # The offered set changes with the batch: newly offered tracks join the
    # selection, tracks no longer offered leave it.
    if st.session_state.get(K_TRACKSET) != offered:
        old = st.session_state.get(K_TRACKSET)
        if old is None:
            _restore(K_TRACKS, list(offered))
        else:
            cur = [s for s in st.session_state.get(K_TRACKS, []) if s in offered]
            st.session_state[K_TRACKS] = cur + [s for s in offered
                                                if s not in old and s not in cur]
        st.session_state[K_TRACKSET] = list(offered)
    else:
        _restore(K_TRACKS, list(offered))
    st.session_state[K_TRACKS] = [s for s in st.session_state[K_TRACKS]
                                  if s in offered]
    selected = list(st.session_state[K_TRACKS])
    cols = _columns()
    ref_name = st.session_state.get(K_REFERENCE)
    n_lab = sum(1 for s in selected if s in pop["labels"])
    st.markdown(f"**{len(cols)}** configuration(s)  ·  **{len(selected)}** of "
                f"{len(offered)} track(s) selected  ·  manual labels: {n_lab} of "
                f"{len(selected)}  ·  reference: **{ref_name or NONE}**")

    # ── 1 · Tracks ────────────────────────────────────────────────────────────
    st.subheader("1 · Tracks")
    n_real = sum(1 for s in offered if source[s] == "real")
    n_syn = len(offered) - n_real
    st.caption(f"Labelled tracks of the train split, read from disk: {n_real} real "
               f"and {n_syn} synthetic. The 16 tracks of the test split are not "
               "offered: their files are not opened and their labels are withheld "
               "before anything on this page reads them.")
    st.checkbox("Include swell_item30 batch", key=K_BATCH,
                help="Adds the train tracks of the item-30 swell batch (split.yaml "
                     "`batches: swell_item30`). Those whose label was adjudicated to "
                     "the item-30 counterfactual are measured in a block of their "
                     "own; the batch's 3 test tracks are never offered.")
    _remember(K_BATCH)
    if pop["batch_error"]:
        st.error(f"The swell_item30 batch could not be loaded "
                 f"({pop['batch_error']}) — continuing without it.")
    elif pop["batch_ids"]:
        n_adj = sum(1 for s in pop["batch_ids"] if s in pop["adjudicated"])
        st.caption(f"swell_item30: {len(pop['batch_ids'])} train tracks loaded, "
                   f"{n_adj} of them with an adjudicated label; its 3 test tracks "
                   "are not offered.")
    if pop["not_offered"]:
        st.warning("Not offered: " + "; ".join(
            f"`{s}` — {why}" for s, why in sorted(pop["not_offered"].items())))
    st.markdown(f"**{len(selected)} of {len(offered)}** track(s) selected.")
    b1, b2, b3, b4, _sp = st.columns([1, 1.2, 1.5, 1, 1.3])
    b1.button("All real", key="val_all_real", on_click=_select,
              args=("real", offered, source), width="stretch")
    b2.button("All synthetic", key="val_all_synthetic", on_click=_select,
              args=("synthetic", offered, source), width="stretch")
    b3.button("Invert selection", key="val_invert", on_click=_select,
              args=("invert", offered, source), width="stretch",
              help=ct.INVERT_HELP)
    b4.button("Clear", key="val_clear", on_click=_select,
              args=("clear", offered, source), width="stretch")
    adj_set = set(pop["adjudicated"])
    with st.expander("Choose individually", expanded=False):
        st.multiselect(
            "Tracks", options=offered, key=K_TRACKS,
            format_func=lambda s: (f"{s} ({source[s]}"
                                   + (", swell_item30" if s in pop["batch_ids"] else "")
                                   + (", adjudicated" if s in adj_set else "") + ")"))
    _remember(K_TRACKS)
    selected = list(st.session_state[K_TRACKS])

    # ── 2 · Configurations ────────────────────────────────────────────────────
    st.subheader("2 · Configurations")
    st.caption("Each configuration is a column: Calibrate's current settings, the "
               "package defaults, a calibration file, an uploaded YAML, or a "
               "published release.")
    full = len(cols) >= MAX_COLUMNS
    a1, a2, a3 = st.columns([1, 1, 2])
    a1.button(f"Add {CURRENT}", key="val_add_current", on_click=_add_current,
              width="stretch", disabled=full or LIVE_CONFIG not in st.session_state,
              help=None if LIVE_CONFIG in st.session_state else
              "Open the Calibrate page once first: its settings have not been built "
              "in this session yet.")
    a2.button(f"Add {DEFAULTS}", key="val_add_defaults", on_click=_add_defaults,
              width="stretch",
              disabled=full or DEFAULTS_CONFIG not in st.session_state)
    with a3:
        up = st.file_uploader("Upload YAML", type=["yaml", "yml"], key=K_UPLOAD,
                              disabled=full,
                              help="A configuration saved with Calibrate's **Save "
                                   "results**. Each new file adds one column.")
    c1, c2, c3, c4 = st.columns([1.6, 1, 1.6, 1], vertical_alignment="bottom")
    cfgs = [p.name for p in bc.available_configs()]
    if st.session_state.get(K_PICK_CONFIG) not in [NONE] + cfgs:
        st.session_state[K_PICK_CONFIG] = NONE
    c1.selectbox("Calibration file (research/labels/configs/)",
                 options=[NONE] + cfgs, key=K_PICK_CONFIG, disabled=full)
    c2.button("Add file", key="val_add_config", on_click=_add_config,
              width="stretch",
              disabled=full or st.session_state.get(K_PICK_CONFIG) == NONE)
    snaps = [p.stem for p in bc.available_snapshots()]
    if st.session_state.get(K_PICK_SNAPSHOT) not in [NONE] + snaps:
        st.session_state[K_PICK_SNAPSHOT] = NONE
    c3.selectbox("Published release (research/snapshots/)",
                 options=[NONE] + snaps, key=K_PICK_SNAPSHOT, disabled=full,
                 help="Phases recorded by a published release with its own package "
                      "defaults, read from the file. Covers the 51 + 12 bundled "
                      "series only, not the swell_item30 batch.")
    c4.button("Add release", key="val_add_snapshot", on_click=_add_snapshot,
              width="stretch",
              disabled=full or st.session_state.get(K_PICK_SNAPSHOT) == NONE)
    for key in (K_PICK_CONFIG, K_PICK_SNAPSHOT):
        _remember(key)
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
                _append(Path(up.name).stem, "upload", doc, up.name,
                        bc.sha256_text(data.decode("utf-8", "replace")))
                st.rerun()
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
    keys = pop["keys"]
    fp = _fingerprint(cols, selected, keys)
    res = st.session_state.get(K_RESULTS)
    blockers = []
    if not cols:
        blockers.append("add at least one configuration")
    if not selected:
        blockers.append("select at least one track")
    why = ("To run, " + " and ".join(blockers) + ".") if blockers else None
    r1, r2 = st.columns([1, 3])
    run_clicked = r1.button("Run", key="val_run", type="primary",
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
            # Always an element in this slot: AppTest on streamlit 1.56.0 kept
            # the out-of-date warning of the click's own pass when the pass
            # after st.rerun() drew nothing here (measured, I2 round 1; the
            # browser cleared it on both versions).
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
            out = {}
            if c.get("snapshot_path"):
                snap = _snapshot(c["snapshot_path"])
                for s in selected:
                    out[s] = vc.snapshot_cell(snap, s)
                    done += 1
                bar.progress(done / total, text=f"Running {done} of {total}: "
                                                f"{c['name']} read from its file")
            else:
                ckey = cc.config_key(c["doc"])
                for s in selected:
                    out[s] = ct._cell(ckey, keys[s], c["doc"], pop["series"][s])
                    done += 1
                    bar.progress(done / total,
                                 text=f"Running {done} of {total}: {c['name']} on {s}")
            cells[c["cid"]] = out
        bar.empty()
        st.session_state[K_RESULTS] = {
            "fingerprint": fp,
            "columns": [{"cid": c["cid"], "name": c["name"]} for c in cols],
            "ids": list(selected),
            "values": {s: tuple(float(v) for v in pop["series"][s].values)
                       for s in selected},
            "cells": cells,
            "labels": {s: pop["labels"][s] for s in selected},
            "adjudicated": [s for s in pop["adjudicated"] if s in selected],
            "batch": bool(st.session_state.get(K_BATCH)),
            "batch_ids": [s for s in pop["batch_ids"] if s in selected],
            "source": {s: source[s] for s in selected},
        }
        st.rerun()

    # ── 4 · Results ───────────────────────────────────────────────────────────
    st.subheader("4 · Results")
    if cols:
        _mark(K_REFERENCE)
        st.selectbox("Reference", options=col_names, key=K_REFERENCE,
                     help="The configuration the cards and the \"relative to\" "
                          "table measure from — a column, never the label (the "
                          "label is measured by the two instruments below). "
                          "Changing it does not run detection again.")
        _remember(K_REFERENCE)
    if res is None:
        st.info("No results yet — add configurations, then press **Run**.")
        return
    run_cols, cells, ids = res["columns"], res["cells"], res["ids"]
    _render_agreement(res)
    ref_run = (next((c for c in run_cols if c["cid"] == ref["cid"]), None)
               if ref is not None else None)
    if ref is not None and ref_run is None:
        st.info(f"**{ref['name']}** was not part of the last run. Press **Run** to "
                "compare against it.")
    if ref_run is not None:
        ref_run = {**ref_run, "name": ref["name"]}
        ct._render_relative(run_cols, cells, ids, ref_run)
        for note in _missing_notes(run_cols, cells, ids):
            st.caption(note + " \"Tracks compared\" leaves them out.")
    ct._render_per_column(run_cols, cells, ids, ref_run["name"] if ref_run else None,
                          missing={c["cid"]: vc.missing(cells[c["cid"]], ids)
                                   for c in run_cols})
    _render_tracks(res, pop)
