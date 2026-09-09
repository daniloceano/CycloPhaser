#!/usr/bin/env python
"""TAREFA 1 (rodada 4) — gate: 2x2 table + sign/magnitude table for the 12
synthetic cases.

MUST be run against BASELINE code (the idx0 fix stashed out) -- caller is
responsible for that (git stash before running, pop after).

READ-ONLY. Reads tests/synthetic/cases.py (already-generated series, no
package modification) and calls process_vorticity / find_peaks_valleys
exactly as shipped, with cyclophaser_params-9.yaml unmodified.

"abre_com_decaimento_genuino" = segments[0]["type"] == "D" (generator ground
truth, not CycloPhaser's own output).

"mudou_na_regra_incondicional" is read from fix_state_before.json /
fix_state_after.json (already produced in the previous round, unconditional
fix vs baseline) -- not recomputed here.

Run:
    ~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python \
        research/labels/diagnostics/build_synthetic_sign_table.py
"""
import csv
import json
import sys
import warnings
from pathlib import Path

DIAG_DIR = Path(__file__).resolve().parent
REPO_ROOT = DIAG_DIR.parent.parent.parent
LABELS_DIR = REPO_ROOT / "research" / "labels"
sys.path.insert(0, str(LABELS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from cyclophaser.determine_periods import process_vorticity, get_periods, find_peaks_valleys  # noqa: E402
from tests.synthetic.cases import CASES  # noqa: E402

CONFIG_PATH = Path.home() / "Downloads" / "cyclophaser_params-9.yaml"
PV_KEYS = ("use_filter", "replace_endpoints_with_lowpass", "use_smoothing",
           "use_smoothing_twice", "savgol_polynomial", "cutoff_low",
           "cutoff_high", "boundary_padding")


def load_config(path):
    import inspect
    doc = yaml.safe_load(path.read_text()) or {}
    gp_accepted = set(inspect.signature(get_periods).parameters) - {"vorticity"}
    pv = {k: v for k, v in (doc.get("filter_params") or {}).items() if k in PV_KEYS}
    gp = {k: v for k, v in (doc.get("phase_params") or {}).items() if k in gp_accepted}
    return pv, gp


def sign_str(x: float) -> str:
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "0"


def opaque_synthetic_id(case_name: str) -> str:
    import hashlib
    return "s" + hashlib.sha256(case_name.encode("utf-8")).hexdigest()[:8]


def main():
    pv, gp = load_config(CONFIG_PATH)

    before = json.loads((DIAG_DIR / "fix_state_before.json").read_text())["tracks"]
    after = json.loads((DIAG_DIR / "fix_state_after.json").read_text())["tracks"]

    rows = []
    for case_name, case in CASES.items():
        oid = opaque_synthetic_id(case_name)
        values = case["series"].astype("float64")
        n = len(values)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vort = process_vorticity(pd.DataFrame({"zeta": values}), **pv)
            df = get_periods(vort, **gp)

        z = df["z"]
        z_unfil = df["z_unfil"]
        idx0_tipo_raw = df["z_peaks_valleys"].iloc[0]
        idx0_tipo = idx0_tipo_raw if isinstance(idx0_tipo_raw, str) else "nenhum"

        d_filt = float(z.iloc[1] - z.iloc[0])
        d_bruta = float(z_unfil.iloc[1] - z_unfil.iloc[0])

        abre_decaimento_genuino = (case["segments"][0]["type"] == "D")
        sinais_concordam = (sign_str(d_bruta) == sign_str(d_filt))

        mudou = None
        if oid in before and oid in after:
            mudou = (before[oid]["periods"] != after[oid]["periods"])

        rows.append({
            "caso": case_name,
            "abre_com_decaimento_genuino": "sim" if abre_decaimento_genuino else "nao",
            "idx0_tipo": idx0_tipo,
            "sinal_dz_bruta": sign_str(d_bruta),
            "sinal_dz_filtrada": sign_str(d_filt),
            "sinais_concordam": "sim" if sinais_concordam else "nao",
            "mag_dz_bruta": abs(d_bruta),
            "mag_dz_filtrada": abs(d_filt),
            "mudou_na_regra_incondicional": ("sim" if mudou else "nao") if mudou is not None else "nao_determinado",
            "_opening_shape_seg0": case["segments"][0].get("shape"),
            "_noise_frac": case.get("kwargs", {}).get("noise_frac", 0.0),
        })

    fieldnames = ["caso", "abre_com_decaimento_genuino", "idx0_tipo",
                  "sinal_dz_bruta", "sinal_dz_filtrada", "sinais_concordam",
                  "mag_dz_bruta", "mag_dz_filtrada", "mudou_na_regra_incondicional"]
    out_path = DIAG_DIR / "synthetic_sign_table.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})
    print(f"wrote {out_path}")

    # console report with the extra shape/noise columns for interpretation
    print(f"\n{'caso':<26}{'genuino':<9}{'idx0':<8}{'bruta':<7}{'filt':<7}{'concord':<9}"
          f"{'mag_bruta':<14}{'mag_filt':<14}{'shape0':<9}{'noise':<7}{'mudou'}")
    for r in rows:
        print(f"{r['caso']:<26}{r['abre_com_decaimento_genuino']:<9}{r['idx0_tipo']:<8}"
              f"{r['sinal_dz_bruta']:<7}{r['sinal_dz_filtrada']:<7}{r['sinais_concordam']:<9}"
              f"{r['mag_dz_bruta']:<14.6e}{r['mag_dz_filtrada']:<14.6e}"
              f"{r['_opening_shape_seg0']:<9}{r['_noise_frac']:<7}{r['mudou_na_regra_incondicional']}")

    # 2x2 table
    from collections import Counter
    table = Counter((r["idx0_tipo"], r["sinais_concordam"]) for r in rows)
    print("\n2x2 idx0_tipo x sinais_concordam:")
    for k in sorted(table):
        print(" ", k, table[k])

    # gate check
    genuine = [r for r in rows if r["abre_com_decaimento_genuino"] == "sim"]
    print(f"\ngate: {len(genuine)} genuine-decay-opening cases")
    for r in genuine:
        print(f"  {r['caso']}: sinais_concordam={r['sinais_concordam']}  "
              f"mag_bruta={r['mag_dz_bruta']:.6e}  mag_filt={r['mag_dz_filtrada']:.6e}")
    gate_pass = all(r["sinais_concordam"] == "sim" for r in genuine)
    print(f"\nGATE: {'PASSOU' if gate_pass else 'FALHOU'}")


if __name__ == "__main__":
    main()
