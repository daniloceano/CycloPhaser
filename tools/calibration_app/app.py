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

import matplotlib.dates as mdates
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

# Resolved relative to this file (not the Streamlit process's CWD, which varies
# depending on how `streamlit run` is invoked) so "Load all test cyclones" works
# regardless of the working directory the app was launched from.
_CALIBRATION_DATA_DIR = Path(__file__).parent.parent.parent / "tests" / "calibration_data"
# Same resolution strategy for the synthetic suite, which the app can load as an
# alternative track set for validating PHASE DETECTION against known ground truth.
_SYNTHETIC_DIR = Path(__file__).parent.parent.parent / "tests" / "synthetic"
_REPO_ROOT = Path(__file__).parent.parent.parent


@st.cache_data(show_spinner=False)
def _load_synthetic_cases():
    """Materialise tests/synthetic/cases.py in the app's own file format.

    Returns (files, ground_truth, preset, error):
      files        {name: csv_bytes}  — ';'-delimited, column 'min_max_zeta_850',
                   identical in shape to the real calibration CSVs, so every
                   downstream code path (process_vorticity, get_periods, the
                   figure renderers, the ZIP export) works unchanged.
      ground_truth {name: int|None}   — index of the designed incipient boundary
                   (the length of a leading 'Ic' segment), or None when the case
                   has no designed Ic.
      preset       dict               — SYNTHETIC_VALIDATION_PRESET.
      error        str|None           — import failure message, if any.

    The modules are loaded BY FILE PATH under a private package name rather
    than with `import tests.synthetic.cases`, because a plain import of a
    top-level name as generic as `tests` is not safe:

      - `pip install -e .` puts the repo root on sys.path via a .pth file,
        which is processed *inside* site-packages handling, so the repo root
        lands AFTER site-packages;
      - any other project that leaked a top-level `tests` package into the
        same environment then wins the name, and `tests.synthetic` raises
        ModuleNotFoundError even though the repo's own tests/ is right there.

    That is not hypothetical — it is what this loader was first reported
    failing on. Resolving the two files directly removes the dependency on
    sys.path ordering (and on `tests` being importable at all), and leaves
    sys.path untouched for everything else in the process.
    """
    import importlib.util
    import sys
    import types

    cases_py = _SYNTHETIC_DIR / "cases.py"
    if not cases_py.is_file():
        return {}, {}, {}, f"not found: {cases_py}"

    try:
        # A private package whose __path__ is tests/synthetic, so that
        # cases.py's `from .generators import ...` resolves next to it.
        pkg_name = "_cyclophaser_app_synthetic"
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(_SYNTHETIC_DIR)]
        sys.modules[pkg_name] = pkg

        spec = importlib.util.spec_from_file_location(
            f"{pkg_name}.cases", cases_py)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)

        CASES = mod.CASES
        SYNTHETIC_VALIDATION_PRESET = mod.SYNTHETIC_VALIDATION_PRESET
    except Exception as exc:  # missing file, syntax error, anything at import
        return {}, {}, {}, f"{type(exc).__name__}: {exc}"

    files, gt = {}, {}
    for name, case in CASES.items():
        series = case["series"]
        files[name] = series.to_csv(
            sep=";", header=["min_max_zeta_850"], index_label="time"
        ).encode("utf-8")
        segs = case.get("segments") or []
        types = [x["type"] for x in segs]
        gt[name] = segs[0]["n"] if (types and types[0] == "Ic") else None
    return files, gt, dict(SYNTHETIC_VALIDATION_PRESET), None

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
    "replace_endpoints": 0,
    "savgol_poly":       3,
    "boundary_padding":  "reflect",
    "n_cols":            2,
    "thr_int_len":       0.075,
    "thr_dec_len":       0.075,
    "thr_mat_len":       0.030,
    "thr_mat_dist":      0.125,
    "thr_int_gap":       0.075,
    "thr_dec_gap":       0.075,
    "thr_inc_len":       0.400,
    "length_scale":      "global",
    "mature_method":              "derivative",
    "mature_amplitude_fraction":  0.90,
    "extrema_prominence_enabled":     False,
    "extrema_prominence_mode":        "relative",   # 'relative' | 'absolute'
    "extrema_prominence_rel_val":     0.10,         # fraction (relative mode)
    "extrema_prominence_val":         1e-6,         # absolute threshold
    "extrema_distance_enabled":       False,
    "extrema_distance_val":           3,
    "incipient_method":               "geometric",
    "incipient_plateau_tau":          0.20,
    "incipient_plateau_signal":       "derivative",
    "incipient_plateau_crossing":     "single",
    "incipient_plateau_k":            3,
    "decay_tail_enabled":             False,
    "decay_tail_fraction_val":        0.05,   # author's validated reference value
}

_SM_OPTS = ["auto", "off", "manual"]
_BOUNDARY_PADDING_OPTS = ["zero", "reflect", "edge"]

# YAML key → (session_state key, converter)
def _parse_boundary_padding(v) -> str:
    """Validating str converter for boundary_padding — same rationale as
    _parse_length_scale below: rejects anything but the three values
    cyclophaser accepts, so a hand-edited/corrupt YAML value is treated as a
    conversion error rather than silently written into session_state and
    crashing the selectbox on next render."""
    v = str(v)
    if v not in _BOUNDARY_PADDING_OPTS:
        raise ValueError(
            f"boundary_padding must be one of {_BOUNDARY_PADDING_OPTS}, got {v!r}")
    return v


_YAML_FILTER_MAP: dict = {
    "use_filter":                    ("use_filter",        bool),
    "cutoff_low":                    ("cutoff_low",        int),
    "cutoff_high":                   ("cutoff_high",       int),
    "replace_endpoints_with_lowpass": ("replace_endpoints", int),
    "savgol_polynomial":             ("savgol_poly",       int),
    "boundary_padding":              ("boundary_padding",  _parse_boundary_padding),
}
def _parse_length_scale(v) -> str:
    """Validating str converter for length_scale — rejects anything but the
    two values cyclophaser accepts, so a hand-edited/corrupt YAML value is
    treated as a conversion error (caught by the _load_yaml_config try/except
    below) rather than silently written into session_state and crashing the
    widget on next render."""
    v = str(v)
    if v not in ("global", "local"):
        raise ValueError(f"length_scale must be 'global' or 'local', got {v!r}")
    return v


def _parse_mature_method(v) -> str:
    """Validating str converter for mature_method — same rationale as
    _parse_length_scale above: rejects anything but the two values
    cyclophaser accepts, so a hand-edited/corrupt YAML value is treated as a
    conversion error rather than silently written into session_state."""
    v = str(v)
    if v not in ("derivative", "amplitude"):
        raise ValueError(f"mature_method must be 'derivative' or 'amplitude', got {v!r}")
    return v


def _parse_incipient_method(v) -> str:
    """Validating str converter for incipient_method — same rationale as
    _parse_mature_method above."""
    v = str(v)
    if v not in ("geometric", "plateau"):
        raise ValueError(f"incipient_method must be 'geometric' or 'plateau', got {v!r}")
    return v


def _parse_incipient_signal(v) -> str:
    """Validating str converter for incipient_plateau_signal."""
    v = str(v)
    if v not in ("derivative", "vorticity"):
        raise ValueError(
            f"incipient_plateau_signal must be 'derivative' or 'vorticity', got {v!r}")
    return v


def _parse_incipient_crossing(v) -> str:
    """Validating str converter for incipient_plateau_crossing."""
    v = str(v)
    if v not in ("single", "sustained"):
        raise ValueError(
            f"incipient_plateau_crossing must be 'single' or 'sustained', got {v!r}")
    return v


def _parse_prominence_relative(v) -> float:
    """Validating converter for prominence_relative — same rationale as
    _parse_length_scale, but the bound that matters here is the *widget's*:
    the sidebar exposes this as a slider over [0.00, 0.50], so a value outside
    that range cannot be represented and would raise inside st.slider on the
    next render (crashing the app) if written into session_state unchecked.
    Treated as a conversion error instead, and reported to the user."""
    v = float(v)
    if not 0.0 <= v <= 0.50:
        raise ValueError(f"prominence_relative must be within [0.00, 0.50], got {v!r}")
    return v


def _parse_prominence(v) -> float:
    """Validating converter for absolute prominence — the sidebar number_input
    declares min_value=0.0, so a negative value would raise on render. Same
    rationale as _parse_prominence_relative."""
    v = float(v)
    if v < 0.0:
        raise ValueError(f"prominence must be >= 0, got {v!r}")
    return v


def _parse_distance(v) -> int:
    """Validating converter for distance (separation in timesteps).

    int(float(...)) because _build_yaml historically coerced every numeric phase
    param through float(), so files exported before that was fixed carry e.g.
    `3.0`; int("3.0") would raise. The lower bound mirrors the sidebar
    number_input's min_value=2 — same rationale as _parse_prominence_relative."""
    v = int(float(v))
    if v < 2:
        raise ValueError(f"distance must be >= 2 timesteps, got {v!r}")
    return v


def _parse_decay_tail_amplitude_fraction(v) -> float:
    """Validating converter for decay_tail_amplitude_fraction — same rationale
    as _parse_prominence_relative: the sidebar slider is bounded to
    [0.01, 0.50] (cyclophaser itself requires (0, 1], but the widget's own
    range is the practical bound that matters here — a value outside it would
    raise inside st.slider on the next render)."""
    v = float(v)
    if not 0.01 <= v <= 0.50:
        raise ValueError(f"decay_tail_amplitude_fraction must be within [0.01, 0.50], got {v!r}")
    return v


# length_scale and mature_method are bundled into phase_params (they are
# get_periods()/determine_periods() phase-detection arguments, not
# filter/smoothing ones), but — unlike every other entry here — they are
# string enums, not numeric thresholds, hence the dedicated validating
# converters instead of `float`.
_YAML_PHASE_MAP: dict = {
    "threshold_intensification_length": ("thr_int_len",  float),
    "threshold_intensification_gap":    ("thr_int_gap",  float),
    "threshold_mature_distance":        ("thr_mat_dist", float),
    "threshold_mature_length":          ("thr_mat_len",  float),
    "threshold_decay_length":           ("thr_dec_len",  float),
    "threshold_decay_gap":              ("thr_dec_gap",  float),
    "threshold_incipient_length":       ("thr_inc_len",  float),
    "length_scale":                     ("length_scale", _parse_length_scale),
    "mature_method":                    ("mature_method", _parse_mature_method),
    "mature_amplitude_fraction":        ("mature_amplitude_fraction", float),
    "incipient_method":                 ("incipient_method", _parse_incipient_method),
    "incipient_plateau_tau":            ("incipient_plateau_tau", float),
    "incipient_plateau_signal":         ("incipient_plateau_signal", _parse_incipient_signal),
    "incipient_plateau_crossing":       ("incipient_plateau_crossing", _parse_incipient_crossing),
    "incipient_plateau_k":              ("incipient_plateau_k", lambda v: int(float(v))),
}
# The extrema-filtering parameters (prominence / prominence_relative / distance)
# and decay_tail_amplitude_fraction are NOT in _YAML_PHASE_MAP: each maps to a
# *group* of session_state keys (enabled flag + mode/value), not to a single
# widget, so they get the same dedicated handling that use_smoothing/
# use_smoothing_twice already get below. They are also OPTIONAL on import:
# _build_yaml only writes a key whose value is not None, so a YAML exported
# with a given check disabled (or prominence filtering in relative mode)
# legitimately lacks that key. Hence they are recognised for the "unknown key"
# check (_KNOWN_PHASE_YAML_KEYS) but excluded from the "missing key" check
# (_REQUIRED_PHASE_YAML_KEYS), which would otherwise warn about a mode that
# simply wasn't in use.
_OPTIONAL_PHASE_YAML_KEYS = {"prominence", "prominence_relative", "distance",
                              "decay_tail_amplitude_fraction",
                              # The incipient_* keys are optional for the same
                              # backward-compatibility reason as boundary_padding
                              # below: every YAML exported before the plateau
                              # method existed legitimately lacks them and must
                              # import cleanly, falling back to the
                              # "geometric" defaults without a spurious
                              # "missing key" warning.
                              "incipient_method", "incipient_plateau_tau",
                              "incipient_plateau_signal",
                              "incipient_plateau_crossing",
                              "incipient_plateau_k"}

# boundary_padding is OPTIONAL on import for the same reason as the optional
# phase keys above, but for a backward-compatibility reason rather than a
# "mode wasn't in use" one: every YAML exported before the option existed
# legitimately lacks the key, and such a file must import cleanly and fall back
# to the default ("zero") without a spurious "missing key" warning. It is still
# recognised for the "unknown key" check.
_OPTIONAL_FILTER_YAML_KEYS = {"boundary_padding"}

# phase_params entries that are string enums, not numbers: exported as-is
# rather than coerced through float().
_PHASE_ENUM_KEYS = ("length_scale", "mature_method", "incipient_method",
                    "incipient_plateau_signal", "incipient_plateau_crossing")

_KNOWN_FILTER_YAML_KEYS = set(_YAML_FILTER_MAP) | {"use_smoothing", "use_smoothing_twice"}
_REQUIRED_FILTER_YAML_KEYS = _KNOWN_FILTER_YAML_KEYS - _OPTIONAL_FILTER_YAML_KEYS
_KNOWN_PHASE_YAML_KEYS  = set(_YAML_PHASE_MAP) | _OPTIONAL_PHASE_YAML_KEYS
_REQUIRED_PHASE_YAML_KEYS = set(_YAML_PHASE_MAP)


# ── Pure helper functions ─────────────────────────────────────────────────────────
def _normalize(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


def _format_date_axis_mmdd(ax) -> None:
    """Simplify a non-compact figure's x-axis to 'mm-dd' (drops the hour),
    which is legible at the larger sizes used for n_cols <= 3. Applied via
    the ax object plot_all_periods draws onto, so cyclophaser's own plotting
    code (cyclophaser/plots.py) is not touched."""
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))


def _reset() -> None:
    for k in _DEFAULTS:
        st.session_state.pop(k, None)
    # Clear YAML import state so a still-loaded file can be re-imported after reset
    st.session_state.pop("_yaml_import_hash", None)
    st.session_state.pop("_yaml_import_result", None)
    # Deliberately does NOT touch bad-case marks (see _clear_bad_marks): resetting
    # filter/threshold parameters to try a different calibration shouldn't wipe an
    # evaluation in progress. Marks are cleared only via their own button.


# Bad-case marks live directly in per-cyclone widget session_state keys
# ("badcase__<cyclone_name>") rather than in a separate mirrored set/list, so the
# checkbox widgets are the single source of truth and can't drift out of sync with
# it. This prefix must not collide with any other session_state key used by the app.
_BAD_CASE_KEY_PREFIX = "badcase__"


def _clear_bad_marks() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith(_BAD_CASE_KEY_PREFIX):
            del st.session_state[k]


def _compute_evaluation(cyclone_names) -> dict:
    """Bad-case evaluation summary for the currently loaded cyclone set.

    Percent is computed against `cyclone_names` (what's loaded *now*), matching
    the footer's "N / total loaded" framing -- a mark left over from a
    previously loaded cyclone that isn't in `cyclone_names` this run simply
    doesn't count here (it still exists in session_state until cleared, so it
    reappears in the count if that cyclone is loaded again).
    """
    names = list(cyclone_names)
    bad = sorted(n for n in names if st.session_state.get(f"{_BAD_CASE_KEY_PREFIX}{n}", False))
    total = len(names)
    percent = round(100 * len(bad) / total, 1) if total else 0.0
    return {
        "total_cyclones": total,
        "bad_cases_count": len(bad),
        "bad_cases_percent": percent,
        "bad_cases": bad,
    }


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
        [f"filter_params.{k}" for k in _REQUIRED_FILTER_YAML_KEYS if k not in fp]
        + [f"phase_params.{k}" for k in _REQUIRED_PHASE_YAML_KEYS if k not in pp]
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

    # Extrema filtering (prominence / prominence_relative / distance) — each is a
    # *group* of session_state keys (enabled + mode + value), so it cannot go
    # through _YAML_PHASE_MAP's single-key mapping; see _EXTREMA_YAML_KEYS above.
    #
    # Absence is meaningful, not missing data: _build_yaml omits any parameter
    # whose value is None, and the two prominence modes are mutually exclusive,
    # so a file carrying neither key describes prominence filtering that was
    # switched OFF. The enabled flags are therefore set from the file in BOTH
    # directions rather than only being turned on — otherwise importing a
    # "filtering off" YAML into a session that currently has filtering on would
    # silently keep the session's filter and reproduce the wrong calibration.
    # prominence_relative wins if a hand-edited file somehow carries both, matching
    # the sidebar radio's single-mode model (relative is its default).
    if "prominence_relative" in pp:
        try:
            st.session_state["extrema_prominence_rel_val"] = _parse_prominence_relative(
                pp["prominence_relative"])
            st.session_state["extrema_prominence_mode"]    = "relative"
            st.session_state["extrema_prominence_enabled"] = True
            count += 1
        except (ValueError, TypeError):
            ignored.append("phase_params.prominence_relative (conversion error)")
    elif "prominence" in pp:
        try:
            st.session_state["extrema_prominence_val"]     = _parse_prominence(pp["prominence"])
            st.session_state["extrema_prominence_mode"]    = "absolute"
            st.session_state["extrema_prominence_enabled"] = True
            count += 1
        except (ValueError, TypeError):
            ignored.append("phase_params.prominence (conversion error)")
    else:
        st.session_state["extrema_prominence_enabled"] = False

    if "distance" in pp:
        try:
            st.session_state["extrema_distance_val"]     = _parse_distance(pp["distance"])
            st.session_state["extrema_distance_enabled"] = True
            count += 1
        except (ValueError, TypeError):
            ignored.append("phase_params.distance (conversion error)")
    else:
        st.session_state["extrema_distance_enabled"] = False

    # decay_tail_amplitude_fraction — same enabled+value group pattern as the
    # extrema block above, and same reasoning for setting `enabled` in BOTH
    # directions (absence means the file describes this check switched OFF).
    if "decay_tail_amplitude_fraction" in pp:
        try:
            st.session_state["decay_tail_fraction_val"] = _parse_decay_tail_amplitude_fraction(
                pp["decay_tail_amplitude_fraction"])
            st.session_state["decay_tail_enabled"] = True
            count += 1
        except (ValueError, TypeError):
            ignored.append("phase_params.decay_tail_amplitude_fraction (conversion error)")
    else:
        st.session_state["decay_tail_enabled"] = False

    # 'evaluation' is optional (older YAMLs, including ones exported before this
    # feature existed, simply don't have it — importing those must not error; see
    # the "missing required sections" check above, which only covers filter_params/
    # phase_params, not this). When present, RESTORES the bad-case marks: clears
    # every existing badcase__* key first, then sets the imported list, so the
    # session's marks become an exact snapshot of what's in the file (matching how
    # every other imported value in this function *replaces* the current one,
    # rather than merging with it) -- useful for resuming a saved evaluation
    # instead of leaving stale marks from whatever was in the current session.
    if "evaluation" in doc:
        ev = doc["evaluation"]
        bad_list = ev.get("bad_cases") if isinstance(ev, dict) else None
        if isinstance(bad_list, list):
            try:
                bad_names = [str(n) for n in bad_list]
            except Exception:
                ignored.append("evaluation.bad_cases (conversion error)")
            else:
                _clear_bad_marks()
                for name in bad_names:
                    st.session_state[f"{_BAD_CASE_KEY_PREFIX}{name}"] = True
                count += len(bad_names)
        elif bad_list is not None:
            ignored.append("evaluation.bad_cases (not a list)")

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
            "boundary_padding":              str(boundary_padding),
        },
        # length_scale and mature_method are string enums ("global"/"local",
        # "derivative"/"amplitude"), not numeric thresholds — exported as-is
        # rather than coerced through float(). `distance` is a count of
        # timesteps and is exported as int so it round-trips as `3` rather than
        # the `3.0` a blanket float() produced (the importer tolerates both).
        # Note every key here is omitted when its value is None, so which
        # extrema keys appear also encodes whether that filter was enabled —
        # see the extrema-import block in _load_yaml_config.
        "phase_params": {
            **{k: (int(v) if k in ("distance", "incipient_plateau_k") else float(v))
               for k, v in _PHASE_PARAMS.items()
               if v is not None and k not in _PHASE_ENUM_KEYS},
            **{k: _PHASE_PARAMS[k] for k in _PHASE_ENUM_KEYS},
        },
        "evaluation": _compute_evaluation(cyclone_names),
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
def _render_periods_png(
    file_bytes: bytes,
    use_filter, cutoff_low, cutoff_high,
    use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
    boundary_padding,
    phase_params_tuple: tuple,
    name: str,
    figsize: tuple,
    show_title: bool,
    gt_boundary_iso: str | None = None,
) -> bytes:
    """Render a plot_all_periods PNG at the given figsize. Cached per unique
    (file, filter params, phase params, name, figsize, show_title) combination
    -- used both for the CSV/PNG/ZIP export (figsize=(12,5), show_title=True)
    and for on-screen display at n_cols in {1, 2, 3} (figsize=_FIGSIZES[n_cols]),
    via st.image() instead of st.pyplot() so a rerun that doesn't change filter
    or phase params (e.g. a bad-case-mark checkbox click) is a cache hit instead
    of a full re-render of every loaded cyclone's figure."""
    df_result, periods_dict, _ = _run_get_periods(
        file_bytes, use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
        boundary_padding,
        phase_params_tuple,
    )
    vort, _ = _run_process_vorticity(
        file_bytes, use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
        boundary_padding,
    )
    fig, ax = plt.subplots(figsize=figsize)
    try:
        plot_all_periods(periods_dict, df_result, ax=ax, vorticity=vort)
        # Ground-truth incipient boundary (synthetic cases only): the designed
        # end of the leading 'Ic' segment. Same green dashed convention as the
        # measurement figures in research/incipient_plateau/.
        if gt_boundary_iso:
            ax.axvline(pd.Timestamp(gt_boundary_iso), color="#00a000",
                       lw=2.0, ls=":", zorder=6, label="ground truth Ic")
        _format_date_axis_mmdd(ax)
    except Exception:
        pass
    if show_title:
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

# Compact-grid (n_cols >= 4) line widths. Only two series are plotted (see
# _plot_compact): 'raw' (zeta, the actual input data) and 'smoothed2'
# (vorticity_smoothed2, the series phase detection is actually run against).
# filtered_vorticity and vorticity_smoothed — the two intermediate pipeline
# stages between them — were dropped from this view (see _plot_compact's
# docstring for why): with four thick lines in a 3.5x2.5in figure the result
# was a blur, and the pair that actually answers "does this look right at a
# glance" is raw-vs-what-the-algorithm-sees, not every intermediate stage.
# Widths still scale up as n_cols grows (smaller canvas -> proportionally
# thicker lines needed to stay legible after Streamlit renders it reduced).
_COMPACT_LW = {
    4: {"raw": 1.3, "smoothed2": 1.6},
    5: {"raw": 1.5, "smoothed2": 1.8},
    6: {"raw": 1.7, "smoothed2": 2.0},
}

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


def _plot_compact(cyclone_name: str, periods_dict: dict, vort, n_cols: int) -> plt.Figure:
    """Dense-grid figure (n_cols >= 4): raw vorticity + phase shading, no labels/titles.

    Plots only 'zeta' (raw input data) and 'vorticity_smoothed2' (the series
    phase detection actually runs against) — not the two intermediate
    pipeline stages (filtered_vorticity, vorticity_smoothed) that the
    non-compact/step-by-step views show. At n_cols>=4 figure sizes (down to
    3.5x2.5in), four overlapping thick lines were unreadable; the raw-vs-
    detection-input pair is what a quick "does this look right" glance over
    dozens of cyclones actually needs.

    zeta and vorticity_smoothed2 are plotted on separate y-axes (twinx) since
    the raw series' noise inflates its range well beyond the smoothed one's
    (checked empirically: ~2-3x wider on real tracks) — sharing one axis would
    flatten the smoothed curve near-invisible. Because twinx's second axis
    renders on top of the first by default, 'zeta' is explicitly promoted
    in front of vorticity_smoothed2 (ax.patch hidden + ax's zorder raised
    above ax2's): without this, the raw line was getting hidden underneath
    the smoothed one wherever they nearly coincide (i.e. across most of a
    well-behaved life cycle), which is what actually made the raw series
    look absent even though it was technically being drawn.
    """
    fig, ax = plt.subplots(figsize=_FIGSIZES[n_cols])
    lw = _COMPACT_LW.get(n_cols, _COMPACT_LW[4])
    phases_list = list(periods_dict.items())
    for i, (ph, (st_, en)) in enumerate(phases_list):
        right = phases_list[i + 1][1][0] if i + 1 < len(phases_list) else en
        ax.axvspan(st_, right, alpha=0.35, color=PHASE_COLORS.get(_normalize(ph), "#cccccc"))

    ax2 = ax.twinx()
    ax2.plot(vort.time, vort["vorticity_smoothed2"], color="#e63946", lw=lw["smoothed2"])
    ax.plot(vort.time, vort["zeta"], color="dimgray", lw=lw["raw"], alpha=0.9)
    ax.patch.set_visible(False)
    ax.set_zorder(ax2.get_zorder() + 1)

    for a in (ax, ax2):
        a.set_xlabel(""); a.set_ylabel(""); a.set_title("")
        a.tick_params(left=False, right=False, bottom=False,
                      labelleft=False, labelright=False, labelbottom=False)
    fig.tight_layout(pad=0.3)
    return fig


@st.cache_data(
    hash_funcs={bytes: lambda b: hashlib.md5(b).hexdigest()},
    show_spinner=False,
)
def _render_compact_png(
    file_bytes: bytes,
    use_filter, cutoff_low, cutoff_high,
    use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
    boundary_padding,
    phase_params_tuple: tuple,
    name: str,
    n_cols: int,
) -> bytes:
    """Cached counterpart of _plot_compact, for the dense grid (n_cols >= 4).
    Returned as PNG bytes and displayed via st.image() instead of st.pyplot()
    for the same reason as _render_periods_png (avoid redrawing every loaded
    cyclone's figure on every rerun, e.g. every bad-case-mark checkbox click)."""
    df_result, periods_dict, _ = _run_get_periods(
        file_bytes, use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
        boundary_padding,
        phase_params_tuple,
    )
    vort, _ = _run_process_vorticity(
        file_bytes, use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
        boundary_padding,
    )
    fig = _plot_compact(name, periods_dict, vort, n_cols)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


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


# ── Cached vorticity processing + phase detection ─────────────────────────────────
# Both steps are cached, split into two separate @st.cache_data functions so that a
# rerun that doesn't change filter/smoothing params (e.g. clicking "Mark as bad", or
# any other widget that isn't a filter/threshold slider) reuses the SAME cached
# results for every loaded cyclone instead of recomputing Lanczos/Savgol filtering
# and phase detection from scratch on every single interaction. Streamlit reruns the
# whole script on any widget click regardless of what changed; without this caching,
# that rerun redid this work for all ~51 test-bank cyclones every time, which is what
# made marking cyclones as bad (or any other click) feel slow -- the mark itself, and
# the evaluation summary it feeds, are cheap; the full-script rerun around them was not.
@st.cache_data(
    show_spinner="Processing vorticity…",
    hash_funcs={bytes: lambda b: hashlib.md5(b).hexdigest()},
)
def _run_process_vorticity(
    file_bytes, use_filter, cutoff_low, cutoff_high,
    use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
    boundary_padding,
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
            boundary_padding=boundary_padding,
        )
    return vort, [str(w.message) for w in caught if issubclass(w.category, UserWarning)]


@st.cache_data(
    show_spinner=False,
    hash_funcs={bytes: lambda b: hashlib.md5(b).hexdigest()},
)
def _run_get_periods(
    file_bytes, use_filter, cutoff_low, cutoff_high,
    use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
    boundary_padding,
    phase_params_tuple: tuple,
):
    """Cached phase detection. Warnings are captured and returned (not just caught by
    an outer `with warnings.catch_warnings()` at the call site) because on a cache
    HIT the function body -- including the warnings.warn() calls inside get_periods --
    never actually runs again; they only fire once, when the result is first computed,
    so they must be part of the cached return value to still be visible afterwards."""
    vort, _ = _run_process_vorticity(
        file_bytes, use_filter, cutoff_low, cutoff_high,
        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
        boundary_padding,
    )
    phase_params = dict(phase_params_tuple)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df_result = get_periods(vorticity=vort, plot=False, plot_steps=False, **phase_params)
    phase_warns = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
    periods_dict = periods_to_dict(df_result)
    return df_result, periods_dict, phase_warns


# ── Synthetic-preset application ─────────────────────────────────────────────────
# Must run BEFORE the sidebar widgets are constructed: Streamlit reads a widget's
# session_state value at construction time, so writing the preset after the
# sidebar has rendered would only take effect one rerun later (and would then
# fight the user's own edits). The checkbox that flips this lives further down
# the page, but its value is already in session_state by the time this reruns.
#
# The preset is applied ONLY on the False->True transition, so the pre-processing
# controls stay fully editable afterwards -- it is a starting point for the
# synthetic validation, not a lock.
_SYNTH_PRESET_WIDGETS = {
    "use_filter":        False,
    "sm_mode":           "off",
    "sm2_mode":          "off",
    "replace_endpoints": 0,
    "savgol_poly":       3,
    "boundary_padding":  "reflect",
    "cutoff_low":        168,
    "cutoff_high":       48,
}
_synth_loaded = bool(st.session_state.get("load_synthetic_cases", False))
if _synth_loaded and not st.session_state.get("_synth_preset_applied", False):
    for _k, _v in _SYNTH_PRESET_WIDGETS.items():
        st.session_state[_k] = _v
    st.session_state["_synth_preset_applied"] = True
elif not _synth_loaded:
    st.session_state.pop("_synth_preset_applied", None)


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
    st.button(
        "🗑 Clear bad-case marks", on_click=_clear_bad_marks, use_container_width=True,
        help=(
            "Unmarks every cyclone currently flagged as a bad detection result. "
            "Kept separate from 'Reset to defaults' on purpose: trying different "
            "filter/threshold values shouldn't wipe an evaluation in progress."
        ),
    )
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
    boundary_padding = st.selectbox(
        "Boundary padding",
        options=_BOUNDARY_PADDING_OPTS,
        index=_BOUNDARY_PADDING_OPTS.index(_DEFAULTS["boundary_padding"]),
        key="boundary_padding",
        help=(
            "How the series is extended beyond its own ends before the Lanczos "
            "convolution.\n\n"
            "**reflect** (default) — pads with the reflection of the series. "
            "Takes the normalised |dz| at the first sample from a median 0.95 down "
            "to 0.42 on the 51-track set.\n\n"
            "**zero** — the pre-fix behaviour: the kernel sees zeros "
            "outside the series. Vorticity has a non-zero floor, so this injects a "
            "spurious deepening ramp worth a median 74% of the cyclone's amplitude "
            "over roughly 48% of every series (the kernel is ~half the series long). "
            "Pass it to reproduce results from before this default changed.\n\n"
            "**edge** — pads with the edge value repeated. Between the two "
            "(median 0.50), changes marginally fewer phase sequences.\n\n"
            "Changing this alters the smoothed signal near the boundaries, so a "
            "calibrated parameter set must be re-validated before it is trusted "
            "in a new mode. Only has an effect when the Lanczos filter is on."
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
            "Replace endpoints with lowpass (timesteps) — DEPRECATED", 0, 48, step=1,
            value=_DEFAULTS["replace_endpoints"], key="replace_endpoints",
            help=(
                "**Deprecated — leave at 0.** Replaces the first and last 5% of the filtered "
                "series with a simple low-pass estimate. It was a palliative for the Lanczos "
                "zero-padding boundary artifact, which `boundary_padding` now fixes at its "
                "source — and it applies the same zero-padded convolution internally.\n\n"
                "Combined with `boundary_padding=reflect` it is actively harmful: both filters "
                "carry full amplitude at the edge, so the 5% splice becomes a visible step. "
                "Measured: **28 of 51** calibration tracks opened with a spurious `decay` phase "
                "with this at 24, against **0/51** with it at 0.\n\n"
                "Default: 0 (was 24 up to v2.0.0)."
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
    length_scale = st.radio(
        "Threshold scale",
        options=["global", "local"],
        index=["global", "local"].index(_DEFAULTS["length_scale"]),
        format_func=lambda x: "Global (default, v2.0.0 behaviour)" if x == "global" else "Local (per-cycle)",
        key="length_scale",
        horizontal=True,
        help=(
            "Controls what length the five sliders below (and the two in "
            "'Advanced thresholds') are fractions *of*. "
            "**global** (default): thresholds are measured against the whole "
            "series length — unchanged from v2.0.0. "
            "**local**: thresholds are measured against each individual life "
            "cycle's own span instead, which resolves tracks containing "
            "multiple asymmetric cycles — a short second cycle would "
            "otherwise have every one of its phases rejected by thresholds "
            "sized for a much larger first cycle, collapsing it into a "
            "single 'residual' block. Does not affect 'Mature distance' or "
            "'Min. incipient length' below, which were already local. "
            "Switching this does not re-run the Lanczos/Savgol filtering — "
            "only phase detection is re-computed."
        ),
    )
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
    mature_method = st.radio(
        "Mature stage method",
        options=["derivative", "amplitude"],
        index=["derivative", "amplitude"].index(_DEFAULTS["mature_method"]),
        format_func=lambda x: "Derivative (default, v2.0.0 behaviour)" if x == "derivative" else "Amplitude (opt-in)",
        key="mature_method",
        horizontal=True,
        help=(
            "Controls how the mature-stage window around each vorticity minimum is sized. "
            "**derivative** (default): a fixed proportion ('Mature distance' below) of the "
            "time distance to the neighbouring vorticity peaks — unchanged from v2.0.0. "
            "**amplitude** (opt-in): the contiguous stretch of vorticity around the minimum "
            "that stays within a fraction of the cycle's own peak-to-valley amplitude on each "
            "side ('Mature amplitude fraction' below). Anchors directly on the vorticity value "
            "rather than on smoothed-derivative extrema, which can lag the true minimum and "
            "displace the 'derivative' window forward on some real cyclones. "
            "'Min. mature length' and 'Mature distance' below have NO EFFECT when 'amplitude' "
            "is selected — that minimum-duration floor was calibrated for 'derivative' and was "
            "observed to discard well-centred amplitude windows for being narrow, which is a "
            "physically meaningful outcome there, not a defect to filter out."
        ),
    )
    _mature_is_derivative = mature_method == "derivative"

    thr_mat_len = st.slider(
        "Min. mature length", 0.005, 0.15, step=0.005,
        value=_DEFAULTS["thr_mat_len"], key="thr_mat_len",
        disabled=not _mature_is_derivative,
        help=(
            "Minimum length of the mature phase (peak intensity period) as a fraction "
            "of total series length. The mature stage spans the period around the vorticity "
            "minimum. Very high values may eliminate the mature stage of rapidly evolving "
            "cyclones; very low values can generate spurious peaks."
            + ("" if _mature_is_derivative else
               " **Inactive**: has no effect when Mature stage method = 'amplitude'.")
        ),
    )
    thr_mat_dist = st.slider(
        "Mature distance", 0.05, 0.30, step=0.005,
        value=_DEFAULTS["thr_mat_dist"], key="thr_mat_dist",
        disabled=not _mature_is_derivative,
        help=(
            "Maximum allowed distance between the intensity peak (vorticity minimum) and "
            "the centre of the mature segment, as a fraction of total length. "
            "Controls how close to the true intensity maximum the mature phase must be located. "
            "Higher values allow offset peaks; lower values are more strict."
            + ("" if _mature_is_derivative else
               " **Inactive**: only used when Mature stage method = 'derivative'.")
        ),
    )
    if not _mature_is_derivative:
        mature_amplitude_fraction = st.slider(
            "Mature amplitude fraction", 0.05, 1.00, step=0.01,
            value=_DEFAULTS["mature_amplitude_fraction"], key="mature_amplitude_fraction",
            help=(
                "Fraction of each side's peak-to-valley vorticity amplitude a timestep must "
                "still reach to count as mature. Higher values (closer to 1) yield a narrower "
                "window tightly centred on the vorticity minimum; lower values widen it toward "
                "the neighbouring peaks. No minimum-duration floor applies in this mode — a "
                "narrow window is accepted on its own terms rather than discarded."
            ),
        )
    else:
        mature_amplitude_fraction = _DEFAULTS["mature_amplitude_fraction"]

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
        incipient_method = st.radio(
            "incipient_method",
            options=["geometric", "plateau"],
            index=["geometric", "plateau"].index(_DEFAULTS["incipient_method"]),
            key="incipient_method",
            horizontal=True,
            format_func=lambda x: (
                "Geometric (default)" if x == "geometric" else "Plateau (opt-in)"
            ),
            help=(
                "'geometric' is the historical rule: the incipient phase ends "
                "`Min. incipient length` of the way to the next dz extremum. "
                "'plateau' instead ends it where the normalised slope first "
                "reaches tau — the end of the initial low-slope plateau.\n\n"
                "**Caveat (measured on the 51-track set):** the plateau rule is only "
                "meaningful once the t0 boundary artifact is controlled. With the "
                "Lanczos filter off, or with derivative smoothing active, the first "
                "sample already exceeds any usable tau on most tracks and the rule "
                "degenerates to 'no incipient phase'."
            ),
        )
        if incipient_method == "geometric":
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
        else:
            # Kept out of the widget tree (not just disabled) under 'plateau' for
            # the same reason threshold_mature_length is hidden under
            # mature_method='amplitude': the parameter is genuinely ignored, and
            # a live slider that does nothing reads as a bug during calibration.
            thr_inc_len = st.session_state.get("thr_inc_len", _DEFAULTS["thr_inc_len"])
            st.caption(
                "`Min. incipient length` is ignored under `incipient_method='plateau'` "
                "(as `Min. mature length` is under `mature_method='amplitude'`)."
            )

        incipient_plateau_tau = st.slider(
            "Plateau tau (normalised slope)", 0.01, 0.60, step=0.01,
            value=_DEFAULTS["incipient_plateau_tau"], key="incipient_plateau_tau",
            disabled=incipient_method != "plateau",
            help=(
                "The incipient phase is the leading stretch where the normalised "
                "slope stays below this value. Measured reference points on the "
                "51-track set under the author's calibration: tau=0.15 is the "
                "smallest value that yields a non-empty plateau on all 51 tracks; "
                "the resulting plateau is short (median 1-3 timesteps)."
            ),
        )
        incipient_plateau_signal = st.radio(
            "Plateau signal",
            options=["derivative", "vorticity"],
            index=["derivative", "vorticity"].index(_DEFAULTS["incipient_plateau_signal"]),
            key="incipient_plateau_signal", horizontal=True,
            disabled=incipient_method != "plateau",
            help=(
                "'derivative': |dz/dt| of the smoothed series — the exact array the "
                "stage detection consumes, so the criterion sees what the detector "
                "sees, but it inherits the filter's edge artifact. "
                "'vorticity': |d(zeta)/dt| computed on the UNFILTERED input, immune "
                "to filter edge artifacts but noisier."
            ),
        )
        incipient_plateau_crossing = st.radio(
            "Plateau crossing",
            options=["single", "sustained"],
            index=["single", "sustained"].index(_DEFAULTS["incipient_plateau_crossing"]),
            key="incipient_plateau_crossing", horizontal=True,
            disabled=incipient_method != "plateau",
            help=(
                "'single': the plateau ends at the first sample reaching tau. "
                "'sustained': it ends at the start of the first run of k consecutive "
                "samples at or above tau, so an isolated noise spike inside the "
                "plateau does not cut it short. If no such run exists anywhere in the "
                "series, no incipient phase is created."
            ),
        )
        if incipient_plateau_crossing == "sustained":
            incipient_plateau_k = st.number_input(
                "Plateau k (consecutive steps)", min_value=1, max_value=25, step=1,
                value=_DEFAULTS["incipient_plateau_k"], key="incipient_plateau_k",
                disabled=incipient_method != "plateau",
                help="Number of consecutive samples at or above tau required by "
                     "'sustained'. Ignored for 'single'.",
            )
        else:
            incipient_plateau_k = st.session_state.get(
                "incipient_plateau_k", _DEFAULTS["incipient_plateau_k"])

    st.divider()
    # --- Extrema filtering (optional) ---
    st.header("Extrema Filtering")
    with st.expander("Prominence & distance filtering (advanced)", expanded=False):
        st.caption(
            "Optional post-processing for the detected peaks/valleys. "
            "Boundary extrema (first and last points) are always preserved. "
            "Leave disabled to use the default CycloPhaser behaviour."
        )
        _prom_enabled = st.checkbox(
            "Enable prominence filter", value=_DEFAULTS["extrema_prominence_enabled"],
            key="extrema_prominence_enabled",
            help=(
                "Remove interior extrema that are not sufficiently prominent. "
                "Boundary extrema are always preserved regardless of this setting."
            ),
        )
        if _prom_enabled:
            _prom_mode = st.radio(
                "Prominence mode",
                options=["relative", "absolute"],
                index=0,
                format_func=lambda x: (
                    "Relative (recommended)" if x == "relative" else "Absolute"
                ),
                key="extrema_prominence_mode",
                horizontal=True,
                help=(
                    "Relative adapts to each cyclone's intensity — no re-tuning needed "
                    "across weak and strong systems. Absolute uses a fixed threshold in "
                    "the same units as the smoothed vorticity."
                ),
            )
            if _prom_mode == "relative":
                _rel_val = st.slider(
                    "Fraction of dominant prominence",
                    min_value=0.00, max_value=0.50, step=0.01,
                    value=_DEFAULTS["extrema_prominence_rel_val"],
                    key="extrema_prominence_rel_val",
                    help=(
                        "Fraction of the cyclone's strongest extremum's prominence; "
                        "adapts to each cyclone's intensity (recommended mode). "
                        "E.g.: 0.10 keeps only extrema with prominence ≥ 10% "
                        "of the dominant extremum."
                    ),
                )
                extrema_prominence          = None
                extrema_prominence_relative = float(_rel_val)
            else:
                _abs_val = st.number_input(
                    "Absolute prominence threshold", min_value=0.0,
                    value=_DEFAULTS["extrema_prominence_val"],
                    format="%.2e", key="extrema_prominence_val",
                    help=(
                        "Minimum prominence in the same units as the smoothed vorticity "
                        "series. Requires re-tuning for datasets of different magnitudes."
                    ),
                )
                extrema_prominence          = float(_abs_val)
                extrema_prominence_relative = None
        else:
            extrema_prominence          = None
            extrema_prominence_relative = None

        _dist_enabled = st.checkbox(
            "Enable distance filter", value=_DEFAULTS["extrema_distance_enabled"],
            key="extrema_distance_enabled",
            help=(
                "If enabled, same-type extrema closer than this many timesteps are merged, "
                "keeping the one with higher prominence. Boundary extrema always count toward "
                "the exclusion radius."
            ),
        )
        if _dist_enabled:
            _dist_val = st.number_input(
                "Minimum distance (timesteps)", min_value=2, step=1,
                value=_DEFAULTS["extrema_distance_val"], key="extrema_distance_val",
                help="Minimum separation (in timesteps) between two same-type extrema.",
            )
            extrema_distance = int(_dist_val)
        else:
            extrema_distance = None

    st.divider()
    # --- Decay-tail extension (optional) ---
    st.header("Decay-Tail Handling")
    with st.expander("Extend decay over a flat tail (advanced)", expanded=False):
        st.caption(
            "Compensates for an artifact of the prominence filter above: on a "
            "single-cycle series, peaks and valleys are scored against SEPARATE "
            "populations, so the largest interior peak always survives "
            "prominence_relative filtering by construction — even when its "
            "prominence is negligible — while the valley of the same ripple is "
            "correctly rejected. This 'orphan' peak (no surviving valley after it) "
            "truncates decay early; the flat tail left behind is then labelled "
            "'residual' even though nothing in the vorticity indicates a genuine "
            "re-intensification. Leave disabled to use the default CycloPhaser "
            "behaviour."
        )
        _decay_tail_enabled = st.checkbox(
            "Extend decay over a flat/plateau tail", value=_DEFAULTS["decay_tail_enabled"],
            key="decay_tail_enabled",
            help=(
                "If the tail right after the last decay block contains no "
                "re-deepening larger than the fraction below (relative to the "
                "cycle's own peak-to-valley amplitude), it is labelled 'decay' "
                "instead of 'residual'. Never touches z_peaks_valleys or any "
                "detected extrema, so the mature window is unaffected."
            ),
        )
        if _decay_tail_enabled:
            _decay_tail_val = st.slider(
                "Fraction of cycle amplitude",
                min_value=0.01, max_value=0.50, step=0.01,
                value=_DEFAULTS["decay_tail_fraction_val"],
                key="decay_tail_fraction_val",
                help=(
                    "Author's validated reference value is 0.05, confirmed safe "
                    "over (0.0356, 0.0651] on the 51-track calibration set: below "
                    "that, some spurious tails aren't absorbed; above it, genuine "
                    "re-intensifications start being swallowed. A re-deepening at "
                    "or above this fraction is left for the catch-all rule to mark "
                    "'residual', as before."
                ),
            )
            decay_tail_amplitude_fraction = float(_decay_tail_val)
        else:
            decay_tail_amplitude_fraction = None

# Bundle phase params
_PHASE_PARAMS = dict(
    threshold_intensification_length=thr_int_len,
    threshold_intensification_gap=thr_int_gap,
    threshold_mature_distance=thr_mat_dist,
    threshold_mature_length=thr_mat_len,
    threshold_decay_length=thr_dec_len,
    threshold_decay_gap=thr_dec_gap,
    threshold_incipient_length=thr_inc_len,
    prominence=extrema_prominence,
    prominence_relative=extrema_prominence_relative,
    distance=extrema_distance,
    length_scale=length_scale,
    mature_method=mature_method,
    mature_amplitude_fraction=mature_amplitude_fraction,
    decay_tail_amplitude_fraction=decay_tail_amplitude_fraction,
    incipient_method=incipient_method,
    incipient_plateau_tau=incipient_plateau_tau,
    incipient_plateau_signal=incipient_plateau_signal,
    incipient_plateau_crossing=incipient_plateau_crossing,
    incipient_plateau_k=incipient_plateau_k,
)
_phase_params_tuple = tuple(sorted(
    (k, v) for k, v in _PHASE_PARAMS.items() if v is not None
))

# ── File upload ──────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload cyclone CSV(s) (format: ';'-delimited, column 'min_max_zeta_850')",
    type=["csv"], accept_multiple_files=True,
)

_calib_data_files = sorted(_CALIBRATION_DATA_DIR.glob("*.csv")) if _CALIBRATION_DATA_DIR.is_dir() else []
load_all_test_cyclones = st.checkbox(
    f"Load all test cyclones (tests/calibration_data — {len(_calib_data_files)} tracks)"
    if _calib_data_files else
    "Load all test cyclones (tests/calibration_data — unavailable in this environment)",
    value=False,
    key="load_all_test_cyclones",
    disabled=not bool(_calib_data_files),
    help=(
        f"Loads all {len(_calib_data_files)} real cyclone tracks bundled in "
        "tests/calibration_data for bulk calibration/validation. If you also "
        "upload files above, both sets are combined; an uploaded file takes "
        "precedence over a bundled one with the same cyclone ID."
        if _calib_data_files else
        "tests/calibration_data was not found next to this app (this checkout "
        "may not include the full repository) — this option is unavailable."
    ),
)

_synth_files, _synth_gt, _synth_preset, _synth_err = _load_synthetic_cases()
load_synthetic_cases = st.checkbox(
    f"Load synthetic cases (tests/synthetic — {len(_synth_files)} cases)"
    if _synth_files else
    "Load synthetic cases (tests/synthetic — unavailable in this environment)",
    value=False,
    key="load_synthetic_cases",
    disabled=not bool(_synth_files),
    help=(
        "Loads the synthetic life-cycle cases from tests/synthetic/cases.py. "
        "These are the only series with a KNOWN incipient boundary, so they are "
        "the ground truth for validating incipient_method. Checking this also "
        "switches the pre-processing controls to SYNTHETIC_VALIDATION_PRESET "
        "(they remain editable)."
        if _synth_files else
        f"tests/synthetic could not be imported ({_synth_err}) — this option is "
        "unavailable."
    ),
)
if _synth_err and not _synth_files:
    st.caption(f"⚠ tests/synthetic unavailable: {_synth_err}")

if load_synthetic_cases and _synth_files:
    st.caption(
        "**Synthetic mode.** Pre-processing has been set to "
        "`SYNTHETIC_VALIDATION_PRESET` (Lanczos off, Savgol off). These series are "
        "clean by construction, so the real-track pre-processing would smooth what "
        "is already smooth and round off the very segment boundaries under test — "
        "it would measure the filter rather than the phase logic. "
        "**Pre-processing conclusions do not transfer from synthetic to real "
        "tracks; phase-detection conclusions do.** "
        "Measured caveat: with BOTH the filter and the smoothing off, the detected "
        "*sequence* degrades on several cases (the unsmoothed derivative has a kink "
        "at each segment join) — read the incipient boundary here, not the full "
        "sequence. The phase controls are unaffected and remain fully editable."
    )

_EXAMPLE = Path(__file__).parent.parent.parent / "cyclophaser" / "example_data" / "example_file.csv"

# Precedence when both an upload and "load all test cyclones" are active: the
# two sets are combined (union), and an uploaded file wins on a cyclone-ID
# collision with a bundled one -- chosen because a user re-uploading a track
# under its bundled ID is more likely re-testing a specific variant of it than
# asking for it to be silently dropped.
files: dict[str, bytes] = {}
if load_all_test_cyclones and _calib_data_files:
    files.update({p.stem: p.read_bytes() for p in _calib_data_files})
if load_synthetic_cases and _synth_files:
    files.update(_synth_files)
if uploaded:
    files.update({Path(f.name).stem: f.getvalue() for f in uploaded})
if not files:
    files = {"example_file": _EXAMPLE.read_bytes()}
    st.caption(f"No file uploaded — using `{_EXAMPLE.name}` as default.")
elif load_all_test_cyclones and uploaded:
    st.caption(
        f"Combined {len(_calib_data_files)} bundled test cyclone(s) with "
        f"{len(uploaded)} uploaded file(s) — {len(files)} total (uploads take "
        "precedence on ID collision)."
    )

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

def _gt_boundary_iso(name: str, file_bytes: bytes) -> str | None:
    """ISO timestamp of the designed incipient boundary, for synthetic cases.

    Returns None for real tracks and for synthetic cases with no designed Ic
    segment (those have no checkable boundary — see section 5 of
    research/incipient_plateau/REPORT_incipient_characterisation.md).
    """
    if not (load_synthetic_cases and _synth_files):
        return None
    idx = _synth_gt.get(name)
    if idx is None:
        return None
    try:
        d = pd.read_csv(io.BytesIO(file_bytes), sep=";", index_col="time",
                        parse_dates=True)
        return d.index[int(idx)].isoformat()
    except Exception:
        return None


# ── Pre-process all cyclones ─────────────────────────────────────────────────────
# Done before rendering tabs so export data (CSV + PNG) is ready for the ZIP button.
all_results: dict[str, dict] = {}

for _cname, _fbytes in files.items():
    _res: dict = {"ok": False, "name": _cname}

    try:
        _vort, _fwarns = _run_process_vorticity(
            _fbytes, use_filter, cutoff_low, cutoff_high,
            use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
            boundary_padding,
        )
    except Exception as _exc:
        _res["error"] = f"Vorticity processing failed: {_exc}"
        all_results[_cname] = _res
        continue

    try:
        _df, _pdict, _pwarns = _run_get_periods(
            _fbytes, use_filter, cutoff_low, cutoff_high,
            use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
            boundary_padding,
            _phase_params_tuple,
        )
    except Exception as _exc:
        _res["error"] = f"Phase detection failed: {_exc}"
        _res["filter_warns"] = _fwarns
        all_results[_cname] = _res
        continue

    try:
        _png = _render_periods_png(
            _fbytes, use_filter, cutoff_low, cutoff_high,
            use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
            boundary_padding,
            _phase_params_tuple, _cname, figsize=(12, 5), show_title=True,
            gt_boundary_iso=_gt_boundary_iso(_cname, _fbytes),
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
            _bad_key = f"{_BAD_CASE_KEY_PREFIX}{cyclone_name}"
            _is_bad = st.session_state.get(_bad_key, False)
            st.subheader(f"⚠️ {cyclone_name}" if _is_bad else cyclone_name)

            if not res["ok"]:
                st.error(res.get("error", "Unknown error"))
                continue

            for msg in res["filter_warns"]:
                st.warning(msg)
            for msg in res["phase_warns"]:
                st.warning(msg)

            # Figure — rendered to PNG bytes by a cached function and shown via
            # st.image() rather than building a live Figure + st.pyplot() here,
            # so a rerun that doesn't change filter/phase params (e.g. a
            # bad-case-mark checkbox click) is a cache hit for every cyclone's
            # figure instead of a full matplotlib re-render of the whole grid.
            try:
                if n_cols >= 4:
                    _png_display = _render_compact_png(
                        files[cyclone_name], use_filter, cutoff_low, cutoff_high,
                        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
                        boundary_padding,
                        _phase_params_tuple, cyclone_name, n_cols,
                    )
                else:
                    _png_display = _render_periods_png(
                        files[cyclone_name], use_filter, cutoff_low, cutoff_high,
                        use_smoothing, use_smoothing_twice, replace_endpoints, savgol_poly,
                        boundary_padding,
                        _phase_params_tuple, cyclone_name,
                        figsize=_FIGSIZES[n_cols], show_title=True,
                        gt_boundary_iso=_gt_boundary_iso(
                            cyclone_name, files[cyclone_name]),
                    )
            except Exception as exc:
                st.error(f"Error in {'compact' if n_cols >= 4 else 'phase'} figure: {exc}")
                continue
            st.image(_png_display, use_container_width=True)

            st.checkbox(
                "⚠️ Mark as bad",
                value=False, key=_bad_key,
                help=(
                    "Flags this cyclone's detection result as bad for the current "
                    "parameter set. Persists across parameter changes within this "
                    "session (use '🗑 Clear bad-case marks' in the sidebar to reset) "
                    "and is included in the exported YAML's 'evaluation' section."
                ),
            )

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

    # Bad-case evaluation summary — always shown, regardless of n_cols.
    st.divider()
    st.subheader("Bad-case evaluation")
    _eval = _compute_evaluation(cyclone_names)
    st.metric(
        "Bad cases",
        f"{_eval['bad_cases_count']} / {_eval['total_cyclones']}",
        f"{_eval['bad_cases_percent']}%",
        delta_color="off",
    )
    if _eval["bad_cases"]:
        st.caption("Marked: " + ", ".join(_eval["bad_cases"]))
    else:
        st.caption("No cyclones marked as bad in this session.")
    st.caption(
        "Mark cyclones using the '⚠️ Mark as bad' checkbox below each figure above. "
        "Clear all marks with '🗑 Clear bad-case marks' in the sidebar. This summary "
        "is also written to the exported YAML's 'evaluation' section, so different "
        "parameter sets can be compared by their bad-case rate."
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

### `boundary_padding` — Lanczos boundary condition
How the series is extended beyond its own ends before the convolution.

- `reflect` (**default**) — pads with the reflection of the series. Normalised `|dz|` at the
  first sample drops from a median **0.95 → 0.42** (last sample 0.98 → 0.35).
- `zero` — the pre-fix behaviour (`scipy.signal.convolve(..., mode="same")`).
  The kernel sees zeros outside the series; since vorticity has a non-zero floor, this injects a
  spurious *deepening* ramp worth a median **74 % of the cyclone's own amplitude**, spread over the
  boundary zone — which is ~**24 % of the series at each end** because the kernel is about half the
  series long. Measured on the 51-track set, this ramp alone accounts for ≥ 80 % of the slope at the
  first sample in **51/51** tracks. Pass it explicitly to reproduce results from before this
  default changed.
- `edge` — pads with the edge value repeated. Between the two (median 0.50) and changes marginally
  fewer phase sequences (13/51 vs 14/51 for `reflect`).

Changing this alters the smoothed signal near the boundaries, so **a calibrated parameter set must be
re-validated before it is trusted in a new mode**. Only has an effect when the Lanczos filter is on.

### `replace_endpoints_with_lowpass` — Endpoint correction (**DEPRECATED**)
Replaces the first/last 5 % of the filtered output with a simple low-pass estimate.
**Default: 0 (disabled)** — it was 24 up to v2.0.0.

It was introduced as a palliative for the same zero-padding artifact described under `boundary_padding`,
and it applies the *same* zero-padded convolution internally, so it never fixed the cause. Combined with
`boundary_padding=reflect` it is **harmful**: both filters carry full amplitude at the edge, so the 5 %
splice becomes a visible step. Measured over the 51 tracks, the number opening with a spurious `decay`
phase goes **4/51 → 28/51** under `reflect` with this at 24, and **0/51** with it at 0. Leave it at 0.

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
All thresholds are **fractions of a length**, making them resolution-independent.
Which length depends on `length_scale` (see below): by default the whole series;
optionally, each threshold's own local cycle.

| Parameter | Default | Description |
|---|---|---|
| `threshold_intensification_length` | 0.075 | Min. duration of an intensification segment. |
| `threshold_decay_length` | 0.075 | Min. duration of a decay segment. |
| `threshold_mature_length` | 0.030 | Min. duration of the mature stage. Only used when `mature_method="derivative"` — see below. |
| `threshold_mature_distance` | 0.125 | Max. distance between vorticity minimum and mature segment centre. Already local — unaffected by `length_scale`. Only used when `mature_method="derivative"` — see below. |
| `threshold_intensification_gap` | 0.075 | Max. gap between consecutive intensification segments for merging. |
| `threshold_decay_gap` | 0.075 | Max. gap between consecutive decay segments for merging. |
| `threshold_incipient_length` | 0.400 | Min. duration of the incipient phase. Already local — unaffected by `length_scale`. |

### `length_scale` — global vs. local threshold denominator

- **`global`** (default): the five thresholds above (excluding mature distance and
  incipient length, which were always local) are measured against the whole input
  series length. Matches all versions prior to this option.
- **`local`**: each candidate segment is instead measured against the span of the
  local life cycle it belongs to (the nearest vorticity extrema immediately before
  and after it). Fixes tracks with multiple, differently-sized life cycles: under
  `global`, a small second cycle's phases are checked against a denominator
  dominated by a much larger first cycle and can all be rejected, collapsing the
  whole second cycle into a single `residual` block.
- Note: for a track containing only **one** life cycle, `local` and `global` are
  mathematically identical (there is no other cycle to distinguish the local scale
  from). `length_scale` only changes anything on tracks with more than one cycle.

### `mature_method` — how the mature window is sized

- **`derivative`** (default): the mature window around each vorticity minimum is a
  fixed proportion (`threshold_mature_distance`) of the *time* distance to the
  neighbouring vorticity peaks — unchanged from v2.0.0. `threshold_mature_length`
  then applies as a minimum-duration floor on that window.
- **`amplitude`** (opt-in): the mature window is instead the contiguous stretch of
  vorticity around the minimum that stays within `mature_amplitude_fraction` of the
  cycle's own peak-to-valley amplitude, evaluated independently on the
  intensification side and the decay side. This anchors directly on the vorticity
  value itself rather than on smoothed-derivative extrema, which can lag the true
  minimum by a few timesteps and displace the `derivative` window forward of where
  the cyclone was actually most intense on some real cyclones.
- **`threshold_mature_length` and `threshold_mature_distance` have NO EFFECT when
  `mature_method="amplitude"`.** That minimum-duration floor was calibrated for
  `derivative`'s window; reusing it for `amplitude` was found (case 20160030) to
  discard well-centred amplitude windows for being narrow, which is a physically
  meaningful outcome of `mature_amplitude_fraction` there, not a defect to filter
  out. No replacement minimum-duration safeguard exists for `amplitude` at this
  time — this is deliberate, to evaluate the method unconstrained first; revisit
  only if calibration surfaces spurious, very short amplitude windows.
- The mature-must-be-followed-by-decay physical confirmation check (see the
  Known methodological notes tab) applies identically in both modes.

### `decay_tail_amplitude_fraction` — extending decay over a flat/plateau tail

- **`None`** (default): disabled, matching all versions prior to this option.
- **Opt-in** (e.g. `0.05`, the author's validated reference value): compensates for
  an artifact of the prominence filter. On a single-cycle series, peaks and valleys
  are scored against SEPARATE populations, so the largest interior peak always
  survives `prominence_relative` filtering by construction — even when its
  prominence is negligible — while the valley of the same ripple is correctly
  rejected. This "orphan" peak (no surviving valley after it) makes
  `find_decay_period` truncate decay early; the flat tail left behind is then
  labelled `residual` by the catch-all rule in `find_residual_period` (step 4
  below), even though nothing in the vorticity indicates a genuine
  re-intensification.
- With this set, `find_residual_period` checks — immediately before that catch-all
  rule, and only when the tail directly follows an existing `decay` block —
  whether the tail contains a genuine re-deepening: a drop below the tail's
  running-maximum vorticity larger than this fraction of the cycle's own
  peak-to-valley amplitude. If not, the tail is labelled `decay` instead of
  `residual`.
- **Never touches `z_peaks_valleys` or any detected extrema**, so it cannot shift
  the mature window — unlike the discarded alternative of dropping the orphan peak
  from the extrema themselves, which was found to inflate the mature window's
  duration in every case it fixed (the decay-side amplitude reference in the
  `amplitude` mature method shifts when the bounding peak changes).
- Validated safe window on the 51-track calibration set: **`(0.0356, 0.0651]`**.
  Below it, some spurious tails aren't absorbed; above it, genuine
  re-intensifications start being swallowed too.
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
