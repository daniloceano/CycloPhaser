#!/usr/bin/env python
"""Passo 4, D1 — every default written in the live documentation against the code.

    <cyclophaser env python> -P research/cleanup/passo4/check_documented_defaults.py LABEL

Read-only. Imports cyclophaser only for `inspect.signature` (asserted to be this
working tree). Definitions are those of passo4/PREVISOES.md; starting point is
passo0/defaults_in_text.py (MANIFEST section 0.2(e)).

Signature defaults: get_periods, process_vorticity, determine_periods,
find_peaks_valleys, lanczos_filter, lanczos_bandpass_filter.

Checked set: docs/*.rst, README.md, tools/calibration_app/README.md, the app's
text (tools/calibration_app/*.py: comments and strings containing whitespace),
CHANGELOG.md between "## [Unreleased]" and the first released section,
research/labels/README.md; and, read-only, the docstrings/comments of
cyclophaser/*.py.

A DEFAULT CLAIM is a value stated as the current default:
  C1  "Default is X" / "Default: X" / "**Default**: X" / "defaults to X" /
      "Default X since ..." / "default value is X" — X is the literal right after;
      A narrative of a change ("moved the default to X", "changed the default
      to X") is not a claim about the current default.
  C2  a value followed by "(default" / "(**default**" (not "(the default before",
      "(the default up to", which are historical);
  C3  the last cell ("now") of a CHANGELOG table row `| `param` | … | … |` whose
      table header names a "now" column.
  C1b "default ``name=value``" — a claim about `name`.
X is a number, True/False/None, or a quoted/backticked token (a token equal to a
parameter name is not a value). A parenthesised or "it was …" value after X is
historical and ignored. The parameter is, in order: the nearest parameter
header at or above the line within the same block (walking up until a blank
line; a docstring "name (type", an rst/markdown bullet "**name**", or a heading
"### `name`"); else, in the app's .py files, the widget of the statement
(`key="w"` / `_DEFAULTS["w"]` up to 14 raw lines above, mapped to a parameter by
the app's own widget→parameter table in `_sidebar_defaults_from_signature`);
else the parameter named nearest before X on the line or earlier in the same
paragraph. (Commit 16c: the widget rule used to come after the paragraph rule,
which attributed app.py:1630 to boundary_padding and app.py:2005 to prominence.)

cyclophaser/find_stages.py documents the STAGE functions, whose parameters come
in `args_periods` with their own fallbacks (`args_periods.get(key, literal)`),
not the public signatures. Its claims are checked against those fallbacks, and
the keys whose stage fallback differs from the public default are listed apart
(an informational finding, not a D1 divergence).

A DIVERGENCE is a claim whose value is not the signature default of the
parameter in any of the functions that have it (numbers compared numerically,
strings after stripping quotes/backticks, case-insensitive for words).

Writes LABEL.json and LABEL.md next to it; exit 0 always (the verdict is read
from the counts).
"""
from __future__ import annotations

import importlib
import inspect
import io
import json
import re
import subprocess
import sys
import tokenize
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import cyclophaser  # noqa: E402

assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
dp = importlib.import_module("cyclophaser.determine_periods")
lf = importlib.import_module("cyclophaser.lanczos_filter")
FUNCS = {"process_vorticity": dp.process_vorticity, "get_periods": dp.get_periods,
         "determine_periods": dp.determine_periods, "find_peaks_valleys": dp.find_peaks_valleys,
         "lanczos_filter": lf.lanczos_filter, "lanczos_bandpass_filter": lf.lanczos_bandpass_filter}
DEFAULTS: dict[str, dict[str, object]] = {}
for fname, fn in FUNCS.items():
    for k, p in inspect.signature(fn).parameters.items():
        if p.default is not inspect.Parameter.empty:
            DEFAULTS.setdefault(k, {})[fname] = p.default
STAGE_FALLBACKS: dict[str, object] = {}
import ast  # noqa: E402
for node in ast.walk(ast.parse((ROOT / "cyclophaser/find_stages.py").read_text())):
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "args_periods"
            and len(node.args) == 2 and isinstance(node.args[0], ast.Constant)):
        try:
            STAGE_FALLBACKS[node.args[0].value] = ast.literal_eval(node.args[1])
        except ValueError:
            pass
_app = (ROOT / "tools/calibration_app/app.py").read_text()
WIDGET_TO_PARAM = dict(re.findall(r'"(\w+)":\s*[^,\n]*?sig\["(\w+)"\]', _app))
NAMES = sorted(DEFAULTS, key=len, reverse=True)
NAME_RE = re.compile(r"(?<![\w])(" + "|".join(map(re.escape, NAMES)) + r")(?![\w])")
HDR_RES = [re.compile(r"^\s*(\w+)\s*\((?:str|float|int|bool|Union|list|dict|optional|number)", re.I),
           re.compile(r"^\s*[-*]\s+\*\*(\w+)\*\*"),
           re.compile(r"^\s*#+\s+`(\w+)`"),
           re.compile(r"^\s*-\s+'(\w+)'\s*\(")]

LIT = (r"(?P<q>``|`|\"|')?(?P<v>-?\d+(?:\.\d+)?|True|False|None|[A-Za-z_][\w.-]*)(?P=q)?"
       r"|``\"(?P<v2>[\w.-]+)\"``|`\"(?P<v3>[\w.-]+)\"`|``'(?P<v4>[\w.-]+)'``|`'(?P<v5>[\w.-]+)'`")
C1 = re.compile(r"(?<!moved the )(?<!changed the )\bdefault(?:s| value)?\b\*{0,2}\s*(?:is|to|:|=)?\s*\*{0,2}\s*:?\s*(?:" + LIT + r")", re.I)
C1B = re.compile(r"\bdefault\s+``?(?P<p>\w+)\s*=\s*[\"']?(?P<v>[\w.-]+)", re.I)
C2 = re.compile(r"(?:" + LIT + r")\s*\(\s*\*{0,2}default(?!\s+(?:before|up|in|of))\b", re.I)
WORD_OK = re.compile(r"^(-?\d+(?:\.\d+)?|True|False|None|auto|reflect|edge|zero|local|global|amplitude|"
                     r"derivative|plateau|geometric|vorticity|sustained|single|southern|northern)$", re.I)


def value_of(m: re.Match) -> str | None:
    for g in ("v2", "v3", "v4", "v5", "v"):
        v = m.groupdict().get(g)
        if v:
            if v in DEFAULTS:
                return None           # a parameter name, not a value
            quoted = g != "v" or bool(m.group("q"))
            if not quoted and not WORD_OK.match(v):
                return None           # "default settings", "defaults of", ... — not a literal
            return v
    return None


def same(v: str, d: object) -> bool:
    if isinstance(d, bool) or d is None:
        return v.lower() == str(d).lower()
    if isinstance(d, (int, float)):
        try:
            return float(v) == float(d)
        except ValueError:
            return False
    return v.strip("\"'`").lower() == str(d).lower()


def files() -> list[str]:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    return [f for f in tracked if f in ("README.md", "CHANGELOG.md", "tools/calibration_app/README.md",
                                        "research/labels/README.md")
            or re.match(r"docs/[^/]+\.rst$", f) or re.match(r"tools/calibration_app/[^/]+\.py$", f)
            or re.match(r"cyclophaser/[^/]+\.py$", f)]


def text_lines(f: str) -> list[str]:
    src = (ROOT / f).read_text(encoding="utf-8")
    lines = src.splitlines()
    if not f.endswith(".py"):
        if f == "CHANGELOG.md":
            start = next(i for i, l in enumerate(lines) if l.startswith("## [Unreleased]"))
            end = next(i for i, l in enumerate(lines) if i > start and re.match(r"## \[\d", l))
            return [l if start <= i < end else "" for i, l in enumerate(lines)]
        return lines
    prose = [""] * len(lines)
    kinds = {tokenize.COMMENT, tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type not in kinds or (tok.type != tokenize.COMMENT and not re.search(r"\s", tok.string)):
            continue
        for k, piece in enumerate(tok.string.split("\n")):
            prose[tok.start[0] - 1 + k] += " " + piece
    return prose


def param_for(lines, raw, i, pos, line):
    # 1. the parameter header of this block (walk up to the first blank line)
    def blank(t):                         # a lone "#" separates comment paragraphs
        return not t.strip() or t.strip() == "#"
    for j in range(i, max(-1, i - 15), -1):
        if j < i and blank(lines[j]):
            break
        for rx in HDR_RES:
            m = rx.match(lines[j])
            if m and m.group(1) in DEFAULTS:
                return m.group(1)
    # 2. app widgets (before any name cited in the paragraph): the widget key of the
    #    statement — the help text of a widget is about that widget's parameter
    #    even when it mentions another parameter (Passo 4, commit 16c correction)
    if raw is not None:
        for j in range(i, max(-1, i - 15), -1):
            m = re.search(r'(?:key=|_DEFAULTS\[)"(\w+)"', raw[j])
            if m and m.group(1) in WIDGET_TO_PARAM:
                return WIDGET_TO_PARAM[m.group(1)]
    # 3. the parameter named nearest before the value, on the line or earlier in the paragraph
    before = [m for m in NAME_RE.finditer(line) if m.start() < pos]
    if before:
        return before[-1].group(1)
    for j in range(i - 1, max(-1, i - 6), -1):
        if blank(lines[j]):
            break
        names = NAME_RE.findall(lines[j])
        if names:
            return names[-1]
    return None


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "defaults_check"
    claims, unassociated = [], []
    for f in files():
        lines = text_lines(f)
        raw = (ROOT / f).read_text(encoding="utf-8").splitlines() if f.startswith("tools/") and f.endswith(".py") else None
        now_table = False
        for i, line in enumerate(lines):
            if not line.strip():
                now_table = False
                continue
            if f == "CHANGELOG.md" and line.startswith("| parameter") and "now" in line:
                now_table = True
                continue
            found = []
            if f == "CHANGELOG.md" and now_table:
                m = re.match(r"^\| `(\w+)` \| .* \| (?P<now>[^|]+) \|\s*$", line)
                if m and m.group(1) in DEFAULTS:
                    v = re.sub(r"[*`\"']", "", m.group("now")).split("—")[0].strip().split(" ")[0].split("(")[0]
                    if v.lower() != "unchanged":
                        found.append(("C3", m.group(1), v))
            spans = []
            for m in C1B.finditer(line):
                if m.group("p") in DEFAULTS:
                    found.append(("C1b", m.group("p"), m.group("v")))
                    spans.append(m.span())
            for rx, kind in ((C1, "C1"), (C2, "C2")):
                for m in rx.finditer(line):
                    if any(a <= m.start() < b for a, b in spans):
                        continue
                    v = value_of(m)
                    if v is None:
                        continue
                    p = param_for(lines, raw, i, m.start(), line)
                    if p is None:
                        unassociated.append(dict(file=f, line=i + 1, kind=kind, value=v, text=line.strip()[:160]))
                        continue
                    found.append((kind, p, v))
            for kind, p, v in found:
                if f == "cyclophaser/find_stages.py" and p in STAGE_FALLBACKS:
                    ref = {"find_stages args_periods fallback": STAGE_FALLBACKS[p]}
                else:
                    ref = DEFAULTS[p]
                ok = any(same(v, d) for d in ref.values())
                claims.append(dict(file=f, line=i + 1, kind=kind, param=p, value=v,
                                   code={k: repr(x) for k, x in ref.items()}, ok=ok,
                                   text=line.strip()[:200]))
    div = [c for c in claims if not c["ok"]]
    stage_vs_public = {k: dict(stage=repr(v), public={f: repr(x) for f, x in DEFAULTS[k].items()})
                       for k, v in sorted(STAGE_FALLBACKS.items())
                       if k in DEFAULTS and not any(same(repr(v).strip("'"), d) for d in DEFAULTS[k].values())}
    by_file = Counter(c["file"] for c in div)
    out = dict(label=label, claims=len(claims), divergences=len(div), divergences_by_file=dict(by_file),
               divergences_in_cyclophaser=sum(n for f, n in by_file.items() if f.startswith("cyclophaser/")),
               unassociated=len(unassociated), divergence_rows=div, unassociated_rows=unassociated,
               claim_rows=claims, stage_fallbacks_differing_from_public=stage_vs_public)
    (HERE / f"{label}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    md = [f"# Passo 4 — documented defaults against the code ({label})", "",
          "Generated by `passo4/check_documented_defaults.py`; definitions in `passo4/PREVISOES.md`.", "",
          f"Claims found: {len(claims)}; divergences: {len(div)} "
          f"(in cyclophaser/: {out['divergences_in_cyclophaser']}); claims with no parameter found: {len(unassociated)}.", "",
          "| file | divergences |", "|---|---|"] + [f"| `{f}` | {n} |" for f, n in sorted(by_file.items())] + [
          "", "## Divergences", "", "| file:line | rule | parameter | written | code | text |", "|---|---|---|---|---|---|"]
    for c in div:
        md.append(f"| `{c['file']}:{c['line']}` | {c['kind']} | {c['param']} | `{c['value']}` | "
                  f"{', '.join(f'{k}={v}' for k, v in c['code'].items())} | {c['text'].replace('|', '/')} |")
    md += ["", "## Stage-function fallbacks that differ from the public defaults (informational)", "",
           "`cyclophaser/find_stages.py` stage functions read these keys from `args_periods` with their own "
           "fallback; `get_periods` always passes every key, so the fallback is reached only by a direct call.", "",
           "| key | stage fallback | public default(s) |", "|---|---|---|"]
    md += [f"| `{k}` | `{v['stage']}` | {', '.join(f'{f}={x}' for f, x in v['public'].items())} |"
           for k, v in stage_vs_public.items()]
    md += ["", "## Claims with no parameter found (not judged)", "", "| file:line | value | text |", "|---|---|---|"]
    for u in unassociated:
        md.append(f"| `{u['file']}:{u['line']}` | `{u['value']}` | {u['text'].replace('|', '/')} |")
    (HERE / f"{label}.md").write_text("\n".join(md) + "\n")
    print(f"{label}: claims {len(claims)}; divergences {len(div)} (cyclophaser/: {out['divergences_in_cyclophaser']}); "
          f"unassociated {len(unassociated)}; stage fallbacks differing from public: {len(stage_vs_public)}")
    for f, n in sorted(by_file.items()):
        print(f"  {f}: {n}")


if __name__ == "__main__":
    main()
