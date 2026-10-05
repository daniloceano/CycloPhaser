#!/usr/bin/env python
"""Passo 4, parte 4a — gera passo4/RELATORIO_4a.md a partir das saídas de passo4/ (nada digitado).

    python research/cleanup/passo4/make_report_4a.py
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def j(n):
    return json.loads((HERE / n).read_text())


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()


B0, B1, A = j("before.json"), j("before_corrected.json"), j("after17.json")
R4 = j("r4_after17.json")
D5 = j("d5_app_fallbacks.json")
suite = (HERE / "suite_after17_raw.txt").read_text()
last = next(l for l in reversed(suite.splitlines()) if re.search(r"\d+ passed", l))
cnt = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed)", last)}
head = re.search(r"^HEAD: ([0-9a-f]{40})", suite, re.M).group(1)
cy = subprocess.run(["git", "diff", "--stat", "129b04d", head, "--", "cyclophaser/"], cwd=ROOT,
                    capture_output=True, text=True).stdout.strip()
out_docs = {f: n for f, n in A["divergences_by_file"].items() if not f.startswith("docs/")}
rows = [
    ("D1 (antes)", "0 divergências em `cyclophaser/`",
     f"oficial (`before.json`): {B0['divergences']}, {B0['divergences_in_cyclophaser']} em `cyclophaser/`; "
     f"corrigida (`before_corrected.json`): {B1['divergences']}, {B1['divergences_in_cyclophaser']} em `cyclophaser/`",
     B0["divergences_in_cyclophaser"] == 0),
    ("D1a", "0 divergências FORA de `docs/*.rst` após o commit 17",
     f"{A['divergences']} no total, {sum(out_docs.values())} fora de `docs/*.rst` "
     f"(por arquivo: {A['divergences_by_file']})", sum(out_docs.values()) == 0),
    ("D4 suíte", "0 falhas", f"{cnt.get('passed', 0)} passed / {cnt.get('failed', 0)} failed (HEAD `{head[:7]}`)",
     cnt.get("failed", 0) == 0),
    ("D4 diff", "diff de `cyclophaser/` desde 16b (`129b04d`) vazio", cy or "vazio", not cy),
    ("D4 R4", "0 referências vivas (scanner corrigido do Passo 3)",
     f"{R4['live_references']} referências; caminhos removidos {R4['removed']}; saídas próprias {R4['own_outputs']}",
     R4["live_references"] == 0),
    ("D5", "1 configuração chega aos caminhos de reserva; resultados inalterados",
     f"{D5['configurations_reaching_a_fallback']} configurações; resultados alterados: {D5['results_changed'] or 'nenhum'}",
     D5["configurations_reaching_a_fallback"] == 1 and not D5["results_changed"]),
]
out = ["# Passo 4, parte 4a — relatório (gerado)\n",
       "Gerado por `passo4/make_report_4a.py` a partir das saídas de `passo4/`. Previsões: `passo4/PREVISOES.md` "
       "(commits 16 e 16c; não editadas).\n",
       "| id | previsto | obtido | confere |", "|---|---|---|---|"]
out += [f"| {a} | {b} | {c} | {'sim' if ok else '**NÃO**'} |" for a, b, c, ok in rows]
out += ["", "## D5 — detalhe\n",
        f"* Reservas com literal ANTES (`{D5['old_rev']}`): `_preset_to_widgets` "
        f"{D5['preset_to_widgets_literal_fallbacks_old']}; `mature_ledger` {D5['mature_ledger_literal_fallbacks_old']}.",
        f"* Em HEAD: `_preset_to_widgets` {D5['preset_to_widgets_literal_fallbacks_head'] or 'nenhuma'}; "
        f"`mature_ledger` {D5['mature_ledger_literal_fallbacks_head'] or 'nenhuma'} (lidas da assinatura).",
        ]
out += [f"* `{n}`: chaves ausentes {r['missing_keys'] or 'nenhuma'}; widgets antes == depois: {r['identical']}"
        for n, r in D5["presets"].items()]
out += [f"* `mature_ledger`: chaves sempre passadas por `build_args_periods`: "
        f"{D5['mature_ledger_keys_in_build_args_periods']}.",
        "* A previsão (1) vinha de supor que o preset \"clean\" não traz todas as chaves de filtragem; "
        "os dois presets trazem todas. **D5 = FAIL na contagem**; resultados inalterados.",
        "", "## D1a — divergências restantes (todas em `docs/*.rst`, revisão do Danilo)\n"]
out += [f"* `{r['file']}:{r['line']}` `{r['param']}`: escrito `{r['value']}`, código {r['code']}"
        for r in A["divergence_rows"]]
out += ["", f"Linha final da suíte: `{last.strip()}`."]
(HERE / "RELATORIO_4a.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
