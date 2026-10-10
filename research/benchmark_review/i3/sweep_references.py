"""I3, part B: every occurrence of "benchmark" (any case) in the repository,
classified — before (the prediction commit) and after (the working tree).

    python research/benchmark_review/i3/sweep_references.py --base ae3a6c7 --out <md>

Matches are taken from `git grep -i -n` (text inside files: names, paths, ids)
and from `git ls-files` (file names). Classes:

  HISTÓRICA      a record not to be rewritten: docs/future_work.md,
                 docs/findings.md, the CHANGELOG outside [Unreleased], research/
                 of earlier fronts (everything under research/ except the live
                 tools research/labels/*.py|README.md and research/snapshots/),
                 research/benchmark_review/, and the frozen split.yaml
  CORRETA        live text that does not refer to the Benchmark PAGE as existing:
                 the module `benchmark_core` (it stays), the front's name
                 ("benchmark review", research/benchmark_review), the page named
                 in the past tense (retired, old, until I3, 39e658c), the test of
                 its removal, the CHANGELOG [Unreleased] entry that removes it
  AMBÍGUA        listed for Danilo's decision, not changed (at the checkpoint
                 Danilo decided all three: see DECIDED below; after the
                 decision none is left)
  VIVA           live text naming the page as existing — to be updated; after
                 the update the count must be 0

Historical files are reported per file (with their line count); every other
occurrence is reported per line.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Danilo's decision at the I3 checkpoint (2026-10-09), for the three lines that
# were AMBÍGUA: README:119 stays as it is (a record of item 31) — classed
# CORRETA with this note; the docstrings of make_published_snapshot.py and of
# benchmark_core.scoreable were reworded (text only) and no longer match.
DECIDED = {
    ("research/labels/README.md", r"which the Benchmark imports"):
        "decisão do Danilo (checkpoint do I3): fica como está — registro do item 31",
}

AMBIGUOUS = {
    # (path, regex on the line): why it is ambiguous
    ("research/labels/README.md", r"which the Benchmark imports"):
        "fala do import (benchmark_core/item19_core), não manda à página; frase de um registro do item 31",
    ("research/snapshots/make_published_snapshot.py", r"Benchmark tab's reference columns"):
        "docstring de script vivo em research/snapshots/, fora da lista do briefing (que cita só os dois README)",
    ("tools/calibration_app/benchmark_core.py", r"Exploration mode's cyclone upload|test_benchmark_apptest.py` drives"):
        "docstring de função de benchmark_core; o briefing restringe a mudança à docstring do MÓDULO",
}

CORRECT = re.compile(
    r"benchmark_core|benchmark[ _]review|benchmark_review|old_benchmark|OLD_BENCHMARK|"
    r"/benchmark\b|retired|\bold Benchmark|until I3|39e658c|benchmark_page_is_gone|"
    r"old_benchmark_address|in_the_benchmark_even|evaluator_and_benchmark_resolve|"
    r"two_benchmark_instruments|benchmark_tab\.py\"\)\.exists|\"benchmark_tab\" not in src|"
    r"_PAGE_BENCHMARK\" not in src|\"Benchmark\"\)|\"Benchmark\" not in nav|"
    r"Benchmark page was retired|Benchmark page's copy|Benchmark tab with a caption|"
    r"Benchmark's \"Add column from|Benchmark page's Exploration upload|the Benchmark drew|"
    r"benchmark_tab's own copy|One benchmark column|pins were the Benchmark|"
    r"the benchmark, make_split|reader of them \(benchmark|"
    r"\(`benchmark_core`\)",
    re.I)


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout


def historical(path: str, line_no: int | None, unreleased: tuple[int, int] | None) -> bool:
    if path in ("docs/future_work.md", "docs/findings.md", "research/labels/split.yaml"):
        return True
    if path == "CHANGELOG.md":
        return not (unreleased and line_no and unreleased[0] <= line_no < unreleased[1])
    if path.startswith("research/"):
        live = (path.startswith("research/snapshots/")
                or (path.startswith("research/labels/") and path.count("/") == 2
                    and path.endswith((".py", "README.md"))))
        return not live
    return False


def n_is_name(line_no) -> bool:
    return line_no is None


def unreleased_span(text: str) -> tuple[int, int]:
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines, 1) if l.startswith("## [Unreleased]"))
    end = next(i for i, l in enumerate(lines, 1) if i > start and l.startswith("## ["))
    return start, end


def classify(path, line_no, text, unreleased):
    if historical(path, line_no, unreleased):
        return "HISTÓRICA", ""
    for (p, pat), why in DECIDED.items():
        if path == p and re.search(pat, text):
            return "CORRETA", why
    for (p, pat), why in AMBIGUOUS.items():
        if path == p and re.search(pat, text):
            return "AMBÍGUA", why
    if path == "CHANGELOG.md":
        return "CORRETA", "[Unreleased]: a entrada que registra a remoção"
    if CORRECT.search(text) or (n_is_name(line_no) and CORRECT.search(path)):
        return "CORRETA", ""
    return "VIVA", ""


def sweep(rev: str | None) -> list[tuple[str, int | None, str]]:
    if rev:
        raw = git("grep", "-I", "-i", "-n", "benchmark", rev, "--", ".")
        rows = []
        for line in raw.splitlines():
            _rev, path, n, text = line.split(":", 3)
            rows.append((path, int(n), text))
        names = git("ls-tree", "-r", "--name-only", rev).splitlines()
        changelog = git("show", f"{rev}:CHANGELOG.md")
    else:
        raw = git("grep", "--untracked", "-I", "-i", "-n", "benchmark", "--", ".",
                  ":!research/benchmark_review/i3/REFERENCIAS.md")   # its own output
        rows = []
        for line in raw.splitlines():
            path, n, text = line.split(":", 2)
            rows.append((path, int(n), text))
        names = git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
        names = [n for n in names if (ROOT / n).exists()]
        changelog = (ROOT / "CHANGELOG.md").read_text()
    rows += [(n, None, "(nome de arquivo)") for n in names if "benchmark" in n.lower()]
    return rows, unreleased_span(changelog)


def report(title, rows, span, changed_paths=frozenset()):
    out = [f"## {title}", ""]
    by_class = defaultdict(list)
    for path, n, text in rows:
        cls, why = classify(path, n, text, span)
        by_class[cls].append((path, n, text, why))
    counts = {c: len(v) for c, v in by_class.items()}
    out.append("| classe | ocorrências |")
    out.append("|---|---|")
    for c in ("HISTÓRICA", "CORRETA", "AMBÍGUA", "VIVA"):
        out.append(f"| {c} | {counts.get(c, 0)} |")
    out.append("")
    hist = defaultdict(int)
    for path, n, text, _w in by_class.get("HISTÓRICA", []):
        hist[path] += 1
    out.append(f"### HISTÓRICA — por arquivo ({len(hist)} arquivos, não tocados)")
    out.append("")
    out.append("| arquivo | linhas/nome |")
    out.append("|---|---|")
    for path in sorted(hist):
        out.append(f"| `{path}` | {hist[path]} |")
    out.append("")
    for cls in ("VIVA", "AMBÍGUA", "CORRETA"):
        items = by_class.get(cls, [])
        out.append(f"### {cls} — por linha ({len(items)})")
        out.append("")
        if not items:
            out.append("nenhuma")
            out.append("")
            continue
        out.append("| arquivo:linha | texto | nota |")
        out.append("|---|---|---|")
        for path, n, text, why in sorted(items, key=lambda r: (r[0], r[1] or 0)):
            t = text.strip().replace("|", "\\|")
            if len(t) > 140:
                t = t[:137] + "…"
            note = why or ("atualizada nesta rodada" if cls == "VIVA" and path in changed_paths
                           else "")
            loc = f"{path}:{n}" if n else path
            out.append(f"| `{loc}` | {t} | {note} |")
        out.append("")
    return out, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    changed = set(git("diff", "--name-only", args.base).splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines())
    before, span_b = sweep(args.base)
    after, span_a = sweep(None)
    head = ["# I3 — referências a \"benchmark\" (gerado por `sweep_references.py`; não editar à mão)",
            "",
            f"Base (antes): `{args.base}` · depois: árvore de trabalho. Varredura sem "
            "distinguir maiúsculas, em texto (`git grep -i`) e em nomes de arquivo. "
            "Classes e regras no cabeçalho do script.",
            "",
            "Na tabela **antes**, cada VIVA é uma referência à página Benchmark como "
            "existente; o arquivo dela está na coluna nota quando foi alterado nesta rodada. "
            "Na tabela **depois**, VIVA deve ser 0.",
            ""]
    b, cb = report("Antes (base)", before, span_b, changed)
    a, ca = report("Depois (árvore de trabalho) — varredura final", after, span_a)
    tail = ["## Resultado", "",
            f"- antes: VIVA {cb.get('VIVA', 0)}, AMBÍGUA {cb.get('AMBÍGUA', 0)}, "
            f"CORRETA {cb.get('CORRETA', 0)}, HISTÓRICA {cb.get('HISTÓRICA', 0)}",
            f"- depois: VIVA **{ca.get('VIVA', 0)}**, AMBÍGUA {ca.get('AMBÍGUA', 0)}, "
            f"CORRETA {ca.get('CORRETA', 0)}, HISTÓRICA {ca.get('HISTÓRICA', 0)}",
            ""]
    Path(args.out).write_text("\n".join(head + tail + b + a) + "\n")
    print("\n".join(tail))


if __name__ == "__main__":
    main()
