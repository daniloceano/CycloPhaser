#!/usr/bin/env python
"""Passo 4, 4b-1 — count, per page of passo4/rtd_map.md section 1, the numbered
"Stale" items and whether a "Repetition" / "Missing" paragraph is present
(1 each). Rewrites the table under "### Problems per page" in place.

    python research/cleanup/passo4/rtd_map_counts.py
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent / "rtd_map.md"
s = P.read_text()
sec1 = s[s.index("## 1. The pages today"):s.index("### Outside the toctree")]
rows = []
for block in re.split(r"^### ", sec1, flags=re.M)[1:]:
    page = block.splitlines()[0].strip()
    stale = block.split("*Stale", 1)[1].split("*Repetition.*")[0].split("*Missing.*")[0] if "*Stale" in block else ""
    n_stale = len(re.findall(r"^\d+\. ", stale, re.M))
    rows.append((page, n_stale, int("*Repetition.*" in block), int("*Missing.*" in block)))
table = "| page | stale | repetition | missing |\n|---|---|---|---|\n" + \
    "".join(f"| {p} | {a} | {b} | {c} |\n" for p, a, b, c in rows)
s = re.sub(r"(### Problems per page\n\n)\| page \|.*?\n\n", lambda m: m.group(1) + table + "\n", s, flags=re.S)
P.write_text(s)
print(table)
