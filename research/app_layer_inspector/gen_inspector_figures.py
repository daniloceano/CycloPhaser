"""Offline render of the calibration app's layer inspector.

VISUALISATION ONLY — this script never modifies ``cyclophaser/``. It exists so
the inspector can be checked WITHOUT starting Streamlit: it imports the very
same pure helpers the app calls (``tools/calibration_app/layer_inspector.py``)
and a matplotlib renderer that consumes them
(``tools/calibration_app/inspector_mpl.py``), so what lands in ``figures/`` is
what the app computes — the only difference is that a static figure has no
switches, so every layer is drawn at once.

Pinned provenance
-----------------
Base commit : 01c44923cc6d9e9ae70c48c0fc717fd126546390  (develop-v2.1)
Branch      : research/app-layer-inspector, on top of research/incipient-plateau
Track set   : tests/calibration_data/

Tracks
------
20190325 and 20206498 are the two the incipient work flagged for the visual
checkpoint. 20150377 is the tight-prominence case: it is run with the author's
``prominence_relative=0.30, distance=3`` so the ledger and the mature layer
have rejections to show — with the filter off, nothing is ever rejected and
the layers have nothing to demonstrate.

Run from the repo root:
    python research/app_layer_inspector/gen_inspector_figures.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))

from cyclophaser.determine_periods import (  # noqa: E402
    get_periods, periods_to_dict, process_vorticity,
)
from cyclophaser.find_stages import (  # noqa: E402
    find_decay_period, find_intensification_period,
)
import layer_inspector as li  # noqa: E402
from inspector_mpl import render_static_inspector  # noqa: E402

CALIB = REPO_ROOT / "tests" / "calibration_data"
OUT = Path(__file__).resolve().parent / "figures"

# The section-3c calibration (same as research/incipient_plateau/), because it
# is the regime the layers were designed against: the prominence filter
# actually rejects candidates there, and a plateau is definable at all.
AUTHOR_PV = dict(use_filter=True, cutoff_low=168, cutoff_high=18,
                 boundary_padding="reflect", replace_endpoints_with_lowpass=0,
                 use_smoothing=False, use_smoothing_twice=False,
                 savgol_polynomial=3)
AUTHOR_GP = dict(mature_method="amplitude", mature_amplitude_fraction=0.95,
                 decay_tail_amplitude_fraction=0.05, length_scale="local",
                 threshold_mature_distance=0.18)

JOBS = [
    # (track, tag, extrema filter, extra get_periods args, incipient lens args)
    ("20190325", "plateau", dict(),
     dict(incipient_method="plateau", incipient_plateau_tau=0.20),
     dict(signal="derivative", tau=0.20, smooth_window=0)),
    ("20206498", "plateau", dict(),
     dict(incipient_method="plateau", incipient_plateau_tau=0.20),
     dict(signal="derivative", tau=0.20, smooth_window=0)),
    # The tight-prominence case: rejections exist, so the ledger and the mature
    # layer have something to show, and the incipient layers degrade gracefully
    # under the geometric rule (rel/tau omitted, dz/dz2 kept).
    ("20150377", "prom-tight-geometric",
     dict(prominence_relative=0.30, distance=3),
     dict(incipient_method="geometric"),
     dict(signal="derivative", tau=0.20, smooth_window=0)),
]


def run(track_id, extrema, gp):
    series = pd.read_csv(CALIB / f"{track_id}.csv", sep=";", index_col="time",
                         parse_dates=True)["min_max_zeta_850"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": series}), **AUTHOR_PV)
        df_result = get_periods(vort, **AUTHOR_GP, **extrema, **gp)
    return vort, df_result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    for track_id, tag, extrema, gp, lens_kw in JOBS:
        vort, df_result = run(track_id, extrema, gp)
        work = li.build_working_frame(
            vort, prominence=extrema.get("prominence"),
            prominence_relative=extrema.get("prominence_relative"),
            distance=extrema.get("distance"))
        args = li.build_args_periods(**AUTHOR_GP, **gp)

        ribbon = li.pipeline_ribbon(work, **args)
        ledgers = {"intensification": li.intensification_ledger(work, **args),
                   "decay": li.decay_ledger(work, **args)}
        after_decay = find_decay_period(
            find_intensification_period(work.copy(deep=True), **args), **args)
        mature = {"lens": li.mature_lens(df_result["z"], **extrema),
                  "records": li.mature_ledger(after_decay, **args)}
        lens = li.incipient_lens(df_result["z_unfil"], df_result["dz"],
                                 df_result["dz2"], **lens_kw)
        incipient = {"lens": lens, "boundary": li.incipient_lead(df_result),
                     "tau": lens_kw["tau"],
                     "plateau_active": gp.get("incipient_method") == "plateau"}

        cfg = ", ".join(f"{k}={v}" for k, v in {**extrema, **gp}.items()) or "defaults"
        fig = render_static_inspector(
            track_id, vort, df_result, periods_to_dict(df_result),
            ribbon=ribbon, ledgers=ledgers, mature=mature, incipient=incipient,
            title_suffix=f" — {cfg}")
        path = OUT / f"inspector_{track_id}_{tag}.png"
        fig.savefig(path, dpi=120, bbox_inches="tight")
        plt.close(fig)

        n_acc = sum(c["accepted"] for c in ledgers["intensification"]["candidates"])
        n_rej = sum(not c["accepted"] for c in ledgers["intensification"]["candidates"])
        n_disc = sum(1 for r in mature["records"]
                     if r.get("written") and not r.get("confirmed"))
        # Step 6 of the ribbon IS get_periods' own result -- assert it here too,
        # so a figure can never be produced from a frame that drifted.
        assert ribbon[-1][1].equals(df_result["periods"]), track_id
        written.append((path, f"intensificação {n_acc} aceitos / {n_rej} rejeitados · "
                              f"{n_disc} janela(s) madura(s) descartada(s) · "
                              f"fronteira incipiente = {incipient['boundary']}"))

    print(f"{len(written)} figuras em {OUT}")
    for path, note in written:
        print(f"  {path.name:<44} {note}")


if __name__ == "__main__":
    main()
