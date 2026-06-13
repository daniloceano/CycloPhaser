"""CycloPhaser calibration app — multi-cyclone, phase detection, diagnostics.

Upload one or more cyclone CSVs, tune filter/smoothing and phase-detection
parameters interactively, and inspect results across all cyclones at once.
"""

import hashlib
import io
import warnings
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yaml

from cyclophaser.determine_periods import get_periods, periods_to_dict, process_vorticity
from cyclophaser.plots import plot_all_periods, plot_didactic

# CycloPhaser version (read from setup.py at import time)
try:
    import re as _re
    _setup = (Path(__file__).parent.parent.parent / "setup.py").read_text()
    _CP_VERSION = _re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]", _setup).group(1)
except Exception:
    _CP_VERSION = "unknown"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CycloPhaser Calibration", layout="wide")

# ── Default parameter values ───────────────────────────────────────────────────
_DEFAULTS: dict = {
    "use_filter":        True,
    "cutoff_low":        168,
    "cutoff_high":       48,
    "sm_mode":           "auto",
    "sm_val":            17,
    "sm2_mode":          "auto",
    "sm2_val":           17,
    "replace_endpoints": 24,
    "savgol_poly":       3,
    "n_cols":            2,
    "thr_int_len":       0.075,
    "thr_dec_len":       0.075,
    "thr_mat_len":       0.030,
    "thr_mat_dist":      0.125,
    "thr_int_gap":       0.075,
    "thr_dec_gap":       0.075,
    "thr_inc_len":       0.400,
}


def _reset() -> None:
    for k in _DEFAULTS:
        st.session_state.pop(k, None)


# ── Page header ────────────────────────────────────────────────────────────────
st.title("CycloPhaser — Calibração de Parâmetros")
st.caption("Filtragem · Suavização · Detecção de Fases · Multi-ciclone")

# ── Sidebar ────────────────────────────────────────────────────────────────────
_SM_OPTS = ["auto", "off", "manual"]

with st.sidebar:
    st.button("↺ Restaurar defaults", on_click=_reset, use_container_width=True)
    st.divider()

    # --- Lanczos filter ---
    st.header("Filtro Lanczos")
    use_filter = st.checkbox(
        "Aplicar filtro Lanczos", value=_DEFAULTS["use_filter"], key="use_filter"
    )
    cutoff_low = st.slider(
        "Cutoff baixo (horas)", 48, 336, step=24,
        value=_DEFAULTS["cutoff_low"], key="cutoff_low",
    )
    cutoff_high = st.slider(
        "Cutoff alto (horas)", 12, 96, step=6,
        value=_DEFAULTS["cutoff_high"], key="cutoff_high",
    )

    st.divider()
    # --- Savgol smoothing ---
    st.header("Suavização Savgol")
    _sm_mode = st.selectbox(
        "use_smoothing", _SM_OPTS,
        index=_SM_OPTS.index(_DEFAULTS["sm_mode"]), key="sm_mode",
    )
    if _sm_mode == "manual":
        use_smoothing = st.slider(
            "Janela Savgol 1× (steps, ímpar)", 3, 61, step=2,
            value=_DEFAULTS["sm_val"], key="sm_val",
        )
    elif _sm_mode == "off":
        use_smoothing = False
    else:
        use_smoothing = "auto"

    _sm2_mode = st.selectbox(
        "use_smoothing_twice", _SM_OPTS,
        index=_SM_OPTS.index(_DEFAULTS["sm2_mode"]), key="sm2_mode",
    )
    if _sm2_mode == "manual":
        use_smoothing_twice = st.slider(
            "Janela Savgol 2× (steps, ímpar)", 3, 61, step=2,
            value=_DEFAULTS["sm2_val"], key="sm2_val",
        )
    elif _sm2_mode == "off":
        use_smoothing_twice = False
    else:
        use_smoothing_twice = "auto"

    with st.expander("Opções avançadas", expanded=False):
        replace_endpoints = st.slider(
            "Substituir bordas com lowpass (timesteps)", 0, 48, step=1,
            value=_DEFAULTS["replace_endpoints"], key="replace_endpoints",
        )
        savgol_poly = st.slider(
            "Grau do polinômio Savgol", 2, 5, step=1,
            value=_DEFAULTS["savgol_poly"], key="savgol_poly",
        )

    st.divider()
    # --- Phase detection thresholds ---
    st.header("Detecção de fases")
    thr_int_len = st.slider(
        "Comprimento mín. intensificação", 0.01, 0.30, step=0.005,
        value=_DEFAULTS["thr_int_len"], key="thr_int_len",
    )
    thr_dec_len = st.slider(
        "Comprimento mín. decaimento", 0.01, 0.30, step=0.005,
        value=_DEFAULTS["thr_dec_len"], key="thr_dec_len",
    )
    thr_mat_len = st.slider(
        "Comprimento mín. maturidade", 0.005, 0.15, step=0.005,
        value=_DEFAULTS["thr_mat_len"], key="thr_mat_len",
    )
    thr_mat_dist = st.slider(
        "Distância maturidade", 0.05, 0.30, step=0.005,
        value=_DEFAULTS["thr_mat_dist"], key="thr_mat_dist",
    )

    with st.expander("Thresholds avançados", expanded=False):
        thr_int_gap = st.slider(
            "Gap máx. intensificação", 0.01, 0.30, step=0.005,
            value=_DEFAULTS["thr_int_gap"], key="thr_int_gap",
        )
        thr_dec_gap = st.slider(
            "Gap máx. decaimento", 0.01, 0.30, step=0.005,
            value=_DEFAULTS["thr_dec_gap"], key="thr_dec_gap",
        )
        thr_inc_len = st.slider(
            "Comprimento mín. incipiente", 0.1, 0.6, step=0.01,
            value=_DEFAULTS["thr_inc_len"], key="thr_inc_len",
        )

# Bundle phase params for reuse throughout the script
_PHASE_PARAMS = dict(
    threshold_intensification_length=thr_int_len,
    threshold_intensification_gap=thr_int_gap,
    threshold_mature_distance=thr_mat_dist,
    threshold_mature_length=thr_mat_len,
    threshold_decay_length=thr_dec_len,
    threshold_decay_gap=thr_dec_gap,
    threshold_incipient_length=thr_inc_len,
)

# ── Cached: process_vorticity ──────────────────────────────────────────────────
# Keyed on MD5 of file bytes + all filter/smoothing params.
# Changing only phase thresholds does NOT trigger a re-run.
@st.cache_data(
    show_spinner="Processando vorticidade…",
    hash_funcs={bytes: lambda b: hashlib.md5(b).hexdigest()},
)
def _run_process_vorticity(
    file_bytes: bytes,
    use_filter: bool,
    cutoff_low: int,
    cutoff_high: int,
    use_smoothing,
    use_smoothing_twice,
    replace_endpoints: int,
    savgol_poly: int,
):
    df_raw = pd.read_csv(
        io.BytesIO(file_bytes), sep=";", index_col="time", parse_dates=True
    )
    series = df_raw["min_max_zeta_850"]
    zeta_df = pd.DataFrame({"zeta": series})
    zeta_df.index = series.index
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        vort = process_vorticity(
            zeta_df,
            use_filter=use_filter,
            cutoff_low=cutoff_low,
            cutoff_high=cutoff_high,
            use_smoothing=use_smoothing,
            use_smoothing_twice=use_smoothing_twice,
            replace_endpoints_with_lowpass=replace_endpoints,
            savgol_polynomial=savgol_poly,
        )
    return vort, [str(w.message) for w in caught if issubclass(w.category, UserWarning)]


# ── Helpers ────────────────────────────────────────────────────────────────────
def _normalize(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


# Figure sizes per column count (matplotlib inches)
_FIGSIZES = {1: (12, 5), 2: (9, 4.5), 3: (7, 4)}


def _compute_diagnostics(name, periods_dict, df_result, all_warns):
    seen, seen_set = [], set()
    for ph in periods_dict:
        n = _normalize(ph)
        if n not in seen_set:
            seen.append(n)
            seen_set.add(n)

    gaps = int(df_result["periods"].isna().sum()) if "periods" in df_result.columns else 0

    phase_rows, short_phases = [], []
    for ph, (start, end) in periods_dict.items():
        dur_h = (end - start).total_seconds() / 3600
        flag = "⚠️" if dur_h < 6 else ""
        if flag:
            short_phases.append(_normalize(ph))
        phase_rows.append({
            "Fase": ph,
            "Início": str(start),
            "Fim": str(end),
            "Duração (h)": round(dur_h, 1),
            "": flag,
        })

    return {
        "name": name,
        "phases": seen,
        "gaps": gaps,
        "warns": all_warns,
        "short_phases": short_phases,
        "residual": any(_normalize(ph) == "residual" for ph in periods_dict),
        "phase_rows": phase_rows,
    }


def _build_yaml(cyclone_names) -> str:
    doc = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cyclophaser_version": _CP_VERSION,
            "cyclones_used": list(cyclone_names),
        },
        "filter_params": {
            "use_filter": use_filter,
            "cutoff_low": int(cutoff_low),
            "cutoff_high": int(cutoff_high),
            "replace_endpoints_with_lowpass": int(replace_endpoints),
            "use_smoothing": use_smoothing,
            "use_smoothing_twice": use_smoothing_twice,
            "savgol_polynomial": int(savgol_poly),
        },
        "phase_params": {k: float(v) for k, v in _PHASE_PARAMS.items()},
    }
    return yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ── File upload ────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Carregar CSV(s) de ciclone"
    " (formato: ';'-delimitado, coluna 'min_max_zeta_850')",
    type=["csv"],
    accept_multiple_files=True,
)

_EXAMPLE = Path(__file__).parent.parent.parent / "cyclophaser" / "example_data" / "example_file.csv"
if uploaded:
    files: dict[str, bytes] = {Path(f.name).stem: f.getvalue() for f in uploaded}
else:
    files = {"example_file": _EXAMPLE.read_bytes()}
    st.caption(f"Nenhum arquivo carregado — usando `{_EXAMPLE.name}` como padrão.")

cyclone_names = list(files.keys())

# ── Sidebar: YAML export (added after file names are known) ───────────────────
with st.sidebar:
    st.divider()
    st.download_button(
        "📥 Exportar parâmetros (YAML)",
        data=_build_yaml(cyclone_names).encode("utf-8"),
        file_name="cyclophaser_params.yaml",
        mime="text/yaml",
        use_container_width=True,
    )

# ── Grid layout control ────────────────────────────────────────────────────────
n_cols: int = st.select_slider(
    "Colunas na grade", options=[1, 2, 3],
    value=_DEFAULTS["n_cols"], key="n_cols",
)

# ── Main processing loop ───────────────────────────────────────────────────────
grid = st.columns(n_cols)
all_diag: list[dict] = []

for idx, (cyclone_name, file_bytes) in enumerate(files.items()):
    with grid[idx % n_cols]:
        st.subheader(cyclone_name)

        # Step 1 — process_vorticity (CACHED: reruns only on filter/smoothing change)
        try:
            vort, filter_warns = _run_process_vorticity(
                file_bytes, use_filter, cutoff_low, cutoff_high,
                use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
            )
        except Exception as exc:
            st.error(f"Erro ao processar vorticidade: {exc}")
            continue

        for msg in filter_warns:
            st.warning(msg)

        # Step 2 — get_periods (NOT cached: always reruns; fast enough for real-time UX)
        with warnings.catch_warnings(record=True) as _phase_caught:
            warnings.simplefilter("always")
            try:
                df_result = get_periods(
                    vorticity=vort, plot=False, plot_steps=False, **_PHASE_PARAMS
                )
            except Exception as exc:
                st.error(f"Erro na detecção de fases: {exc}")
                continue

        phase_warns = [
            str(w.message) for w in _phase_caught
            if issubclass(w.category, UserWarning)
        ]
        for msg in phase_warns:
            st.warning(msg)

        periods_dict = periods_to_dict(df_result)

        # Step 3 — plot_all_periods with controlled figsize
        fig, ax_pre = plt.subplots(figsize=_FIGSIZES[n_cols])
        try:
            plot_all_periods(periods_dict, df_result, ax=ax_pre, vorticity=vort)
        except Exception as exc:
            st.error(f"Erro na figura de fases: {exc}")
            plt.close(fig)
            continue
        ax_pre.set_title(cyclone_name, fontweight="bold")
        st.pyplot(fig)
        plt.close(fig)

        # Step 4 — plot_didactic (1-col mode only, inside expander)
        if n_cols == 1:
            with st.expander("Ver análise passo a passo"):
                try:
                    fig_d = plot_didactic(
                        df_result, vort, output_directory=None, **_PHASE_PARAMS
                    )
                    st.pyplot(fig_d)
                    plt.close(fig_d)
                except Exception as exc:
                    st.error(f"Erro no plot didático: {exc}")

        # Diagnostics
        diag = _compute_diagnostics(
            cyclone_name, periods_dict, df_result, filter_warns + phase_warns
        )
        all_diag.append(diag)

        # Detail table — 1-col mode
        if n_cols == 1:
            with st.expander("Diagnósticos detalhados", expanded=True):
                if diag["gaps"] > 0:
                    st.warning(f"Gaps sem fase: {diag['gaps']} timesteps")
                if diag["short_phases"]:
                    st.warning(
                        f"Fases curtas (< 6 h): {', '.join(diag['short_phases'])}"
                    )
                st.dataframe(
                    pd.DataFrame(diag["phase_rows"]).set_index("Fase"),
                    use_container_width=True,
                )

# ── Consolidated diagnostics — 2-3 col mode ───────────────────────────────────
if n_cols > 1 and all_diag:
    st.divider()
    st.subheader("Diagnósticos consolidados")
    rows = []
    for d in all_diag:
        rows.append({
            "Ciclone":      d["name"],
            "Fases":        " → ".join(d["phases"]),
            "N fases":      len(d["phases"]),
            "Gaps":         f"{d['gaps']} ⚠️" if d["gaps"] > 0 else "0",
            "Residual":     "✓" if d["residual"] else "—",
            "Fases curtas": ", ".join(d["short_phases"]) if d["short_phases"] else "—",
            "Warnings":     f"{len(d['warns'])} ⚠️" if d["warns"] else "0",
        })
    st.dataframe(
        pd.DataFrame(rows).set_index("Ciclone"),
        use_container_width=True,
    )
