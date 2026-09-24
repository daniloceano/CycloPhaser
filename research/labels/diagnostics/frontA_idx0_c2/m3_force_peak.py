#!/usr/bin/env python
"""M3 — re-measure "force index 0 to 'peak'" (Front A, 6060c6d) under params-13.

Front A's original measurement ran under params-9 and against a detector whose
provenance item 13 later questioned. This re-runs the same variant at the
develop-v2.1 tip under params-13, on the 9 series the brief names: the 5 tracks
whose index 0 is typed `valley`, and the 4 synthetic cases that open with a
genuine decay by construction.

Where C2 fires on its `valley->peak` branch, this IS what C2 would produce — so
these rows double as C2's forward measurement. Where C2 does NOT fire, the row
says what the unconditional Front A variant does and C2 does not.

Two force channels are measured, because `6060c6d` patched `find_peaks_valleys`
itself and therefore hit z, dz AND dz2, while C2 is defined on the z extremum
list alone:
    force=all     — the literal 6060c6d behaviour
    force=z_only  — z's extremum list only
Under params-13 (`incipient_method: plateau`) nothing reads `dz_peaks_valleys`,
so the two are expected to coincide; the script measures that rather than
assuming it.

Nothing in `cyclophaser/` is modified: the variant lives in `common.py` as a
local copy and is injected by an explicit replay of `get_periods`' body, whose
fidelity is asserted on the unforced run.

20206498 is in the frozen TEST split: its sequences are printed, and never
compared with its label. The label is not read.

Run:
    python research/labels/diagnostics/frontA_idx0_c2/m3_force_peak.py \
        --config research/labels/configs/cyclophaser_params-13.yaml \
        --outdir research/labels/diagnostics/frontA_idx0_c2/outputs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    A_SYNTHETIC_CASES, A_TARGET_IDS, TEST_ONLY_EXAMINE, phase_starts,
    provenance, replay, seq_str, sha256_of,
)

from labels_core import (  # noqa: E402
    load_real_series, load_synthetic_series, normalize_phase, opaque_synthetic_id,
    read_labels, series_sha256,
)
from evaluate_against_labels import load_config  # noqa: E402


def label_seq(rec):
    return [(p["phase"], int(p["start_idx"]), int(p["tolerance_idx"]),
             bool(p.get("unsure"))) for p in rec["phases"]]


def compare(det_starts, rec):
    """(match: bool, detail: str) under score_phase_sequences' own criterion."""
    lab = label_seq(rec)
    det = [(normalize_phase(p), int(i)) for p, i in det_starts]
    if [p for p, _, _, _ in lab] != [p for p, _ in det]:
        return False, "sequencia diferente"
    bits = []
    for k in range(1, len(lab)):
        phase, lidx, tol, unsure = lab[k]
        didx = det[k][1]
        err = abs(didx - lidx)
        flag = "unsure" if unsure else ("ok" if err <= tol else "FORA")
        bits.append(f"{phase}@{lidx}±{tol}: det {didx} (err {err}, {flag})")
    return True, "; ".join(bits) if bits else "sequencia de 1 fase"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--extra", nargs="*", default=[],
                    help="extra real track ids to measure (e.g. a C2 peak->valley hit)")
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    pv, gp = load_config(a.config)
    print(f"config: {a.config}\n  sha256: {sha256_of(a.config)}")
    print(f"  get_periods kwargs ({len(gp)})\n", flush=True)

    real = load_real_series()
    synth, case_names = load_synthetic_series()
    labels = read_labels()

    targets = [(sid, real[sid], "real", "") for sid in A_TARGET_IDS]
    for case in A_SYNTHETIC_CASES:
        oid = opaque_synthetic_id(case)
        targets.append((oid, synth[oid], "sintetico", case))
    for sid in a.extra:
        targets.append((sid, real[sid], "real (extra)", ""))

    rows = []
    for sid, values, source, case in targets:
        base = replay(values, pv, gp, force="none", verify=True)
        assert base["replay_ok"] is True, f"replay diverged for {sid}"
        f_all = replay(values, pv, gp, force="all", verify=False)
        f_z = replay(values, pv, gp, force="z_only", verify=False)

        seq_base = seq_str(base["final"])
        seq_all = seq_str(f_all["final"])
        seq_z = seq_str(f_z["final"])
        identical = [str(x) for x in f_all["final"]] == [str(x) for x in f_z["final"]]

        row = {
            "id": sid, "fonte": source, "caso": case, "n_steps": len(values),
            "seq_base": seq_base,
            "seq_forcado_all": seq_all,
            "seq_forcado_z_only": seq_z,
            "all_==_z_only": identical,
            "mudou": seq_base != seq_all,
        }

        if sid in TEST_ONLY_EXAMINE:
            row.update({"rotulo": "<split de teste: nao lido>",
                        "bate_base": "", "bate_forcado": "",
                        "detalhe_base": "", "detalhe_forcado": ""})
        else:
            rec = labels.get(sid)
            if rec is None:
                row.update({"rotulo": "<sem rotulo>", "bate_base": "",
                            "bate_forcado": "", "detalhe_base": "",
                            "detalhe_forcado": ""})
            else:
                stale = rec["series_sha256"] != series_sha256(values)
                if stale:
                    raise SystemExit(f"{sid}: series_sha256 mismatch — label is stale")
                lab_txt = ">".join(p["phase"] for p in rec["phases"])
                m_b, d_b = compare(phase_starts(base["final"]), rec)
                m_f, d_f = compare(phase_starts(f_all["final"]), rec)
                row.update({"rotulo": lab_txt,
                            "bate_base": m_b, "bate_forcado": m_f,
                            "detalhe_base": d_b, "detalhe_forcado": d_f})
        rows.append(row)

    tab = pd.DataFrame(rows)
    out_csv = a.outdir / "m3_force_peak.csv"
    tab.to_csv(out_csv, index=False)
    print(f"wrote {out_csv}\n")

    for _, r in tab.iterrows():
        print("-" * 74)
        head = f"{r['id']} ({r['fonte']}{(' — ' + r['caso']) if r['caso'] else ''}, n={r['n_steps']})"
        print(head)
        print(f"  rotulo            : {r['rotulo']}")
        print(f"  base (params-13)  : {r['seq_base']}")
        print(f"  forcado (all)     : {r['seq_forcado_all']}")
        print(f"  forcado (z_only)  : {r['seq_forcado_z_only']}"
              f"   [all == z_only: {r['all_==_z_only']}]")
        print(f"  mudou             : {r['mudou']}")
        if r["detalhe_base"] != "" or r["bate_base"] != "":
            print(f"  bate base         : {r['bate_base']}  | {r['detalhe_base']}")
            print(f"  bate forcado      : {r['bate_forcado']}  | {r['detalhe_forcado']}")
    print("-" * 74)

    scored = tab[tab["bate_base"] != ""]
    if len(scored):
        print(f"\nscored (label read): {len(scored)} series")
        print(f"  sequence match, base    : {int((scored['bate_base'] == True).sum())}/{len(scored)}")
        print(f"  sequence match, forced  : {int((scored['bate_forcado'] == True).sum())}/{len(scored)}")
    print(f"all == z_only on {int(tab['all_==_z_only'].sum())}/{len(tab)} series")

    make_figure(targets, pv, gp, labels, a.outdir)
    return 0


def make_figure(targets, pv, gp, labels, outdir):
    """One row per series: z, with the base and the forced phase map as bands."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"(no figure: {exc})")
        return
    import numpy as np
    from labels_core import PHASE_COLORS

    fig, axes = plt.subplots(len(targets), 1, figsize=(11, 2.0 * len(targets)))
    for ax, (sid, values, source, case) in zip(np.atleast_1d(axes), targets):
        base = replay(values, pv, gp, force="none", verify=False)
        forced = replay(values, pv, gp, force="all", verify=False)
        z = np.asarray(base["df"]["z"], dtype=float)
        ax.plot(range(len(z)), z, color="k", lw=0.9, zorder=3)
        for half, per in ((0, base["final"]), (1, forced["final"])):
            labs = [normalize_phase(str(v)) for v in per]
            lo, hi = ax.get_ylim()
            start = 0
            for i in range(1, len(labs) + 1):
                if i == len(labs) or labs[i] != labs[start]:
                    ax.axvspan(start - 0.5, i - 0.5,
                               ymin=0.5 * half, ymax=0.5 * (half + 1),
                               color=PHASE_COLORS.get(labs[start], "white"),
                               alpha=0.5, lw=0)
                    start = i
        title = f"{sid}{(' — ' + case) if case else ''}   (baixo: base | alto: idx0 forcado a peak)"
        ax.set_title(title, fontsize=8, loc="left")
        ax.set_ylabel("z", fontsize=7)
        ax.tick_params(labelsize=7)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.5) for c in PHASE_COLORS.values()]
    fig.legend(handles, list(PHASE_COLORS), loc="lower center", ncol=5, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    png = outdir / "m3_force_peak.png"
    fig.savefig(png, dpi=140)
    print(f"wrote {png}")


if __name__ == "__main__":
    raise SystemExit(main())
