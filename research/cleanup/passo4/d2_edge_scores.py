#!/usr/bin/env python
"""Passo 4, D2 — no live text attributes to the current default scores measured
under boundary_padding="edge" (definitions: passo4/PREVISOES.md).

    python research/cleanup/passo4/d2_edge_scores.py LABEL   # writes LABEL.json / LABEL.md next to it

Live set: the D1 set (docs/*.rst, README.md, tools/calibration_app/README.md,
tools/calibration_app/*.py, CHANGELOG.md [Unreleased], research/labels/README.md,
the docstrings and comments of cyclophaser/*.py, read whole here) plus the
generated docs/generated/*.inc included by the site.

Step 1 (mechanical): every line that talks about a score or a measured result
(score/scores/scored/scoring, PASS in capitals, in tolerance, accuracy, hit rate,
measured).
Step 2 (mechanical): of those, the lines whose context (the line and two on each
side) names edge, params-track, params-15 or the default(s) — the only lines
that could attribute an edge-measured score to the current default.
Step 3 (review): each flagged line has a verdict in REVIEW below, written after
reading it in context; a flagged line without a verdict fails the check.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCORE = re.compile(r"\b[Ss]cor(e|es|ed|ing)\b|\bPASS\b|[Ii]n tolerance|[Aa]ccuracy|[Hh]it rate|\b[Mm]easured\b|\bMEASURED\b")
CTX = re.compile(r"\bedge\b|params-track|params-15|\bdefaults?\b", re.I)


def live_files():
    fs = sorted((ROOT / "docs").glob("*.rst")) + sorted((ROOT / "docs/generated").glob("*.inc"))
    fs += [ROOT / "README.md", ROOT / "tools/calibration_app/README.md", ROOT / "research/labels/README.md"]
    fs += sorted((ROOT / "tools/calibration_app").glob("*.py")) + sorted((ROOT / "cyclophaser").glob("*.py"))
    return fs


def changelog_unreleased():
    lines = (ROOT / "CHANGELOG.md").read_text().splitlines()
    a = next(i for i, l in enumerate(lines) if l.startswith("## [Unreleased]"))
    b = next(i for i, l in enumerate(lines) if l.startswith("## [") and i > a)
    return [(i + 1, lines[i]) for i in range(a, b)], lines


REVIEW = {}   # "file:line" -> verdict, written after reading each flagged line in context
_V = {
    "OK-ASSIGNS": "OK: assigns the measured scores to params-track (edge) and says the default has none",
    "OK-FILTER": "OK: a measured effect of the filter or of the padding on the signal, not a detection score",
    "OK-SIGNAL": "OK: 'measured' describes a signal or a rate, not a score",
    "OK-NOOP": "OK: a measured no-op, labelled with the defaults before item 31",
    "OK-WHERE": "OK: points to where something was measured; no score stated",
    "OK-OTHER": "OK: not about the default's scores",
}
for k in ["docs/defaults.rst:41", "docs/defaults.rst:44", "docs/defaults.rst:47",
          "research/labels/README.md:63", "research/labels/README.md:64", "research/labels/README.md:65",
          "cyclophaser/determine_periods.py:432", "cyclophaser/determine_periods.py:433",
          "cyclophaser/determine_periods.py:435", "cyclophaser/determine_periods.py:565",
          "cyclophaser/determine_periods.py:891", "cyclophaser/determine_periods.py:892",
          "cyclophaser/determine_periods.py:894", "cyclophaser/determine_periods.py:1431",
          "cyclophaser/determine_periods.py:1432", "cyclophaser/determine_periods.py:1434",
          "CHANGELOG.md:29", "CHANGELOG.md:30", "CHANGELOG.md:31", "CHANGELOG.md:33",
          "CHANGELOG.md:91", "CHANGELOG.md:93", "tools/calibration_app/app.py:1638"]:
    REVIEW[k] = _V["OK-ASSIGNS"]
for k in ["docs/generated/boundary_padding_effect.inc:1", "tools/calibration_app/README.md:137",
          "tools/calibration_app/app.py:1674", "tools/calibration_app/layer_inspector.py:478",
          "cyclophaser/determine_periods.py:595", "cyclophaser/determine_periods.py:1527",
          "cyclophaser/lanczos_filter.py:34", "cyclophaser/lanczos_filter.py:42",
          "cyclophaser/lanczos_filter.py:172", "cyclophaser/lanczos_filter.py:230",
          "CHANGELOG.md:685", "CHANGELOG.md:710", "CHANGELOG.md:714", "CHANGELOG.md:791",
          "CHANGELOG.md:662"]:
    REVIEW[k] = _V["OK-FILTER"]
for k in ["cyclophaser/determine_periods.py:1079", "cyclophaser/determine_periods.py:1099",
          "cyclophaser/determine_periods.py:1568", "cyclophaser/determine_periods.py:1588",
          "cyclophaser/find_stages.py:874", "cyclophaser/find_stages.py:903"]:
    REVIEW[k] = _V["OK-SIGNAL"]
for k in ["cyclophaser/determine_periods.py:1143", "cyclophaser/determine_periods.py:1629", "CHANGELOG.md:330"]:
    REVIEW[k] = _V["OK-NOOP"]
for k in ["cyclophaser/determine_periods.py:1157", "cyclophaser/determine_periods.py:1643", "CHANGELOG.md:350"]:
    REVIEW[k] = _V["OK-WHERE"]
REVIEW["tools/calibration_app/label_tab.py:1518"] = "OK: 'EDGE' is a phase boundary in the label tab, not boundary_padding"
REVIEW["CHANGELOG.md:664"] = "OK: the validation scope (input type) of a past change, not a score of the current default"
REVIEW["research/labels/README.md:43"] = _V["OK-OTHER"] + " (describes the evaluation script)"


def main():
    label = sys.argv[1]
    hits, flagged = [], []
    sources = [(f.relative_to(ROOT).as_posix(), f.read_text().splitlines(), None) for f in live_files()]
    cl, cl_all = changelog_unreleased()
    sources.append(("CHANGELOG.md", cl_all, {n for n, _ in cl}))
    for name, lines, only in sources:
        for i, line in enumerate(lines, 1):
            if only is not None and i not in only:
                continue
            if not SCORE.search(line):
                continue
            ctx = " ".join(lines[max(0, i - 3):i + 2])
            row = dict(where=f"{name}:{i}", text=line.strip()[:200])
            hits.append(row)
            if CTX.search(ctx):
                row["verdict"] = REVIEW.get(row["where"])
                flagged.append(row)
    missing = [r for r in flagged if not r.get("verdict")]
    attributing = [r for r in flagged if (r.get("verdict") or "").startswith("ATTRIBUTES")]
    out = dict(label=label, score_lines=len(hits), flagged=len(flagged), unreviewed=len(missing),
               attributing=len(attributing), flagged_rows=flagged)
    (HERE / f"{label}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    md = [f"# {label} — D2 (generated by d2_edge_scores.py)\n",
          f"Lines about a score or a measured result: {len(hits)}; flagged (context names edge, params-track, "
          f"params-15 or the default): {len(flagged)}; without a verdict: {len(missing)}; attributing an "
          f"edge-measured score to the current default: **{len(attributing)}**.\n",
          "| where | text | verdict |", "|---|---|---|"]
    md += [f"| `{r['where']}` | {r['text'].replace('|', '\\|')} | {r.get('verdict') or '**(none)**'} |" for r in flagged]
    (HERE / f"{label}.md").write_text("\n".join(md) + "\n")
    print(md[1])
    for r in flagged:
        print(f"  {r['where']}: {r['text'][:150]}")


if __name__ == "__main__":
    main()
