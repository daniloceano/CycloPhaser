"""I1 gate (b), mechanical half: what disappeared and what appeared in the app.

    python research/app_redesign/i1/check_inventory.py > research/app_redesign/i1/inventory_check.txt

For every Python file of tools/calibration_app/ (origin/develop vs the WORKING
TREE), lists by AST:
  * top-level names — functions, classes, module-level assignments;
  * widget keys — every literal `key="..."` (f-strings by their literal prefix);
  * the string options of the display-mode list `_VIEW_MODES`.
Anything gone from one file must reappear elsewhere (moved) or be one of the
retirements Danilo approved; INVENTARIO.md accounts for every line printed under
"gone". Read-only: it never writes anything but stdout.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP_DIR = "tools/calibration_app"
BASE = "origin/develop"


def files_at_base() -> dict[str, str]:
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", BASE, APP_DIR],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return {n: subprocess.run(["git", "show", f"{BASE}:{n}"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout
            for n in names if n.endswith(".py")}


def files_now() -> dict[str, str]:
    return {str(p.relative_to(ROOT)): p.read_text()
            for p in sorted((ROOT / APP_DIR).rglob("*.py"))
            if "__pycache__" not in p.parts and not p.name.startswith("_test_")}


def scan(src: str) -> tuple[set[str], set[str], list]:
    tree = ast.parse(src)
    top = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            top.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    top.add(t.id)
    keys, view_modes = set(), []
    for n in ast.walk(tree):
        if isinstance(n, ast.keyword) and n.arg == "key":
            v = n.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                keys.add(v.value)
            elif isinstance(v, ast.JoinedStr) and v.values and isinstance(
                    v.values[0], ast.Constant):
                keys.add(v.values[0].value + "…")
        if (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_VIEW_MODES"
                                              for t in n.targets)):
            view_modes = [e.value for e in n.value.elts]
    return top, keys, view_modes


def main() -> None:
    base, now = files_at_base(), files_now()
    all_base = {f: scan(s) for f, s in base.items()}
    all_now = {f: scan(s) for f, s in now.items()}
    names_now = {nm for t, _k, _v in all_now.values() for nm in t}
    keys_now = {k for _t, k, _v in all_now.values() for k in k}
    print(f"base {BASE} = {subprocess.run(['git', 'rev-parse', BASE], cwd=ROOT, capture_output=True, text=True).stdout.strip()}; now = working tree")
    print(f"files only now: {sorted(set(now) - set(base))}")
    print(f"files only at base: {sorted(set(base) - set(now))}")
    for f in sorted(set(base) | set(now)):
        tb, kb, vb = all_base.get(f, (set(), set(), []))
        tn, kn, vn = all_now.get(f, (set(), set(), []))
        print(f"\n== {f}")
        gone = sorted(tb - tn)
        print("  top-level names gone:", [(g, "moved" if g.lstrip("_") in
                                           {x.lstrip("_") for x in names_now} else "GONE")
                                          for g in gone])
        print("  top-level names new: ", sorted(tn - tb))
        print("  widget keys gone:", [(k, "moved" if k in keys_now else "GONE")
                                      for k in sorted(kb - kn)])
        print("  widget keys new: ", sorted(kn - kb))
        if vb or vn:
            print("  _VIEW_MODES:", vb, "->", vn)


if __name__ == "__main__":
    main()
