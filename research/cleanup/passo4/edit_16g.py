#!/usr/bin/env python
"""Passo 4, commit 16g — docstring-only edits in cyclophaser/determine_periods.py.

    <cyclophaser env python> -P research/cleanup/passo4/edit_16g.py

1. The unmatched bold in determine_periods' `x` parameter (the build warning).
2. rst section titles (a line underlined with dashes) inside the docstrings of
   process_vorticity, get_periods and determine_periods become bold paragraphs,
   content unchanged: a section title nests everything after it, the Args field
   list included, and Sphinx then does not group the fields into "Parameters".
3. The Portuguese quotation "adotada sem validação independente" → its English
   translation, said to be a translation of the record's wording (every
   occurrence; they are all in those three docstrings).
4. prominence / prominence_relative documented in determine_periods' Args, the
   defaults read from its signature.
Every replacement is asserted to match the stated number of times. Log:
passo4/edit_16g_log.json.
"""
import ast
import inspect
import json
import re
from pathlib import Path

from cyclophaser import determine_periods as DP_FN
import cyclophaser

ROOT = Path(__file__).resolve().parents[3]
assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
F = ROOT / "cyclophaser/determine_periods.py"
s = F.read_text()
log = []


def rep(old, new, n=1, why=""):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, new)
    log.append(dict(why=why, count=n, old=old, new=new))


# 1 ------------------------------------------------------------------------------
rep("**Must match the length of `series**`.", "**Must match the length of** `series`.", why="unmatched bold")

# 2 ------------------------------------------------------------------------------
tree = ast.parse(s)
spans = [(n.body[0].lineno, n.body[0].end_lineno) for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name in ("process_vorticity", "get_periods", "determine_periods")]
lines = s.split("\n")
titles = []
for a, b in spans:
    for i in range(a, b - 1):                       # 0-based i = title line, i+1 = underline
        t, u = lines[i], lines[i + 1]
        if t.strip() and re.fullmatch(r"\s*-{4,}\s*", u) and len(u.strip()) >= len(t.strip()) - 2:
            titles.append(i)
for i in titles:
    indent = re.match(r"\s*", lines[i]).group(0)
    old_t, old_u = lines[i], lines[i + 1]
    lines[i] = f"{indent}**{lines[i].strip()}**"
    lines[i + 1] = ""
    log.append(dict(why="section title -> bold paragraph", count=1, old=old_t + "\n" + old_u,
                    new=lines[i] + "\n" + lines[i + 1], line=i + 1))
s = "\n".join(lines)

# 3 ------------------------------------------------------------------------------
TR = "adopted without independent validation"
rep('is **"adotada sem\n      validação independente"** (item 30): no independent validation exists.',
    f'was **"{TR}"** (English\n      translation of the record\'s wording; item 30): no independent validation exists.',
    n=3, why="Portuguese quotation -> English translation")
rep("Default True since item 31 — **adotada sem validação independente** (item 30);",
    f"Default True since item 31 — **{TR}** (English translation of the record's wording; item 30);",
    n=2, why="Portuguese quotation -> English translation")
assert "adotada" not in s and "validação" not in s

# 4 ------------------------------------------------------------------------------
sig = inspect.signature(DP_FN).parameters
anchor = ('            ``incipient_method="plateau"``. See ``find_incipient_period``.\n'
          "        reclassify_index0 (bool, optional): Rule C2' — retype the extremum at\n")
# the anchor occurs in get_periods (which already documents prominence before reclassify_index0) only if
# prominence is absent there; restrict to determine_periods' docstring
dstart = s.index("def determine_periods(")
i = s.index(anchor, dstart)
block = ("            ``incipient_method=\"plateau\"``. See ``find_incipient_period``.\n"
         f"        prominence (float, optional): Absolute minimum prominence threshold for\n"
         f"            z-extrema filtering. Default {sig['prominence'].default!r}. See ``find_peaks_valleys``\n"
         f"            for the full description of prominence modes.\n"
         f"        prominence_relative (float, optional): Relative prominence threshold as a\n"
         f"            fraction of the most prominent interior z-extremum. Default\n"
         f"            {sig['prominence_relative'].default!r}. See ``find_peaks_valleys``.\n"
         "        reclassify_index0 (bool, optional): Rule C2' — retype the extremum at\n")
s = s[:i] + block + s[i + len(anchor):]
log.append(dict(why="prominence / prominence_relative documented (defaults from the signature)", count=1,
                old=anchor, new=block))

F.write_text(s)
(Path(__file__).with_name("edit_16g_log.json")).write_text(json.dumps(log, indent=1, ensure_ascii=False))
print(f"{len(log)} edits; section titles converted: {len(titles)}")
for e in log:
    if e["why"].startswith("section"):
        print("  ", e["line"], e["old"].splitlines()[0].strip())
