# Passo 3 — relatório (gerado)

Gerado por `passo3/make_report.py` a partir das saídas de `passo3/`. Previsões: `passo3/PREVISOES.md` (commit 11, `654a3e5`, onde está a tag).

| id | previsto | obtido | confere |
|---|---|---|---|
| R1 | removidos = remover + consolidar do MANIFEST = 309 | listados 309; apagados por `2912b79` 309; mesmo conjunto: True | sim |
| R2 | 100 % na tag | 309/309 em `archive/research-diagnostics-pre-cleanup` (`654a3e5`) | sim |
| R3 | S10: 0 falhas | 203 linhas; falhas 0 | sim |
| R4 | referências vivas: 0 | primeira medição 0 com scanner defeituoso → medição corrigida em `2912b79`: **7** em 5 arquivos (lista abaixo) | **NÃO** |
| R5 | .py mantidos: 0 falhas | 33 arquivos, 46 imports locais; falhas 0 | sim |
| R6 | suíte 0 falhas; diff de cyclophaser/ vazio | 1438 passed / 0 failed (HEAD `2912b79`); diff: vazio | sim |
| R7 | digest igual antes e depois | `7552bc67…` (HEAD `654a3e5`) → `7552bc67…` (árvore do commit 12) | sim |
| R8 | verify_citations: 0 falhas | 543/543 citações; falhas 0; fracas 45 | sim |

## R4 — correção (depois do commit 13)

O scanner da primeira medição só reconhecia o caminho completo (e o nome solto no mesmo diretório); menções por caminho parcial (`diagnostics/item31/...`) ou só pelo nome passaram. Corrigido em `passo3/live_refs.py` com a MESMA definição do PREVISOES (qualquer sufixo de 2+ componentes, ou o nome sozinho quando nenhum arquivo em HEAD o tem). **R4 = FAIL**; a previsão não é ajustada.

Medição corrigida na árvore de `2912b79` — 7 referências em 5 arquivos (`live_refs_2912b79_corrected.txt`):

* `research/labels/README.md:106` → `research/labels/diagnostics/item31/stale_scripts.md`
* `research/labels/config_defaults.py:4` → `research/labels/diagnostics/item31/DESIGN.md`
* `research/labels/config_defaults.py:12` → `research/labels/diagnostics/item31/make_defaults_2_0_0.py`
* `research/labels/labels_core.py:61` → `research/labels/diagnostics/item30/PREDICTIONS_part3.md`
* `research/labels/swell_item30/adjudicate_item30.py:16` → `research/labels/diagnostics/item30/REPORT_figs_cf.md`
* `research/labels/swell_item30/adjudicate_item30.py:54` → `research/labels/diagnostics/item30/REPORT_figs_cf.md`
* `research/labels/swell_item30/freeze_validation_batch.py:5` → `research/labels/diagnostics/item30/PREDICTIONS_part3.md`

Reescritas no commit 14 para `archive/research-diagnostics-pre-cleanup:<caminho>`. No mesmo commit, `item30/figs_cf.py` voltou ao estado de `654a3e5` e `item30/separability_train_params14.csv` foi restaurado da tag (manter, decisão 8).

### Medido uma vez depois do commit 14

| medida | obtido |
|---|---|
| R4 (scanner corrigido) | 0 referências vivas; caminhos removidos 308; saídas do próprio script 13 (`live_refs_after14_own_outputs.txt`) |
| R5 | 33 .py, 46 imports locais, falhas 0 |
| suíte | 1438 passed / 0 failed / 1 skipped / 29 deselected (HEAD `51596c0`) |
| verify_citations | 542/542 citações, falhas 0, fracas 45 |
| diff de `cyclophaser/` desde `654a3e5` | vazio |

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
