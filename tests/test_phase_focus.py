"""Tests for the calibration app's phase-focus lenses (tools/calibration_app/phase_focus.py).

The lenses are PURE VISUALISATION — they must never change what the package
detects, and they must never *misreport* it either. Three things are worth
locking down, and this file covers exactly those:

1. **Mature-lens fidelity.** The peaks/valleys the lens draws as "accepted"
   have to be the same objects ``find_mature_stage`` iterates over, i.e. the
   ``'peak'`` / ``'valley'`` entries of ``df['z_peaks_valleys']`` in the real
   detection result — same indices, not "close enough". A lens that showed an
   approximate parallel calculation would be worse than no lens, because it
   would teach the wrong thing about the parameter being tuned.

2. **The diagnostics are actually correct** (the ``|d2z|`` knee and the
   normalised ``rel`` profile), checked against series whose answer is known by
   construction rather than by re-running the same code.

3. **Overview is untouched.** The lens module must not perturb the figure the
   Overview focus draws, nor mutate the frames it is handed.
"""

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "calibration_app"))

from cyclophaser.determine_periods import (  # noqa: E402
    get_periods, periods_to_dict, process_vorticity,
)
from cyclophaser.plots import plot_all_periods  # noqa: E402
from phase_focus import (  # noqa: E402
    incipient_lens, knee_index, mature_lens,
)

CALIB = REPO_ROOT / "tests" / "calibration_data"

# The section-3c calibration the incipient-plateau research used: it is the
# regime in which the prominence filter actually rejects candidates on real
# tracks, so it is the regime where the mature lens has something to show.
AUTHOR_PV = dict(use_filter=True, cutoff_low=168, cutoff_high=18,
                 boundary_padding="reflect", replace_endpoints_with_lowpass=0,
                 use_smoothing=False, use_smoothing_twice=False,
                 savgol_polynomial=3)
AUTHOR_GP = dict(mature_method="amplitude", mature_amplitude_fraction=0.95,
                 decay_tail_amplitude_fraction=0.05, length_scale="local",
                 threshold_mature_distance=0.18)

# Five real tracks (the requirement is >= 3): two that the incipient work
# flagged as case-C tracks, one plain case-B track, and two with a high r(t0).
FIDELITY_TRACKS = ["20150377", "20190325", "20203373", "20203947", "20206498"]

# Extrema-filter settings exercised for fidelity. The tight one (0.30 / 3) is
# the author's; the loose ones bracket it, and `all None` is the package
# default where nothing may be rejected at all.
EXTREMA_SETTINGS = [
    dict(prominence=None, prominence_relative=None, distance=None),
    dict(prominence=None, prominence_relative=0.30, distance=3),
    dict(prominence=None, prominence_relative=0.05, distance=None),
]


def _run(track_id, **gp):
    series = pd.read_csv(CALIB / f"{track_id}.csv", sep=";", index_col="time",
                         parse_dates=True)["min_max_zeta_850"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": series}), **AUTHOR_PV)
        df = get_periods(vort, **AUTHOR_GP, **gp)
    return series, vort, df


def _detector_positions(df, kind):
    """The indices phase detection itself consumes, straight from the result."""
    return np.flatnonzero((df["z_peaks_valleys"] == kind).to_numpy())


# ══════════════════════════════════════════════════════════════════════════════
# 1. Mature-lens fidelity
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("track_id", FIDELITY_TRACKS)
@pytest.mark.parametrize("extrema", EXTREMA_SETTINGS,
                         ids=["no-filter", "tight-0.30-d3", "loose-0.05"])
def test_mature_lens_accepted_extrema_are_the_detector_s(track_id, extrema):
    """The lens's "accepted" set == the extrema mature detection actually uses.

    Ground truth is ``df['z_peaks_valleys']`` from a real ``get_periods`` run —
    the exact column ``find_mature_stage`` reads its z_valleys and z_peaks from.
    """
    _, _, df = _run(track_id, **extrema)
    lens = mature_lens(df["z"], **extrema)

    np.testing.assert_array_equal(lens["accepted_peaks"],
                                  _detector_positions(df, "peak"))
    np.testing.assert_array_equal(lens["accepted_valleys"],
                                  _detector_positions(df, "valley"))


@pytest.mark.parametrize("track_id", FIDELITY_TRACKS)
def test_mature_lens_accepted_plus_rejected_is_the_candidate_set(track_id):
    """Nothing is invented and nothing is lost: accepted | rejected == candidates.

    The candidate set is the unfiltered ``find_peaks_valleys`` output, so this
    also pins that the lens's "rejected" markers are genuinely things the
    filter removed rather than points the lens made up.
    """
    _, _, df = _run(track_id)                       # unfiltered reference run
    unfiltered = mature_lens(df["z"])
    filtered = mature_lens(df["z"], prominence_relative=0.30, distance=3)

    for kind in ("peak", "valley"):
        candidates = set(unfiltered[f"accepted_{kind}s"].tolist())
        shown = (set(filtered[f"accepted_{kind}s"].tolist())
                 | set(filtered[f"rejected_{kind}s"].tolist()))
        assert shown == candidates
        # A filter can only remove; it never promotes a new extremum.
        assert set(filtered[f"accepted_{kind}s"].tolist()) <= candidates


@pytest.mark.parametrize("track_id", FIDELITY_TRACKS)
def test_effective_threshold_explains_the_classification(track_id):
    """The drawn threshold line separates accepted from rejected, exactly.

    Run without the distance filter, so prominence is the ONLY reason an
    interior candidate can be dropped and the horizontal line must therefore
    account for every rejection. Boundary extrema are excluded because the
    package preserves them unconditionally, whatever their prominence.
    """
    _, _, df = _run(track_id, prominence_relative=0.30)
    lens = mature_lens(df["z"], prominence_relative=0.30)
    n = lens["n"]

    for kind in ("peak", "valley"):
        thr = lens[f"{kind}_threshold"]
        assert thr is not None
        proms = lens[f"{kind}_prominences"]
        for idx in lens[f"accepted_{kind}s"]:
            if idx in (0, n - 1):
                continue
            assert proms[int(idx)] >= thr
        for idx in lens[f"rejected_{kind}s"]:
            assert int(idx) not in (0, n - 1)
            assert proms[int(idx)] < thr


def test_no_prominence_filter_means_no_threshold_line():
    """With both prominence modes off there is no cut to draw, and nothing is cut."""
    _, _, df = _run("20190325")
    lens = mature_lens(df["z"])
    assert lens["peak_threshold"] is None
    assert lens["valley_threshold"] is None
    assert len(lens["rejected_peaks"]) == 0
    assert len(lens["rejected_valleys"]) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. Diagnostics on series with a known answer
# ══════════════════════════════════════════════════════════════════════════════

def test_knee_index_on_a_known_series():
    """|d2z| is largest at a designed spike inside the first half."""
    dz2 = np.zeros(100)
    dz2[20] = 3.0        # the knee: the largest |.| in the leading half
    dz2[10] = -1.5
    dz2[80] = -50.0      # a far larger turn later on, which must NOT win
    assert knee_index(dz2) == 20
    # Sign is irrelevant — it is |d2z| that is maximised.
    dz2[20] = -3.0
    assert knee_index(dz2) == 20


def test_knee_index_window_follows_the_fraction():
    dz2 = np.zeros(100)
    dz2[15] = 1.0
    dz2[40] = 5.0
    assert knee_index(dz2, fraction=0.5) == 40    # window [0, 50)
    assert knee_index(dz2, fraction=0.2) == 15    # window [0, 20)


def test_knee_index_degenerate_inputs():
    assert knee_index(np.array([])) == 0
    assert knee_index(np.array([np.nan, np.nan])) == 0
    assert knee_index(np.zeros(10)) == 0          # flat: argmax is index 0


def test_rel_profile_is_abs_dz_over_its_max():
    """rel(t) on the "derivative" signal is exactly |dz| / max|dz|."""
    dz = np.array([0.0, -1.0, 2.0, -8.0, 4.0, 0.5])
    lens = incipient_lens(z_unfil=np.zeros_like(dz), dz=dz, dz2=np.zeros_like(dz),
                          signal="derivative", tau=0.20)
    np.testing.assert_allclose(lens["rel_raw"], np.abs(dz) / 8.0)
    # tau=0.20 -> first sample with |dz|/8 >= 0.2 is index 2 (2/8 = 0.25):
    # index 1 is 1/8 = 0.125, below tau.
    assert lens["boundary_raw"] == 2
    # "derivative" reads a curve the pipeline already filtered, so the probe
    # smoothing is inert there and both profiles must coincide.
    assert lens["smoothing_applies"] is False
    np.testing.assert_array_equal(lens["rel_raw"], lens["rel_smoothed"])


def test_rel_profile_flat_signal_is_all_zero():
    flat = np.zeros(20)
    lens = incipient_lens(z_unfil=flat, dz=flat, dz2=flat,
                          signal="derivative", tau=0.20)
    np.testing.assert_array_equal(lens["rel_raw"], np.zeros(20))
    assert lens["boundary_raw"] == 0        # no crossing -> no incipient phase


def test_incipient_lens_boundary_matches_the_pipeline_boundary():
    """Under plateau, the lens's rel crossing is the boundary the run produced."""
    for track_id in ("20190325", "20206498"):
        _, _, df = _run(track_id, incipient_method="plateau",
                        incipient_plateau_tau=0.20)
        lens = incipient_lens(df["z_unfil"], df["dz"], df["dz2"],
                              signal="derivative", tau=0.20)
        inc = (df["periods"] == "incipient").to_numpy()
        lead = int(np.argmin(inc)) if (inc[0] and not inc.all()) else 0
        assert lens["boundary_raw"] == lead


def test_probe_smoothing_is_reported_only_where_it_applies():
    """smoothing_applies mirrors the package's own "vorticity only" rule."""
    x = np.linspace(0, 1, 60) ** 2
    common = dict(z_unfil=x, dz=np.gradient(x), dz2=np.gradient(np.gradient(x)),
                  tau=0.20, smooth_polyorder=3)
    assert incipient_lens(signal="vorticity", smooth_window=9, **common)["smoothing_applies"]
    assert not incipient_lens(signal="vorticity", smooth_window=0, **common)["smoothing_applies"]
    assert not incipient_lens(signal="derivative", smooth_window=9, **common)["smoothing_applies"]


# ══════════════════════════════════════════════════════════════════════════════
# 3. Overview is unchanged
# ══════════════════════════════════════════════════════════════════════════════

def _overview_config(periods_dict, df, vort):
    """A structural fingerprint of the Overview figure (what the app renders)."""
    fig, ax = plt.subplots(figsize=(12, 5))
    try:
        plot_all_periods(periods_dict, df, ax=ax, vorticity=vort)
        cfg = {
            "n_lines": len(ax.lines),
            "labels": tuple(line.get_label() for line in ax.lines),
            "colors": tuple(str(line.get_color()) for line in ax.lines),
            "data": tuple(
                (float(np.nansum(line.get_ydata(orig=False).astype(float))),
                 len(line.get_ydata()))
                for line in ax.lines
            ),
            "n_collections": len(ax.collections),
            "n_patches": len(ax.patches),
            "xlim": tuple(float(v) for v in ax.get_xlim()),
            "ylim": tuple(float(v) for v in ax.get_ylim()),
        }
    finally:
        plt.close(fig)
    return cfg


def test_overview_figure_config_is_untouched_by_the_lenses():
    """Rendering the lenses must leave the Overview figure bit-for-bit the same.

    The realistic regression here is a lens helper mutating the shared frame
    (a column overwritten, an index re-sorted) — which would silently change
    the Overview figure the next time it is drawn. So: fingerprint Overview,
    run BOTH lenses over the very same objects, fingerprint it again, and
    require identity. The frames themselves are checked for mutation too.
    """
    _, vort, df = _run("20190325", prominence_relative=0.30, distance=3)
    periods_dict = periods_to_dict(df)

    before = _overview_config(periods_dict, df, vort)
    df_snapshot = df.copy(deep=True)

    m = mature_lens(df["z"], prominence_relative=0.30, distance=3)
    i = incipient_lens(df["z_unfil"], df["dz"], df["dz2"], signal="vorticity",
                       tau=0.20, smooth_window=9)
    assert m["n"] > 0 and i["rel_raw"].size > 0       # the lenses really ran

    after = _overview_config(periods_dict, df, vort)
    assert after == before

    # No column was written, reordered, or retyped by the lens computations.
    pd.testing.assert_frame_equal(df, df_snapshot)


def test_lenses_do_not_mutate_their_input_arrays():
    dz = np.array([0.0, -1.0, 2.0, -8.0, 4.0, 0.5])
    dz2 = np.array([1.0, 2.0, -3.0, 0.5, 0.0, 0.0])
    z = np.linspace(1.0, 2.0, 6)
    dz_copy, dz2_copy, z_copy = dz.copy(), dz2.copy(), z.copy()

    incipient_lens(z, dz, dz2, signal="vorticity", tau=0.2, smooth_window=5)
    mature_lens(pd.Series(z), prominence_relative=0.1)

    np.testing.assert_array_equal(dz, dz_copy)
    np.testing.assert_array_equal(dz2, dz2_copy)
    np.testing.assert_array_equal(z, z_copy)
