#!/usr/bin/env python
"""Stage 2 gate — Q1 to Q8, from the three fingerprint files plus a live run.

Reads the JSON written by `stage2_reference.py` for

  * `develop-v2.1 @ c714451` (the code before this change),
  * the working tree with `reclassify_index0=False`,
  * the working tree with `reclassify_index0=True` (the new default),

and decides each declared prediction against them. Q7's "before H" map and Q8's
boundary are measured live, because a fingerprint of the final output cannot see
either: H overwrites the opening, and the boundary is never written to `periods`
at all.

Emits the 63-row table the brief asks for and the before/after figures.

Run:
    python stage2_gate.py --ref <json> --off <json> --on <json> \
        --config <params-14.yaml> --outdir <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import A_TARGET_IDS, provenance, sha256_of  # noqa: E402

from labels_core import (  # noqa: E402
    PHASE_COLORS, load_real_series, load_synthetic_series, normalize_phase,
    read_labels, read_split, series_sha256,
)
from evaluate_against_labels import load_config  # noqa: E402

from cyclophaser.determine_periods import get_periods, process_vorticity  # noqa: E402
from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel,
    find_decay_period, find_incipient_period, find_intensification_period,
    find_mature_stage, find_residual_period,
)
from cyclophaser.determine_periods import (  # noqa: E402
    find_peaks_valleys, post_process_periods,
)

# Declared before the run — Q2 of the brief.
Q2_EXPECTED_VALLEY_TO_PEAK = {"20180170", "20190325", "20191014", "20206498"}
Q2_EXPECTED_PEAK_TO_VALLEY = {"20190639"}
Q2_EXPECTED = Q2_EXPECTED_VALLEY_TO_PEAK | Q2_EXPECTED_PEAK_TO_VALLEY

Q3_Q7 = {
    "20180170": "incipient>intensification>mature>decay",
    "20190325": "incipient>intensification>decay>intensification>mature>decay",
    "20191014": "incipient>intensification>mature>decay>residual",
    "20190639": "incipient>decay>intensification>mature>decay",
}
Q6_BLOCKS = "incipient[0,13) decay[13,26) intensification[26,88) mature[88,105) decay[105,180)"


def blocks_str(periods) -> str:
    names = [normalize_phase(str(v)) for v in periods]
    out, start = [], 0
    for i in range(1, len(names) + 1):
        if i == len(names) or names[i] != names[start]:
            out.append(f"{names[start]}[{start},{i})")
            start = i
    return " ".join(out)


def seq_of(periods) -> str:
    out, prev = [], None
    for v in pd.Series(periods).astype(str):
        if v != prev:
            out.append(v)
            prev = v
    return ">".join(out)


def label_seq(rec) -> str:
    return ">".join(p["phase"] for p in rec["phases"])


def matches_label(periods, rec) -> bool:
    det, prev = [], None
    for v in pd.Series(periods).astype(str):
        n = normalize_phase(v)
        if n != prev:
            det.append(n)
            prev = n
    return det == [p["phase"] for p in rec["phases"]]


def run(values, pv, gp, flag):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        return get_periods(vort, **{**gp, "reclassify_index0": flag})


def pre_H(values, pv, gp, flag):
    """The phase map as it stands when find_incipient_period's overwrite runs.

    A replay, so it must be shown to be the real pipeline: the final column of
    this replay is compared with get_periods' own output by the caller.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
    df = vort.vorticity_smoothed2.to_dataframe().rename(
        columns={"vorticity_smoothed2": "z"})
    df["z_unfil"] = vort.zeta.to_dataframe()
    df["dz"] = vort.dz_dt_smoothed2.to_dataframe()
    df["dz2"] = vort.dz_dt2_smoothed2.to_dataframe()
    df["z_peaks_valleys"] = find_peaks_valleys(
        df["z"], prominence=gp.get("prominence"),
        prominence_relative=gp.get("prominence_relative"),
        reclassify_index0=flag)
    df["dz_peaks_valleys"] = find_peaks_valleys(df["dz"], reclassify_index0=False)
    df["dz2_peaks_valleys"] = find_peaks_valleys(df["dz2"], reclassify_index0=False)
    df["periods"] = np.nan
    df["periods"] = df["periods"].astype("object")
    args = {k: v for k, v in gp.items()
            if k not in ("prominence", "prominence_relative", "reclassify_index0")}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = find_intensification_period(df, **args)
        df = find_decay_period(df, **args)
        df = find_mature_stage(df, **args)
        df = find_residual_period(df, **args)
        df = post_process_periods(df)
        before = df["periods"].copy().fillna("incipient")
        df = find_incipient_period(df, **args)
    rel = _incipient_plateau_rel(df, gp.get("incipient_plateau_signal", "derivative"),
                                 gp.get("incipient_smooth_window", 0),
                                 gp.get("incipient_smooth_polyorder", 3))
    boundary = int(_incipient_plateau_boundary(
        rel, gp.get("incipient_plateau_tau", 0.20),
        gp.get("incipient_plateau_crossing", "single"),
        gp.get("incipient_plateau_k", 3)))
    return before, boundary, df["periods"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, type=Path)
    ap.add_argument("--off", required=True, type=Path)
    ap.add_argument("--on", required=True, type=Path)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    ref = json.loads(a.ref.read_text())
    off = json.loads(a.off.read_text())
    on = json.loads(a.on.read_text())
    print(f"reference : {ref['cyclophaser']}\n  determine_periods sha256 {ref['determine_periods_sha256']}")
    print(f"current   : {on['cyclophaser']}\n  determine_periods sha256 {on['determine_periods_sha256']}")
    print(f"config    : {a.config}  sha256 {sha256_of(a.config)}\n")

    pv, gp = load_config(a.config)
    real = load_real_series()
    synth, names = load_synthetic_series()
    allser = {**real, **synth}
    labels = read_labels()
    split = read_split()
    split_of = {s: "treino" for s in split.get("train", [])}
    split_of.update({s: "teste" for s in split.get("test", [])})

    ids = sorted(ref["records"])
    rows = []
    for sid in ids:
        r, o, n = ref["records"][sid], off["records"][sid], on["records"][sid]
        changed = o["periods_sha256"] != n["periods_sha256"]
        # Labels are read for TRAIN series only. The frozen TEST split is run
        # through the detector — Q1, Q2, Q7 and Q8 are mechanical and need every
        # series — but no test label is opened, printed, written to the table or
        # added into any count. A per-series "does it match" for a held-out
        # series is a score, and 16 of them are a score of the test set.
        is_train = split_of.get(sid) == "treino"
        rec = labels.get(sid)
        scoreable = is_train and rec is not None
        if scoreable and rec["series_sha256"] != series_sha256(allser[sid]):
            raise SystemExit(f"{sid}: stale label")
        rows.append({
            "id": sid,
            "fonte": r["fonte"],
            "caso": r["caso"],
            "split": split_of.get(sid, "?"),
            "alvo_A": sid in A_TARGET_IDS,
            "n_steps": r["n_steps"],
            "sha_igual_ref_vs_False": r["periods_sha256"] == o["periods_sha256"],
            "dispara": changed,
            "ramo": ("vale->pico" if sid in Q2_EXPECTED_VALLEY_TO_PEAK else
                     "pico->vale" if sid in Q2_EXPECTED_PEAK_TO_VALLEY else
                     "") if changed else "",
            "seq_False": o["sequencia"],
            "seq_True": n["sequencia"],
            "rotulo": (label_seq(rec) if scoreable
                       else ("<teste: nao lido>" if not is_train
                             else "<sem rotulo>")),
            "bate_False": "",
            "bate_True": "",
        })
        if scoreable:
            rows[-1]["bate_False"] = matches_label(
                run(allser[sid], pv, gp, False)["periods"], rec)
            rows[-1]["bate_True"] = matches_label(
                run(allser[sid], pv, gp, True)["periods"], rec)

    tab = pd.DataFrame(rows)
    out_csv = a.outdir / "stage2_table.csv"
    tab.to_csv(out_csv, index=False)
    print(f"wrote {out_csv} ({len(tab)} rows)\n")

    verdicts = {}

    # ── Q1 ──────────────────────────────────────────────────────────────────
    n_same = int(tab["sha_igual_ref_vs_False"].sum())
    verdicts["Q1"] = (n_same == len(tab),
                      f"False == c714451 em {n_same}/{len(tab)} séries (sha256 do periods)")
    if n_same != len(tab):
        print(tab[~tab["sha_igual_ref_vs_False"]][["id", "seq_False"]].to_string(index=False))

    # ── Q2 ──────────────────────────────────────────────────────────────────
    fired = set(tab[tab["dispara"]]["id"])
    synth_fired = set(tab[(tab["dispara"]) & (tab["fonte"] == "sintetico")]["id"])
    verdicts["Q2"] = (fired == Q2_EXPECTED and not synth_fired,
                      f"dispara em {len(fired)}/63: {sorted(fired)}; "
                      f"esperado {sorted(Q2_EXPECTED)}; sintéticos que disparam: "
                      f"{sorted(synth_fired) or 'nenhum'}; "
                      f"{len(tab) - len(fired)} séries byte-idênticas entre False e True")

    # ── Q3-Q6 ───────────────────────────────────────────────────────────────
    for q, sid in (("Q3", "20180170"), ("Q4", "20190325"), ("Q5", "20191014"),
                   ("Q6", "20190639")):
        got = on["records"][sid]["sequencia"]
        want = Q3_Q7[sid]
        ok = got == want
        msg = f"{sid}: {got}" + ("" if ok else f"  (esperado {want})")
        if q == "Q6":
            blocks = blocks_str(run(allser[sid], pv, gp, True)["periods"])
            ok = ok and blocks == Q6_BLOCKS
            msg += f"\n        blocos: {blocks}"
            if blocks != Q6_BLOCKS:
                msg += f"\n        esperado: {Q6_BLOCKS}"
        if q == "Q3":
            ok = ok and bool(tab.loc[tab["id"] == sid, "bate_True"].iloc[0])
            msg += f"  | bate rótulo: {tab.loc[tab['id'] == sid, 'bate_True'].iloc[0]}"
        verdicts[q] = (ok, msg)

    # ── Q7 — 20180608, before and after H ───────────────────────────────────
    sid = "20180608"
    q7_lines, q7_ok = [], True
    for flag in (False, True):
        before, boundary, final = pre_H(allser[sid], pv, gp, flag)
        real_final = run(allser[sid], pv, gp, flag)["periods"]
        replay_ok = [str(x) for x in final] == [str(x) for x in real_final]
        q7_ok = q7_ok and replay_ok
        q7_lines.append(
            f"        flag={flag}: replay==get_periods {replay_ok}; boundary={boundary}; "
            f"ANTES de H {blocks_str(before)}; DEPOIS {seq_of(real_final)}")
    same = (off["records"][sid]["periods_sha256"] == on["records"][sid]["periods_sha256"])
    q7_ok = q7_ok and same
    verdicts["Q7"] = (q7_ok, f"{sid}: saída final idêntica entre False e True: {same}\n"
                      + "\n".join(q7_lines))

    # ── Q8 — the incipient boundary ─────────────────────────────────────────
    diffs = []
    for sid in ids:
        _, b_off, _ = pre_H(allser[sid], pv, gp, False)
        _, b_on, _ = pre_H(allser[sid], pv, gp, True)
        if b_off != b_on:
            diffs.append((sid, b_off, b_on))
    verdicts["Q8"] = (not diffs,
                      f"boundary idêntico entre False e True em {len(ids) - len(diffs)}/{len(ids)}"
                      + (f"; divergem: {diffs}" if diffs else ""))

    print("=" * 74)
    print("PORTÃO — Q1 a Q8")
    print("=" * 74)
    for q in ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"):
        ok, msg = verdicts[q]
        print(f"  {q}: {'CONFIRMADA' if ok else 'REFUTADA'} — {msg}")
    all_ok = all(ok for ok, _ in verdicts.values())
    print()
    print(f"  Q1-Q8: {'PASS' if all_ok else 'FAIL'}  (Q9 = a suíte, rodada à parte)")
    print()

    scored = tab[(tab["split"] == "treino") & (tab["bate_False"] != "")]
    n_off = int((scored["bate_False"] == True).sum())
    n_on = int((scored["bate_True"] == True).sum())
    print(f"  acerto de sequência — TREINO apenas ({len(scored)} séries): "
          f"False {n_off}/{len(scored)} -> True {n_on}/{len(scored)}")
    excepted = n_on + int(
        ((scored["id"] == "20190639") & (scored["bate_True"] == False)).sum())
    print(f"  com a exceção declarada para 20190639 (avaliado pelos blocos de Q6, "
          f"decisão do Danilo): {excepted}/{len(scored)}")
    print("  o split de TESTE não é pontuado aqui e seus rótulos não são lidos.")
    print()
    print(tab[tab["dispara"]][["id", "split", "ramo", "seq_False", "seq_True",
                               "rotulo", "bate_False", "bate_True"]].to_string(index=False))

    make_figures(sorted(fired), allser, pv, gp, names, a.outdir)
    return 0 if all_ok else 1


def make_figures(ids, allser, pv, gp, names, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len(ids), 1, figsize=(12, 2.3 * len(ids)))
    for ax, sid in zip(np.atleast_1d(axes), ids):
        res_off = run(allser[sid], pv, gp, False)
        res_on = run(allser[sid], pv, gp, True)
        z = np.asarray(res_off["z"], dtype=float)
        ax.plot(range(len(z)), z, color="k", lw=1.1, zorder=3)
        for half, per in ((0, res_off["periods"]), (1, res_on["periods"])):
            labs = [normalize_phase(str(v)) for v in per]
            start = 0
            for i in range(1, len(labs) + 1):
                if i == len(labs) or labs[i] != labs[start]:
                    ax.axvspan(start - 0.5, i - 0.5, ymin=0.5 * half,
                               ymax=0.5 * (half + 1),
                               color=PHASE_COLORS.get(labs[start], "white"),
                               alpha=0.5, lw=0)
                    start = i
        ax.set_title(f"{sid}{(' — ' + names[sid]) if sid in names else ''}   "
                     f"(baixo: reclassify_index0=False | alto: True)",
                     fontsize=9, loc="left")
        ax.set_ylabel("z", fontsize=8)
        ax.tick_params(labelsize=7)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.5)
               for c in PHASE_COLORS.values()]
    fig.legend(handles, list(PHASE_COLORS), loc="lower center", ncol=5, fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    png = outdir / "stage2_changed_series.png"
    fig.savefig(png, dpi=140)
    print(f"\nwrote {png}")


if __name__ == "__main__":
    raise SystemExit(main())
