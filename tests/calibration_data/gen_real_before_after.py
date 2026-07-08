"""Comparação: pipeline v2.0.0 SEM vs COM filtragem de extremos.

AMBAS as colunas usam o mesmo pipeline de pré-processamento v2.0.0 sem
modificações (use_filter='auto', use_smoothing='auto', use_smoothing_twice='auto').
A ÚNICA variável entre os dois lados é o parâmetro de filtragem ativo —
isto isola o efeito real do mecanismo de filtragem de extremos.

Modos suportados (escolhidos via FILTER_MODE abaixo):
  "absolute"  — filtra por prominence absoluta + distance
  "relative"  — filtra por prominence relativa (fração do extremo dominante)

Coluna ESQUERDA — v2.0.0 sem filtragem de extremos:
  Pipeline padrão CycloPhaser v2.0.0.  Sem prominence / distance.

Coluna DIREITA — v2.0.0 com filtragem de extremos:
  Mesmo pipeline.  Extremos de z filtrados pelo modo escolhido.

Rodar do raiz do repo:
    python tests/calibration_data/gen_real_before_after.py
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

DATA_DIR = Path(__file__).parent
FIGURES_ROOT = DATA_DIR / "figures"

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

# Marcadores: azul = sem filtro (v2.0.0), vermelho = com prominence/distance
_BLUE = "#2171b5"
_RED  = "#cb181d"

MK_PEAK   = dict(marker="^", s=60, zorder=5, clip_on=False)
MK_VALLEY = dict(marker="v", s=60, zorder=5, clip_on=False)


def _normalize(name):
    return name.rstrip(" 0123456789").strip()


def _get_pos(result, times, label):
    return [i for i, t in enumerate(times) if result[t] == label]


def _phase_seq(phases_dict):
    return " → ".join(dict.fromkeys(_normalize(k) for k in phases_dict).keys())


def _draw_phases(ax, phases_dict, ts_to_idx, n):
    phases_list = list(phases_dict.items())
    for i, (ph, (st, en)) in enumerate(phases_list):
        right_ts = phases_list[i + 1][1][0] if i + 1 < len(phases_list) else en
        left_i  = ts_to_idx.get(st,       0)
        right_i = ts_to_idx.get(right_ts, n - 1)
        color = PHASE_COLORS.get(_normalize(ph), "#cccccc")
        ax.axvspan(left_i, right_i, alpha=0.28, color=color, lw=0)


def _build_legend_handles():
    phase_patches = [
        mpatches.Patch(color=PHASE_COLORS[ph], alpha=0.6, label=ph.capitalize())
        for ph in ALL_PHASES
    ]
    series_handles = [
        mlines.Line2D([], [], color="#888888", lw=1.4, alpha=0.8,
                      label="série original (eixo dir.)"),
    ]
    extrema_handles = [
        mlines.Line2D([], [], marker="^", color=_BLUE, linestyle="None",
                      markersize=8, label="pico — sem filtro"),
        mlines.Line2D([], [], marker="v", color=_BLUE, linestyle="None",
                      markersize=8, label="vale — sem filtro"),
        mlines.Line2D([], [], marker="^", color=_RED, linestyle="None",
                      markersize=8, label="pico — com prominence/dist"),
        mlines.Line2D([], [], marker="v", color=_RED, linestyle="None",
                      markersize=8, label="vale — com prominence/dist"),
    ]
    return phase_patches + series_handles + extrema_handles


def make_figure(csv_path, prominence=None, prominence_relative=None,
                distance=None, out_dir=None):
    track_id = csv_path.stem
    df_input = pd.read_csv(csv_path, sep=";", index_col="time", parse_dates=True)
    series   = df_input["min_max_zeta_850"].rename("zeta")

    n        = len(series)
    dt_hours = (series.index[1] - series.index[0]).total_seconds() / 3600
    dur_days = (series.index[-1] - series.index[0]).total_seconds() / 86400
    date_str = (f"{series.index[0].strftime('%Y-%m-%d')} → "
                f"{series.index[-1].strftime('%Y-%m-%d')}")

    # Build a short tag describing the active filter for subtitles
    filter_parts = []
    if prominence is not None:
        filter_parts.append(f"abs={prominence:.1e}")
    if prominence_relative is not None:
        filter_parts.append(f"rel={prominence_relative:.2f}")
    if distance is not None:
        dist_hours = distance * dt_hours
        filter_parts.append(f"dist={distance}steps/{dist_hours:.0f}h")
    filter_tag = "  ·  ".join(filter_parts) if filter_parts else "(nenhum)"

    zeta_df = pd.DataFrame({"zeta": series})

    # ── Processar uma única vez com defaults v2.0.0 ───────────────────────────
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(zeta_df)   # use_filter='auto', use_smoothing='auto'

    # Séries — idênticas nos dois lados
    z   = pd.Series(vort["vorticity_smoothed2"].values, index=series.index)
    dz  = pd.Series(vort["dz_dt_smoothed2"].values,     index=series.index)
    dz2 = pd.Series(vort["dz_dt2_smoothed2"].values,    index=series.index)
    z_raw = pd.Series(vort["zeta"].values,               index=series.index)

    times     = list(series.index)
    t_vals    = np.arange(n)
    ts_to_idx = {t: i for i, t in enumerate(times)}

    # ── Fases: v2.0.0 sem e com filtragem ────────────────────────────────────
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df_base = get_periods(vort)
        df_filt = get_periods(vort, prominence=prominence,
                              prominence_relative=prominence_relative,
                              distance=distance)

    phases_base = periods_to_dict(df_base)
    phases_filt = periods_to_dict(df_filt)

    seq_base = _phase_seq(phases_base)
    seq_filt = _phase_seq(phases_filt)
    changed  = "⚠ DIFERENTE" if seq_base != seq_filt else "✓ igual"

    # ── Extremos de z: diferem entre os dois lados ────────────────────────────
    # dz e dz2: não filtrados por prominence (idênticos nos dois lados)
    z_extr_base = find_peaks_valleys(z)
    z_extr_filt = find_peaks_valleys(z, prominence=prominence,
                                     prominence_relative=prominence_relative,
                                     distance=distance)
    dz_extr     = find_peaks_valleys(dz)
    dz2_extr    = find_peaks_valleys(dz2)

    panel_cfg = [
        ("z",   z,   C_Z,   "z  (vorticity suavizada)",   z_extr_base,  z_extr_filt),
        ("dz",  dz,  C_DZ,  "dz/dt  (1ª derivada)",       dz_extr,      dz_extr),
        ("dz2", dz2, C_DZ2, "d²z/dt²  (2ª derivada)",     dz2_extr,     dz2_extr),
    ]

    col_titles = [
        f"v2.0.0 SEM filtragem de extremos\n{seq_base}",
        f"v2.0.0 COM filtragem  ({filter_tag})\n{seq_filt}",
    ]

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(17, 13))
    fig.suptitle(
        f"Ciclone {track_id}  ·  {n} pts  ·  {date_str}  ·  {dur_days:.1f} dias\n"
        f"Única variável: {filter_tag}  ·  {changed}",
        fontsize=11, fontweight="bold", y=0.99,
    )
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.10,
                           top=0.91, bottom=0.14)

    for ri, (key, ser, color, ser_label, extr_left, extr_right) in enumerate(panel_cfg):
        for ci, (extr, phases, mk_color) in enumerate([
            (extr_left,  phases_base, _BLUE),
            (extr_right, phases_filt, _RED),
        ]):
            ax = fig.add_subplot(gs[ri, ci])

            _draw_phases(ax, phases, ts_to_idx, n)

            # Eixo direito: série original bruta (escala própria)
            ax2 = ax.twinx()
            ax2.plot(t_vals, z_raw.values, color="#888888", lw=1.4,
                     alpha=0.65, zorder=1)
            ax2.tick_params(axis="y", labelsize=6, colors="#888888", length=3)
            ax2.set_ylabel("original", fontsize=6, color="#888888")
            ax2.set_xlim(-0.5, n - 0.5)

            # Eixo esquerdo: série suavizada + marcadores
            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)
            ax.axhline(0, color="gray", lw=0.5, ls="--")
            ax.plot(t_vals, ser.values, color=color, lw=1.8, zorder=3)

            peaks   = _get_pos(extr, times, "peak")
            valleys = _get_pos(extr, times, "valley")
            if peaks:
                ax.scatter(peaks,   [ser.values[i] for i in peaks],
                           color=mk_color, **MK_PEAK)
            if valleys:
                ax.scatter(valleys, [ser.values[i] for i in valleys],
                           color=mk_color, **MK_VALLEY)

            if ri == 0:
                ax.set_title(col_titles[ci], fontsize=8.5, pad=6)
            ax.set_ylabel(
                f"{ser_label}\n({len(peaks)}p / {len(valleys)}v)", fontsize=7.5)
            ax.tick_params(labelsize=7)
            ax.set_xlim(-0.5, n - 0.5)

            step = max(1, n // 8)
            tick_pos = list(range(0, n, step))
            ax.set_xticks(tick_pos)
            ax.set_xticklabels(
                [times[i].strftime("%m/%d\n%Hh") for i in tick_pos], fontsize=6)
            if ri == 2:
                ax.set_xlabel("Data/hora", fontsize=8)

    # ── Legenda única na base ─────────────────────────────────────────────────
    handles = _build_legend_handles()
    fig.legend(handles=handles, loc="lower center",
               ncol=min(len(handles), 5),
               fontsize=8, bbox_to_anchor=(0.5, 0.01),
               frameon=True, framealpha=0.92,
               handlelength=1.6, handletextpad=0.5, columnspacing=1.2)

    save_dir = out_dir if out_dir is not None else OUT
    out_path = save_dir / f"{track_id}_base_vs_filtered.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path, seq_base, seq_filt


# ── Modo de filtragem ─────────────────────────────────────────────────────────
# Altere FILTER_MODE para escolher o que comparar:
#   "relative"  → prominence_relative=0.10 (fração do extremo dominante)
#   "absolute"  → prominence=5e-6, distance=10
FILTER_MODE = "relative"

# Parâmetros por modo
_CONFIGS = {
    "relative": dict(
        prominence=None,
        prominence_relative=0.10,
        distance=None,
    ),
    "absolute": dict(
        prominence=5e-6,
        prominence_relative=None,
        distance=10,
    ),
}

_cfg = _CONFIGS[FILTER_MODE]
PROMINENCE          = _cfg["prominence"]
PROMINENCE_RELATIVE = _cfg["prominence_relative"]
DISTANCE            = _cfg["distance"]


def _out_tag():
    parts = []
    if PROMINENCE is not None:
        def _pt(p): return f"prom{p:.0e}".replace("e-0", "e-").replace("e+0", "e")
        parts.append(_pt(PROMINENCE))
    if PROMINENCE_RELATIVE is not None:
        parts.append(f"prom_rel{PROMINENCE_RELATIVE:.2f}")
    if DISTANCE is not None:
        parts.append(f"dist{DISTANCE}steps")
    return "_".join(parts) if parts else "baseline"


# Subdiretório nomeado automaticamente pelos parâmetros usados.
# Cada rodada de validação fica em seu próprio diretório, tornando
# comparações incrementais rastreáveis sem sobrescrever resultados anteriores.
OUT = FIGURES_ROOT / _out_tag()
OUT.mkdir(parents=True, exist_ok=True)

print(f"Pipeline: v2.0.0 defaults (Lanczos auto + Savgol auto)")
print(f"Modo: {FILTER_MODE}  |  {_cfg}")
print(f"Saída em: {OUT}/\n")

csvs = sorted(DATA_DIR.glob("*.csv"))
results = []
for csv in csvs:
    out, sb, sf = make_figure(csv,
                               prominence=PROMINENCE,
                               prominence_relative=PROMINENCE_RELATIVE,
                               distance=DISTANCE,
                               out_dir=OUT)
    flag = "⚠" if sb != sf else " "
    results.append((csv.stem, sb, sf, flag))
    print(f"  {flag} {csv.stem:12s}  base: {sb:45s}  filtrado: {sf}")

n_diff = sum(1 for _, _, _, f in results if f.strip())
print(f"\nTotal: {len(csvs)} figuras  ·  {n_diff} diferentes  ·  {len(csvs)-n_diff} idênticos")
