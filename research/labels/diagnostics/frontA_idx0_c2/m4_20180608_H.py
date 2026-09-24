#!/usr/bin/env python
"""M4 — does the incipient overwrite (H) mask the index-0 artefact on 20180608?

H is `find_stages.py:1134`, inside the `incipient_method="plateau"` branch:

    if boundary > 0:
        df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'

It overwrites [0, boundary) with `incipient` AFTER every other phase has been
assigned. A spurious `decay` block opening at index 0 therefore survives into the
final output only if it extends past `boundary`.

This script snapshots the phase map on 20180608 immediately BEFORE line 1134 and
immediately after, with and without index 0 forced to 'peak', and reports what
each state's leading block is. The H step is re-executed here from the package's
own `_incipient_plateau_rel` / `_incipient_plateau_boundary`, and the result is
asserted equal to the replay's final column, so the "before" snapshot is a
snapshot of the real pipeline and not of a lookalike.

Also emits a figure with the four states.

Run:
    python research/labels/diagnostics/frontA_idx0_c2/m4_20180608_H.py \
        --config research/labels/configs/cyclophaser_params-13.yaml \
        --outdir research/labels/diagnostics/frontA_idx0_c2/outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import provenance, replay, seq_str, sha256_of  # noqa: E402

from labels_core import PHASE_COLORS, load_real_series, normalize_phase  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel,
)

TRACK = "20180608"


def leading_block(periods: pd.Series) -> tuple[str, int]:
    """(phase name, length) of the first block."""
    vals = [str(v) for v in periods]
    first = vals[0]
    n = 0
    for v in vals:
        if v != first:
            break
        n += 1
    return first, n


def h_step(out, gp):
    """Reproduce H from the package's own helpers. Returns (pre_H, boundary, post_H)."""
    df = out["df"]
    pre_H = out["after_post"].copy()
    # find_stages.py:1102 — the catch-all fill that runs before H.
    pre_H = pre_H.fillna('incipient')
    rel = _incipient_plateau_rel(df,
                                 gp.get('incipient_plateau_signal', 'derivative'),
                                 gp.get('incipient_smooth_window', 0),
                                 gp.get('incipient_smooth_polyorder', 3))
    boundary = _incipient_plateau_boundary(rel,
                                           gp.get('incipient_plateau_tau', 0.20),
                                           gp.get('incipient_plateau_crossing', 'single'),
                                           gp.get('incipient_plateau_k', 3))
    post_H = pre_H.copy()
    if boundary > 0:
        post_H.iloc[:boundary] = 'incipient'
    ok = [str(a) for a in post_H] == [str(b) for b in out["final"]]
    return pre_H, int(boundary), post_H, ok


def describe(tag, pre_H, boundary, post_H):
    lb_pre, n_pre = leading_block(pre_H)
    lb_post, n_post = leading_block(post_H)
    print(f"  [{tag}]")
    print(f"    boundary (H overwrites [0, {boundary}))      : {boundary}")
    print(f"    sequencia ANTES de H                        : {seq_str(pre_H)}")
    print(f"    primeiro bloco ANTES de H                   : {lb_pre} x{n_pre}")
    print(f"    sequencia DEPOIS de H (= saida final)       : {seq_str(post_H)}")
    print(f"    primeiro bloco DEPOIS de H                  : {lb_post} x{n_post}")
    masked = (normalize_phase(lb_pre) not in ("incipient",)) and n_pre <= boundary
    print(f"    H mascara o primeiro bloco?                 : {masked}"
          f"   (bloco {n_pre} passos <= boundary {boundary})")
    return {"tag": tag, "boundary": boundary,
            "seq_pre_H": seq_str(pre_H), "primeiro_bloco_pre_H": f"{lb_pre} x{n_pre}",
            "seq_pos_H": seq_str(post_H), "primeiro_bloco_pos_H": f"{lb_post} x{n_post}",
            "H_mascara": masked}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--track", default=TRACK)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    pv, gp = load_config(a.config)
    print(f"config: {a.config}\n  sha256: {sha256_of(a.config)}\n")

    values = load_real_series()[a.track]
    print(f"track {a.track}, n={len(values)}\n")

    rows, states = [], {}
    for tag, force in (("sem forcar", "none"), ("idx0 forcado a peak", "all")):
        out = replay(values, pv, gp, force=force, verify=(force == "none"))
        if force == "none" and out["replay_ok"] is not True:
            raise SystemExit("replay diverged from get_periods")
        pre_H, boundary, post_H, ok = h_step(out, gp)
        if not ok:
            raise SystemExit(f"H re-execution != replay final ({tag})")
        print(f"H re-executada confere com o final do replay: {ok}")
        rows.append(describe(tag, pre_H, boundary, post_H))
        states[tag] = (pre_H, post_H, boundary, out["df"])
        print()

    tab = pd.DataFrame(rows)
    out_csv = a.outdir / f"m4_{a.track}_H.csv"
    tab.to_csv(out_csv, index=False)
    print(f"wrote {out_csv}")

    # ── the first `boundary` steps, step by step ────────────────────────────
    pre0, post0, b0, df0 = states["sem forcar"]
    pre1, post1, b1, df1 = states["idx0 forcado a peak"]
    m = max(b0, b1) + 6
    head = pd.DataFrame({
        "idx": range(m),
        "z": np.asarray(df0["z"], dtype=float)[:m],
        "z_pv_base": list(df0["z_peaks_valleys"])[:m],
        "z_pv_forcado": list(df1["z_peaks_valleys"])[:m],
        "pre_H_base": [str(v) for v in pre0[:m]],
        "pos_H_base": [str(v) for v in post0[:m]],
        "pre_H_forcado": [str(v) for v in pre1[:m]],
        "pos_H_forcado": [str(v) for v in post1[:m]],
    })
    head_csv = a.outdir / f"m4_{a.track}_head.csv"
    head.to_csv(head_csv, index=False)
    print(f"wrote {head_csv}\n")
    print(head.to_string(index=False))

    # ── figure ──────────────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"(no figure: {exc})")
        return 0

    fig, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    panels = [("ANTES de H — base", pre0, df0, b0),
              ("DEPOIS de H — base (saida final)", post0, df0, b0),
              ("ANTES de H — idx0 forcado a peak", pre1, df1, b1),
              ("DEPOIS de H — idx0 forcado a peak", post1, df1, b1)]
    z = np.asarray(df0["z"], dtype=float)
    for ax, (title, per, dfx, bnd) in zip(axes, panels):
        ax.plot(range(len(z)), z, color="k", lw=1.0, zorder=3)
        labs = [normalize_phase(str(v)) for v in per]
        start = 0
        for i in range(1, len(labs) + 1):
            if i == len(labs) or labs[i] != labs[start]:
                ax.axvspan(start - 0.5, i - 0.5,
                           color=PHASE_COLORS.get(labs[start], "white"), alpha=0.45, lw=0)
                start = i
        ax.axvline(bnd - 0.5, color="magenta", ls="--", lw=1.2,
                   label=f"boundary = {bnd}")
        ax.set_title(f"{a.track} — {title}", fontsize=9, loc="left")
        ax.legend(loc="upper right", fontsize=7)
        ax.set_ylabel("z")
    axes[-1].set_xlabel("indice")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.45)
               for c in PHASE_COLORS.values()]
    fig.legend(handles, list(PHASE_COLORS), loc="lower center", ncol=5, fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    png = a.outdir / f"m4_{a.track}_H.png"
    fig.savefig(png, dpi=140)
    print(f"\nwrote {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
