#!/usr/bin/env python
"""Front B part 1b - which script and which config produces each reference number.

Runs the two scorers at the two configurations and prints the provenance of
every figure quoted in the front B brief. TRAIN split only.

    python research/labels/diagnostics/front_b/reference_score_attribution.py

`measure_topology_proxy.py` lives on branch `research/v3-topology-proxy` and is
not on develop-v2.1, so its figures are quoted from a verified run (2026-09-16,
conda `cyclophaser`) rather than re-executed here; the run is reproduced in
`topology_run_gate_excerpt.txt` next to this file.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EVAL = REPO / "research" / "labels" / "evaluate_against_labels.py"
CONFIG = REPO / "research" / "labels" / "configs" / "cyclophaser_params-9.yaml"

lines = []


def P(s=""):
    print(s)
    lines.append(s)


def run(args):
    r = subprocess.run([sys.executable, str(EVAL)] + args,
                       capture_output=True, text=True, cwd=str(REPO))
    return r.stdout


def parse(txt):
    """{('real'|'synthetic', metric): 'a/b'} from one evaluate run."""
    out, block = {}, None
    for ln in txt.splitlines():
        if "TRAIN · real" in ln:
            block = "real"
        elif "TRAIN · synthetic" in ln:
            block = "synthetic"
        elif "TRAIN · ALL" in ln:
            block = "all"
        if block is None:
            continue
        m = re.search(r"boundary labels\s+(\d+)\s+hit within margin\s+(\d+)", ln)
        if m:
            out[(block, "incipient boundary")] = f"{m.group(2)}/{m.group(1)}"
        m = re.search(r"label says none:\s+(\d+), detector agreed on (\d+)", ln)
        if m:
            out[(block, "refusal")] = f"{m.group(2)}/{m.group(1)}"
        m = re.search(r"sequence\s+(\d+) of (\d+) match", ln)
        if m:
            out[(block, "sequence")] = f"{m.group(1)}/{m.group(2)}"
    return out


P("FRONT B part 1b - provenance of every reference number")
P("=" * 94)
P()
P("Running evaluate_against_labels.py twice (TRAIN only)...")
defaults = parse(run([]))
params9 = parse(run(["--config", str(CONFIG)]))
P()

P(f"  {'metric':<28} {'source':<10} {'DEFAULTS':>10} {'params-9':>10}")
P("  " + "-" * 62)
for src in ("real", "synthetic", "all"):
    for metric in ("incipient boundary", "refusal", "sequence"):
        k = (src, metric)
        if k in defaults or k in params9:
            P(f"  {metric:<28} {src:<10} {defaults.get(k,'-'):>10} "
              f"{params9.get(k,'-'):>10}")
P()
P("=" * 94)
P("ATTRIBUTION of the numbers quoted in the brief")
P("=" * 94)
P()
rowfmt = "  {:<8} {:<34} {:<26} {:<10}"
P(rowfmt.format("number", "script", "config", "verified"))
P("  " + "-" * 82)


def chk(num, script, config, got):
    P(rowfmt.format(num, script, config, "YES" if got == num else f"NO (got {got})"))


chk("8/17", "evaluate_against_labels.py", "params-9",
    params9.get(("real", "incipient boundary")))
chk("14/16", "evaluate_against_labels.py", "params-9",
    params9.get(("real", "refusal")))
chk("18/35", "evaluate_against_labels.py", "params-9",
    params9.get(("real", "sequence")))
chk("9/10", "evaluate_against_labels.py", "params-9",
    params9.get(("synthetic", "incipient boundary")))
chk("12/12", "evaluate_against_labels.py", "params-9",
    params9.get(("synthetic", "sequence")))
chk("11/12", "evaluate_against_labels.py", "PACKAGE DEFAULTS",
    defaults.get(("synthetic", "sequence")))
chk("22/47", "evaluate_against_labels.py", "PACKAGE DEFAULTS",
    defaults.get(("all", "sequence")))
P()
P("  11/12 and 22/47 are ALSO produced by measure_topology_proxy.py (branch")
P("  research/v3-topology-proxy), which runs the detector at package defaults:")
P("      six-function detector        22 / 47    46.8%")
P("      real       n=35   detector 11/35 ( 31.4%)")
P("      synthetic  n=12   detector 11/12 ( 91.7%)")
P("  The two scripts agree exactly at defaults, so 11/12 and 22/47 are NOT")
P("  specific to the topology front - they are the default-parameter figures.")
P()
P("  Consistency check:")
dr = defaults.get(("real", "sequence"), "0/0").split("/")[0]
ds = defaults.get(("synthetic", "sequence"), "0/0").split("/")[0]
da = defaults.get(("all", "sequence"), "0/0")
P(f"      defaults : real {dr}/35 + synthetic {ds}/12 = {int(dr)+int(ds)}/47  "
  f"(reported ALL: {da})")
pr = params9.get(("real", "sequence"), "0/0").split("/")[0]
ps = params9.get(("synthetic", "sequence"), "0/0").split("/")[0]
pa = params9.get(("all", "sequence"), "0/0")
P(f"      params-9 : real {pr}/35 + synthetic {ps}/12 = {int(pr)+int(ps)}/47  "
  f"(reported ALL: {pa})")

(OUT / "reference_score_attribution.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'reference_score_attribution.txt'}")
