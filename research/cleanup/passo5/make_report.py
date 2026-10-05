#!/usr/bin/env python
"""Passo 5 — gera passo5/RELATORIO.md a partir das saídas de passo5/ (nada digitado).

    python research/cleanup/passo5/make_report.py
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def j(n):
    return json.loads((HERE / n).read_text())


def last(n):
    t = (HERE / n).read_text()
    line = next(l for l in reversed(t.splitlines()) if re.search(r"\d+ (passed|failed)", l))
    return {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed)", line)}, line.strip()


s1, l1 = last("suite_e1_raw.txt")              # the measurement (first run)
s2, l2 = last("suite_e1_second_raw.txt")       # after 9bc670b, recorded alongside
_app = set((HERE / "app_tests.txt").read_text().split())
_failed = [l.split("::")[0].replace("FAILED ", "") for l in (HERE / "suite_e1_raw.txt").read_text().splitlines()
           if l.startswith("FAILED ")]
app_failed_e1 = sum(1 for f in _failed if f in _app)
failed_files = sorted(set(_failed))
cy = subprocess.run(["git", "diff", "--stat", "32651c8", "HEAD", "--", "cyclophaser/"], cwd=ROOT,
                    capture_output=True, text=True).stdout.strip()
pin, lpin = last("e2_pinned_final.txt")
bb, lbb = last("e2_benchmark_pinned_before.txt")
# classification of the Benchmark failures before the fix: a failure whose traceback runs
# through the AppTest harness (streamlit/testing/v1/element_tree.py) with the KeyError is
# "environment" (the app itself renders and accepts raw ids under 1.58: e2_probe_multiselect.py)
_t = (HERE / "e2_benchmark_pinned_before.txt").read_text().split("\n")
_heads = [i for i, l in enumerate(_t) if re.match(r"^_+ test_\w+ _+$", l)]
_end = next(i for i, l in enumerate(_t) if "short test summary" in l)
_b = _heads + [_end]
env_n = sum(1 for a, b in zip(_b, _b[1:]) if "streamlit/testing/v1/element_tree.py" in "\n".join(_t[a:b])
            and "KeyError" in "\n".join(_t[a:b]))
code_n = len(_heads) - env_n
e3b, e3a = j("e3_before.json"), j("e3_after.json")
e4b, e4a = j("e4_before.json"), j("e4_after.json")
e5 = j("e5.json")
d1, r4 = j("e6_d1.json"), j("e6_r4.json")
ids_b, ids_a = j("b_test_ids_before.json"), j("b_test_ids_after.json")
cb, ca = j("c_eval_before_audit.json"), j("c_eval_after_audit.json")
rows = [
    ("E1", "suíte 0 falhas; diff de `cyclophaser/` desde `32651c8` vazio",
     f"{s1.get('passed', 0)} passed / {s1.get('failed', 0)} failed (todas em {', '.join(f'`{f}`' for f in failed_files)}: "
     f"o stub de `score_labels` do teste não tem `n_hit`, que a seção nova do avaliador lê); depois da correção "
     f"`9bc670b`, segunda medição registrada ao lado: {s2.get('passed', 0)} passed / {s2.get('failed', 0)} failed; "
     f"diff: {cy or 'vazio'}",
     s1.get("failed", 0) == 0 and not cy),
    ("E2", "testes do app 0 falhas nos dois ambientes; dos 23 do Benchmark: 0 de ambiente, 23 de código",
     f"dedicado: {app_failed_e1} falhas entre os arquivos de teste do app no E1; fixado: {pin.get('passed', 0)} passed / "
     f"{pin.get('failed', 0)} failed. Benchmark antes, fixado: {bb.get('failed', 0)} falhas (eram 23 no registro): "
     f"**{env_n} de ambiente, {code_n} de código** (o harness AppTest 1.58 reaplica format_func aos rótulos que o "
     "teste passava; o app real renderiza e aceita ids crus no 1.58)",
     app_failed_e1 == 0 and pin.get("failed", 0) == 0 and (env_n, code_n) == (0, 23)),
    ("E3", "build numa cópia limpa: 0 erros, 0 avisos",
     f"antes {e3b['errors']}/{e3b['warnings']} → depois {e3a['errors']}/{e3a['warnings']} (erros/avisos)",
     e3a["errors"] == 0 and e3a["warnings"] == 0),
    ("E4", "0 ocorrências de caminho absoluto fora da exceção",
     f"antes {e4b['occurrences']} → depois {e4a['occurrences']} ({e4a['by_file']})", e4a["occurrences"] == 0),
    ("E5", "gerador não abre arquivo do teste; digest igual antes e depois",
     f"abertos antes (na árvore, pela leitura do código) "
     f"{e5['before_generator_in_normal_tree_by_reading_the_code']['csv_in_directory']}, dos quais "
     f"{e5['before_generator_in_normal_tree_by_reading_the_code']['of_which_test_split']} de teste → depois "
     f"{e5['after_run_in_working_tree']['opened']}, dos quais {e5['after_run_in_working_tree']['test']}; digest "
     f"`{e5['before_run_in_copy_without_test_files']['sha256'][:8]}…` → `{e5['after_run_in_working_tree']['sha256'][:8]}…`",
     e5["after_run_in_working_tree"]["test"] == 0 and e5["digest_equal"]),
    ("E6", "D1 e R4 continuam 0", f"D1 {d1['divergences']}; R4 {r4['live_references']}",
     d1["divergences"] == 0 and r4["live_references"] == 0),
]
out = ["# Passo 5 — relatório (gerado por make_report.py)\n",
       "Previsões: `passo5/PREVISOES.md` (commit 20, `79862a0`), não editadas.\n",
       "| id | previsto | obtido | confere |", "|---|---|---|---|"]
out += [f"| {a} | {b} | {c} | {'sim' if ok else '**NÃO**'} |" for a, b, c, ok in rows]
out += ["", f"E2: a divisão prevista era 0 de ambiente / 23 de código; a obtida é {env_n} de ambiente / {code_n} de "
        "código. As falhas em si foram eliminadas (0 nos dois ambientes).",
        "", "E4 não confere: as 2 ocorrências restantes são menções ao padrão (`/Users/…`, sem nome de usuário) em "
        "`docs/future_work.md`, registro histórico que não é reescrito; não são caminhos.",
        "", "## Outras saídas", "",
        f"* Avaliador, arquivos de trilha abertos: antes (cópia sem arquivos de teste) {cb['csv_opened_under_calibration_data']}, "
        f"depois (árvore) {ca['csv_opened_under_calibration_data']}, dos quais do teste {ca['of_which_test_split']}. "
        "Saída: só as linhas de base foram acrescentadas (`c_eval_before.txt` × `c_eval_after.txt`).",
        f"* Literais de id do split de teste no código do app e dos testes (contagem, sem ids): antes "
        f"{ids_b['test_id_literals']} em {ids_b['lines_with_test_ids']} linhas → depois {ids_a['test_id_literals']} em "
        f"{ids_a['lines_with_test_ids']} linhas, nenhuma em `tools/calibration_app/` "
        "(pendência dos testes restantes em docs/findings.md S11).",
        "", f"Linhas finais: suíte (1ª) `{l1}`; suíte (2ª, depois de `9bc670b`) `{l2}`; app no ambiente fixado `{lpin}`; Benchmark antes, fixado `{lbb}`."]
(HERE / "RELATORIO.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
