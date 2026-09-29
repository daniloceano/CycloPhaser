#!/usr/bin/env python
"""Passo 3 — render research/cleanup/passo3/RELATORIO.md from this step's outputs (nothing typed).

    python research/cleanup/passo3/make_report.py
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TAG = "archive/research-diagnostics-pre-cleanup"


def j(n):
    return json.loads((HERE / n).read_text())


def digest(n):
    t = (HERE / n).read_text()
    return re.search(r"SHA256\s*=\s*([0-9a-f]{64})", t).group(1), re.search(r"^HEAD: ([0-9a-f]{40})", t, re.M).group(1)


T = j("tag_and_trace.json")
L = j("live_refs.json")
I = j("imports_check.json")
V = j("verify_citations_after.json")
suite = (HERE / "suite_raw.txt").read_text()
last = next(l for l in reversed(suite.splitlines()) if re.search(r"\d+ passed", l))
cnt = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|deselected)", last)}
suite_head = re.search(r"^HEAD: ([0-9a-f]{40})", suite, re.M).group(1)
d0, h0 = digest("digest_before_raw.txt")
d1, h1 = digest("digest_after_raw.txt")
tag_commit = subprocess.check_output(["git", "rev-parse", "--short", f"{TAG}^{{commit}}"], cwd=ROOT, text=True).strip()
cy_diff = subprocess.run(["git", "diff", "--stat", "39ff8c8", "HEAD", "--", "cyclophaser/"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
r1 = T["R1"]
rows = [
    ("R1", "removidos = remover + consolidar do MANIFEST = 309",
     f"listados {r1['listed']}; apagados por `{r1['removal_commit']}` {r1['deleted_by_commit']}; mesmo conjunto: {r1['same_set']}",
     r1["listed"] == 309 and r1["same_set"]),
    ("R2", "100 % na tag", f"{T['R2']['present_at_tag']}/{T['R2']['checked']} em `{TAG}` (`{tag_commit}`)",
     not T["R2"]["missing"]),
    ("R3", "S10: 0 falhas", f"{T['R3']['rows']} linhas; falhas {len(T['R3']['failures'])}", not T["R3"]["failures"]),
    ("R4", "referências vivas: 0", f"{L['live_references']} (saídas do próprio script, à parte: {L['own_outputs']})",
     L["live_references"] == 0),
    ("R5", ".py mantidos: 0 falhas", f"{I['kept_py']} arquivos, {I['local_imports_checked']} imports locais; falhas {len(I['failures'])}",
     not I["failures"]),
    ("R6", "suíte 0 falhas; diff de cyclophaser/ vazio",
     f"{cnt.get('passed', 0)} passed / {cnt.get('failed', 0)} failed (HEAD `{suite_head[:7]}`); diff: {cy_diff or 'vazio'}",
     cnt.get("failed", 0) == 0 and not cy_diff),
    ("R7", "digest igual antes e depois", f"`{d0[:8]}…` (HEAD `{h0[:7]}`) → `{d1[:8]}…` (árvore do commit 12)", d0 == d1),
    ("R8", "verify_citations: 0 falhas",
     f"{V['citations_resolved']}/{V['citations_total']} citações; falhas {len(V['failures'])}; fracas {V['weak_citations']}",
     not V["failures"]),
]
out = ["# Passo 3 — relatório (gerado)\n",
       "Gerado por `passo3/make_report.py` a partir das saídas de `passo3/`. Previsões: `passo3/PREVISOES.md` "
       f"(commit 11, `{tag_commit}`, onde está a tag).\n",
       "| id | previsto | obtido | confere |", "|---|---|---|---|"]
out += [f"| {a} | {b} | {c} | {'sim' if ok else '**NÃO**'} |" for a, b, c, ok in rows]
out += ["", "## Removidos por diretório\n", "| diretório | arquivos |", "|---|---|"]
out += [f"| `{k}` | {v} |" for k, v in r1["per_dir"].items()]
out += ["", f"Linha final da suíte: `{last.strip()}`."]
(HERE / "RELATORIO.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
