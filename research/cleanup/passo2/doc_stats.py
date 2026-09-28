#!/usr/bin/env python
"""Passo 2 — counts for the orchestration summary, from docs/findings.md (read-only).

    python research/cleanup/passo2/doc_stats.py

Per section S01–S12: list items that carry at least one citation (a finding),
split by subsection (Confirmed causes / Refuted hypotheses / Decisions / Open
/ other), plus table rows with a citation. Also: total lines, and the
cyclophaser/ diff over this step (`git diff 33dc4e1 HEAD -- cyclophaser/`).
Writes doc_stats.json next to it.
"""
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CITE = re.compile(r"`[^`\s]+?:\d+@[0-9a-f]{7,40}`")
doc = (ROOT / "docs/findings.md").read_text().splitlines()
sec, sub = None, None
count = defaultdict(lambda: defaultdict(int))
for l in doc:
    m = re.match(r"^## (S\d\d)\b", l)
    if m:
        sec, sub = m.group(1), "(section)"
        continue
    m = re.match(r"^### (.+)", l)
    if m:
        sub = m.group(1)
        continue
    if sec and CITE.search(l):
        kind = "table row" if l.startswith("|") else sub
        count[sec][kind] += 1
diff = subprocess.run(["git", "diff", "--stat", "33dc4e1", "HEAD", "--", "cyclophaser/"],
                      cwd=ROOT, capture_output=True, text=True).stdout.strip()
out = dict(total_lines=len(doc),
           per_section={s: dict(v, total=sum(v.values())) for s, v in sorted(count.items())},
           refuted_hypotheses=sum(v.get("Refuted hypotheses", 0) for v in count.values()),
           s11_open_items=count["S11"].get("(section)", 0),
           cyclophaser_diff_33dc4e1_HEAD=diff or "(empty)")
(Path(__file__).with_name("doc_stats.json")).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(out, indent=1, ensure_ascii=False))
