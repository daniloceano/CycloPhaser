#!/usr/bin/env python
"""Passo 2, Q4 — every number cited in docs/findings.md is on the line it cites.

    python research/cleanup/passo2/verify_citations.py [DOC]

Independent of make_findings.py (which enforces the same rule while rendering):
this script re-reads the RENDERED document and every cited line with
`git show <commit>:<path>`, and implements the rule of passo2/PREVISOES.md (Q4)
on its own, token by token, deciding each number's status from its context.

For each line of the document that is a list item or a table row:
* every citation `path:N@commit` must resolve: the file exists at that commit
  and has a line N;
* every numeric token of the line, outside the citations and outside the
  exclusions of PREVISOES.md (labels S01…, item/stage/part/step/§ N, E01…,
  P1/Q1/C1…, 20(b)-style item refs, params-N names, dates, hashes, versions,
  path-like code spans, numbers glued to an identifier), must appear as a
  numeric token on at least one of the lines that line cites;
* a line with such a number and no citation is a failure too.

Writes verify_citations.json next to it and exits non-zero on any failure.

Weak citations (listed, never a failure): a citation whose numbers checked
against it — the line's own numbers that occur on that cited line — are all
integers below 10. Such a match says little, since small integers occur on
many lines. Written to weak_citations.txt: findings.md section, findings.md
line, cited source, numbers checked. Citations against which no number was
checked (text support only) are not listed.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/findings.md"
CITE = re.compile(r"`([^`\s]+?):(\d+)@([0-9a-f]{7,40})`")
NUM = re.compile(r"\d+(?:\.\d+)?")
LABEL_BEFORE = re.compile(
    r"(?:\b(?:items?|stages?|parts?|steps?|fronts?|sections?)\s+|\b(?:pre-)?(?:item|stage)-|§\s*|\bparams-)$",
    re.I)
_files: dict = {}


def git_lines(commit: str, path: str):
    key = (commit, path)
    if key not in _files:
        r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, text=True)
        _files[key] = r.stdout.splitlines() if r.returncode == 0 else None
    return _files[key]


def masked_spans(text: str) -> list[tuple[int, int]]:
    """Character spans whose digits are not numbers in the sense of Q4."""
    spans = []
    for m in re.finditer(r"`[^`]*`", text):                      # path-like code spans
        body = m.group(0)
        if "/" in body or re.search(r"\.(py|md|ya?ml|csv|txt|json)\b", body):
            spans.append(m.span())
    for rx in (r"\b\d{4}-\d{2}-\d{2}\b",                         # dates
               r"\bv?\d+\.\d+\.\d+\b",                          # versions
               r"\b[0-9a-f]*[a-f][0-9a-f]*\b",                  # hex words (hashes)
               r"\b\d+[a-z]?(?:\([a-z]{1,4}\))+",               # 20(b), 20(e)(i)
               r"\b(?:S\d{2}|E\d{2}|[PQRVGMTDC]\d{1,2}′?)"):     # labels
        spans += [m.span() for m in re.finditer(rx, text)]
    return spans


def numbers(text: str, strict: bool) -> list[str]:
    """Numeric tokens: not glued to a letter, underscore, digit or decimal point.

    strict=True also drops the Q4 exclusions (used on the document's own lines);
    strict=False is used on the cited source lines, where any number counts.
    """
    spans = masked_spans(text) if strict else []
    out = []
    for m in NUM.finditer(text):
        a, b = m.span()
        before, after = text[a - 1:a], text[b:b + 1]
        if before and (before.isalnum() or before in "_."):
            continue
        if after and (after.isalnum() or after == "_" or (after == "." and text[b + 1:b + 2].isdigit())):
            continue
        if strict:
            if any(s <= a and b <= e for s, e in spans):
                continue
            if LABEL_BEFORE.search(text[:a]):
                continue
        out.append(m.group(0))
    return out


def main():
    lines = DOC.read_text().splitlines()
    failures, checked_numbers, checked_lines, checked_cites = [], 0, 0, 0
    weak, section = [], None
    for n, line in enumerate(lines, 1):
        m = re.match(r"^## (S\d\d)\b", line)
        if m:
            section = m.group(1)
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|---") or not (s.startswith("- ") or s.startswith("|")):
            continue
        cites = CITE.findall(line)
        source_numbers, per_cite = set(), []
        for path, ln, commit in cites:
            checked_cites += 1
            src = git_lines(commit, path)
            if src is None:
                failures.append(dict(line=n, kind="unresolved file", cite=f"{path}@{commit}"))
                continue
            if int(ln) < 1 or int(ln) > len(src):
                failures.append(dict(line=n, kind="line out of range", cite=f"{path}:{ln}@{commit}"))
                continue
            nums = set(numbers(src[int(ln) - 1], strict=False))
            source_numbers |= nums
            per_cite.append((f"{path}:{ln}@{commit}", nums))
        own = numbers(CITE.sub(" ", line), strict=True)
        if not own:
            continue
        checked_lines += 1
        checked_numbers += len(own)
        if not cites:
            failures.append(dict(line=n, kind="numbers without citation", numbers=own, text=line[:160]))
            continue
        for cite, nums in per_cite:
            conferred = sorted({x for x in own if x in nums}, key=float)
            if conferred and all(re.fullmatch(r"\d+", x) and int(x) < 10 for x in conferred):
                weak.append((section or "-", n, cite, conferred))
        missing = [x for x in own if x not in source_numbers]
        if missing:
            failures.append(dict(line=n, kind="number not on cited lines", numbers=missing, text=line[:160]))
    out = dict(doc=str(DOC.relative_to(ROOT)), lines_with_numbers=checked_lines,
               numbers_checked=checked_numbers, citations_resolved=checked_cites - sum(
                   1 for f in failures if f["kind"] in ("unresolved file", "line out of range")),
               citations_total=checked_cites, failures=failures)
    out["weak_citations"] = len(weak)
    (Path(__file__).with_name("verify_citations.json")).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    wl = ["# Weak citations: every number checked against the citation is an integer below 10 (listed, not a failure).",
          f"# document: {out['doc']}; generated by verify_citations.py",
          "section\tfindings.md line\tcited source\tnumbers checked"]
    wl += [f"{sec}\t{ln}\t{cite}\t{', '.join(nums)}" for sec, ln, cite, nums in weak]
    wl.append(f"# total: {len(weak)}")
    (Path(__file__).with_name("weak_citations.txt")).write_text("\n".join(wl) + "\n")
    print(f"lines with numbers: {checked_lines}; numbers checked: {checked_numbers}; "
          f"citations: {out['citations_resolved']}/{checked_cites} resolved; failures: {len(failures)}; "
          f"weak citations: {len(weak)}")
    for f in failures:
        print("  ", f)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
