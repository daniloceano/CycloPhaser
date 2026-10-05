#!/usr/bin/env python
"""Final gate (a) — what touched cyclophaser/ on this branch since develop-v2.1.

    python research/cleanup/final/gate_a.py    # writes gate_a.json next to it; exit 1 on a failure

Expected: C1 (742e685) and, besides it, only docstring/comment commits. For each
commit other than C1:
  * re-measured here: the syntax tree WITHOUT docstrings of every cyclophaser/*.py
    is identical at the commit and at its parent (comments are not in the tree);
    the commit touches only .py files under cyclophaser/;
  * recorded at the time (passo4/): the docstring-free tree check of that commit
    (`identical: true`) and the default digest before == after, in one session.
And: the docstring-free tree of HEAD is identical to that of 742e685.
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P4 = HERE.parent / "passo4"
C1 = "742e685"
# docstring/comment commits -> (recorded tree check, recorded digest label); from passo4/PREVISOES.md
RECORDED = {"129b04d": ("ast_no_docstrings.json", "16b"), "c5e298b": ("ast_16d.json", "16d"),
            "00718d4": ("ast_16g.json", "16g"), "32651c8": ("ast_16h.json", "16h")}


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True)


def stripped(code):
    tree = ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) \
                and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def trees(ref):
    fs = [f for f in git("ls-tree", "-r", "--name-only", ref, "cyclophaser/").split() if f.endswith(".py")]
    return {f: stripped(git("show", f"{ref}:{f}")) for f in fs}


def same(a, b):
    ta, tb = trees(a), trees(b)
    diff = sorted(f for f in set(ta) | set(tb) if ta.get(f) != tb.get(f))
    return dict(files=len(set(ta) | set(tb)), differing=diff, identical=not diff)


def digest(label, mode):
    t = (P4 / f"digest_{label}_{mode}_raw.txt").read_text()
    return re.search(r"SHA256\s*=\s*([0-9a-f]{64})", t).group(1)


base = git("merge-base", "origin/develop-v2.1", "HEAD").strip()
commits = git("log", "--format=%h", "--abbrev=7", "origin/develop-v2.1..HEAD", "--", "cyclophaser/").split()
rows, ok = [], True
for c in commits:
    row = dict(commit=c, subject=git("log", "-1", "--format=%s", c).strip())
    if c == C1:
        row["role"] = "C1 — the behaviour change"
        rows.append(row)
        continue
    files = git("diff-tree", "--no-commit-id", "--name-only", "-r", c, "--", "cyclophaser/").split()
    row["files"] = files
    row["only_py"] = all(f.endswith(".py") for f in files)
    row["remeasured_parent_vs_commit"] = same(f"{c}^", c)
    rec = RECORDED.get(c)
    if rec:
        aj = json.loads((P4 / rec[0]).read_text())
        b, a = digest(rec[1], "before"), digest(rec[1], "after")
        row["recorded"] = dict(tree_check=f"passo4/{rec[0]}", tree_identical=aj["identical"],
                               digest=f"passo4/digest_{rec[1]}_{{before,after}}_raw.txt",
                               digest_before=b[:8], digest_after=a[:8], digest_equal=b == a)
    row["ok"] = bool(rec) and row["only_py"] and row["remeasured_parent_vs_commit"]["identical"] \
        and row["recorded"]["tree_identical"] and row["recorded"]["digest_equal"]
    ok &= row["ok"]
    rows.append(row)
head_vs_c1 = same(C1, "HEAD")
ok &= head_vs_c1["identical"] and C1 in commits and set(commits) - {C1} == set(RECORDED)
out = dict(head=git("rev-parse", "--short=7", "HEAD").strip(), merge_base=base[:7], commits=rows,
           commits_listed=commits, expected_others=sorted(RECORDED), head_vs_c1=head_vs_c1, ok=ok)
(HERE / "gate_a.json").write_text(json.dumps(out, indent=1) + "\n")
print(f"git log -- cyclophaser/ since develop-v2.1: {' '.join(commits)}")
for r in rows:
    if "role" in r:
        print(f"  {r['commit']}: {r['role']}")
    else:
        print(f"  {r['commit']}: tree w/o docstrings parent==commit {r['remeasured_parent_vs_commit']['identical']}; "
              f"recorded tree {r.get('recorded', {}).get('tree_identical')}, digest "
              f"{r.get('recorded', {}).get('digest_before')}→{r.get('recorded', {}).get('digest_after')}")
print(f"HEAD vs {C1}, tree w/o docstrings: identical {head_vs_c1['identical']} ({head_vs_c1['files']} files)")
print("gate (a):", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
