"""The Benchmark tab — N configurations over the same cyclones, aligned in columns.

All logic lives in `benchmark_core`; this file is the Streamlit surface over it.
See that module's docstring for the three structural rules (code commit as
provenance, `bad_cases_count` never a score, `item19_core.CONFIG` never
repointed) and for the leakage rule on aggregates.

Two interface choices worth stating, because they were decisions rather than
defaults:

* **A column is edited as YAML text.** The alternative — a full widget tree per
  column — multiplies every sidebar control by the number of columns, and the
  point of this tab is to hold several configurations on screen at once. A text
  area also keeps "what is this column running" answerable by reading one thing,
  which is the property the header exists to guarantee.
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
    st.markdown(
        " ".join(
            f"<span style='background:{c};padding:1px 7px;border-radius:3px;"
            f"font-size:11px;color:#111'>{p}</span>"
            for p, c in PHASE_COLORS.items()),
        unsafe_allow_html=True)


# ── header rendering ──────────────────────────────────────────────────────────
def _render_header(col: dict, spec: bc.ColumnSpec) -> None:
    h = spec.header()
    st.markdown(f"**{col['name']}**")
    st.caption(f"1 · sha256 do YAML: `{h['config_sha256_display']}`")
    st.caption(f"2 · commit do código: `{h['code_commit'][:12] if len(h['code_commit']) == 40 else h['code_commit']}`")

    if h["ignored"]:
        st.caption("3 · chaves ignoradas pela assinatura atual: "
                   + ", ".join(f"`{k}`" for k in h["ignored"]))
    else:
        st.caption("3 · chaves ignoradas: nenhuma")

    if h["defaulted"]:
        with st.expander(f"4 · {len(h['defaulted'])} chave(s) no default atual",
                         expanded=False):
            for k, v in h["defaulted"].items():
                st.caption(f"`{k}` = `{v!r}`")
    else:
        st.caption("4 · nenhuma chave ausente")

    if h["pre_filter_fix"]:
        st.warning(h["pre_filter_fix_warning"], icon="⚠️")

    if h.get("historical"):
        hist = h["historical"]
        with st.expander("anotação histórica (NÃO é métrica)", expanded=False):
            st.caption(hist["note"])
            st.caption(f"`evaluation.bad_cases_count` = {hist['bad_cases_count']} "
                       f"de {hist['total_cyclones']} — {hist['timestamp']}")
            if hist["bad_cases"]:
                st.caption(", ".join(str(b) for b in hist["bad_cases"]))

    if h.get("frozen_snapshot"):
        snap = h["frozen_snapshot"]
        with st.expander("snapshot congelado", expanded=False):
            st.caption(f"{snap['label']}")
            st.caption(f"gerado {snap['generated']} · python {snap['python']}")
            st.caption(f"parâmetros: {snap['parameters']}")


def _render_metrics(block: dict, kind: str) -> None:
    """Both measurements, each named by its instrument. Never blended."""
    seq, mat = block["sequence"], block["mature"]
    st.caption(f"**{kind}** — {len(block['ids'])} série(s)")
    st.caption(f"_sequência_ · {seq['instrument']}")
    if seq.get("n_series"):
        rate = seq["sequence_match_rate"]
        st.caption(f"  sequência: {seq['n_sequence_match']}/{seq['n_series']}"
                   + (f" ({100 * rate:.0f}%)" if rate is not None else ""))
        br = seq.get("boundary_hit_rate")
        st.caption(f"  fronteiras: {seq['n_boundaries_hit']}/{seq['n_boundaries']}"
                   + (f" ({100 * br:.0f}%)" if br is not None else ""))
    else:
        st.caption("  — sem rótulos nesta seleção")
    st.caption(f"_maduro_ · {mat['instrument']}")
    if mat["n"]:
        st.caption(f"  pareado: {mat['n_hit']}/{mat['n']}"
                   + (f" ({100 * mat['hit_rate']:.0f}%)"
                      if mat["hit_rate"] is not None else ""))
    else:
        st.caption("  — sem rótulo de maduro nesta seleção")


# ── the tab ───────────────────────────────────────────────────────────────────
def render() -> None:
    _init_state()
    st.subheader("Benchmark — N configurações sobre os mesmos ciclones")
    st.caption(
        "Cada coluna é uma configuração independente, rodada sobre os ciclones "
        "escolhidos abaixo e alinhada por ciclone. Os dois medidores aparecem "
        "sempre, cada um com o nome do instrumento que o produziu — são "
        "instrumentos diferentes e não são somados. "
        "`evaluation.bad_cases_count` do YAML nunca é usado como placar: aparece "
        "apenas como anotação histórica rotulada."
    )

    series_all, source_of = bc.load_all_series()
    membership = bc.split_membership()
    labels = bc.labels_for_display()

    # ── cyclone selection ─────────────────────────────────────────────────────
    ids_sorted = sorted(series_all, key=lambda s: (source_of[s], s))
    with st.expander("Ciclones", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Todos os reais (51)", key="bench_pick_real",
                         use_container_width=True):
                st.session_state[K_IDS] = [s for s in ids_sorted
                                           if source_of[s] == "real"]
        with c2:
            if st.button("Todos os sintéticos (12)", key="bench_pick_synth",
                         use_container_width=True):
                st.session_state[K_IDS] = [s for s in ids_sorted
                                           if source_of[s] == "synthetic"]
        with c3:
            if st.button("Limpar", key="bench_pick_none",
                         use_container_width=True):
                st.session_state[K_IDS] = []
        selected = st.multiselect(
            "Seleção livre — qualquer subconjunto dos 63 registros "
            "(51 reais + 12 sintéticos). Sem vínculo com o split treino/teste.",
            options=ids_sorted,
            default=st.session_state[K_IDS],
            key="bench_ids_widget",
            format_func=lambda s: f"{s} ({source_of[s]}/{membership.get(s, '—')})",
        )
        st.session_state[K_IDS] = list(selected)

        st.checkbox(
            "Mostrar rótulos manuais na primeira coluna", key=K_LABELS,
            help="Opt-in. Desenha o rótulo humano ao lado da primeira coluna, "
                 "sobre os 63 registros que têm rótulo.",
        )

    # ── column management ─────────────────────────────────────────────────────
    with st.expander("Colunas", expanded=True):
        st.caption(
            "⚠️ **Custo:** cada coluna roda o detector inteiro sobre cada "
            f"ciclone selecionado. Agora: {len(st.session_state[K_COLUMNS])} "
            f"coluna(s) × {len(selected)} ciclone(s) = "
            f"{len(st.session_state[K_COLUMNS]) * len(selected)} execuções "
            "(cacheadas por par config×ciclone)."
        )
        a1, a2 = st.columns(2)
        with a1:
            if st.button("+ coluna do estado atual da sidebar",
                         key="bench_add_sidebar", use_container_width=True):
                doc = _sidebar_doc()
                st.session_state[K_COLUMNS].append(_new_column(
                    f"sidebar #{st.session_state[K_NEXT_ID]}", doc, "sidebar",
                    "estado atual da sidebar",
                    bc.sha256_text(yaml.safe_dump(doc, sort_keys=True))))
        with a2:
            cfgs = bc.available_configs()
            pick = st.selectbox(
                "de research/labels/configs/", options=["—"] + [p.name for p in cfgs],
                key="bench_pick_config")
            if st.button("+ coluna do arquivo selecionado", key="bench_add_config",
                         use_container_width=True, disabled=(pick == "—")):
                path = next(p for p in cfgs if p.name == pick)
                text = path.read_text()
                st.session_state[K_COLUMNS].append(_new_column(
                    path.stem.replace("cyclophaser_params-", "params-"),
                    bc.load_config_text(text), "configs", path.name,
                    bc.sha256_text(text)))

        up = st.file_uploader("+ coluna de um YAML enviado", type=["yaml", "yml"],
                              key="bench_upload")
        if up is not None:
            text = up.getvalue().decode("utf-8")
            sha = bc.sha256_text(text)
            if st.session_state.get("_bench_upload_sha") != sha:
                try:
                    st.session_state[K_COLUMNS].append(_new_column(
                        Path(up.name).stem, bc.load_config_text(text),
                        "upload", up.name, sha))
                    st.session_state["_bench_upload_sha"] = sha
                except Exception as exc:
                    st.error(f"YAML inválido: {exc}")

        snaps = bc.available_snapshots()
        if snaps:
            s1, s2 = st.columns(2)
            with s1:
                spick = st.selectbox("snapshot congelado",
                                     options=["—"] + [p.stem for p in snaps],
                                     key="bench_pick_snapshot")
            with s2:
                if st.button("+ coluna de referência", key="bench_add_snapshot",
                             use_container_width=True, disabled=(spick == "—")):
                    path = next(p for p in snaps if p.stem == spick)
                    st.session_state[K_COLUMNS].append(_new_column(
                        f"publicada {path.stem}", {}, "snapshot", path.name,
                        bc.sha256_text(path.read_text()), snapshot_path=str(path)))

    cols = st.session_state[K_COLUMNS]
    if not cols:
        st.info("Nenhuma coluna ainda. Adicione ao menos uma acima.")
        return
    if not selected:
        st.info("Nenhum ciclone selecionado.")
        return

    _legend()

    # ── per-column headers and editors ────────────────────────────────────────
    specs: list[bc.ColumnSpec] = []
    header_cols = st.columns(len(cols))
    for i, col in enumerate(cols):
        with header_cols[i]:
            spec = _spec(col)
            specs.append(spec)
            _render_header(col, spec)
            if col["origin"] != "snapshot":
                with st.expander("editar", expanded=False):
                    new_text = st.text_area(
                        "config (YAML)", value=col["yaml_text"], height=200,
                        key=f"bench_edit_{col['cid']}",
                        label_visibility="collapsed")
                    if st.button("aplicar", key=f"bench_apply_{col['cid']}"):
                        try:
                            bc.load_config_text(new_text)
                        except Exception as exc:
                            st.error(f"YAML inválido: {exc}")
                        else:
                            if new_text != col["yaml_text"]:
                                col["yaml_text"] = new_text
                                col["edited"] = True
                            st.rerun()
            if st.button("remover", key=f"bench_del_{col['cid']}"):
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

    # ── aggregates, train and test in separate blocks ─────────────────────────
    st.divider()
    st.markdown("#### Agregados")
    st.caption(
        "Regra de vazamento: todo número agregado abaixo é calculado sobre o "
        "split de TREINO. O bloco de teste é separado, rotulado, e nunca somado "
        "ao de treino."
    )
    agg_cols = st.columns(len(cols))
    for i, col in enumerate(cols):
        with agg_cols[i]:
            st.markdown(f"**{col['name']}**")
            m = bc.metrics_by_split(results[i], labels, selected, membership)
            _render_metrics(m["train"], "TREINO")
            if m["test"]["ids"]:
                st.caption("— — —")
                _render_metrics(m["test"], "TESTE (split congelado)")

    # ── aligned grid ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("#### Por ciclone")
    show_labels = st.session_state[K_LABELS]
    for sid in selected:
        st.markdown(f"**{sid}** · {source_of[sid]} · split "
                    f"{membership.get(sid, '—')}")
        values = tuple(float(x) for x in series_all[sid].values)
        row = st.columns(len(cols) + (1 if show_labels else 0))
        off = 0
        if show_labels:
            with row[0]:
                rec = labels.get(sid)
                if rec is None:
                    st.caption("sem rótulo manual")
                else:
                    runs = bc.label_runs_for(rec)
                    st.image(_cell_png(values, tuple(runs), "rótulo manual"),
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
                    st.caption(f"sequência: {'bate' if seq_ok else 'difere'}")
                    mm = bc.mature_metrics({sid: res}, labels, [sid])
                    if mm["rows"]:
                        r = mm["rows"][0]
                        if r["d_start"] is None:
                            st.caption("maduro: sem par")
                        else:
                            st.caption(
                                f"maduro Δ={r['d_start']:+d}/{r['d_end']:+d} "
                                f"({'ok' if r['hit'] else 'fora'} de "
                                f"{bc.MATURE_MARGIN})")
        st.divider()
