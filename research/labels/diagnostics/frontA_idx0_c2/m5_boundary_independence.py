#!/usr/bin/env python
"""M5 — does the incipient `boundary` depend on the phase map? (code + measurement)

Read: `find_incipient_period`'s plateau branch computes

    rel      = _incipient_plateau_rel(df, signal, smooth_window, smooth_polyorder)
    boundary = _incipient_plateau_boundary(rel, tau, crossing, k)

`_incipient_plateau_rel` reads `df['dz']` (signal="derivative") or
`np.gradient(df['z_unfil'])` (signal="vorticity"), and nothing else from the
frame; `_incipient_plateau_boundary` is a pure function of `(rel, tau, crossing,
k)`. Neither reads `df['periods']` nor any `*_peaks_valleys` column.

Two checks, so the claim rests on more than a reading:

  (1) STATIC — the source of both functions is parsed and every attribute /
      subscript access on the frame is listed. `'periods'` must not appear.
  (2) MEASURED — `boundary` is recomputed on all 63 series with index 0 forced
      to 'peak' and without it. Forcing changes `z_peaks_valleys` and therefore
      the phase map; if `boundary` moved on any series, the independence claim
      would be false.

Run:
    python research/labels/diagnostics/frontA_idx0_c2/m5_boundary_independence.py \
        --config research/labels/configs/cyclophaser_params-13.yaml \
        --outdir research/labels/diagnostics/frontA_idx0_c2/outputs
"""

from __future__ import annotations

import argparse
import ast
import inspect
import sys
import textwrap
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import provenance, replay, sha256_of  # noqa: E402

from labels_core import load_real_series, load_synthetic_series  # noqa: E402
from evaluate_against_labels import load_config  # noqa: E402

from cyclophaser import find_stages  # noqa: E402
from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel, find_incipient_period,
)


def frame_keys(fn) -> set[str]:
    """Every string literal used as a subscript key inside `fn`'s source."""
    src = inspect.getsource(fn)
    tree = ast.parse(textwrap.dedent(src))
    keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str):
            keys.add(node.slice.value)
    return keys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    provenance()
    pv, gp = load_config(a.config)
    print(f"config: {a.config}\n  sha256: {sha256_of(a.config)}\n")

    # ── (1) static ─────────────────────────────────────────────────────────
    src_file = Path(find_stages.__file__)
    lines = src_file.read_text().splitlines()
    print("=" * 74)
    print("M5 (1) — static reading")
    print("=" * 74)
    for fn in (_incipient_plateau_rel, _incipient_plateau_boundary):
        start = inspect.getsourcelines(fn)[1]
        end = start + len(inspect.getsourcelines(fn)[0]) - 1
        keys = sorted(frame_keys(fn))
        print(f"  {fn.__name__}  (find_stages.py:{start}-{end})")
        print(f"    string subscript keys: {keys}")
        print(f"    reads 'periods'      : {'periods' in keys}")
    # the call site
    for i, line in enumerate(lines, start=1):
        if "_incipient_plateau_rel(" in line or "_incipient_plateau_boundary(" in line \
                or "df.iloc[:boundary" in line:
            print(f"    call site  find_stages.py:{i}: {line.strip()}")
    start = inspect.getsourcelines(find_incipient_period)[1]
    print(f"  find_incipient_period (find_stages.py:{start}-) plateau branch keys: "
          f"{sorted(frame_keys(find_incipient_period))}")

    # ── (2) measured ───────────────────────────────────────────────────────
    real = load_real_series()
    synth, names = load_synthetic_series()
    allser = [(k, real[k], "real") for k in sorted(real)] + \
             [(k, synth[k], "sintetico") for k in sorted(synth)]

    rows = []
    for sid, values, source in allser:
        base = replay(values, pv, gp, force="none", verify=False)
        forced = replay(values, pv, gp, force="all", verify=False)
        b = {}
        for tag, out in (("base", base), ("forcado", forced)):
            rel = _incipient_plateau_rel(out["df"],
                                         gp.get("incipient_plateau_signal", "derivative"),
                                         gp.get("incipient_smooth_window", 0),
                                         gp.get("incipient_smooth_polyorder", 3))
            b[tag] = int(_incipient_plateau_boundary(
                rel, gp.get("incipient_plateau_tau", 0.20),
                gp.get("incipient_plateau_crossing", "single"),
                gp.get("incipient_plateau_k", 3)))
        rows.append({"id": sid, "fonte": source, "caso": names.get(sid, ""),
                     "boundary_base": b["base"], "boundary_forcado": b["forcado"],
                     "igual": b["base"] == b["forcado"]})

    tab = pd.DataFrame(rows)
    out_csv = a.outdir / "m5_boundary_independence.csv"
    tab.to_csv(out_csv, index=False)
    print()
    print("=" * 74)
    print("M5 (2) — measured")
    print("=" * 74)
    n_eq = int(tab["igual"].sum())
    print(f"  boundary identical with and without index 0 forced: {n_eq}/{len(tab)}")
    if n_eq != len(tab):
        print(tab[~tab["igual"]].to_string(index=False))
    print(f"  wrote {out_csv}")
    return 0 if n_eq == len(tab) else 1


if __name__ == "__main__":
    raise SystemExit(main())
