#!/usr/bin/env python
"""M2 addendum — what C2's `peak->valley` branch would do where it fires.

Prediction P4 declared the `peak->valley` branch would fire on 0 of 63 series.
It fires on one (20190639, train split), which the brief's measurement plan did
not provide for: M3 only measures forcing index 0 to 'peak'. This script
measures the mirror operation on exactly the series where that branch fires, so
the front can say what C2 as specified would DO there rather than only that it
would trigger.

The mirror force exists only in `common.py`; no version of `cyclophaser/` has
ever contained it.

Run:
    python research/labels/diagnostics/frontA_idx0_c2/m2b_peak_to_valley.py \
        --config research/labels/configs/cyclophaser_params-13.yaml \
        --outdir research/labels/diagnostics/frontA_idx0_c2/outputs --ids 20190639
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    TEST_ONLY_EXAMINE, phase_starts, provenance, replay, seq_str, sha256_of,
)
from m3_force_peak import compare  # noqa: E402

from labels_core import load_real_series, read_labels, series_sha256  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--ids", nargs="+", required=True)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    pv, gp = load_config(a.config)
    print(f"config: {a.config}\n  sha256: {sha256_of(a.config)}\n")

    real = load_real_series()
    labels = read_labels()
    rows = []
    for sid in a.ids:
        values = real[sid]
        base = replay(values, pv, gp, force="none", verify=True)
        assert base["replay_ok"] is True, sid
        forced = replay(values, pv, gp, force="all_valley", verify=False)
        fz = replay(values, pv, gp, force="z_only_valley", verify=False)
        row = {"id": sid, "n_steps": len(values),
               "seq_base": seq_str(base["final"]),
               "seq_forcado_valley_all": seq_str(forced["final"]),
               "seq_forcado_valley_z_only": seq_str(fz["final"]),
               "all_==_z_only": [str(x) for x in forced["final"]] == [str(x) for x in fz["final"]],
               "mudou": seq_str(base["final"]) != seq_str(forced["final"])}
        if sid in TEST_ONLY_EXAMINE:
            row.update({"rotulo": "<split de teste: nao lido>", "bate_base": "",
                        "bate_forcado": "", "detalhe_base": "", "detalhe_forcado": ""})
        else:
            rec = labels[sid]
            if rec["series_sha256"] != series_sha256(values):
                raise SystemExit(f"{sid}: series_sha256 mismatch — label is stale")
            m_b, d_b = compare(phase_starts(base["final"]), rec)
            m_f, d_f = compare(phase_starts(forced["final"]), rec)
            row.update({"rotulo": ">".join(p["phase"] for p in rec["phases"]),
                        "bate_base": m_b, "bate_forcado": m_f,
                        "detalhe_base": d_b, "detalhe_forcado": d_f})
        rows.append(row)
        print("-" * 74)
        for k, v in row.items():
            print(f"  {k:26s}: {v}")
    print("-" * 74)

    tab = pd.DataFrame(rows)
    out_csv = a.outdir / "m2b_peak_to_valley.csv"
    tab.to_csv(out_csv, index=False)
    print(f"\nwrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
