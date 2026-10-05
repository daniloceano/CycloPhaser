#!/usr/bin/env python
"""Passo 4 — mask machine paths in this step's outputs; log in passo4/mask_log.json.

    <cyclophaser env python> research/cleanup/passo4/mask.py FILE [FILE ...] [--as LABEL=PATH ...]

Same substitutions as passo0/anonymize.py (imported, not copied): conda env ->
<env>, repository root -> <repo>, home -> ~; plus any extra `--as LABEL=PATH`
pair (e.g. a throw-away worktree path -> <worktree:pre>), and the system temp
dir -> <tmp>. Idempotent. Kept in
passo4/ so that this step writes nothing outside its own folder.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "passo0"))
from anonymize import ROOT, substitutions  # noqa: E402


def main(argv):
    extra, files = [], []
    it = iter(argv)
    for a in it:
        if a == "--as":
            label, path = next(it).split("=", 1)
            extra.append((path, label))
        else:
            files.append(Path(a).resolve())
    tmp = tempfile.gettempdir()
    subs = extra + [(os.path.realpath(tmp), "<tmp>"), (tmp, "<tmp>")] + substitutions()
    logp = HERE / "mask_log.json"
    log = json.loads(logp.read_text()) if logp.exists() else {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        counts = {}
        for a, b in subs:
            n = text.count(a)
            if n:
                text = text.replace(a, b)
                counts[b] = counts.get(b, 0) + n
        f.write_text(text, encoding="utf-8")
        key = str(f.relative_to(ROOT))
        if counts:
            prev = log.get(key, {})
            for k, v in counts.items():
                prev[k] = prev.get(k, 0) + v
            log[key] = prev
    logp.write_text(json.dumps(log, indent=1, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
