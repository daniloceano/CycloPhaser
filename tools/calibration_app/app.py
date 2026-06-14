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

# Methodology image (used in Documentation tab)
_METHOD_IMG = (
    Path(__file__).parent.parent.parent / "docs" / "_images" / "cyclophaser_methodology.jpg"
)

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CycloPhaser Calibration", layout="wide")

# ── Default parameter values ─────────────────────────────────────────────────────
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


# ── Page header ──────────────────────────────────────────────────────────────────
st.title("CycloPhaser — Parameter Calibration")
st.caption("Filtering · Smoothing · Phase Detection · Multi-cyclone")

# ── Sidebar ──────────────────────────────────────────────────────────────────────
_SM_OPTS = ["auto", "off", "manual"]

with st.sidebar:
    st.button("↺ Reset to defaults", on_click=_reset, use_container_width=True)
    st.divider()

    # --- Lanczos filter ---
    st.header("Lanczos Filter")
    use_filter = st.checkbox(
        "Apply Lanczos filter", value=_DEFAULTS["use_filter"], key="use_filter",
        help=(
            "Applies a band-pass Lanczos filter to the raw vorticity series. "
            "Removes large-scale trends (slow variations) and high-frequency noise, "
            "isolating the cyclone signal at synoptic scales. Disabling this leaves "
            "the raw series, which typically yields very noisy phase detection."
        ),
    )
    cutoff_low = st.slider(
        "Low cutoff (hours)", 48, 336, step=24,
        value=_DEFAULTS["cutoff_low"], key="cutoff_low",
        help=(
            "Maximum period (hours) retained by the filter — the lower frequency bound. "
            "Components with periods longer than this value are suppressed. "
            "Higher values remove more large-scale trend; lower values preserve slower "
            "cyclone variations. Default: 168 h (7 days)."
        ),
    )
    cutoff_high = st.slider(
        "High cutoff (hours)", 12, 96, step=6,
        value=_DEFAULTS["cutoff_high"], key="cutoff_high",
        help=(
            "Minimum period (hours) retained by the filter — the upper frequency bound. "
            "Components with periods shorter than this value are suppressed as noise. "
            "Lower values allow more high-frequency variability; higher values produce "
            "a smoother curve. Default: 48 h (2 days)."
        ),
    )

    st.divider()
    # --- Savgol smoothing ---
    st.header("Savgol Smoothing")
    _sm_mode = st.selectbox(
        "use_smoothing", _SM_OPTS,
        index=_SM_OPTS.index(_DEFAULTS["sm_mode"]), key="sm_mode",
        help=(
            "Controls whether and how the Savitzky-Golay filter is applied after Lanczos. "
            "'auto': window computed automatically from series length. "
            "'off': no additional smoothing (uses Lanczos output directly). "
            "'manual': set the window size with the slider below."
        ),
    )
    if _sm_mode == "manual":
        use_smoothing = st.slider(
            "Savgol window 1× (steps, odd)", 3, 61, step=2,
            value=_DEFAULTS["sm_val"], key="sm_val",
            help=(
                "Window size of the Savitzky-Golay filter (number of timesteps, must be odd). "
                "Larger windows produce smoother, more stable curves for peak detection, "
                "but may erase details in short life-cycle events. "
                "Small windows preserve local variations but can create spurious extrema."
            ),
        )
    elif _sm_mode == "off":
        use_smoothing = False
    else:
        use_smoothing = "auto"

    _sm2_mode = st.selectbox(
        "use_smoothing_twice", _SM_OPTS,
        index=_SM_OPTS.index(_DEFAULTS["sm2_mode"]), key="sm2_mode",
        help=(
            "Applies the Savitzky-Golay filter a second time on the already-smoothed curve. "
            "Useful for noisy or high-temporal-resolution series where a single pass is "
            "insufficient to remove spurious oscillations. "
            "May distort or shorten phases in short-lived cyclones."
        ),
    )
    if _sm2_mode == "manual":
        use_smoothing_twice = st.slider(
            "Savgol window 2× (steps, odd)", 3, 61, step=2,
            value=_DEFAULTS["sm2_val"], key="sm2_val",
            help=(
                "Window size for the second Savitzky-Golay smoothing pass. "
                "Works the same as the 1× window, but is applied to the already-smoothed "
                "series. Generally can be equal to or slightly larger than the 1× window "
                "to ensure incremental smoothing."
            ),
        )
    elif _sm2_mode == "off":
        use_smoothing_twice = False
    else:
        use_smoothing_twice = "auto"

    with st.expander("Advanced options", expanded=False):
        replace_endpoints = st.slider(
            "Replace endpoints with lowpass (timesteps)", 0, 48, step=1,
            value=_DEFAULTS["replace_endpoints"], key="replace_endpoints",
            help=(
                "Replaces the first and last N timesteps of the filtered series with values "
                "from a simple low-pass filter. Reduces Gibbs-effect artifacts at the "
                "series boundaries introduced by the Lanczos filter. "
                "Set to 0 to disable. Default: 24 timesteps."
            ),
        )
        savgol_poly = st.slider(
            "Savgol polynomial degree", 2, 5, step=1,
            value=_DEFAULTS["savgol_poly"], key="savgol_poly",
            help=(
                "Degree of the polynomial fitted in each Savitzky-Golay window. "
                "Lower degrees (2–3) yield more aggressive smoothing. "
                "Higher degrees (4–5) better preserve local extrema and inflection points, "
                "but may be unstable with small window sizes. Default: 3."
            ),
        )

    st.divider()
    # --- Phase detection thresholds ---
    st.header("Phase Detection")
    thr_int_len = st.slider(
        "Min. intensification length", 0.01, 0.30, step=0.005,
        value=_DEFAULTS["thr_int_len"], key="thr_int_len",
        help=(
            "Minimum length of an intensification segment, expressed as a fraction of "
            "the total series length. Segments shorter than this are discarded or absorbed "
            "by adjacent phases. Higher values require longer, more sustained intensification; "
            "lower values allow brief intensification episodes."
        ),
    )
    thr_dec_len = st.slider(
        "Min. decay length", 0.01, 0.30, step=0.005,
        value=_DEFAULTS["thr_dec_len"], key="thr_dec_len",
        help=(
            "Minimum length of a decay segment as a fraction of total series length. "
            "Analogous to the intensification threshold, applied to the weakening phase. "
            "Higher values eliminate short decay episodes."
        ),
    )
    thr_mat_len = st.slider(
        "Min. mature length", 0.005, 0.15, step=0.005,
        value=_DEFAULTS["thr_mat_len"], key="thr_mat_len",
        help=(
            "Minimum length of the mature phase (peak intensity period) as a fraction "
            "of total series length. The mature stage spans the period around the vorticity "
            "minimum. Very high values may eliminate the mature stage of rapidly evolving "
            "cyclones; very low values can generate spurious peaks."
        ),
    )
    thr_mat_dist = st.slider(
        "Mature distance", 0.05, 0.30, step=0.005,
        value=_DEFAULTS["thr_mat_dist"], key="thr_mat_dist",
        help=(
            "Maximum allowed distance between the intensity peak (vorticity minimum) and "
            "the centre of the mature segment, as a fraction of total length. "
            "Controls how close to the true intensity maximum the mature phase must be located. "
            "Higher values allow offset peaks; lower values are more strict."
        ),
    )

    with st.expander("Advanced thresholds", expanded=False):
        thr_int_gap = st.slider(
            "Max. intensification gap", 0.01, 0.30, step=0.005,
            value=_DEFAULTS["thr_int_gap"], key="thr_int_gap",
            help=(
                "Maximum gap between two consecutive intensification segments that allows "
                "them to be merged into a single continuous segment. Expressed as a fraction "
                "of total series length. Gaps larger than this keep the segments separate."
            ),
        )
        thr_dec_gap = st.slider(
            "Max. decay gap", 0.01, 0.30, step=0.005,
            value=_DEFAULTS["thr_dec_gap"], key="thr_dec_gap",
            help=(
                "Maximum gap between consecutive decay segments for merging. "
                "Analogous to the intensification gap. Useful when the cyclone shows brief "
                "recoveries during decay that should not fragment the phase."
            ),
        )
        thr_inc_len = st.slider(
            "Min. incipient length", 0.1, 0.6, step=0.01,
            value=_DEFAULTS["thr_inc_len"], key="thr_inc_len",
            help=(
                "Minimum length of the incipient phase (pre-intensification period) as a "
                "fraction of total series length. The incipient stage covers genesis and "
                "early development before any identifiable intensification. "
                "Lower values allow shorter incipient phases."
            ),
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

# ── Cached: process_vorticity ────────────────────────────────────────────────────
# Keyed on MD5 of file bytes + all filter/smoothing params.
# Changing only phase thresholds does NOT trigger a re-run.
@st.cache_data(
    show_spinner="Processing vorticity…",
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


# ── Helpers ──────────────────────────────────────────────────────────────────────
def _normalize(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


# Figure sizes per column count (matplotlib inches)
_FIGSIZES = {1: (12, 5), 2: (9, 4.5), 3: (7, 4), 4: (5, 3), 5: (4, 2.8), 6: (3.5, 2.5)}

# Phase colours (mirror of plot_all_periods — kept here for compact mode and legend)
PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "gray",
}


def _render_global_legend() -> None:
    """Render one HTML legend bar showing phase colours. Used in dense-grid modes."""
    swatches = "&nbsp;&nbsp;".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;">'
        f'<span style="background:{c};display:inline-block;width:14px;height:14px;'
        f'border-radius:3px;flex-shrink:0;"></span>{ph}</span>'
        for ph, c in PHASE_COLORS.items()
    )
    st.markdown(
        f'<div style="font-size:12px;padding:4px 0 8px 0;">{swatches}</div>',
        unsafe_allow_html=True,
    )


def _plot_compact(cyclone_name: str, periods_dict: dict, vort) -> plt.Figure:
    """Dense-grid figure (n_cols >= 4): all vorticity series, no labels or titles.

    Same twin-axis layout as the full figure (left = zeta raw, right =
    filtered/smoothed), with phase shading and gap fix.  All text stripped
    so the figure is pure signal — the cyclone name comes from st.subheader.
    """
    fig, ax = plt.subplots(figsize=_FIGSIZES[n_cols])

    # Phase shading with gap fix
    phases_list = list(periods_dict.items())
    for i, (ph, (st_, en)) in enumerate(phases_list):
        right = phases_list[i + 1][1][0] if i + 1 < len(phases_list) else en
        ax.axvspan(st_, right, alpha=0.35, color=PHASE_COLORS.get(_normalize(ph), "#cccccc"))

    # Left axis: zeta original (raw)
    ax.plot(vort.time, vort["zeta"], color="gray", lw=0.6, alpha=0.7)

    # Right twin axis: filtered + smoothed (separate scale — same reason as full figure)
    ax2 = ax.twinx()
    ax2.plot(vort.time, vort["filtered_vorticity"], color="#d68c45", lw=1.0)
    ax2.plot(vort.time, vort["vorticity_smoothed"],  color="#1d3557", lw=1.2)
    ax2.plot(vort.time, vort["vorticity_smoothed2"], color="#e63946", lw=1.2)

    # Strip ALL text — labels, ticks, title
    for a in (ax, ax2):
        a.set_xlabel(""); a.set_ylabel(""); a.set_title("")
        a.tick_params(left=False, right=False, bottom=False,
                      labelleft=False, labelright=False, labelbottom=False)

    fig.tight_layout(pad=0.3)
    return fig


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
            "Phase":       ph,
            "Start":       str(start),
            "End":         str(end),
            "Duration (h)": round(dur_h, 1),
            "":            flag,
        })

    return {
        "name":         name,
        "phases":       seen,
        "gaps":         gaps,
        "warns":        all_warns,
        "short_phases": short_phases,
        "residual":     any(_normalize(ph) == "residual" for ph in periods_dict),
        "phase_rows":   phase_rows,
    }


def _build_yaml(cyclone_names) -> str:
    doc = {
        "metadata": {
            "timestamp":           datetime.now(timezone.utc).isoformat(),
            "cyclophaser_version": _CP_VERSION,
            "cyclones_used":       list(cyclone_names),
        },
        "filter_params": {
            "use_filter":                    use_filter,
            "cutoff_low":                    int(cutoff_low),
            "cutoff_high":                   int(cutoff_high),
            "replace_endpoints_with_lowpass": int(replace_endpoints),
            "use_smoothing":                 use_smoothing,
            "use_smoothing_twice":           use_smoothing_twice,
            "savgol_polynomial":             int(savgol_poly),
        },
        "phase_params": {k: float(v) for k, v in _PHASE_PARAMS.items()},
    }
    return yaml.dump(doc, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ── File upload ──────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload cyclone CSV(s)"
    " (format: ';'-delimited, column 'min_max_zeta_850')",
    type=["csv"],
    accept_multiple_files=True,
)

_EXAMPLE = Path(__file__).parent.parent.parent / "cyclophaser" / "example_data" / "example_file.csv"
if uploaded:
    files: dict[str, bytes] = {Path(f.name).stem: f.getvalue() for f in uploaded}
else:
    files = {"example_file": _EXAMPLE.read_bytes()}
    st.caption(f"No file uploaded — using `{_EXAMPLE.name}` as default.")

cyclone_names = list(files.keys())

# ── Sidebar: YAML export (added after file names are known) ───────────────────
with st.sidebar:
    st.divider()
    st.download_button(
        "📥 Export parameters (YAML)",
        data=_build_yaml(cyclone_names).encode("utf-8"),
        file_name="cyclophaser_params.yaml",
        mime="text/yaml",
        use_container_width=True,
    )

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab_cal, tab_doc = st.tabs(["Calibration", "Documentation"])

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Calibration
# ══════════════════════════════════════════════════════════════════════════════════
with tab_cal:
    # Grid layout control
    n_cols: int = st.select_slider(
        "Grid columns", options=[1, 2, 3, 4, 5, 6],
        value=_DEFAULTS["n_cols"], key="n_cols",
    )

    # Dense-grid global legend (rendered once, above the grid)
    if n_cols >= 4:
        _render_global_legend()

    # Main processing loop
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
                st.error(f"Error processing vorticity: {exc}")
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
                    st.error(f"Error in phase detection: {exc}")
                    continue

            phase_warns = [
                str(w.message) for w in _phase_caught
                if issubclass(w.category, UserWarning)
            ]
            for msg in phase_warns:
                st.warning(msg)

            periods_dict = periods_to_dict(df_result)

            # Step 3 — figure: compact (n_cols >= 4) or full plot_all_periods (n_cols <= 3)
            if n_cols >= 4:
                try:
                    fig = _plot_compact(cyclone_name, periods_dict, vort)
                except Exception as exc:
                    st.error(f"Error in compact figure: {exc}")
                    continue
            else:
                fig, ax_pre = plt.subplots(figsize=_FIGSIZES[n_cols])
                try:
                    plot_all_periods(periods_dict, df_result, ax=ax_pre, vorticity=vort)
                except Exception as exc:
                    st.error(f"Error in phase figure: {exc}")
                    plt.close(fig)
                    continue
                ax_pre.set_title(cyclone_name, fontweight="bold")
            st.pyplot(fig)
            plt.close(fig)

            # Step 4 — plot_didactic (1-col mode only, inside expander)
            if n_cols == 1:
                with st.expander("Step-by-step analysis"):
                    try:
                        fig_d = plot_didactic(
                            df_result, vort, output_directory=None, **_PHASE_PARAMS
                        )
                        st.pyplot(fig_d)
                        plt.close(fig_d)
                    except Exception as exc:
                        st.error(f"Error in didactic plot: {exc}")

            # Diagnostics
            diag = _compute_diagnostics(
                cyclone_name, periods_dict, df_result, filter_warns + phase_warns
            )
            all_diag.append(diag)

            # Detail table — 1-col mode
            if n_cols == 1:
                with st.expander("Detailed diagnostics", expanded=True):
                    if diag["gaps"] > 0:
                        st.warning(f"Unlabelled gaps: {diag['gaps']} timesteps")
                    if diag["short_phases"]:
                        st.warning(
                            f"Short phases (< 6 h): {', '.join(diag['short_phases'])}"
                        )
                    st.dataframe(
                        pd.DataFrame(diag["phase_rows"]).set_index("Phase"),
                        use_container_width=True,
                    )

    # Consolidated diagnostics — 2+ col mode
    if n_cols > 1 and all_diag:
        st.divider()
        st.subheader("Consolidated diagnostics")
        rows = []
        for d in all_diag:
            rows.append({
                "Cyclone":      d["name"],
                "Phases":       " → ".join(d["phases"]),
                "N phases":     len(d["phases"]),
                "Gaps":         f"{d['gaps']} ⚠️" if d["gaps"] > 0 else "0",
                "Residual":     "✓" if d["residual"] else "—",
                "Short phases": ", ".join(d["short_phases"]) if d["short_phases"] else "—",
                "Warnings":     f"{len(d['warns'])} ⚠️" if d["warns"] else "0",
            })
        st.dataframe(
            pd.DataFrame(rows).set_index("Cyclone"),
            use_container_width=True,
        )

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 2 — Documentation
# ══════════════════════════════════════════════════════════════════════════════════
with tab_doc:
    st.header("CycloPhaser — Method Documentation")
    st.caption(
        "Reference: de Souza et al. (2024). *New perspectives on South Atlantic storm track "
        "through an automatic method for detecting extratropical cyclones' lifecycle*. "
        "International Journal of Climatology."
    )

    # ── 1. Method overview ──────────────────────────────────────────────────────
    with st.expander("1 · Method overview", expanded=True):
        if _METHOD_IMG.exists():
            st.image(
                str(_METHOD_IMG),
                caption=(
                    "Illustration of CycloPhaser methodology. "
                    "(A) Raw vorticity series. (B) After Lanczos band-pass filtering "
                    "(dashed circles: endpoint artifacts). (C) After first Savitzky-Golay pass. "
                    "(D) After second Savitzky-Golay pass. (E) Identified peaks and valleys. "
                    "(F–J) Sequential detection of intensification, decay, mature, residual, "
                    "and incipient stages. (K) Full life cycle. From de Souza et al. (2024)."
                ),
            )

        st.markdown("""
CycloPhaser identifies distinct phases of cyclone life cycles by analyzing the relative
vorticity time series at the cyclone centre and its first derivative.

**Four main stages** are detected, plus an optional residual stage:

| Stage | Description |
|---|---|
| **Incipient** | Early development before any identifiable intensification. Detected last (fills unlabelled periods at the series start). |
| **Intensification** | Vorticity intensity increases (more negative in the Southern Hemisphere) from one peak to a subsequent valley. |
| **Mature** | Interval between a derivative valley and its following derivative peak — represents the cyclone's peak strength (minimum central vorticity, SH). |
| **Decay** | Decrease in vorticity after the mature phase until dissipation. |
| **Residual** | Re-intensification episodes that do not progress to a full mature stage. |

**Processing pipeline:**

1. **Lanczos band-pass filter** — removes large-scale (low-frequency) trends and
   high-frequency noise, isolating the synoptic-scale cyclone signal.
   Endpoint artifacts (Gibbs effect) are optionally corrected by replacing the first
   and last *N* timesteps with a simple low-pass estimate.

2. **Savitzky-Golay smoothing** — applied once (or twice) to the filtered series,
   ensuring a clean sinusoidal pattern in both the vorticity and its derivative.
   This is critical for reliable peak/valley detection.

3. **Phase detection** — peaks and valleys in the smoothed series and its derivative
   are identified and matched against the threshold criteria (see sections 3 and 4).

> **Southern Hemisphere convention**: vorticity is negative; more negative = more intense.
> For Northern Hemisphere data, multiply the vorticity series by −1 before passing it
> to CycloPhaser.
""")

    # ── 2. Filter and smoothing parameters ─────────────────────────────────────
    with st.expander("2 · Filter and smoothing parameters", expanded=False):
        st.markdown("""
These parameters control the preprocessing chain that transforms the raw vorticity
series into the smoothed signal used for phase detection.

---

### `use_filter` — Apply Lanczos band-pass filter
Activates the Lanczos spectral filter. When disabled, the raw vorticity series is
passed directly to the smoothing step (or used as-is if smoothing is also off).
Disabling typically produces very noisy phase detection.

### `cutoff_low` — Low-frequency cutoff (hours)
Maximum period retained by the filter. Variability slower than this (e.g., seasonal
trends, synoptic-scale background flow) is removed. **Default: 168 h (7 days).**
Increasing this value removes more of the background state; decreasing it may retain
slow drifts that interfere with phase detection.

### `cutoff_high` — High-frequency cutoff (hours)
Minimum period retained. Variability faster than this (sub-synoptic noise) is suppressed.
**Default: 48 h (2 days).** Decreasing allows finer-scale oscillations through;
increasing produces a smoother but potentially over-smoothed signal.

### `replace_endpoints_with_lowpass` — Endpoint correction (timesteps)
The Lanczos filter introduces Gibbs-effect oscillations at the series edges. This
parameter replaces the first and last *N* timesteps of the filtered output with a
simple low-pass estimate. **Default: 24 timesteps.** Set to 0 to disable.
The methodology figure panel (B) shows the endpoint artifacts that this parameter corrects.

---

### `use_smoothing` — Savitzky-Golay (1st pass)
Controls the first smoothing pass:
- `'auto'`: window length computed automatically from series length (recommended).
- `'off'`: no smoothing; use the Lanczos output directly.
- `'manual'`: specify the window via the slider (must be an odd integer).

When set to `'manual'`, the **window size** controls the degree of smoothing:
larger windows → smoother curves, but risk erasing details of short life cycles.

### `use_smoothing_twice` — Savitzky-Golay (2nd pass)
Applies a second Savitzky-Golay pass on the already-smoothed series. Useful for
high-temporal-resolution data (e.g., hourly) where a single pass leaves residual
oscillations. Same mode options as `use_smoothing`. Can distort short phases.

### `savgol_polynomial` — Polynomial degree
Degree of the polynomial fitted within each Savitzky-Golay window. **Default: 3.**
Lower degrees (2–3) give more aggressive smoothing; higher degrees (4–5) better
preserve local extrema but may be unstable with small windows.
""")

    # ── 3. Phase detection thresholds ──────────────────────────────────────────
    with st.expander("3 · Phase detection thresholds", expanded=False):
        st.markdown("""
All thresholds below are expressed as **fractions of the total series length**
(number of timesteps), unless noted otherwise. This makes them resolution-independent
across datasets with different temporal coverages.

---

### `threshold_intensification_length`
Minimum duration of an intensification segment. Segments shorter than this fraction
are discarded or absorbed by adjacent phases. **Default: 0.075.**
Increase to require more sustained intensification; decrease to allow brief episodes.

### `threshold_decay_length`
Minimum duration of a decay segment. Analogous to the intensification threshold.
**Default: 0.075.**

### `threshold_mature_length`
Minimum duration of the mature stage (peak intensity interval). **Default: 0.030.**
Very high values may eliminate the mature stage of rapidly evolving cyclones.

### `threshold_mature_distance`
Maximum distance between the vorticity minimum (true intensity peak) and the
centre of the detected mature segment, as a fraction of total series length.
**Default: 0.125.** Higher values allow greater offset; lower values are stricter
about centering the mature stage on the true peak.

### `threshold_intensification_gap`
Maximum gap between two consecutive intensification segments that allows them to
be merged into a single block. **Default: 0.075.**
Gaps larger than this keep the segments separate.

### `threshold_decay_gap`
Maximum merging gap for consecutive decay segments. **Default: 0.075.**
Useful when the cyclone shows brief recoveries during weakening.

### `threshold_incipient_length`
Minimum duration of the incipient phase (genesis and early development, before
the first identifiable intensification). **Default: 0.400.**
This is the largest threshold by default because the incipient stage often
spans a significant portion of the early life cycle.
""")

    # ── 4. Known methodological notes ──────────────────────────────────────────
    with st.expander("4 · Known methodological notes", expanded=False):
        st.markdown("""
### Detection pipeline and phase precedence

The detection functions are called in a **fixed sequential order**:

1. `find_intensification_period`
2. `find_decay_period`
3. `find_mature_stage`
4. `find_residual_period`
5. `post_process_periods` — gap-filling and singleton removal
6. `find_incipient_period` — fills unlabelled timesteps at the series start

Each function writes to the `periods` column of the DataFrame.
**Functions called later can overwrite regions already labelled by earlier functions.**
The most significant consequence is that `find_decay_period` (step 2) may overwrite
timesteps that `find_intensification_period` (step 1) had already marked, because
both functions scan the same peaks/valleys and their detected intervals can overlap.

---

### Threshold calibration: inspect the final output

Because of this precedence, the practical effect of a threshold may be smaller
than expected. For example, `threshold_intensification_gap` controls the maximum
gap bridged between two intensification blocks — but if `find_decay_period`
subsequently marks those same timesteps as decay, the gap-bridging has no visible
effect on the final output.

> **When calibrating thresholds, always inspect the final `periods` column rather
> than assuming each parameter acts in isolation.**
> The Calibration tab's phase figures and diagnostics table reflect the actual
> final output after all pipeline steps.

---

### Phase detection lag

The detected *start* of a phase may lag the true onset by up to approximately
**15–18 h (5–6 timesteps at 3-hourly resolution)**. This lag is an inherent
consequence of the Lanczos + Savgol filtering chain: the smoothed signal requires
several timesteps to build enough amplitude for the algorithm to reliably identify
a new feature.

The lag is most pronounced for the **residual** stage (re-intensification after
decay), where it was consistently observed to be 15–18 h across controlled synthetic
test cases. Other transitions (e.g., the onset of intensification when no explicit
incipient segment precedes it) can show similar lags.

> When interpreting results or defining search windows for event attribution,
> a margin of at least **18 h** around detected phase boundaries is recommended.
""")
