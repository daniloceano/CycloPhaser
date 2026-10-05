#!/usr/bin/env python
"""Passo 4, Fase C — gera passo4/RELATORIO_faseC.md a partir das saídas (nada digitado).
Previsões: passo4/PREVISOES.md (D1–D3 do commit 16; D4 redeclarado no 16h).

    python research/cleanup/passo4/make_report_faseC.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def j(n):
    return json.loads((HERE / n).read_text())


D1, D2 = j("faseC_d1.json"), j("faseC_d2.json")
B0, B1 = j("build_before_raw.json"), j("build_faseC_raw.json")
R4 = j("faseC_r4.json")
cy = (HERE / "faseC_cyclophaser_diff.txt").read_text().strip()
cy_empty = cy.endswith("[]")
suite = (HERE / "suite_faseC_raw.txt").read_text()
last = next(l for l in reversed(suite.splitlines()) if re.search(r"\d+ passed", l))
cnt = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed)", last)}
rows = [
    ("D1", "0 divergências no conjunto verificado (incluindo `docs/*.rst`)",
     f"{D1['divergences']} divergências ({D1['claims']} afirmações; em `cyclophaser/`: "
     f"{D1['divergences_in_cyclophaser']})", D1["divergences"] == 0),
    ("D2", "nenhum texto vivo atribui ao default atual escores medidos sob `edge`",
     f"{D2['attributing']} (linhas sobre escore/medição: {D2['score_lines']}; revisadas: {D2['flagged']}; "
     f"sem veredito: {D2['unreviewed']}; lista em `faseC_d2.md`)",
     D2["attributing"] == 0 and D2["unreviewed"] == 0),
    ("D3", "build sem erros; avisos depois ≤ avisos antes",
     f"antes {B0['errors']} erros / {B0['warnings']} avisos → depois {B1['errors']} erros / {B1['warnings']} avisos",
     B1["errors"] == 0 and B1["warnings"] <= B0["warnings"]),
    ("D4 suíte", "0 falhas", f"{cnt.get('passed', 0)} passed / {cnt.get('failed', 0)} failed", cnt.get("failed", 0) == 0),
    ("D4 diff", "diff de `cyclophaser/` desde 16h vazio", cy, cy_empty),
    ("D4 R4", "0 referências vivas", f"{R4['live_references']} (caminhos removidos {R4['removed']})",
     R4["live_references"] == 0),
]
out = ["# Passo 4, Fase C — relatório (gerado por make_report_faseC.py)\n",
       "Medido uma vez, depois de \"aprovo a documentação\", sobre a árvore que os commits da Fase C gravam.\n",
       "| id | previsto | obtido | confere |", "|---|---|---|---|"]
out += [f"| {a} | {b} | {c} | {'sim' if ok else '**NÃO**'} |" for a, b, c, ok in rows]
out += ["", f"Linha final da suíte: `{last.strip()}`."]
(HERE / "RELATORIO_faseC.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
