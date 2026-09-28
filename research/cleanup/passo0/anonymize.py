#!/usr/bin/env python
"""Remove machine paths from this front's versioned outputs (idempotent).

    python research/cleanup/passo0/anonymize.py [files...]

Run with the interpreter of the dedicated `cyclophaser` conda env: its
`sys.prefix` IS the environment path to mask. Substitutions, in this order
(longest first, so the env path is not half-eaten by the home one):

    <conda env prefix>                 -> <env>
    <env prefix, relative to the repo> -> <env>   (pytest prints site-packages
                                                   paths relative to the cwd)
    <env prefix, home written as ~>    -> <env>   (already home-masked text)
    <repository root>                  -> <repo>
    <home directory>                   -> ~

With no arguments it rewrites every text output under research/cleanup/
(`*.txt`, `*.json`, `*.md`, `*.diff`); scripts are never touched. Prints and
writes anonymize_log.json (file -> count per substitution), so the masking is
declared rather than silent. A second run changes nothing.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLEANUP = ROOT / "research/cleanup"


def substitutions():
    env = os.path.realpath(sys.prefix)
    assert os.path.basename(env) == "cyclophaser", f"run with the cyclophaser env, got {env}"
    subs = [(env, "<env>"), (sys.prefix, "<env>"),
            (os.path.relpath(env, ROOT), "<env>"),
            ("~" + env[len(str(Path.home())):] if env.startswith(str(Path.home())) else env, "<env>"),
            (str(ROOT), "<repo>"), (os.path.realpath(ROOT), "<repo>"),
            (str(Path.home()), "~")]
    seen, out = set(), []
    for a, b in subs:
        if a not in seen:
            seen.add(a)
            out.append((a, b))
    return out


def main(argv):
    files = [Path(a).resolve() for a in argv] or sorted(
        p for p in CLEANUP.rglob("*") if p.is_file() and p.suffix in (".txt", ".json", ".md", ".diff")
        and p.name != "anonymize_log.json")
    subs = substitutions()
    log = {}
    for f in files:
        text = f.read_text(encoding="utf-8")
        counts = {}
        for a, b in subs:
            n = text.count(a)
            if n:
                text = text.replace(a, b)
                label = b + " <- " + ("env prefix" if b == "<env>" else "repo root" if b == "<repo>" else "home")
                counts[label] = counts.get(label, 0) + n
        if counts:
            f.write_text(text, encoding="utf-8")
            log[str(f.relative_to(ROOT))] = counts
    logp = Path(__file__).with_name("anonymize_log.json")
    old = json.loads(logp.read_text()) if logp.exists() else {}
    old.update(log)
    logp.write_text(json.dumps(old, indent=1, ensure_ascii=False, sort_keys=True))
    for k, v in log.items():
        print(k, v)
    print(f"{len(log)} file(s) rewritten")


if __name__ == "__main__":
    main(sys.argv[1:])
