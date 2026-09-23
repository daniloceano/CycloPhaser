#!/usr/bin/env python
"""Does the new default change anything under the PACKAGE's own defaults?

The brief provided for a separate commit updating the CI reference baselines,
on the assumption that a change of default behaviour moves them. The suite says
it does not. Absence of a failure is not a measurement, so this is the
measurement: `determine_periods(series)` with no arguments at all, both ways,
over the 51 calibration tracks, the 12 synthetic series and the packaged example
file, compared step by step.

The reason to expect no change — stated here so the result is a test of it and
not a rationalisation after the fact: raw `argrelextrema` output alternates
peak/valley, so the extremum right after a valley at index 0 is a peak the
series rose to, which cannot lie below index 0; symmetrically for a peak. The
rule therefore has nothing to act on until something removes the extremum in
between — which is what the prominence filter does, and the package's defaults
leave that filter OFF (`prominence=None`, `prominence_relative=None`).

Run:
    python stage2_defaults_check.py --outdir <dir>
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import provenance  # noqa: E402

from labels_core import load_real_series, load_synthetic_series  # noqa: E402

from cyclophaser import determine_periods, example_file  # noqa: E402


def run(values, **kw):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return [str(v) for v in determine_periods(values, **kw)["periods"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)
    provenance()

    real = load_real_series()
    synth, names = load_synthetic_series()
    series = [(k, real[k], "real") for k in sorted(real)] + \
             [(k, synth[k], "sintetico") for k in sorted(synth)]

    track = pd.read_csv(example_file, parse_dates=[0], delimiter=";", index_col=[0])
    series.append(("<example_file>", track["min_max_zeta_850"], "exemplo"))

    rows = []
    for sid, values, source in series:
        off = run(values, reclassify_index0=False)
        on = run(values, reclassify_index0=True)
        default = run(values)
        rows.append({"id": sid, "fonte": source, "n_steps": len(values),
                     "igual_off_on": off == on,
                     "default_igual_on": default == on})
    tab = pd.DataFrame(rows)
    out = a.outdir / "stage2_defaults_check.csv"
    tab.to_csv(out, index=False)

    n_same = int(tab["igual_off_on"].sum())
    n_def = int(tab["default_igual_on"].sum())
    print()
    print("=" * 74)
    print("Sob os DEFAULTS do pacote (filtro de proeminência desligado)")
    print("=" * 74)
    print(f"  saída idêntica com e sem a regra : {n_same}/{len(tab)} séries")
    print(f"  o default do pacote == regra ON  : {n_def}/{len(tab)} séries")
    if n_same != len(tab):
        print(tab[~tab["igual_off_on"]].to_string(index=False))
    print(f"  wrote {out}")
    return 0 if n_same == len(tab) else 1


if __name__ == "__main__":
    raise SystemExit(main())
