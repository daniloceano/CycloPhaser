#!/usr/bin/env python
"""Passo 4, commit 16h — docstring-only: the rst simple table in process_vorticity's
replace_endpoints_with_lowpass note was malformed (a cell wider than its column
border: 1 ERROR in the documentation build). The table is rebuilt with each
column as wide as its widest cell; the cells are unchanged. Log:
passo4/edit_16h_log.json.

    python research/cleanup/passo4/edit_16h.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
F = ROOT / "cyclophaser/determine_periods.py"
s = F.read_text()
lines = s.split("\n")
start = next(i for i, l in enumerate(lines) if 'configuration' in l and '"zero"' in l and '"reflect"' in l) - 1
end = start + 5                                   # border, header, border, row, row, border
block = lines[start:end + 1]
assert all(re.fullmatch(r"\s*=+(\s+=+)+\s*", block[i]) for i in (0, 2, 5)), block
indent = re.match(r"\s*", block[0]).group(0)
spans = [(m.start(), m.end()) for m in re.finditer(r"=+", block[0])]


def cells(row):
    """Split a row: the first column is everything up to the run of 2+ spaces that
    precedes the remaining columns (the first cell itself contains single spaces)."""
    parts = re.split(r"\s{2,}", row.strip())
    return parts


rows = [cells(block[i]) for i in (1, 3, 4)]
assert all(len(r) == len(spans) for r in rows), rows
w = [max(len(r[c]) for r in rows) for c in range(len(spans))]
border = indent + "  ".join("=" * x for x in w)
fmt = lambda r: indent + "  ".join(r[c].ljust(w[c]) for c in range(len(w))).rstrip()
new = [border, fmt(rows[0]), border, fmt(rows[1]), fmt(rows[2]), border]
old_text, new_text = "\n".join(block), "\n".join(new)
assert s.count(old_text) == 1
F.write_text(s.replace(old_text, new_text))
(Path(__file__).with_name("edit_16h_log.json")).write_text(json.dumps(
    dict(file="cyclophaser/determine_periods.py", line=start + 1, old=old_text, new=new_text), indent=1))
print(new_text)
