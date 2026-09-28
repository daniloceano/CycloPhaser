#!/usr/bin/env python
"""Passo 2, Q1–Q3 — coverage of docs/findings.md against the manifest.

    python research/cleanup/passo2/coverage.py

Definitions are those of passo2/PREVISOES.md.

Q1  every "consolidar" file of research/cleanup/MANIFEST.md appears in the S10
    table with a destination section that exists in the document, AND is cited
    as a source (`path:N@commit`) somewhere outside the S10 table.
Q2  S02 carries one table row per row of geometric_vs_plateau.csv (at 06d8550)
    and cites both the CSV and gen_geometric_vs_plateau.py.
Q3  in the S10 table, no destination cell contains the path of a file whose
    manifest destination is "consolidar" or "remover" (group rows such as
    `docs/_images/item5/*.png` are expanded with git ls-files at 06d8550).

Reads only the working tree's docs/findings.md and MANIFEST.md, plus git.
Writes coverage.json next to it.
"""
from __future__ import annotations

import csv
import fnmatch
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = "06d8550"
CITE = re.compile(r"`([^`\s]+?):(\d+)@([0-9a-f]{7,40})`")


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True)


def manifest_dest():
    """{path_or_glob: 'consolidar'|'remover'} from the 0.2 tables of MANIFEST.md."""
    out = {}
    for l in (ROOT / "research/cleanup/MANIFEST.md").read_text().splitlines():
        m = re.match(r"^\| `([^`]+)`.*? \| \*\*(consolidar|remover|manter)\*\* \|", l)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def sections(doc: str) -> dict[str, str]:
    parts = re.split(r"^## (S\d\d)\b.*$", doc, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def main():
    doc = (ROOT / "docs/findings.md").read_text()
    secs = sections(doc)
    dest = manifest_dest()
    consolidar = sorted(p for p, d in dest.items() if d == "consolidar")
    leaving_patterns = [p for p, d in dest.items() if d in ("consolidar", "remover")]
    tracked = git("ls-tree", "-r", "--name-only", BASE).split()
    leaving = set()
    for p in leaving_patterns:
        leaving |= {t for t in tracked if fnmatch.fnmatch(t, p)} if "*" in p else {p}

    s10 = secs.get("S10", "")
    table = [l for l in s10.splitlines() if l.startswith("| `")]
    rows = {}
    for l in table:
        cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
        rows[cells[0].strip("`")] = cells
    outside_s10_table = "\n".join(l for l in doc.splitlines() if l not in set(table))
    cited_outside = {m.group(1) for m in CITE.finditer(outside_s10_table)}

    q1 = []
    for p in consolidar:
        r = rows.get(p)
        dest_secs = re.findall(r"§(S\d\d)", r[3]) if r else []
        ok_table = bool(r) and bool(dest_secs) and all(s in secs for s in dest_secs)
        ok_cited = p in cited_outside
        q1.append(dict(path=p, in_s10=bool(r), destination=r[3] if r else None,
                       section_exists=ok_table, cited_outside_s10_table=ok_cited, ok=ok_table and ok_cited))

    csv_lines = git("show", f"{BASE}:research/incipient_plateau/geometric_vs_plateau.csv").splitlines()
    csv_rows = list(csv.DictReader(io.StringIO("\n".join(csv_lines))))
    s02 = secs.get("S02", "")
    row_hits = [r["name"] for r in csv_rows
                if re.search(rf"^\| {r['set']} \| `{re.escape(r['name'])}` \| {r['geo']} \| {r['plateau']} \|", s02, re.M)]
    q2 = dict(csv_rows=len(csv_rows), table_rows_found=len(row_hits),
              cites_csv="research/incipient_plateau/geometric_vs_plateau.csv:" in s02,
              cites_generator="research/incipient_plateau/gen_geometric_vs_plateau.py:" in s02)
    q2["ok"] = q2["csv_rows"] == q2["table_rows_found"] and q2["cites_csv"] and q2["cites_generator"]

    q3 = []
    for p, cells in rows.items():
        bad = sorted(x for x in re.findall(r"`([^`\s]+?)(?::\d+@[0-9a-f]+)?`", cells[3]) if x in leaving)
        if bad:
            q3.append(dict(row=p, destination=cells[3], leaving=bad))
    kinds = {"findings.md section": sum(1 for c in rows.values() if "§S" in c[3]),
             "future_work.md line": sum(1 for c in rows.values() if "docs/future_work.md:" in c[3])}

    out = dict(
        Q1=dict(n_consolidar=len(consolidar), ok=sum(x["ok"] for x in q1),
                without_destination=[x["path"] for x in q1 if not x["ok"]], detail=q1),
        Q2=q2,
        Q3=dict(s10_rows=len(rows), destination_kinds=kinds, rows_pointing_to_leaving_file=len(q3), detail=q3),
        doc_lines=len(doc.splitlines()),
    )
    (Path(__file__).with_name("coverage.json")).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"Q1: {out['Q1']['ok']}/{len(consolidar)} consolidar files mapped; without destination: "
          f"{out['Q1']['without_destination'] or 'none'}")
    print(f"Q2: CSV rows {q2['csv_rows']}, table rows in S02 {q2['table_rows_found']}, "
          f"cites CSV {q2['cites_csv']}, cites generator {q2['cites_generator']}")
    print(f"Q3: S10 rows {len(rows)}; destinations {kinds}; rows pointing to a leaving file: {len(q3)}")


if __name__ == "__main__":
    main()
