"""CycloPhaser calibration app — multi-cyclone, phase detection, diagnostics.

Upload one or more cyclone CSVs, tune filter/smoothing and phase-detection
parameters interactively, and inspect results across all cyclones at once.
"""

import hashlib
import io
import warnings
import zipfile
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

_METHOD_IMG = (
    Path(__file__).parent.parent.parent / "docs" / "_images" / "cyclophaser_methodology.jpg"
)

# ── Page config ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CycloPhaser Calibration", layout="wide")

# ── Defaults ─────────────────────────────────────────────────────────────────────
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

_SM_OPTS = ["auto", "off", "manual"]

# YAML key → (session_state key, converter)
_YAML_FILTER_MAP: dict = {
    "use_filter":                    ("use_filter",        bool),
    "cutoff_low":                    ("cutoff_low",        int),
    "cutoff_high":                   ("cutoff_high",       int),
    "replace_endpoints_with_lowpass": ("replace_endpoints", int),
    "savgol_polynomial":             ("savgol_poly",       int),
}
_YAML_PHASE_MAP: dict = {
    "threshold_intensification_length": ("thr_int_len",  float),
    "threshold_intensification_gap":    ("thr_int_gap",  float),
    "threshold_mature_distance":        ("thr_mat_dist", float),
    "threshold_mature_length":          ("thr_mat_len",  float),
    "threshold_decay_length":           ("thr_dec_len",  float),
    "threshold_decay_gap":              ("thr_dec_gap",  float),
    "threshold_incipient_length":       ("thr_inc_len",  float),
}
_KNOWN_FILTER_YAML_KEYS = set(_YAML_FILTER_MAP) | {"use_smoothing", "use_smoothing_twice"}
_KNOWN_PHASE_YAML_KEYS  = set(_YAML_PHASE_MAP)


# ── Pure helper functions ─────────────────────────────────────────────────────────
def _normalize(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


def _reset() -> None:
    for k in _DEFAULTS:
        st.session_state.pop(k, None)
    # Clear YAML import state so a still-loaded file can be re-imported after reset
    st.session_state.pop("_yaml_import_hash", None)
    st.session_state.pop("_yaml_import_result", None)


def _load_yaml_config(yaml_bytes: bytes) -> dict:
    """Parse an exported YAML and write values into session_state.

    Returns {"error": str|None, "ignored": list, "missing": list, "count": int}.
    """
    try:
        doc = yaml.safe_load(yaml_bytes)
    except yaml.YAMLError as exc:
        return {"error": f"Invalid YAML: {exc}", "ignored": [], "missing": [], "count": 0}

    if not isinstance(doc, dict):
        return {"error": "YAML root must be a mapping.", "ignored": [], "missing": [], "count": 0}

    missing_secs = [s for s in ("filter_params", "phase_params") if s not in doc]
    if missing_secs:
        return {
            "error": f"Missing required sections: {', '.join(missing_secs)}",
            "ignored": [], "missing": [], "count": 0,
        }

    fp = doc["filter_params"]
    pp = doc["phase_params"]

    ignored = (
        [f"filter_params.{k}" for k in fp if k not in _KNOWN_FILTER_YAML_KEYS]
        + [f"phase_params.{k}" for k in pp if k not in _KNOWN_PHASE_YAML_KEYS]
    )
    missing = (
        [f"filter_params.{k}" for k in _KNOWN_FILTER_YAML_KEYS if k not in fp]
        + [f"phase_params.{k}" for k in _KNOWN_PHASE_YAML_KEYS  if k not in pp]
    )

    count = 0
    for yaml_key, (ss_key, conv) in _YAML_FILTER_MAP.items():
        if yaml_key in fp:
            try:
                st.session_state[ss_key] = conv(fp[yaml_key])
                count += 1
            except (ValueError, TypeError):
                ignored.append(f"filter_params.{yaml_key} (conversion error)")

    # use_smoothing / use_smoothing_twice need special handling (mode + optional value)
    for yaml_key, mode_key, val_key in [
        ("use_smoothing",       "sm_mode",  "sm_val"),
        ("use_smoothing_twice", "sm2_mode", "sm2_val"),
    ]:
        if yaml_key in fp:
            v = fp[yaml_key]
            if v == "auto":
                st.session_state[mode_key] = "auto"; count += 1
            elif v is False or v == "off":
                st.session_state[mode_key] = "off"; count += 1
            elif isinstance(v, int):
                st.session_state[mode_key] = "manual"
                st.session_state[val_key]  = v
                count += 1

    for yaml_key, (ss_key, conv) in _YAML_PHASE_MAP.items():
        if yaml_key in pp:
            try:
                st.session_state[ss_key] = conv(pp[yaml_key])
                count += 1
            except (ValueError, TypeError):
                ignored.append(f"phase_params.{yaml_key} (conversion error)")

    return {"error": None, "ignored": ignored, "missing": missing, "count": count}


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


def _render_csv(periods_dict: dict) -> bytes:
    rows = [
        {"phase": ph, "start": str(s), "end": str(e)}
        for ph, (s, e) in periods_dict.items()
    ]
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


@st.cache_data(
    hash_funcs={bytes: lambda b: hashlib.md5(b).hexdigest()},
    show_spinner=False,
)
def _render_png_for_export(
    file_bytes: bytes,
    use_filter, cutoff_low, cutoff_high,
    use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
    phase_params_tuple: tuple,
    name: str,
) -> bytes:
    """Render a full-size plot_all_periods PNG. Cached per unique param combination."""
    vort, _ = _run_process_vorticity(
        file_bytes, use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
    )
    phase_params = dict(phase_params_tuple)
    df_result = get_periods(vorticity=vort, plot=False, plot_steps=False, **phase_params)
    periods_dict = periods_to_dict(df_result)
    fig, ax = plt.subplots(figsize=(12, 5))
    try:
        plot_all_periods(periods_dict, df_result, ax=ax, vorticity=vort)
    except Exception:
        pass
    ax.set_title(name, fontweight="bold")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _build_zip(ok_results: dict, yaml_str: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("parameters.yaml", yaml_str)
        for name, res in ok_results.items():
            zf.writestr(f"{name}_periods.csv", res["csv_bytes"].decode("utf-8"))
            zf.writestr(f"{name}_periods.png", res["png_bytes"])
    buf.seek(0)
    return buf.getvalue()


# Figure sizes per column count (matplotlib inches)
_FIGSIZES = {1: (12, 5), 2: (9, 4.5), 3: (7, 4), 4: (5, 3), 5: (4, 2.8), 6: (3.5, 2.5)}

PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "gray",
}


def _render_global_legend() -> None:
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
    """Dense-grid figure (n_cols >= 4): all vorticity series, no labels/titles."""
    fig, ax = plt.subplots(figsize=_FIGSIZES[n_cols])
    phases_list = list(periods_dict.items())
    for i, (ph, (st_, en)) in enumerate(phases_list):
        right = phases_list[i + 1][1][0] if i + 1 < len(phases_list) else en
        ax.axvspan(st_, right, alpha=0.35, color=PHASE_COLORS.get(_normalize(ph), "#cccccc"))
    ax.plot(vort.time, vort["zeta"], color="gray", lw=0.6, alpha=0.7)
    ax2 = ax.twinx()
    ax2.plot(vort.time, vort["filtered_vorticity"], color="#d68c45", lw=1.0)
    ax2.plot(vort.time, vort["vorticity_smoothed"],  color="#1d3557", lw=1.2)
    ax2.plot(vort.time, vort["vorticity_smoothed2"], color="#e63946", lw=1.2)
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
            seen.append(n); seen_set.add(n)
    gaps = int(df_result["periods"].isna().sum()) if "periods" in df_result.columns else 0
    phase_rows, short_phases = [], []
    for ph, (start, end) in periods_dict.items():
        dur_h = (end - start).total_seconds() / 3600
        flag = "⚠️" if dur_h < 6 else ""
        if flag:
            short_phases.append(_normalize(ph))
        phase_rows.append({
            "Phase": ph, "Start": str(start), "End": str(end),
            "Duration (h)": round(dur_h, 1), "": flag,
        })
    return {
        "name": name, "phases": seen, "gaps": gaps, "warns": all_warns,
        "short_phases": short_phases,
        "residual": any(_normalize(ph) == "residual" for ph in periods_dict),
        "phase_rows": phase_rows,
    }


# ── Cached vorticity processing ───────────────────────────────────────────────────
@st.cache_data(
    show_spinner="Processing vorticity…",
    hash_funcs={bytes: lambda b: hashlib.md5(b).hexdigest()},
)
def _run_process_vorticity(
    file_bytes, use_filter, cutoff_low, cutoff_high,
    use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
):
    df_raw = pd.read_csv(io.BytesIO(file_bytes), sep=";", index_col="time", parse_dates=True)
    series = df_raw["min_max_zeta_850"]
    zeta_df = pd.DataFrame({"zeta": series}); zeta_df.index = series.index
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        vort = process_vorticity(
            zeta_df, use_filter=use_filter, cutoff_low=cutoff_low, cutoff_high=cutoff_high,
            use_smoothing=use_smoothing, use_smoothing_twice=use_smoothing_twice,
            replace_endpoints_with_lowpass=replace_endpoints, savgol_polynomial=savgol_poly,
        )
    return vort, [str(w.message) for w in caught if issubclass(w.category, UserWarning)]


# ── Page header ──────────────────────────────────────────────────────────────────
st.title("CycloPhaser — Parameter Calibration")
st.caption("Filtering · Smoothing · Phase Detection · Multi-cyclone")

# ── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    # --- YAML import ---
    st.subheader("Import configuration")
    _yaml_file = st.file_uploader(
        "Load previously exported YAML", type=["yaml", "yml"], key="yaml_import",
        help="Upload a YAML file exported by this app to restore its filter and phase parameters.",
    )
    if _yaml_file is not None:
        _fhash = hashlib.md5(_yaml_file.getvalue()).hexdigest()
        if st.session_state.get("_yaml_import_hash") != _fhash:
            _result = _load_yaml_config(_yaml_file.getvalue())
            st.session_state["_yaml_import_hash"] = _fhash
            st.session_state["_yaml_import_result"] = _result
            if _result["error"] is None:
                st.rerun()  # reflect new widget values immediately
    else:
        # File removed — clear hash so the same file can be re-imported if needed
        st.session_state.pop("_yaml_import_hash", None)

    if "_yaml_import_result" in st.session_state:
        _r = st.session_state["_yaml_import_result"]
        if _r["error"]:
            st.error(f"Import failed: {_r['error']}")
        else:
            st.success(f"Loaded {_r['count']} parameters from YAML.")
            if _r["ignored"]:
                st.warning(f"Ignored unknown keys: {', '.join(_r['ignored'])}")
            if _r["missing"]:
                st.warning(f"Using defaults for missing keys: {', '.join(_r['missing'])}")

    st.divider()
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

# Bundle phase params
_PHASE_PARAMS = dict(
    threshold_intensification_length=thr_int_len,
    threshold_intensification_gap=thr_int_gap,
    threshold_mature_distance=thr_mat_dist,
    threshold_mature_length=thr_mat_len,
    threshold_decay_length=thr_dec_len,
    threshold_decay_gap=thr_dec_gap,
    threshold_incipient_length=thr_inc_len,
)
_phase_params_tuple = tuple(sorted(_PHASE_PARAMS.items()))

# ── File upload ──────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload cyclone CSV(s) (format: ';'-delimited, column 'min_max_zeta_850')",
    type=["csv"], accept_multiple_files=True,
)
_EXAMPLE = Path(__file__).parent.parent.parent / "cyclophaser" / "example_data" / "example_file.csv"
if uploaded:
    files: dict[str, bytes] = {Path(f.name).stem: f.getvalue() for f in uploaded}
else:
    files = {"example_file": _EXAMPLE.read_bytes()}
    st.caption(f"No file uploaded — using `{_EXAMPLE.name}` as default.")

cyclone_names = list(files.keys())

# ── Sidebar: YAML export ─────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.download_button(
        "📥 Export parameters (YAML)",
        data=_build_yaml(cyclone_names).encode("utf-8"),
        file_name="cyclophaser_params.yaml",
        mime="text/yaml",
        use_container_width=True,
    )

# ── Pre-process all cyclones ─────────────────────────────────────────────────────
# Done before rendering tabs so export data (CSV + PNG) is ready for the ZIP button.
all_results: dict[str, dict] = {}

for _cname, _fbytes in files.items():
    _res: dict = {"ok": False, "name": _cname}

    try:
        _vort, _fwarns = _run_process_vorticity(
            _fbytes, use_filter, cutoff_low, cutoff_high,
            use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
        )
    except Exception as _exc:
        _res["error"] = f"Vorticity processing failed: {_exc}"
        all_results[_cname] = _res
        continue

    with warnings.catch_warnings(record=True) as _wc:
        warnings.simplefilter("always")
        try:
            _df = get_periods(vorticity=_vort, plot=False, plot_steps=False, **_PHASE_PARAMS)
        except Exception as _exc:
            _res["error"] = f"Phase detection failed: {_exc}"
            _res["filter_warns"] = _fwarns
            all_results[_cname] = _res
            continue

    _pwarns = [str(w.message) for w in _wc if issubclass(w.category, UserWarning)]
    _pdict  = periods_to_dict(_df)

    try:
        _png = _render_png_for_export(
            _fbytes, use_filter, cutoff_low, cutoff_high,
            use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
            _phase_params_tuple, _cname,
        )
    except Exception:
        _png = b""

    _res.update({
        "ok":           True,
        "vort":         _vort,
        "df_result":    _df,
        "periods_dict": _pdict,
        "filter_warns": _fwarns,
        "phase_warns":  _pwarns,
        "diag":         _compute_diagnostics(_cname, _pdict, _df, _fwarns + _pwarns),
        "csv_bytes":    _render_csv(_pdict),
        "png_bytes":    _png,
    })
    all_results[_cname] = _res

_ok_results = {n: r for n, r in all_results.items() if r["ok"]}
_zip_bytes  = _build_zip(_ok_results, _build_yaml(cyclone_names))

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab_cal, tab_doc = st.tabs(["Calibration", "Documentation"])

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Calibration
# ══════════════════════════════════════════════════════════════════════════════════
with tab_cal:
    # Top row: grid selector + ZIP export
    _c1, _c2 = st.columns([4, 1])
    with _c1:
        n_cols: int = st.select_slider(
            "Grid columns", options=[1, 2, 3, 4, 5, 6],
            value=_DEFAULTS["n_cols"], key="n_cols",
        )
    with _c2:
        st.download_button(
            "📦 Export all (ZIP)",
            data=_zip_bytes,
            file_name="cyclophaser_results.zip",
            mime="application/zip",
            use_container_width=True,
            disabled=not bool(_ok_results),
            help=(
                "Downloads a ZIP containing, for each cyclone: "
                "<name>_periods.csv, <name>_periods.png, and parameters.yaml."
            ),
        )

    if n_cols >= 4:
        _render_global_legend()

    # Display grid
    grid = st.columns(n_cols)
    for idx, (cyclone_name, res) in enumerate(all_results.items()):
        with grid[idx % n_cols]:
            st.subheader(cyclone_name)

            if not res["ok"]:
                st.error(res.get("error", "Unknown error"))
                continue

            for msg in res["filter_warns"]:
                st.warning(msg)
            for msg in res["phase_warns"]:
                st.warning(msg)

            # Figure
            if n_cols >= 4:
                try:
                    fig = _plot_compact(cyclone_name, res["periods_dict"], res["vort"])
                except Exception as exc:
                    st.error(f"Error in compact figure: {exc}")
                    continue
            else:
                fig, ax_pre = plt.subplots(figsize=_FIGSIZES[n_cols])
                try:
                    plot_all_periods(
                        res["periods_dict"], res["df_result"],
                        ax=ax_pre, vorticity=res["vort"],
                    )
                except Exception as exc:
                    st.error(f"Error in phase figure: {exc}")
                    plt.close(fig)
                    continue
                ax_pre.set_title(cyclone_name, fontweight="bold")
            st.pyplot(fig)
            plt.close(fig)

            # 1-col extras
            if n_cols == 1:
                with st.expander("Step-by-step analysis"):
                    try:
                        fig_d = plot_didactic(
                            res["df_result"], res["vort"],
                            output_directory=None, **_PHASE_PARAMS,
                        )
                        st.pyplot(fig_d); plt.close(fig_d)
                    except Exception as exc:
                        st.error(f"Error in didactic plot: {exc}")

                diag = res["diag"]
                with st.expander("Detailed diagnostics", expanded=True):
                    if diag["gaps"] > 0:
                        st.warning(f"Unlabelled gaps: {diag['gaps']} timesteps")
                    if diag["short_phases"]:
                        st.warning(f"Short phases (< 6 h): {', '.join(diag['short_phases'])}")
                    st.dataframe(
                        pd.DataFrame(diag["phase_rows"]).set_index("Phase"),
                        use_container_width=True,
                    )
                    # Individual download buttons
                    _dl1, _dl2 = st.columns(2)
                    with _dl1:
                        st.download_button(
                            "⬇ Download CSV",
                            data=res["csv_bytes"],
                            file_name=f"{cyclone_name}_periods.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
                    with _dl2:
                        st.download_button(
                            "⬇ Download PNG",
                            data=res["png_bytes"],
                            file_name=f"{cyclone_name}_periods.png",
                            mime="image/png",
                            use_container_width=True,
                            disabled=not bool(res["png_bytes"]),
                        )

    # Consolidated diagnostics — 2+ col mode
    if n_cols > 1 and _ok_results:
        st.divider()
        st.subheader("Consolidated diagnostics")
        rows = []
        for d in (r["diag"] for r in _ok_results.values()):
            rows.append({
                "Cyclone":      d["name"],
                "Phases":       " → ".join(d["phases"]),
                "N phases":     len(d["phases"]),
                "Gaps":         f"{d['gaps']} ⚠️" if d["gaps"] > 0 else "0",
                "Residual":     "✓" if d["residual"] else "—",
                "Short phases": ", ".join(d["short_phases"]) if d["short_phases"] else "—",
                "Warnings":     f"{len(d['warns'])} ⚠️" if d["warns"] else "0",
            })
        st.dataframe(pd.DataFrame(rows).set_index("Cyclone"), use_container_width=True)

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

    with st.expander("1 · Method overview", expanded=True):
        if _METHOD_IMG.exists():
            st.image(
                str(_METHOD_IMG),
                caption=(
                    "Illustration of CycloPhaser methodology. "
                    "(A) Raw vorticity series. (B) After Lanczos band-pass filtering "
                    "(dashed circles: endpoint artifacts). (C) After first Savitzky-Golay pass. "
                    "(D) After second pass. (E) Identified peaks and valleys. "
                    "(F–J) Sequential detection of intensification, decay, mature, residual, "
                    "and incipient stages. (K) Full life cycle. From de Souza et al. (2024)."
                ),
            )
        st.markdown("""
CycloPhaser identifies distinct phases of cyclone life cycles by analyzing the relative
vorticity time series at the cyclone centre and its first derivative.

**Five stages:**

| Stage | Description |
|---|---|
| **Incipient** | Early development before any identifiable intensification. Detected last (fills unlabelled periods at the series start). |
| **Intensification** | Vorticity intensity increases (more negative in SH) from one peak to a subsequent valley. |
| **Mature** | Interval between a derivative valley and its following derivative peak — cyclone's peak strength. |
| **Decay** | Decrease in vorticity after the mature phase until dissipation. |
| **Residual** | Re-intensification episodes that do not progress to a full mature stage. |

**Pipeline:** Lanczos band-pass filter → Savitzky-Golay smoothing (1× or 2×) → peak/valley detection → phase labelling.

> **Southern Hemisphere convention**: vorticity is negative; more negative = more intense.
> For Northern Hemisphere data, multiply the series by −1 before passing to CycloPhaser.
""")

    with st.expander("2 · Filter and smoothing parameters", expanded=False):
        st.markdown("""
### `use_filter` — Lanczos band-pass filter
Activates spectral filtering. Disabling leaves the raw series and typically yields very noisy detection.

### `cutoff_low` — Low-frequency cutoff (hours)
Maximum period retained. Variability slower than this is suppressed (e.g., seasonal trends).
**Default: 168 h (7 days).**

### `cutoff_high` — High-frequency cutoff (hours)
Minimum period retained. Variability faster than this is suppressed as noise.
**Default: 48 h (2 days).**

### `replace_endpoints_with_lowpass` — Endpoint correction
Replaces the first/last *N* timesteps of the filtered output with a simple low-pass estimate,
correcting Gibbs-effect artifacts at the series edges. **Default: 24 timesteps.** Set to 0 to disable.

### `use_smoothing` / `use_smoothing_twice` — Savitzky-Golay
- `'auto'`: window computed from series length (recommended).
- `'off'`: skip smoothing.
- `'manual'`: set window size explicitly (must be odd).

A second pass (`use_smoothing_twice`) further smooths the already-smoothed curve — useful for hourly data.
Can distort short phases.

### `savgol_polynomial` — Polynomial degree
Degree of the polynomial fitted in each window. Lower (2–3) = more smoothing; higher (4–5) = better
preservation of extrema. **Default: 3.**
""")

    with st.expander("3 · Phase detection thresholds", expanded=False):
        st.markdown("""
All thresholds are **fractions of total series length**, making them resolution-independent.

| Parameter | Default | Description |
|---|---|---|
| `threshold_intensification_length` | 0.075 | Min. duration of an intensification segment. |
| `threshold_decay_length` | 0.075 | Min. duration of a decay segment. |
| `threshold_mature_length` | 0.030 | Min. duration of the mature stage. |
| `threshold_mature_distance` | 0.125 | Max. distance between vorticity minimum and mature segment centre. |
| `threshold_intensification_gap` | 0.075 | Max. gap between consecutive intensification segments for merging. |
| `threshold_decay_gap` | 0.075 | Max. gap between consecutive decay segments for merging. |
| `threshold_incipient_length` | 0.400 | Min. duration of the incipient phase. |
""")

    with st.expander("4 · Known methodological notes", expanded=False):
        st.markdown("""
### Detection pipeline and phase precedence

Functions are called in a **fixed order**:

1. `find_intensification_period`
2. `find_decay_period`
3. `find_mature_stage`
4. `find_residual_period`
5. `post_process_periods` — gap-filling and singleton removal
6. `find_incipient_period` — fills unlabelled timesteps at the start

**Later functions can overwrite earlier ones.** `find_decay_period` (step 2) may overwrite
regions already labelled by `find_intensification_period` (step 1) because both scan the same
peaks/valleys and their intervals can overlap.

### Calibrating thresholds: inspect the final output

Because of this precedence, a threshold may have a smaller effect than expected.
For example, `threshold_intensification_gap` bridges gaps between intensification blocks —
but if `find_decay_period` subsequently relabels those timesteps as decay, the gap-bridging
has no visible effect on the final output.

> **Always inspect the final `periods` column, not the effect of each threshold in isolation.**

### Phase detection lag

The detected *start* of a phase may lag the true onset by up to **15–18 h
(5–6 timesteps at 3-hourly resolution)**. This is an inherent consequence of the
Lanczos + Savgol chain: the smoothed signal requires several timesteps to build
enough amplitude for reliable detection. The lag is most pronounced for **residual**
(re-intensification after decay), where it was consistently 15–18 h across synthetic
test cases.

> When defining search windows for event attribution, allow a margin of at least **18 h**
> around detected phase boundaries.
""")
