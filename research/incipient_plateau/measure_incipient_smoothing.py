"""Choose the incipient probe's smoothing window and boundary criterion BY NUMBER.

MEASUREMENT ONLY — does not modify ``cyclophaser/``. Sibling of
``measure_incipient.py``; that script and its three output artefacts are left
untouched.

What this answers
-----------------
The incipient probe reads its rate on ``d(zeta_raw)/dt``
(``incipient_plateau_signal="vorticity"``), which is immune to the pipeline's
edge artifacts but exposed to raw noise. ``incipient_smooth_window`` gives that
probe its own light denoising. Two open choices follow, and they are settled
here against the synthetic ground truth rather than by eye:

  1. how wide the smoothing window should be, and
  2. which boundary criterion to read off the denoised curve.

Three candidate criteria are compared:

  (a) tau-slope, single crossing   — first t with rel(t) >= tau
  (b) tau-slope, sustained k       — first t starting a run of k samples >= tau
  (c) knee (MEASUREMENT ONLY, deliberately NOT in the package) — argmax of
      |d2z| over the first half, restricted to before the slope peak. This is
      the curvature-based alternative: instead of asking "when does the rate
      exceed a level", it asks "where does the curve actually turn". It carries
      no threshold at all, which is its appeal and the reason it is worth
      measuring before committing the package to a tau.

Ground truth
------------
Only the cases whose segment list opens with a literal ``Ic`` segment have a
checkable boundary — its length. The rest have a genuine initial plateau but no
designed boundary index (see the classification block in
``tests/synthetic/cases.py``), so they are reported but not scored.

Run from the repo root:
    python research/incipient_plateau/measure_incipient_smoothing.py
    python research/incipient_plateau/measure_incipient_smoothing.py --no-figures
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from cyclophaser.determine_periods import get_periods, process_vorticity
from cyclophaser.find_stages import (
    _incipient_plateau_boundary, _incipient_plateau_rel, _smooth_incipient_probe,
)
from tests.synthetic.cases import (
    CASES, NOISY_CASE_IDS, STEEP_START_CASE_IDS, preset_for,
)

OUT = Path(__file__).resolve().parent
FIG = OUT / "figures" / "incipient_smoothing"
CALIB = REPO_ROOT / "tests" / "calibration_data"

WINDOWS = [0, 3, 5, 7, 9]
TAUS = [0.10, 0.15, 0.20, 0.30]
K_SUSTAINED = 3
POLYORDER = 3
TOLERANCE = 6          # the synthetic suite's own tolerance, in timesteps

# Designed Ic boundary = length of the leading 'Ic' segment.
GROUND_TRUTH = {
    cid: c["segments"][0]["n"]
    for cid, c in CASES.items()
    if c["segments"] and c["segments"][0]["type"] == "Ic"
}

# The author's validated section-3c calibration, for the real-track figures.
AUTHOR_PV = dict(use_filter=True, cutoff_low=168, cutoff_high=18,
                 boundary_padding="reflect", replace_endpoints_with_lowpass=0,
                 use_smoothing=False, use_smoothing_twice=False,
                 savgol_polynomial=3)
AUTHOR_GP = dict(prominence_relative=0.3, distance=3, mature_method="amplitude",
                 mature_amplitude_fraction=0.95,
                 decay_tail_amplitude_fraction=0.05, length_scale="local",
                 threshold_mature_distance=0.18)

FIGURE_TRACKS = ["20190325", "20206498", "20150377", "20190639", "20203373",
                 "20170225", "20204655"]


# ── candidates ───────────────────────────────────────────────────────────────
def knee_index(z_probe):
    """Curvature knee: argmax |d2z| over the first half, before the slope peak.

    MEASUREMENT ONLY — deliberately not in the package. Restricting to the
    stretch before the slope peak is what makes it the *onset* knee rather than
    the (usually larger) curvature at the top of the deepening; capping at the
    first half keeps it from wandering into the decay leg on short series.
    Index 0 is excluded: np.gradient's one-sided endpoint formula makes |d2z|
    at the boundary unrepresentative.
    """
    z = np.asarray(z_probe, dtype=float)
    n = z.size
    if n < 5:
        return 0
    d1 = np.gradient(z)
    d2 = np.abs(np.gradient(d1))
    slope_peak = int(np.argmax(np.abs(d1)))
    stop = max(2, min(slope_peak if slope_peak > 1 else n // 2, n // 2))
    seg = d2[1:stop]
    if seg.size == 0:
        return 0
    return int(np.argmax(seg)) + 1


def probe_curves(df, window, polyorder=POLYORDER):
    """The denoised probe curve and its normalised rate, as the package sees them."""
    z_raw = np.asarray(df['z_unfil'], dtype=float)
    z_s = _smooth_incipient_probe(z_raw, window, polyorder)
    rel = _incipient_plateau_rel(df, "vorticity", window, polyorder)
    return z_raw, z_s, rel


def candidates_for(df, window):
    """All boundary candidates on one series at one smoothing window."""
    _, z_s, rel = probe_curves(df, window)
    out = {}
    for tau in TAUS:
        out[f"tau{tau:.2f}_single"] = _incipient_plateau_boundary(
            rel, tau, "single", K_SUSTAINED)
        out[f"tau{tau:.2f}_sustained{K_SUSTAINED}"] = _incipient_plateau_boundary(
            rel, tau, "sustained", K_SUSTAINED)
    out["knee"] = knee_index(z_s)
    return out


# ── synthetic sweep ──────────────────────────────────────────────────────────
def run_synthetic():
    rows = []
    for cid, case in CASES.items():
        series = case["series"]
        preset = preset_for(cid)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": series}), **preset)
            df = get_periods(vort)
        gt = GROUND_TRUTH.get(cid)
        for w in WINDOWS:
            for name, idx in candidates_for(df, w).items():
                rows.append({
                    "case": cid,
                    "group": "noisy" if cid in NOISY_CASE_IDS else "clean",
                    "steep_start": cid in STEEP_START_CASE_IDS,
                    "window": w,
                    "candidate": name,
                    "boundary": idx,
                    "gt": gt if gt is not None else np.nan,
                    "error": (idx - gt) if gt is not None else np.nan,
                })
    return pd.DataFrame(rows)


def summarise(d: pd.DataFrame) -> str:
    lines, A = [], lambda t: lines.append(t)
    scored = d[d["gt"].notna()]

    A("=" * 78)
    A("TABLE 1 — mean |error| vs ground truth, by candidate x smoothing window")
    A("=" * 78)
    A(f"(scored on the {scored['case'].nunique()} designed-Ic cases; "
      f"suite tolerance = {TOLERANCE} timesteps)")
    piv = scored.pivot_table(index="candidate", columns="window",
                             values="error", aggfunc=lambda e: np.abs(e).mean())
    A(piv.round(2).to_string())

    A("")
    A("=" * 78)
    A("TABLE 2 — worst |error| (the stability criterion)")
    A("=" * 78)
    piv2 = scored.pivot_table(index="candidate", columns="window",
                              values="error", aggfunc=lambda e: np.abs(e).max())
    A(piv2.round(0).to_string())

    A("")
    A("=" * 78)
    A("TABLE 3 — cases INSIDE tolerance, out of the designed-Ic set")
    A("=" * 78)
    piv3 = scored.pivot_table(index="candidate", columns="window", values="error",
                              aggfunc=lambda e: int((np.abs(e) <= TOLERANCE).sum()))
    A(piv3.to_string())

    A("")
    A("=" * 78)
    A("TABLE 4 — false positives: the two steep-start true negatives")
    A("=" * 78)
    A("(these are designed with a linear onset; boundary 0 == correctly refused)")
    steep = d[d["steep_start"]]
    piv4 = steep.pivot_table(index="candidate", columns="window",
                             values="boundary", aggfunc=lambda b: int((b > 0).sum()))
    A(piv4.to_string())

    A("")
    A("=" * 78)
    A("TABLE 5 — per-case boundary, designed-Ic cases")
    A("=" * 78)
    for cid in sorted(GROUND_TRUTH):
        sub = d[d["case"] == cid]
        A(f"\\n{cid}  (ground truth {GROUND_TRUTH[cid]}, "
          f"{'noisy' if cid in NOISY_CASE_IDS else 'clean'})")
        A(sub.pivot_table(index="candidate", columns="window",
                          values="boundary", aggfunc="first").to_string())

    A("")
    A("=" * 78)
    A("TABLE 4b — MISSES: designed-Ic cases that get NO incipient phase at all")
    A("=" * 78)
    A("(boundary 0 on a case that HAS a designed Ic segment — a qualitative")
    A(" failure, not a 3-step error, which is why it is counted separately)")
    piv4b = scored.pivot_table(index="candidate", columns="window",
                               values="boundary",
                               aggfunc=lambda b: int((b == 0).sum()))
    A(piv4b.to_string())

    A("")
    A("=" * 78)
    A("BEST BY NUMBER")
    A("=" * 78)
    agg = (scored.groupby(["candidate", "window"])["error"]
           .agg(mean_abs=lambda e: np.abs(e).mean(),
                worst=lambda e: np.abs(e).max())
           .reset_index())
    miss = (scored.groupby(["candidate", "window"])["boundary"]
            .agg(misses=lambda b: int((b == 0).sum())).reset_index())
    fp = (steep.groupby(["candidate", "window"])["boundary"]
          .agg(false_pos=lambda b: int((b > 0).sum())).reset_index())
    agg = agg.merge(miss, on=["candidate", "window"], how="left")
    agg = agg.merge(fp, on=["candidate", "window"], how="left")
    agg = agg.sort_values(["false_pos", "misses", "mean_abs", "worst"])
    A("ranked by (false positives, misses, mean |error|, worst |error|):")
    A(agg.head(14).to_string(index=False))
    A("")
    A("Reading: `false_pos` counts the two linear-onset true negatives that")
    A("wrongly receive an incipient phase; `misses` counts designed-Ic cases")
    A("left with none. A criterion must score 0 on both before its error")
    A("matters at all.")
    return "\\n".join(lines)


# ── figures ──────────────────────────────────────────────────────────────────
def make_figure(name, series, df, out_path, windows=(0, 5, 9), gt=None):
    """Raw vs smoothed probe on the dz panel, tau on the rel profile, knee marked."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.gridspec as gridspec
    import matplotlib.lines as mlines
    import matplotlib.pyplot as plt

    n = len(series)
    t = np.arange(n)
    times = list(series.index)
    z_raw = np.asarray(df['z_unfil'], dtype=float)

    fig = plt.figure(figsize=(19, 11))
    dur = (series.index[-1] - series.index[0]).total_seconds() / 86400
    fig.suptitle(
        f"{name}  ·  {n} pts  ·  {dur:.1f} dias  ·  sondagem da incipiente\\n"
        f"linha 1: z cru vs suavizado  ·  linha 2: |dz| da sondagem  ·  "
        f"linha 3: rel(t) com tau e joelho"
        + (f"  ·  ground truth Ic = {gt}" if gt is not None else ""),
        fontsize=11, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(3, len(windows), figure=fig, hspace=0.45, wspace=0.12,
                           top=0.88, bottom=0.12)

    for ci, w in enumerate(windows):
        _, z_s, rel = probe_curves(df, w)
        kn = knee_index(z_s)
        b_single = _incipient_plateau_boundary(rel, 0.20, "single", K_SUSTAINED)
        b_sust = _incipient_plateau_boundary(rel, 0.20, "sustained", K_SUSTAINED)

        # row 0 — raw vs smoothed probe curve
        ax = fig.add_subplot(gs[0, ci])
        ax.plot(t, z_raw, color="#999999", lw=1.2, label="z cru")
        ax.plot(t, z_s, color="#1d3557", lw=2.0, label="z sondagem (suavizado)")
        ax.set_title(f"incipient_smooth_window = {w}"
                     + ("  (desligado)" if w == 0 else ""),
                     fontsize=9.5, pad=6)
        ax.set_ylabel("z", fontsize=8)
        if ci == 0:
            ax.legend(fontsize=7, loc="lower right")

        # row 1 — |dz| of the probe, raw vs smoothed
        ax1 = fig.add_subplot(gs[1, ci])
        ax1.plot(t, np.abs(np.gradient(z_raw)), color="#999999", lw=1.2)
        ax1.plot(t, np.abs(np.gradient(z_s)), color="#457b9d", lw=2.0)
        ax1.set_ylabel("|dz| da sondagem", fontsize=8)

        # row 2 — normalised rate with tau lines and candidates
        ax2 = fig.add_subplot(gs[2, ci])
        ax2.plot(t, rel, color="#e63946", lw=1.8)
        for tau in TAUS:
            ax2.axhline(tau, color="#8856a7", lw=0.6, ls=":", alpha=0.7)
        ax2.set_ylim(0, 1.02)
        ax2.set_ylabel("rel(t) = |dz|/max|dz|", fontsize=8)
        ax2.set_xlabel("passo", fontsize=8)

        for a in (ax, ax1, ax2):
            a.set_xlim(-0.5, n - 0.5)
            a.tick_params(labelsize=7)
            if gt is not None:
                a.axvline(gt, color="#00a000", lw=2.0, ls=":", zorder=6)
            a.axvline(kn, color="#ff7f00", lw=1.8, zorder=5)
            if b_single > 0:
                a.axvline(b_single, color="#d000d0", lw=1.6, zorder=5)
            if b_sust > 0:
                a.axvline(b_sust, color="#0080a0", lw=1.4, ls="--", zorder=5)
        ax2.set_title(f"tau0.20 single={b_single}  sustained={b_sust}  joelho={kn}",
                      fontsize=8)

    handles = [
        mlines.Line2D([], [], color="#999999", lw=1.2, label="cru"),
        mlines.Line2D([], [], color="#1d3557", lw=2.0, label="sondagem suavizada"),
        mlines.Line2D([], [], color="#ff7f00", lw=1.8, label="joelho (max |d2z|)"),
        mlines.Line2D([], [], color="#d000d0", lw=1.6, label="tau=0.20 single"),
        mlines.Line2D([], [], color="#0080a0", lw=1.4, ls="--", label="tau=0.20 sustained k=3"),
        mlines.Line2D([], [], color="#00a000", lw=2.0, ls=":", label="ground truth Ic"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 0.02))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def real_track_table():
    """rel(0) on the real tracks, both signals, across the smoothing sweep.

    This is the decisive table for real-track validation: tau can only fire if
    it exceeds rel(0), so a rel(0) above every usable tau means the criterion
    refuses outright.
    """
    lines, A = [], lambda t: lines.append(t)
    wins = [0, 3, 5, 7, 9, 15, 21]
    A("=" * 78)
    A("TABLE 6 — rel(0) on the real tracks (author's 3c calibration)")
    A("=" * 78)
    A("tau must EXCEED rel(0) for a boundary to exist at all.")
    A("")
    A("signal='vorticity' — raw gradient, the path the smoothing acts on:")
    A(f"{'track':10s}" + "".join(f"{'w=' + str(w):>9}" for w in wins))
    rows = []
    for tid in FIGURE_TRACKS:
        raw = pd.read_csv(CALIB / f"{tid}.csv", sep=";", index_col="time",
                          parse_dates=True)["min_max_zeta_850"].rename("zeta")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": raw}), **AUTHOR_PV)
            df = get_periods(vort, **AUTHOR_GP)
        vals = [_incipient_plateau_rel(df, "vorticity", w, POLYORDER)[0] for w in wins]
        deriv = _incipient_plateau_rel(df, "derivative", 0, POLYORDER)[0]
        A(f"{tid:10s}" + "".join(f"{v:>9.3f}" for v in vals))
        rows.append({"track": tid, "rel0_derivative": deriv,
                     **{f"rel0_vorticity_w{w}": v for w, v in zip(wins, vals)}})
    A("")
    A("signal='derivative' — the pipeline-filtered curve, for reference:")
    for r in rows:
        A(f"{r['track']:10s}{r['rel0_derivative']:>9.3f}")
    A("")
    A("Reading: under the author's 3c calibration the Lanczos already controls")
    A("the edge, so 'derivative' sits at 0.005-0.091 — far below any usable tau.")
    A("'vorticity' sits at 0.18-0.68 and the smoothing brings it down only")
    A("slowly and NON-MONOTONICALLY (20170225: 0.436 -> 0.656 at w=5 -> 0.382 at")
    A("w=7 -> 0.467 at w=9), so a wider window is not reliably better. The")
    A("smoothing rescues 'vorticity' on the SYNTHETIC noisy series, where the")
    A("input is genuinely unfiltered; on real TRACK data the Lanczos is already")
    A("doing that job.")
    return "\n".join(lines), pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-figures", action="store_true")
    args = ap.parse_args()

    d = run_synthetic()
    d.to_csv(OUT / "incipient_smoothing_sweep.csv", index=False)
    print(f"wrote {OUT / 'incipient_smoothing_sweep.csv'} ({len(d)} rows)")

    text = summarise(d).replace("\\n", "\n")
    rt_text, rt_df = real_track_table()
    rt_df.to_csv(OUT / "incipient_smoothing_real_rel0.csv", index=False)
    text = text + "\n\n" + rt_text.replace("\\n", "\n")
    print(text)
    (OUT / "incipient_smoothing_tables.txt").write_text(text)
    print(f"\nwrote {OUT / 'incipient_smoothing_tables.txt'}")

    if args.no_figures:
        return

    for cid, case in CASES.items():
        preset = preset_for(cid)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": case["series"]}), **preset)
            df = get_periods(vort)
        make_figure(cid, case["series"], df, FIG / "synthetic" / f"{cid}.png",
                    gt=GROUND_TRUTH.get(cid))

    print("\n--- real tracks (author's 3c calibration) ---")
    for tid in FIGURE_TRACKS:
        raw = pd.read_csv(CALIB / f"{tid}.csv", sep=";", index_col="time",
                          parse_dates=True)["min_max_zeta_850"].rename("zeta")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": raw}), **AUTHOR_PV)
            df = get_periods(vort, **AUTHOR_GP)
        make_figure(tid, raw, df, FIG / "real" / f"{tid}.png")
        _, z_s, rel = probe_curves(df, 5)
        print(f"  {tid}: w=5 tau0.20 single="
              f"{_incipient_plateau_boundary(rel, 0.20, 'single', K_SUSTAINED)} "
              f"joelho={knee_index(z_s)}")
    print(f"\nfigures -> {FIG}")


if __name__ == "__main__":
    main()
