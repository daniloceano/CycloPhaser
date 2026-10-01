#!/usr/bin/env python
"""Passo 4, commit 16d — gera passo4/RELATORIO_16d.md a partir das saídas (nada digitado).

    python research/cleanup/passo4/make_report_16d.py
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def j(n):
    return json.loads((HERE / n).read_text())


def digest(n):
    t = (HERE / n).read_text()
    return re.search(r"SHA256\s*=\s*([0-9a-f]{64})", t).group(1), re.search(r"^HEAD: ([0-9a-f]{40})", t, re.M).group(1)


R = j("sweep_16d_review.json")
A = j("ast_16d.json")
E = j("edit_16d_log.json")
V = j("after16d.json")
d0, h0 = digest("digest_16d_before_raw.txt")
d1, h1 = digest("digest_16d_after_raw.txt")
suite = (HERE / "suite_16d_raw.txt").read_text()
last = next(l for l in reversed(suite.splitlines()) if re.search(r"\d+ passed", l))
cnt = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed)", last)}
glog = subprocess.check_output(["git", "log", "--format=%h %s", "develop-v2.1..HEAD", "--", "cyclophaser/"],
                               cwd=ROOT, text=True).strip().splitlines()
(HERE / "gate_a_16d.txt").write_text("git log --format='%h %s' develop-v2.1..HEAD -- cyclophaser/\n"
                                     + "\n".join(glog) + "\n")
rst = [e for e in E if "**sea level" in e["new"] or "Must be less than" in e["new"] or "``|dz|``" in e["new"]]
out = ["# Commit 16d — relatório (gerado por make_report_16d.py)\n",
       "| verificação | obtido |", "|---|---|",
       f"| varredura (`sweep_16d.py`, antes) | {R['hits']} linhas; corrigidas {R['corrected']}, mantidas {R['kept']} "
       "(`sweep_16d_review.md`) |",
       f"| edições (`edit_16d.py`) | {len(E)} edições, {sum(e['count'] for e in E)} substituições; destas, {len(rst)} "
       "são as correções de rst que quebravam a build |",
       f"| verificador de defaults depois (`after16d.json`) | divergências em `cyclophaser/`: "
       f"{V['divergences_in_cyclophaser']} |",
       f"| (i) árvore sintática sem docstrings (`ast_16d.json`, {A['before']} → {A['after']}) | idêntica: "
       f"{A['identical']} ({A['files']} arquivos) |",
       f"| (ii) digest default, mesma sessão | `{d0[:8]}…` (HEAD `{h0[:7]}`) → `{d1[:8]}…`; igual: {d0 == d1} |",
       f"| suíte `-m \"not browser\"` | {cnt.get('passed', 0)} passed / {cnt.get('failed', 0)} failed |",
       "| `git log -- cyclophaser/` desde develop-v2.1 (`gate_a_16d.txt`) | "
       + "; ".join(f"`{l.split()[0]}`" for l in glog) + " |",
       "", f"Linha final da suíte: `{last.strip()}`."]
(HERE / "RELATORIO_16d.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
