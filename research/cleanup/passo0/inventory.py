#!/usr/bin/env python
"""Passo 0 — mechanical inventory of every tracked file (read-only).

    python research/cleanup/passo0/inventory.py

Writes research/cleanup/passo0/inventory.json. Nothing outside
research/cleanup/ is written, and no series is loaded: this script only runs
`git` and reads text.

Per tracked file (`git ls-files`, HEAD of chore/repo-cleanup):
  type        heuristic type from the path (see TYPE_RULES)
  last_commit hash + ISO date of the last commit touching the path
  refs        every `git grep -n -F` hit of the file's path, of its path
              relative to its parent directory ("frontD/census.txt"), and of
              its basename when that basename is unique among tracked files;
              the file itself is excluded

`.pypirc` is excluded from every content grep: it is a credentials file and
this inventory does not read it (flagged for Danilo in the manifest).

Section greps (same file, keys `grep_*`): params-1..14, params-15,
boundary_padding, absolute paths. Each hit is `file:line: text`.
"""
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
OUT = ROOT / "research/cleanup/passo0/inventory.json"
SELF_DIR = "research/cleanup/"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


TYPE_RULES = [  # first match wins
    (r"^cyclophaser/example_data/", "dados"),
    (r"^cyclophaser/", "pacote"),
    (r"^tests/(calibration_data|synthetic/data)/.*\.csv$", "dados"),
    (r"^tests/.*/gen_[^/]*\.py$", "script de diagnóstico"),
    (r"^tests/baselines/.*\.csv$", "dados"),
    (r"^tests/(expected_.*|test)\.csv$", "dados"),
    (r"^tests/", "teste"),
    (r"^tools/calibration_app/(README\.md)$", "doc de usuário"),
    (r"^tools/calibration_app/", "app"),
    (r"^docs/future_work\.md$", "registro/relatório"),
    (r"^docs/_images/", "doc de usuário"),
    (r"^docs/", "doc de usuário"),
    (r"^(README\.md|CHANGELOG\.md|LICENSE)$", "doc de usuário"),
    (r"^CLAUDE\.md$", "config"),
    (r"^research/labels/configs/", "config"),
    (r"^research/labels/(manual_labels|split)\.yaml$", "dados"),
    (r"^research/labels/swell_item30/.*\.yaml$", "dados"),
    (r"^research/snapshots/.*\.(json)$|SHA256SUMS$", "dados"),
    (r"^[^/]+$", "config"),  # remaining root files: setup.py, requirements.txt, runtime.txt, ...
    (r"^research/labels/[^/]+\.py$|^research/snapshots/[^/]+\.py$", "script de pesquisa (vivo)"),
    (r"\.(md)$", "registro/relatório"),
    (r"\.py$", "script de diagnóstico"),
    (r"\.(txt|json|csv|log|png)$", "saída gerada"),
    (r".*", "config"),
]


def ftype(p):
    for pat, t in TYPE_RULES:
        if re.search(pat, p):
            return t
    return "?"


def mask(text):
    """Keep absolute paths out of this front's own versioned outputs."""
    return text.replace(str(ROOT), "<repo>").replace(str(Path.home()), "~")


def grep_fixed(s):
    out = git("grep", "-n", "-F", "-e", s, "HEAD", "--", ".", f":(exclude){SELF_DIR}", ":(exclude).pypirc")
    hits = []
    for line in out.splitlines():
        # HEAD:path:line:text
        _, rest = line.split(":", 1)
        path, ln, text = rest.split(":", 2)
        hits.append((path, int(ln), text.strip()[:200]))
    return hits


def grep_regex(pattern, pathspecs=(".",)):
    out = git("grep", "-n", "-I", "-P", "-e", pattern, "HEAD", "--", *pathspecs, f":(exclude){SELF_DIR}", ":(exclude).pypirc")
    hits = []
    for line in out.splitlines():
        _, rest = line.split(":", 1)
        path, ln, text = rest.split(":", 2)
        hits.append({"file": path, "line": int(ln), "text": mask(text.strip())[:240]})
    return hits


def main():
    head = git("rev-parse", "HEAD").strip()
    files = [f for f in git("ls-files").splitlines() if not f.startswith(SELF_DIR)]
    base_count = Counter(Path(f).name for f in files)

    rows = []
    for f in files:
        h, d = (git("log", "-1", "--format=%h %cs", "--", f).strip().split() + ["?", "?"])[:2]
        needles = {f}
        parts = f.split("/")
        if len(parts) >= 2:
            needles.add("/".join(parts[-2:]))
        name = parts[-1]
        if base_count[name] == 1 and len(name) > 6:
            needles.add(name)
        refs = set()
        for n in needles:
            for path, ln, _ in grep_fixed(n):
                if path != f:
                    refs.add((path, ln))
        rows.append({
            "path": f, "type": ftype(f), "last_commit": h, "last_date": d,
            "refs": sorted(f"{p}:{l}" for p, l in refs),
        })

    data = {
        "head": head,
        "n_tracked_total": len(files),  # excludes research/cleanup/ so a rerun after this commit agrees
        "n_tracked_excluding_cleanup": len(files),
        "files": rows,
        # params-1..14 as config names/files (params-15 and params-track excluded by the lookahead)
        "grep_params_1_14": grep_regex(r"params[-_]?(1[0-4]|[1-9])(?![0-9])"),
        "grep_params_15": grep_regex(r"params[-_]?15(?![0-9])"),
        "grep_boundary_padding": grep_regex(
            r"boundary_padding",
            ("cyclophaser", "tools", "docs", "README.md", "CHANGELOG.md", "*.yaml", "*.yml")),
        "grep_abs_paths": grep_regex(r"(/Users/|/home/|[A-Za-z]:\\\\)"),
    }
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"HEAD {head[:7]}  files {len(files)}  "
          f"p1-14 {len(data['grep_params_1_14'])}  p15 {len(data['grep_params_15'])}  "
          f"bp {len(data['grep_boundary_padding'])}  abs {len(data['grep_abs_paths'])}")


if __name__ == "__main__":
    main()
