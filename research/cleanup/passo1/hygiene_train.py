#!/usr/bin/env python
"""Passo 1 — hygiene of the new default (C1) on the TRAIN series only.

    <cyclophaser env python> -P research/cleanup/passo1/hygiene_train.py

No scoring against labels. For every TRAIN series, in one process, on the code
of this working tree (asserted in-process):

  default : determine_periods(series)                       (no arguments)
  edge    : determine_periods(series, boundary_padding="edge")

and records, per mode: exception (if any); validity of the phase sequence;
whether incipient was refused; the phase sequence. Across modes: whether the
final phase map changed. Two supplementary facts per mode, from
process_vorticity on the same series, used to check text claims (not
predictions): defect I (item 8(d): sign(z[1]-z[0]) of the raw input disagrees
with that of `filtered_vorticity`) and |dz_dt_smoothed2[0]| / max|dz_dt_smoothed2|
(the normalised filtered derivative at t0).

Definitions, fixed in passo1/PREVISOES.md before any measurement:
  TRAIN     = `train:` of research/labels/split.yaml plus every `batches.*.train`.
              Only those files are opened (no test series is read).
  valid     = no exception; `periods` has the series' length and no nulls; every
              label, numbering stripped, in {incipient, intensification,
              mature, decay, residual}.
  refusal   = the final map does not start in `incipient` (leading incipient
              run at t0 of length 0).

Each series is checked against the `series_sha256` of its label before use (the
labels file is read; only TRAIN entries are looked up). Writes
hygiene_train.json and hygiene_train.md next to it; no absolute path is written.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "labels"))
import cyclophaser  # noqa: E402

assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
assert os.path.realpath(cyclophaser.__file__).startswith(os.path.realpath(ROOT) + os.sep), cyclophaser.__file__
dp = importlib.import_module("cyclophaser.determine_periods")
from labels_core import read_labels, series_sha256  # noqa: E402

OUT = Path(__file__).resolve().parent
PHASES = {"incipient", "intensification", "mature", "decay", "residual"}
MODES = {"default": {}, "edge": {"boundary_padding": "edge"}}


def train_series():
    split = yaml.safe_load((ROOT / "research/labels/split.yaml").read_text())
    src = split["source"]
    out = {}
    for sid in split["train"]:
        if src[sid] == "real":
            df = pd.read_csv(ROOT / "tests/calibration_data" / f"{sid}.csv", sep=";",
                             index_col="time", parse_dates=True)
        else:
            df = pd.read_csv(ROOT / "tests/synthetic/data" / f"{sid}.csv", sep=";",
                             index_col="time", parse_dates=True, float_precision="round_trip")
        out[sid] = ("top-level " + src[sid], df["min_max_zeta_850"].astype("float64"))
    for name, blk in (split.get("batches") or {}).items():
        for sid in blk.get("train", []):
            p = ROOT / blk["data_dir"] / f"{sid}.csv"
            got = hashlib.sha256(p.read_bytes()).hexdigest()
            assert got == blk["file_sha256"][sid], f"{sid}: file sha256 drifted"
            df = pd.read_csv(p, sep=";", index_col="time", parse_dates=True)
            out[sid] = (f"batch {name}", df["min_max_zeta_850"].astype("float64"))
    return out


def base(label) -> str:
    return re.sub(r"\s*\d+$", "", str(label)).strip()


def sequence(periods) -> list[str]:
    seq = []
    for p in periods:
        b = base(p)
        if not seq or seq[-1] != b:
            seq.append(b)
    return seq


def run(series, kw):
    rec = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = dp.determine_periods(series, **kw)
    except Exception as e:  # recorded, never raised
        return dict(exception=f"{type(e).__name__}: {e}", valid=False, refused=None, sequence=None, periods=None)
    per = df["periods"]
    labels = [str(x) for x in per]
    problems = []
    if len(per) != len(series):
        problems.append(f"length {len(per)} != {len(series)}")
    if per.isna().any():
        problems.append(f"{int(per.isna().sum())} null")
    bad = sorted({base(x) for x in labels} - PHASES)
    if bad:
        problems.append(f"unknown labels {bad}")
    rec.update(exception=None, valid=not problems, problems=problems,
               refused=base(labels[0]) != "incipient" if labels else None,
               sequence=sequence(labels), periods=labels)
    return rec


def t0_facts(series, kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        v = dp.process_vorticity(pd.DataFrame({"zeta": series}), **kw)
    raw = v["zeta"].values
    filt = v["filtered_vorticity"].values
    d_raw, d_filt = float(raw[1] - raw[0]), float(filt[1] - filt[0])
    dz = np.asarray(v["dz_dt_smoothed2"].values, dtype=float)
    amax = float(np.nanmax(np.abs(dz)))
    return dict(defect_I=((d_raw > 0) != (d_filt > 0)) if (d_raw != 0 and d_filt != 0) else None,
                dz_t0_rel=(abs(float(dz[0])) / amax) if amax > 0 else None)


def main():
    labels = read_labels()
    series = train_series()
    stale = [s for s, (_, v) in series.items() if s in labels and series_sha256(v) != labels[s]["series_sha256"]]
    assert not stale, f"series_sha256 mismatch: {stale}"
    rows = []
    for sid in sorted(series):
        grp, s = series[sid]
        r = dict(id=sid, group=grp, n=len(s), labelled=sid in labels)
        for m, kw in MODES.items():
            r[m] = run(s, kw)
            r[m].update(t0_facts(s, kw))
        a, b = r["default"]["periods"], r["edge"]["periods"]
        r["map_changed"] = None if (a is None or b is None) else a != b
        r["sequence_changed"] = None if (a is None or b is None) else r["default"]["sequence"] != r["edge"]["sequence"]
        rows.append(r)

    def count(m, key, val=True):
        return sum(1 for r in rows if r[m].get(key) is val)

    summary = dict(
        n_train=len(rows),
        n_by_group={g: sum(1 for r in rows if r["group"] == g) for g in sorted({r["group"] for r in rows})},
        cyclophaser_file=os.path.relpath(cyclophaser.__file__, ROOT),
        exceptions={m: sum(1 for r in rows if r[m]["exception"]) for m in MODES},
        invalid_sequences={m: sum(1 for r in rows if not r[m]["valid"]) for m in MODES},
        refusals={m: count(m, "refused") for m in MODES},
        refused_ids={m: [r["id"] for r in rows if r[m]["refused"]] for m in MODES},
        maps_changed=sum(1 for r in rows if r["map_changed"]),
        sequences_changed=sum(1 for r in rows if r["sequence_changed"]),
        defect_I={m: count(m, "defect_I") for m in MODES},
        defect_I_ids={m: [r["id"] for r in rows if r[m]["defect_I"]] for m in MODES},
        dz_t0_rel_zero={m: sum(1 for r in rows if r[m]["dz_t0_rel"] == 0.0) for m in MODES},
        dz_t0_rel_median={m: float(np.median([r[m]["dz_t0_rel"] for r in rows if r[m]["dz_t0_rel"] is not None]))
                          for m in MODES},
        dz_t0_rel_max={m: float(np.max([r[m]["dz_t0_rel"] for r in rows if r[m]["dz_t0_rel"] is not None]))
                       for m in MODES},
    )
    slim = [{k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "periods"})
             for k, v in r.items()} for r in rows]
    (OUT / "hygiene_train.json").write_text(json.dumps(dict(summary=summary, rows=slim), indent=1, ensure_ascii=False))

    L = ["# Passo 1 — higiene do novo default (treino)\n",
         "Gerado por `passo1/hygiene_train.py` (definições em `passo1/PREVISOES.md`). Sem pontuação contra rótulos. "
         f"`cyclophaser.__file__` = `{summary['cyclophaser_file']}` (relativo à raiz; assert no processo).\n",
         "| medida | default (reflect) | edge |", "|---|---|---|"]
    for k in ("exceptions", "invalid_sequences", "refusals", "defect_I", "dz_t0_rel_zero", "dz_t0_rel_median", "dz_t0_rel_max"):
        v = summary[k]
        f = (lambda x: f"{x:.3f}") if "median" in k or "max" in k else str
        L.append(f"| {k} | {f(v['default'])} | {f(v['edge'])} |")
    L += ["", f"Séries de treino: **{summary['n_train']}** ({', '.join(f'{g}: {n}' for g, n in summary['n_by_group'].items())}). "
          f"Mapas de fase que mudam entre default e edge: **{summary['maps_changed']}**; sequências que mudam: "
          f"**{summary['sequences_changed']}**.",
          f"Recusas de incipient — default: {summary['refused_ids']['default'] or 'nenhuma'}; edge: {summary['refused_ids']['edge'] or 'nenhuma'}.",
          f"Defeito I — default: {summary['defect_I_ids']['default'] or 'nenhum'}; edge: {summary['defect_I_ids']['edge'] or 'nenhum'}.", "",
          "| id | grupo | n | exceção (d/e) | válida (d/e) | recusa (d/e) | mapa muda | defeito I (d/e) | |dz|t0 rel (d/e) | sequência default | sequência edge |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    yn = lambda x: "—" if x is None else ("sim" if x else "não")
    for r in rows:
        d, e = r["default"], r["edge"]
        fr = lambda x: "—" if x is None else f"{x:.3f}"
        L.append(f"| `{r['id']}` | {r['group']} | {r['n']} | {yn(bool(d['exception']))}/{yn(bool(e['exception']))} | "
                 f"{yn(d['valid'])}/{yn(e['valid'])} | {yn(d['refused'])}/{yn(e['refused'])} | {yn(r['map_changed'])} | "
                 f"{yn(d['defect_I'])}/{yn(e['defect_I'])} | {fr(d['dz_t0_rel'])}/{fr(e['dz_t0_rel'])} | "
                 f"{' > '.join(d['sequence'] or ['EXC'])} | {' > '.join(e['sequence'] or ['EXC'])} |")
    (OUT / "hygiene_train.md").write_text("\n".join(L) + "\n")
    print(json.dumps({k: summary[k] for k in summary if not k.endswith("_ids")}, ensure_ascii=False))
    print("refused:", summary["refused_ids"])
    print("defect I:", summary["defect_I_ids"])


if __name__ == "__main__":
    main()
