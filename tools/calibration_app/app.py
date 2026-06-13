"""CycloPhaser calibration app — Etapa 1: Filter & Smoothing Tuning.

Loads a single cyclone CSV, runs process_vorticity with user-controlled
parameters, and displays the raw vs. filtered vs. smoothed vorticity series
so the user can visually tune the filter/smoothing settings before moving
on to phase-detection threshold calibration (Etapa 2).
"""

import io
import warnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from cyclophaser.determine_periods import process_vorticity

st.set_page_config(
    page_title="CycloPhaser Calibration",
    layout="wide",
)

# ── Page header ────────────────────────────────────────────────────────────────
st.title("CycloPhaser — Calibração de Parâmetros")
st.caption("Etapa 1 · Filtragem e Suavização · 1 ciclone")

# ── Sidebar: parameters ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtro Lanczos")
    use_filter = st.checkbox("Aplicar filtro Lanczos", value=True)
    cutoff_low = st.slider(
        "Cutoff baixo (horas)", min_value=48, max_value=336, step=24, value=168
    )
    cutoff_high = st.slider(
        "Cutoff alto (horas)", min_value=12, max_value=96, step=6, value=48
    )

    st.divider()
    st.header("Suavização Savgol")

    _sm_mode = st.selectbox("use_smoothing", ["auto", "off", "manual"])
    if _sm_mode == "manual":
        _sm_val = st.slider(
            "Janela Savgol 1× (steps, ímpar)", min_value=3, max_value=61, step=2, value=17
        )
        use_smoothing = _sm_val
    elif _sm_mode == "off":
        use_smoothing = False
    else:
        use_smoothing = "auto"

    _sm2_mode = st.selectbox("use_smoothing_twice", ["auto", "off", "manual"])
    if _sm2_mode == "manual":
        _sm2_val = st.slider(
            "Janela Savgol 2× (steps, ímpar)", min_value=3, max_value=61, step=2, value=17
        )
        use_smoothing_twice = _sm2_val
    elif _sm2_mode == "off":
        use_smoothing_twice = False
    else:
        use_smoothing_twice = "auto"

    with st.expander("Opções avançadas", expanded=False):
        replace_endpoints = st.slider(
            "Substituir bordas com lowpass (timesteps)",
            min_value=0, max_value=48, step=1, value=24,
        )
        savgol_poly = st.slider(
            "Grau do polinômio Savgol", min_value=2, max_value=5, step=1, value=3
        )

# ── Cached processing ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Processando vorticidade…")
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
    df = pd.read_csv(
        io.BytesIO(file_bytes), sep=";", index_col="time", parse_dates=True
    )
    series = df["min_max_zeta_850"]
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


# ── File upload ────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Carregar CSV do ciclone (formato: ';'-delimitado, coluna 'min_max_zeta_850')",
    type=["csv"],
)

if uploaded is None:
    st.info("Faça o upload de um arquivo CSV para começar.")
    st.stop()

st.caption(f"Arquivo: **{uploaded.name}** · {len(uploaded.getvalue())} bytes")

# ── Run processing ─────────────────────────────────────────────────────────────
try:
    vort, warns = _run_process_vorticity(
        uploaded.getvalue(),
        use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice,
        replace_endpoints, savgol_poly,
    )
except Exception as exc:
    st.error(f"Erro ao processar vorticidade: {exc}")
    st.stop()

for msg in warns:
    st.warning(msg)

# ── Figure: raw vs filtered vs smoothed ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 4.5))

ax.plot(
    vort.time, vort.zeta,
    color="gray", lw=0.8, alpha=0.7, label="ζ original",
)
ax.plot(
    vort.time, vort.filtered_vorticity,
    color="#d68c45", lw=1.5, label="ζ filtrada (Lanczos)",
)

if use_smoothing is not False:
    ax.plot(
        vort.time, vort.vorticity_smoothed,
        color="#1d3557", lw=2.0, label="ζ suavizada 1×",
    )
    if use_smoothing_twice is not False:
        ax.plot(
            vort.time, vort.vorticity_smoothed2,
            color="#e63946", lw=2.0, label="ζ suavizada 2×",
        )

ax.axhline(0, color="k", lw=0.4, ls="--")
ax.set_ylabel("ζ (s⁻¹)")
ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %HZ"))
plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
ax.legend(loc="upper right", fontsize=9)
ax.set_title(
    "Vorticidade: original · filtrada · suavizada", fontweight="bold"
)
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)
