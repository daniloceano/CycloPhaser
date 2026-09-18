"""The Benchmark tab — N configurations over the same cyclones, aligned in columns.

All logic lives in `benchmark_core`; this file is the Streamlit surface over it.
See that module's docstring for the three structural rules (code commit as
provenance, `bad_cases_count` never a score, `item19_core.CONFIG` never
repointed) and for the leakage rule on aggregates.

Layout decisions worth stating, because they were decisions rather than defaults:

* **A column is edited as YAML text.** The alternative — a full widget tree per
  column — multiplies every sidebar control by the number of columns, and the
  point of this tab is to hold several configurations on screen at once. A text
  area also keeps "what is this column running" answerable by reading one thing,
  which is the property the header exists to guarantee.
* **The header is one visible line plus a Provenance drop-down.** All five
  mandatory items are still there; stacking them as five captions per column
  buried the figures under a wall of small text. The one item that stays visible
  is the pre-filter-fix warning, because it is the one that stops a column being
  misread as history.
* **The colour legend sits immediately above the first figure**, not at the top
  of the tab — a key the reader has to scroll back to is not a key.
* **Column state lives in explicit `st.session_state` entries**, not in widget-key
  memory. A widget with a stable key loses its value across an `st.rerun()` issued
  earlier in the same script run, which this tab does on every add/remove.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yaml

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

import benchmark_core as bc  # noqa: E402

PHASE_COLORS = {
    "incipient": "#65a1e6",
    "intensification": "#f7b538",
    "mature": "#d62828",
    "decay": "#9aa981",
    "residual": "gray",
}

# session_state keys — explicit, see the module docstring
K_COLUMNS = "bench_columns"
K_IDS = "bench_selected_ids"
K_LABELS = "bench_show_labels"
K_NEXT_ID = "bench_next_id"


# ── state ─────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    st.session_state.setdefault(K_COLUMNS, [])
    st.session_state.setdefault(K_IDS, [])
    st.session_state.setdefault(K_LABELS, False)
    st.session_state.setdefault(K_NEXT_ID, 1)


def _new_column(name: str, doc: dict, origin: str, origin_name: str = "",
                source_sha256: str | None = None,
                snapshot_path: str | None = None) -> dict:
    cid = st.session_state[K_NEXT_ID]
    st.session_state[K_NEXT_ID] = cid + 1
    return {
        "cid": cid,
        "name": name,
        "yaml_text": yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
        "origin": origin,
        "origin_name": origin_name,
        "source_sha256": source_sha256,
        "edited": False,
        "snapshot_path": snapshot_path,
    }


def _spec(col: dict) -> bc.ColumnSpec:
    snap = None
    if col.get("snapshot_path"):
        snap = bc.load_snapshot(Path(col["snapshot_path"]))
    try:
        doc = bc.load_config_text(col["yaml_text"])
    except Exception:
        doc = {}
    return bc.ColumnSpec(
        name=col["name"], doc=doc, origin=col["origin"],
        origin_name=col.get("origin_name", ""),
        source_sha256=col.get("source_sha256"),
        edited=bool(col.get("edited")), snapshot=snap,
    )


def _sidebar_doc() -> dict:
    """The sidebar's live state as a config document.

    Read from `st.session_state["_bench_live_config"]`, which app.py refreshes on
    every run from the same `_PHASE_PARAMS`/filter values it passes to the
    detector — so a column created from the sidebar carries exactly what the
    Calibration tab is showing, not a re-derivation of it.
    """
    return st.session_state.get("_bench_live_config") or {
        "filter_params": {}, "phase_params": {}}


# ── figure ────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, max_entries=512)
def _cell_png(values_tuple: tuple, runs_tuple: tuple, title: str) -> bytes:
    """Raw series with the column's phases as background bands."""
    matplotlib.use("Agg")
    fig, ax = plt.subplots(figsize=(3.6, 1.7))
    ax.plot(range(len(values_tuple)), values_tuple, color="k", lw=1.0)
    for phase, a, b in runs_tuple:
        ax.axvspan(a, b + 0.999, color=PHASE_COLORS.get(phase, "white"),
                   alpha=0.45, lw=0)
    ax.set_title(title, fontsize=7)
    ax.tick_params(labelsize=6)
    ax.set_xlim(0, max(1, len(values_tuple) - 1))
    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    return buf.getvalue()


def _legend() -> None:
    """Phase colour key. Rendered next to the figures it explains."""
    st.markdown(
        "<div style='margin:2px 0 6px 0'>"
        + " ".join(
            f"<span style='background:{c};padding:2px 9px;border-radius:3px;"
            f"font-size:11px;color:#111;margin-right:4px'>{p}</span>"
            for p, c in PHASE_COLORS.items())
        + "</div>",
        unsafe_allow_html=True)


# ── header rendering ──────────────────────────────────────────────────────────
def _short(sha: str) -> str:
    return sha[:12] if sha and len(sha) == 64 else (sha or "—")


def _render_header(col: dict, spec: bc.ColumnSpec) -> None:
    """One visible identity line, the warning if it applies, then a drop-down.

    All five mandatory header items are present: 1 and 2 on the visible line and
    repeated in full inside Provenance, 3 4 and 5 inside it — except the
    pre-filter-fix warning, which also stays visible.
    """
    h = spec.header()
    st.markdown(f"**{col['name']}**")

    sha = h["config_sha256"]
    sha_txt = sha if sha in ("editado na sessão", "edited in session") else _short(sha)
    commit = h["code_commit"]
    commit_txt = commit[:12] if len(commit) == 40 else commit
    st.caption(f"`{sha_txt}` · code `{commit_txt}`")

    if h["pre_filter_fix"]:
        st.warning(h.get("pre_filter_fix_short") or h["pre_filter_fix_warning"],
                   icon="⚠️")

    n_extra = len(h["ignored"]) + len(h["defaulted"])
    with st.expander(f"Provenance ({n_extra} note(s))" if n_extra else "Provenance",
                     expanded=False):
        st.caption(f"**1 · source YAML sha256** — `{sha_txt}`")
        st.caption(f"**2 · running code commit** — `{commit_txt}` "
                   "(not `metadata.cyclophaser_version`, which reads 2.0.0 in "
                   "every one of the eleven files)")
        if h["ignored"]:
            st.caption("**3 · keys ignored by the current signature** — "
                       + ", ".join(f"`{k}`" for k in h["ignored"]))
        else:
            st.caption("**3 · keys ignored by the current signature** — none")
        if h["defaulted"]:
            st.caption(f"**4 · keys absent, filled by the current default** "
                       f"({len(h['defaulted'])})")
            st.dataframe(
                pd.DataFrame({"default in use": {k: repr(v)
                                                 for k, v in h["defaulted"].items()}}),
                use_container_width=True)
        else:
            st.caption("**4 · keys absent, filled by the current default** — none")
        if h["pre_filter_fix"]:
            st.caption("**5 · pre-filter-fix warning**")
            st.caption(h["pre_filter_fix_warning"])
        else:
            st.caption("**5 · pre-filter-fix warning** — not applicable "
                       "(`boundary_padding` is present)")

        if h.get("historical"):
            hist = h["historical"]
            st.divider()
            st.caption("**Historical annotation — not a metric**")
            st.caption(hist["note"])
            st.caption(f"`evaluation.bad_cases_count` = {hist['bad_cases_count']} "
                       f"of {hist['total_cyclones']} · {hist['timestamp']}")
            if hist["bad_cases"]:
                st.caption(", ".join(str(b) for b in hist["bad_cases"]))

        if h.get("frozen_snapshot"):
            snap = h["frozen_snapshot"]
            st.divider()
            st.caption("**Frozen snapshot**")
            st.caption(snap["label"])
            st.caption(f"generated {snap['generated']} · python {snap['python']}")
            st.caption(f"parameters: {snap['parameters']}")


# ── the summary table ─────────────────────────────────────────────────────────
def _pct(x) -> str:
    return "—" if x is None else f"{100 * x:.0f}%"


def _summary_frame(metrics_per_column: list[dict], names: list[str],
                   split: str) -> pd.DataFrame:
    """Rows = measurements, columns = configurations — the tab's own alignment."""
    data: dict[str, dict[str, str]] = {}
    for name, m in zip(names, metrics_per_column):
        blk = m[split]
        seq, mat = blk["sequence"], blk["mature"]
        n_series = seq.get("n_series") or 0
        data[name] = {
            "Series": str(len(blk["ids"])),
            "Sequence match": (f"{seq['n_sequence_match']}/{n_series}"
                               if n_series else "—"),
            "Sequence match rate": (_pct(seq["sequence_match_rate"])
                                    if n_series else "—"),
            "Boundaries within margin": (f"{seq['n_boundaries_hit']}/"
                                         f"{seq['n_boundaries']}"
                                         if seq.get("n_boundaries") else "—"),
            "Boundary hit rate": (_pct(seq.get("boundary_hit_rate"))
                                  if seq.get("n_boundaries") else "—"),
            "Mature paired": f"{mat['n_hit']}/{mat['n']}" if mat["n"] else "—",
            "Mature hit rate": _pct(mat["hit_rate"]) if mat["n"] else "—",
        }
    return pd.DataFrame(data)


def _render_summary(metrics_per_column: list[dict], names: list[str]) -> None:
    st.markdown("#### Summary")
    st.caption(
        "Leakage rule: every aggregate here is computed over the TRAIN split. "
        "The test block is separate, labelled, and never added into the train "
        "one."
    )
    train_n = len(metrics_per_column[0]["train"]["ids"]) if metrics_per_column else 0
    test_n = len(metrics_per_column[0]["test"]["ids"]) if metrics_per_column else 0

    with st.expander(f"Train split — {train_n} series", expanded=True):
        if train_n:
            st.dataframe(_summary_frame(metrics_per_column, names, "train"),
                         use_container_width=True)
            st.caption(
                f"Sequence rows · {bc.SEQUENCE_INSTRUMENT}  \n"
                f"Mature rows · {bc.MATURE_INSTRUMENT}  \n"
                "Two different instruments. Reported side by side, never summed."
            )
        else:
            st.caption("No train-split cyclone in the current selection.")

    with st.expander(f"Test split (frozen) — {test_n} series", expanded=False):
        if test_n:
            st.caption(
                "⚠️ Frozen test split. Shown on request; never combined with the "
                "train numbers above.")
            st.dataframe(_summary_frame(metrics_per_column, names, "test"),
                         use_container_width=True)
        else:
            st.caption("No test-split cyclone in the current selection.")


# ── the tab ───────────────────────────────────────────────────────────────────
def render() -> None:
    _init_state()
    st.subheader("Benchmark — N configurations over the same cyclones")
    st.caption(
        "Each column is an independent configuration, run over the cyclones "
        "selected below and aligned by cyclone. Both measurements are always "
        "shown, each named by the instrument that produced it — they are "
        "different instruments and are never summed. The YAML's own "
        "`evaluation.bad_cases_count` is never used as a score: it appears only "
        "as a labelled historical annotation, under each column's Provenance."
    )

    series_all, source_of = bc.load_all_series()
    membership = bc.split_membership()
    labels = bc.labels_for_display()

    # ── 1 · cyclone selection ─────────────────────────────────────────────────
    ids_sorted = sorted(series_all, key=lambda s: (source_of[s], s))
    # Every add/remove reruns, so this count is always the settled one.
    n_cols_now = len(st.session_state[K_COLUMNS])
    # `expanded` is forced on every rerun, so a value derived from state would
    # make these panels snap open and shut under the user as they work. Both are
    # therefore statically open: adding columns and changing the selection are
    # the two repeated actions in this tab.
    with st.expander(
            f"1 · Cyclones — {len(st.session_state[K_IDS])} selected",
            expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("All real (51)", key="bench_pick_real",
                         use_container_width=True):
                st.session_state[K_IDS] = [s for s in ids_sorted
                                           if source_of[s] == "real"]
        with c2:
            if st.button("All synthetic (12)", key="bench_pick_synth",
                         use_container_width=True):
                st.session_state[K_IDS] = [s for s in ids_sorted
                                           if source_of[s] == "synthetic"]
        with c3:
            if st.button("Clear", key="bench_pick_none",
                         use_container_width=True):
                st.session_state[K_IDS] = []
        selected = st.multiselect(
            "Free selection — any subset of the 63 records (51 real + 12 "
            "synthetic). Not tied to the train/test split.",
            options=ids_sorted,
            default=st.session_state[K_IDS],
            key="bench_ids_widget",
            format_func=lambda s: f"{s} ({source_of[s]}/{membership.get(s, '—')})",
        )
        st.session_state[K_IDS] = list(selected)

        st.checkbox(
            "Show manual labels as a first column", key=K_LABELS,
            help="Opt-in. Draws the human label beside the first column, for "
                 "the records that carry one.",
        )

    # ── 2 · columns ───────────────────────────────────────────────────────────
    with st.expander(f"2 · Configurations — {n_cols_now} column(s)",
                     expanded=True):
        st.caption(
            f"Each column runs the whole detector over every selected cyclone. "
            f"Now: {n_cols_now} column(s) × {len(selected)} cyclone(s) = "
            f"{n_cols_now * len(selected)} run(s), cached per "
            "config × cyclone pair."
        )
        a1, a2 = st.columns(2)
        with a1:
            st.markdown("**From the sidebar**")
            if st.button("Add column from current sidebar state",
                         key="bench_add_sidebar", use_container_width=True):
                doc = _sidebar_doc()
                st.session_state[K_COLUMNS].append(_new_column(
                    f"sidebar #{st.session_state[K_NEXT_ID]}", doc, "sidebar",
                    "current sidebar state",
                    bc.sha256_text(yaml.safe_dump(doc, sort_keys=True))))
                st.rerun()
        with a2:
            st.markdown("**From a saved configuration**")
            cfgs = bc.available_configs()
            pick = st.selectbox(
                "research/labels/configs/",
                options=["—"] + [p.name for p in cfgs],
                key="bench_pick_config")
            if st.button("Add column from the selected file",
                         key="bench_add_config",
                         use_container_width=True, disabled=(pick == "—")):
                path = next(p for p in cfgs if p.name == pick)
                text = path.read_text()
                st.session_state[K_COLUMNS].append(_new_column(
                    path.stem.replace("cyclophaser_params-", "params-"),
                    bc.load_config_text(text), "configs", path.name,
                    bc.sha256_text(text)))
                st.rerun()

        b1, b2 = st.columns(2)
        with b1:
            st.markdown("**From an uploaded YAML**")
            up = st.file_uploader("Upload a configuration", type=["yaml", "yml"],
                                  key="bench_upload", label_visibility="collapsed")
            if up is not None:
                text = up.getvalue().decode("utf-8")
                sha = bc.sha256_text(text)
                if st.session_state.get("_bench_upload_sha") != sha:
                    try:
                        st.session_state[K_COLUMNS].append(_new_column(
                            Path(up.name).stem, bc.load_config_text(text),
                            "upload", up.name, sha))
                        st.session_state["_bench_upload_sha"] = sha
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Invalid YAML: {exc}")
        with b2:
            st.markdown("**From a frozen published version**")
            snaps = bc.available_snapshots()
            if snaps:
                spick = st.selectbox("research/snapshots/",
                                     options=["—"] + [p.stem for p in snaps],
                                     key="bench_pick_snapshot")
                if st.button("Add reference column", key="bench_add_snapshot",
                             use_container_width=True, disabled=(spick == "—")):
                    path = next(p for p in snaps if p.stem == spick)
                    st.session_state[K_COLUMNS].append(_new_column(
                        f"published {path.stem}", {}, "snapshot", path.name,
                        bc.sha256_text(path.read_text()), snapshot_path=str(path)))
                    st.rerun()
            else:
                st.caption("No snapshot files found in research/snapshots/.")

    cols = st.session_state[K_COLUMNS]
    if not cols:
        st.info("No columns yet — add at least one under **2 · Configurations**.")
        return
    if not selected:
        st.info("No cyclones selected — pick some under **1 · Cyclones**.")
        return

    # ── column headers ────────────────────────────────────────────────────────
    st.divider()
    specs: list[bc.ColumnSpec] = []
    header_cols = st.columns(len(cols))
    for i, col in enumerate(cols):
        with header_cols[i]:
            spec = _spec(col)
            specs.append(spec)
            _render_header(col, spec)
            if col["origin"] != "snapshot":
                with st.expander("Edit", expanded=False):
                    new_text = st.text_area(
                        "config (YAML)", value=col["yaml_text"], height=200,
                        key=f"bench_edit_{col['cid']}",
                        label_visibility="collapsed")
                    if st.button("Apply", key=f"bench_apply_{col['cid']}"):
                        try:
                            bc.load_config_text(new_text)
                        except Exception as exc:
                            st.error(f"Invalid YAML: {exc}")
                        else:
                            if new_text != col["yaml_text"]:
                                col["yaml_text"] = new_text
                                col["edited"] = True
                            st.rerun()
            if st.button("Remove", key=f"bench_del_{col['cid']}"):
                st.session_state[K_COLUMNS] = [
                    c for c in st.session_state[K_COLUMNS] if c["cid"] != col["cid"]]
                st.rerun()

    # ── run ───────────────────────────────────────────────────────────────────
    runner = bc.ColumnRunner()
    series_sel = {s: series_all[s] for s in selected}
    results = [runner.run(spec, series_sel) for spec in specs]

    # Published as ordinary app state, in column order, so what each column
    # actually computed is inspectable without reaching into Streamlit
    # internals — `tests/test_benchmark_apptest.py` asserts on this and on
    # nothing private. It is a digest (phase runs per series), not the figures.
    st.session_state["bench_last_results"] = [
        {"name": col["name"],
         "config_sha256": spec.effective_sha256(),
         "series": {sid: (None if res["error"] else
                          [[p, a, b] for p, a, b in res["runs"]])
                    for sid, res in per_col.items()},
         "errors": {sid: res["error"] for sid, res in per_col.items()
                    if res["error"]}}
        for col, spec, per_col in zip(cols, specs, results)
    ]

    # ── summary ───────────────────────────────────────────────────────────────
    st.divider()
    metrics = [bc.metrics_by_split(r, labels, selected, membership) for r in results]
    _render_summary(metrics, [c["name"] for c in cols])

    # ── aligned grid ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Per cyclone")
    _legend()
    show_labels = st.session_state[K_LABELS]
    for sid in selected:
        st.markdown(f"**{sid}** · {source_of[sid]} · {membership.get(sid, '—')} split")
        values = tuple(float(x) for x in series_all[sid].values)
        row = st.columns(len(cols) + (1 if show_labels else 0))
        off = 0
        if show_labels:
            with row[0]:
                rec = labels.get(sid)
                if rec is None:
                    st.caption("no manual label")
                else:
                    runs = bc.label_runs_for(rec)
                    st.image(_cell_png(values, tuple(runs), "manual label"),
                             use_container_width=True)
            off = 1
        for i, col in enumerate(cols):
            with row[i + off]:
                res = results[i][sid]
                if res["error"]:
                    st.error(res["error"])
                    continue
                st.image(_cell_png(values, tuple(res["runs"]), col["name"]),
                         use_container_width=True)
                rec = labels.get(sid)
                if rec is not None:
                    seq_ok = ([p for p, _ in res["starts"]]
                              == [bc.normalize_phase(p["phase"])
                                  for p in rec["phases"]])
                    st.caption(f"sequence: {'match' if seq_ok else 'differs'}")
                    mm = bc.mature_metrics({sid: res}, labels, [sid])
                    if mm["rows"]:
                        r = mm["rows"][0]
                        if r["d_start"] is None:
                            st.caption("mature: no pair")
                        else:
                            st.caption(
                                f"mature Δ={r['d_start']:+d}/{r['d_end']:+d} "
                                f"({'within' if r['hit'] else 'outside'} "
                                f"{bc.MATURE_MARGIN})")
        st.divider()
