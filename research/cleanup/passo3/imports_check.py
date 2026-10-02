#!/usr/bin/env python
"""Passo 3, R5 — every kept .py under research/ and tools/ compiles and its local imports resolve.

    python research/cleanup/passo3/imports_check.py

Kept = tracked in the index now (after the removal), under research/ or tools/,
research/cleanup/ excluded. For each file: `compile()` of its source, then every
`import X` / `from X import ...` (top-level name X) whose X is a LOCAL module,
i.e. a .py named X.py that was tracked at the archive tag (before the removal).
A local import resolves if a kept .py named X.py exists now. Static (AST only):
nothing is imported or run. Writes imports_check.json; exit 1 on any failure.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TAG = "archive/research-diagnostics-pre-cleanup"


def main():
    now = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).split()
    before = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", TAG], cwd=ROOT, text=True).split()
    local_before = {Path(t).stem for t in before if t.endswith(".py")}
    kept_names = {Path(t).stem for t in now if t.endswith(".py")}
    kept = [t for t in now if t.endswith(".py") and t.startswith(("research/", "tools/"))
            and not t.startswith("research/cleanup/")]
    failures, n_imports = [], 0
    for f in kept:
        src = (ROOT / f).read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=f)
            compile(src, f, "exec")
        except SyntaxError as e:
            failures.append(dict(file=f, kind="does not compile", detail=str(e)))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module.split(".")[0]]
            else:
                continue
            for m in mods:
                if m in local_before:
                    n_imports += 1
                    if m not in kept_names:
                        failures.append(dict(file=f, line=node.lineno, kind="local import unresolved", module=m))
    out = dict(kept_py=len(kept), local_imports_checked=n_imports, failures=failures)
    (Path(__file__).with_name("imports_check.json")).write_text(json.dumps(out, indent=1))
    print(f"kept .py under research/ and tools/: {len(kept)}; local imports checked: {n_imports}; "
          f"failures: {len(failures)}")
    for x in failures:
        print("  ", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
