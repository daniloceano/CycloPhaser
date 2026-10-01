#!/usr/bin/env python
"""Passo 4, commit 16d — every sentence in the docstrings and comments of
cyclophaser/*.py that states a default or an opt-in status (read-only).

    python research/cleanup/passo4/sweep_16d.py LABEL [REV]   # writes LABEL.json / LABEL.md next to it

REV (optional): read the files at that git revision instead of the working tree.

Text sources: docstrings (module, class, function; ast) and `#` comments
(tokenize). A hit is a LINE of such text matching, case-insensitively, any of:
  default | opt-in | opt in | off by default | on by default | disabled by
  default | enabled by default | unchanged behaviour/behavior | byte-identical |
  backward compat | prior behaviour/behavior | previous behaviour/behavior
Each hit carries its enclosing function (innermost def whose line range holds
it; "<module>" otherwise), so the reviewer can check it against the right
reference: the public signature (get_periods / determine_periods /
process_vorticity / ...) or the stage function's own fallback.
"""
import ast
import io
import json
import re
import subprocess
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAT = re.compile(r"default|opt-in|opt in|off by default|on by default|unchanged behavio|byte-identical|"
                 r"backward[- ]compat|prior behavio|previous behavio", re.I)


def files(rev):
    if rev:
        names = subprocess.check_output(["git", "ls-tree", "--name-only", rev, "cyclophaser/"], cwd=ROOT,
                                        text=True).split()
        return {n: subprocess.check_output(["git", "show", f"{rev}:{n}"], cwd=ROOT, text=True)
                for n in names if n.endswith(".py")}
    return {str(p.relative_to(ROOT)): p.read_text() for p in sorted((ROOT / "cyclophaser").glob("*.py"))}


def scan(name, src):
    tree = ast.parse(src)
    funcs = [(n.lineno, n.end_lineno, n.name) for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]

    def owner(line):
        inside = [f for f in funcs if f[0] <= line <= f[1]]
        return min(inside, key=lambda f: f[1] - f[0])[2] if inside else "<module>"

    lines = src.splitlines()
    text_lines = {}                       # line -> kind
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
            b = n.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                for ln in range(b.lineno, b.end_lineno + 1):
                    text_lines[ln] = "docstring"
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            text_lines[tok.start[0]] = "comment"
    hits = []
    for ln, kind in sorted(text_lines.items()):
        t = lines[ln - 1]
        seg = t[t.index("#"):] if kind == "comment" and "#" in t else t
        if PAT.search(seg):
            hits.append(dict(file=name, line=ln, kind=kind, function=owner(ln), text=seg.strip()))
    return hits


def main():
    label = sys.argv[1]
    rev = sys.argv[2] if len(sys.argv) > 2 else None
    hits = [h for n, s in files(rev).items() for h in scan(n, s)]
    out = dict(rev=rev or "working tree", hits=len(hits), by_file={}, rows=hits)
    for h in hits:
        out["by_file"][h["file"]] = out["by_file"].get(h["file"], 0) + 1
    (HERE / f"{label}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    md = [f"# {label} — default/opt-in sentences in cyclophaser/ ({out['rev']})\n",
          f"{len(hits)} lines; by file {out['by_file']}\n", "| file:line | kind | function | text |", "|---|---|---|---|"]
    md += [f"| `{h['file']}:{h['line']}` | {h['kind']} | `{h['function']}` | {h['text'].replace('|', '\\|')} |" for h in hits]
    (HERE / f"{label}.md").write_text("\n".join(md) + "\n")
    print(f"{len(hits)} lines; {out['by_file']}")


if __name__ == "__main__":
    main()
