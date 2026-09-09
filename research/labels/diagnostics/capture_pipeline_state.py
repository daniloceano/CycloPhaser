#!/usr/bin/env python
"""Capture full pipeline output (periods + z_peaks_valleys arrays) for all 51
real tracks and all 12 synthetic cases, using cyclophaser_params-9.yaml
unmodified.

READ-ONLY with respect to the package: just calls process_vorticity /
get_periods. Used to snapshot state BEFORE and AFTER the idx0 boundary-type
fix, for the M1/M2/M3/M6/M7 measurements. Run once before editing
determine_periods.py (tag="before") and once after (tag="after"); each run is
a fresh process so there is no stale-import risk.

Usage:
    python capture_pipeline_state.py before
    python capture_pipeline_state.py after
"""
import json
import sys
import warnings
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"

sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from labels_core import load_real_series, load_synthetic_series  # noqa: E402
from cyclophaser.determine_periods import process_vorticity, get_periods  # noqa: E402

CONFIG_PATH = Path.home() / "Downloads" / "cyclophaser_params-9.yaml"
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")


def load_config(path):
    import inspect
    doc = yaml.safe_load(path.read_text()) or {}
    gp_accepted = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_accepted}
    return pv, gp


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("before", "after"):
        print("usage: capture_pipeline_state.py before|after", file=sys.stderr)
        sys.exit(1)
    tag = sys.argv[1]

    pv, gp = load_config(CONFIG_PATH)

    real = load_real_series()
    synth, synth_names = load_synthetic_series()

    out = {"config_pv": pv, "config_gp": gp, "tracks": {}}

    for sid, values in {**real, **synth}.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
                df = get_periods(vort, **gp)
            except Exception as exc:
                out["tracks"][sid] = {"error": f"{type(exc).__name__}: {exc}"}
                continue

        out["tracks"][sid] = {
            "n_steps": len(df),
            "periods": [str(p) for p in df["periods"]],
            "z_peaks_valleys": [(None if pd.isna(v) else str(v)) for v in df["z_peaks_valleys"]],
            "source": "real" if sid in real else "synthetic",
        }

    out_path = DIAG_DIR / f"fix_state_{tag}.json"
    out_path.write_text(json.dumps(out, indent=1))
    print(f"wrote {out_path} ({len(out['tracks'])} tracks)")


if __name__ == "__main__":
    main()
