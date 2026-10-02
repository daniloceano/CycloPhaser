#!/usr/bin/env python
"""Figures and tables of the usage guide (docs/usage.rst).

    python docs/figures/make_noisy_example.py

Deterministic. Uses the HOURLY example track docs/data/example_track_hourly.csv
(column ``min_max_zeta_850``; origin in docs/data/README.md) and the package's
own plotting function (``plots.plot_all_periods``), drawn into an axis and
saved at web resolution. Writes, under docs/generated/:

  example_default.png        the example track with the defaults
  example_default_phases.csv the phases of that run (periods_to_dict)
  example_noisy_default.png  the same track plus seeded noise, with the defaults
  example_noisy_custom.png   the noisy track with a customised filtering
                             (CUSTOM below, which includes smoothing)

The noisy track and CUSTOM only illustrate HOW to customise the filtering; they
are not a validated configuration.
"""
import importlib
import inspect
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

importlib.import_module("cyclophaser.determine_periods")
DP = sys.modules["cyclophaser.determine_periods"]
PL = importlib.import_module("cyclophaser.plots")

OUT = Path(__file__).resolve().parents[1] / "generated"
NOISE_FRACTION = 0.3       # noise std as a fraction of the track's own std
SEED = 0
CUSTOM = dict(use_smoothing="auto", use_smoothing_twice="auto")


TRACK = Path(__file__).resolve().parents[1] / "data" / "example_track_hourly.csv"


def load_example():
    track = pd.read_csv(TRACK, parse_dates=[0], delimiter=";", index_col=[0])
    return track["min_max_zeta_850"]


def run(series, **kwargs):
    zeta_df = pd.DataFrame({"zeta": series.values}, index=series.index)
    pv_keys = set(inspect.signature(DP.process_vorticity).parameters)
    vort = DP.process_vorticity(zeta_df, **{k: v for k, v in kwargs.items() if k in pv_keys})
    df = DP.get_periods(vort, **{k: v for k, v in kwargs.items() if k not in pv_keys})
    assert df.equals(DP.determine_periods(series, **kwargs))
    return df, vort


def draw(df, vort, path, title):
    fig, ax = plt.subplots(figsize=(9, 5.4))
    fig.subplots_adjust(bottom=0.3)
    PL.plot_all_periods(DP.periods_to_dict(df), df, ax=ax, vorticity=vort, periods_outfile_path=None)
    ax.set_title(title, fontsize=11)
    fig.savefig(path, dpi=110, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    warnings.simplefilter("ignore")
    s = load_example()
    df, vort = run(s)
    draw(df, vort, OUT / "example_default.png", "Example track, package defaults")
    phases = DP.periods_to_dict(df)
    pd.DataFrame([(p, a, b) for p, (a, b) in phases.items()], columns=["phase", "start", "end"]) \
        .to_csv(OUT / "example_default_phases.csv", index=False)

    rng = np.random.default_rng(SEED)
    noisy = s + NOISE_FRACTION * s.std() * rng.standard_normal(len(s))
    df_n, vort_n = run(noisy)
    draw(df_n, vort_n, OUT / "example_noisy_default.png", "Example track with added noise, package defaults")
    df_c, vort_c = run(noisy, **CUSTOM)
    draw(df_c, vort_c, OUT / "example_noisy_custom.png",
         "Example track with added noise, customised filtering (illustration only)")
    print("written:", ", ".join(p.name for p in sorted(OUT.glob("example_*"))))


if __name__ == "__main__":
    main()
