"""The Benchmark tab — N configurations over the same cyclones, aligned in columns.

All logic lives in `benchmark_core`; this file is the Streamlit surface over it.
See that module's docstring for the three structural rules (code commit as
provenance, `bad_cases_count` never a score, `item19_core.CONFIG` never
repointed) and for the leakage rule on aggregates.

Reading order
-------------
A fixed status line, then four numbered sections: **1 Mode → 2 Data →
3 Configurations → 4 Results**. Each section owns everything it governs — in
particular the configuration cards render INSIDE section 3, so collapsing the
section hides them. (They used to render below it, which made the collapse do
nothing visible and left orphaned cards on screen.)

Mode is not independent state
-----------------------------
`Validation` and `Exploration` filter what is SELECTABLE and what is emphasised.
They do **not** decide whether a number is produced: that is decided per row by
the existence of a manual label for that cyclone, in `benchmark_core.scoreable`.
A row without a label yields no scoring number in either mode. All 63 bundled
records are labelled, so the unlabelled case arrives through Exploration's
cyclone upload.

Without ground truth, Exploration measures each column against the **reference
column** (section 3) rather than against truth, and every such number is labelled
`relative to reference` — it is a distance, never an accuracy.

Nothing recomputes on edit
--------------------------
Results are produced by an explicit **Run**. A fingerprint of (columns ×
selection × reference) is stored with them; when it stops matching, the results
are flagged out of date rather than silently recomputed, so a half-edited
configuration never quietly replaces the numbers being read.

Layout decisions worth stating
------------------------------
* **A column is edited as YAML text.** A full widget tree per column multiplies
  every sidebar control by the number of columns, and the point of this tab is to
  hold several configurations on screen at once.
* **A card shows only the parameters that DIFFER from the reference.** The eleven
  YAMLs share ~15 identical parameters; listing all of them hides the two or
  three that separate one configuration from another. The full config sits behind
  a drop-down.
* **Column state lives in explicit `st.session_state` entries**, not widget-key
  memory: a widget with a stable key loses its value across an `st.rerun()`
  issued earlier in the same script run, which this tab does on every add/remove.
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

MODES = ["Validation", "Exploration"]
FIGURE_LAYOUTS = ["Side by side", "Stacked"]

# session_state keys — explicit, see the module docstring
K_COLUMNS = "bench_columns"
K_IDS = "bench_selected_ids"
K_LABELS = "bench_show_labels"
K_NEXT_ID = "bench_next_id"
K_MODE = "bench_mode"
K_REFERENCE = "bench_reference"
K_FIGLAYOUT = "bench_figure_layout"
K_EXTRA = "bench_extra_series"          # uploaded, unlabelled cyclones
K_RESULTS = "bench_last_results"
K_FINGERPRINT = "bench_results_fingerprint"
K_SCORE_LABELLED = "bench_score_labelled_subset"

REFERENCE_MANUAL = "Manual label"


# ── state ─────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    st.session_state.setdefault(K_COLUMNS, [])
    st.session_state.setdefault(K_IDS, [])
    st.session_state.setdefault(K_LABELS, False)
    st.session_state.setdefault(K_NEXT_ID, 1)
    st.session_state.setdefault(K_MODE, "Validation")
    st.session_state.setdefault(K_REFERENCE, None)
    st.session_state.setdefault(K_FIGLAYOUT, "Side by side")
    st.session_state.setdefault(K_EXTRA, {})
    st.session_state.setdefault(K_SCORE_LABELLED, False)


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
    """The sidebar's live state as a config document, published by app.py."""
    return st.session_state.get("_bench_live_config") or {
        "filter_params": {}, "phase_params": {}}


def _fingerprint(cols, ids, reference) -> str:
    """Identity of a run: the configs, the selection and the reference."""
    parts = [str(reference), "|".join(sorted(ids))]
    for c in cols:
        parts.append(f"{c['cid']}:{c['name']}:{bc.sha256_text(c['yaml_text'])}"
                     f":{c.get('snapshot_path') or ''}")
    return bc.sha256_text("||".join(parts))


# ── figures ───────────────────────────────────────────────────────────────────
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


@st.cache_data(show_spinner=False, max_entries=256)
def _stacked_png(values_tuple: tuple, panels: tuple) -> bytes:
    """All columns stacked vertically on a SHARED x axis and a shared y scale.

    The point of this arrangement is that a boundary that moved between two
    configurations is read straight down the figure. That only works if the two
    axes are actually the same, so `sharex=True` and one y range for every panel
    are the arrangement, not decoration.
    """
    matplotlib.use("Agg")
    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(7.2, 1.35 * n + 0.4),
                             sharex=True, sharey=True, squeeze=False)
    lo, hi = min(values_tuple), max(values_tuple)
    pad = 0.05 * (hi - lo or 1.0)
    for ax, (title, runs) in zip(axes[:, 0], panels):
        ax.plot(range(len(values_tuple)), values_tuple, color="k", lw=1.0)
        for phase, a, b in runs:
            ax.axvspan(a, b + 0.999, color=PHASE_COLORS.get(phase, "white"),
                       alpha=0.45, lw=0)
        ax.set_ylabel(title, fontsize=7, rotation=0, ha="right", va="center")
        ax.tick_params(labelsize=6)
        ax.set_ylim(lo - pad, hi + pad)
    axes[-1, 0].set_xlim(0, max(1, len(values_tuple) - 1))
    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110)
    plt.close(fig)
    return buf.getvalue()


def _legend() -> None:
    """Phase colour key, rendered next to the figures it explains."""
    st.markdown(
        "<div style='margin:2px 0 6px 0'>"
        + " ".join(
            f"<span style='background:{c};padding:2px 9px;border-radius:3px;"
            f"font-size:11px;color:#111;margin-right:4px'>{p}</span>"
            for p, c in PHASE_COLORS.items())
        + "</div>",
        unsafe_allow_html=True)


# ── column card ───────────────────────────────────────────────────────────────
def _short(sha: str) -> str:
    return sha[:12] if sha and len(sha) == 64 else (sha or "—")


def _render_card(col: dict, spec: bc.ColumnSpec, ref_doc: dict,
                 ref_name: str) -> None:
    """One collapsed configuration card: name, short hash, what DIFFERS."""
    h = spec.header()
    sha = h["config_sha256"]
    sha_txt = sha if sha == "edited in session" else _short(sha)
    commit = h["code_commit"]
    commit_txt = commit[:12] if len(commit) == 40 else commit

    st.markdown(f"**{col['name']}**")
    st.caption(f"`{sha_txt}` · code `{commit_txt}`")

    if h["pre_filter_fix"]:
        st.warning(h.get("pre_filter_fix_short") or h["pre_filter_fix_warning"],
                   icon="⚠️")

    if spec.snapshot is not None:
        st.caption("Frozen published wheel — no parameters of its own to diff.")
    else:
        diffs = bc.config_differences(spec.doc, ref_doc)
        if not diffs:
            st.caption(f"No parameter differs from **{ref_name}**.")
        else:
            st.caption(f"Differs from **{ref_name}** in {len(diffs)} parameter(s):")
            st.dataframe(
                pd.DataFrame(
                    {"this column": {k: repr(v[0]) for k, v in diffs.items()},
                     ref_name: {k: repr(v[1]) for k, v in diffs.items()}}),
                use_container_width=True)

    n_extra = len(h["ignored"]) + len(h["defaulted"])
    with st.expander(f"Provenance ({n_extra} note(s))" if n_extra else "Provenance",
                     expanded=False):
        st.caption(f"**1 · source YAML sha256** — `{sha_txt}`")
        st.caption(f"**2 · running code commit** — `{commit_txt}`",
                   help="The commit of the code actually running. NOT "
                        "`metadata.cyclophaser_version`, which reads 2.0.0 in "
                        "every one of the eleven files and so distinguishes "
                        "nothing.")
        st.caption("**3 · keys ignored by the current signature** — "
                   + (", ".join(f"`{k}`" for k in h["ignored"]) if h["ignored"]
                      else "none"))
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
            st.caption("**Historical annotation — not a score**",
                       help="These marks were made in different weeks with "
                            "different knowledge of the problem (params-5 and "
                            "-6 record 0, params-9 records 6). Comparing two of "
                            "them compares two inspections, not two "
                            "configurations, so `evaluation.bad_cases_count` is "
                            "never used as a score in this tab.")
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

        st.divider()
        st.caption("**Full configuration**")
        st.code(col["yaml_text"] or "(frozen snapshot — no YAML)", language="yaml")

    if col["origin"] != "snapshot":
        with st.expander("Edit", expanded=False):
            new_text = st.text_area(
                "config (YAML)", value=col["yaml_text"], height=200,
                key=f"bench_edit_{col['cid']}", label_visibility="collapsed")
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


# ── scoring panel ─────────────────────────────────────────────────────────────
def _pct(x) -> str:
    return "—" if x is None else f"{100 * x:.0f}%"


def _summary_frame(metrics_per_column, names, split) -> pd.DataFrame:
    data: dict[str, dict[str, str]] = {}
    for name, m in zip(names, metrics_per_column):
        blk = m[split]
        seq, mat = blk["sequence"], blk["mature"]
        n_series = seq.get("n_series") or 0
        data[name] = {
            "Series scored": str(n_series),
            "Sequence match": f"{seq['n_sequence_match']}/{n_series}" if n_series else "—",
            "Sequence match rate": _pct(seq["sequence_match_rate"]) if n_series else "—",
            "Boundaries within margin": (f"{seq['n_boundaries_hit']}/{seq['n_boundaries']}"
                                         if seq.get("n_boundaries") else "—"),
            "Boundary hit rate": (_pct(seq.get("boundary_hit_rate"))
                                  if seq.get("n_boundaries") else "—"),
            "Mature paired": f"{mat['n_hit']}/{mat['n']}" if mat["n"] else "—",
            "Mature hit rate": _pct(mat["hit_rate"]) if mat["n"] else "—",
        }
    return pd.DataFrame(data)


def _render_scoring(metrics, names, n_unscored: int) -> None:
    train_n = len(metrics[0]["train"]["ids"]) if metrics else 0
    test_n = len(metrics[0]["test"]["ids"]) if metrics else 0

    st.markdown("**Scored against the manual labels**")
    if n_unscored:
        st.caption(f"{n_unscored} selected cyclone(s) carry no manual label and "
                   "are excluded from every number below.")

    with st.expander(f"Train split — {train_n} series", expanded=True):
        if train_n:
            st.dataframe(_summary_frame(metrics, names, "train"),
                         use_container_width=True)
            st.caption(
                "Sequence rows and mature rows come from two different "
                "instruments and are never summed.",
                help=f"Sequence rows · {bc.SEQUENCE_INSTRUMENT} — starts only, "
                     "each boundary against its own tolerance_idx, and it "
                     "refuses to pair boundaries at all when the sequence does "
                     f"not match.\n\nMature rows · {bc.MATURE_INSTRUMENT} — "
                     "largest-overlap block, both ends, fixed margin.")
        else:
            st.caption("No train-split cyclone in the current selection.")

    with st.expander(f"Test split (frozen) — {test_n} series", expanded=False):
        if test_n:
            st.caption(
                "Frozen test split — shown on request, never combined with the "
                "train numbers.",
                help="Leakage rule: every aggregate is computed over the train "
                     "split. Aggregates involving the 16 real cyclones of the "
                     "frozen test split live in this block alone and are never "
                     "added into the train one.")
            st.dataframe(_summary_frame(metrics, names, "test"),
                         use_container_width=True)
        else:
            st.caption("No test-split cyclone in the current selection.")


def _render_reference_metrics(results, names, ref_results, ids,
                              ref_name: str) -> None:
    """Exploration's four measures — distances from the reference, not accuracy."""
    st.markdown(f"**Relative to reference — `{ref_name}`**",
                help="There is no ground truth on this path. Every number here "
                     "is a DISTANCE from the reference column, never a hit rate "
                     "and never an accuracy. The reference compared against "
                     "itself is all zeros, which is the correct reading.")
    data: dict[str, dict[str, str]] = {}
    for name, res in zip(names, results):
        m = bc.reference_metrics(res, ref_results, ids)
        def _fmt_counts(d):
            return ", ".join(f"{k} +{v}" for k, v in sorted(d.items())) or "—"
        data[name] = {
            "Cyclones compared": str(m["n_compared"]),
            "Sequence changed": str(m["n_sequence_changed"]),
            "Boundary shift, median (steps)": ("—" if m["shift_median"] is None
                                               else f"{m['shift_median']:.1f}"),
            "Boundary shift, max (steps)": ("—" if m["shift_max"] is None
                                            else str(m["shift_max"])),
            "Phases appeared": _fmt_counts(m["appeared"]),
            "Phases disappeared": _fmt_counts(m["disappeared"]),
            "Refused incipient": str(m["n_refused_incipient"]),
        }
    st.dataframe(pd.DataFrame(data), use_container_width=True)
    st.caption("Boundary shift is measured only on cyclones whose phase "
               "sequence matches the reference — pairing boundaries across a "
               "sequence mismatch would compare two different transitions.")


# ── the tab ───────────────────────────────────────────────────────────────────
def render() -> None:
    _init_state()

    series_bundled, source_of = bc.load_all_series()
    extra = st.session_state[K_EXTRA]
    series_all = {**series_bundled,
                  **{k: pd.Series(v) for k, v in extra.items()}}
    for k in extra:
        source_of[k] = "uploaded"
    membership = bc.split_membership()
    labels = bc.labels_for_display()

    mode = st.session_state[K_MODE]
    cols = st.session_state[K_COLUMNS]
    selected = [s for s in st.session_state[K_IDS] if s in series_all]
    st.session_state[K_IDS] = selected

    # ── status bar ────────────────────────────────────────────────────────────
    ref_name = st.session_state[K_REFERENCE] or "—"
    n_lab = len(bc.scoreable(selected, labels))
    gt_badge = (f"ground truth: available ({n_lab}/{len(selected)})" if n_lab
                else "ground truth: absent")
    st.markdown(
        f"`{mode}`  ·  **{len(cols)}** config(s)  ·  **{len(selected)}** "
        f"cyclone(s)  ·  {gt_badge}  ·  reference: **{ref_name}**")
    st.divider()

    # ── 1 · Mode ──────────────────────────────────────────────────────────────
    with st.expander("1 · Mode", expanded=True):
        st.radio(
            "Mode", options=MODES, key=K_MODE, horizontal=True,
            label_visibility="collapsed",
            help="**Validation** — only labelled sources are selectable (the 51 "
                 "real tracks and the 12 frozen synthetic cases), and the "
                 "scoring panel is shown.\n\n**Exploration** — every source is "
                 "selectable, uploads included; the scoring panel is collapsed "
                 "and columns are measured against the reference column "
                 "instead.\n\nMode does not decide whether a number is "
                 "produced: that is decided per cyclone by whether it carries a "
                 "manual label.")
        mode = st.session_state[K_MODE]
        if mode == "Validation":
            st.caption("Labelled sources only. Scoring panel visible.")
        else:
            st.caption("All sources selectable, uploads included. Scoring panel "
                       "collapsed; unlabelled rows are never scored.")

    # ── 2 · Data ──────────────────────────────────────────────────────────────
    selectable = ([s for s in series_bundled] if mode == "Validation"
                  else list(series_all))
    selectable = sorted(selectable, key=lambda s: (source_of[s], s))
    # Validation offers labelled sources only, so an uploaded track selected in
    # Exploration is dropped from the selection when the mode changes rather
    # than being carried along invisibly into a run that claims to be scored.
    dropped = [s for s in selected if s not in selectable]
    if dropped:
        selected = [s for s in selected if s in selectable]
        st.session_state[K_IDS] = selected

    n_real = sum(1 for s in selected if source_of.get(s) == "real")
    n_syn = sum(1 for s in selected if source_of.get(s) == "synthetic")
    n_up = sum(1 for s in selected if source_of.get(s) == "uploaded")
    parts = [f"{n_real} real", f"{n_syn} synthetic"] + ([f"{n_up} uploaded"]
                                                        if n_up else [])
    with st.expander(f"2 · Data — {len(selected)} selected", expanded=True):
        st.caption(f"**{len(selected)} selected** — {', '.join(parts)}")
        if dropped:
            st.info(f"{len(dropped)} unlabelled track(s) dropped from the "
                    "selection: Validation mode offers labelled sources only.")

        def _set(ids):
            st.session_state[K_IDS] = [s for s in ids if s in selectable]

        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1:
            if st.button("All real", key="bench_pick_real", use_container_width=True):
                _set([s for s in selectable if source_of[s] == "real"])
        with s2:
            if st.button("All synthetic", key="bench_pick_synth",
                         use_container_width=True):
                _set([s for s in selectable if source_of[s] == "synthetic"])
        with s3:
            if st.button("Train", key="bench_pick_train", use_container_width=True):
                _set([s for s in selectable if membership.get(s) == "train"])
        with s4:
            if st.button("Test", key="bench_pick_test", use_container_width=True):
                _set([s for s in selectable if membership.get(s) == "test"])
        with s5:
            if st.button("Invert", key="bench_pick_invert", use_container_width=True):
                _set([s for s in selectable if s not in selected])
        with s6:
            if st.button("Clear", key="bench_pick_none", use_container_width=True):
                st.session_state[K_IDS] = []

        with st.expander("Choose individually", expanded=False):
            picked = st.multiselect(
                "Any subset of the available records. Not tied to the "
                "train/test split.",
                options=selectable,
                default=[s for s in selected if s in selectable],
                key="bench_ids_widget",
                format_func=lambda s: (f"{s} ({source_of[s]}/"
                                       f"{membership.get(s, 'unlabelled')})"),
            )
            if picked != [s for s in selected if s in selectable]:
                st.session_state[K_IDS] = list(picked)
                selected = list(picked)

        if mode == "Exploration":
            up = st.file_uploader(
                "Add cyclone CSV(s) — ';'-delimited, column 'min_max_zeta_850'",
                type=["csv"], accept_multiple_files=True, key="bench_data_upload",
                help="Uploaded tracks carry no manual label, so they can be "
                     "compared against the reference column but are never "
                     "scored.")
            if up:
                for f in up:
                    name = Path(f.name).stem
                    if name in st.session_state[K_EXTRA]:
                        continue
                    try:
                        ser = bc.parse_cyclone_csv(f.getvalue())
                    except Exception as exc:
                        st.error(f"{f.name}: {exc}")
                        continue
                    st.session_state[K_EXTRA][name] = list(ser.values)
                    st.session_state[K_IDS] = list(st.session_state[K_IDS]) + [name]
                    st.rerun()

        st.checkbox(
            "Show manual labels as a first column", key=K_LABELS,
            help="Opt-in. Draws the human label beside the first column, for "
                 "the records that carry one.")

    # ── 3 · Configurations ────────────────────────────────────────────────────
    with st.expander(f"3 · Configurations — {len(cols)} column(s)", expanded=True):
        st.caption(
            f"Each column runs the whole detector over every selected cyclone: "
            f"{len(cols)} × {len(selected)} = {len(cols) * len(selected)} run(s), "
            "cached per config × cyclone pair.")

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
            pick = st.selectbox("research/labels/configs/",
                                options=["—"] + [p.name for p in cfgs],
                                key="bench_pick_config")
            if st.button("Add column from the selected file", key="bench_add_config",
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
            upy = st.file_uploader("Upload a configuration", type=["yaml", "yml"],
                                   key="bench_upload", label_visibility="collapsed")
            if upy is not None:
                text = upy.getvalue().decode("utf-8")
                sha = bc.sha256_text(text)
                if st.session_state.get("_bench_upload_sha") != sha:
                    try:
                        st.session_state[K_COLUMNS].append(_new_column(
                            Path(upy.name).stem, bc.load_config_text(text),
                            "upload", upy.name, sha))
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
                st.caption("No snapshot files in research/snapshots/.")

        cols = st.session_state[K_COLUMNS]

        # reference column selector
        st.divider()
        ref_options = ([REFERENCE_MANUAL] if labels else []) + [c["name"] for c in cols]
        if st.session_state[K_REFERENCE] not in ref_options:
            st.session_state[K_REFERENCE] = ref_options[0] if ref_options else None
        if ref_options:
            st.selectbox(
                "Reference column", options=ref_options, key=K_REFERENCE,
                help="Every diff on a card and every `relative to reference` "
                     "number is computed against this. Defaults to the manual "
                     "label when one exists, otherwise the first configuration "
                     "column.")
        ref_name = st.session_state[K_REFERENCE] or "—"

        # the parameter baseline for the cards: the manual label has no config,
        # so parameter diffs fall back to the first configuration column.
        cfg_cols = [c for c in cols if c["origin"] != "snapshot"]
        if ref_name != REFERENCE_MANUAL:
            base_col = next((c for c in cols if c["name"] == ref_name), None)
        else:
            base_col = cfg_cols[0] if cfg_cols else None
        base_doc = {}
        base_label = ref_name
        if base_col is not None:
            try:
                base_doc = bc.load_config_text(base_col["yaml_text"])
            except Exception:
                base_doc = {}
            base_label = base_col["name"]
        if ref_name == REFERENCE_MANUAL and base_col is not None:
            st.caption(f"The manual label has no parameters, so card diffs use "
                       f"**{base_label}** as the parameter baseline.")

        # ── the cards, INSIDE this section ────────────────────────────────────
        if cols:
            st.divider()
            specs = [_spec(c) for c in cols]
            card_cols = st.columns(len(cols))
            for i, col in enumerate(cols):
                with card_cols[i]:
                    _render_card(col, specs[i], base_doc, base_label)
        else:
            specs = []
            st.info("No columns yet — add at least one above.")

        # ── run ───────────────────────────────────────────────────────────────
        st.divider()
        fp = _fingerprint(cols, selected, ref_name)
        stale = (K_RESULTS in st.session_state
                 and st.session_state.get(K_FINGERPRINT) != fp)
        r1, r2 = st.columns([1, 3])
        with r1:
            run_clicked = st.button("Run", key="bench_run", type="primary",
                                    use_container_width=True,
                                    disabled=not (cols and selected))
        with r2:
            if stale:
                st.warning("Results out of date — configuration or selection "
                           "changed since the last run.", icon="⚠️")
            elif K_RESULTS not in st.session_state:
                st.caption("Nothing has been run yet. Nothing recomputes on "
                           "edit; press **Run**.")

    # ── run, only on demand ───────────────────────────────────────────────────
    if run_clicked:
        runner = bc.ColumnRunner()
        series_sel = {s: series_all[s] for s in selected}
        results = [runner.run(spec, series_sel) for spec in specs]
        st.session_state[K_RESULTS] = [
            {"name": col["name"],
             "config_sha256": spec.effective_sha256(),
             "series": {sid: (None if res["error"] else
                              [[p, a, b] for p, a, b in res["runs"]])
                        for sid, res in per_col.items()},
             "errors": {sid: res["error"] for sid, res in per_col.items()
                        if res["error"]}}
            for col, spec, per_col in zip(cols, specs, results)]
        st.session_state[K_FINGERPRINT] = fp
        st.session_state["_bench_runs"] = results
        st.session_state["_bench_run_ids"] = list(selected)
        st.session_state["_bench_run_names"] = [c["name"] for c in cols]
        # Section 3's run/staleness message is rendered ABOVE this point, so on
        # the click's own pass it still describes the pre-run state while
        # section 4 already shows results. Re-render once so the whole page
        # agrees; the results are in session_state, so nothing is recomputed.
        st.rerun()

    # ── 4 · Results ───────────────────────────────────────────────────────────
    results = st.session_state.get("_bench_runs")
    run_ids = st.session_state.get("_bench_run_ids", [])
    names = st.session_state.get("_bench_run_names", [])
    with st.expander("4 · Results", expanded=True):
        if not results:
            st.info("No results yet — press **Run** in section 3.")
            return

        scored_ids = bc.scoreable(run_ids, labels)
        n_unscored = len(run_ids) - len(scored_ids)
        metrics = [bc.metrics_by_split(r, labels, run_ids, membership)
                   for r in results]

        if mode == "Validation":
            _render_scoring(metrics, names, n_unscored)
        else:
            if scored_ids:
                st.caption(
                    f"{len(scored_ids)} of the {len(run_ids)} selected cyclone(s) "
                    "carry a manual label.")
                st.checkbox(
                    "Also score the labelled rows", key=K_SCORE_LABELLED,
                    help="Scores ONLY the labelled rows. The unlabelled ones "
                         "stay out of every number.")
            with st.expander("Scored against the manual labels", expanded=False):
                if scored_ids and st.session_state[K_SCORE_LABELLED]:
                    _render_scoring(metrics, names, n_unscored)
                elif scored_ids:
                    st.caption("Switch on **Also score the labelled rows** above.")
                else:
                    st.caption("No selected cyclone carries a manual label, so "
                               "there is nothing to score.")

        # reference-relative metrics
        ref_results = None
        if ref_name == REFERENCE_MANUAL:
            ref_results = {sid: {"runs": bc.label_runs_for(labels[sid])}
                           for sid in run_ids if sid in labels}
        else:
            for nm, res in zip(names, results):
                if nm == ref_name:
                    ref_results = res
                    break
        if ref_results is not None:
            st.divider()
            _render_reference_metrics(results, names, ref_results, run_ids,
                                      ref_name)

        # ── per cyclone ───────────────────────────────────────────────────────
        st.divider()
        h1, h2 = st.columns([2, 1])
        with h1:
            st.markdown("**Per cyclone**")
        with h2:
            st.radio("Figure layout", options=FIGURE_LAYOUTS, key=K_FIGLAYOUT,
                     horizontal=True, label_visibility="collapsed",
                     help="Same data either way. **Stacked** puts the panels on "
                          "a shared x axis and a shared y scale, so a boundary "
                          "that moved is read straight down the figure.")
        _legend()
        show_labels = st.session_state[K_LABELS]
        stacked = st.session_state[K_FIGLAYOUT] == "Stacked"

        for sid in run_ids:
            st.markdown(f"**{sid}** · {source_of.get(sid, '—')} · "
                        f"{membership.get(sid, 'unlabelled')}")
            values = tuple(float(x) for x in series_all[sid].values)
            rec = labels.get(sid)

            if stacked:
                panels = []
                if show_labels and rec is not None:
                    panels.append(("manual label", tuple(bc.label_runs_for(rec))))
                for i, nm in enumerate(names):
                    res = results[i][sid]
                    if not res["error"]:
                        panels.append((nm, tuple(res["runs"])))
                if panels:
                    st.image(_stacked_png(values, tuple(panels)),
                             use_container_width=True)
                for i, nm in enumerate(names):
                    if results[i][sid]["error"]:
                        st.error(f"{nm}: {results[i][sid]['error']}")
                _render_row_notes(results, names, sid, rec, labels)
            else:
                row = st.columns(len(names) + (1 if show_labels else 0))
                off = 0
                if show_labels:
                    with row[0]:
                        if rec is None:
                            st.caption("no manual label")
                        else:
                            st.image(_cell_png(values,
                                               tuple(bc.label_runs_for(rec)),
                                               "manual label"),
                                     use_container_width=True)
                    off = 1
                for i, nm in enumerate(names):
                    with row[i + off]:
                        res = results[i][sid]
                        if res["error"]:
                            st.error(res["error"])
                            continue
                        st.image(_cell_png(values, tuple(res["runs"]), nm),
                                 use_container_width=True)
                        _render_cell_notes(res, sid, rec, labels)
            st.divider()


def _mature_note(res, sid, labels) -> str | None:
    mm = bc.mature_metrics({sid: res}, labels, [sid])
    if not mm["rows"]:
        return None
    r = mm["rows"][0]
    if r["d_start"] is None:
        return "mature: no pair"
    return (f"mature start {r['d_start']:+d} steps, end {r['d_end']:+d} steps "
            f"(margin {bc.MATURE_MARGIN})")


def _render_cell_notes(res, sid, rec, labels) -> None:
    """Per-cell notes. Only ever drawn for a cyclone that HAS a label."""
    if rec is None:
        st.caption("unlabelled — not scored")
        return
    seq_ok = ([p for p, _ in res["starts"]]
              == [bc.normalize_phase(p["phase"]) for p in rec["phases"]])
    st.caption(f"sequence: {'match' if seq_ok else 'differs'}")
    note = _mature_note(res, sid, labels)
    if note:
        st.caption(note)


def _render_row_notes(results, names, sid, rec, labels) -> None:
    if rec is None:
        st.caption("unlabelled — not scored")
        return
    bits = []
    for i, nm in enumerate(names):
        res = results[i][sid]
        if res["error"]:
            continue
        seq_ok = ([p for p, _ in res["starts"]]
                  == [bc.normalize_phase(p["phase"]) for p in rec["phases"]])
        note = _mature_note(res, sid, labels) or ""
        bits.append(f"**{nm}** — sequence: {'match' if seq_ok else 'differs'}"
                    + (f"; {note}" if note else ""))
    for b in bits:
        st.caption(b)
