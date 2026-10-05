# Passo 5 — relatório (gerado por make_report.py)

Previsões: `passo5/PREVISOES.md` (commit 20, `79862a0`), não editadas.

| id | previsto | obtido | confere |
|---|---|---|---|
| E1 | suíte 0 falhas; diff de `cyclophaser/` desde `32651c8` vazio | 1437 passed / 6 failed (todas em `tests/test_evaluate_batch_train.py`: o stub de `score_labels` do teste não tem `n_hit`, que a seção nova do avaliador lê); depois da correção `9bc670b`, segunda medição registrada ao lado: 1443 passed / 0 failed; diff: vazio | **NÃO** |
| E2 | testes do app 0 falhas nos dois ambientes; dos 23 do Benchmark: 0 de ambiente, 23 de código | dedicado: 0 falhas entre os arquivos de teste do app no E1; fixado: 658 passed / 0 failed. Benchmark antes, fixado: 24 falhas (eram 23 no registro): **24 de ambiente, 0 de código** (o harness AppTest 1.58 reaplica format_func aos rótulos que o teste passava; o app real renderiza e aceita ids crus no 1.58) | **NÃO** |
| E3 | build numa cópia limpa: 0 erros, 0 avisos | antes 0/1 → depois 0/0 (erros/avisos) | sim |
| E4 | 0 ocorrências de caminho absoluto fora da exceção | antes 3 → depois 2 ({'docs/future_work.md': 2}) | **NÃO** |
| E5 | gerador não abre arquivo do teste; digest igual antes e depois | abertos antes (na árvore, pela leitura do código) 51, dos quais 16 de teste → depois 35, dos quais 0; digest `7552bc67…` → `7552bc67…` | sim |
| E6 | D1 e R4 continuam 0 | D1 0; R4 0 | sim |

E2: a divisão prevista era 0 de ambiente / 23 de código; a obtida é 24 de ambiente / 0 de código. As falhas em si foram eliminadas (0 nos dois ambientes).

E4 não confere: as 2 ocorrências restantes são menções ao padrão (`/Users/…`, sem nome de usuário) em `docs/future_work.md`, registro histórico que não é reescrito; não são caminhos.

## Outras saídas

* Avaliador, arquivos de trilha abertos: antes (cópia sem arquivos de teste) 35, depois (árvore) 35, dos quais do teste 0. Saída: só as linhas de base foram acrescentadas (`c_eval_before.txt` × `c_eval_after.txt`).
* Literais de id do split de teste no código do app e dos testes (contagem, sem ids): antes 13 em 9 linhas → depois 10 em 8 linhas, nenhuma em `tools/calibration_app/` (pendência dos testes restantes em docs/findings.md S11).

Linhas finais: suíte (1ª) `6 failed, 1437 passed, 1 skipped, 29 deselected, 89 warnings in 479.95s (0:07:59)`; suíte (2ª, depois de `9bc670b`) `1443 passed, 1 skipped, 29 deselected, 89 warnings in 469.58s (0:07:49)`; app no ambiente fixado `658 passed, 15 warnings in 212.63s (0:03:32)`; Benchmark antes, fixado `24 failed, 29 passed, 14 warnings in 33.22s`.
