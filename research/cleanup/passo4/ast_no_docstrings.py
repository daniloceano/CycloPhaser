#!/usr/bin/env python
"""Passo 4, commit 16b (i) — the syntax tree WITHOUT docstrings is identical before and after.

    python research/cleanup/passo4/ast_no_docstrings.py [BEFORE] [AFTER]

BEFORE is a commit (default b9991c4); AFTER is a commit or WORKTREE (default).
For every .py under cyclophaser/ at either end: parse, drop the docstring
(first statement that is a string constant) of the module and of every
function/class, and compare `ast.dump` (no line numbers). Comments are not in
the AST. Writes ast_no_docstrings.json next to it; exit 1 on any difference.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
before = sys.argv[1] if len(sys.argv) > 1 else "b9991c4"
after = sys.argv[2] if len(sys.argv) > 2 else "WORKTREE"


def src(ref, path):
    if ref == "WORKTREE":
        return (ROOT / path).read_text()
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True)


def files(ref):
    if ref == "WORKTREE":
        return sorted(str(p.relative_to(ROOT)) for p in (ROOT / "cyclophaser").glob("*.py"))
    return sorted(f for f in subprocess.check_output(["git", "ls-tree", "-r", "--name-only", ref, "cyclophaser/"],
                                                     cwd=ROOT, text=True).split() if f.endswith(".py"))


def stripped(code):
    tree = ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \
                and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


fb, fa = files(before), files(after)
rows = []
for f in sorted(set(fb) | set(fa)):
    same = f in fb and f in fa and stripped(src(before, f)) == stripped(src(after, f))
    text_same = f in fb and f in fa and src(before, f) == src(after, f)
    rows.append(dict(file=f, ast_without_docstrings_identical=same, source_identical=text_same))
ok = all(r["ast_without_docstrings_identical"] for r in rows)
out = dict(before=before, after=after, files=len(rows), identical=ok, rows=rows)
Path(__file__).with_name("ast_no_docstrings.json").write_text(json.dumps(out, indent=1))
for r in rows:
    print(f"{r['file']}: AST w/o docstrings identical={r['ast_without_docstrings_identical']}, "
          f"source identical={r['source_identical']}")
print(f"{before} → {after}: {len(rows)} files; identical without docstrings: {ok}")
sys.exit(0 if ok else 1)
