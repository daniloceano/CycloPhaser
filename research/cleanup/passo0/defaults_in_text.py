#!/usr/bin/env python
"""Passo 0, section (e) — where parameter DEFAULT VALUES are written as text.

    python research/cleanup/passo0/defaults_in_text.py

Read-only. Imports cyclophaser only to read `inspect.signature` (no series is
loaded, nothing is run). Writes research/cleanup/passo0/defaults_in_text.json
and .md, the input for Passo 4 (derive every written default from the code).

Scope (per the brief): README.md, docs/*.rst, tools/calibration_app/README.md,
tools/calibration_app/*.py (app text), CHANGELOG.md — plus cyclophaser/*.py,
whose docstrings are user documentation through autodoc (docs/api.rst).
docs/future_work.md is a historical register and is out of scope.

A line is reported when it names a parameter of the public functions AND
  (a) contains the word "default", or
  (b) spells an assignment `name=value` / `name: value` / "name" : value, or
  (c) is a markdown table row carrying the name in backticks.
In .py files only prose is scanned (via `tokenize`): comments, and string
literals that contain whitespace (docstrings, help/UI text). A dict key or a
call is code, not written text.
For docstring lines that say "Default is …" without the name, the parameter is
the nearest `name (type…)` header in the 12 preceding lines.
This is a HEURISTIC locator for Passo 4, not a verdict on each line: `code`
is the signature default, shown so a reader can compare, never auto-judged.
"""
import inspect
import io
import tokenize
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
OUT = ROOT / "research/cleanup/passo0"

import importlib  # noqa: E402

import cyclophaser  # noqa: E402

# `from cyclophaser import determine_periods` yields the FUNCTION (the package
# re-exports it under the module's name); import_module returns the module.
dp = importlib.import_module("cyclophaser.determine_periods")
lf = importlib.import_module("cyclophaser.lanczos_filter")

assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__

FUNCS = {
    "process_vorticity": dp.process_vorticity,
    "get_periods": dp.get_periods,
    "determine_periods": dp.determine_periods,
    "find_peaks_valleys": dp.find_peaks_valleys,
    "lanczos_filter": lf.lanczos_filter,
    "lanczos_bandpass_filter": lf.lanczos_bandpass_filter,
}
DEFAULTS = {}
for fname, fn in FUNCS.items():
    for k, p in inspect.signature(fn).parameters.items():
        if p.default is not inspect.Parameter.empty:
            DEFAULTS.setdefault(k, {})[fname] = repr(p.default)
NAMES = sorted(DEFAULTS, key=len, reverse=True)
NAME_RE = re.compile(r"(?<![\w])(" + "|".join(map(re.escape, NAMES)) + r")(?![\w])")
HDR_RE = re.compile(r"^\s*(\w+)\s*\((?:str|float|int|bool|Union|list|dict|optional|number)", re.I)

files = [f for f in subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
         if f == "README.md" or f == "CHANGELOG.md" or re.match(r"docs/[^/]+\.rst$", f)
         or f == "tools/calibration_app/README.md"
         or re.match(r"tools/calibration_app/[^/]+\.py$", f)
         or re.match(r"cyclophaser/[^/]+\.py$", f)]

rows = []
for f in files:
    src = (ROOT / f).read_text(encoding="utf-8")
    lines = src.splitlines()
    prose = None  # .py: line number -> the prose text on that line
    if f.endswith(".py"):
        prose = {}
        kinds = {tokenize.COMMENT, tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)}
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            # a comment, or a string that reads as a sentence (has whitespace);
            # a bare dict key like "use_filter" is code, not text
            if tok.type not in kinds or (tok.type != tokenize.COMMENT and not re.search(r"\s", tok.string)):
                continue
            for k, piece in enumerate(tok.string.split("\n")):
                prose[tok.start[0] + k] = prose.get(tok.start[0] + k, "") + " " + piece
    for i, full in enumerate(lines, 1):
        line = full if prose is None else prose.get(i, "")
        names = NAME_RE.findall(line)
        low = line.lower()
        has_default = "default" in low
        why = None
        if names and has_default:
            why = "names+default"
        elif names and re.search(r"(?<![\w])(" + "|".join(map(re.escape, names)) + r")[`\"']?\s*(=|:)\s*[^=\s]", line):
            why = "assignment"
        elif names and line.lstrip().startswith("|") and "`" in line:
            why = "table-row"
        elif not names and re.search(r"\bdefault(s)?\s+(is|:|=)", low):
            for j in range(i - 2, max(-1, i - 14), -1):
                m = HDR_RE.match(lines[j])
                if m and m.group(1) in DEFAULTS:
                    names, why = [m.group(1)], "default-line (header %d)" % (j + 1)
                    break
        if why is None:
            continue
        rows.append({"file": f, "line": i, "params": sorted(set(names)), "why": why,
                     "code": {n: DEFAULTS[n] for n in set(names)}, "text": full.strip()[:220]})

# Supplement: literal fallbacks in app CODE — `.get("<param>", <literal>)` —
# a default written by hand rather than read from the signature.
GET_RE = re.compile(r"\.get\(\s*[\"'](\w+)[\"']\s*,\s*([^()]+?)\s*\)")
fallbacks = []
for f in files:
    if not f.startswith("tools/calibration_app/"):
        continue
    for i, line in enumerate((ROOT / f).read_text(encoding="utf-8").splitlines(), 1):
        for name, lit in GET_RE.findall(line):
            if name in DEFAULTS:
                fallbacks.append({"file": f, "line": i, "param": name, "literal": lit,
                                  "code": DEFAULTS[name], "text": line.strip()[:200]})

(OUT / "defaults_in_text.json").write_text(json.dumps(
    {"signature_defaults": DEFAULTS, "rows": rows, "app_literal_fallbacks": fallbacks},
    indent=1, ensure_ascii=False))

md = ["# Passo 0 (e) — defaults written as text (generated by `defaults_in_text.py`)", "",
      "Heuristic locator for Passo 4; `code` = signature default(s) per function. "
      "Not a verdict per line.", "",
      f"{len(rows)} line(s) in {len({r['file'] for r in rows})} file(s).", "",
      "| file:line | param(s) | code default | text |", "|---|---|---|---|"]
for r in rows:
    code = "; ".join(f"{n}: " + ", ".join(f"{fn}={v}" for fn, v in r["code"][n].items())
                     for n in r["params"])
    txt = r["text"].replace("|", "\\|")
    md.append(f"| `{r['file']}:{r['line']}` | {', '.join(r['params'])} | {code} | {txt} |")
md += ["", "## Supplement — literal fallbacks in app code (`.get(\"param\", literal)`)", "",
       f"{len(fallbacks)} occurrence(s).", "",
       "| file:line | param | literal | code default |", "|---|---|---|---|"]
for r in fallbacks:
    code = ", ".join(f"{fn}={v}" for fn, v in r["code"].items())
    md.append(f"| `{r['file']}:{r['line']}` | {r['param']} | `{r['literal']}` | {code} |")
(OUT / "defaults_in_text.md").write_text("\n".join(md) + "\n")
by_file = {}
for r in rows:
    by_file[r["file"]] = by_file.get(r["file"], 0) + 1
print(len(rows), "rows;", by_file, "| app literal fallbacks:", len(fallbacks))
