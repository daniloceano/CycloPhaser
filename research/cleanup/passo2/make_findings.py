#!/usr/bin/env python
"""Passo 2 — render docs/findings.md from research/cleanup/passo2/findings_src.md.

    <cyclophaser env python> -P research/cleanup/passo2/make_findings.py

Template syntax (path shorthands FW, CL, D/, IP/, IN/, P1/ — see ALIASES)
---------------------------------------------------------------------
{{path|needle}}        a citation of the one line of `path` at 06d8550 that
                       contains `needle`; rendered as `path:LINE@06d8550`.
{{path@REF|needle}}    the same, at commit REF (a branch commit or a commit of
                       this branch).
{{!csv_table}}         S02: research/incipient_plateau/geometric_vs_plateau.csv
                       at 06d8550, one table row per CSV row, each row citing
                       its own CSV line.
{{!params_track_diff}} S08: params-track against the package signature
                       defaults, regenerated here from the working tree (the
                       same comparison as passo1/params_track_vs_defaults.py).
{{!traceability}}      S10: every file that leaves (manifest destination
                       "consolidar" or "remover") and carries a finding, with
                       its final destination.

Build-time checks (the render aborts on any failure):
* a needle must occur on exactly one line of the file at REF;
* the Q4 rule of passo2/PREVISOES.md: every numeric token of a rendered line
  (list item or table row) must occur as a numeric token on one of the lines
  that line cites, and a line with numeric tokens must cite something. This is
  one implementation of the rule; passo2/verify_citations.py is a second,
  independent one, run on the rendered file.

Writes docs/findings.md and passo2/traceability.json (read by the manifest).
"""
from __future__ import annotations

import csv
import importlib
import inspect
import io
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = "06d8550"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/cleanup/passo0"))
import judgements as J  # noqa: E402

ERRORS: list[str] = []
# Shorthands usable in the template only; the rendered document always carries full paths.
ALIASES = {"FW": "docs/future_work.md", "CL": "CHANGELOG.md", "D": "research/labels/diagnostics",
           "IP": "research/incipient_plateau", "IN": "research/inert_params", "P1": "research/cleanup/passo1"}
_cache: dict = {}


def show(ref: str, path: str) -> list[str]:
    key = (ref, path)
    if key not in _cache:
        r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            ERRORS.append(f"cannot read {path}@{ref}")
            _cache[key] = []
        else:
            _cache[key] = r.stdout.splitlines()
    return _cache[key]


def resolve(path: str, ref: str, needle: str) -> tuple[str, str]:
    lines = show(ref, path)
    hits = [i for i, l in enumerate(lines, 1) if needle in l]
    if len(hits) != 1:
        ERRORS.append(f"needle {'absent' if not hits else 'ambiguous (%d)' % len(hits)}: {path}@{ref} :: {needle!r}")
        return f"`{path}:?@{ref}`", ""
    return f"`{path}:{hits[0]}@{ref}`", lines[hits[0] - 1]


# ---------------------------------------------------------------- Q4 rule (A)
CITE_RE = re.compile(r"`([^`\s]+):(\d+)@([0-9a-f]{7,40})`")
TOKEN = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w]|\.\d)")
EXCLUDE = [
    re.compile(r"`[^`]*(/|\.py|\.md|\.ya?ml|\.csv|\.txt|\.json)[^`]*`"),   # paths / code refs
    re.compile(r"\b[0-9a-f]*[a-f][0-9a-f]*\b(?=…|`|\b)") ,                 # hex hashes (with a letter)
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),                                  # dates
    re.compile(r"\bv?\d+\.\d+\.\d+\b"),                                    # versions
    re.compile(r"\b(?:items?|stages?|parts?|steps?|fronts?|sections?)\s+\d+[a-z]?(?:\([a-z]+\))*", re.I),
    re.compile(r"\b(?:pre-)?(?:item|stage)-\d+", re.I),                  # "pre-item-31", "stage-1"
    re.compile(r"§\s*\d+(?:\.\d+)*"),
    re.compile(r"\b\d+[a-z]?\([a-z]{1,4}\)(?:\([a-z]{1,4}\))*"),           # 20(b), 8(d), 20(e)(i)
    re.compile(r"\bparams-(?:\d+(?:\.\.\d+)?)"),                           # config names
    re.compile(r"\bS\d{2}\b|\bE\d{2}\b|\b[PQRVGMTDC]\d{1,2}′?"),           # labels
]


def numeric_tokens(text: str, exclude: bool) -> set[str]:
    if exclude:
        text = CITE_RE.sub(" ", text)
        for rx in EXCLUDE:
            text = rx.sub(" ", text)
    return set(TOKEN.findall(text))


def lint(rendered: str) -> list[str]:
    bad = []
    for n, line in enumerate(rendered.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#") or line.startswith("|---"):
            continue
        toks = numeric_tokens(line, exclude=True)
        if not toks:
            continue
        cited = CITE_RE.findall(line)
        if not cited:
            bad.append(f"line {n}: numbers {sorted(toks)} with no citation: {line[:120]}")
            continue
        src = set()
        for path, ln, ref in cited:
            lines = show(ref, path)
            if int(ln) <= len(lines):
                src |= numeric_tokens(lines[int(ln) - 1], exclude=False)
        missing = sorted(toks - src)
        if missing:
            bad.append(f"line {n}: {missing} not on cited lines: {line[:140]}")
    return bad


# ---------------------------------------------------------------- generated blocks
def csv_table() -> str:
    path = "research/incipient_plateau/geometric_vs_plateau.csv"
    lines = show(BASE, path)
    rows = list(csv.DictReader(io.StringIO("\n".join(lines))))
    out = ["| set | case | geometric | plateau | designed Ic boundary | source |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 2):
        out.append(f"| {r['set']} | `{r['name']}` | {r['geo']} | {r['plateau']} | {r['gt'] or '—'} | "
                   f"`{path}:{i}@{BASE}` |")
    return "\n".join(out)


def params_track_diff() -> str:
    import yaml
    import cyclophaser
    assert os.path.realpath(cyclophaser.__file__).startswith(os.path.realpath(ROOT) + os.sep), cyclophaser.__file__
    dp = importlib.import_module("cyclophaser.determine_periods")
    doc = yaml.safe_load((ROOT / "research/labels/configs/cyclophaser_params-track.yaml").read_text())
    out, same = [], 0
    for group, fn in (("filter_params", dp.process_vorticity), ("phase_params", dp.get_periods)):
        sig = {k: p.default for k, p in inspect.signature(fn).parameters.items()
               if p.default is not inspect.Parameter.empty}
        for k, v in doc[group].items():
            d = sig[k]
            if v == d and type(v) is type(d):
                same += 1
            elif v == d:
                same += 1
            else:
                out.append((group, k, v, d))
        for k in sig:
            if k not in doc[group] and k not in ("plot", "plot_steps", "export_dict"):
                out.append((group, k, "(absent)", sig[k]))
    rel = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    rows = ["| key | params-track | package default |", "|---|---|---|"]
    for g, k, v, d in out:
        rows.append(f"| `{g}.{k}` | {'(absent)' if v == '(absent)' else f'`{v!r}`'} | `{d!r}` |")
    expected = {("filter_params", "use_filter"), ("filter_params", "boundary_padding"), ("phase_params", "prominence")}
    if {(g, k) for g, k, _, _ in out} != expected:
        ERRORS.append(f"params-track diff changed: {out}")
    return ("Regenerated at render time from `inspect.signature` and the YAML (working tree at "
            f"HEAD `{rel}`; the render aborts if the set of differing keys changes):\n\n" + "\n".join(rows))


def manifest_rows():
    """(path, dest, finding, registered[]) for every leaving file, from MANIFEST.md."""
    text = (ROOT / "research/cleanup/MANIFEST.md").read_text().splitlines()
    rows = {}
    # 0.2 tables: | caminho | tipo | último commit | achado? | refs | destino | motivo | seção | registrado em |
    for l in text:
        m = re.match(r"^\| `([^`]+)`(?: — \*\*(\d+) arquivos\*\*[^|]*)? \| [^|]+ \| `[0-9a-f]+` [0-9-]+ \| (.*?) \| .*? \| \*\*(consolidar|remover)\*\* \| .*? \| (S\d\d|—) \| (.*) \|$", l)
        if m:
            path, _, fin, dest, sec, reg = m.groups()
            fin = fin[len("sim — "):] if fin.startswith("sim — ") else None
            rows[path] = dict(path=path, dest=dest, finding=fin, sec=None if sec == "—" else sec,
                              reg=re.findall(r"`([^`]+:\d+)`", reg))
    return rows


def anchors_for(path: str) -> list[tuple[str, str]]:
    """Where the manifest's judgement says this file's finding is recorded (passo0/judgements.py)."""
    import fnmatch
    if path in J.FINDING:
        return list(J.FINDING[path][1])
    for k, v in J.FINDING.items():
        if "*" in k and fnmatch.fnmatch(path, k):
            return list(v[1])
    if fnmatch.fnmatch(path, "docs/_images/item5/*"):   # make_manifest.classify's own rule
        return [(J.FW, "## 21. Calibration app — Benchmark tab")]
    return []


def section_of(path: str) -> str | None:
    for k, v in J.FRONTS.items():
        if path.startswith(k):
            return v["sec"]
    return None


SECTION_OVERRIDE = {
    "research/incipient_plateau/geometric_vs_plateau.csv": "S02",
    "research/incipient_plateau/gen_geometric_vs_plateau.py": "S02",
}


def traceability(sections_present: set[str]):
    rows = manifest_rows()
    leaving = set(rows)
    out, data = [], []
    for p, r in sorted(rows.items()):
        if r["dest"] == "remover" and not r["finding"]:
            continue
        sec = SECTION_OVERRIDE.get(p) or r["sec"] or section_of(p)
        fw = [resolve(f, BASE, needle)[0].strip("`") for f, needle in anchors_for(p) if f == "docs/future_work.md"]
        dests = []
        if sec:
            if sec not in sections_present:
                ERRORS.append(f"traceability: section {sec} for {p} not in the document")
            dests.append(f"§{sec}")
        for x in fw:
            dests.append(f"`{x}`")
        if not dests:
            ERRORS.append(f"traceability: no destination for {p}")
        for d in dests:
            if any(lp in d for lp in leaving):
                ERRORS.append(f"traceability: destination is a leaving file: {p} -> {d}")
        if r["dest"] == "consolidar":
            recorded = f"the report itself (`{p}:1@{BASE}`)"
        elif anchors_for(p):
            recorded = "; ".join(resolve(f, BASE, needle)[0] for f, needle in anchors_for(p))
        elif sec == "S02" and p in SECTION_OVERRIDE:
            recorded = "only in this file: reproduced in §S02"
        else:
            recorded = "—"
            ERRORS.append(f"traceability: finding of {p} recorded nowhere")
        data.append(dict(path=p, dest=r["dest"], finding=r["finding"], section=sec, future_work=fw,
                         recorded_at=[f"{f}::{n}" for f, n in anchors_for(p)], destination=dests))
        dest_en = {"consolidar": "consolidate", "remover": "remove"}[r["dest"]]
        out.append(f"| `{p}` | {dest_en} | {recorded} | {'; '.join(dests)} |")
    n_silent = sum(1 for r in rows.values() if r["dest"] == "remover" and not r["finding"])
    head = ("| file that leaves | manifest destination | finding recorded at (source) | destination |\n"
            "|---|---|---|---|")
    return head + "\n" + "\n".join(out), data, n_silent


# ---------------------------------------------------------------- render
def main():
    src = (HERE / "findings_src.md").read_text()
    sections = set(re.findall(r"^## (S\d\d)\b", src, re.M))

    def cite(m):
        body = m.group(1)
        if body.startswith("!"):
            return m.group(0)
        path, needle = body.split("|", 1)
        ref = BASE
        if "@" in path:
            path, ref = path.split("@", 1)
        for a, full in ALIASES.items():
            if path == a or path.startswith(a + "/"):
                path = full + path[len(a):]
        return resolve(path.strip(), ref.strip(), needle)[0]

    out = re.sub(r"\{\{(.+?)\}\}", cite, src)
    out = out.replace("{{!csv_table}}", csv_table())
    out = out.replace("{{!params_track_diff}}", params_track_diff())
    table, data, n_silent = traceability(sections)
    out = out.replace("{{!traceability}}", table)
    out = out.replace("{{!n_silent}}", str(n_silent))
    ERRORS.extend(lint(out))
    if ERRORS:
        print("ERRORS:\n  " + "\n  ".join(ERRORS))
        sys.exit(1)
    (ROOT / "docs/findings.md").write_text(out)
    (HERE / "traceability.json").write_text(json.dumps(dict(rows=data, n_remover_without_finding=n_silent),
                                                       indent=1, ensure_ascii=False))
    print(f"docs/findings.md: {len(out.splitlines())} lines; traceability rows {len(data)}; "
          f"remover without finding {n_silent}")


if __name__ == "__main__":
    main()
