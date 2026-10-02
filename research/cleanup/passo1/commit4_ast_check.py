#!/usr/bin/env python
"""Passo 1 — commit 4 changes no code: for every .py it touches, the AST (comments
are not in it) has the same shape before and after, and only str constants
(docstrings, help text) differ. The suite was run at the C1 commit; this is what
licenses carrying that result to the commit after it.

    python research/cleanup/passo1/commit4_ast_check.py [BEFORE AFTER]
"""
import ast
import subprocess
import sys

before, after = (sys.argv[1:3] if len(sys.argv) > 2 else ("742e685", "052a876"))
files = [f for f in subprocess.check_output(["git", "diff", "--name-only", before, after], text=True).split()
         if f.endswith(".py")]
ok = True
for f in files:
    a = ast.parse(subprocess.check_output(["git", "show", f"{before}:{f}"], text=True))
    b = ast.parse(subprocess.check_output(["git", "show", f"{after}:{f}"], text=True))
    na, nb = list(ast.walk(a)), list(ast.walk(b))
    shape = [type(x).__name__ for x in na] == [type(x).__name__ for x in nb]
    nonstr = [(x.lineno, x.value, y.value) for x, y in zip(na, nb)
              if isinstance(x, ast.Constant) and isinstance(y, ast.Constant) and x.value != y.value
              and not (isinstance(x.value, str) and isinstance(y.value, str))]
    ok &= shape and not nonstr
    print(f"{f}: same AST shape={shape}; non-string constant changes={nonstr}")
print(f"{before}..{after}: {len(files)} .py file(s); code unchanged: {ok}")
sys.exit(0 if ok else 1)
