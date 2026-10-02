#!/usr/bin/env python
"""Which test files reach streamlit without a pytest.importorskip("streamlit") guard
(read-only). The CI installs only the wheel + pytest + pyyaml: no streamlit.

    python research/cleanup/final/scan_streamlit_guards.py LABEL   # writes LABEL.json next to it

For every tracked tests/*.py, parsed with ast:
* a STREAMLIT IMPORT is an `import streamlit...` / `from streamlit... import`, or an
  import of a module of tools/calibration_app/ that itself imports streamlit at
  module level (directly or through another such module);
* it is GUARDED when a `pytest.importorskip("streamlit")` (or `importorskip`
  of the same) call comes before it in the same scope chain — at module level
  before it, or earlier in the enclosing function — or when the module calls
  pytest.importorskip("streamlit") at module level anywhere before the first
  streamlit import.
Unguarded imports are listed file:line with the enclosing function.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "tools/calibration_app"


def imported_modules(tree, top_level_only):
    out = []
    nodes = tree.body if top_level_only else ast.walk(tree)
    for n in nodes:
        if isinstance(n, ast.Import):
            out += [(a.name, n.lineno) for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            out.append((n.module, n.lineno))
    return out


# app modules that pull streamlit in at import time (fixed point)
app_tops = {p.stem: [m for m, _ in imported_modules(ast.parse(p.read_text()), True)] for p in APP.glob("*.py")}
pulls = set()
changed = True
while changed:
    changed = False
    for mod, imps in app_tops.items():
        if mod not in pulls and any(i.split(".")[0] == "streamlit" or i in pulls for i in imps):
            pulls.add(mod)
            changed = True


def is_st(name):
    return name.split(".")[0] == "streamlit" or name.split(".")[0] in pulls


def is_guard(node):
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
    return name == "importorskip" and node.args and isinstance(node.args[0], ast.Constant) \
        and str(node.args[0].value).split(".")[0] == "streamlit"


rows = []
files = [f for f in subprocess.check_output(["git", "ls-files", "tests"], cwd=ROOT, text=True).split()
         if Path(f).name.startswith("test_") and f.endswith(".py")]
for f in files:
    tree = ast.parse((ROOT / f).read_text())
    module_guard = min((n.lineno for n in ast.walk(tree) if is_guard(n)
                        and any(n in ast.walk(s) for s in tree.body if not isinstance(s, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)))),
                       default=None)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    unguarded, n_imports = [], 0
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Import, ast.ImportFrom)):
            continue
        names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module] if n.module and n.level == 0 else [])
        if not any(is_st(x) for x in names):
            continue
        n_imports += 1
        if module_guard is not None and module_guard < n.lineno:
            continue
        enclosing = [fn for fn in funcs if fn.lineno <= n.lineno <= fn.end_lineno]
        guarded = any(is_guard(c) and c.lineno < n.lineno for fn in enclosing for c in ast.walk(fn))
        if not guarded:
            unguarded.append(dict(where=f"{f}:{n.lineno}", imports=names,
                                  function=enclosing[-1].name if enclosing else "<module>"))
    if n_imports:
        rows.append(dict(file=f, streamlit_imports=n_imports, module_level_guard_line=module_guard,
                         unguarded=unguarded))
label = sys.argv[1]
out = dict(label=label, app_modules_pulling_streamlit=sorted(pulls), test_files_scanned=len(files),
           files_reaching_streamlit=len(rows), files_with_unguarded=[r["file"] for r in rows if r["unguarded"]],
           unguarded_imports=sum(len(r["unguarded"]) for r in rows), rows=rows)
(HERE / f"{label}.json").write_text(json.dumps(out, indent=1) + "\n")
print(f"{len(files)} test files; {len(rows)} reach streamlit; unguarded imports {out['unguarded_imports']} "
      f"in {out['files_with_unguarded']}")
for r in rows:
    for u in r["unguarded"]:
        print("  ", u)
