#!/usr/bin/env python
"""Passo 3 — the removal list, generated from research/cleanup/MANIFEST.md (never typed).

    python research/cleanup/passo3/removal_list.py            # print the count (R1)
    python research/cleanup/passo3/removal_list.py --write    # also write passo3/removed_files.txt
    python research/cleanup/passo3/removal_list.py --apply    # write it and `git rm` exactly those files

The list is every file of the manifest's file tables (section "0.2 Manifesto de
arquivos", up to "0.2 (a)") whose destination is **remover** or **consolidar**.
A group row (a glob such as `docs/_images/item5/*.png`) is expanded with
`git ls-files`, same directory depth as the glob. Every listed path must be
tracked, or the script aborts. research/cleanup/ is never listed (the manifest
excludes it).
"""
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("removed_files.txt")


def removal_list() -> list[str]:
    text = (ROOT / "research/cleanup/MANIFEST.md").read_text()
    body = text[text.index("## 0.2 Manifesto de arquivos"):text.index("## 0.2 (a)")]
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).split()
    out = set()
    for line in body.splitlines():
        m = re.match(r"^\| `([^`]+)`.*? \| \*\*(consolidar|remover|manter)\*\* \|", line)
        if not m or m.group(2) == "manter":
            continue
        p = m.group(1)
        if "*" in p:
            hits = [t for t in tracked if fnmatch.fnmatch(t, p) and t.count("/") == p.count("/")]
            if not hits:
                sys.exit(f"ABORT: group {p} matches no tracked file")
            out |= set(hits)
        else:
            if p not in tracked:
                sys.exit(f"ABORT: {p} is not tracked")
            out.add(p)
    assert not any(p.startswith("research/cleanup/") for p in out)
    return sorted(out)


def main():
    files = removal_list()
    print(f"removal list: {len(files)} files")
    if "--write" in sys.argv or "--apply" in sys.argv:
        OUT.write_text("\n".join(files) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    if "--apply" in sys.argv:
        for i in range(0, len(files), 100):
            subprocess.run(["git", "rm", "-q", "--", *files[i:i + 100]], cwd=ROOT, check=True)
        print(f"git rm: {len(files)} files")


if __name__ == "__main__":
    main()
