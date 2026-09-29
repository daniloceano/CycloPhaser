# Passo 3 — relatório (gerado)

Gerado por `passo3/make_report.py` a partir das saídas de `passo3/`. Previsões: `passo3/PREVISOES.md` (commit 11, `654a3e5`, onde está a tag).

| id | previsto | obtido | confere |
|---|---|---|---|
| R1 | removidos = remover + consolidar do MANIFEST = 309 | listados 309; apagados por `2912b79` 309; mesmo conjunto: True | sim |
| R2 | 100 % na tag | 309/309 em `archive/research-diagnostics-pre-cleanup` (`654a3e5`) | sim |
| R3 | S10: 0 falhas | 203 linhas; falhas 0 | sim |
| R4 | referências vivas: 0 | 0 (saídas do próprio script, à parte: 11) | sim |
| R5 | .py mantidos: 0 falhas | 33 arquivos, 46 imports locais; falhas 0 | sim |
| R6 | suíte 0 falhas; diff de cyclophaser/ vazio | 1438 passed / 0 failed (HEAD `2912b79`); diff: vazio | sim |
| R7 | digest igual antes e depois | `7552bc67…` (HEAD `654a3e5`) → `7552bc67…` (árvore do commit 12) | sim |
| R8 | verify_citations: 0 falhas | 543/543 citações; falhas 0; fracas 45 | sim |

## Removidos por diretório

| diretório | arquivos |
|---|---|
| `Pipfile` | 1 |
| `docs/_images` | 6 |
| `research/incipient_plateau` | 9 |
| `research/inert_params` | 14 |
| `research/labels/diagnostics/frontA_idx0_c2` | 38 |
| `research/labels/diagnostics/frontA_reverify` | 30 |
| `research/labels/diagnostics/frontC` | 11 |
| `research/labels/diagnostics/frontD` | 21 |
| `research/labels/diagnostics/frontRefusal` | 21 |
| `research/labels/diagnostics/front_b` | 19 |
| `research/labels/diagnostics/item19` | 17 |
| `research/labels/diagnostics/item20a` | 7 |
| `research/labels/diagnostics/item20b` | 18 |
| `research/labels/diagnostics/item30` | 45 |
| `research/labels/diagnostics/item31` | 50 |
| `tests/calibration_data` | 1 |
| `tests/synthetic` | 1 |

Linha final da suíte: `1438 passed, 1 skipped, 29 deselected, 89 warnings in 433.80s (0:07:13)`.
