"""Tests for the calibration app's layer inspector (tools/calibration_app/).

The inspector is PURE VISUALISATION — it must never change what the package
detects, and it must never MISREPORT it either. A view that showed a plausible
parallel calculation would be worse than no view, because it would teach the
wrong thing about the very parameter being tuned. So the tests here are almost
entirely fidelity tests against the package itself:

1. **Ledger fidelity** (the risky piece). The union of the candidates the
   ledger marks ACCEPTED — plus the gaps it marks FILLED — must equal, bit for
   bit, the mask ``find_intensification_period`` / ``find_decay_period``
   produce when run in isolation on a fresh frame. Over the whole 51-track
   calibration set x several prominence and length_scale settings.
   Plus the measured reference counts, which pin the arithmetic itself.

2. **Ribbon fidelity.** Step 6 of the pipeline ribbon must equal the
   ``periods`` column ``get_periods`` returns. If it does not, the working
   frame was built wrong — the ribbon would be narrating a run that never
   happened.

3. **Mature fidelity.** The windows the mature ledger says survive the strict
   neighbour confirmation must be exactly the ones ``find_mature_stage``
   leaves behind, and the accepted extrema must be the ones the detector
   consumes.

4. **The diagnostics are actually correct** (the ``|d2z|`` knee, the normalised
   ``rel`` profile), on series whose answer is known by construction.

5. **"Grid" mode is untouched.** The phase figure and the ZIP's PNG must be
   BYTE-IDENTICAL to the research/incipient-plateau baseline — the inspector is
   an addition, not a change.
"""

import hashlib
import io
import sys
import warnings
import zipfile
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
from cyclophaser.find_stages import (  # noqa: E402
    find_decay_period, find_intensification_period, find_mature_stage,
)
from cyclophaser.plots import plot_all_periods  # noqa: E402

import layer_inspector as li  # noqa: E402

CALIB = REPO_ROOT / "tests" / "calibration_data"
ALL_TRACKS = sorted(p.stem for p in CALIB.glob("*.csv"))

# Package-default pre-processing with smoothing off — the configuration the
# reference ledger counts below were measured under.
PV_DEFAULT = dict(use_filter=True, use_smoothing=False, use_smoothing_twice=False)

# The section-3c calibration, the regime in which the prominence filter
# actually rejects candidates on real tracks.
AUTHOR_PV = dict(use_filter=True, cutoff_low=168, cutoff_high=18,
                 boundary_padding="reflect", replace_endpoints_with_lowpass=0,
                 use_smoothing=False, use_smoothing_twice=False,
                 savgol_polynomial=3)


def _series(track_id):
    return pd.read_csv(CALIB / f"{track_id}.csv", sep=";", index_col="time",
                       parse_dates=True)["min_max_zeta_850"]


def _vorticity(track_id, **pv):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return process_vorticity(pd.DataFrame({"zeta": _series(track_id)}),
                                 **{**PV_DEFAULT, **pv})


@pytest.fixture(scope="module")
def vort_cache():
    """process_vorticity is the expensive step; compute each track once."""
    return {}


def _vort(cache, track_id, key="default", **pv):
    ck = (track_id, key)
    if ck not in cache:
        cache[ck] = _vorticity(track_id, **pv)
    return cache[ck]


# ══════════════════════════════════════════════════════════════════════════════
# 1. Ledger fidelity — the union of accepted candidates IS the package's mask
# ══════════════════════════════════════════════════════════════════════════════

# 51 tracks x 6 configurations x both stage functions. The brief asked for
# >= 20 tracks x >= 2 prominence values; length_scale and the gap threshold are
# swept too because both change which arithmetic the ledger has to reproduce
# (_local_cycle_scale instead of the global length; gap bridging on or off).
LEDGER_CONFIGS = [
    (None, "global", 0.0),
    (None, "global", 0.075),
    (0.10, "global", 0.075),
    (0.10, "local",  0.075),
    (0.30, "global", 0.0),
    (0.30, "local",  0.075),
]


@pytest.mark.parametrize("prominence_relative,length_scale,gap", LEDGER_CONFIGS)
@pytest.mark.parametrize("kind", ["intensification", "decay"])
def test_ledger_union_equals_the_package_mask(vort_cache, kind,
                                              prominence_relative, length_scale,
                                              gap):
    """Every accepted candidate, and nothing else, is what the package marks.

    Run over ALL 51 calibration tracks per configuration. The oracle is the
    package function itself, executed in isolation on a fresh copy of the same
    working frame, so a divergence means the ledger is telling the user a
    different story from the one the detector acted on.
    """
    ledger_fn = (li.intensification_ledger if kind == "intensification"
                 else li.decay_ledger)
    divergences = []
    for track_id in ALL_TRACKS:
        df = li.build_working_frame(_vort(vort_cache, track_id),
                                    prominence_relative=prominence_relative)
        args = li.build_args_periods(
            threshold_intensification_length=0.075,
            threshold_intensification_gap=gap,
            threshold_decay_length=0.075,
            threshold_decay_gap=gap,
            length_scale=length_scale,
        )
        mine = ledger_fn(df, **args)["mask"]
        theirs = li.ledger_reference_mask(df, kind, **args)
        if not np.array_equal(mine, theirs):
            divergences.append((track_id, int((mine != theirs).sum())))
    assert divergences == [], f"{len(divergences)} tracks diverge: {divergences[:5]}"


# Measured on the 51 calibration tracks, intensification, length_scale='global',
# package-default pre-processing with smoothing off. These pin the ARITHMETIC
# (duration > scale x threshold), not just the agreement with the package: a
# ledger that agreed with a wrongly-parameterised run would still pass the test
# above.
INTENSIFICATION_REFERENCE = {0.075: (71, 2), 0.15: (61, 12),
                             0.25: (48, 25), 0.40: (31, 42)}


@pytest.mark.parametrize("threshold,expected", sorted(INTENSIFICATION_REFERENCE.items()))
def test_intensification_ledger_reference_counts(vort_cache, threshold, expected):
    accepted = rejected = 0
    for track_id in ALL_TRACKS:
        df = li.build_working_frame(_vort(vort_cache, track_id))
        args = li.build_args_periods(threshold_intensification_length=threshold,
                                     length_scale="global")
        ledger = li.intensification_ledger(df, **args)
        accepted += sum(c["accepted"] for c in ledger["candidates"])
        rejected += sum(not c["accepted"] for c in ledger["candidates"])
    assert (accepted, rejected) == expected


def test_decay_ledger_covers_the_last_valley_to_the_end_of_the_series(vort_cache):
    """find_decay_period runs the last z_valley to the end of the record when no
    z_peak follows it. That branch is a candidate like any other and must appear
    in the ledger — otherwise the view would silently omit the decay segment
    that most often ends a track."""
    seen = 0
    for track_id in ALL_TRACKS:
        df = li.build_working_frame(_vort(vort_cache, track_id))
        ledger = li.decay_ledger(df, **li.build_args_periods())
        tails = [c for c in ledger["candidates"] if c["to_series_end"]]
        assert len(tails) <= 1
        if tails:
            seen += 1
            assert tails[0]["end"] == df.index[-1]
    assert seen > 0, "no track exercised the last-valley branch"


def test_gap_records_use_the_opposite_comparison(vort_cache):
    """A candidate is accepted when it is LONGER than its minimum; a gap is
    filled when it is SHORTER than its maximum. Getting that backwards would be
    invisible in the union mask on most tracks, so it is pinned directly."""
    for track_id in ALL_TRACKS[:10]:
        df = li.build_working_frame(_vort(vort_cache, track_id))
        args = li.build_args_periods(threshold_intensification_gap=0.075)
        ledger = li.intensification_ledger(df, **args)
        for c in ledger["candidates"]:
            assert c["accepted"] == (c["duration"] > c["minimum"])
        for g in ledger["gaps"]:
            assert g["accepted"] == (g["duration"] < g["minimum"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. Ribbon fidelity — step 6 IS get_periods' result
# ══════════════════════════════════════════════════════════════════════════════

RIBBON_TRACKS = ALL_TRACKS[:12]        # the brief asked for >= 10
RIBBON_CONFIGS = [
    dict(),
    dict(prominence_relative=0.30, distance=3, length_scale="local"),
    dict(mature_method="amplitude", mature_amplitude_fraction=0.95,
         decay_tail_amplitude_fraction=0.05),
    dict(incipient_method="plateau", incipient_plateau_tau=0.20),
]
_EXTREMA_KEYS = ("prominence", "prominence_relative", "distance")


@pytest.mark.parametrize("config", RIBBON_CONFIGS,
                         ids=["defaults", "tight-local", "amplitude-tail", "plateau"])
def test_ribbon_step_six_equals_get_periods(vort_cache, config):
    """The last lane of the ribbon must be the run the app is showing.

    This is the check that the working frame was transcribed correctly: every
    other guarantee in this module rests on ``build_working_frame`` producing
    the frame ``get_periods`` builds internally, and this is the only way to
    verify that from outside the function.
    """
    for track_id in RIBBON_TRACKS:
        vort = _vort(vort_cache, track_id)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_result = get_periods(vort, **config)
        df = li.build_working_frame(
            vort, **{k: config.get(k) for k in _EXTREMA_KEYS})
        args = li.build_args_periods(
            **{k: v for k, v in config.items() if k not in _EXTREMA_KEYS})
        steps = li.pipeline_ribbon(df, **args)

        assert len(steps) == 6
        assert [n for n, _ in steps] == list(li.STEP_NAMES)
        pd.testing.assert_series_equal(steps[-1][1], df_result["periods"],
                                       check_names=False)


def test_ribbon_does_not_mutate_the_frame_it_is_given(vort_cache):
    df = li.build_working_frame(_vort(vort_cache, ALL_TRACKS[0]))
    snapshot = df.copy(deep=True)
    li.pipeline_ribbon(df, **li.build_args_periods())
    pd.testing.assert_frame_equal(df, snapshot)


def test_ribbon_shows_a_later_step_overwriting_an_earlier_one(vort_cache):
    """The measured reference case for the ribbon (20150069, package defaults,
    use_filter=True / use_smoothing=False): decay takes the end of the
    intensification from 28/01 17h; mature then takes stretches from BOTH
    between 28/01 13h and 20h; incipient takes the first 6 steps of the
    intensification. If the ribbon stopped showing this, it would have stopped
    doing the one thing it exists for."""
    df = li.build_working_frame(_vort(vort_cache, "20150069"))
    steps = li.pipeline_ribbon(df, **li.build_args_periods())
    got = {(r["step"], r["from"], r["to"],
            r["start"].strftime("%d/%m %H"), r["end"].strftime("%d/%m %H"), r["n"])
           for r in li.ribbon_overwrites(steps)}
    assert ("2 find_decay_period", "intensification", "decay",
            "28/01 17", "28/01 17", 1) in got
    assert ("3 find_mature_stage", "intensification", "mature",
            "28/01 13", "28/01 16", 4) in got
    assert ("3 find_mature_stage", "decay", "mature",
            "28/01 17", "28/01 20", 4) in got
    assert ("6 find_incipient_period", "intensification", "incipient",
            "27/01 04", "27/01 09", 6) in got


# ══════════════════════════════════════════════════════════════════════════════
# 3. Mature fidelity
# ══════════════════════════════════════════════════════════════════════════════

MATURE_TRACKS = ["20150377", "20190325", "20203373", "20203947", "20206498"]
MATURE_CONFIGS = [
    dict(),
    dict(prominence_relative=0.30, distance=3),
    dict(mature_method="amplitude", mature_amplitude_fraction=0.95),
    dict(length_scale="local", threshold_mature_length=0.06),
]


@pytest.mark.parametrize("track_id", MATURE_TRACKS)
@pytest.mark.parametrize("config", MATURE_CONFIGS,
                         ids=["defaults", "tight", "amplitude", "local-floor"])
def test_mature_ledger_confirmed_windows_are_the_detector_s(vort_cache, track_id,
                                                            config):
    """The windows the ledger says survive == the 'mature' find_mature_stage writes.

    ``mature_ledger`` is the one place in the module that reconstructs a
    criterion the package does not expose as a callable (the window sizing is
    inline in find_mature_stage), so it is pinned against find_mature_stage's
    own output — including the strict neighbour confirmation, whose whole point
    here is that a discarded window otherwise leaves no trace at all.
    """
    vort = _vort(vort_cache, track_id, key="author", **AUTHOR_PV)
    df = li.build_working_frame(vort, **{k: config.get(k) for k in _EXTREMA_KEYS})
    args = li.build_args_periods(
        **{k: v for k, v in config.items() if k not in _EXTREMA_KEYS})

    after_decay = find_decay_period(
        find_intensification_period(df.copy(deep=True), **args), **args)
    records = li.mature_ledger(after_decay, **args)
    mine = li.mature_confirmed_mask(after_decay, records)
    theirs = (find_mature_stage(after_decay.copy(deep=True), **args)["periods"]
              == "mature").to_numpy()
    np.testing.assert_array_equal(mine, theirs)


@pytest.mark.parametrize("track_id", MATURE_TRACKS[:3])
def test_discarded_mature_windows_carry_a_reason(vort_cache, track_id):
    """Every window that was written and then erased says WHY, in the vocabulary
    of the confirmation rule — that string is the entire point of the layer."""
    vort = _vort(vort_cache, track_id, key="author", **AUTHOR_PV)
    df = li.build_working_frame(vort)
    args = li.build_args_periods()
    after_decay = find_decay_period(
        find_intensification_period(df.copy(deep=True), **args), **args)
    allowed = {"no preceding intensification", "no following decay",
               "block starts at the beginning of the series",
               "block ends at the end of the series"}
    for rec in records_written(li.mature_ledger(after_decay, **args)):
        if rec["confirmed"]:
            assert rec["reason"] == ""
        else:
            assert rec["reason"], "a discarded window must say why"
            assert set(rec["reason"].split(" · ")) <= allowed


def records_written(records):
    return [r for r in records if r["written"]]


@pytest.mark.parametrize("track_id", MATURE_TRACKS)
@pytest.mark.parametrize("extrema", [dict(), dict(prominence_relative=0.30, distance=3),
                                     dict(prominence_relative=0.05)],
                         ids=["no-filter", "tight-0.30-d3", "loose-0.05"])
def test_mature_lens_accepted_extrema_are_the_detector_s(vort_cache, track_id,
                                                         extrema):
    """The lens's "accepted" set == the extrema mature detection actually uses.

    Ground truth is ``df['z_peaks_valleys']`` from a real ``get_periods`` run —
    the exact column ``find_mature_stage`` reads its z_valleys and z_peaks from.
    (Carried over from the abandoned research/app-phase-focus branch, which is
    where this lens and its test were first written.)
    """
    vort = _vort(vort_cache, track_id, key="author", **AUTHOR_PV)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_result = get_periods(vort, **extrema)
    lens = li.mature_lens(df_result["z"], **extrema)
    for kind in ("peak", "valley"):
        np.testing.assert_array_equal(
            lens[f"accepted_{kind}s"],
            np.flatnonzero((df_result["z_peaks_valleys"] == kind).to_numpy()))


def test_effective_threshold_explains_the_classification(vort_cache):
    """The drawn threshold line separates accepted from rejected, exactly.

    No distance filter, so prominence is the ONLY reason an interior candidate
    can be dropped and the line must account for every rejection. Boundary
    extrema are excluded: the package preserves them unconditionally.
    """
    for track_id in MATURE_TRACKS:
        vort = _vort(vort_cache, track_id, key="author", **AUTHOR_PV)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df_result = get_periods(vort, prominence_relative=0.30)
        lens = li.mature_lens(df_result["z"], prominence_relative=0.30)
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


# ══════════════════════════════════════════════════════════════════════════════
# 4. Diagnostics on series with a known answer
# ══════════════════════════════════════════════════════════════════════════════

def test_knee_index_on_a_known_series():
    """|d2z| is largest at a designed spike inside the first half."""
    dz2 = np.zeros(100)
    dz2[20] = 3.0        # the knee: the largest |.| in the leading half
    dz2[10] = -1.5
    dz2[80] = -50.0      # a far larger turn later on, which must NOT win
    assert li.knee_index(dz2) == 20
    dz2[20] = -3.0       # sign is irrelevant — it is |d2z| that is maximised
    assert li.knee_index(dz2) == 20


def test_knee_index_window_follows_the_fraction():
    dz2 = np.zeros(100)
    dz2[15] = 1.0
    dz2[40] = 5.0
    assert li.knee_index(dz2, fraction=0.5) == 40    # window [0, 50)
    assert li.knee_index(dz2, fraction=0.2) == 15    # window [0, 20)


def test_knee_index_degenerate_inputs():
    assert li.knee_index(np.array([])) == 0
    assert li.knee_index(np.array([np.nan, np.nan])) == 0
    assert li.knee_index(np.zeros(10)) == 0          # flat: argmax is index 0


def test_rel_profile_is_abs_dz_over_its_max():
    """rel(t) on the "derivative" signal is exactly |dz| / max|dz|."""
    dz = np.array([0.0, -1.0, 2.0, -8.0, 4.0, 0.5])
    lens = li.incipient_lens(z_unfil=np.zeros_like(dz), dz=dz,
                             dz2=np.zeros_like(dz), signal="derivative", tau=0.20)
    np.testing.assert_allclose(lens["rel_raw"], np.abs(dz) / 8.0)
    # tau=0.20 -> first sample with |dz|/8 >= 0.2 is index 2 (2/8 = 0.25);
    # index 1 is 1/8 = 0.125, below tau.
    assert lens["boundary_raw"] == 2
    # "derivative" reads a curve the pipeline already filtered, so the probe
    # smoothing is inert there and both profiles must coincide.
    assert lens["smoothing_applies"] is False
    np.testing.assert_array_equal(lens["rel_raw"], lens["rel_smoothed"])


def test_rel_profile_flat_signal_is_all_zero():
    flat = np.zeros(20)
    lens = li.incipient_lens(z_unfil=flat, dz=flat, dz2=flat,
                             signal="derivative", tau=0.20)
    np.testing.assert_array_equal(lens["rel_raw"], np.zeros(20))
    assert lens["boundary_raw"] == 0        # no crossing -> no incipient phase


def test_probe_smoothing_is_reported_only_where_it_applies():
    """smoothing_applies mirrors the package's own "vorticity only" rule."""
    x = np.linspace(0, 1, 60) ** 2
    common = dict(z_unfil=x, dz=np.gradient(x), dz2=np.gradient(np.gradient(x)),
                  tau=0.20, smooth_polyorder=3)
    assert li.incipient_lens(signal="vorticity", smooth_window=9, **common)["smoothing_applies"]
    assert not li.incipient_lens(signal="vorticity", smooth_window=0, **common)["smoothing_applies"]
    assert not li.incipient_lens(signal="derivative", smooth_window=9, **common)["smoothing_applies"]


@pytest.mark.parametrize("track_id", ["20190325", "20206498"])
def test_incipient_boundary_is_read_back_not_recomputed(vort_cache, track_id):
    """``incipient_lead`` reports the boundary the RUN produced.

    Under the plateau rule with this calibration it coincides with the lens's
    own tau crossing; the layer draws both precisely so a divergence (the
    catch-all fillna extending the phase past the crossing) stays visible
    rather than being silently reconciled.
    """
    vort = _vort(vort_cache, track_id, key="author", **AUTHOR_PV)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_result = get_periods(vort, incipient_method="plateau",
                                incipient_plateau_tau=0.20)
    lens = li.incipient_lens(df_result["z_unfil"], df_result["dz"],
                             df_result["dz2"], signal="derivative", tau=0.20)
    assert li.incipient_lead(df_result) == lens["boundary_raw"]


def test_helpers_do_not_mutate_their_input_arrays():
    dz = np.array([0.0, -1.0, 2.0, -8.0, 4.0, 0.5])
    dz2 = np.array([1.0, 2.0, -3.0, 0.5, 0.0, 0.0])
    z = np.linspace(1.0, 2.0, 6)
    dz_copy, dz2_copy, z_copy = dz.copy(), dz2.copy(), z.copy()

    li.incipient_lens(z, dz, dz2, signal="vorticity", tau=0.2, smooth_window=5)
    li.mature_lens(pd.Series(z), prominence_relative=0.1)

    np.testing.assert_array_equal(dz, dz_copy)
    np.testing.assert_array_equal(dz2, dz2_copy)
    np.testing.assert_array_equal(z, z_copy)


def test_build_args_periods_rejects_a_non_parameter():
    """A typo'd threshold silently falling back to the default would make the
    ribbon and the ledgers explain a different run from the one on screen."""
    with pytest.raises(KeyError):
        li.build_args_periods(threshold_intensification_lenght=0.075)


# ══════════════════════════════════════════════════════════════════════════════
# 5. "Grid" mode is byte-identical to the research/incipient-plateau baseline
# ══════════════════════════════════════════════════════════════════════════════

GRID_TRACKS = ["20150069", "20190325", "20206498"]


def _phase_png(track_id, figsize=(12, 5), show_title=True) -> bytes:
    """The Grid mode's phase figure, produced exactly as _render_periods_png does.

    Transcribed from the app rather than imported because importing app.py
    executes a Streamlit script; the point here is the matplotlib call chain,
    which is what a regression would break.
    """
    vort = _vorticity(track_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_result = get_periods(vort, plot=False, plot_steps=False)
    periods_dict = periods_to_dict(df_result)

    fig, ax = plt.subplots(figsize=figsize)
    try:
        plot_all_periods(periods_dict, df_result, ax=ax, vorticity=vort)
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    except Exception:
        pass
    if show_title:
        ax.set_title(track_id, fontweight="bold")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


@pytest.mark.parametrize("track_id", GRID_TRACKS)
def test_grid_phase_figure_is_unchanged_by_the_inspector(track_id):
    """Rendering the inspector's layers must leave the Grid figure identical.

    The realistic regression is a helper mutating the shared frame (a column
    overwritten, an index re-sorted), which would silently change the figure
    the next time it is drawn. So: render, run EVERY inspector computation over
    the same objects, render again, and require byte equality.
    """
    before = _phase_png(track_id)

    vort = _vorticity(track_id)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_result = get_periods(vort)
    snapshot = df_result.copy(deep=True)

    args = li.build_args_periods()
    work = li.build_working_frame(vort)
    li.pipeline_ribbon(work, **args)
    li.intensification_ledger(work, **args)
    li.decay_ledger(work, **args)
    after_decay = find_decay_period(
        find_intensification_period(work.copy(deep=True), **args), **args)
    li.mature_ledger(after_decay, **args)
    li.mature_lens(df_result["z"])
    li.incipient_lens(df_result["z_unfil"], df_result["dz"], df_result["dz2"])

    after = _phase_png(track_id)
    assert hashlib.md5(after).hexdigest() == hashlib.md5(before).hexdigest()
    pd.testing.assert_frame_equal(df_result, snapshot)


def test_grid_zip_png_is_the_same_figure_as_the_export():
    """The ZIP entry is the phase PNG at the export size, unchanged.

    Guards the export path specifically: the inspector added a second renderer,
    and the exported PNG has to stay deterministic matplotlib output.
    """
    png = _phase_png("20190325", figsize=(12, 5), show_title=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("20190325_periods.png", png)
    buf.seek(0)
    with zipfile.ZipFile(buf) as zf:
        assert zf.read("20190325_periods.png") == png
    assert png.startswith(b"\x89PNG")


# ══════════════════════════════════════════════════════════════════════════════
# 6. The renderers consume the helpers without touching detection
# ══════════════════════════════════════════════════════════════════════════════

def test_plotly_inspector_starts_with_every_layer_on(vort_cache):
    """The inspector opens with everything visible, and nothing is missing.

    Every pipeline series and every extrema column is a trace, all of them
    visible; phase shading is present as shapes with a client-side on/off
    button (a full-height band cannot be a legend item in Plotly). Switching a
    layer off is a legend click, which leaves it in the figure as
    'legendonly' — that is what makes the toggle free.
    """
    pytest.importorskip("plotly")
    from inspector_plotly import build_inspector_figure

    vort = _vorticity("20190325")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_result = get_periods(vort)
    fig = build_inspector_figure("20190325", vort, df_result,
                                 periods_to_dict(df_result))

    visible = {t.name for t in fig.data if t.visible is True}
    for expected in ("zeta (raw input)", "filtered_vorticity (Lanczos)",
                     "vorticity_smoothed (Savgol 1)",
                     "vorticity_smoothed2 (what detection reads)",
                     "dz_dt_filt", "dz_dt_smoothed2 (what detection reads)",
                     "dz_dt2_filt", "dz_dt2_smoothed2 (what detection reads)",
                     "z_peaks_valleys", "dz_peaks_valleys", "dz2_peaks_valleys"):
        assert expected in visible, expected
    assert not [t for t in fig.data if t.visible == "legendonly"]
    # Phase shading is always present and has no toggle: it is the background
    # every other layer is read against.
    assert len(fig.layout.shapes) > 0
    assert len(fig.layout.updatemenus) == 0


def test_plotly_inspector_shared_scale_spreads_every_curve_over_the_panel(vort_cache):
    """Rescaling is what lets one axis hold curves of different magnitude.

    With it on every plotted curve spans exactly [0, 1] — the panel is then
    read for shape, which is what the phase rules act on — and the hover still
    carries the RAW value, so the number is never lost. With it off the
    plotted values ARE the raw ones.
    """
    pytest.importorskip("plotly")
    from inspector_plotly import build_inspector_figure

    vort = _vorticity("20190325")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_result = get_periods(vort)
    common = ("20190325", vort, df_result, periods_to_dict(df_result))

    normed = build_inspector_figure(*common, normalize=True)
    series = [t for t in normed.data
              if t.name and t.name.startswith(("zeta", "filtered", "vorticity",
                                               "dz_dt"))]
    assert len(series) == 8
    for t in series:
        y = np.asarray(t.y, dtype=float)
        assert np.isclose(np.nanmin(y), 0.0), t.name
        assert np.isclose(np.nanmax(y), 1.0), t.name
        raw = np.asarray([c[0] for c in t.customdata], dtype=float)
        lo, hi = np.nanmin(raw), np.nanmax(raw)
        np.testing.assert_allclose(y * (hi - lo) + lo, raw, rtol=1e-9)

    plain = build_inspector_figure(*common, normalize=False)
    raw_trace = next(t for t in plain.data if t.name == "zeta (raw input)")
    np.testing.assert_allclose(np.asarray(raw_trace.y, dtype=float),
                               np.asarray(vort["zeta"].values, dtype=float))


def test_normalise_series_spreads_over_zero_to_one():
    y = np.array([-4.0, -2.0, 0.0, 1.0, 2.0])
    out, lo, hi = li.normalise_series(y)
    assert (lo, hi) == (-4.0, 2.0)
    np.testing.assert_allclose(out, (y + 4.0) / 6.0)
    assert out[0] == 0.0 and out[-1] == 1.0
    # A flat series has no range to spread over: centre it instead of dividing
    # by zero.
    flat, flo, fhi = li.normalise_series(np.zeros(5))
    np.testing.assert_array_equal(flat, np.full(5, 0.5))
    assert flo == fhi


def test_rescaler_puts_an_overlay_on_the_curve_it_annotates():
    """An overlay must use the SAME transform as the curve it is drawn over,
    or a ledger segment would float above or below the z line it describes."""
    z = np.array([-4.0, -2.0, 0.0, 2.0])
    f = li.rescaler(z, normalize=True)
    np.testing.assert_allclose(f(z), [0.0, 1 / 3, 0.5 + 1 / 6, 1.0])
    # A subset of the same curve lands exactly on the full curve's rendering.
    np.testing.assert_allclose(f(z[1:3]), f(z)[1:3])
    # Off, the transform is the identity.
    np.testing.assert_array_equal(li.rescaler(z, normalize=False)(z), z)
