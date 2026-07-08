"""Gera figuras antes x depois da filtragem de extremos (prominence + distance).

Para cada caso sintético: mostra z, dz, dz2 com picos/vales marcados
antes (padrão) e depois (com prominence + distance). Em todos os painéis
o fundo mostra as fases *detectadas* pelo CycloPhaser para aquele cenário,
permitindo avaliar o impacto da filtragem na detecção de fases.

Rodar do raiz do repo:
    python tests/synthetic/gen_extrema_before_after.py
"""

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cyclophaser.determine_periods import (
    find_peaks_valleys, get_periods, periods_to_dict, process_vorticity,
)
from tests.synthetic.cases import CASES

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)

# ── Cores padrão CycloPhaser ──────────────────────────────────────────────────
PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "#999999",
}
ALL_PHASES = ["incipient", "intensification", "mature", "decay", "residual"]
C_Z, C_DZ, C_DZ2 = "#1d3557", "#457b9d", "#e63946"

# ── Marcadores de extremos ────────────────────────────────────────────────────
# Convenção: antes = azul, depois = vermelho; ▲ pico, ▼ vale (sempre)
_BLUE = "#2171b5"
_RED  = "#cb181d"
_GRAY = "#555555"

MK_PEAK_BEF   = dict(marker="^", color=_BLUE, s=60, zorder=5, clip_on=False)
MK_VALLEY_BEF = dict(marker="v", color=_BLUE, s=60, zorder=5, clip_on=False)
MK_PEAK_AFT   = dict(marker="^", color=_RED,  s=60, zorder=6, clip_on=False)
MK_VALLEY_AFT = dict(marker="v", color=_RED,  s=60, zorder=6, clip_on=False)
MK_REMOVED    = dict(marker="x", color=_GRAY, s=80, zorder=7,
                     linewidths=1.8, clip_on=False)


def _normalize(name):
    return name.rstrip(" 0123456789").strip()


def _get_pos(result, times, label):
    return [i for i, t in enumerate(times) if result[t] == label]


def _draw_phases(ax, phases_dict, ts_to_idx, n):
    """Desenha axvspan colorido para cada fase detectada."""
    phases_list = list(phases_dict.items())
    for i, (ph, (st, en)) in enumerate(phases_list):
        right_ts = phases_list[i + 1][1][0] if i + 1 < len(phases_list) else en
        left_i  = ts_to_idx.get(st,       0)
        right_i = ts_to_idx.get(right_ts, n - 1)
        color = PHASE_COLORS.get(_normalize(ph), "#cccccc")
        ax.axvspan(left_i, right_i, alpha=0.28, color=color, lw=0)


def _draw_extrema(ax, ser, result_bef, result_aft, times, is_before):
    """Marca picos/vales; no painel 'depois' adiciona X nos removidos."""
    if is_before:
        peaks   = _get_pos(result_bef, times, "peak")
        valleys = _get_pos(result_bef, times, "valley")
        if peaks:
            ax.scatter(peaks,   [ser.values[i] for i in peaks],   **MK_PEAK_BEF)
        if valleys:
            ax.scatter(valleys, [ser.values[i] for i in valleys], **MK_VALLEY_BEF)
    else:
        peaks   = _get_pos(result_aft, times, "peak")
        valleys = _get_pos(result_aft, times, "valley")
        if peaks:
            ax.scatter(peaks,   [ser.values[i] for i in peaks],   **MK_PEAK_AFT)
        if valleys:
            ax.scatter(valleys, [ser.values[i] for i in valleys], **MK_VALLEY_AFT)
        bef_p = set(_get_pos(result_bef, times, "peak"))
        bef_v = set(_get_pos(result_bef, times, "valley"))
        removed = sorted((bef_p - set(peaks)) | (bef_v - set(valleys)))
        if removed:
            ax.scatter(removed, [ser.values[i] for i in removed], **MK_REMOVED)
    return len(peaks if not is_before else _get_pos(result_bef, times, "peak")), \
           len(valleys if not is_before else _get_pos(result_bef, times, "valley"))


def _build_legend_handles(has_gt=False):
    """Monta handles para a legenda única na base da figura."""
    # Fases
    phase_patches = [
        mpatches.Patch(color=PHASE_COLORS[ph], alpha=0.6, label=ph.capitalize())
        for ph in ALL_PHASES
    ]
    # Extremos
    extrema_handles = [
        mlines.Line2D([], [], color="#aaaaaa", lw=1.2, alpha=0.9,
                      label="série original"),
        mlines.Line2D([], [], marker="^", color=_BLUE, linestyle="None",
                      markersize=8, label="pico — antes"),
        mlines.Line2D([], [], marker="v", color=_BLUE, linestyle="None",
                      markersize=8, label="vale — antes"),
        mlines.Line2D([], [], marker="^", color=_RED,  linestyle="None",
                      markersize=8, label="pico — depois"),
        mlines.Line2D([], [], marker="v", color=_RED,  linestyle="None",
                      markersize=8, label="vale — depois"),
        mlines.Line2D([], [], marker="x", color=_GRAY, linestyle="None",
                      markersize=7, markeredgewidth=1.8, label="extremo removido"),
    ]
    handles = phase_patches + extrema_handles
    if has_gt:
        handles.append(
            mlines.Line2D([], [], color="k", ls=":", lw=1.2, alpha=0.6,
                          label="fronteira GT")
        )
    return handles


def make_figure(case_name, case, prominence, distance):
    series = case["series"]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": series}))

    # Séries suavizadas (usadas para extremos e fases)
    z   = pd.Series(vort["vorticity_smoothed2"].values, index=series.index)
    dz  = pd.Series(vort["dz_dt_smoothed2"].values,     index=series.index)
    dz2 = pd.Series(vort["dz_dt2_smoothed2"].values,    index=series.index)
    # Séries originais / menos processadas (referência de fundo)
    z_raw   = pd.Series(vort["zeta"].values,         index=series.index)
    dz_raw  = pd.Series(vort["dz_dt_filt"].values,   index=series.index)
    dz2_raw = pd.Series(vort["dz_dt2_filt"].values,  index=series.index)

    times     = list(series.index)
    t_vals    = np.arange(len(times))
    ts_to_idx = {t: i for i, t in enumerate(times)}

    # Fases detectadas antes e depois
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_bef = get_periods(vort)
        df_aft = get_periods(vort, prominence=prominence, distance=distance)

    phases_bef = periods_to_dict(df_bef)
    phases_aft = periods_to_dict(df_aft)

    # Extremos antes e depois (por série)
    extr = {}
    for key, ser in [("z", z), ("dz", dz), ("dz2", dz2)]:
        extr[f"{key}_bef"] = find_peaks_valleys(ser)
        extr[f"{key}_aft"] = find_peaks_valleys(ser, prominence=prominence,
                                                 distance=distance)

    # ── Nomes das fases detectadas (para título de coluna) ────────────────────
    def _phase_seq(pd_): return " → ".join(
        dict.fromkeys(_normalize(k) for k in pd_).keys()
    )
    seq_bef = _phase_seq(phases_bef)
    seq_aft = _phase_seq(phases_aft)
    changed = "⚠ MUDOU" if seq_bef != seq_aft else "✓ igual"

    has_gt = "expected_starts_idx" in case
    panel_cfg = [
        ("z",   z,   z_raw,   C_Z,   "z  (vorticity)"),
        ("dz",  dz,  dz_raw,  C_DZ,  "dz/dt  (1ª derivada)"),
        ("dz2", dz2, dz2_raw, C_DZ2, "d²z/dt²  (2ª derivada)"),
    ]

    fig = plt.figure(figsize=(17, 13))
    dt_hours = (series.index[1] - series.index[0]).total_seconds() / 3600
    dist_hours = distance * dt_hours
    fig.suptitle(
        f"{case_name}  —  Antes vs. Depois da filtragem de extremos\n"
        f"prominence = {prominence:.1e}   distance = {distance} steps "
        f"({dist_hours:.0f}h a {dt_hours:.0f}h/step)   |   impacto nas fases: {changed}",
        fontsize=12, fontweight="bold", y=0.99,
    )
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.10,
                           top=0.91, bottom=0.14)

    col_titles = [
        f"ANTES (padrão)\n{seq_bef}",
        f"DEPOIS (prominence={prominence:.1e}, dist={distance} steps/{dist_hours:.0f}h)\n{seq_aft}",
    ]

    for ri, (key, ser, ser_raw, color, ser_label) in enumerate(panel_cfg):
        for ci, is_before in enumerate([True, False]):
            ax = fig.add_subplot(gs[ri, ci])

            # Fases detectadas como fundo
            ph_dict = phases_bef if is_before else phases_aft
            _draw_phases(ax, ph_dict, ts_to_idx, len(times))

            # Ground-truth boundaries (linhas pontilhadas, ambos os painéis)
            if has_gt:
                for ph, pstart in case["expected_starts_idx"].items():
                    ax.axvline(pstart,
                               color=PHASE_COLORS.get(_normalize(ph), "k"),
                               ls=":", lw=1.1, alpha=0.55)

            # Eixo direito: série original (cinza, escala própria)
            ax2 = ax.twinx()
            ax2.plot(t_vals, ser_raw.values, color="#888888", lw=1.4,
                     alpha=0.65, zorder=1)
            ax2.tick_params(axis="y", labelsize=6, colors="#888888", length=3)
            ax2.set_ylabel("original", fontsize=6, color="#888888")
            ax2.set_xlim(-0.5, len(t_vals) - 0.5)

            # Eixo esquerdo: série suavizada + marcadores (frente)
            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)
            ax.axhline(0, color="gray", lw=0.5, ls="--")
            ax.plot(t_vals, ser.values, color=color, lw=1.8, zorder=3)

            _draw_extrema(ax, ser, extr[f"{key}_bef"], extr[f"{key}_aft"],
                          times, is_before)

            np_ = len(_get_pos(extr[f"{key}_bef" if is_before else f"{key}_aft"],
                                times, "peak"))
            nv_ = len(_get_pos(extr[f"{key}_bef" if is_before else f"{key}_aft"],
                                times, "valley"))

            if ri == 0:
                ax.set_title(f"{col_titles[ci]}", fontsize=8.5, pad=6)
            ax.set_ylabel(f"{ser_label}\n({np_}p / {nv_}v)", fontsize=7.5)
            ax.tick_params(labelsize=7)
            ax.set_xlim(-0.5, len(t_vals) - 0.5)

            if ri == 2:
                ax.set_xlabel("Passo de tempo", fontsize=8)

    # ── Legenda única na base ─────────────────────────────────────────────────
    handles = _build_legend_handles(has_gt=has_gt)
    fig.legend(handles=handles, loc="lower center",
               ncol=min(len(handles), 6),
               fontsize=8, bbox_to_anchor=(0.5, 0.01),
               frameon=True, framealpha=0.92,
               handlelength=1.6, handletextpad=0.5, columnspacing=1.0)

    out_path = OUT / f"{case_name}_extrema_before_after.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────
# Valores ilustrativos — NÃO ajustados; mostram apenas o mecanismo.
PROMINENCE = 0.5e-4   # ~6% da amplitude baseline→peak (8e-4)
DISTANCE   = 5        # 5 passos = 15 h a 3 h/passo

print(f"prominence = {PROMINENCE:.1e}   distance = {DISTANCE}")
print(f"Saída em: {OUT}/\n")

for case_name, case in CASES.items():
    out = make_figure(case_name, case, PROMINENCE, DISTANCE)
    print(f"  {case_name:30s}  →  {out.name}")

print(f"\nTotal: {len(CASES)} figuras geradas.")
