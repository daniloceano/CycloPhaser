"""Phase-focus lenses for the calibration app — pure computation + drawing.

PURE VISUALISATION. Nothing here changes phase detection: every quantity a
lens displays is either read back from the package (``find_peaks_valleys``,
``_incipient_plateau_rel``, ``_incipient_plateau_boundary``,
``_smooth_incipient_probe``) or a diagnostic computed on top of it. The module
deliberately does not import ``streamlit`` so the maths can be unit-tested and
re-used by the offline figure script in ``research/app_phase_focus/``.

Two lenses
----------
``mature_lens``
    Which z peaks/valleys the detector actually consumes, and which candidates
    the prominence filter threw away. Fidelity is by CONSTRUCTION: the accepted
    set is read from the very same ``find_peaks_valleys`` call that
    ``get_periods`` makes to build ``df['z_peaks_valleys']`` — the column
    ``find_mature_stage`` iterates. The lens never re-implements the criterion.

``incipient_lens``
    The signal the plateau rule measures: the raw vs probe-smoothed curve, the
    normalised slope profile ``rel`` against ``tau``, and the ``|d2z|`` knee as
    a diagnostic of where the series stops being flat.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.signal import peak_prominences

from cyclophaser.determine_periods import find_peaks_valleys
from cyclophaser.find_stages import (
    _incipient_plateau_boundary,
    _incipient_plateau_rel,
    _smooth_incipient_probe,
)

# Marker / colour conventions, shared with the research figures in
# research/incipient_plateau/ so the two read the same way.
C_ACCEPT_PEAK = "#2171b5"
C_ACCEPT_VALLEY = "#cb181d"
C_REJECT = "#9e9e9e"
C_THRESHOLD = "#8856a7"
C_Z = "#1d3557"
C_DZ = "#457b9d"
C_DZ2 = "#6a51a3"
C_REL = "#e63946"
C_SMOOTH = "#e07b00"
C_BOUNDARY = "#d000d0"
C_KNEE = "#00a000"

PHASE_COLORS = {"incipient": "#65a1e6", "intensification": "#f7b538",
                "mature": "#d62828", "decay": "#9aa981", "residual": "#999999"}


# ══════════════════════════════════════════════════════════════════════════════
# Mature lens — peaks/valleys of z and the prominence filter that selects them
# ══════════════════════════════════════════════════════════════════════════════

def _label_positions(labels: pd.Series, kind: str) -> np.ndarray:
    """Positional indices carrying `kind` ('peak'/'valley') in a labels Series."""
    return np.flatnonzero((labels == kind).to_numpy())


def _effective_threshold(signed_data: np.ndarray,
                         interior: np.ndarray,
                         prominence,
                         prominence_relative):
    """Prominences of `interior` and the prominence threshold actually applied.

    Replicates ``determine_periods._refine_extrema``'s bookkeeping exactly so
    the horizontal line a lens draws is the line the filter used, not an
    approximation of it:

      * prominences are computed once, with ``peak_prominences`` on
        ``signed_data`` (``data`` for peaks, ``-data`` for valleys);
      * absolute filtering runs first;
      * the relative denominator is the max prominence of the set that SURVIVED
        the absolute step, not of the original set.

    Both filters are ``prom >= threshold`` tests on the same prominence values,
    so a single number — ``max(absolute, relative x denominator)`` — describes
    the combined cut and can be drawn as one line.

    Returns:
        (prom_vals, threshold) where `threshold` is None when neither
        prominence filter is active (nothing was cut on prominence grounds).
    """
    if interior.size == 0:
        return np.zeros(0), None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        prom_vals = peak_prominences(signed_data, interior)[0]

    if prominence is None and prominence_relative is None:
        return prom_vals, None

    threshold = float(prominence) if prominence is not None else 0.0
    surviving = prom_vals[prom_vals >= threshold] if prominence is not None else prom_vals
    if prominence_relative is not None and surviving.size:
        max_prom = float(surviving.max())
        if max_prom > 0.0:
            threshold = max(threshold, float(prominence_relative) * max_prom)
    return prom_vals, threshold


def mature_lens(z: pd.Series,
                prominence=None,
                prominence_relative=None,
                distance=None) -> dict:
    """Accepted/rejected z extrema under the current extrema-filter settings.

    Args:
        z: the smoothed vorticity the detector runs on (``df['z']`` /
           ``vorticity_smoothed2``), indexed as in the working frame.
        prominence, prominence_relative, distance: the extrema-filter
           parameters, passed through to ``find_peaks_valleys`` verbatim.

    Returns:
        dict with, for each of 'peak' and 'valley':
          ``accepted_<kind>s`` / ``rejected_<kind>s`` — positional indices;
          ``<kind>_prominences`` — {position: prominence} for interior
            candidates (boundary extrema are unconditionally preserved and
            have no meaningful prominence, so they are absent);
          ``<kind>_threshold`` — the effective prominence cut, or None.
        plus ``n`` (series length) and ``boundary`` (preserved boundary
        positions).

    The accepted sets are read from ``find_peaks_valleys`` called with exactly
    the pipeline's arguments, so they are the same objects ``find_mature_stage``
    consumes — including the ``result.iloc[zeros] = 0`` overwrite, which the
    package applies after prominence filtering.
    """
    data = np.asarray(z, dtype=float)
    n = data.size

    candidates = find_peaks_valleys(z)
    accepted = find_peaks_valleys(z, prominence=prominence,
                                  prominence_relative=prominence_relative,
                                  distance=distance)

    out = {"n": n, "boundary": tuple(i for i in (0, n - 1) if n > 0)}
    for kind, signed in (("peak", data), ("valley", -data)):
        cand = _label_positions(candidates, kind)
        acc = _label_positions(accepted, kind)
        rej = np.array(sorted(set(cand.tolist()) - set(acc.tolist())), dtype=int)

        interior = np.array([i for i in cand if i not in (0, n - 1)], dtype=int)
        prom_vals, threshold = _effective_threshold(
            signed, interior, prominence, prominence_relative)

        out[f"accepted_{kind}s"] = acc
        out[f"rejected_{kind}s"] = rej
        out[f"{kind}_prominences"] = dict(zip(interior.tolist(),
                                              prom_vals.tolist()))
        out[f"{kind}_threshold"] = threshold
    return out


# ══════════════════════════════════════════════════════════════════════════════
# Incipient lens — the probe curve, rel(t) vs tau, and the |d2z| knee
# ══════════════════════════════════════════════════════════════════════════════

def knee_index(dz2, fraction: float = 0.5) -> int:
    """Position of the largest |d2z| in the leading `fraction` of the series.

    Diagnostic only — no phase rule reads it. It marks where curvature is
    strongest before the slope peaks, i.e. where a flat start turns into the
    rise the plateau rule is trying to time. Comparing it against the tau
    crossing shows whether tau is firing on the actual knee or somewhere on the
    flat before/after it.

    The search window is the leading `fraction` of the series (default: the
    first half) so the far larger curvature around the mature/decay turn cannot
    win. An empty window degrades to index 0.
    """
    a = np.abs(np.asarray(dz2, dtype=float))
    if a.size == 0:
        return 0
    stop = max(1, int(a.size * float(fraction)))
    window = a[:stop]
    if not np.isfinite(window).any():
        return 0
    return int(np.nanargmax(window))


def incipient_lens(z_unfil,
                   dz,
                   dz2,
                   signal: str = "derivative",
                   tau: float = 0.20,
                   crossing: str = "single",
                   k: int = 3,
                   smooth_window: int = 0,
                   smooth_polyorder: int = 3,
                   knee_fraction: float = 0.5) -> dict:
    """Everything the incipient lens draws, computed via the package helpers.

    Args:
        z_unfil: the UNFILTERED input vorticity (``df['z_unfil']`` /
            ``vorticity.zeta``) — the curve the "vorticity" probe reads.
        dz, dz2: the pipeline's first and second smoothed derivatives.
        signal, tau, crossing, k, smooth_window, smooth_polyorder: the plateau
            parameters, passed to the package helpers verbatim.
        knee_fraction: leading fraction of the series searched for the knee.

    Returns:
        dict with ``rel_raw``/``rel_smoothed`` (the normalised slope profile
        with the probe smoothing off and on), the corresponding boundaries
        ``boundary_raw``/``boundary_smoothed``, the probe curve before and
        after smoothing (``probe_raw``/``probe_smoothed``), ``knee``, and
        ``smoothing_applies`` — False when the window is inert because the
        probe reads the already-filtered derivative (see
        ``_incipient_plateau_rel``), in which case the two rel profiles are
        identical by construction.
    """
    z_raw = np.asarray(z_unfil, dtype=float)
    probe = pd.DataFrame({"z_unfil": z_raw,
                          "dz": np.asarray(dz, dtype=float)})

    rel_raw = _incipient_plateau_rel(probe, signal, 0, smooth_polyorder)
    rel_smoothed = _incipient_plateau_rel(probe, signal, smooth_window,
                                          smooth_polyorder)
    return {
        "rel_raw": rel_raw,
        "rel_smoothed": rel_smoothed,
        "boundary_raw": _incipient_plateau_boundary(rel_raw, tau, crossing, k),
        "boundary_smoothed": _incipient_plateau_boundary(rel_smoothed, tau,
                                                         crossing, k),
        "probe_raw": z_raw,
        "probe_smoothed": _smooth_incipient_probe(z_raw, smooth_window,
                                                  smooth_polyorder),
        "knee": knee_index(dz2, knee_fraction),
        "smoothing_applies": bool(int(smooth_window) > 0
                                  and signal == "vorticity"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Drawing (matplotlib only — no streamlit), shared by the app and the figures
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_phase(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


def _shade_phases(ax, periods_dict, index) -> None:
    """Phase shading in POSITIONAL coordinates (the lenses plot against step)."""
    if not periods_dict:
        return
    pos = {ts: i for i, ts in enumerate(index)}
    items = list(periods_dict.items())
    for i, (phase, (start, end)) in enumerate(items):
        right = items[i + 1][1][0] if i + 1 < len(items) else end
        ax.axvspan(pos.get(start, 0), pos.get(right, len(index) - 1),
                   alpha=0.22, lw=0,
                   color=PHASE_COLORS.get(_normalize_phase(phase), "#cccccc"))


def draw_mature_lens(axes, z: pd.Series, lens: dict, periods_dict=None,
                     title: str = "") -> None:
    """Two stacked panels: z with classified extrema, and the prominence cut.

    axes: sequence of two matplotlib Axes (top = z, bottom = prominence stems).
    """
    ax_z, ax_p = axes[0], axes[1]
    y = np.asarray(z, dtype=float)
    t = np.arange(y.size)

    if periods_dict:
        _shade_phases(ax_z, periods_dict, z.index)
    ax_z.plot(t, y, color=C_Z, lw=1.6, zorder=3)

    def _scatter(idx, marker, colour, filled, label):
        if len(idx) == 0:
            return
        ax_z.scatter(idx, y[idx], marker=marker, s=70, zorder=6, clip_on=False,
                     facecolors=colour if filled else "none",
                     edgecolors=colour, linewidths=1.6, label=label)

    _scatter(lens["accepted_peaks"], "^", C_ACCEPT_PEAK, True,
             f"peak aceito ({len(lens['accepted_peaks'])})")
    _scatter(lens["accepted_valleys"], "v", C_ACCEPT_VALLEY, True,
             f"valley aceito ({len(lens['accepted_valleys'])})")
    _scatter(lens["rejected_peaks"], "^", C_REJECT, False,
             f"peak rejeitado ({len(lens['rejected_peaks'])})")
    _scatter(lens["rejected_valleys"], "v", C_REJECT, False,
             f"valley rejeitado ({len(lens['rejected_valleys'])})")

    ax_z.set_ylabel("z (vorticity_smoothed2)", fontsize=8)
    ax_z.legend(fontsize=7, loc="best", ncol=2, framealpha=0.85)
    if title:
        ax_z.set_title(title, fontsize=10, fontweight="bold")

    # Prominence panel: peaks plotted upward, valleys downward, each against
    # its OWN threshold — peaks and valleys are scored as separate populations
    # by _refine_extrema, so a single shared line would be wrong.
    accepted = set(lens["accepted_peaks"].tolist()) | set(
        lens["accepted_valleys"].tolist())
    for kind, sign in (("peak", 1.0), ("valley", -1.0)):
        proms = lens[f"{kind}_prominences"]
        for idx, prom in proms.items():
            ok = idx in accepted
            ax_p.vlines(idx, 0, sign * prom, lw=2.0,
                        color=(C_ACCEPT_PEAK if kind == "peak" else C_ACCEPT_VALLEY)
                        if ok else C_REJECT,
                        zorder=4 if ok else 3)
            ax_p.scatter([idx], [sign * prom], s=26, zorder=5,
                         color=(C_ACCEPT_PEAK if kind == "peak" else C_ACCEPT_VALLEY)
                         if ok else C_REJECT)
        thr = lens[f"{kind}_threshold"]
        if thr is not None:
            ax_p.axhline(sign * thr, color=C_THRESHOLD, lw=1.4, ls="--",
                         zorder=6,
                         label=f"limiar {kind} = {thr:.3e}")
    ax_p.axhline(0.0, color="#444444", lw=0.8)
    ax_p.set_ylabel("proeminencia\n(peak ^ / valley v)", fontsize=8)
    ax_p.set_xlabel("passo", fontsize=8)
    handles, _ = ax_p.get_legend_handles_labels()
    if handles:
        ax_p.legend(fontsize=7, loc="best", framealpha=0.85)
    else:
        ax_p.text(0.01, 0.9, "sem filtro de proeminencia ativo — todos os "
                  "candidatos interiores sao aceitos",
                  transform=ax_p.transAxes, fontsize=7, color="#555555")

    for ax in (ax_z, ax_p):
        ax.tick_params(labelsize=7)
        ax.set_xlim(-0.5, y.size - 0.5)


def draw_incipient_lens(axes, lens: dict, dz, dz2, tau: float,
                        boundary: int | None = None,
                        plateau_active: bool = True,
                        head_fraction: float = 0.5,
                        title: str = "") -> None:
    """Two or three stacked panels focused on the start of the series.

    axes: two or three Axes (dz + probe overlay, d2z + knee, and — only when
    the plateau rule is what is being tuned — rel + tau). `plateau_active`
    False (incipient_method != "plateau") degrades to the raw dz / d2z panels:
    pass two axes to drop the rel panel entirely, or three to keep the slot and
    have it carry the explanatory text. The caller adds the caption either way.
    """
    dz = np.asarray(dz, dtype=float)
    dz2 = np.asarray(dz2, dtype=float)
    n = dz.size
    t = np.arange(n)
    ax_dz, ax_dz2 = axes[0], axes[1]
    ax_rel = axes[2] if len(axes) > 2 else None
    panels = [ax for ax in (ax_dz, ax_dz2, ax_rel) if ax is not None]

    # ── the incipient boundary the run actually produced ─────────────────────
    # Drawn first so it is present in each panel's legend (matplotlib builds a
    # legend from the artists that exist at the moment legend() is called).
    if boundary:
        for ax in panels:
            ax.axvline(boundary, color="#000000", lw=1.8, alpha=0.8, zorder=7,
                       label=f"fronteira incipiente = {boundary}")

    # ── panel 1: raw dz, with the smoothed probe curve overlaid ──────────────
    ax_dz.plot(t, dz, color=C_DZ, lw=1.5, label="dz cru (pipeline)")
    if plateau_active and lens.get("smoothing_applies"):
        # The probe is a different quantity in different units (d/dt of the
        # smoothed RAW vorticity, not the pipeline's filtered derivative), so
        # it gets its own axis rather than being silently rescaled onto dz's.
        ax_probe = ax_dz.twinx()
        ax_probe.plot(t, np.gradient(lens["probe_smoothed"]), color=C_SMOOTH,
                      lw=1.9, label="sondagem suavizada d/dt")
        ax_probe.plot(t, np.gradient(lens["probe_raw"]), color=C_SMOOTH,
                      lw=0.9, alpha=0.45, label="sondagem crua d/dt")
        ax_probe.set_ylabel("d(zeta)/dt (sondagem)", fontsize=7,
                            color=C_SMOOTH)
        ax_probe.tick_params(labelsize=6, colors=C_SMOOTH)
        ax_probe.legend(fontsize=6, loc="lower right", framealpha=0.85)
    ax_dz.set_ylabel("dz", fontsize=8)
    ax_dz.legend(fontsize=7, loc="upper left", framealpha=0.85)
    if title:
        ax_dz.set_title(title, fontsize=10, fontweight="bold")

    # ── panel 2: d2z with the knee ───────────────────────────────────────────
    ax_dz2.plot(t, dz2, color=C_DZ2, lw=1.5, label="dz2")
    knee = lens.get("knee", 0)
    # zorder above the boundary line: the two frequently land on the same step
    # (that coincidence is itself the finding), and the knee must stay visible.
    ax_dz2.axvline(knee, color=C_KNEE, lw=1.6, ls="-.", zorder=8,
                   label=f"joelho |dz2| = {knee}")
    ax_dz2.set_ylabel("dz2", fontsize=8)
    ax_dz2.legend(fontsize=7, loc="upper right", framealpha=0.85)

    # ── panel 3: rel(t) against tau ──────────────────────────────────────────
    if plateau_active and ax_rel is not None:
        ax_rel.plot(t, lens["rel_raw"], color=C_REJECT, lw=1.2,
                    label="rel sem suavizacao")
        if lens.get("smoothing_applies"):
            ax_rel.plot(t, lens["rel_smoothed"], color=C_REL, lw=1.9,
                        label="rel com suavizacao")
        ax_rel.axhline(tau, color=C_THRESHOLD, lw=1.4, ls="--",
                       label=f"tau = {tau:.2f}")
        # A boundary of 0 is not "at t0" — it is the package's way of saying no
        # crossing was found (rel(t0) already >= tau, or no sustained run), i.e.
        # no incipient phase from this rule. Say so, rather than leaving the
        # line silently absent.
        no_crossing = []
        for key, colour, style, lbl in (
                ("boundary_raw", C_REJECT, ":", "cruzamento sem suavizacao"),
                ("boundary_smoothed", C_BOUNDARY, "-", "cruzamento com suavizacao")):
            if key == "boundary_smoothed" and not lens.get("smoothing_applies"):
                continue
            b = lens.get(key, 0)
            if b > 0:
                ax_rel.axvline(b, color=colour, lw=1.6, ls=style,
                               label=f"{lbl} = {b}")
            else:
                no_crossing.append(lbl)
        if no_crossing:
            ax_rel.text(
                0.01, 0.06,
                "sem cruzamento (rel(t0) >= tau ou nenhuma corrida sustentada): "
                + ", ".join(no_crossing),
                transform=ax_rel.transAxes, fontsize=6.5, color="#555555")
        ax_rel.set_ylim(0, 1.02)
        ax_rel.set_ylabel("rel = |dz|/max|dz|", fontsize=8)
        ax_rel.legend(fontsize=6, loc="upper right", ncol=2, framealpha=0.85)
    elif ax_rel is not None:
        ax_rel.text(0.5, 0.5,
                    "tau / sondagem so aparecem em incipient_method='plateau'",
                    ha="center", va="center", transform=ax_rel.transAxes,
                    fontsize=9, color="#555555")
        ax_rel.set_yticks([])
    panels[-1].set_xlabel("passo", fontsize=8)

    # ── zoom on the start, wide enough to contain knee and boundary ──────────
    stop = max(int(n * float(head_fraction)), knee + 3,
               int(boundary or 0) + 3,
               int(lens.get("boundary_raw", 0)) + 3,
               int(lens.get("boundary_smoothed", 0)) + 3, 10)
    stop = min(stop, n)
    for ax in panels:
        ax.set_xlim(-0.5, stop - 0.5)
        ax.tick_params(labelsize=7)
