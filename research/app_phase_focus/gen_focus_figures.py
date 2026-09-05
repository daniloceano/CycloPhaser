"""Offline render of the calibration app's phase-focus lenses.

VISUALISATION ONLY — this script never modifies ``cyclophaser/``. It exists so
the lenses can be checked without starting Streamlit: it imports the very same
pure helpers and drawing functions the app calls
(``tools/calibration_app/phase_focus.py``), so what lands in ``figures/`` is
what the app shows, modulo figure size.

Pinned provenance
-----------------
Base commit : 01c44923cc6d9e9ae70c48c0fc717fd126546390  (develop-v2.1)
Branch      : research/app-phase-focus, on top of research/incipient-plateau
Track set   : tests/calibration_data/

Configuration
-------------
The section-3c calibration (``AUTHOR_PV`` / ``AUTHOR_GP``), same as
research/incipient_plateau/gen_geometric_vs_plateau.py, because that is the
regime the lenses were designed against: it is where the prominence filter
actually rejects candidates on real tracks, and where a plateau is definable at
all (see section 4 of REPORT_incipient_characterisation.md).

Run from the repo root:
    python research/app_phase_focus/gen_focus_figures.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))

from cyclophaser.determine_periods import (  # noqa: E402
    get_periods, periods_to_dict, process_vorticity,
)
from phase_focus import (  # noqa: E402
    draw_incipient_lens, draw_mature_lens, incipient_lens, mature_lens,
)

CALIB = REPO_ROOT / "tests" / "calibration_data"
OUT = Path(__file__).resolve().parent / "figures"

AUTHOR_PV = dict(use_filter=True, cutoff_low=168, cutoff_high=18,
                 boundary_padding="reflect", replace_endpoints_with_lowpass=0,
                 use_smoothing=False, use_smoothing_twice=False,
                 savgol_polynomial=3)
AUTHOR_GP = dict(mature_method="amplitude", mature_amplitude_fraction=0.95,
                 decay_tail_amplitude_fraction=0.05, length_scale="local",
                 threshold_mature_distance=0.18)

# ── Mature lens: three tracks, spanning "filter off" to the author's tight
#    setting, so the effect of the prominence slider is visible as a contrast
#    rather than only as an absolute picture. 20190325 appears twice on purpose
#    (loose vs tight) — that pair IS the demonstration.
MATURE_JOBS = [
    ("20190325", "prom-off",    dict()),
    ("20190325", "prom-tight",  dict(prominence_relative=0.30, distance=3)),
    ("20206498", "prom-tight",  dict(prominence_relative=0.30, distance=3)),
    ("20150377", "prom-loose",  dict(prominence_relative=0.05)),
]

# ── Incipient lens: the two tracks flagged for the visual checkpoint, each in
#    the three regimes the lens has to handle — the pipeline derivative, the
#    smoothed raw-vorticity probe, and a non-plateau run (graceful degradation).
INCIPIENT_JOBS = [
    ("20190325", "plateau-derivative",
     dict(incipient_method="plateau", incipient_plateau_tau=0.20),
     dict(signal="derivative", tau=0.20, smooth_window=0)),
    ("20190325", "plateau-vorticity-w9",
     dict(incipient_method="plateau", incipient_plateau_tau=0.20,
          incipient_plateau_signal="vorticity", incipient_smooth_window=9),
     dict(signal="vorticity", tau=0.20, smooth_window=9)),
    ("20190325", "geometric-degraded",
     dict(incipient_method="geometric"),
     dict(signal="derivative", tau=0.20, smooth_window=0, plateau_active=False)),
    ("20206498", "plateau-derivative",
     dict(incipient_method="plateau", incipient_plateau_tau=0.20),
     dict(signal="derivative", tau=0.20, smooth_window=0)),
    ("20206498", "plateau-vorticity-w9",
     dict(incipient_method="plateau", incipient_plateau_tau=0.20,
          incipient_plateau_signal="vorticity", incipient_smooth_window=9),
     dict(signal="vorticity", tau=0.20, smooth_window=9)),
]


def run(track_id, **gp):
    series = pd.read_csv(CALIB / f"{track_id}.csv", sep=";", index_col="time",
                         parse_dates=True)["min_max_zeta_850"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": series}), **AUTHOR_PV)
        df = get_periods(vort, **AUTHOR_GP, **gp)
    return df


def incipient_lead(df) -> int:
    inc = (df["periods"] == "incipient").to_numpy()
    if inc.size == 0 or not inc[0]:
        return 0
    return int(inc.size) if inc.all() else int(np.argmin(inc))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    for track_id, tag, extrema in MATURE_JOBS:
        df = run(track_id, **extrema)
        lens = mature_lens(df["z"],
                           prominence=extrema.get("prominence"),
                           prominence_relative=extrema.get("prominence_relative"),
                           distance=extrema.get("distance"))
        fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                                 gridspec_kw={"height_ratios": [2.0, 1.0]})
        cfg = ", ".join(f"{k}={v}" for k, v in extrema.items()) or "sem filtro"
        draw_mature_lens(
            axes, df["z"], lens, periods_dict=periods_to_dict(df),
            title=f"{track_id} — lente Mature — {cfg}")
        fig.tight_layout()
        path = OUT / f"mature_{track_id}_{tag}.png"
        fig.savefig(path, dpi=130, bbox_inches="tight")
        plt.close(fig)
        written.append((path, f"aceitos p/v = "
                              f"{len(lens['accepted_peaks'])}/{len(lens['accepted_valleys'])}, "
                              f"rejeitados p/v = "
                              f"{len(lens['rejected_peaks'])}/{len(lens['rejected_valleys'])}"))

    for track_id, tag, gp, lens_kw in INCIPIENT_JOBS:
        plateau_active = lens_kw.pop("plateau_active", True)
        df = run(track_id, **gp)
        lens = incipient_lens(df["z_unfil"], df["dz"], df["dz2"], **lens_kw)
        nrows = 3 if plateau_active else 2
        fig, axes = plt.subplots(nrows, 1, figsize=(13, 3 * nrows), sharex=True)
        boundary = incipient_lead(df)
        draw_incipient_lens(
            axes, lens, df["dz"], df["dz2"], lens_kw["tau"],
            boundary=boundary, plateau_active=plateau_active,
            title=f"{track_id} — lente Incipient — {tag}")
        if not plateau_active:
            fig.text(0.5, 0.005,
                     "incipient_method != 'plateau': tau e a sondagem nao se "
                     "aplicam; apenas dz/dz2 crus e a fronteira produzida pela "
                     "regra geometrica.",
                     ha="center", fontsize=8, color="#555555")
        fig.tight_layout()
        path = OUT / f"incipient_{track_id}_{tag}.png"
        fig.savefig(path, dpi=130, bbox_inches="tight")
        plt.close(fig)
        written.append((path, f"fronteira = {boundary}, joelho = {lens['knee']}, "
                              f"cruzamento cru/suav = {lens['boundary_raw']}/"
                              f"{lens['boundary_smoothed']}"))

    print(f"{len(written)} figuras em {OUT}")
    for path, note in written:
        print(f"  {path.name:<44} {note}")


if __name__ == "__main__":
    main()
