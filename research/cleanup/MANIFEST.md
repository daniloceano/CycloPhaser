# Passo 0 — Inventário: manifesto de arquivos, branches e rastreabilidade

**Frente:** limpeza do repositório + default `boundary_padding` · **Passo 0 — somente leitura**, corrigido no Passo 1. No Passo 0 nada fora de `research/cleanup/` foi removido, movido, renomeado ou editado; as decisões do Danilo sobre esta proposta estão em "Decisões aprovadas".

* Branch `chore/repo-cleanup`, criada de `origin/develop-v2.1` @ `06d8550` (ponta esperada `06d8550`: confere); inventário regerado em HEAD `c080f4d`.
* **Correções do Passo 1** (aprovadas pelo Danilo): `.pypirc` saiu do versionamento (commit próprio, conteúdo não lido); branches com equivalência de patch separadas das ancestrais; `measure_incipient_smoothing.py` → manter; saídas de `passo0/` sem caminhos absolutos; decisões aprovadas registradas. Seções 0.1–0.4 regeradas pelos scripts.
* Gerado por `research/cleanup/passo0/make_manifest.py` a partir de `inventory.py`, `branches.py`, `defaults_in_text.py` (mecânico) e `judgements.py` (julgamento: destino, motivo, achado). Toda contagem e todo `arquivo:linha` abaixo é regerado pelo script; nenhum número foi digitado.
* Âncoras de registro são resolvidas por texto (arquivo + trecho) e o render aborta se o trecho faltar ou for ambíguo.
* `.pypirc` foi excluído de toda leitura de conteúdo (é arquivo de credenciais) e, no Passo 1, saiu do versionamento (decisão 2).

## 0.1 Linha de base (mesma máquina, mesma sessão)

Previsões declaradas no prompt da frente antes da medição; não ajustadas.

| medida | previsto | obtido | confere |
|---|---|---|---|
| suíte `-m "not browser"` — passed | 1438 | 1438 | sim |
| suíte — failed | 0 | 0 | sim |
| digest `front_b/default_behaviour_hash.py` | começa por `3a6de265` | `3a6de265…` (47 séries) | sim |

Linha final bruta da suíte: `1438 passed, 1 skipped, 29 deselected, 89 warnings in 464.42s (0:07:44)`. Ambiente (`baseline_env.txt`): HEAD: 06d85504474b72a894b4e7f72b2944fc577fd139; cyclophaser.__file__: <repo>/cyclophaser/__init__.py.
**Anonimização declarada (Passo 1).** Nenhuma saída versionada desta frente contém caminho absoluto: raiz do repositório → `<repo>`, ambiente conda (absoluto, relativo à raiz ou com `~`) → `<env>`, home → `~`. Feita por `passo0/anonymize.py` (idempotente); `inventory.py` aplica a mesma regra ao que grava e `run_baseline.sh` chama o anonimizador ao fim. Substituições por arquivo (`passo0/anonymize_log.json`): `MANIFEST.md`: <env> <- env prefix ×41; `passo0/baseline_digest_raw.txt`: <repo> <- repo root ×2; `passo0/baseline_env.txt`: <env> <- env prefix ×2, <repo> <- repo root ×1; `passo0/baseline_suite_raw.txt`: <env> <- env prefix ×8, <repo> <- repo root ×1; `passo0/inventory.json`: <env> <- env prefix ×41.
"Suíte completa" = `-m "not browser"`: CLAUDE.md proíbe rodar `tests/test_label_browser.py`. Só passed/failed são reportados (regra fixa). Saídas brutas: `passo0/baseline_suite_raw.txt`, `passo0/baseline_digest_raw.txt`, `passo0/baseline_env.txt`; comando: `passo0/run_baseline.sh`.

**Efeito colateral tratado:** o gerador canônico ANEXA um registro ao seu livro-razão `research/labels/diagnostics/front_b/default_behaviour_sha256.txt`. Como este passo não edita nada fora de `research/cleanup/`, o registro anexado foi guardado em `passo0/baseline_digest_appended_record.diff` e o livro-razão restaurado para HEAD. Na rodada medida isso foi feito à mão logo após o script; `run_baseline.sh` foi depois atualizado para fazer o mesmo sozinho.

## 0.2 Manifesto de arquivos

Arquivos versionados em HEAD: **536** (git ls-files, excluindo `research/cleanup/`, i.e. a árvore de develop). Linhas do manifesto: 434 (425 individuais + 9 grupos homogêneos cobrindo 111 arquivos).

| destino | arquivos |
|---|---|
| manter | 222 |
| consolidar | 40 |
| remover | 274 |

Colunas: caminho · tipo · último commit (hash data) · contém achado? · quem o referencia (arquivo(nº de linhas); `diag/` = `research/labels/diagnostics/`; lista completa com linhas em `passo0/inventory.json`) · destino · motivo · seção de destino no documento único (se consolidar/achado a mover) · onde o achado já está registrado.

Semântica: **manter** = fica; **consolidar** = o conteúdo vai para o documento único de achados (Passo 2) e o arquivo sai depois; **remover** = sai, porque o conteúdo já está registrado em outro lugar (ou é reprodutível pelo commit). Nada sai neste passo.

Seções propostas para o documento único (Passo 2):

* **S01** — Filtro de Lanczos e padding de borda (itens 3c, 4, 8(d))
* **S02** — Fase incipiente: método plateau, suavização, recusa (relatórios incipient_plateau, itens 25, 26)
* **S03** — Índice 0: tipo do extremo e reclassificação (Front A, itens 8, 27, 28)
* **S04** — Mature: proeminência × amplitude, profundidade, pareamento (itens 20, 20(a), 22)
* **S05** — Intensification: piso de profundidade (item 24)
* **S06** — `distance` / `length_scale` (Front B, item 19)
* **S07** — Plateau que sobrescreve intensification; lote swell (item 30)
* **S08** — params-15/params-track como default do pacote; exposição do teste (item 31)
* **S09** — Parâmetros inertes no app (item 9(b))
* **S10** — Rastreabilidade: scripts aposentados, instrumentos, índices de recuperação

### `(raiz)`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `.gitignore` | config | `c080f4d` 2026-09-28 | não | — | **manter** | config de versionamento | — | — |
| `.python-version` | config | `0df0ef5` 2026-06-16 | não | .gitignore(1), tools/calibration_app/requirements.txt(1) | **manter** | versão do Python do deploy do app (citado em tools/calibration_app/requirements.txt) | — | — |
| `.readthedocs.yml` | config | `a1ff4d7` 2023-12-18 | não | — | **manter** | build da documentação | — | — |
| `CHANGELOG.md` | doc de usuário | `cc5519e` 2026-09-28 | sim — mudanças de comportamento por versão, com tabelas de defaults | docs/future_work.md(1), docs/usage.rst(1), diag/frontA_idx0_c2/REPORT.md(1), diag/frontC/REPORT.md(1), +1 | **manter** | doc de usuário; [Unreleased] é vivo | — | — |
| `CLAUDE.md` | config | `0f680c5` 2026-09-16 | não | docs/future_work.md(2), diag/frontA_reverify/REPORT.md(1), diag/frontRefusal/REPORT.md(1), diag/item19/PROVENANCE.md(1), +1 | **manter** | regras fixas para agentes | — | — |
| `LICENSE` | doc de usuário | `f2c51f3` 2024-09-17 | não | CHANGELOG.md(1), docs/license.rst(1) | **manter** | licença | — | — |
| `Pipfile` | config | `b734799` 2024-10-18 | não | .gitignore(5), docs/future_work.md(1), environment.yml(1) | **remover** | pins de 2024 que não batem com setup.py/environment.yml; nenhum CI/RTD/env o usa (environment.yml é o canônico) | — | — |
| `README.md` | doc de usuário | `7a14eb0` 2026-09-11 | não | docs/future_work.md(7), research/labels/README.md(2), diag/item30/REPORT_part3.md(2), diag/item31/recovery_table.py(2), +4 | **manter** | doc de usuário (entrada do pacote no PyPI) | — | — |
| `environment.yml` | config | `d876a71` 2026-09-11 | não | docs/future_work.md(7), .circleci/config.yml(1), README.md(1), tests/test_app_distance_removed.py(1) | **manter** | ambiente conda canônico (regra fixa) | — | — |
| `pyproject.toml` | config | `b7a1c04` 2026-06-15 | não | — | **manter** | build-system | — | — |
| `requirements.txt` | config | `42af263` 2024-10-29 | não | environment.yml(4), docs/future_work.md(3), docs/installation.rst(2), .readthedocs.yml(1), +3 | **manter** | fica (decisão 10): as instruções de instalação/contribuição dos docs de usuário o leem (ver Dados gerados) | — | — |
| `runtime.txt` | config | `3d25bd5` 2026-06-15 | não | — | **manter** | versão do Python do deploy | — | — |
| `setup.py` | config | `f423476` 2026-06-15 | não | environment.yml(2), tools/calibration_app/app.py(2), CHANGELOG.md(1), README.md(1), +4 | **manter** | empacotamento (versão, dependências) | — | — |

### `.circleci`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `.circleci/config.yml` | config | `d876a71` 2026-09-11 | não | docs/future_work.md(1), environment.yml(1) | **manter** | CI do pacote (instala do wheel) | — | — |

### `cyclophaser`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `cyclophaser/__init__.py` | pacote | `a6842d9` 2024-10-18 | não | diag/frontA_idx0_c2/outputs/stage2_gate.log(3), diag/item31/gate_2a.txt(3), diag/item30/figs_cf_output.txt(2), diag/item30/part3_measure_output.txt(2), +49 | **manter** | código/dados do pacote | — | — |
| `cyclophaser/determine_periods.py` | pacote | `a1784b5` 2026-09-28 | não | docs/future_work.md(15), research/inert_params/REPORT_inertia_sweep.md(8), diag/item19/PROVENANCE.md(8), research/inert_params/INCIDENTAL_crash_bug.md(7), +52 | **manter** | código/dados do pacote | — | — |
| `cyclophaser/find_stages.py` | pacote | `f85e1b8` 2026-09-27 | não | docs/future_work.md(29), diag/item19/REPORT.md(14), diag/frontA_idx0_c2/outputs/m5_boundary_independence.log(9), diag/item19/stage2_grid.py(9), +52 | **manter** | código/dados do pacote | — | — |
| `cyclophaser/lanczos_filter.py` | pacote | `4e70d17` 2026-09-03 | não | docs/future_work.md(1), diag/item20b/REPORT.md(1), diag/item20b/supplement_20b.py(1), diag/item20b/supplement_20b.txt(1) | **manter** | código/dados do pacote | — | — |
| `cyclophaser/plots.py` | pacote | `5cc80ba` 2026-06-14 | não | tests/test_manual_labels.py(2), CHANGELOG.md(1), research/labels/labels_core.py(1), research/snapshots/README.md(1), +3 | **manter** | código/dados do pacote | — | — |

### `cyclophaser/example_data`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `cyclophaser/example_data/example_file.csv` | dados | `a6842d9` 2024-10-18 | não | docs/future_work.md(2), cyclophaser/__init__.py(1), setup.py(1), tests/test_track_io.py(1), +2 | **manter** | código/dados do pacote | — | — |

### `docs`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `docs/Makefile` | doc de usuário | `3e5155c` 2023-12-18 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/api.rst` | doc de usuário | `7b8c4aa` 2024-10-28 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/calibration_tool.rst` | doc de usuário | `829296e` 2026-06-15 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/conf.py` | doc de usuário | `56a4546` 2026-06-15 | não | .readthedocs.yml(1) | **manter** | documentação de usuário / build RTD | — | — |
| `docs/contribute.rst` | doc de usuário | `f2c51f3` 2024-09-17 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/future_work.md` | registro/relatório | `06d8550` 2026-09-28 | sim — registro canônico de todas as frentes (achados, gates, decisões) | diag/item31/exposure_table.md(39), diag/item31/exposure_table.json(19), CHANGELOG.md(8), diag/frontD/REPORT.md(3), +32 | **manter** | registro canônico; histórico NÃO reescrito (só nota params-15 → params-track) | — | — |
| `docs/index.rst` | doc de usuário | `829296e` 2026-06-15 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/installation.rst` | doc de usuário | `177eb88` 2024-11-08 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/license.rst` | doc de usuário | `f2c51f3` 2024-09-17 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/make.bat` | doc de usuário | `3e5155c` 2023-12-18 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/overview.rst` | doc de usuário | `107152a` 2024-09-27 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/requirements.txt` | doc de usuário | `56a4546` 2026-06-15 | não | .readthedocs.yml(1) | **manter** | documentação de usuário / build RTD | — | — |
| `docs/testing.rst` | doc de usuário | `f2c51f3` 2024-09-17 | não | — | **manter** | documentação de usuário / build RTD | — | — |
| `docs/usage.rst` | doc de usuário | `c5217b5` 2026-09-28 | não | docs/future_work.md(1), diag/item31/DESIGN.md(1) | **manter** | documentação de usuário / build RTD | — | — |

### `docs/_images`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `docs/_images/cyclophaser_methodology.jpg` | doc de usuário | `107152a` 2024-09-27 | não | docs/overview.rst(1), tools/calibration_app/app.py(1) | **manter** | documentação de usuário / build RTD | — | — |
| `docs/_images/density_map_Aggregate.png` | doc de usuário | `a6842d9` 2024-10-18 | não | — | **remover** | órfã: nenhum arquivo a referencia (última mudança na 1.8.7) | — | — |
| `docs/_images/item5/*.png` — **5 arquivos** (`git ls-files 'docs/_images/item5/*.png'`) | doc de usuário | `23cb784` 2026-09-18 | sim — evidência visual (barra lateral/benchmark antes-depois) | — | **remover** | capturas de tela do item 21; nenhum doc as referencia | — | `docs/future_work.md:2004` |
| `docs/_images/test_custom.png` | doc de usuário | `a6842d9` 2024-10-18 | não | README.md(1), docs/index.rst(1), docs/usage.rst(1) | **manter** | documentação de usuário / build RTD | — | — |
| `docs/_images/test_default.png` | doc de usuário | `a6842d9` 2024-10-18 | não | docs/usage.rst(1) | **manter** | documentação de usuário / build RTD | — | — |
| `docs/_images/test_steps_default.png` | doc de usuário | `598fc88` 2024-10-03 | não | docs/usage.rst(1) | **manter** | documentação de usuário / build RTD | — | — |

### `research/app_layer_inspector`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/app_layer_inspector/gen_inspector_figures.py` | script de diagnóstico | `d560bf9` 2026-09-05 | não | tools/calibration_app/README.md(1), tools/calibration_app/inspector_mpl.py(1) | **manter** | citado pelo app (inspector_mpl.py, README do app) como gerador das figuras | — | — |

### `research/incipient_plateau`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/incipient_plateau/REPORT_incipient_characterisation.md` | registro/relatório | `0fbacc8` 2026-09-04 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/exposure_table.md(17), docs/future_work.md(2), CHANGELOG.md(1), cyclophaser/find_stages.py(1), +5 | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S02 | `docs/future_work.md:1294` |
| `research/incipient_plateau/REPORT_incipient_smoothing.md` | registro/relatório | `e0b1b49` 2026-09-04 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/exposure_table.md(6), CHANGELOG.md(1), diag/item31/exposure_table.json(1), diag/item31/exposure_table.py(1), +1 | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S02 | `docs/future_work.md:1294` |
| `research/incipient_plateau/gen_geometric_vs_plateau.py` | script de diagnóstico | `8a79f6a` 2026-09-04 | sim — gerador do checkpoint visual geometric×plateau (produz geometric_vs_plateau.csv); nenhum relatório o cita | — | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | S02 | **SÓ AQUI** |
| `research/incipient_plateau/geometric_vs_plateau.csv` | saída gerada | `e965eca` 2026-09-04 | sim — fronteira incipient por caso, reais e sintéticos: geometric vs plateau vs verdade de projeto | research/incipient_plateau/gen_geometric_vs_plateau.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | **SÓ AQUI** |
| `research/incipient_plateau/incipient_measurements.csv` | saída gerada | `0fbacc8` 2026-09-04 | sim — medições incipient por trajetória (caracterização) | research/incipient_plateau/measure_incipient.py(2), research/incipient_plateau/REPORT_incipient_characterisation.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/incipient_plateau/REPORT_incipient_characterisation.md:57` |
| `research/incipient_plateau/incipient_smoothing_real_rel0.csv` | saída gerada | `e0b1b49` 2026-09-04 | sim — rel(t0) nas trajetórias reais por janela de suavização | research/incipient_plateau/REPORT_incipient_smoothing.md(1), research/incipient_plateau/measure_incipient_smoothing.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/incipient_plateau/REPORT_incipient_smoothing.md:118` |
| `research/incipient_plateau/incipient_smoothing_sweep.csv` | saída gerada | `e0b1b49` 2026-09-04 | sim — varredura de janela/critério da sonda incipient | research/incipient_plateau/measure_incipient_smoothing.py(2), research/incipient_plateau/REPORT_incipient_smoothing.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/incipient_plateau/REPORT_incipient_smoothing.md:96` |
| `research/incipient_plateau/incipient_smoothing_tables.txt` | saída gerada | `e0b1b49` 2026-09-04 | sim — tabelas da varredura de suavização | research/incipient_plateau/measure_incipient_smoothing.py(2), research/incipient_plateau/REPORT_incipient_smoothing.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/incipient_plateau/REPORT_incipient_smoothing.md:157` |
| `research/incipient_plateau/measure_incipient.py` | script de diagnóstico | `0fbacc8` 2026-09-04 | não | docs/future_work.md(1), research/incipient_plateau/REPORT_incipient_characterisation.md(1), research/incipient_plateau/REPORT_incipient_smoothing.md(1), research/incipient_plateau/gen_geometric_vs_plateau.py(1), +1 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/incipient_plateau/measure_incipient_smoothing.py` | script de diagnóstico | `e0b1b49` 2026-09-04 | não | CHANGELOG.md(1), cyclophaser/find_stages.py(1), research/incipient_plateau/REPORT_incipient_smoothing.md(1) | **manter** | citado por comentário vivo do pacote (o alvo do comentário tem de existir; linha em 'registrado em') | — | `cyclophaser/find_stages.py:905` |
| `research/incipient_plateau/summary_tables.txt` | saída gerada | `0fbacc8` 2026-09-04 | sim — tabelas-resumo da caracterização | research/incipient_plateau/measure_incipient.py(2), research/incipient_plateau/REPORT_incipient_characterisation.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/incipient_plateau/REPORT_incipient_characterisation.md:302` |

### `research/inert_params`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/inert_params/BACKLOG_inexplicada.md` | registro/relatório | `25a113a` 2026-09-10 | sim — relatório de frente fechada (achados, previsões, veredito) | research/inert_params/REPORT_inertia_sweep.md(4), research/inert_params/DATA_DEPENDENT_findings.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S09 | `docs/future_work.md:756` |
| `research/inert_params/DATA_DEPENDENT_findings.md` | registro/relatório | `25a113a` 2026-09-10 | sim — relatório de frente fechada (achados, previsões, veredito) | research/inert_params/BACKLOG_inexplicada.md(2), research/inert_params/REPORT_inertia_sweep.md(2), research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md(1), research/inert_params/classify.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S09 | `docs/future_work.md:756` |
| `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md` | registro/relatório | `25a113a` 2026-09-10 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1), research/inert_params/DATA_DEPENDENT_findings.md(1), research/inert_params/REPORT_inertia_sweep.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S09 | `docs/future_work.md:756` |
| `research/inert_params/INCIDENTAL_crash_bug.md` | registro/relatório | `25a113a` 2026-09-10 | sim — relatório de frente fechada (achados, previsões, veredito) | research/inert_params/REPORT_inertia_sweep.md(3), docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S09 | `docs/future_work.md:756` |
| `research/inert_params/PREDICTION.md` | registro/relatório | `f188bae` 2026-09-10 | sim — relatório de frente fechada (achados, previsões, veredito) | research/inert_params/REPORT_inertia_sweep.md(3), research/inert_params/extra_checks.py(1), research/inert_params/followup_checks.py(1), research/inert_params/sweep_inertia.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S09 | `docs/future_work.md:756` |
| `research/inert_params/REPORT_inertia_sweep.md` | registro/relatório | `4c0767c` 2026-09-16 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/exposure_table.md(17), tests/test_app_distance_removed.py(2), .gitignore(1), CHANGELOG.md(1), +10 | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S09 | `docs/future_work.md:756` |
| `research/inert_params/classify.py` | script de diagnóstico | `25a113a` 2026-09-10 | não | research/inert_params/REPORT_inertia_sweep.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/inert_params/extra_checks.py` | script de diagnóstico | `f188bae` 2026-09-10 | não | research/inert_params/REPORT_inertia_sweep.md(2) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/inert_params/followup_checks.py` | script de diagnóstico | `f188bae` 2026-09-10 | não | research/inert_params/REPORT_inertia_sweep.md(2) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/inert_params/inertia_matrix.csv` | saída gerada | `25a113a` 2026-09-10 | sim — matriz de inércia parâmetro × config | research/inert_params/REPORT_inertia_sweep.md(3), research/inert_params/DATA_DEPENDENT_findings.md(2), research/inert_params/classify.py(2), research/inert_params/sweep_inertia.py(2), +2 | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S09 | `research/inert_params/REPORT_inertia_sweep.md:36` |
| `research/inert_params/inertia_matrix_full.csv` | saída gerada | `25a113a` 2026-09-10 | sim — matriz de inércia completa (com derivados) | research/inert_params/REPORT_inertia_sweep.md(2), research/inert_params/classify.py(2), research/inert_params/sweep_derived.py(2), docs/future_work.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S09 | `docs/future_work.md:756` |
| `research/inert_params/sweep_derived.py` | script de diagnóstico | `25a113a` 2026-09-10 | não | docs/future_work.md(2), research/inert_params/REPORT_inertia_sweep.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/inert_params/sweep_derived_summary.txt` | saída gerada | `25a113a` 2026-09-10 | sim — resumo da varredura derivada | research/inert_params/REPORT_inertia_sweep.md(3), research/inert_params/sweep_derived.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S09 | `research/inert_params/REPORT_inertia_sweep.md:87` |
| `research/inert_params/sweep_inertia.py` | script de diagnóstico | `f188bae` 2026-09-10 | não | research/inert_params/REPORT_inertia_sweep.md(2), research/inert_params/sweep_derived.py(2), docs/future_work.md(1), research/inert_params/extra_checks.py(1), +1 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/inert_params/sweep_summary.txt` | saída gerada | `f188bae` 2026-09-10 | sim — resumo da varredura de inércia | research/inert_params/REPORT_inertia_sweep.md(3), research/inert_params/sweep_inertia.py(2), .gitignore(1), research/inert_params/DATA_DEPENDENT_findings.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S09 | `research/inert_params/REPORT_inertia_sweep.md:26` |

### `research/labels`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/README.md` | registro/relatório | `1766338` 2026-09-28 | sim — tabela de proveniência/hash das configs, removidas incluídas | docs/future_work.md(3), diag/item30/REPORT_part3.md(2), CLAUDE.md(1), diag/item31/recovery_table.py(1) | **manter** | doc do conjunto de rótulos e das configs (vivo) | — | — |
| `research/labels/config_defaults.py` | script de pesquisa (vivo) | `a5067df` 2026-09-28 | não | research/labels/README.md(2), CHANGELOG.md(1), diag/item31/DESIGN.md(1), diag/item31/make_defaults_2_0_0.py(1), +2 | **manter** | preenchimento de chaves ausentes (app e testes) | — | — |
| `research/labels/configs/cyclophaser_params-15.yaml` | config | `f85e1b8` 2026-09-27 | não | cyclophaser/determine_periods.py(3), diag/item31/gate_2a.py(3), research/labels/README.md(2), CHANGELOG.md(1), +11 | **manter** | a config de referência (renomear para params-track no Passo 1, conteúdo intacto) | — | — |
| `research/labels/defaults_2.0.0.json` | saída gerada | `a5067df` 2026-09-28 | não | cyclophaser/determine_periods.py(3), CHANGELOG.md(2), research/labels/README.md(2), research/labels/config_defaults.py(2), +10 | **manter** | tabela congelada dos defaults 2.0.0 (pacote, docs, testes) | — | — |
| `research/labels/evaluate_against_labels.py` | script de pesquisa (vivo) | `a5067df` 2026-09-28 | não | docs/future_work.md(14), diag/front_b/ADDENDUM_part1b.md(9), diag/front_b/reference_score_attribution.py(9), diag/frontD/REPORT.md(8), +28 | **manter** | avaliador vivo (medidor de sequência) | — | — |
| `research/labels/freeze_synthetic_series.py` | script de pesquisa (vivo) | `490a90e` 2026-09-10 | não | research/labels/labels_core.py(2), docs/future_work.md(1) | **manter** | gerador das séries sintéticas congeladas | — | — |
| `research/labels/front_g/front_g_deviation_table.py` | script de diagnóstico | `727efd2` 2026-09-15 | não | docs/future_work.md(1), research/labels/front_g/front_g_synthetic_deviations.md(1) | **manter** | gerador da tabela citada por teste vivo | — | — |
| `research/labels/front_g/front_g_synthetic_deviations.md` | registro/relatório | `727efd2` 2026-09-15 | sim — desvio detectado − rótulo por fronteira sintética | docs/future_work.md(3), research/labels/front_g/front_g_deviation_table.py(2), tests/synthetic/test_synthetic_lifecycles.py(1) | **manter** | citado por teste vivo (test_synthetic_lifecycles.py); tabela por fronteira | — | — |
| `research/labels/labels_core.py` | script de pesquisa (vivo) | `d1841cc` 2026-09-27 | não | docs/future_work.md(5), diag/item30/prove_defaults_30c.py(2), diag/item30/prove_defaults_part3.py(2), research/labels/README.md(1), +5 | **manter** | núcleo de rótulos (importado por testes e app) | — | — |
| `research/labels/make_split.py` | script de pesquisa (vivo) | `97513a7` 2026-09-05 | não | research/labels/README.md(2), tests/test_manual_labels.py(1) | **manter** | gerador do split (lido por teste) | — | — |
| `research/labels/manual_labels.yaml` | dados | `9dc87d4` 2026-09-27 | não | docs/future_work.md(12), research/labels/README.md(4), research/labels/swell_item30/adjudicate_item30.py(4), diag/frontA_idx0_c2/REPORT.md(3), +15 | **manter** | verdade dos rótulos (fonte da temporização) | — | — |
| `research/labels/split.yaml` | dados | `916ecfc` 2026-09-27 | não | docs/future_work.md(9), research/labels/labels_core.py(6), tools/calibration_app/label_tab.py(6), research/labels/swell_item30/README.md(5), +32 | **manter** | split CONGELADO | — | — |
| `research/labels/swell_item30/README.md` | registro/relatório | `916ecfc` 2026-09-27 | sim — registro do lote swell (seleção, marcas, exposição) | research/labels/README.md(2), docs/future_work.md(1), diag/item31/exposure_table.py(1) | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/adjudicate_item30.py` | script de diagnóstico | `9dc87d4` 2026-09-27 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1), tests/test_evaluate_batch_train.py(1) | **manter** | gerador de dados congelados — proveniência do lote | — | — |
| `research/labels/swell_item30/adjudicate_item30_output.txt` | saída gerada | `9dc87d4` 2026-09-27 | sim — log da adjudicação dos 5 rótulos (demais blocos idênticos) | — | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/draw_batch.py` | script de diagnóstico | `659eb5e` 2026-09-25 | não | research/labels/split.yaml(1), research/labels/swell_item30/README.md(1), research/labels/swell_item30/transcribe_groups.py(1) | **manter** | gerador de dados congelados — proveniência do lote | — | — |
| `research/labels/swell_item30/freeze_validation_batch.py` | script de diagnóstico | `d1841cc` 2026-09-27 | não | research/labels/split.yaml(1) | **manter** | gerador de dados congelados — proveniência do lote | — | — |
| `research/labels/swell_item30/freeze_validation_batch_output.txt` | saída gerada | `d1841cc` 2026-09-27 | sim — log do congelamento do lote de validação | — | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/groups_params11.yaml` | dados | `659eb5e` 2026-09-25 | não | research/labels/swell_item30/draw_batch.py(3), diag/item30/outside_signal.py(1), diag/item30/part3_measure.py(1), diag/item30/separability.py(1), +4 | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/labels_v1_snapshot.yaml` | dados | `9dc87d4` 2026-09-27 | não | research/labels/manual_labels.yaml(5), research/labels/swell_item30/adjudicate_item30.py(2), docs/future_work.md(1), diag/item30/REPORT_part3.md(1), +3 | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/provenance.yaml` | dados | `7a480a5` 2026-09-25 | não | research/labels/swell_item30/README.md(1), research/labels/swell_item30/draw_batch.py(1), research/labels/swell_item30/freeze_validation_batch.py(1) | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/provenance_val.yaml` | dados | `d1841cc` 2026-09-27 | não | research/labels/swell_item30/freeze_validation_batch.py(2), diag/item30/REPORT_part3.md(1) | **manter** | dados/proveniência do lote swell (lidos por testes e pelo avaliador) | — | — |
| `research/labels/swell_item30/transcribe_groups.py` | script de diagnóstico | `659eb5e` 2026-09-25 | não | research/labels/swell_item30/README.md(1) | **manter** | gerador de dados congelados — proveniência do lote | — | — |

### `research/labels/diagnostics/frontA_idx0_c2`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/frontA_idx0_c2/REPORT.md` | registro/relatório | `e97eb17` 2026-09-24 | sim — relatório de frente fechada (achados, previsões, veredito) | cyclophaser/determine_periods.py(3), docs/future_work.md(2), CHANGELOG.md(1), tests/test_reclassify_index0.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S03 | `docs/future_work.md:2931` |
| `research/labels/diagnostics/frontA_idx0_c2/common.py` | script de diagnóstico | `b3bdaa1` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(2), diag/frontA_idx0_c2/fig_20190639.py(1), diag/frontA_idx0_c2/m2b_peak_to_valley.py(1), diag/frontA_idx0_c2/m3_force_peak.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/fig_20190639.py` | script de diagnóstico | `8f55c81` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(2) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/m1_m2_census.py` | script de diagnóstico | `b3bdaa1` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/m2b_peak_to_valley.py` | script de diagnóstico | `b3bdaa1` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/m3_force_peak.py` | script de diagnóstico | `b3bdaa1` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/m4_20180608_H.py` | script de diagnóstico | `b3bdaa1` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/m5_boundary_independence.py` | script de diagnóstico | `b3bdaa1` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log` | saída gerada | `8f55c81` 2026-09-23 | sim — log da figura de 20190639 (blocos C2 vs rótulo) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_blocks.csv` | saída gerada | `8f55c81` 2026-09-23 | sim — blocos de 20190639: rótulo, base, C2 | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/fig_20190639.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_boundaries.csv` | saída gerada | `8f55c81` 2026-09-23 | sim — erro por fronteira de 20190639: base vs C2 | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_c2.png` | saída gerada | `8f55c81` 2026-09-23 | sim — figura de 20190639 sob C2 | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/fig_20190639.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.json` | saída gerada | `740b994` 2026-09-23 | sim — impressão digital do tree com a flag desligada | diag/frontA_idx0_c2/outputs/fp_cur_off.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log` | saída gerada | `740b994` 2026-09-23 | sim — log da impressão digital (flag off) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.json` | saída gerada | `740b994` 2026-09-23 | sim — impressão digital do tree com a flag ligada | diag/frontA_idx0_c2/outputs/fp_cur_on.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log` | saída gerada | `740b994` 2026-09-23 | sim — log da impressão digital (flag on) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.json` | saída gerada | `740b994` 2026-09-23 | sim — impressão digital de referência (c714451) para o gate da etapa 2 | diag/frontA_idx0_c2/outputs/fp_ref_c714451.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429`, `docs/future_work.md:3108` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.log` | saída gerada | `740b994` 2026-09-23 | sim — log da impressão digital de referência | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log` | saída gerada | `b3bdaa1` 2026-09-23 | sim — M1/M2: como a proeminência do idx0 é computada e onde C2 dispararia | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:114`, `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:156` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2_c2_table.csv` | saída gerada | `b3bdaa1` 2026-09-23 | sim — tabela por série de onde C2 dispara | diag/frontA_idx0_c2/REPORT.md(3), diag/frontA_idx0_c2/m1_m2_census.py(2), diag/frontA_idx0_c2/outputs/m1_m2_census.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:156` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.csv` | saída gerada | `b3bdaa1` 2026-09-23 | sim — o ramo peak->valley de C2 onde dispara (20190639) | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/m2b_peak_to_valley.py(1), diag/frontA_idx0_c2/outputs/m2b_peak_to_valley.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:261` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log` | saída gerada | `b3bdaa1` 2026-09-23 | sim — log do adendo M2 (ramo peak->valley) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:261` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.csv` | saída gerada | `b3bdaa1` 2026-09-23 | sim — M3: forçar idx0 a peak sob params-13 | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/m3_force_peak.py(1), diag/frontA_idx0_c2/outputs/m3_force_peak.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log` | saída gerada | `b3bdaa1` 2026-09-23 | sim — log de M3 | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.png` | saída gerada | `b3bdaa1` 2026-09-23 | sim — figura de M3 | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/m3_force_peak.py(1), diag/frontA_idx0_c2/outputs/m3_force_peak.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.csv` | saída gerada | `b3bdaa1` 2026-09-23 | sim — M4: a sobrescrita incipient (defeito H) mascara o efeito em 20180608 | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/m4_20180608_H.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log` | saída gerada | `b3bdaa1` 2026-09-23 | sim — log de M4 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.png` | saída gerada | `b3bdaa1` 2026-09-23 | sim — figura de M4 | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/m4_20180608_H.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_head.csv` | saída gerada | `b3bdaa1` 2026-09-23 | sim — cabeça da série 20180608 antes/depois de H (M4) | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/m4_20180608_H.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.csv` | saída gerada | `b3bdaa1` 2026-09-23 | sim — M5: a fronteira incipient não depende do mapa de fases | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/m5_boundary_independence.py(1), diag/frontA_idx0_c2/outputs/m5_boundary_independence.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:314`, `docs/future_work.md:3048` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log` | saída gerada | `b3bdaa1` 2026-09-23 | sim — log de M5 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:314` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_changed_series.png` | saída gerada | `740b994` 2026-09-23 | sim — figura das séries alteradas pela regra C2' | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/stage2_gate.log(1), diag/frontA_idx0_c2/stage2_gate.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.csv` | saída gerada | `740b994` 2026-09-23 | sim — sob os defaults do pacote a nova regra não muda nada | diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/outputs/stage2_defaults_check.log(1), diag/frontA_idx0_c2/stage2_defaults_check.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `docs/future_work.md:3131` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log` | saída gerada | `740b994` 2026-09-23 | sim — log da checagem sob defaults do pacote | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `docs/future_work.md:3131` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log` | saída gerada | `e97eb17` 2026-09-24 | sim — gate da etapa 2 (Q1–Q8) — PASS | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429`, `docs/future_work.md:3083` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_table.csv` | saída gerada | `e97eb17` 2026-09-24 | sim — tabela por série da etapa 2 (dispara, ramo, sequências off/on) | diag/frontA_idx0_c2/REPORT.md(2), diag/frontA_idx0_c2/outputs/stage2_gate.log(1), diag/frontA_idx0_c2/stage2_gate.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:467` |
| `research/labels/diagnostics/frontA_idx0_c2/stage2_defaults_check.py` | script de diagnóstico | `740b994` 2026-09-23 | não | CHANGELOG.md(1), diag/frontA_idx0_c2/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/stage2_gate.py` | script de diagnóstico | `e97eb17` 2026-09-24 | não | diag/frontA_idx0_c2/REPORT.md(2), docs/future_work.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_idx0_c2/stage2_reference.py` | script de diagnóstico | `740b994` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(2), docs/future_work.md(1), diag/frontA_idx0_c2/stage2_gate.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |

### `research/labels/diagnostics/frontA_reverify`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/frontA_reverify/REPORT.md` | registro/relatório | `077d273` 2026-09-23 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S03 | `docs/future_work.md:2784` |
| `research/labels/diagnostics/frontA_reverify/attribute_params.py` | script de diagnóstico | `077d273` 2026-09-23 | não | diag/frontA_reverify/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontA_reverify/census_tip.py` | script de diagnóstico | `077d273` 2026-09-23 | não | diag/frontA_reverify/outputs/1b_census.log(5), docs/future_work.md(1), diag/frontA_reverify/REPORT.md(1), diag/frontA_reverify/compare_against_A.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_reverify/compare_1a.py` | script de diagnóstico | `077d273` 2026-09-23 | não | diag/frontA_reverify/REPORT.md(2), docs/future_work.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_reverify/compare_against_A.py` | script de diagnóstico | `077d273` 2026-09-23 | não | diag/frontA_reverify/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_final_output_check.log` | saída gerada | `077d273` 2026-09-23 | sim — log (proveniência + corpo) da regeneração do final_output_check no passo 1a | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_idx0_inventory.log` | saída gerada | `077d273` 2026-09-23 | sim — log da regeneração do inventário idx0 no passo 1a | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_capture_pipeline_state.log` | saída gerada | `077d273` 2026-09-23 | sim — log da captura do estado do pipeline no passo 1a | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_eval_raw.log` | saída gerada | `077d273` 2026-09-23 | sim — saída do avaliador no passo 1a (reprodução de A) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_gate.log` | saída gerada | `077d273` 2026-09-23 | sim — gate 1a: reprodução campo a campo dos artefatos de A — PASS | diag/frontA_reverify/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135`, `docs/future_work.md:2799` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log` | saída gerada | `077d273` 2026-09-23 | sim — censo do passo 1b na ponta com params-9 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179`, `docs/future_work.md:2817` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_diff_vs_A.log` | saída gerada | `077d273` 2026-09-23 | sim — diff por trajetória contra A no passo 1b: nenhuma diferença | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:195`, `docs/future_work.md:2817` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_eval_params9.log` | saída gerada | `077d273` 2026-09-23 | sim — avaliador na ponta com params-9 (incipient, recusa) idêntico a A | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `docs/future_work.md:2827` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_attribution.log` | saída gerada | `077d273` 2026-09-23 | sim — atribuição chave-a-chave da perda de mature em 20191014 a mature_min_depth | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:239`, `docs/future_work.md:2837` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log` | saída gerada | `077d273` 2026-09-23 | sim — censo do passo 2 com params-13 | diag/frontA_idx0_c2/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213`, `docs/future_work.md:2817` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_diff_vs_A.log` | saída gerada | `077d273` 2026-09-23 | sim — diff contra A no passo 2 (params-13): nenhuma diferença | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:220` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_final_output_check.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela regenerada final_output_check (passo 1a) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_fix_eval_before.txt` | saída gerada | `077d273` 2026-09-23 | sim — avaliação regenerada 'antes do fix' de A (passo 1a) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0_final_stage.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela regenerada idx0_final_stage (passo 1a) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0_inventory.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela regenerada idx0_inventory (passo 1a) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0b_prominence.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela regenerada idx0b_prominence (passo 1a) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_V_table.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela V (primeira fase não-incipient) sob params-9 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0_final_stage.csv` | saída gerada | `077d273` 2026-09-23 | sim — idx0_final_stage sob params-9 (passo 1b) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0_inventory.csv` | saída gerada | `077d273` 2026-09-23 | sim — idx0_inventory sob params-9 (passo 1b) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0b_prominence.csv` | saída gerada | `077d273` 2026-09-23 | sim — idx0b_prominence sob params-9 (passo 1b) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_attribution.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela da atribuição chave-a-chave (passo 2) | diag/frontA_reverify/attribute_params.py(1), diag/frontA_reverify/outputs/2_attribution.log(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:239` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_V_table.csv` | saída gerada | `077d273` 2026-09-23 | sim — tabela V sob params-13 | diag/frontA_reverify/attribute_params.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0_final_stage.csv` | saída gerada | `077d273` 2026-09-23 | sim — idx0_final_stage sob params-13 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0_inventory.csv` | saída gerada | `077d273` 2026-09-23 | sim — idx0_inventory sob params-13 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0b_prominence.csv` | saída gerada | `077d273` 2026-09-23 | sim — idx0b_prominence sob params-13 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S03 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/run_in_worktree.py` | script de diagnóstico | `077d273` 2026-09-23 | não | diag/frontA_reverify/REPORT.md(3), docs/future_work.md(1), diag/frontA_idx0_c2/REPORT.md(1) | **manter** | modelo de execução em worktree com assert de cyclophaser.__file__ (regra fixa) | — | — |

### `research/labels/diagnostics/frontC`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/frontC/REPORT.md` | registro/relatório | `a284209` 2026-09-22 | sim — relatório de frente fechada (achados, previsões, veredito) | — | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S05 | `docs/future_work.md:2334` |
| `research/labels/diagnostics/frontC/d2_segments.csv` | saída gerada | `9c0d80e` 2026-09-22 | sim — segmentos de intensificação e sua profundidade D2 (separação no treino) | diag/frontC/d2_separation.py(2), docs/future_work.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S05 | `research/labels/diagnostics/frontC/REPORT.md:41`, `docs/future_work.md:2366` |
| `research/labels/diagnostics/frontC/d2_segments.json` | saída gerada | `9c0d80e` 2026-09-22 | sim — mesmos segmentos D2, formato bruto | diag/frontC/d2_separation.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S05 | `docs/future_work.md:2366` |
| `research/labels/diagnostics/frontC/d2_separation.py` | script de diagnóstico | `9c0d80e` 2026-09-22 | não | docs/future_work.md(1), diag/frontC/REPORT.md(1), diag/frontC/report_test_series.py(1), diag/item31/DESIGN.md(1), +2 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontC/default_equivalence.py` | script de diagnóstico | `e1b29cc` 2026-09-22 | não | docs/future_work.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontC/fig_20180654_before_after.png` | saída gerada | `9c0d80e` 2026-09-22 | sim — antes/depois do piso de intensificação em 20180654 | diag/frontC/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S05 | `research/labels/diagnostics/frontC/REPORT.md:41` |
| `research/labels/diagnostics/frontC/fig_20180733_before_after.png` | saída gerada | `9c0d80e` 2026-09-22 | sim — antes/depois do piso de intensificação em 20180733 | diag/frontC/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S05 | `research/labels/diagnostics/frontC/REPORT.md:41` |
| `research/labels/diagnostics/frontC/make_figures.py` | script de diagnóstico | `9c0d80e` 2026-09-22 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontC/measure_frontC.py` | script de diagnóstico | `9c0d80e` 2026-09-22 | não | diag/frontC/REPORT.md(2), docs/future_work.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), +1 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontC/measurements.json` | saída gerada | `9c0d80e` 2026-09-22 | sim — medições brutas de treino params-12 → params-13 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S05 | `research/labels/diagnostics/frontC/REPORT.md:41`, `docs/future_work.md:2334` |
| `research/labels/diagnostics/frontC/report_test_series.py` | script de diagnóstico | `9c0d80e` 2026-09-22 | não | docs/future_work.md(1), diag/frontC/REPORT.md(1), diag/frontC/make_figures.py(1), diag/frontC/measure_frontC.py(1), +3 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |

### `research/labels/diagnostics/frontD`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/frontD/REPORT.md` | registro/relatório | `80e0551` 2026-09-23 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(2) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S02 | `docs/future_work.md:2519` |
| `research/labels/diagnostics/frontD/anchoring.json` | saída gerada | `23fd778` 2026-09-23 | sim — teste de ancoragem artefato vs fase real (C1) | diag/frontD/anchoring.py(2), diag/frontD/REPORT.md(1), diag/frontD/anchoring.txt(1), diag/frontD/make_figures.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:158` |
| `research/labels/diagnostics/frontD/anchoring.py` | script de diagnóstico | `23fd778` 2026-09-23 | não | diag/frontD/REPORT.md(2), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontD/anchoring.txt` | saída gerada | `23fd778` 2026-09-23 | sim — teste de ancoragem artefato vs fase real (C1) | diag/frontD/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:158` |
| `research/labels/diagnostics/frontD/census.json` | saída gerada | `23fd778` 2026-09-23 | sim — censo incipient do treino sob params-13 | diag/frontD/REPORT.md(3), docs/future_work.md(2), diag/frontD/census.py(2), diag/item31/future_work_numbers.py(2), +5 | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:61` |
| `research/labels/diagnostics/frontD/census.py` | script de diagnóstico | `23fd778` 2026-09-23 | não | diag/frontD/REPORT.md(2), diag/item31/DESIGN.md(2), diag/frontA_idx0_c2/REPORT.md(1), diag/frontA_idx0_c2/m1_m2_census.py(1), +3 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontD/census.txt` | saída gerada | `23fd778` 2026-09-23 | sim — censo incipient do treino sob params-13 | diag/item31/DESIGN.md(2), diag/item31/test_label_census.py(2), diag/frontD/REPORT.md(1), diag/item31/stage1_run.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:61` |
| `research/labels/diagnostics/frontD/constant_baseline.json` | saída gerada | `23fd778` 2026-09-23 | sim — baseline constante para o fim do incipient | diag/frontD/constant_baseline.py(2), diag/frontD/REPORT.md(1), diag/frontD/constant_baseline.txt(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:308` |
| `research/labels/diagnostics/frontD/constant_baseline.py` | script de diagnóstico | `23fd778` 2026-09-23 | não | diag/frontD/REPORT.md(3), docs/future_work.md(2), diag/item31/constant_train.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontD/constant_baseline.txt` | saída gerada | `23fd778` 2026-09-23 | sim — baseline constante para o fim do incipient | diag/frontD/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:308` |
| `research/labels/diagnostics/frontD/evaluate_params13_train.txt` | saída gerada | `23fd778` 2026-09-23 | sim — saída do avaliador (treino, params-13) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:243` |
| `research/labels/diagnostics/frontD/fig_*_opening.png` — **7 arquivos** (`git ls-files 'research/labels/diagnostics/frontD/fig_*_opening.png'`) | saída gerada | `23fd778` 2026-09-23 | sim — figuras da abertura das séries C1 (bruta e filtrada) | diag/frontD/REPORT.md(4) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:361` |
| `research/labels/diagnostics/frontD/make_figures.py` | script de diagnóstico | `23fd778` 2026-09-23 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontD/verify_hashes.py` | script de diagnóstico | `23fd778` 2026-09-23 | não | diag/frontD/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontD/verify_hashes.txt` | saída gerada | `23fd778` 2026-09-23 | sim — verificação dos hashes antes de medir — PASS | diag/frontD/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontD/REPORT.md:29` |

### `research/labels/diagnostics/frontRefusal`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/frontRefusal/REPORT.md` | registro/relatório | `edb1a99` 2026-09-23 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(2) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S02 | `docs/future_work.md:2662` |
| `research/labels/diagnostics/frontRefusal/classification.json` | saída gerada | `d1e243c` 2026-09-23 | sim — classificação das recusas por causa (M1>M2>M3) | diag/frontRefusal/classify.py(2), diag/frontRefusal/classification.txt(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:170` |
| `research/labels/diagnostics/frontRefusal/classification.txt` | saída gerada | `d1e243c` 2026-09-23 | sim — classificação por causa; contagem do defeito I no conjunto | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:170`, `docs/future_work.md:672` |
| `research/labels/diagnostics/frontRefusal/classify.py` | script de diagnóstico | `d1e243c` 2026-09-23 | não | — | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontRefusal/diagnose.py` | script de diagnóstico | `d1e243c` 2026-09-23 | não | diag/frontRefusal/REPORT.md(4), diag/frontRefusal/separability.py(2), docs/future_work.md(1), diag/frontRefusal/make_figures.py(1), +3 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontRefusal/evaluate_params13_train.txt` | saída gerada | `d1e243c` 2026-09-23 | sim — saída do avaliador (treino, params-13) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:46` |
| `research/labels/diagnostics/frontRefusal/fig_*_refusal.png` — **6 arquivos** (`git ls-files 'research/labels/diagnostics/frontRefusal/fig_*_refusal.png'`) | saída gerada | `d1e243c` 2026-09-23 | sim — figuras das séries recusadas | diag/frontRefusal/REPORT.md(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:155` |
| `research/labels/diagnostics/frontRefusal/make_figures.py` | script de diagnóstico | `d1e243c` 2026-09-23 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/frontRefusal/refusal.json` | saída gerada | `d1e243c` 2026-09-23 | sim — caminhos de recusa por série | diag/frontRefusal/diagnose.py(2), diag/frontRefusal/make_figures.py(2), diag/frontRefusal/separability.py(2), diag/frontRefusal/REPORT.md(1), +3 | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:67` |
| `research/labels/diagnostics/frontRefusal/refusal.txt` | saída gerada | `d1e243c` 2026-09-23 | sim — caminhos de recusa e as seis séries | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:102` |
| `research/labels/diagnostics/frontRefusal/separability.json` | saída gerada | `d1e243c` 2026-09-23 | sim — separabilidade da recusa por tau | diag/frontRefusal/separability.py(2), diag/frontRefusal/separability.txt(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:201` |
| `research/labels/diagnostics/frontRefusal/separability.py` | script de diagnóstico | `d1e243c` 2026-09-23 | não | — | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontRefusal/separability.txt` | saída gerada | `d1e243c` 2026-09-23 | sim — separabilidade da recusa por tau | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:201` |
| `research/labels/diagnostics/frontRefusal/tau_sweep.json` | saída gerada | `edb1a99` 2026-09-23 | sim — varredura completa de tau: nenhum tau leva o bastante à tolerância | diag/frontRefusal/tau_sweep.py(2), docs/future_work.md(1), diag/frontRefusal/REPORT.md(1), diag/frontRefusal/tau_sweep.txt(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:334` |
| `research/labels/diagnostics/frontRefusal/tau_sweep.py` | script de diagnóstico | `edb1a99` 2026-09-23 | não | docs/future_work.md(1), diag/frontRefusal/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/frontRefusal/tau_sweep.txt` | saída gerada | `edb1a99` 2026-09-23 | sim — varredura completa de tau | docs/future_work.md(1), diag/frontRefusal/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S02 | `research/labels/diagnostics/frontRefusal/REPORT.md:334` |

### `research/labels/diagnostics/front_b`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/front_b/ADDENDUM_part1b.md` | registro/relatório | `a284209` 2026-09-22 | sim — relatório de frente fechada (achados, previsões, veredito) | research/inert_params/REPORT_inertia_sweep.md(1), diag/front_b/REPORT_front_b_part1.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S06 | `docs/future_work.md:1564` |
| `research/labels/diagnostics/front_b/REPORT_front_b_part1.md` | registro/relatório | `a284209` 2026-09-22 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1), research/inert_params/REPORT_inertia_sweep.md(1), diag/front_b/ADDENDUM_part1b.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S06 | `docs/future_work.md:1564` |
| `research/labels/diagnostics/front_b/collect_train_diagnostics.py` | script de diagnóstico | `4c0767c` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/front_b/default_behaviour_hash.py` | script de diagnóstico | `a284209` 2026-09-22 | não | docs/future_work.md(2), diag/frontC/default_equivalence.py(2), diag/front_b/ADDENDUM_part1b.md(2), diag/front_b/default_behaviour_sha256.txt(2), +7 | **manter** | gerador canônico do digest default (linha de base de toda frente) | — | — |
| `research/labels/diagnostics/front_b/default_behaviour_sha256.txt` | saída gerada | `06d8550` 2026-09-28 | sim — histórico do digest default por commit/ambiente | diag/front_b/ADDENDUM_part1b.md(3), diag/front_b/REPORT_front_b_part1.md(3), CHANGELOG.md(2), diag/front_b/report_headroom.py(2), +3 | **manter** | livro-razão do gerador canônico (o script anexa registros a ele) | — | — |
| `research/labels/diagnostics/front_b/distance_sweep.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — varredura de `distance` nas séries de treino: parâmetro inerte na referência | diag/front_b/ADDENDUM_part1b.md(2), diag/front_b/sweep_distance.py(2), docs/future_work.md(1), research/inert_params/REPORT_inertia_sweep.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33`, `docs/future_work.md:1564` |
| `research/labels/diagnostics/front_b/headroom_and_hash.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — folga de `distance` e primeiro registro do digest default | diag/front_b/report_headroom.py(2), diag/front_b/ADDENDUM_part1b.md(1), diag/front_b/REPORT_front_b_part1.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:267` |
| `research/labels/diagnostics/front_b/mature_pairing_audit.py` | script de diagnóstico | `7fbda56` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(2) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/front_b/mature_pairing_audit.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — o que o n do pareamento mature conta e o que foi excluído | diag/front_b/ADDENDUM_part1b.md(2), diag/front_b/mature_pairing_audit.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:86` |
| `research/labels/diagnostics/front_b/reference_score_attribution.py` | script de diagnóstico | `4c0767c` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(2), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/front_b/reference_score_attribution.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — proveniência de cada número de referência (armadilha de atribuição) | diag/front_b/ADDENDUM_part1b.md(2), diag/front_b/reference_score_attribution.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:149` |
| `research/labels/diagnostics/front_b/report_headroom.py` | script de diagnóstico | `7fbda56` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/front_b/report_targets.py` | script de diagnóstico | `7fbda56` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/front_b/report_train_aggregate.py` | script de diagnóstico | `7fbda56` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/front_b/sensitivity.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — sonda causal: sensibilidade das fases a `distance`/`length_scale` | docs/future_work.md(1), diag/front_b/ADDENDUM_part1b.md(1), diag/front_b/REPORT_front_b_part1.md(1), diag/front_b/sensitivity_probe.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:223` |
| `research/labels/diagnostics/front_b/sensitivity_probe.py` | script de diagnóstico | `4c0767c` 2026-09-16 | não | diag/front_b/ADDENDUM_part1b.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/front_b/sweep_distance.py` | script de diagnóstico | `4c0767c` 2026-09-16 | sim — docstring registra a menor folga sobrevivente e em que série | diag/front_b/ADDENDUM_part1b.md(3), research/inert_params/REPORT_inertia_sweep.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), +1 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | S06 | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:68` |
| `research/labels/diagnostics/front_b/target_tracks.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — as duas trajetórias-alvo: janelas mature e extremos antes/depois do filtro | diag/front_b/ADDENDUM_part1b.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:100` |
| `research/labels/diagnostics/front_b/topology_run_gate_excerpt.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — trecho do gate de topologia citado como referência (score de pacote) | diag/front_b/ADDENDUM_part1b.md(2), docs/future_work.md(1), diag/front_b/reference_score_attribution.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:149` |
| `research/labels/diagnostics/front_b/train_aggregate.txt` | saída gerada | `7fbda56` 2026-09-16 | sim — agregado do split de treino sob a config de referência da época | diag/front_b/report_train_aggregate.py(2), diag/front_b/ADDENDUM_part1b.md(1), diag/front_b/REPORT_front_b_part1.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:193` |
| `research/labels/diagnostics/front_b/train_raw.json` | saída gerada | `7fbda56` 2026-09-16 | sim — dados brutos por série do diagnóstico de treino | diag/front_b/ADDENDUM_part1b.md(2), diag/front_b/collect_train_diagnostics.py(2), diag/front_b/REPORT_front_b_part1.md(1), diag/front_b/mature_pairing_audit.py(1), +3 | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S06 | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:193` |

### `research/labels/diagnostics/item19`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/item19/PROVENANCE.md` | registro/relatório | `0541a54` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item19/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1640` |
| `research/labels/diagnostics/item19/REPORT.md` | registro/relatório | `f376a03` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1640` |
| `research/labels/diagnostics/item19/closeout_measurements.py` | script de diagnóstico | `f376a03` 2026-09-17 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item19/closeout_measurements.txt` | saída gerada | `f376a03` 2026-09-17 | sim — as três medições de fechamento pedidas na revisão | diag/item19/closeout_measurements.py(2), diag/item19/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:405` |
| `research/labels/diagnostics/item19/evaluate_params10_train.txt` | saída gerada | `0541a54` 2026-09-17 | sim — saída do avaliador (treino, params-10) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:45` |
| `research/labels/diagnostics/item19/fig_20160735_params10.png` | saída gerada | `0541a54` 2026-09-17 | sim — figura de 20160735 sob params-10 | diag/item19/stage1_describe.py(2), diag/item19/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:41` |
| `research/labels/diagnostics/item19/fig_prominence_distributions.png` | saída gerada | `0541a54` 2026-09-17 | sim — distribuições de proeminência relativa | diag/item19/stage1_describe.py(3), diag/item19/REPORT.md(1), diag/item19/stage1_prominence.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:92` |
| `research/labels/diagnostics/item19/fig_tradeoff_pr060_maf090.png` | saída gerada | `0541a54` 2026-09-17 | sim — o trade-off desenhado | diag/item19/REPORT.md(2), diag/item19/stage2_tradeoff_figure.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:207` |
| `research/labels/diagnostics/item19/item19_core.py` | script de diagnóstico | `a5067df` 2026-09-28 | não | docs/future_work.md(3), diag/item20a/BLOCKER_pairing_rule.md(3), diag/item20a/REPORT.md(3), diag/item20a/measure_20a.py(2), +9 | **manter** | importado pelo app (benchmark_core: pair_by_overlap, MARGIN) — medidor vivo | — | — |
| `research/labels/diagnostics/item19/stage1_baseline.txt` | saída gerada | `0541a54` 2026-09-17 | sim — baseline constante do estágio 1 | diag/item19/stage1_describe.py(3), diag/item19/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:76` |
| `research/labels/diagnostics/item19/stage1_describe.py` | script de diagnóstico | `0541a54` 2026-09-17 | não | diag/item19/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item19/stage1_per_series.md` | registro/relatório | `0541a54` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item19/stage1_describe.py(3), diag/item19/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1640` |
| `research/labels/diagnostics/item19/stage1_prominence.md` | registro/relatório | `0541a54` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item19/stage1_describe.py(3), diag/item19/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1640` |
| `research/labels/diagnostics/item19/stage2_cells.json` | saída gerada | `0541a54` 2026-09-17 | sim — grade de 45 células, bruto | diag/item19/stage2_grid.py(2), diag/item19/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item19/REPORT.md:143`, `docs/future_work.md:1731` |
| `research/labels/diagnostics/item19/stage2_grid.md` | registro/relatório | `0541a54` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item19/stage2_grid.py(3), diag/item19/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1640` |
| `research/labels/diagnostics/item19/stage2_grid.py` | script de diagnóstico | `0541a54` 2026-09-17 | não | diag/item19/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item19/stage2_losses.md` | registro/relatório | `0541a54` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item19/stage2_grid.py(3), diag/item19/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1640` |
| `research/labels/diagnostics/item19/stage2_tradeoff_figure.py` | script de diagnóstico | `0541a54` 2026-09-17 | não | diag/item19/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |

### `research/labels/diagnostics/item20a`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md` | registro/relatório | `9477132` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1), diag/item20a/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1830` |
| `research/labels/diagnostics/item20a/REPORT.md` | registro/relatório | `2b27ed0` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | — | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1830` |
| `research/labels/diagnostics/item20a/evaluate_params10_train.txt` | saída gerada | `2b27ed0` 2026-09-17 | sim — avaliador params-10 (antes) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20a/REPORT.md:38` |
| `research/labels/diagnostics/item20a/evaluate_params11_train.txt` | saída gerada | `2b27ed0` 2026-09-17 | sim — avaliador params-11 (depois) | diag/item20a/REPORT.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20a/REPORT.md:52` |
| `research/labels/diagnostics/item20a/measure_20a.py` | script de diagnóstico | `2b27ed0` 2026-09-17 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item20a/measurements.json` | saída gerada | `2b27ed0` 2026-09-17 | sim — medições brutas params-10 vs params-11 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20a/REPORT.md:107` |
| `research/labels/diagnostics/item20a/tables.md` | registro/relatório | `2b27ed0` 2026-09-17 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item20a/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:1830` |

### `research/labels/diagnostics/item20b`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/item20b/REPORT.md` | registro/relatório | `eb19304` 2026-09-21 | sim — relatório de frente fechada (achados, previsões, veredito) | — | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:2140` |
| `research/labels/diagnostics/item20b/REPORT_stage2.md` | registro/relatório | `b026147` 2026-09-21 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S04 | `docs/future_work.md:2140` |
| `research/labels/diagnostics/item20b/analyse_20b.py` | script de diagnóstico | `eb19304` 2026-09-21 | não | diag/item20b/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item20b/analyse_20b.txt` | saída gerada | `eb19304` 2026-09-21 | sim — números do relatório do estágio 1 (profundidade dos vales) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT.md:145`, `docs/future_work.md:2146` |
| `research/labels/diagnostics/item20b/default_equivalence.py` | script de diagnóstico | `b026147` 2026-09-21 | não | diag/frontC/default_equivalence.py(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item20b/defectH_watch.txt` | saída gerada | `b026147` 2026-09-21 | sim — vigia do defeito H durante o piso de mature | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT_stage2.md:227` |
| `research/labels/diagnostics/item20b/denominator_robustness.txt` | saída gerada | `b026147` 2026-09-21 | sim — robustez do denominador de D1 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT_stage2.md:250` |
| `research/labels/diagnostics/item20b/depth_table.csv` | saída gerada | `eb19304` 2026-09-21 | sim — tabela dos vales geradores e suas profundidades | diag/item20b/REPORT.md(2), diag/item20b/measure_20b.py(2), docs/future_work.md(1), diag/item20b/analyse_20b.txt(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT.md:145` |
| `research/labels/diagnostics/item20b/fig_20160735_before_after.png` | saída gerada | `b026147` 2026-09-21 | sim — antes/depois de mature_min_depth em 20160735 | diag/item20b/REPORT_stage2.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT_stage2.md:114` |
| `research/labels/diagnostics/item20b/fig_20205386_before_after.png` | saída gerada | `b026147` 2026-09-21 | sim — antes/depois de mature_min_depth em 20205386 | diag/item20b/REPORT_stage2.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT_stage2.md:112` |
| `research/labels/diagnostics/item20b/gate_stage2.py` | script de diagnóstico | `b026147` 2026-09-21 | não | diag/frontC/REPORT.md(1), diag/frontC/measure_frontC.py(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), +1 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item20b/gate_stage2.txt` | saída gerada | `b026147` 2026-09-21 | sim — gate (a)–(f) do estágio 2 — PASS | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT_stage2.md:191`, `docs/future_work.md:2191` |
| `research/labels/diagnostics/item20b/make_figures.py` | script de diagnóstico | `b026147` 2026-09-21 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item20b/measure_20b.py` | script de diagnóstico | `eb19304` 2026-09-21 | não | diag/item20b/REPORT.md(2), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item20b/measurements.json` | saída gerada | `eb19304` 2026-09-21 | sim — dump por série do estágio 1 | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT.md:49` |
| `research/labels/diagnostics/item20b/stage2_measurements.json` | saída gerada | `b026147` 2026-09-21 | sim — dump do gate do estágio 2 | diag/item20b/gate_stage2.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT_stage2.md:191` |
| `research/labels/diagnostics/item20b/supplement_20b.py` | script de diagnóstico | `eb19304` 2026-09-21 | não | diag/item20b/REPORT.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item20b/supplement_20b.txt` | saída gerada | `eb19304` 2026-09-21 | sim — conteúdo DC da série que alimenta mature; recontagem | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S04 | `research/labels/diagnostics/item20b/REPORT.md:96` |

### `research/labels/diagnostics/item30`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/item30/PREDICTIONS.md` | registro/relatório | `f01ca88` 2026-09-25 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item30/REPORT.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/PREDICTIONS_part2.md` | registro/relatório | `2ded3af` 2026-09-26 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item30/REPORT_part2.md(1), diag/item30/separability.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/PREDICTIONS_part3.md` | registro/relatório | `84f7c89` 2026-09-27 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item30/REPORT_part3.md(1), diag/item30/part3_measure.py(1), research/labels/labels_core.py(1), research/labels/swell_item30/freeze_validation_batch.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/REPORT.md` | registro/relatório | `002078b` 2026-09-25 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1), research/labels/swell_item30/README.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/REPORT_figs_cf.md` | registro/relatório | `1a3ad76` 2026-09-27 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item30/figs_cf.py(2), research/labels/swell_item30/adjudicate_item30.py(2), docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/REPORT_part2.md` | registro/relatório | `99f5a9a` 2026-09-26 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/REPORT_part3.md` | registro/relatório | `2319609` 2026-09-27 | sim — relatório de frente fechada (achados, previsões, veredito) | docs/future_work.md(2), diag/item30/part3_measure.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S07 | `docs/future_work.md:3380` |
| `research/labels/diagnostics/item30/census_train.py` | script de diagnóstico | `002078b` 2026-09-25 | não | diag/item30/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item30/census_train_params14.csv` | saída gerada | `002078b` 2026-09-25 | sim — censo de treino sob params-14 | diag/item30/REPORT.md(2), diag/item30/census_train.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT.md:184` |
| `research/labels/diagnostics/item30/evaluate_params14_train_batch.txt` | saída gerada | `002078b` 2026-09-25 | sim — avaliador params-14 com lote | diag/item30/REPORT.md(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT.md:118` |
| `research/labels/diagnostics/item30/figs_cf.py` | script de diagnóstico | `4e674b2` 2026-09-27 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1), research/labels/swell_item30/adjudicate_item30.py(1), +1 | **manter** | importado por teste vivo (tests/test_item30_spare_intensification.py) | — | — |
| `research/labels/diagnostics/item30/figs_cf/*.png` — **9 arquivos** (`git ls-files 'research/labels/diagnostics/item30/figs_cf/*.png'`) | saída gerada | `1a3ad76` 2026-09-27 | sim — figuras rótulo × params-13 × params-14 × contrafactual (treino) | diag/item30/figs_cf.py(3), diag/item30/REPORT_figs_cf.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_figs_cf.md:3`, `docs/future_work.md:3504` |
| `research/labels/diagnostics/item30/figs_cf_output.txt` | saída gerada | `1a3ad76` 2026-09-27 | sim — tabela rótulo × params-14 × contrafactual para os 8 casos | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_figs_cf.md:1` |
| `research/labels/diagnostics/item30/figs_part3/*.png` — **6 arquivos** (`git ls-files 'research/labels/diagnostics/item30/figs_part3/*.png'`) | saída gerada | `c6abe5e` 2026-09-27 | sim — antes/depois dos 5 adjudicados | diag/item30/part3_measure.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:123` |
| `research/labels/diagnostics/item30/item30_core.py` | script de diagnóstico | `ce1b74b` 2026-09-26 | não | diag/item30/REPORT.md(2) | **manter** | importado por teste vivo (tests/test_item30_spare_intensification.py) | — | — |
| `research/labels/diagnostics/item30/outside_signal.py` | script de diagnóstico | `4e674b2` 2026-09-27 | sim — docstring registra quantas trajetórias swell a regra muda | diag/item30/REPORT_part3.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:45` |
| `research/labels/diagnostics/item30/outside_signal_output.txt` | saída gerada | `4e674b2` 2026-09-27 | sim — as 5 fora do sinal e a variante estreita (medida, não adotada) | diag/item30/REPORT_part3.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:130` |
| `research/labels/diagnostics/item30/part3_eval_params14.txt` | saída gerada | `c6abe5e` 2026-09-27 | sim — avaliador params-14 (parte 3) | diag/item30/part3_measure.py(2), diag/item30/REPORT_part3.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:57` |
| `research/labels/diagnostics/item30/part3_eval_params15.txt` | saída gerada | `c6abe5e` 2026-09-27 | sim — avaliador params-15 (parte 3) | diag/item30/part3_measure.py(2), diag/item30/REPORT_part3.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:57` |
| `research/labels/diagnostics/item30/part3_measure.py` | script de diagnóstico | `c6abe5e` 2026-09-27 | não | diag/item30/REPORT_part3.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item30/part3_measure_output.txt` | saída gerada | `c6abe5e` 2026-09-27 | sim — medição da parte 3 (predições R1..) | diag/item30/REPORT_part3.md(1), diag/item30/part3_measure.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:29` |
| `research/labels/diagnostics/item30/post_merge_checks.py` | script de diagnóstico | `6f956fc` 2026-09-27 | não | docs/future_work.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item30/post_merge_checks_output.txt` | saída gerada | `6f956fc` 2026-09-27 | sim — checagens pós-merge: avaliador e 51 séries idênticos | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `docs/future_work.md:3619` |
| `research/labels/diagnostics/item30/prove_defaults_30c.py` | script de diagnóstico | `395d607` 2026-09-26 | não | docs/future_work.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item30/prove_defaults_30c.txt` | saída gerada | `395d607` 2026-09-26 | sim — 30c não muda caminhos default | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `docs/future_work.md:3800` |
| `research/labels/diagnostics/item30/prove_defaults_part3.py` | script de diagnóstico | `d1841cc` 2026-09-27 | não | diag/item30/REPORT_part3.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item30/prove_defaults_part3_checkpoint.txt` | saída gerada | `4e674b2` 2026-09-27 | sim — parte 3 não muda caminhos default (checkpoint) | diag/item30/REPORT_part3.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:191` |
| `research/labels/diagnostics/item30/prove_defaults_part3_step2.txt` | saída gerada | `d1841cc` 2026-09-27 | sim — parte 3 não muda caminhos default (passo 2) | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:125` |
| `research/labels/diagnostics/item30/prove_defaults_part3_step3.txt` | saída gerada | `c6abe5e` 2026-09-27 | sim — parte 3 não muda caminhos default (passo 3) | diag/item30/REPORT_part3.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part3.md:42` |
| `research/labels/diagnostics/item30/prove_evaluator_default.py` | script de diagnóstico | `002078b` 2026-09-25 | não | diag/item30/REPORT.md(2), diag/item30/prove_defaults_30c.py(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), +1 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item30/separability.py` | script de diagnóstico | `99f5a9a` 2026-09-26 | não | diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **manter** | importado por teste vivo via figs_cf (sep.candidates) | — | — |
| `research/labels/diagnostics/item30/separability_criterion.json` | saída gerada | `99f5a9a` 2026-09-26 | sim — critério de separabilidade declarado | diag/item30/REPORT_part2.md(2), diag/item30/separability.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part2.md:15` |
| `research/labels/diagnostics/item30/separability_train_output.txt` | saída gerada | `99f5a9a` 2026-09-26 | sim — separabilidade no treino: sem separação | diag/item30/REPORT_part2.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part2.md:77` |
| `research/labels/diagnostics/item30/separability_train_params14.csv` | saída gerada | `99f5a9a` 2026-09-26 | sim — tabela de separabilidade por série (params-14) | diag/item30/REPORT_part2.md(2), diag/item30/figs_cf.py(2), diag/item30/separability.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S07 | `research/labels/diagnostics/item30/REPORT_part2.md:77` |
| `research/labels/diagnostics/item30/swell_baseline_gate.py` | script de diagnóstico | `002078b` 2026-09-25 | não | diag/item30/REPORT.md(1), diag/item31/DESIGN.md(1), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |

### `research/labels/diagnostics/item31`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/labels/diagnostics/item31/DESIGN.md` | registro/relatório | `e31b727` 2026-09-28 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/exposure_table.md(17), diag/item31/stage1_run.py(5), diag/item31/exposure_table.py(2), diag/item31/recovery_table.py(2), +9 | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S08 | `docs/future_work.md:3823` |
| `research/labels/diagnostics/item31/benchmark_swap_mutation.txt` | saída gerada | `1766338` 2026-09-28 | sim — mutação: colunas trocadas no teste do benchmark são detectadas | diag/item31/DESIGN.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/benchmark_swap_mutation_2c.txt` | saída gerada | `4304d70` 2026-09-28 | sim — mutação repetida na etapa 2c | docs/future_work.md(1), diag/item31/DESIGN.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:923` |
| `research/labels/diagnostics/item31/constant_train.json` | saída gerada | `a21bca2` 2026-09-28 | sim — baseline constante no treino (params-15, defaults, constante) | diag/item31/stage1_smoke_train.txt(7), diag/item31/stage1_smoke_train.py(3), diag/item31/DESIGN.md(2), diag/item31/constant_train.py(2), +3 | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:170` |
| `research/labels/diagnostics/item31/constant_train.py` | script de diagnóstico | `a21bca2` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/stage1_smoke_train.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/constant_train.txt` | saída gerada | `a21bca2` 2026-09-28 | sim — baseline constante no treino | diag/item31/DESIGN.md(4), diag/item31/constant_train.py(2), diag/item31/stage1_run.py(1), diag/item31/test_label_census.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:170` |
| `research/labels/diagnostics/item31/exposure_table.json` | saída gerada | `5075e49` 2026-09-28 | sim — dados do registro de exposição do TESTE | diag/item31/exposure_table.py(2), diag/item31/future_work_numbers.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:88` |
| `research/labels/diagnostics/item31/exposure_table.md` | registro/relatório | `5075e49` 2026-09-28 | sim — relatório/registro | diag/item31/DESIGN.md(4), diag/item31/exposure_table.py(2), docs/future_work.md(1) | **consolidar** | registro de exposição das séries de TESTE — precisa sobreviver à limpeza | S08 | — |
| `research/labels/diagnostics/item31/exposure_table.py` | script de diagnóstico | `5075e49` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/exposure_table.md(1), diag/item31/stale_scripts.md(1), diag/item31/stale_scripts.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/fix_use_filter_false_after.json` | saída gerada | `a1784b5` 2026-09-28 | sim — registro depois do fix use_filter=False | — | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `CHANGELOG.md:107` |
| `research/labels/diagnostics/item31/fix_use_filter_false_before.json` | saída gerada | `e5cd91b` 2026-09-28 | sim — registro antes do fix use_filter=False (crash) | diag/item31/fix_use_filter_false_equivalence.py(2), diag/item31/DESIGN.md(1), diag/item31/future_work_numbers.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:865` |
| `research/labels/diagnostics/item31/fix_use_filter_false_equivalence.py` | script de diagnóstico | `e5cd91b` 2026-09-28 | sim — docstring descreve o defeito encontrado | diag/item31/DESIGN.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | S08 | `CHANGELOG.md:107` |
| `research/labels/diagnostics/item31/fix_use_filter_false_equivalence.txt` | saída gerada | `a1784b5` 2026-09-28 | sim — o que rodava antes do fix roda igual; o que quebrava agora roda | CHANGELOG.md(1), diag/item31/fix_use_filter_false_equivalence.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `CHANGELOG.md:118` |
| `research/labels/diagnostics/item31/footprint_train.json` | saída gerada | `e42da8b` 2026-09-28 | sim — pegada do default novo no treino | diag/item31/footprint_train.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:442` |
| `research/labels/diagnostics/item31/footprint_train.py` | script de diagnóstico | `e42da8b` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/footprint_train.txt` | saída gerada | `e42da8b` 2026-09-28 | sim — pegada do default novo no treino | diag/item31/DESIGN.md(4), diag/item31/footprint_train.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:442` |
| `research/labels/diagnostics/item31/future_work_numbers.json` | saída gerada | `cc5519e` 2026-09-28 | sim — números do registro do item 31, regenerados | diag/item31/future_work_numbers.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `docs/future_work.md:3823` |
| `research/labels/diagnostics/item31/future_work_numbers.py` | script de diagnóstico | `cc5519e` 2026-09-28 | não | docs/future_work.md(1), diag/item31/DESIGN.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/gate_2a.py` | script de diagnóstico | `1766338` 2026-09-28 | não | diag/item31/DESIGN.md(1), diag/item31/recovery_table.py(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/gate_2a.txt` | saída gerada | `eed8e77` 2026-09-28 | sim — gate 2a (remoção de params-1..14) — PASS | diag/item31/DESIGN.md(1), diag/item31/gate_2a.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:595` |
| `research/labels/diagnostics/item31/gate_2b.json` | saída gerada | `c5217b5` 2026-09-28 | sim — gate 2b (defaults viram params-15) | diag/item31/future_work_numbers.py(4), diag/item31/gate_2b.py(2), diag/item31/DESIGN.md(1), diag/item31/train_sequences_2b.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/gate_2b.py` | script de diagnóstico | `c5217b5` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/gate_2b.txt` | saída gerada | `c5217b5` 2026-09-28 | sim — gate 2b | diag/item31/DESIGN.md(1), diag/item31/gate_2b.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/item31_core.py` | script de diagnóstico | `e42da8b` 2026-09-28 | não | — | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/make_defaults_2_0_0.py` | script de diagnóstico | `a5067df` 2026-09-28 | não | diag/item31/gate_2a.py(2), research/labels/config_defaults.py(1), research/labels/defaults_2.0.0.json(1), diag/item31/DESIGN.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/p15_expected_digest.py` | script de diagnóstico | `e42da8b` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item31/p15_expected_digest.txt` | saída gerada | `e42da8b` 2026-09-28 | sim — digest esperado após a etapa 2 (layout front_b) | diag/item31/DESIGN.md(2), diag/item31/p15_expected_digest.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:375` |
| `research/labels/diagnostics/item31/param_table.json` | saída gerada | `e42da8b` 2026-09-28 | sim — tabela defaults do pacote × params-15 (item 31) | diag/item31/make_defaults_2_0_0.py(3), diag/item31/DESIGN.md(2), diag/item31/future_work_numbers.py(2), diag/item31/param_table.py(2), +2 | **manter** | lido por teste vivo (tests/test_config_defaults.py, PARAM_TABLE) | — | — |
| `research/labels/diagnostics/item31/param_table.md` | registro/relatório | `e42da8b` 2026-09-28 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/DESIGN.md(3), diag/item31/param_table.py(2), diag/item31/footprint_train.py(1), diag/item31/p15_expected_digest.py(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S08 | `docs/future_work.md:3823` |
| `research/labels/diagnostics/item31/param_table.py` | script de diagnóstico | `e42da8b` 2026-09-28 | não | diag/item31/DESIGN.md(1), diag/item31/param_table.md(1) | **manter** | gerador do param_table.json lido por teste vivo | — | — |
| `research/labels/diagnostics/item31/reachability_train.json` | saída gerada | `e42da8b` 2026-09-28 | sim — alcançabilidade no treino | diag/item31/future_work_numbers.py(2), diag/item31/reachability_train.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:62` |
| `research/labels/diagnostics/item31/reachability_train.py` | script de diagnóstico | `e42da8b` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item31/reachability_train.txt` | saída gerada | `e42da8b` 2026-09-28 | sim — alcançabilidade no treino | diag/item31/DESIGN.md(2), diag/item31/reachability_train.py(2), diag/item31/p15_expected_digest.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:62` |
| `research/labels/diagnostics/item31/recovery_table.json` | saída gerada | `b484738` 2026-09-28 | sim — idem, dados | diag/item31/future_work_numbers.py(3), diag/item31/gate_2a.py(2), diag/item31/recovery_table.py(2) | **manter** | dados do índice de recuperação (mesmo gerador) | — | — |
| `research/labels/diagnostics/item31/recovery_table.md` | registro/relatório | `b484738` 2026-09-28 | sim — de onde recuperar cada params-1..14 (hash verificado) | research/labels/README.md(2), diag/item31/DESIGN.md(2), diag/item31/recovery_table.py(2), CHANGELOG.md(1), +3 | **manter** | índice de recuperação de params-1..14 (citado pelo app README e por teste vivo) | — | — |
| `research/labels/diagnostics/item31/recovery_table.py` | script de diagnóstico | `b484738` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/recovery_table.md(1) | **manter** | gerador do índice de recuperação | — | — |
| `research/labels/diagnostics/item31/regenerate_baselines_2b.py` | script de diagnóstico | `55a4780` 2026-09-28 | não | — | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/sidebar_table_2c.json` | saída gerada | `4304d70` 2026-09-28 | sim — barra lateral derivada da assinatura (2c) | diag/item31/future_work_numbers.py(4), diag/item31/sidebar_table_2c.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:923` |
| `research/labels/diagnostics/item31/sidebar_table_2c.md` | registro/relatório | `4304d70` 2026-09-28 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/sidebar_table_2c.py(2), CHANGELOG.md(1), docs/future_work.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S08 | `docs/future_work.md:3823` |
| `research/labels/diagnostics/item31/sidebar_table_2c.py` | script de diagnóstico | `4304d70` 2026-09-28 | não | diag/item31/DESIGN.md(2) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/stage1_output.json` | saída gerada | `33ea489` 2026-09-28 | sim — a rodada única de pontuação do estágio 1 — PASS | diag/item31/stage1_run.py(3), diag/item31/future_work_numbers.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `docs/future_work.md:3854` |
| `research/labels/diagnostics/item31/stage1_output.txt` | saída gerada | `33ea489` 2026-09-28 | sim — a rodada única de pontuação do estágio 1 — PASS | diag/item31/stage1_run.py(4), diag/item31/DESIGN.md(2), CHANGELOG.md(1), diag/item31/stage1_smoke_train.py(1), +1 | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `docs/future_work.md:3854` |
| `research/labels/diagnostics/item31/stage1_run.py` | script de diagnóstico | `5075e49` 2026-09-28 | não | diag/item31/DESIGN.md(6), diag/item31/stage1_smoke_train.py(2), docs/future_work.md(1), diag/item31/stage1_output.json(1), +3 | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item31/stage1_smoke_train.py` | script de diagnóstico | `5075e49` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/stale_scripts.json(1), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque (não roda na ponta: params-1..14 removidos) | — | — |
| `research/labels/diagnostics/item31/stage1_smoke_train.txt` | saída gerada | `5075e49` 2026-09-28 | sim — smoke test do pontuador no treino | diag/item31/DESIGN.md(2), diag/item31/stage1_smoke_train.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:547` |
| `research/labels/diagnostics/item31/stale_scripts.json` | saída gerada | `1766338` 2026-09-28 | sim — lista dos scripts que param de rodar | diag/item31/future_work_numbers.py(2), diag/item31/stale_scripts.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:595` |
| `research/labels/diagnostics/item31/stale_scripts.md` | registro/relatório | `1766338` 2026-09-28 | sim — relatório/registro | diag/item31/stale_scripts.py(2), CHANGELOG.md(1), docs/future_work.md(1), research/labels/README.md(1), +1 | **consolidar** | índice dos scripts que param de rodar; vira seção de rastreabilidade | S10 | — |
| `research/labels/diagnostics/item31/stale_scripts.py` | script de diagnóstico | `1766338` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/stale_scripts.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/suite_2a.txt` | saída gerada | `cc5519e` 2026-09-28 | sim — suíte após 2a | diag/item31/DESIGN.md(1), diag/item31/future_work_numbers.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:595` |
| `research/labels/diagnostics/item31/suite_2b_final.txt` | saída gerada | `cc5519e` 2026-09-28 | sim — suíte após 2b | diag/item31/DESIGN.md(1), diag/item31/future_work_numbers.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/suite_2b_measure.txt` | saída gerada | `45f0600` 2026-09-28 | sim — suíte com os defaults novos antes de tocar testes (falhas esperadas) | diag/item31/future_work_numbers.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:815` |
| `research/labels/diagnostics/item31/suite_2b_prefix.txt` | saída gerada | `cc5519e` 2026-09-28 | sim — suíte no prefixo de 2b (uma falha, a do use_filter=False) | diag/item31/future_work_numbers.py(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/suite_2c.txt` | saída gerada | `e31b727` 2026-09-28 | sim — suíte após 2c | diag/item31/future_work_numbers.py(2), diag/item31/DESIGN.md(1) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `docs/future_work.md:3983` |
| `research/labels/diagnostics/item31/test_label_census.json` | saída gerada | `a21bca2` 2026-09-28 | sim — censo declarado dos rótulos de TESTE (contagens) | diag/item31/future_work_numbers.py(2), diag/item31/test_label_census.py(2) | **remover** | saída gerada de frente fechada; o achado está no registro indicado | S08 | `research/labels/diagnostics/item31/DESIGN.md:124` |
| `research/labels/diagnostics/item31/test_label_census.py` | script de diagnóstico | `e42da8b` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **remover** | script de diagnóstico de frente fechada; reprodutível pelo commit do último toque | — | — |
| `research/labels/diagnostics/item31/test_label_census.txt` | saída gerada | `a21bca2` 2026-09-28 | sim — relatório/registro | diag/item31/DESIGN.md(2), diag/item31/test_label_census.py(2), diag/item31/stage1_run.py(1) | **consolidar** | censo declarado dos rótulos de TESTE (contagens) — registro de exposição | S08 | — |
| `research/labels/diagnostics/item31/train_sequences_2b.md` | registro/relatório | `ba16572` 2026-09-28 | sim — relatório de frente fechada (achados, previsões, veredito) | diag/item31/DESIGN.md(1) | **consolidar** | relatório de frente fechada; achados vão ao documento único (Passo 2) | S08 | `docs/future_work.md:3823` |

### `research/snapshots`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `research/snapshots/README.md` | registro/relatório | `1766338` 2026-09-28 | sim — comparação snapshot publicado × params-11 | docs/future_work.md(1) | **manter** | colunas de referência do Benchmark (releases publicados) | — | — |
| `research/snapshots/SHA256SUMS` | dados | `7f137fe` 2026-09-18 | não | research/snapshots/README.md(1) | **manter** | colunas de referência do Benchmark (releases publicados) | — | — |
| `research/snapshots/make_published_snapshot.py` | script de pesquisa (vivo) | `7f137fe` 2026-09-18 | não | docs/future_work.md(1), research/snapshots/README.md(1), research/snapshots/v1.9.4.json(1), research/snapshots/v2.0.0.json(1) | **manter** | colunas de referência do Benchmark (releases publicados) | — | — |
| `research/snapshots/v1.9.4.json` | dados | `7f137fe` 2026-09-18 | não | research/snapshots/README.md(2), research/snapshots/SHA256SUMS(1), research/snapshots/make_published_snapshot.py(1) | **manter** | colunas de referência do Benchmark (releases publicados) | — | — |
| `research/snapshots/v2.0.0.json` | dados | `7f137fe` 2026-09-18 | não | research/snapshots/README.md(1), research/snapshots/SHA256SUMS(1) | **manter** | colunas de referência do Benchmark (releases publicados) | — | — |

### `tests`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `tests/__init__.py` | teste | `b83a572` 2023-08-29 | não | — | **manter** | suíte de testes | — | — |
| `tests/browser_harness.py` | teste | `f300420` 2026-09-14 | não | docs/future_work.md(1), research/inert_params/REPORT_inertia_sweep.md(1), tests/test_label_browser.py(1) | **manter** | suíte de testes | — | — |
| `tests/conftest.py` | teste | `263d5bf` 2026-09-06 | não | tests/synthetic/test_synthetic_lifecycles.py(1) | **manter** | suíte de testes | — | — |
| `tests/expected_default.csv` | dados | `55a4780` 2026-09-28 | não | diag/item31/DESIGN.md(1), diag/item31/regenerate_baselines_2b.py(1), tests/test_determine_periods.py(1) | **manter** | suíte de testes | — | — |
| `tests/expected_no_filter.csv` | dados | `a1784b5` 2026-09-28 | não | diag/item31/DESIGN.md(3), diag/item31/fix_use_filter_false_equivalence.py(1), diag/item31/regenerate_baselines_2b.py(1), tests/test_determine_periods.py(1) | **manter** | suíte de testes | — | — |
| `tests/legacy_defaults.py` | teste | `c5217b5` 2026-09-28 | não | docs/future_work.md(1), diag/item31/DESIGN.md(1), tests/test_incipient_plateau.py(1) | **manter** | suíte de testes | — | — |
| `tests/test.csv` | dados | `64c199c` 2024-04-11 | não | cyclophaser/find_stages.py(1), docs/api.rst(1), docs/testing.rst(1), diag/item31/regenerate_baselines_2b.py(1), +1 | **manter** | suíte de testes | — | — |
| `tests/test_app_distance_removed.py` | teste | `a5067df` 2026-09-28 | não | research/inert_params/REPORT_inertia_sweep.md(1), diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_benchmark_apptest.py` | teste | `4304d70` 2026-09-28 | não | diag/item31/DESIGN.md(3), docs/future_work.md(2), diag/item31/benchmark_swap_mutation.txt(1), diag/item31/benchmark_swap_mutation_2c.txt(1), +1 | **manter** | suíte de testes | — | — |
| `tests/test_boundary_padding.py` | teste | `c5217b5` 2026-09-28 | não | research/inert_params/INCIDENTAL_crash_bug.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_config_defaults.py` | teste | `1766338` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_decay_tail_amplitude_fraction.py` | teste | `c5217b5` 2026-09-28 | não | docs/future_work.md(4), tests/test_boundary_padding.py(2), research/inert_params/INCIDENTAL_crash_bug.md(1), diag/frontC/REPORT.md(1), +3 | **manter** | suíte de testes | — | — |
| `tests/test_determine_periods.py` | teste | `7b8c4aa` 2024-10-28 | não | diag/item31/DESIGN.md(2), diag/item31/fix_use_filter_false_equivalence.py(1) | **manter** | suíte de testes | — | — |
| `tests/test_evaluate_batch_train.py` | teste | `9dc87d4` 2026-09-27 | não | diag/item30/REPORT.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_incipient_plateau.py` | teste | `c5217b5` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_inspector_apptest.py` | teste | `95275ee` 2026-09-25 | não | docs/future_work.md(2) | **manter** | suíte de testes | — | — |
| `tests/test_integration_prominence.py` | teste | `4c0767c` 2026-09-16 | não | — | **manter** | suíte de testes | — | — |
| `tests/test_intensification_min_depth.py` | teste | `c5217b5` 2026-09-28 | não | diag/frontC/REPORT.md(1), diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_item30_spare_intensification.py` | teste | `c5217b5` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_label_apptest.py` | teste | `916ecfc` 2026-09-27 | não | research/labels/swell_item30/README.md(1), tools/calibration_app/label_tab.py(1) | **manter** | suíte de testes | — | — |
| `tests/test_label_browser.py` | teste | `f300420` 2026-09-14 | não | docs/future_work.md(5), CLAUDE.md(2), research/inert_params/REPORT_inertia_sweep.md(2), research/labels/README.md(2), +3 | **manter** | suíte de testes | — | — |
| `tests/test_layer_inspector.py` | teste | `c5217b5` 2026-09-28 | não | docs/future_work.md(5), tools/calibration_app/layer_inspector.py(3), tests/test_manual_labels.py(2), research/inert_params/INCIDENTAL_crash_bug.md(1), +3 | **manter** | suíte de testes | — | — |
| `tests/test_manual_labels.py` | teste | `ab17faa` 2026-09-13 | não | tools/calibration_app/label_tab.py(4), docs/future_work.md(2), research/labels/README.md(2), research/labels/labels_core.py(1) | **manter** | suíte de testes | — | — |
| `tests/test_peaks_valleys_plateau.py` | teste | `522675e` 2026-06-12 | não | — | **manter** | suíte de testes | — | — |
| `tests/test_prominence.py` | teste | `4c0767c` 2026-09-16 | não | tests/test_integration_prominence.py(1) | **manter** | suíte de testes | — | — |
| `tests/test_reclassify_index0.py` | teste | `4e7fa9f` 2026-09-23 | não | diag/frontA_idx0_c2/REPORT.md(1), diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_regression_baseline.py` | teste | `55a4780` 2026-09-28 | não | diag/item31/DESIGN.md(2), research/inert_params/INCIDENTAL_crash_bug.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_sidebar_coverage.py` | teste | `773cbef` 2026-09-18 | não | diag/item20b/REPORT_stage2.md(2), docs/future_work.md(1), tests/test_item30_spare_intensification.py(1), tools/calibration_app/README.md(1), +1 | **manter** | suíte de testes | — | — |
| `tests/test_sidebar_defaults.py` | teste | `4304d70` 2026-09-28 | não | diag/item31/DESIGN.md(2), CHANGELOG.md(1), docs/future_work.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_swell_batch.py` | teste | `916ecfc` 2026-09-27 | não | research/labels/swell_item30/README.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_track_io.py` | teste | `baaf595` 2026-09-24 | não | docs/future_work.md(2) | **manter** | suíte de testes | — | — |
| `tests/test_track_upload_apptest.py` | teste | `baaf595` 2026-09-24 | não | tests/test_track_io.py(1) | **manter** | suíte de testes | — | — |
| `tests/test_use_filter_bool.py` | teste | `4a1ebdb` 2026-09-03 | não | docs/future_work.md(1) | **manter** | suíte de testes | — | — |
| `tests/test_use_smoothing_false_derivatives.py` | teste | `cbf917a` 2026-09-04 | não | research/inert_params/INCIDENTAL_crash_bug.md(1) | **manter** | suíte de testes | — | — |

### `tests/baselines`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `tests/baselines/baseline_default.csv` | dados | `55a4780` 2026-09-28 | não | diag/item31/DESIGN.md(2), diag/item31/regenerate_baselines_2b.py(1) | **manter** | suíte de testes | — | — |
| `tests/baselines/baseline_default_2_0_0.csv` | dados | `55a4780` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/baselines/baseline_defaults_multitrack.csv` | dados | `d810d22` 2026-09-04 | não | tests/test_incipient_plateau.py(2), CHANGELOG.md(1), diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/baselines/baseline_smoothing.csv` | dados | `55a4780` 2026-09-28 | não | diag/item31/DESIGN.md(1), diag/item31/regenerate_baselines_2b.py(1) | **manter** | suíte de testes | — | — |
| `tests/baselines/baseline_smoothing_2_0_0.csv` | dados | `55a4780` 2026-09-28 | não | diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |
| `tests/baselines/figures/.gitignore` | teste | `29b66ba` 2026-06-12 | não | — | **manter** | suíte de testes | — | — |
| `tests/baselines/figures/.gitkeep` | teste | `29b66ba` 2026-06-12 | não | — | **manter** | suíte de testes | — | — |
| `tests/baselines/figures_diff/.gitignore` | teste | `29b66ba` 2026-06-12 | não | — | **manter** | suíte de testes | — | — |
| `tests/baselines/figures_diff/.gitkeep` | teste | `29b66ba` 2026-06-12 | não | — | **manter** | suíte de testes | — | — |

### `tests/calibration_data`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `tests/calibration_data/*.csv` — **51 arquivos** (`git ls-files 'tests/calibration_data/*.csv'`) | dados | `11e530a` 2026-07-08 | não | tests/test_incipient_plateau.py(3), research/labels/swell_item30/README.md(1), research/labels/swell_item30/draw_batch.py(1), research/labels/swell_item30/provenance.yaml(1), +4 | **manter** | séries reais usadas pela suíte e pelo app (carregadas por diretório) | — | — |
| `tests/calibration_data/gen_real_before_after.py` | script de diagnóstico | `4c0767c` 2026-09-16 | não | research/incipient_plateau/gen_geometric_vs_plateau.py(1), research/incipient_plateau/measure_incipient.py(1) | **remover** | gerador exploratório de figuras (frente de proeminência); não é teste nem dado; figuras não versionadas; só citado por scripts que também saem | — | — |
| `tests/calibration_data/swell_item30/*.csv` — **10 arquivos** (`git ls-files 'tests/calibration_data/swell_item30/*.csv'`) | dados | `7a480a5` 2026-09-25 | não | research/labels/swell_item30/provenance.yaml(10) | **manter** | séries reais usadas pela suíte e pelo app (carregadas por diretório) | — | — |
| `tests/calibration_data/swell_item30_val/*.csv` — **5 arquivos** (`git ls-files 'tests/calibration_data/swell_item30_val/*.csv'`) | dados | `d1841cc` 2026-09-27 | não | research/labels/swell_item30/provenance_val.yaml(5) | **manter** | séries reais usadas pela suíte e pelo app (carregadas por diretório) | — | — |

### `tests/synthetic`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `tests/synthetic/__init__.py` | teste | `4a348c2` 2026-06-13 | não | — | **manter** | suíte de testes | — | — |
| `tests/synthetic/cases.py` | teste | `f80c2f6` 2026-09-04 | não | docs/future_work.md(11), tools/calibration_app/app.py(6), research/labels/labels_core.py(5), research/labels/README.md(3), +10 | **manter** | suíte de testes | — | — |
| `tests/synthetic/data/*.csv` — **12 arquivos** (`git ls-files 'tests/synthetic/data/*.csv'`) | dados | `490a90e` 2026-09-10 | não | — | **manter** | séries sintéticas CONGELADAS (verdade dos testes) | — | — |
| `tests/synthetic/figures/.gitkeep` | teste | `9171ad2` 2026-06-13 | não | — | **manter** | suíte de testes | — | — |
| `tests/synthetic/gen_extrema_before_after.py` | script de diagnóstico | `4c0767c` 2026-09-16 | não | research/incipient_plateau/gen_geometric_vs_plateau.py(1) | **remover** | gerador exploratório de figuras (frente de proeminência); não é teste; figuras não versionadas; só citado por um script que também sai | — | — |
| `tests/synthetic/generate_figures.py` | teste | `68defa2` 2026-06-13 | não | CHANGELOG.md(2), cyclophaser/plots.py(1) | **manter** | suíte de testes | — | — |
| `tests/synthetic/generators.py` | teste | `1448603` 2026-06-13 | não | docs/future_work.md(2), tests/synthetic/cases.py(1) | **manter** | suíte de testes | — | — |
| `tests/synthetic/test_length_scale_regression.py` | teste | `ba16572` 2026-09-28 | não | docs/future_work.md(1) | **manter** | suíte de testes | — | — |
| `tests/synthetic/test_synthetic_lifecycles.py` | teste | `727efd2` 2026-09-15 | não | docs/future_work.md(3), CLAUDE.md(1), research/labels/README.md(1), diag/item31/DESIGN.md(1) | **manter** | suíte de testes | — | — |

### `tools/calibration_app`

| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |
|---|---|---|---|---|---|---|---|---|
| `tools/calibration_app/.gitignore` | app | `70cf0b1` 2026-06-14 | não | — | **manter** | app de calibração | — | — |
| `tools/calibration_app/.streamlit/config.toml` | app | `4e042a2` 2026-06-13 | não | — | **manter** | app de calibração | — | — |
| `tools/calibration_app/README.md` | doc de usuário | `1766338` 2026-09-28 | não | — | **manter** | app de calibração | — | — |
| `tools/calibration_app/app.py` | app | `4304d70` 2026-09-28 | não | README.md(2), docs/future_work.md(2), research/inert_params/REPORT_inertia_sweep.md(2), research/inert_params/sweep_inertia.py(2), +10 | **manter** | app de calibração | — | — |
| `tools/calibration_app/benchmark_core.py` | app | `a5067df` 2026-09-28 | não | diag/item30/prove_defaults_30c.py(2), diag/item30/prove_defaults_part3.py(2) | **manter** | app de calibração | — | — |
| `tools/calibration_app/benchmark_tab.py` | app | `a5067df` 2026-09-28 | não | — | **manter** | app de calibração | — | — |
| `tools/calibration_app/inspector_mpl.py` | app | `7133570` 2026-09-09 | não | research/app_layer_inspector/gen_inspector_figures.py(1) | **manter** | app de calibração | — | — |
| `tools/calibration_app/inspector_plotly.py` | app | `95275ee` 2026-09-25 | não | docs/future_work.md(2), tools/calibration_app/app.py(2), environment.yml(1) | **manter** | app de calibração | — | — |
| `tools/calibration_app/label_tab.py` | app | `916ecfc` 2026-09-27 | não | tools/calibration_app/app.py(7), docs/future_work.md(4), research/labels/README.md(2), research/labels/labels_core.py(1), +3 | **manter** | app de calibração | — | — |
| `tools/calibration_app/layer_inspector.py` | app | `c5217b5` 2026-09-28 | não | docs/future_work.md(5), diag/item30/figs_cf_output.txt(2), diag/item30/part3_measure_output.txt(2), tests/test_manual_labels.py(2), +10 | **manter** | app de calibração | — | — |
| `tools/calibration_app/package_args.py` | app | `baaf595` 2026-09-24 | não | — | **manter** | app de calibração | — | — |
| `tools/calibration_app/requirements-app.txt` | app | `e3e7b6a` 2026-09-05 | não | docs/future_work.md(3), tools/calibration_app/README.md(2), README.md(1), docs/calibration_tool.rst(1), +3 | **manter** | app de calibração | — | — |
| `tools/calibration_app/requirements.txt` | app | `e3e7b6a` 2026-09-05 | não | README.md(1), docs/calibration_tool.rst(1), docs/future_work.md(1), environment.yml(1) | **manter** | app de calibração | — | — |
| `tools/calibration_app/track_format_ui.py` | app | `baaf595` 2026-09-24 | não | docs/future_work.md(1) | **manter** | app de calibração | — | — |
| `tools/calibration_app/track_io.py` | app | `baaf595` 2026-09-24 | não | docs/future_work.md(3), CHANGELOG.md(1), tests/test_track_io.py(1), tools/calibration_app/README.md(1) | **manter** | app de calibração | — | — |

## 0.2 (a) Scripts de `item31/stale_scripts.md`

| script | existe? | evidência (stale_scripts.json; conferida na linha) | módulos locais importados | caminhos literais | resultado registrado em | destino |
|---|---|---|---|---|---|---|
| `diag/frontA_reverify/attribute_params.py` | sim | removed file params-9 (line 76); removed file params-13 (line 77) | cyclophaser, evaluate_against_labels, labels_core | — | `docs/future_work.md:2784`, `research/labels/diagnostics/frontA_reverify/REPORT.md:239` | **remover** |
| `diag/frontC/d2_separation.py` | sim | removed file params-12 (line 94) | cyclophaser, labels_core | — | `docs/future_work.md:2334`, `research/labels/diagnostics/frontC/REPORT.md:41` | **remover** |
| `diag/frontC/default_equivalence.py` | sim | removed file params-12 (line 133); removed file params-13 (line 141) | cyclophaser, labels_core | — | `docs/future_work.md:2334`, `research/labels/diagnostics/frontC/REPORT.md:41` | **remover** |
| `diag/frontC/make_figures.py` | sim | removed file params-12 (line 99); removed file params-13 (line 100) | cyclophaser, d2_separation, labels_core, measure_frontC | — | `docs/future_work.md:2334`, `research/labels/diagnostics/frontC/REPORT.md:41` | **remover** |
| `diag/frontC/measure_frontC.py` | sim | removed file params-12 (line 148); removed file params-13 (line 148); removed file params-12 (line 153); removed file params-13 (line 154) | cyclophaser, labels_core | — | `docs/future_work.md:2334`, `research/labels/diagnostics/frontC/REPORT.md:41` | **remover** |
| `diag/frontC/report_test_series.py` | sim | removed file params-12 (line 42); removed file params-13 (line 43); removed config name params-12 (line 53); removed config name params-13 (line 53); removed config name params-12 (line 62); removed config name params-13 (line 62); removed config name params-12 (line 64); removed config name params-13 (line 64) | cyclophaser, d2_separation, labels_core, measure_frontC | — | `docs/future_work.md:2334`, `research/labels/diagnostics/frontC/REPORT.md:41` | **remover** |
| `diag/frontD/anchoring.py` | sim | removed file params-13 (line 38) | cyclophaser, evaluate_against_labels, labels_core | research/labels/configs/cyclophaser_params-13.yaml | `docs/future_work.md:2519`, `research/labels/diagnostics/frontD/REPORT.md:61` | **remover** |
| `diag/frontD/census.py` | sim | removed file params-13 (line 43) | cyclophaser, evaluate_against_labels, labels_core | research/labels/configs/cyclophaser_params-13.yaml | `docs/future_work.md:2519`, `research/labels/diagnostics/frontD/REPORT.md:61` | **remover** |
| `diag/frontD/make_figures.py` | sim | removed file params-13 (line 27) | cyclophaser, evaluate_against_labels, labels_core | research/labels/configs/cyclophaser_params-13.yaml | `docs/future_work.md:2519`, `research/labels/diagnostics/frontD/REPORT.md:61` | **remover** |
| `diag/frontD/verify_hashes.py` | sim | removed file params-13 (line 31) | labels_core | research/labels/configs/cyclophaser_params-13.yaml | `docs/future_work.md:2519`, `research/labels/diagnostics/frontD/REPORT.md:61` | **remover** |
| `diag/frontRefusal/diagnose.py` | sim | removed file params-13 (line 51) | cyclophaser, evaluate_against_labels, labels_core | research/labels/configs/cyclophaser_params-13.yaml | `docs/future_work.md:2662`, `research/labels/diagnostics/frontRefusal/REPORT.md:170` | **remover** |
| `diag/frontRefusal/make_figures.py` | sim | removed file params-13 (line 38) | cyclophaser, evaluate_against_labels, labels_core | research/labels/configs/cyclophaser_params-13.yaml | `docs/future_work.md:2662`, `research/labels/diagnostics/frontRefusal/REPORT.md:170` | **remover** |
| `diag/front_b/collect_train_diagnostics.py` | sim | removed file params-9 (line 40) | cyclophaser, labels_core | — | `docs/future_work.md:1564`, `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33` | **remover** |
| `diag/front_b/reference_score_attribution.py` | sim | removed file params-9 (line 24); removed config name params-9 (line 72); removed config name params-9 (line 94); removed config name params-9 (line 96); removed config name params-9 (line 98); removed config name params-9 (line 100); removed config name params-9 (line 102) | — | — | `docs/future_work.md:1564`, `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33` | **remover** |
| `diag/front_b/sensitivity_probe.py` | sim | removed file params-9 (line 11) | cyclophaser, labels_core | research/labels/configs/cyclophaser_params-9.yaml, research/labels/diagnostics/front_b/sensitivity.txt | `docs/future_work.md:1564`, `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33` | **remover** |
| `diag/front_b/sweep_distance.py` | sim | removed file params-9 (line 34) | cyclophaser, labels_core | — | `docs/future_work.md:1564`, `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33` | **remover** |
| `diag/item19/closeout_measurements.py` | sim | item19_core default config: load_config() (line 24) | item19_core, labels_core | — | `docs/future_work.md:1731`, `research/labels/diagnostics/item19/REPORT.md:460` | **remover** |
| `diag/item19/stage1_describe.py` | sim | item19_core default config: load_config() (line 85); item19_core default config: .CONFIG (line 89) | cyclophaser, item19_core, labels_core | — | `docs/future_work.md:1731`, `research/labels/diagnostics/item19/REPORT.md:460` | **remover** |
| `diag/item19/stage2_grid.py` | sim | item19_core default config: load_config() (line 131); item19_core default config: .CONFIG (line 135) | cyclophaser, item19_core, labels_core | — | `docs/future_work.md:1731`, `research/labels/diagnostics/item19/REPORT.md:460` | **remover** |
| `diag/item19/stage2_tradeoff_figure.py` | sim | item19_core default config: load_config() (line 29); removed config name params-10 (line 73) | item19_core, labels_core | — | `docs/future_work.md:1731`, `research/labels/diagnostics/item19/REPORT.md:460` | **remover** |
| `diag/item20a/measure_20a.py` | sim | removed file params-10 (line 33); removed file params-11 (line 34) | item19_core, labels_core | — | `docs/future_work.md:1830`, `research/labels/diagnostics/item20a/REPORT.md:52` | **remover** |
| `diag/item20b/default_equivalence.py` | sim | removed file params-11 (line 69); removed file params-12 (line 78) | cyclophaser, labels_core | — | `docs/future_work.md:2140`, `research/labels/diagnostics/item20b/REPORT_stage2.md:191` | **remover** |
| `diag/item20b/gate_stage2.py` | sim | removed file params-11 (line 184); removed file params-12 (line 184); removed file params-11 (line 189); removed file params-12 (line 190) | cyclophaser, labels_core | — | `docs/future_work.md:2140`, `research/labels/diagnostics/item20b/REPORT_stage2.md:191` | **remover** |
| `diag/item20b/make_figures.py` | sim | removed file params-11 (line 73); removed file params-12 (line 74) | cyclophaser, gate_stage2, labels_core | — | `docs/future_work.md:2140`, `research/labels/diagnostics/item20b/REPORT_stage2.md:191` | **remover** |
| `diag/item20b/measure_20b.py` | sim | removed file params-11 (line 39); item19_core default config: load_config() (line 285) | cyclophaser, labels_core | — | `docs/future_work.md:2140`, `research/labels/diagnostics/item20b/REPORT_stage2.md:191` | **remover** |
| `diag/item30/census_train.py` | sim | removed config name params-14 (line 51) | item30_core | — | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/figs_cf.py` | sim | removed config name params-13 (line 122); removed config name params-14 (line 123); removed config name params-13 (line 156); removed config name params-13 (line 207); removed config name params-14 (line 207); removed config name params-14 (line 258); removed config name params-14 (line 260) | cyclophaser, item30_core, separability | — | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **manter** |
| `diag/item30/outside_signal.py` | sim | removed config name params-14 (line 89); removed config name params-14 (line 107) | cyclophaser, figs_cf, item30_core, part3_measure, track_io | swell_item30/groups_params11.yaml | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/part3_measure.py` | sim | removed config name params-14 (line 130); removed config name params-13 (line 131); removed config name params-14 (line 157); removed config name params-14 (line 163) | cyclophaser, evaluate_against_labels, figs_cf, item30_core, track_io | swell_item30/groups_params11.yaml, swell_item30/labels_v1_snapshot.yaml | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/post_merge_checks.py` | sim | removed file params-14 (line 42); removed config name params-14 (line 46); removed config name params-14 (line 64) | item30_core, part3_measure, prove_evaluator_default | — | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/prove_defaults_30c.py` | sim | removed file params-14 (line 89); removed config name params-14 (line 93) | labels_core, prove_evaluator_default | research/labels/evaluate_against_labels.py, research/labels/labels_core.py, tools/calibration_app/benchmark_core.py | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/prove_defaults_part3.py` | sim | removed file params-14 (line 89); removed config name params-14 (line 92) | labels_core, prove_evaluator_default | research/labels/evaluate_against_labels.py, research/labels/labels_core.py, tools/calibration_app/benchmark_core.py | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/prove_evaluator_default.py` | sim | removed file params-14 (line 67); removed config name params-14 (line 71) | labels_core | — | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item30/separability.py` | sim | removed config name params-14 (line 131) | item30_core, track_io | research/labels/swell_item30/groups_params11.yaml | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **manter** |
| `diag/item30/swell_baseline_gate.py` | sim | removed config name params-11 (line 70); removed config name params-14 (line 70); removed config name params-14 (line 74); removed config name params-11 (line 75) | item30_core, track_io | — | `docs/future_work.md:3380`, `research/labels/diagnostics/item30/REPORT_part3.md:201` | **remover** |
| `diag/item31/p15_expected_digest.py` | sim | removed config name params-14 (line 75) | item31_core | — | `docs/future_work.md:3823`, `research/labels/diagnostics/item31/DESIGN.md:547` | **remover** |
| `diag/item31/reachability_train.py` | sim | removed config name params-14 (line 36) | item31_core | — | `docs/future_work.md:3823`, `research/labels/diagnostics/item31/DESIGN.md:547` | **remover** |
| `diag/item31/stage1_run.py` | sim | removed config name params-14 (line 350); removed config name params-14 (line 354) | item19_core, item31_core, p15_expected_digest | — | `docs/future_work.md:3823`, `research/labels/diagnostics/item31/DESIGN.md:547` | **remover** |
| `diag/item31/stage1_smoke_train.py` | sim | removed config name params-14 (line 52) | item19_core, item31_core, stage1_run | — | `docs/future_work.md:3823`, `research/labels/diagnostics/item31/DESIGN.md:547` | **remover** |
| `research/labels/swell_item30/adjudicate_item30.py` | sim | removed config name params-14 (line 134) | figs_cf, item30_core | research/labels/manual_labels.yaml | `docs/future_work.md:3380`, `research/labels/swell_item30/README.md:1` | **manter** |

**40 de 40** scripts confirmados existentes. Os marcados **manter** (`item30/figs_cf.py`, `item30/separability.py`, `swell_item30/adjudicate_item30.py`) não rodam como script na ponta, mas são importados por teste vivo ou são proveniência de dados congelados; `stale_scripts.md` já registra, à parte, `item19_core.py` e `item31/exposure_table.py` como acertos estáticos que CONTINUAM rodando.

## 0.2 (b) Referências a params-1..14

`git grep -P 'params[-_]?(1[0-4]|[1-9])(?![0-9])'` (sem `research/cleanup/`): **986 ocorrências em 167 arquivos**. Lista completa, linha a linha: `passo0/inventory.json` → `grep_params_1_14`.

**Diagnósticos de frentes fechadas e `future_work.md`** — proposta por regra: *aposentar* (o script sai com a frente; reexecução = `git worktree add` em `33ea489` com o assert de `cyclophaser.__file__`); texto de relatório/registro fica como histórico. Exceções: `item19/item19_core.py` já migrado (só `REMOVED_CONFIG`, que é a mensagem de erro); `item30/figs_cf.py`, `item30/separability.py` e `item30/item30_core.py` são importados por teste vivo — o teste reconstrói params-14 em memória a partir de params-15, então nada precisa ser recuperado.

| área | ocorrências |
|---|---|
| `research/labels/diagnostics/frontA_idx0_c2` | 51 |
| `research/labels/diagnostics/frontA_reverify` | 65 |
| `research/labels/diagnostics/frontC` | 36 |
| `research/labels/diagnostics/frontD` | 23 |
| `research/labels/diagnostics/frontRefusal` | 18 |
| `research/labels/diagnostics/front_b` | 51 |
| `research/labels/diagnostics/item19` | 64 |
| `research/labels/diagnostics/item20a` | 11 |
| `research/labels/diagnostics/item20b` | 53 |
| `research/labels/diagnostics/item30` | 140 |
| `research/labels/diagnostics/item31` | 268 |
| `docs/future_work.md` | 103 (HISTÓRICO, não reescrever) |

**Fora dos diagnósticos** — cada ocorrência, com proposta por arquivo:

| arquivo:linha | trecho | proposta | motivo |
|---|---|---|---|
| `CHANGELOG.md:128` | * **`research/labels/configs/` holds only `params-15`.** params-1 to params-14 | **manter** | entradas de CHANGELOG narram a história das configs; não carregam arquivo |
| `CHANGELOG.md:169` | bit-identical (128/128: 64 series × params-14 and app defaults). The warning | **manter** | entradas de CHANGELOG narram a história das configs; não carregam arquivo |
| `CHANGELOG.md:199` | **What moves.** Under the calibration reference (params-13 + the rule = | **manter** | entradas de CHANGELOG narram a história das configs; não carregam arquivo |
| `CHANGELOG.md:200` | params-14) the output changes on 5 of those 63 series and is byte-identical on | **manter** | entradas de CHANGELOG narram a história das configs; não carregam arquivo |
| `CHANGELOG.md:231` | any calibration config from params-1 to params-13, all of which predate the rule | **manter** | entradas de CHANGELOG narram a história das configs; não carregam arquivo |
| `CHANGELOG.md:232` | — pass `reclassify_index0=False`. `research/labels/configs/cyclophaser_params-14.yaml` | **migrar** | [Unreleased] aponta `configs/cyclophaser_params-14.yaml`, que não existe mais na árvore — apontar recovery_table/33ea489 ou params-track |
| `CHANGELOG.md:288` | segments on that split. `research/labels/configs/cyclophaser_params-13.yaml` | **migrar** | [Unreleased] aponta `configs/cyclophaser_params-13.yaml`, que não existe mais — idem |
| `cyclophaser/determine_periods.py:1126` | calibration config exported before it, params-1 to params-13 — | **manter** | docstring: fato histórico (configs anteriores à regra) — não carrega arquivo |
| `cyclophaser/determine_periods.py:1127` | params-14 is the first that states it). Applied to ``z`` only: no | **manter** | docstring: fato histórico (configs anteriores à regra) — não carrega arquivo |
| `cyclophaser/determine_periods.py:1594` | calibration config exported before it, params-1 to params-13 — | **manter** | docstring: fato histórico (configs anteriores à regra) — não carrega arquivo |
| `cyclophaser/determine_periods.py:1595` | params-14 is the first that states it). Applied to ``z`` only: no | **manter** | docstring: fato histórico (configs anteriores à regra) — não carrega arquivo |
| `research/inert_params/REPORT_inertia_sweep.md:363` | `research/labels/configs/cyclophaser_params-9.yaml` | **manter** | relatório histórico (consolidar no Passo 2) |
| `research/inert_params/REPORT_inertia_sweep.md:388` | versioned `params-9`) imports cleanly: the key is applied to nothing and is | **manter** | relatório histórico (consolidar no Passo 2) |
| `research/inert_params/REPORT_inertia_sweep.md:408` | Measured on the 47 training series under `params-9` (amplitude), switching | **manter** | relatório histórico (consolidar no Passo 2) |
| `research/labels/README.md:53` | `cyclophaser_params-15.yaml`, the calibration reference.** params-1 to | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:54` | params-14 were removed by Danilo's decision. They are not lost: each one is | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:59` | `cyclophaser_params-11.yaml` once held params-14's values | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:64` | \| `cyclophaser_params-1.yaml` … `-8.yaml` \| see `diagnostics/item31/recovery_table.md` \| removed (item 31); hi | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:65` | \| `cyclophaser_params-9.yaml` \| `0c3ec55910c45a6dcf9a1787ceca3f3c6796cf25da953be642befa29eaac9f63` \| removed ( | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:66` | \| `cyclophaser_params-10.yaml` \| `c14755e3ac1c2dcb2da8e652e7eba61ce20b8c45235b18cd7183abac047902d7` \| removed  | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:67` | \| `cyclophaser_params-11.yaml` \| `24dd7f22b76d98cf0cab0b18ff040e010209604a8485007551095e9622abe420` \| removed  | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:68` | \| `cyclophaser_params-12.yaml` \| `39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3` \| removed  | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:69` | \| `cyclophaser_params-13.yaml` \| `c1ab8ce02631f1270b3a633cff2ef43fb5caff64dd492642f56cf5a96e483973` \| removed  | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:70` | \| `cyclophaser_params-14.yaml` \| `acf4985339e8849603711012b2049d8913997e329a3c56d5399f6700e2d1159e` \| removed  | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:71` | \| **`cyclophaser_params-15.yaml`** \| `5aa61f2dec710029b46a47668812d14e6d552517b7bca8912a8e00fd130ccf04` \| **th | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:75` | cites it. It was written by hand from params-14 (plus one line), so its | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/README.md:76` | `metadata` block is params-14's, timestamp included. | **manter** | tabela de proveniência das configs removidas (histórico com hashes) |
| `research/labels/split.yaml:159` | groups_file: research/labels/swell_item30/groups_params11.yaml | **manter** | CONGELADO — não reescrever |
| `research/labels/split.yaml:162` | > peak_idx; C = good AND NOT plateau_boundary > peak_idx (repo params-11, see groups_file) | **manter** | CONGELADO — não reescrever |
| `research/labels/split.yaml:231` | como cyclophaser_params-11.yaml (sha256 6df2cc0721d080acc294d943a06e03fa0967fd7d91c81b9dccb48a347251f739), | **manter** | CONGELADO — não reescrever |
| `research/labels/split.yaml:232` | cujos parâmetros de filtro e de fase são idênticos aos de params-14 (intensification_min_depth | **manter** | CONGELADO — não reescrever |
| `research/labels/split.yaml:233` | 0.05, mature_min_depth 0.80, reclassify_index0 true) — não os do params-11 do repo (24dd7f22…), | **manter** | CONGELADO — não reescrever |
| `research/labels/split.yaml:242` | under params-14 (part 2, separability.py step 2: 10 of 17), minus those already drawn | **manter** | CONGELADO — não reescrever |
| `research/labels/swell_item30/README.md:18` | \| `groups_params11.yaml` \| The groups R (9), S (10) and C (175), plus Danilo's 15 bad marks. \| | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:55` | - The repo's `params-11` config (`24dd7f22…`). The three keys it does not set | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:83` | app exported as `cyclophaser_params-11.yaml` (2026-09-24T22:42Z, sha256 | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:85` | filter and phase parameters are identical to `params-14`** | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:87` | true), not to the repo's `params-11`. The diagnostic ran the repo's `params-11` | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:93` | This was established by reading the code, not by running it under `params-14`. | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:129` | above, whose parameters equal those of `params-14`. It was **not** the repo's | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:130` | `params-11`, under which the groups were computed. The whole 200-track sample | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:144` | ## Name trap: an export called `params-11` that holds `params-14` | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:146` | The app export `cyclophaser_params-11.yaml` (sha256 `6df2cc07…`), the file that | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:147` | holds the 15 bad marks, carries **`params-14`'s values**: | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:150` | `params-14`. The file's name is not its configuration. Before attributing a | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/README.md:222` | params-14. Visual marks are judgement, not a score. | **manter** | registro histórico (recebe só nota de correspondência) |
| `research/labels/swell_item30/adjudicate_item30.py:4` | `1a3ad76` differs from params-14 (20120297, 19940445, 19810854, 19860380, | **recuperar de 33ea489** | script de proveniência de dados; load_config('params-14') não roda na ponta |
| `research/labels/swell_item30/adjudicate_item30.py:15` | (`diagnostics/item30/figs_cf.py`, unchanged since), under params-14, and | **recuperar de 33ea489** | script de proveniência de dados; load_config('params-14') não roda na ponta |
| `research/labels/swell_item30/adjudicate_item30.py:134` | cfg14 = core.load_config("params-14") | **recuperar de 33ea489** | script de proveniência de dados; load_config('params-14') não roda na ponta |
| `research/labels/swell_item30/draw_batch.py:17` | * Population: the three groups of `groups_params11.yaml` (sha256 pinned below). | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/draw_batch.py:59` | GROUPS_FILE = HERE / "groups_params11.yaml" | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/draw_batch.py:75` | "arquivo que o app exportou como cyclophaser_params-11.yaml (sha256 " | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/draw_batch.py:77` | "parâmetros de filtro e de fase são idênticos aos de params-14 " | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/draw_batch.py:79` | "true) — não os do params-11 do repo (24dd7f22…), sob o qual os grupos foram " | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/draw_batch.py:167` | "groups_file": "research/labels/swell_item30/groups_params11.yaml", | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/draw_batch.py:172` | "(repo params-11, see groups_file)"), | **manter** | `groups_params11.yaml` é nome de arquivo de dados congelado + texto de proveniência |
| `research/labels/swell_item30/freeze_validation_batch.py:10` | `separability_swell17_params14.csv`, written OUTSIDE the repo. The selection is | **manter** | texto de proveniência; não carrega config |
| `research/labels/swell_item30/freeze_validation_batch.py:27` | --part2-table <.../diag_item30/separability_swell17_params14.csv> | **manter** | texto de proveniência; não carrega config |
| `research/labels/swell_item30/freeze_validation_batch.py:48` | "defined under params-14 (part 2, separability.py step 2: 10 of 17), minus " | **manter** | texto de proveniência; não carrega config |
| `research/labels/swell_item30/transcribe_groups.py:8` | 2026-09-24 (200 swell tracks, repo `params-11`, package code of develop-v2.1 @ | **manter** | texto de proveniência + nome do arquivo congelado |
| `research/labels/swell_item30/transcribe_groups.py:39` | OUT = HERE / "groups_params11.yaml" | **manter** | texto de proveniência + nome do arquivo congelado |
| `research/snapshots/README.md:75` | Against `params-11`, over the 51 real tracks (computed with | **manter** | comparação histórica, já aponta a recuperação via 33ea489 |
| `research/snapshots/README.md:76` | `research/labels/configs/cyclophaser_params-11.yaml` on the current working tree; that | **manter** | comparação histórica, já aponta a recuperação via 33ea489 |
| `research/snapshots/README.md:77` | file was removed in item 31 and is recoverable with `git show 33ea489358d9:research/labels/configs/cyclophaser | **manter** | comparação histórica, já aponta a recuperação via 33ea489 |
| `research/snapshots/README.md:95` | **What this does not establish.** The snapshot column differs from params-11 in | **manter** | comparação histórica, já aponta a recuperação via 33ea489 |
| `tests/test_app_distance_removed.py:138` | """The real-world case: every export up to params-9 carried `distance: 5`. | **manter** | YAML inline com o valor de params-9 — instrumento congelado embutido |
| `tests/test_app_distance_removed.py:140` | params-9 itself left the repo in item 31 (recoverable from 33ea489, see | **manter** | YAML inline com o valor de params-9 — instrumento congelado embutido |
| `tests/test_app_distance_removed.py:142` | inline YAML carrying params-9's own value, run through the app's real | **manter** | YAML inline com o valor de params-9 — instrumento congelado embutido |
| `tests/test_benchmark_apptest.py:49` | # Item 31: params-1 … params-14 left research/labels/configs/, so the two | **manter** | comentários históricos do item 31 |
| `tests/test_benchmark_apptest.py:708` | from params-1" on params-1's own card — true, and unreadable as anything but | **manter** | comentários históricos do item 31 |
| `tests/test_intensification_min_depth.py:46` | # reference value 0.05 (params-13) sits inside that gap. | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:69` | # params-13 = params-12 + intensification_min_depth. Kept in sync with | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:70` | # research/labels/configs/cyclophaser_params-13.yaml by | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:71` | # test_params13_yaml_matches_this_module. | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:105` | # The params-13 reference value. | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:222` | """Under params-13 the phantom residual tail is gone and the series ends in | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:440` | """params-15 is the calibration reference (params-13 left the repo in item 31; | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_intensification_min_depth.py:441` | params-15 = params-13 + reclassify_index0 + incipient_plateau_spare_intensification, | **migrar** | linhas 69-71: comentário diz sincronizar com arquivo removido por teste que não existe mais (hoje test_params15_yaml_matches_this_module) |
| `tests/test_item30_spare_intensification.py:144` | # params-14 left the repo in item 31. It was params-15 minus this one key | **manter** | params-14 reconstruído em memória como params-15 − 1 chave (instrumento congelado derivado) |
| `tests/test_item30_spare_intensification.py:190` | key (params-14 was exactly that, and left the repo in item 31).""" | **manter** | params-14 reconstruído em memória como params-15 − 1 chave (instrumento congelado derivado) |
| `tests/test_layer_inspector.py:983` | #    mature 0.80 — the same floors as params-14, which left the repo in item 31; | **manter** | comentários históricos |
| `tests/test_layer_inspector.py:1045` | # Measured 2026-09-25 under params-14; identical under params-15, whose one | **manter** | comentários históricos |
| `tests/test_reclassify_index0.py:192` | # params-13 — the calibration reference this rule was measured under. | **manter** | valores de params-13 embutidos inline (PARAMS_13_PV) — instrumento congelado |
| `tools/calibration_app/README.md:164` | file in `research/labels/configs/` (since item 31 only params-15; params-1..14 | **manter** | aponta a recuperação; linha 279 é histórico |
| `tools/calibration_app/README.md:279` | 20203947 under params-9) and `boundary_padding` (a filter parameter that governs | **manter** | aponta a recuperação; linha 279 é histórico |
| `tools/calibration_app/app.py:448` | # backward-compatibility reason: params-1..11 were | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:455` | # same reason, one config later: params-1..12 all | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:474` | # backward-compatibility reason: params-1..13 all | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:482` | # Item 30: every config up to params-14 predates | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:743` | # config up to params-14 predates it). Set in both directions, like the | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:744` | # extrema block below: otherwise importing params-14 into a session with the | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:1734` | "with decay. Uncheck to reproduce params-13 and every earlier " | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:1812` | # training series under params-9 (amplitude), local vs global changes the | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/app.py:1828` | "20203947 under params-9. That is why it sits above steps 4-6 rather " | **manter** | comentários/ajuda de compatibilidade com YAMLs antigos que usuários ainda importam |
| `tools/calibration_app/benchmark_core.py:19` | different weeks with different understanding of the problem (params-5 and -6 | **migrar** | docstring/comentário afirmam que item19_core.CONFIG fixa params-10 — CONFIG não existe mais; 'onze configurações' também |
| `tools/calibration_app/benchmark_core.py:20` | record 0, params-9 records 6). It is carried as a labelled historical | **migrar** | docstring/comentário afirmam que item19_core.CONFIG fixa params-10 — CONFIG não existe mais; 'onze configurações' também |
| `tools/calibration_app/benchmark_core.py:22` | * **`item19_core.CONFIG` is never repointed.** It pins params-10 deliberately, as | **migrar** | docstring/comentário afirmam que item19_core.CONFIG fixa params-10 — CONFIG não existe mais; 'onze configurações' também |
| `tools/calibration_app/benchmark_core.py:78` | # params-10; nothing here writes to it. See the module docstring. | **migrar** | docstring/comentário afirmam que item19_core.CONFIG fixa params-10 — CONFIG não existe mais; 'onze configurações' também |
| `tools/calibration_app/benchmark_core.py:280` | """Numeric order, so params-2 sorts before params-10 (lexicographic does not).""" | **migrar** | docstring/comentário afirmam que item19_core.CONFIG fixa params-10 — CONFIG não existe mais; 'onze configurações' também |
| `tools/calibration_app/benchmark_tab.py:346` | "different knowledge of the problem (params-5 and " | **manter** | ajuda do anotador histórico (bad_cases_count de YAMLs antigos) |
| `tools/calibration_app/benchmark_tab.py:347` | "-6 record 0, params-9 records 6). Comparing two of " | **manter** | ajuda do anotador histórico (bad_cases_count de YAMLs antigos) |
| `tools/calibration_app/layer_inspector.py:544` | settings, and under params-14 with the depth floor active. | **migrar** | docstrings dizem que a fidelidade é fixada 'sob params-14'; o teste hoje usa params-15 |
| `tools/calibration_app/layer_inspector.py:858` | params-14 with the floor active. | **migrar** | docstrings dizem que a fidelidade é fixada 'sob params-14'; o teste hoje usa params-15 |

Nota: a lista de opções do prompt (migrar / aposentar / recuperar de 33ea489) não cobre menção puramente histórica que não carrega arquivo; para esses casos a proposta é **manter** (ver desvios).

## 0.2 (c) Ocorrências de "params-15"

`git grep -P 'params[-_]?15(?![0-9])'` (pega também `params_15`, `PARAMS_15`, `params15`): **317 ocorrências** — VIVAS **66**, HISTÓRICAS **251**. Regra: VIVA = código, app, testes, READMEs, docs de usuário, benchmark e o [Unreleased] do CHANGELOG; HISTÓRICA = future_work.md, split.yaml, swell_item30/README.md e relatórios/diagnósticos de frente.

| arquivo:linha | classe | trecho |
|---|---|---|
| `CHANGELOG.md:12` | VIVA | ### Changed — default behaviour: the package defaults are now `params-15` (item 31, stage 2b, `45f0600`; approved by Dan |
| `CHANGELOG.md:16` | VIVA | now the calibration reference `research/labels/configs/cyclophaser_params-15.yaml`. |
| `CHANGELOG.md:105` | VIVA | the params-15 column. |
| `CHANGELOG.md:128` | VIVA | * **`research/labels/configs/` holds only `params-15`.** params-1 to params-14 |
| `cyclophaser/determine_periods.py:429` | VIVA | The defaults are the calibration reference ``params-15`` |
| `cyclophaser/determine_periods.py:430` | VIVA | (research/labels/configs/cyclophaser_params-15.yaml). They fall in two |
| `cyclophaser/determine_periods.py:547` | VIVA | moved it to ``"edge"``, the padding of the calibration reference params-15: |
| `cyclophaser/determine_periods.py:871` | VIVA | The defaults are the calibration reference ``params-15`` |
| `cyclophaser/determine_periods.py:872` | VIVA | (research/labels/configs/cyclophaser_params-15.yaml). They fall in two |
| `cyclophaser/determine_periods.py:1399` | VIVA | The defaults are the calibration reference ``params-15`` |
| `cyclophaser/determine_periods.py:1400` | VIVA | (research/labels/configs/cyclophaser_params-15.yaml). They fall in two |
| `docs/future_work.md:3380` | HISTÓRICA | ## 30. Plateau overwriting intensification — selection, parts 1–3, opt-in rule and params-15 — **closed, merged 2026-09- |
| `docs/future_work.md:3519` | HISTÓRICA | **Part 3 — opt-in rule, params-15 CANDIDATE, adjudicated labels (2026-09-27, |
| `docs/future_work.md:3529` | HISTÓRICA | - **Configs.** `params-15` is `params-14` plus the key; `params-14` is |
| `docs/future_work.md:3581` | HISTÓRICA | evaluation under params-15 (27 Sept 2026, 20:43Z, 249 tracks), none of the 5 |
| `docs/future_work.md:3585` | HISTÓRICA | - **V: spent.** The 5 validation tracks were seen under params-15 before they |
| `docs/future_work.md:3590` | HISTÓRICA | - **Test exposure.** 19 test series were evaluated in the Grid under params-15: |
| `docs/future_work.md:3596` | HISTÓRICA | unfilled, so params-15 remains a CANDIDATE and is not the reference |
| `docs/future_work.md:3602` | HISTÓRICA | - **Adoption (Danilo): "adotado sem validação independente".** params-15 is |
| `docs/future_work.md:3605` | HISTÓRICA | table in `research/labels/README.md` now runs to params-15, which also clears |
| `docs/future_work.md:3626` | HISTÓRICA | - R1, rerun: params-15 changes exactly the 5 adjudicated TRAIN series of 54, |
| `docs/future_work.md:3823` | HISTÓRICA | ## 31. params-15 as the package default — stages 0, 1, 2a, 2b, 2c — **closed, merged 2026-09-28** (merge `0a469eb`) |
| `docs/future_work.md:3825` | HISTÓRICA | **Merge (2026-09-28).** `research/item31-params15-default` @ `e31b727` merged into `develop-v2.1` with `--no-ff`, no PR, |
| `docs/future_work.md:3834` | HISTÓRICA | * **params-15 against the 2.0.0 defaults.** Of 31 keys, |
| `docs/future_work.md:3839` | HISTÓRICA | * **Reachability on TRAIN** (sequence changes from params-14 to params-15): |
| `docs/future_work.md:3861` | HISTÓRICA | \| params-15 \| 3/9 \| 6/6 \| 9/15 \| 10/16 \| 11/15 \| 4 \| |
| `docs/future_work.md:3865` | HISTÓRICA | Discordant pairs, params-15 against the 2.0.0 defaults: |
| `docs/future_work.md:3866` | HISTÓRICA | * C: 7 where params-15 is right and |
| `docs/future_work.md:3876` | HISTÓRICA | * they were seen under params-15 when it was adopted (E22); |
| `docs/future_work.md:3883` | HISTÓRICA | * Hits for params-15: 3/9 (33 %) on TEST against |
| `docs/future_work.md:3886` | HISTÓRICA | * On H alone, params-15 is below the 2.0.0 defaults (3 vs 4). |
| `docs/future_work.md:3890` | HISTÓRICA | params-15 final-map count, outside the verdict. **Its effect on the score was |
| `docs/future_work.md:3902` | HISTÓRICA | * Comparators: params-15, the 2.0.0 defaults and the constant. params-14 is |
| `docs/future_work.md:3906` | HISTÓRICA | * **Filtering.** The default filtering is params-15's, with `use_filter='auto'` |
| `docs/future_work.md:3907` | HISTÓRICA | and no presets. The hybrid (params-15 phases on 2.0.0 filtering) is parked. |
| `docs/future_work.md:3912` | HISTÓRICA | * **Approvals:** 2b (defaults = params-15), the `use_filter=False` fix |
| `docs/future_work.md:3932` | HISTÓRICA | ### Stage 2b — the defaults become params-15 (`c5217b5` → `45f0600`) |
| `docs/future_work.md:3940` | HISTÓRICA | \| EQ2 control (params-15, spare=False) \| `3756392e…` \| |
| `docs/future_work.md:3942` | HISTÓRICA | \| EQ3 (`determine_periods` == G() == G(params-15)) \| train 54/54, example 1/1, test 16/16, batch test 3/3, validation 5/ |
| `docs/usage.rst:89` | VIVA | ``params-15``. This is a change of default behaviour relative to 2.0.0; every |
| `research/labels/README.md:53` | VIVA | `cyclophaser_params-15.yaml`, the calibration reference.** params-1 to |
| `research/labels/README.md:71` | VIVA | \| **`cyclophaser_params-15.yaml`** \| `5aa61f2dec710029b46a47668812d14e6d552517b7bca8912a8e00fd130ccf04` \| **the calibrat |
| `research/labels/README.md:73` | VIVA | **Do not normalise or reformat params-15.** Its identity is its file hash: the |
| `research/labels/diagnostics/item30/PREDICTIONS_part3.md:1` | HISTÓRICA | # Item 30, parte 3 — regra opt-in e params-15: previsões (registradas 2026-09-27T15:05:32Z, antes de qualquer implementa |
| `research/labels/diagnostics/item30/PREDICTIONS_part3.md:13` | HISTÓRICA | R4 nas 49 séries de treino NÃO adjudicadas, o escore de params-15 é |
| `research/labels/diagnostics/item30/PREDICTIONS_part3.md:16` | HISTÓRICA | de sequência params-15 ≤ params-14 em 5/5 e < em ≥ 3/5. Medido depois. |
| `research/labels/diagnostics/item30/PREDICTIONS_part3.md:17` | HISTÓRICA | Se Danilo não rotular, params-15 só pode ser adotado registrado como |
| `research/labels/diagnostics/item30/REPORT_part3.md:1` | HISTÓRICA | # Item 30, part 3 — opt-in rule, params-15 candidate, adjudicated labels (checkpoint) |
| `research/labels/diagnostics/item30/REPORT_part3.md:36` | HISTÓRICA | \| **R4** \| the 49 non-adjudicated TRAIN series score identically under params-14 and params-15 \| **CONFIRMED.** Every bl |
| `research/labels/diagnostics/item30/REPORT_part3.md:57` | HISTÓRICA | ## Score, params-14 → params-15 (evaluator, `--batch-train swell_item30`) |
| `research/labels/diagnostics/item30/REPORT_part3.md:66` | HISTÓRICA | counterfactual, and params-15 reproduces the counterfactual exactly (R1). So |
| `research/labels/diagnostics/item30/REPORT_part3.md:69` | HISTÓRICA | outputs are in `part3_eval_params14.txt` and `part3_eval_params15.txt`. |
| `research/labels/diagnostics/item30/REPORT_part3.md:124` | HISTÓRICA | label \| params-14 \| params-15), plus a board. |
| `research/labels/diagnostics/item30/REPORT_part3.md:161` | HISTÓRICA | same replica without the extra condition reproduces params-15 on 54/54 TRAIN |
| `research/labels/diagnostics/item30/REPORT_part3.md:204` | HISTÓRICA | evaluation under params-15 (27 Sept 2026, 20:43Z, 249 tracks), none of the 5 |
| `research/labels/diagnostics/item30/REPORT_part3.md:208` | HISTÓRICA | - **V: spent.** The 5 validation tracks were seen under params-15 before they |
| `research/labels/diagnostics/item30/REPORT_part3.md:213` | HISTÓRICA | - **Test exposure.** 19 test series were evaluated in the Grid under params-15: |
| `research/labels/diagnostics/item30/REPORT_part3.md:219` | HISTÓRICA | unfilled, so params-15 remains a CANDIDATE and is not the reference |
| `research/labels/diagnostics/item30/REPORT_part3.md:225` | HISTÓRICA | - **Adoption (Danilo): "adotado sem validação independente".** params-15 is |
| `research/labels/diagnostics/item30/REPORT_part3.md:228` | HISTÓRICA | table in `research/labels/README.md` now runs to params-15, which also clears |
| `research/labels/diagnostics/item30/outside_signal.py:11` | HISTÓRICA | per track (params-14 \| params-15) and a board. The per-track table and every |
| `research/labels/diagnostics/item30/outside_signal.py:19` | HISTÓRICA | params-15 on every track (TRAIN and swell), which is checked. |
| `research/labels/diagnostics/item30/outside_signal.py:80` | HISTÓRICA | "params14_seq": core.seq(r["final"]), "params15_seq": core.seq(a["final15"]), |
| `research/labels/diagnostics/item30/outside_signal.py:90` | HISTÓRICA | "params-15": figs_cf.norm_runs(a["final15"])}, |
| `research/labels/diagnostics/item30/outside_signal.py:107` | HISTÓRICA | cfg14, cfg15 = core.load_config("params-14"), core.load_config("params-15") |
| `research/labels/diagnostics/item30/outside_signal.py:123` | HISTÓRICA | # replica fidelity: the full rule, replicated, equals params-15 on every track |
| `research/labels/diagnostics/item30/outside_signal.py:160` | HISTÓRICA | print(f"STEP 2 replica fidelity (full rule replicated == params-15): TRAIN " |
| `research/labels/diagnostics/item30/outside_signal_output.txt:6` | HISTÓRICA | STEP 2 replica fidelity (full rule replicated == params-15): TRAIN 54/54, swell 196/196 |
| `research/labels/diagnostics/item30/part3_eval_params15.txt:3` | HISTÓRICA | config: <repo>/research/labels/configs/cyclophaser_params-15.yaml |
| `research/labels/diagnostics/item30/part3_measure.py:1` | HISTÓRICA | """Item 30, part 3, step 4 — R1, R3, R4 and the three-block score, params-14 vs params-15. |
| `research/labels/diagnostics/item30/part3_measure.py:17` | HISTÓRICA | part3_eval_params14.txt / part3_eval_params15.txt, figs_part3/*.png. |
| `research/labels/diagnostics/item30/part3_measure.py:61` | HISTÓRICA | print(f"R1: {len(train)} TRAIN series; params-15 final map differs from params-14 " |
| `research/labels/diagnostics/item30/part3_measure.py:131` | HISTÓRICA | "params-15": c["maps"]["params-13"]}      # case() ran cfg15 there |
| `research/labels/diagnostics/item30/part3_measure.py:157` | HISTÓRICA | cfg14, cfg15 = core.load_config("params-14"), core.load_config("params-15") |
| `research/labels/diagnostics/item30/part3_measure.py:163` | HISTÓRICA | e14, e15 = evaluator("params-14"), evaluator("params-15") |
| `research/labels/diagnostics/item30/part3_measure.py:165` | HISTÓRICA | (HERE / "part3_eval_params15.txt").write_text(e15) |
| `research/labels/diagnostics/item30/part3_measure.py:169` | HISTÓRICA | print(f"R4/score block {name!r}: identical under params-14 and params-15 = " |
| `research/labels/diagnostics/item30/part3_measure_output.txt:4` | HISTÓRICA | R1: 54 TRAIN series; params-15 final map differs from params-14 in 5: 19810854, 19860380, 19870927, 19940445, 20120297 |
| `research/labels/diagnostics/item30/part3_measure_output.txt:9` | HISTÓRICA | R4/score block 'TRAIN · real': identical under params-14 and params-15 = True |
| `research/labels/diagnostics/item30/part3_measure_output.txt:10` | HISTÓRICA | R4/score block 'TRAIN · synthetic': identical under params-14 and params-15 = True |
| `research/labels/diagnostics/item30/part3_measure_output.txt:11` | HISTÓRICA | R4/score block 'TRAIN · ALL': identical under params-14 and params-15 = True |
| `research/labels/diagnostics/item30/part3_measure_output.txt:12` | HISTÓRICA | R4/score block 'BATCH swell_item30 · TRAIN': identical under params-14 and params-15 = True |
| `research/labels/diagnostics/item30/part3_measure_output.txt:13` | HISTÓRICA | R4/score block 'ADJUDICATED': identical under params-14 and params-15 = False |
| `research/labels/diagnostics/item30/post_merge_checks.py:8` | HISTÓRICA | 3. R1 rerun: params-15 changes the final map of exactly the 5 adjudicated TRAIN |
| `research/labels/diagnostics/item30/post_merge_checks.py:64` | HISTÓRICA | pm.r1(train, core.load_config("params-14"), core.load_config("params-15")) |
| `research/labels/diagnostics/item30/post_merge_checks_output.txt:5` | HISTÓRICA | R1: 54 TRAIN series; params-15 final map differs from params-14 in 5: 19810854, 19860380, 19870927, 19940445, 20120297 |
| `research/labels/diagnostics/item31/DESIGN.md:1` | HISTÓRICA | # Item 31 — params-15 as the package default: stage 0, declared design |
| `research/labels/diagnostics/item31/DESIGN.md:5` | HISTÓRICA | branch). Branch `research/item31-params15-default`, from `develop-v2.1` at |
| `research/labels/diagnostics/item31/DESIGN.md:36` | HISTÓRICA | `determine_periods`, and from the raw YAML of params-15, so YAML types are kept. |
| `research/labels/diagnostics/item31/DESIGN.md:38` | HISTÓRICA | * params-15 sets **31** keys, all of which are signature parameters: 8 filtering |
| `research/labels/diagnostics/item31/DESIGN.md:57` | HISTÓRICA | * **Six signature parameters are not in params-15:** `x`, `hemisphere`, |
| `research/labels/diagnostics/item31/DESIGN.md:59` | HISTÓRICA | `prominence` (default `None`) affects detection, and params-15 leaves it at |
| `research/labels/diagnostics/item31/DESIGN.md:64` | HISTÓRICA | The measurement compares params-14 with params-15 on TRAIN: 35 original real |
| `research/labels/diagnostics/item31/DESIGN.md:78` | HISTÓRICA | * In 4 of the 5, params-15 removes the incipient phase altogether; in 19870927 |
| `research/labels/diagnostics/item31/DESIGN.md:82` | HISTÓRICA | TRAIN series the rule changes nothing, so a comparison of params-15 against |
| `research/labels/diagnostics/item31/DESIGN.md:94` | HISTÓRICA | TEST series, were evaluated visually in the Grid **under params-15**, which is |
| `research/labels/diagnostics/item31/DESIGN.md:97` | HISTÓRICA | blind test of params-15's output. It can be called a first scoring of that |
| `research/labels/diagnostics/item31/DESIGN.md:98` | HISTÓRICA | output against labels that were not scored under params-15. That claim rests |
| `research/labels/diagnostics/item31/DESIGN.md:118` | HISTÓRICA | If one was looked at under params-15, stage 1 is not a first scoring either. |
| `research/labels/diagnostics/item31/DESIGN.md:121` | HISTÓRICA | recorded and may include params-15. E23 is now kind **S** in |
| `research/labels/diagnostics/item31/DESIGN.md:186` | HISTÓRICA | * **P15**: `research/labels/configs/cyclophaser_params-15.yaml` via |
| `research/labels/diagnostics/item31/DESIGN.md:241` | HISTÓRICA | number of the 16 on which the final maps of params-14 and params-15 differ. It |
| `research/labels/diagnostics/item31/DESIGN.md:304` | HISTÓRICA | * **It tests** params-15 as a whole against the current defaults and against |
| `research/labels/diagnostics/item31/DESIGN.md:305` | HISTÓRICA | the constant, on 16 labels. Those labels were never scored under params-15, |
| `research/labels/diagnostics/item31/DESIGN.md:317` | HISTÓRICA | > de calibração visual (E01), foram vistas sob params-15 na revisão que o |
| `research/labels/diagnostics/item31/DESIGN.md:325` | HISTÓRICA | part of the visual calibration set (E01), were seen under params-15 in the |
| `research/labels/diagnostics/item31/DESIGN.md:343` | HISTÓRICA | \| \| params-15 \| defaults \| |
| `research/labels/diagnostics/item31/DESIGN.md:379` | HISTÓRICA | to params-15. It covers the 17 behavioural differences in `param_table.md`, |
| `research/labels/diagnostics/item31/DESIGN.md:397` | HISTÓRICA | public wrapper around it. At stage 0, with params-15 passed explicitly, the two |
| `research/labels/diagnostics/item31/DESIGN.md:407` | HISTÓRICA | \| EQ2 \| the same layout over the 54 (47 + 7 batch train), no kwargs \| **`923e1a03…`**. EQ1 alone cannot see `spare_inten |
| `research/labels/diagnostics/item31/DESIGN.md:408` | HISTÓRICA | \| EQ3 \| `determine_periods(s)` == `G(s; {}, {})` == `G(s; **params-15 explicit)`, element for element \| identical on eve |
| `research/labels/diagnostics/item31/DESIGN.md:444` | HISTÓRICA | **Recommendation: ship params-15's filter with its phase parameters.** |
| `research/labels/diagnostics/item31/DESIGN.md:457` | HISTÓRICA | 1. **params-15 is one calibrated object.** Every phase parameter from items 19 |
| `research/labels/diagnostics/item31/DESIGN.md:468` | HISTÓRICA | \| params-15 \| 22/33 \| 19/35 \| 27/33 \| |
| `research/labels/diagnostics/item31/DESIGN.md:471` | HISTÓRICA | unfiltered vorticity. **The params-15 filter is therefore not dominant.** It |
| `research/labels/diagnostics/item31/DESIGN.md:476` | HISTÓRICA | is pursued, it needs its own front. **Decided (§8.4): params-15's filtering; |
| `research/labels/diagnostics/item31/DESIGN.md:505` | HISTÓRICA | params-15. The E23 row of `exposure_table.md` is updated to kind **S**, and |
| `research/labels/diagnostics/item31/DESIGN.md:507` | HISTÓRICA | 4. **Default filtering = params-15's filtering:** |
| `research/labels/diagnostics/item31/DESIGN.md:514` | HISTÓRICA | **The hybrid is parked** (params-15's phases on the 2.0.0 filtering, §7.2). |
| `research/labels/diagnostics/item31/DESIGN.md:529` | HISTÓRICA | the clean-up front, by Danilo's decision. **params-15 stays.** Old records in |
| `research/labels/diagnostics/item31/DESIGN.md:533` | HISTÓRICA | may be the second source, **provided the sidebar differs from params-15 in at |
| `research/labels/diagnostics/item31/DESIGN.md:540` | HISTÓRICA | 8. **2b approved.** The package defaults are params-15. The checkpoint |
| `research/labels/diagnostics/item31/DESIGN.md:635` | HISTÓRICA | \| `test_benchmark_apptest.py` \| params-1 (CFG_A), params-5 (third column), params-11 (CFG_B, reference option, cards) \|  |
| `research/labels/diagnostics/item31/DESIGN.md:636` | HISTÓRICA | \| `test_intensification_min_depth.py::test_params13_yaml_matches_this_module` \| params-13 \| The reference file becomes * |
| `research/labels/diagnostics/item31/DESIGN.md:637` | HISTÓRICA | \| `test_item30_spare_intensification.py` (2 tests) \| params-14 \| **(i)** `params15_reproduces_the_counterfactual`: `cfg1 |
| `research/labels/diagnostics/item31/DESIGN.md:638` | HISTÓRICA | \| `test_layer_inspector.py` (§7 fidelity, 4 tests) \| params-14 \| `_params_14` → `_params_15`, and the tests are renamed. |
| `research/labels/diagnostics/item31/DESIGN.md:713` | HISTÓRICA | \| G3 \| the 14 files are absent; `git show 33ea489:<path>` hashes match; params-15 intact and alone in `configs/` \| PASS  |
| `research/labels/diagnostics/item31/DESIGN.md:715` | HISTÓRICA | \| G5 \| the evaluator's stdout equals 33ea489's evaluator under params-15 and under package defaults \| identical (params- |
| `research/labels/diagnostics/item31/DESIGN.md:723` | HISTÓRICA | `test_the_sidebar_differs_from_params15_in_a_declared_parameter`. |
| `research/labels/diagnostics/item31/DESIGN.md:731` | HISTÓRICA | order (params-15 first, sidebar second) and the pins unchanged. The result was |
| `research/labels/diagnostics/item31/DESIGN.md:747` | HISTÓRICA | \| G3 removed + recoverable, params-15 intact \| PASS \| **PASS** \| |
| `research/labels/diagnostics/item31/DESIGN.md:749` | HISTÓRICA | \| G5 evaluator stdout == 33ea489 (params-15; defaults) \| identical \| **identical** (3258 and 3103 chars) \| |
| `research/labels/diagnostics/item31/DESIGN.md:753` | HISTÓRICA | of (a) on params-15 is a stderr note from the evaluator: |
| `research/labels/diagnostics/item31/DESIGN.md:756` | HISTÓRICA | ## 11. Stage 2b — the defaults become params-15 (CHECKPOINT, pending Danilo's approval) |
| `research/labels/diagnostics/item31/DESIGN.md:764` | HISTÓRICA | take the params-15 defaults, normalised to the annotated types: |
| `research/labels/diagnostics/item31/DESIGN.md:771` | HISTÓRICA | default equals params-15 (`use_filter` `'auto'` ≡ `True`). |
| `research/labels/diagnostics/item31/DESIGN.md:796` | HISTÓRICA | \| EQ2 control: params-15 with spare=False explicit \| `3756392e…` \| **`3756392e…`** \| |
| `research/labels/diagnostics/item31/DESIGN.md:797` | HISTÓRICA | \| EQ3 `determine_periods(s)` == `G(s)` == `G(s, params-15)` \| identical everywhere \| **54/54 train, 1/1 example, 16/16 t |
| `research/labels/diagnostics/item31/DESIGN.md:914` | HISTÓRICA | \| Inspector (`build_args_periods`) \| its fallback table mirrors `get_periods` \| 2.0.0 table \| **params-15 table**. The a |
| `research/labels/diagnostics/item31/DESIGN.md:916` | HISTÓRICA | **Open, for Danilo:** should the sidebar's `_DEFAULTS` also move to params-15? |
| `research/labels/diagnostics/item31/DESIGN.md:920` | HISTÓRICA | params-15 (§10.2, `incipient_method` `geometric` vs `plateau`). Moving the |
| `research/labels/diagnostics/item31/DESIGN.md:994` | HISTÓRICA | \| `test_benchmark_apptest.py`: the sidebar column (positive control), `DECLARED_DIFF`, `_sidebar_yaml` \| the sidebar now |
| `research/labels/diagnostics/item31/benchmark_swap_mutation.txt:1` | HISTÓRICA | Item 31 addendum — MUTATION: tests/test_benchmark_apptest.py copied with _two_column_app adding the columns SWAPPED (par |
| `research/labels/diagnostics/item31/benchmark_swap_mutation.txt:5` | HISTÓRICA | PASSED tests/test_zz_mutation_swap_tmp.py::test_the_sidebar_differs_from_params15_in_a_declared_parameter |
| `research/labels/diagnostics/item31/benchmark_swap_mutation_2c.txt:1` | HISTÓRICA | Item 31 stage 2c — MUTATION: tests/test_benchmark_apptest.py copied with _two_column_app adding the columns SWAPPED (par |
| `research/labels/diagnostics/item31/benchmark_swap_mutation_2c.txt:5` | HISTÓRICA | PASSED tests/test_zz_mutation_swap_tmp.py::test_the_sidebar_differs_from_params15_in_a_declared_parameter |
| `research/labels/diagnostics/item31/constant_train.json:46` | HISTÓRICA | "params-15": { |
| `research/labels/diagnostics/item31/constant_train.json:96` | HISTÓRICA | "params-15": 9, |
| `research/labels/diagnostics/item31/constant_train.json:101` | HISTÓRICA | "params-15": 8, |
| `research/labels/diagnostics/item31/constant_train.json:106` | HISTÓRICA | "params-15": 2, |
| `research/labels/diagnostics/item31/constant_train.json:111` | HISTÓRICA | "params-15": 0, |
| `research/labels/diagnostics/item31/constant_train.json:116` | HISTÓRICA | "params-15": 0, |
| `research/labels/diagnostics/item31/constant_train.json:121` | HISTÓRICA | "params-15": 0, |
| `research/labels/diagnostics/item31/constant_train.json:164` | HISTÓRICA | "params-15": { |
| `research/labels/diagnostics/item31/constant_train.json:214` | HISTÓRICA | "params-15": 9, |
| `research/labels/diagnostics/item31/constant_train.json:219` | HISTÓRICA | "params-15": 8, |
| `research/labels/diagnostics/item31/constant_train.json:224` | HISTÓRICA | "params-15": 2, |
| `research/labels/diagnostics/item31/constant_train.json:229` | HISTÓRICA | "params-15": 0, |
| `research/labels/diagnostics/item31/constant_train.json:234` | HISTÓRICA | "params-15": 0, |
| `research/labels/diagnostics/item31/constant_train.json:239` | HISTÓRICA | "params-15": 0, |
| `research/labels/diagnostics/item31/constant_train.py:22` | HISTÓRICA | score_phase_sequences): params-15, package defaults and the constant — plus, |
| `research/labels/diagnostics/item31/constant_train.py:23` | HISTÓRICA | for task 7 only, params-15's phase parameters on the current default filter. These are |
| `research/labels/diagnostics/item31/constant_train.py:124` | HISTÓRICA | p15 = core.load_config("params-15") |
| `research/labels/diagnostics/item31/constant_train.py:125` | HISTÓRICA | # Task 7 support, INFORMATION ONLY: params-15's phase parameters on the CURRENT |
| `research/labels/diagnostics/item31/constant_train.py:127` | HISTÓRICA | cfgs = {"params-15": p15, "defaults": core.load_config(None), |
| `research/labels/diagnostics/item31/constant_train.txt:15` | HISTÓRICA | params-15            incipient hits  8/17 none agreed 14/16 false refusals  6  correct 22/33  sequence 19/35  mature 27/ |
| `research/labels/diagnostics/item31/constant_train.txt:19` | HISTÓRICA | 14  intensification > mature > decay                                       params-15 9  defaults 0  p15-phase\|def-filter |
| `research/labels/diagnostics/item31/constant_train.txt:20` | HISTÓRICA | 13  incipient > intensification > mature > decay                           params-15 8  defaults 11  p15-phase\|def-filte |
| `research/labels/diagnostics/item31/constant_train.txt:21` | HISTÓRICA | 3  intensification > mature > decay > residual                            params-15 2  defaults 0  p15-phase\|def-filter  |
| `research/labels/diagnostics/item31/constant_train.txt:22` | HISTÓRICA | 2  incipient > intensification                                            params-15 0  defaults 0  p15-phase\|def-filter  |
| `research/labels/diagnostics/item31/constant_train.txt:23` | HISTÓRICA | 2  incipient > intensification > mature > decay > residual                params-15 0  defaults 0  p15-phase\|def-filter  |
| `research/labels/diagnostics/item31/constant_train.txt:24` | HISTÓRICA | 1  incipient > intensification > mature > decay > intensification > mature > decay > residual params-15 0  defaults 0  p |
| `research/labels/diagnostics/item31/constant_train.txt:38` | HISTÓRICA | params-15            incipient hits  8/17 none agreed 14/16 false refusals  6  correct 22/33  sequence 19/35  mature 27/ |
| `research/labels/diagnostics/item31/constant_train.txt:42` | HISTÓRICA | 14  intensification > mature > decay                                       params-15 9  defaults 0  p15-phase\|def-filter |
| `research/labels/diagnostics/item31/constant_train.txt:43` | HISTÓRICA | 13  incipient > intensification > mature > decay                           params-15 8  defaults 11  p15-phase\|def-filte |
| `research/labels/diagnostics/item31/constant_train.txt:44` | HISTÓRICA | 3  intensification > mature > decay > residual                            params-15 2  defaults 0  p15-phase\|def-filter  |
| `research/labels/diagnostics/item31/constant_train.txt:45` | HISTÓRICA | 2  incipient > intensification                                            params-15 0  defaults 0  p15-phase\|def-filter  |
| `research/labels/diagnostics/item31/constant_train.txt:46` | HISTÓRICA | 2  incipient > intensification > mature > decay > residual                params-15 0  defaults 0  p15-phase\|def-filter  |
| `research/labels/diagnostics/item31/constant_train.txt:47` | HISTÓRICA | 1  incipient > intensification > mature > decay > intensification > mature > decay > residual params-15 0  defaults 0  p |
| `research/labels/diagnostics/item31/exposure_table.json:365` | HISTÓRICA | "config": "**params-15**", |
| `research/labels/diagnostics/item31/exposure_table.json:392` | HISTÓRICA | "config": "UNRECORDED \u2014 may include **params-15**", |
| `research/labels/diagnostics/item31/exposure_table.json:394` | HISTÓRICA | "what": "Danilo CONFIRMS having displayed TEST blocks in the Benchmark tab (sequence + mature scored against the 16 test |
| `research/labels/diagnostics/item31/exposure_table.md:30` | HISTÓRICA | \| E22 \| D \| ALL16+BATCH3 \| **params-15** \| 2026-09-27 \| All 19 test series (+20203389) evaluated visually in the Grid UN |
| `research/labels/diagnostics/item31/exposure_table.md:31` | HISTÓRICA | \| E23 \| S \| ALL16 \| UNRECORDED — may include **params-15** \| since 2026-09-18 \| Danilo CONFIRMS having displayed TEST bl |
| `research/labels/diagnostics/item31/exposure_table.py:114` | HISTÓRICA | ("E22", "D", ALL16 + "+" + BATCH3, "**params-15**", "2026-09-27", |
| `research/labels/diagnostics/item31/exposure_table.py:122` | HISTÓRICA | ("E23", "S", ALL16, "UNRECORDED — may include **params-15**", "since 2026-09-18", |
| `research/labels/diagnostics/item31/exposure_table.py:125` | HISTÓRICA | "include params-15. Answered 2026-09-28 (stage 0 had it as '?').", |
| `research/labels/diagnostics/item31/footprint_train.py:1` | HISTÓRICA | """Item 31, stage 0, task 6 support — TRAIN footprint of "params-15 as default". |
| `research/labels/diagnostics/item31/footprint_train.py:9` | HISTÓRICA | TRAIN series, with params-15 passed EXPLICITLY (defaults untouched): |
| `research/labels/diagnostics/item31/footprint_train.py:15` | HISTÓRICA | B. BEHAVIOUR-ONLY EQUIVALENCES of param_table.md, checked on data: params-15 with |
| `research/labels/diagnostics/item31/footprint_train.py:22` | HISTÓRICA | between package defaults and params-15. Per-series lines are printed (TRAIN). |
| `research/labels/diagnostics/item31/footprint_train.py:53` | HISTÓRICA | pv15, gp15 = core.load_config("params-15") |
| `research/labels/diagnostics/item31/footprint_train.py:87` | HISTÓRICA | print(f"\nA. generator agreement G1 == G2 (params-15 explicit): {agreeA}/{total}") |
| `research/labels/diagnostics/item31/footprint_train.py:90` | HISTÓRICA | print("\nC. footprint, package defaults → params-15") |
| `research/labels/diagnostics/item31/footprint_train.py:98` | HISTÓRICA | print("\nper series (TRAIN), sequence default → params-15, incipient end:") |
| `research/labels/diagnostics/item31/footprint_train.txt:3` | HISTÓRICA | A. generator agreement G1 == G2 (params-15 explicit): 54/54 |
| `research/labels/diagnostics/item31/footprint_train.txt:6` | HISTÓRICA | C. footprint, package defaults → params-15 |
| `research/labels/diagnostics/item31/footprint_train.txt:13` | HISTÓRICA | per series (TRAIN), sequence default → params-15, incipient end: |
| `research/labels/diagnostics/item31/future_work_numbers.json:11` | HISTÓRICA | "params15_keys": 31, |
| `research/labels/diagnostics/item31/future_work_numbers.py:68` | HISTÓRICA | p15_train = ct["current"]["scores"]["params-15"] |
| `research/labels/diagnostics/item31/future_work_numbers.py:72` | HISTÓRICA | "params15_keys": pt["params_15_keys"], |
| `research/labels/diagnostics/item31/gate_2a.py:12` | HISTÓRICA | params-15 is present with its recorded hash. |
| `research/labels/diagnostics/item31/gate_2a.py:16` | HISTÓRICA | params-15 and under package defaults (TRAIN only, test never read). The old |
| `research/labels/diagnostics/item31/gate_2a.py:85` | HISTÓRICA | p15 = REPO / "research/labels/configs/cyclophaser_params-15.yaml" |
| `research/labels/diagnostics/item31/gate_2a.py:89` | HISTÓRICA | ["cyclophaser_params-15.yaml"] |
| `research/labels/diagnostics/item31/gate_2a.py:90` | HISTÓRICA | ok["G3 14 removed + recoverable (git show hash), params-15 intact"] = g3 |
| `research/labels/diagnostics/item31/gate_2a.py:101` | HISTÓRICA | old_p15 = str(a.old_worktree / "research/labels/configs/cyclophaser_params-15.yaml") |
| `research/labels/diagnostics/item31/gate_2a.py:104` | HISTÓRICA | for name, argv_old, argv_new in (("params-15", ["--config", old_p15], ["--config", new_p15]), |
| `research/labels/diagnostics/item31/gate_2a.py:116` | HISTÓRICA | ok["G5 evaluator stdout identical to 33ea489 (params-15, defaults)"] = g5 |
| `research/labels/diagnostics/item31/gate_2a.txt:3` | HISTÓRICA | G5 evaluator params-15: stdout identical to 33ea489 = True (3258 chars); package = ['PKG <repo>/cyclophaser/__init__.py' |
| `research/labels/diagnostics/item31/gate_2a.txt:8` | HISTÓRICA | PASS  G3 14 removed + recoverable (git show hash), params-15 intact |
| `research/labels/diagnostics/item31/gate_2a.txt:10` | HISTÓRICA | PASS  G5 evaluator stdout identical to 33ea489 (params-15, defaults) |
| `research/labels/diagnostics/item31/gate_2b.py:12` | HISTÓRICA | Predicted 923e1a03…. Control: params-15 with |
| `research/labels/diagnostics/item31/gate_2b.py:15` | HISTÓRICA | EQ3  determine_periods(s) == G(s) with no arguments == G(s, params-15 explicit), |
| `research/labels/diagnostics/item31/gate_2b.py:78` | HISTÓRICA | pv15, gp15 = core.load_config("params-15") |
| `research/labels/diagnostics/item31/gate_2b.py:137` | HISTÓRICA | print("\nEQ3 determine_periods == G() == G(params-15):", |
| `research/labels/diagnostics/item31/gate_2b.txt:7` | HISTÓRICA | EQ3 determine_periods == G() == G(params-15): train_54 54/54, example_file 1/1, test_16 16/16, batch_test_3 3/3, validat |
| `research/labels/diagnostics/item31/p15_expected_digest.py:7` | HISTÓRICA | params-15 the default: |
| `research/labels/diagnostics/item31/p15_expected_digest.py:10` | HISTÓRICA | "\\n", same sha256 — but with params-15 passed EXPLICITLY: |
| `research/labels/diagnostics/item31/p15_expected_digest.py:24` | HISTÓRICA | so the 47-id digest is identical under params-14 and params-15 and cannot see |
| `research/labels/diagnostics/item31/p15_expected_digest.py:68` | HISTÓRICA | pv15, gp15 = core.load_config("params-15") |
| `research/labels/diagnostics/item31/p15_expected_digest.py:88` | HISTÓRICA | f"EXPECTED after stage 2 (params-15 explicit, use_filter='auto') = {expected}", |
| `research/labels/diagnostics/item31/p15_expected_digest.py:89` | HISTÓRICA | f"  same 47 under params-14 = {e47_14}  (identical to params-15: {e47_14 == expected}" |
| `research/labels/diagnostics/item31/p15_expected_digest.py:91` | HISTÓRICA | f"EXPECTED over 54 (47 + 7 batch TRAIN, same layout), params-15 = {e54}", |
| `research/labels/diagnostics/item31/p15_expected_digest.txt:6` | HISTÓRICA | EXPECTED after stage 2 (params-15 explicit, use_filter='auto') = 3a6de26501c6fed05091025480cacf7502fe2d7d0076ba8479a9ecc |
| `research/labels/diagnostics/item31/p15_expected_digest.txt:7` | HISTÓRICA | same 47 under params-14 = 3a6de26501c6fed05091025480cacf7502fe2d7d0076ba8479a9ecca81703b99  (identical to params-15: Tru |
| `research/labels/diagnostics/item31/p15_expected_digest.txt:8` | HISTÓRICA | EXPECTED over 54 (47 + 7 batch TRAIN, same layout), params-15 = 923e1a0389ae1fb627172564ea35063791523ae035d867b3a01d18a0 |
| `research/labels/diagnostics/item31/param_table.json:11` | HISTÓRICA* | "params_15_keys": 31, |
| `research/labels/diagnostics/item31/param_table.json:12` | HISTÓRICA* | "params_15_keys_matched_to_a_signature": 31, |
| `research/labels/diagnostics/item31/param_table.json:28` | HISTÓRICA* | "signature_params_absent_from_params_15": [ |
| `research/labels/diagnostics/item31/param_table.md:1` | HISTÓRICA | # Item 31 — package defaults vs params-15 (generated) |
| `research/labels/diagnostics/item31/param_table.md:5` | HISTÓRICA | \| parameter \| default atual \| params-15 \| grupo \| igual? strict / value / behaviour \| nota \| |
| `research/labels/diagnostics/item31/param_table.md:39` | HISTÓRICA | Signature parameters params-15 does not set (they take the default under both, so they cannot differ): |
| `research/labels/diagnostics/item31/param_table.md:92` | HISTÓRICA | "params_15_keys": 31, |
| `research/labels/diagnostics/item31/param_table.md:93` | HISTÓRICA | "params_15_keys_matched_to_a_signature": 31, |
| `research/labels/diagnostics/item31/param_table.md:109` | HISTÓRICA | "signature_params_absent_from_params_15": [ |
| `research/labels/diagnostics/item31/param_table.py:1` | HISTÓRICA | """Item 31, stage 0, task 1 — parameter table: package defaults vs params-15. |
| `research/labels/diagnostics/item31/param_table.py:4` | HISTÓRICA | and `determine_periods`) and from the raw YAML of params-15 (yaml.safe_load, so |
| `research/labels/diagnostics/item31/param_table.py:12` | HISTÓRICA | * params-15    — the value in `research/labels/configs/cyclophaser_params-15.yaml` |
| `research/labels/diagnostics/item31/param_table.py:82` | HISTÓRICA | doc = yaml.safe_load(core.config_path("params-15").read_text()) |
| `research/labels/diagnostics/item31/param_table.py:125` | HISTÓRICA | "params_15_keys": len(p15), |
| `research/labels/diagnostics/item31/param_table.py:126` | HISTÓRICA | "params_15_keys_matched_to_a_signature": len(in15), |
| `research/labels/diagnostics/item31/param_table.py:139` | HISTÓRICA | "signature_params_absent_from_params_15": [r["param"] for r in rows |
| `research/labels/diagnostics/item31/param_table.py:144` | HISTÓRICA | out = ["# Item 31 — package defaults vs params-15 (generated)", "", |
| `research/labels/diagnostics/item31/param_table.py:147` | HISTÓRICA | "\| parameter \| default atual \| params-15 \| grupo \| igual? strict / value / behaviour \| nota \|", |
| `research/labels/diagnostics/item31/param_table.py:154` | HISTÓRICA | out += ["", "Signature parameters params-15 does not set (they take the default " |
| `research/labels/diagnostics/item31/reachability_train.py:1` | HISTÓRICA | """Item 31, stage 0, task 2 — which TRAIN series change phase SEQUENCE, params-14 → params-15. |
| `research/labels/diagnostics/item31/reachability_train.py:36` | HISTÓRICA | cfg14, cfg15 = core.load_config("params-14"), core.load_config("params-15") |
| `research/labels/diagnostics/item31/reachability_train.py:37` | HISTÓRICA | assert cfg14[0] == cfg15[0], "filter params differ between params-14 and params-15" |
| `research/labels/diagnostics/item31/reachability_train.py:39` | HISTÓRICA | print("config diff params-14 → params-15: phase_params." |
| `research/labels/diagnostics/item31/reachability_train.txt:2` | HISTÓRICA | config diff params-14 → params-15: phase_params.incipient_plateau_spare_intensification False → True, nothing else |
| `research/labels/diagnostics/item31/recovery_table.py:4` | HISTÓRICA | from research/labels/configs/; params-15 stays. Before anything is deleted, |
| `research/labels/diagnostics/item31/recovery_table.py:54` | HISTÓRICA | assert (CONFIGS / "cyclophaser_params-15.yaml").is_file() |
| `research/labels/diagnostics/item31/stage1_output.txt:10` | HISTÓRICA | config params-15: research/labels/configs/cyclophaser_params-15.yaml sha256 5aa61f2dec710029b46a47668812d14e6d552517b7bc |
| `research/labels/diagnostics/item31/stage1_run.py:1` | HISTÓRICA | """Item 31, stage 1 — THE single scoring run of params-15 against the 16 TEST labels. |
| `research/labels/diagnostics/item31/stage1_run.py:27` | HISTÓRICA | P15   — research/labels/configs/cyclophaser_params-15.yaml via |
| `research/labels/diagnostics/item31/stage1_run.py:349` | HISTÓRICA | cfg = {"P15": core.load_config("params-15"), "DEF": core.load_config(None), |
| `research/labels/diagnostics/item31/stage1_run.py:354` | HISTÓRICA | for name in ("params-15", "params-14"): |
| `research/labels/diagnostics/item31/stage1_smoke_train.py:35` | HISTÓRICA | NAMES = {"P15": "params-15", "DEF": "defaults", "CONST": "constant"} |
| `research/labels/diagnostics/item31/stage1_smoke_train.py:51` | HISTÓRICA | cfg = {"P15": core.load_config("params-15"), "DEF": core.load_config(None), |
| `research/labels/split.yaml:272` | HISTÓRICA | foram vistos sob params-15 antes de qualquer rotulagem, então a previsão V não pode mais |
| `research/labels/swell_item30/README.md:219` | HISTÓRICA | evaluation under params-15 (27 Sept 2026, 20:43Z, 249 tracks), none of the 5 |
| `research/labels/swell_item30/README.md:223` | HISTÓRICA | - **V: spent.** The 5 validation tracks were seen under params-15 before they |
| `research/labels/swell_item30/README.md:228` | HISTÓRICA | - **Test exposure.** 19 test series were evaluated in the Grid under params-15: |
| `research/labels/swell_item30/README.md:234` | HISTÓRICA | unfilled, so params-15 remains a CANDIDATE and is not the reference |
| `research/labels/swell_item30/README.md:248` | HISTÓRICA | - **Reason:** the 5 tracks were seen under params-15 before any labelling, so |
| `tests/legacy_defaults.py:3` | VIVA | Item 31 moved the package defaults to params-15. Tests whose assertions were |
| `tests/test_benchmark_apptest.py:51` | VIVA | # params-15, the calibration reference (Danilo's addendum, 2026-09-28). Since |
| `tests/test_benchmark_apptest.py:52` | VIVA | # stage 2c the sidebar OPENS with the package defaults, which ARE params-15, so |
| `tests/test_benchmark_apptest.py:55` | VIVA | # filter_params.cutoff_high = 48 (package default and params-15: 18). It changes |
| `tests/test_benchmark_apptest.py:57` | VIVA | # `test_the_sidebar_differs_from_params15_in_a_declared_parameter` asserts it; |
| `tests/test_benchmark_apptest.py:62` | VIVA | CFG_B = "cyclophaser_params-15.yaml" |
| `tests/test_benchmark_apptest.py:273` | VIVA | assert "params-15" in ref.options |
| `tests/test_benchmark_apptest.py:274` | VIVA | ref.set_value("params-15") |
| `tests/test_benchmark_apptest.py:276` | VIVA | assert at.session_state["bench_reference"] == "params-15" |
| `tests/test_benchmark_apptest.py:351` | VIVA | def test_the_sidebar_differs_from_params15_in_a_declared_parameter(): |
| `tests/test_benchmark_apptest.py:354` | VIVA | silently become a second copy of params-15.""" |
| `tests/test_benchmark_apptest.py:358` | VIVA | sec, key, in_sidebar, in_params15 = DECLARED_DIFF |
| `tests/test_benchmark_apptest.py:360` | VIVA | assert _doc_for(CFG_B)[sec][key] == in_params15 |
| `tests/test_benchmark_apptest.py:372` | VIVA | "the sidebar and params-15 agree on all of " |
| `tests/test_benchmark_apptest.py:381` | VIVA | assert b["series"] == _expected_for(CFG_B, ids), "column 1 is not params-15" |
| `tests/test_config_defaults.py:13` | VIVA | * params-15 lacks exactly one key (`prominence`), and the app imports it with |
| `tests/test_config_defaults.py:38` | VIVA | P15 = LABELS / "configs" / "cyclophaser_params-15.yaml" |
| `tests/test_config_defaults.py:107` | VIVA | def test_params15_lacks_exactly_prominence(): |
| `tests/test_config_defaults.py:155` | VIVA | # params-15 filters by RELATIVE prominence 0.3; the filled None for the |
| `tests/test_intensification_min_depth.py:439` | VIVA | def test_params15_yaml_matches_this_module(): |
| `tests/test_intensification_min_depth.py:440` | VIVA | """params-15 is the calibration reference (params-13 left the repo in item 31; |
| `tests/test_intensification_min_depth.py:441` | VIVA | params-15 = params-13 + reclassify_index0 + incipient_plateau_spare_intensification, |
| `tests/test_intensification_min_depth.py:446` | VIVA | "configs", "cyclophaser_params-15.yaml") |
| `tests/test_item30_spare_intensification.py:135` | VIVA | # ── the 5 adjudicated TRAIN cases: params-15 == the counterfactual ────────── |
| `tests/test_item30_spare_intensification.py:137` | VIVA | def test_params15_reproduces_the_counterfactual_in_the_five(): |
| `tests/test_item30_spare_intensification.py:144` | VIVA | # params-14 left the repo in item 31. It was params-15 minus this one key |
| `tests/test_item30_spare_intensification.py:145` | VIVA | # (asserted in item 31, stage 0), so it is params-15 with the key OFF. |
| `tests/test_item30_spare_intensification.py:146` | VIVA | cfg15 = core.load_config("params-15") |
| `tests/test_item30_spare_intensification.py:189` | VIVA | """params-15's text with the key's line removed — a real config without the |
| `tests/test_item30_spare_intensification.py:191` | VIVA | lines = _config_bytes("params-15").decode().splitlines(keepends=True) |
| `tests/test_item30_spare_intensification.py:209` | VIVA | def test_importing_params15_turns_the_rule_on(): |
| `tests/test_item30_spare_intensification.py:215` | VIVA | res = load(_config_bytes("params-15")) |
| `tests/test_layer_inspector.py:880` | VIVA | PARAMS_15 = REPO_ROOT / "research" / "labels" / "configs" / "cyclophaser_params-15.yaml" |
| `tests/test_layer_inspector.py:886` | VIVA | # The app's own YAML converters for the three integer-valued keys (params-15 |
| `tests/test_layer_inspector.py:907` | VIVA | def _params_15(): |
| `tests/test_layer_inspector.py:908` | VIVA | """(filter_params, phase_params) of params-15, phase values typed as the app |
| `tests/test_layer_inspector.py:925` | VIVA | pv, phase = _params_15() |
| `tests/test_layer_inspector.py:982` | VIVA | # ── Fidelity with the depth floors ACTIVE (params-15: intensification 0.05, |
| `tests/test_layer_inspector.py:984` | VIVA | #    params-15 adds only incipient_plateau_spare_intensification=True, so the |
| `tests/test_layer_inspector.py:990` | VIVA | pv, phase = _params_15() |
| `tests/test_layer_inspector.py:999` | VIVA | def test_params_15_has_both_depth_floors_active(): |
| `tests/test_layer_inspector.py:1000` | VIVA | """Guard for the tests below: if params-15 ever stopped setting the floors, |
| `tests/test_layer_inspector.py:1002` | VIVA | _, phase = _params_15() |
| `tests/test_layer_inspector.py:1007` | VIVA | def test_ribbon_step_six_equals_get_periods_under_params_15(vort_cache): |
| `tests/test_layer_inspector.py:1008` | VIVA | pv, _ = _params_15() |
| `tests/test_layer_inspector.py:1023` | VIVA | def test_ledger_accepted_set_is_the_package_mask_under_params_15(vort_cache, kind): |
| `tests/test_layer_inspector.py:1045` | VIVA | # Measured 2026-09-25 under params-14; identical under params-15, whose one |
| `tests/test_regression_baseline.py:79` | VIVA | # The package defaults moved to params-15 (item 31), so baseline_default / |
| `tools/calibration_app/README.md:164` | VIVA | file in `research/labels/configs/` (since item 31 only params-15; params-1..14 |
| `tools/calibration_app/app.py:2269` | VIVA | # params-15 (prominence_relative=0.3, decay_tail_amplitude_fraction=0.3), so an |
| `tools/calibration_app/layer_inspector.py:146` | VIVA | # Item 31: the package defaults moved to params-15; these follow them (the |

`HISTÓRICA*` = `item31/param_table.json`: artefato histórico, mas `tests/test_config_defaults.py` lê o arquivo (só a chave `rows`); as ocorrências são nomes de campos. Conferir no Passo 1 que o renome não o afeta.

Ocorrências VIVAS que dependem do NOME do arquivo (quebram no renome se não forem atualizadas juntas): `tests/test_benchmark_apptest.py` (CFG_B e a opção `params-15` do seletor), `tests/test_config_defaults.py` (P15), `tests/test_intensification_min_depth.py`, `tests/test_layer_inspector.py` (PARAMS_15), `tests/test_item30_spare_intensification.py` (`core.load_config("params-15")`, via `item30_core`), e as docstrings de `cyclophaser/determine_periods.py` que citam o caminho.

## 0.2 (d) Default de `boundary_padding`

`git grep boundary_padding` em `cyclophaser/`, `tools/`, `docs/`, `README.md`, `CHANGELOG.md` e YAMLs: **126 ocorrências**. `README.md` não menciona o parâmetro.

**Defaults na assinatura (lidos por `inspect.signature`, `defaults_in_text.py`):** `process_vorticity` = 'edge', `determine_periods` = 'edge', `lanczos_filter` = 'reflect', `lanczos_bandpass_filter` = 'reflect'.

**`get_periods` tem default próprio?** **NÃO** — `get_periods` não recebe `boundary_padding` (recebe a série já filtrada); suas docstrings só CITAM o default de `process_vorticity`. Quem tem default próprio: `process_vorticity` e `determine_periods` (`"edge"`) e, no módulo do filtro, `lanczos_filter`, `lanczos_bandpass_filter` e `_convolve_same` (`"reflect"`) — um default que o prompt não listou.

| arquivo:linha | natureza | trecho |
|---|---|---|
| `CHANGELOG.md:28` | tabela do CHANGELOG [Unreleased] (2.0.0 → agora) | \| `boundary_padding` \| `"reflect"` \| `"edge"` \| |
| `CHANGELOG.md:537` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | (`boundary_padding="reflect"`, see below), the derivative Savgol had become the |
| `CHANGELOG.md:560` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | \| `boundary_padding` \| `"zero"` \| **`"reflect"`** \| |
| `CHANGELOG.md:563` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | They had to move together: with `boundary_padding="reflect"` and a non-zero |
| `CHANGELOG.md:579` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | **`boundary_padding` now defaults to `"reflect"`** |
| `CHANGELOG.md:600` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | > **How to reproduce earlier results:** pass `boundary_padding="zero"` **and** |
| `CHANGELOG.md:614` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | It was introduced as a palliative for exactly the artifact `boundary_padding` now |
| `CHANGELOG.md:619` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | whereas `boundary_padding="reflect"` takes it to 0.42 at no amplitude cost. |
| `CHANGELOG.md:621` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | With `boundary_padding="reflect"` it is worse than redundant, it is harmful — see |
| `CHANGELOG.md:653` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | **`boundary_padding` — opt-in fix for the Lanczos zero-padding edge artifact** |
| `CHANGELOG.md:670` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | `boundary_padding` accepts `"reflect"`, `"edge"` and `"zero"` (the latter |
| `CHANGELOG.md:691` | texto de CHANGELOG — entradas antigas [Unreleased→2.0.0]; histórico da mudança zero→reflect | 0/51 bad cases with `use_filter=true`, `cutoff_high=18`, `boundary_padding=reflect` |
| `cyclophaser/determine_periods.py:423` | ASSINATURA process_vorticity (default) | boundary_padding="edge"): |
| `cyclophaser/determine_periods.py:439` | docstring (process_vorticity: nota de defaults calibrados) | ``boundary_padding="edge"``, ``use_filter='auto'``) were calibrated ONLY |
| `cyclophaser/determine_periods.py:483` | docstring (process_vorticity: parâmetro + boundary_padding note) | boundary_padding (str, optional): How the series is extended beyond its own |
| `cyclophaser/determine_periods.py:487` | docstring (process_vorticity: parâmetro + boundary_padding note) | "boundary_padding note" below. Only meaningful when ``use_filter`` is |
| `cyclophaser/determine_periods.py:512` | docstring (process_vorticity: parâmetro + boundary_padding note) | boundary_padding note |
| `cyclophaser/determine_periods.py:551` | docstring (process_vorticity: parâmetro + boundary_padding note) | ``boundary_padding="zero"`` explicitly. Note that switching modes changes |
| `cyclophaser/determine_periods.py:563` | docstring (process_vorticity: parâmetro + boundary_padding note) | from 24 to **0** together with the ``boundary_padding`` default above. Passing |
| `cyclophaser/determine_periods.py:567` | docstring (process_vorticity: parâmetro + boundary_padding note) | It was introduced as a palliative for exactly the artefact ``boundary_padding`` |
| `cyclophaser/determine_periods.py:575` | docstring (process_vorticity: parâmetro + boundary_padding note) | With ``boundary_padding="reflect"`` it is worse than redundant, it is |
| `cyclophaser/determine_periods.py:593` | docstring (process_vorticity: parâmetro + boundary_padding note) | ``boundary_padding="reflect"`` trades one boundary artefact for another. |
| `cyclophaser/determine_periods.py:613` | validação / texto de DeprecationWarning | lanfil._validate_padding(boundary_padding) |
| `cyclophaser/determine_periods.py:619` | validação / texto de DeprecationWarning | "boundary artefact, which boundary_padding now fixes at its source, " |
| `cyclophaser/determine_periods.py:621` | validação / texto de DeprecationWarning | "Combined with boundary_padding='reflect' it is actively harmful: " |
| `cyclophaser/determine_periods.py:718` | uso/passagem do parâmetro em código | boundary_padding=boundary_padding) |
| `cyclophaser/determine_periods.py:738` | uso/passagem do parâmetro em código | boundary_padding=boundary_padding) |
| `cyclophaser/determine_periods.py:881` | docstring (get_periods: nota de defaults calibrados — cita o default de process_vorticity) | ``boundary_padding="edge"``, ``use_filter='auto'``) were calibrated ONLY |
| `cyclophaser/determine_periods.py:1044` | docstring (get_periods, incipient_method: 'reflect' como regime calibrado) | ``boundary_padding="reflect"`` and ``use_smoothing=False``) — as the current defaults are. Default is ``"plate |
| `cyclophaser/determine_periods.py:1369` | ASSINATURA determine_periods (default) | boundary_padding: str = "edge", |
| `cyclophaser/determine_periods.py:1409` | docstring (determine_periods: nota de defaults calibrados) | ``boundary_padding="edge"``, ``use_filter='auto'``) were calibrated ONLY |
| `cyclophaser/determine_periods.py:1456` | docstring (determine_periods: parâmetro + nota) | palliative for the Lanczos zero-padding artefact that `boundary_padding` now fixes at its source, |
| `cyclophaser/determine_periods.py:1457` | docstring (determine_periods: parâmetro + nota) | and combined with `boundary_padding="reflect"` it is harmful (the endpoint splice becomes a step; |
| `cyclophaser/determine_periods.py:1477` | docstring (determine_periods: parâmetro + nota) | boundary_padding (str, optional): How the series is extended beyond its own ends |
| `cyclophaser/determine_periods.py:1485` | docstring (determine_periods: parâmetro + nota) | "boundary_padding note" in `process_vorticity` for the full mechanism, |
| `cyclophaser/determine_periods.py:1521` | docstring (determine_periods, incipient_method: idem) | ``boundary_padding="reflect"`` and ``use_smoothing=False``) — as the current defaults are. Default is ``"plate |
| `cyclophaser/determine_periods.py:1746` | uso/passagem do parâmetro em código | boundary_padding=boundary_padding |
| `cyclophaser/lanczos_filter.py:6` | comentário de módulo | # boundary_padding: "zero" (default) vs "reflect" / "edge" |
| `cyclophaser/lanczos_filter.py:39` | comentário de módulo | # ``boundary_padding`` selects the padding used instead: |
| `cyclophaser/lanczos_filter.py:56` | comentário de módulo | # who needs the old output must now pass ``boundary_padding="zero"`` |
| `cyclophaser/lanczos_filter.py:62` | comentário de módulo | # zero-padded lowpass endpoints.  With ``boundary_padding="reflect"`` it loses |
| `cyclophaser/lanczos_filter.py:73` | uso/passagem do parâmetro em código | def _validate_padding(boundary_padding): |
| `cyclophaser/lanczos_filter.py:74` | uso/passagem do parâmetro em código | if boundary_padding not in PADDING_MODES: |
| `cyclophaser/lanczos_filter.py:76` | uso/passagem do parâmetro em código | f"boundary_padding must be one of {PADDING_MODES}, got {boundary_padding!r}." |
| `cyclophaser/lanczos_filter.py:80` | ASSINATURA _convolve_same (default próprio) | def _convolve_same(variable, weights, boundary_padding="reflect"): |
| `cyclophaser/lanczos_filter.py:84` | docstring / corpo | ``np.pad`` and convolved in "valid" mode.  With ``boundary_padding="zero"`` |
| `cyclophaser/lanczos_filter.py:96` | docstring / corpo | boundary_padding (str): one of ``PADDING_MODES``. See the module |
| `cyclophaser/lanczos_filter.py:103` | docstring / corpo | ValueError: if *boundary_padding* is not a recognised mode, or if the |
| `cyclophaser/lanczos_filter.py:106` | docstring / corpo | _validate_padding(boundary_padding) |
| `cyclophaser/lanczos_filter.py:108` | docstring / corpo | if boundary_padding == "zero": |
| `cyclophaser/lanczos_filter.py:116` | docstring / corpo | if n < 2 and boundary_padding == "reflect": |
| `cyclophaser/lanczos_filter.py:121` | docstring / corpo | padded = np.pad(data, (left, right), mode=boundary_padding) |
| `cyclophaser/lanczos_filter.py:159` | ASSINATURA lanczos_filter (default próprio) | def lanczos_filter(variable, window_length_lanczo, frequency, boundary_padding="reflect"): |
| `cyclophaser/lanczos_filter.py:167` | docstring / corpo | boundary_padding (str, optional): How the series is extended beyond its |
| `cyclophaser/lanczos_filter.py:180` | docstring / corpo | ValueError: if *boundary_padding* is not one of ``PADDING_MODES``. |
| `cyclophaser/lanczos_filter.py:183` | docstring / corpo | filtered_variable = _convolve_same(variable, weights, boundary_padding) |
| `cyclophaser/lanczos_filter.py:216` | ASSINATURA lanczos_bandpass_filter (default próprio) | boundary_padding="reflect"): |
| `cyclophaser/lanczos_filter.py:225` | docstring / corpo | boundary_padding (str, optional): How the series is extended beyond its |
| `cyclophaser/lanczos_filter.py:238` | docstring / corpo | ValueError: if *boundary_padding* is not one of ``PADDING_MODES``. |
| `cyclophaser/lanczos_filter.py:241` | uso/passagem do parâmetro em código | filtered_variable = _convolve_same(variable, weights, boundary_padding) |
| `docs/future_work.md:262` | registro histórico | ### `boundary_padding` (opt-in, default `"zero"`) |
| `docs/future_work.md:310` | registro histórico | `boundary_padding="reflect"` is *less* disruptive than with `"zero"` — measured |
| `docs/future_work.md:332` | registro histórico | boundary_padding: reflect |
| `docs/future_work.md:401` | registro histórico | with `boundary_padding="reflect"` as default and the `use_filter=True` bug fixed). |
| `docs/future_work.md:518` | registro histórico | whether the now-corrected Lanczos stage (`boundary_padding="reflect"` plus the |
| `docs/future_work.md:674` | registro histórico | With `boundary_padding='edge'`, the raw and filtered series disagree on |
| `docs/future_work.md:680` | registro histórico | above, and behind item 3c's `r(t₀)` measurements for `boundary_padding`. |
| `docs/future_work.md:774` | registro histórico | 1. `use_filter=False` → `cutoff_low`, `cutoff_high`, `boundary_padding` |
| `docs/future_work.md:2037` | registro histórico | widget: `length_scale` and `boundary_padding`. |
| `docs/future_work.md:2315` | registro histórico | `boundary_padding`). Under `params-12` the parameter is **inert** on both |
| `docs/future_work.md:3175` | registro histórico | `boundary_padding='edge'` flipping the sign at t0, 7 of 51 real tracks — and |
| `docs/future_work.md:4013` | registro histórico | `boundary_padding='edge'` is the default. Re-measured under the current |
| `docs/usage.rst:80` | texto de doc de usuário | - **boundary_padding**: (str, optional) How the series is extended beyond its ends before the Lanczos convolut |
| `docs/usage.rst:99` | texto de doc de usuário | ``use_smoothing_twice=False``, ``boundary_padding="edge"``, |
| `research/labels/configs/cyclophaser_params-15.yaml:64` | YAML (params-15, conteúdo intacto) | boundary_padding: edge |
| `tools/calibration_app/README.md:178` | texto do README do app | 5. the **"pre-filter-fix config"** warning when `boundary_padding` is missing. |
| `tools/calibration_app/README.md:279` | texto do README do app | 20203947 under params-9) and `boundary_padding` (a filter parameter that governs |
| `tools/calibration_app/app.py:216` | app: default lido da ASSINATURA (derivado) | "boundary_padding": sig["boundary_padding"], |
| `tools/calibration_app/app.py:271` | uso/passagem do parâmetro em código | def _parse_boundary_padding(v) -> str: |
| `tools/calibration_app/app.py:272` | uso/passagem do parâmetro em código | """Validating str converter for boundary_padding — same rationale as |
| `tools/calibration_app/app.py:280` | uso/passagem do parâmetro em código | f"boundary_padding must be one of {_BOUNDARY_PADDING_OPTS}, got {v!r}") |
| `tools/calibration_app/app.py:290` | uso/passagem do parâmetro em código | "boundary_padding":              ("boundary_padding",  _parse_boundary_padding), |
| `tools/calibration_app/app.py:461` | uso/passagem do parâmetro em código | # backward-compatibility reason as boundary_padding |
| `tools/calibration_app/app.py:487` | uso/passagem do parâmetro em código | # boundary_padding is OPTIONAL on import for the same reason as the optional |
| `tools/calibration_app/app.py:493` | uso/passagem do parâmetro em código | _OPTIONAL_FILTER_YAML_KEYS = {"boundary_padding"} |
| `tools/calibration_app/app.py:531` | uso/passagem do parâmetro em código | "boundary_padding":               ("boundary_padding",), |
| `tools/calibration_app/app.py:840` | uso/passagem do parâmetro em código | "boundary_padding":              str(boundary_padding), |
| `tools/calibration_app/app.py:879` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:896` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:902` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:932` | uso/passagem do parâmetro em código | savgol_poly, boundary_padding, |
| `tools/calibration_app/app.py:948` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1012` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1024` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1227` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1239` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1245` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1297` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1308` | uso/passagem do parâmetro em código | boundary_padding=boundary_padding, |
| `tools/calibration_app/app.py:1367` | uso/passagem do parâmetro em código | boundary_padding=boundary_padding, |
| `tools/calibration_app/app.py:1385` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1396` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:1439` | app: fallback LITERAL de preset ("reflect") | "boundary_padding":  str(preset.get("boundary_padding", "reflect")), |
| `tools/calibration_app/app.py:1523` | uso/passagem do parâmetro em código | #                                   boundary_padding, replace_endpoints_with_lowpass |
| `tools/calibration_app/app.py:1581` | uso/passagem do parâmetro em código | boundary_padding = st.selectbox( |
| `tools/calibration_app/app.py:1584` | app: widget inicializado de _DEFAULTS (derivado da assinatura) | index=_BOUNDARY_PADDING_OPTS.index(_DEFAULTS["boundary_padding"]), |
| `tools/calibration_app/app.py:1585` | uso/passagem do parâmetro em código | key="boundary_padding", |
| `tools/calibration_app/app.py:1624` | app: texto de ajuda do widget | "zero-padding boundary artifact, which `boundary_padding` now fixes at its " |
| `tools/calibration_app/app.py:1626` | app: texto de ajuda do widget | "Combined with `boundary_padding=reflect` it is actively harmful: both filters " |
| `tools/calibration_app/app.py:2287` | uso/passagem do parâmetro em código | "boundary_padding": boundary_padding, |
| `tools/calibration_app/app.py:2520` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:2531` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:2544` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:2665` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:2672` | uso/passagem do parâmetro em código | boundary_padding, |
| `tools/calibration_app/app.py:2690` | uso/passagem do parâmetro em código | savgol_poly, boundary_padding, |
| `tools/calibration_app/app.py:2925` | uso/passagem do parâmetro em código | savgol_poly, boundary_padding, |
| `tools/calibration_app/app.py:3129` | app: texto de ajuda (aba Documentation) | ### `boundary_padding` — Lanczos boundary condition |
| `tools/calibration_app/app.py:3151` | app: texto de ajuda (aba Documentation) | It was introduced as a palliative for the same zero-padding artifact described under `boundary_padding`, |
| `tools/calibration_app/app.py:3153` | app: texto de ajuda (aba Documentation) | `boundary_padding=reflect` it is **harmful**: both filters carry full amplitude at the edge, so the 5 % |
| `tools/calibration_app/benchmark_core.py:93` | app/benchmark: detecção de YAML pré-fix (ausência da chave) | "cutoff_high", "boundary_padding") |
| `tools/calibration_app/benchmark_core.py:103` | app/benchmark: detecção de YAML pré-fix (ausência da chave) | "This YAML carries no `boundary_padding`, which dates it to before the filter " |
| `tools/calibration_app/benchmark_core.py:168` | app/benchmark: detecção de YAML pré-fix (ausência da chave) | * `pre_filter_fix` — True when `boundary_padding` is absent, which dates the |
| `tools/calibration_app/benchmark_core.py:187` | app/benchmark: detecção de YAML pré-fix (ausência da chave) | "pre_filter_fix": "boundary_padding" not in fp, |
| `tools/calibration_app/benchmark_core.py:250` | app/benchmark: detecção de YAML pré-fix (ausência da chave) | "release has no `boundary_padding` — its filter convolution " |
| `tools/calibration_app/benchmark_tab.py:339` | app/benchmark: texto | "(`boundary_padding` is present)") |

**O rótulo "2.0.0" não é o release 2.0.0.** `passo0/v200_vs_defaults_json.py` compara, por AST (nada é importado nem rodado da tag), as assinaturas da tag `v2.0.0` (`5d99ae3`) com `research/labels/defaults_2.0.0.json`: **13 de 32 chaves iguais, 19 diferentes** — `boundary_padding` NÃO EXISTE na tag (o filtro publicado faz zero-padding). A tabela é a de develop no estágio 0 do item 31 (fonte declarada: research/labels/diagnostics/item31/param_table.json @ e42da8b (column 'default')). Portanto a coluna "2.0.0" da tabela do CHANGELOG [Unreleased] (linha 28: `"reflect"`), as docstrings "(`"reflect"` up to 2.0.0)" e `docs/usage.rst:80` descrevem develop antes do item 31, não o pacote publicado. Diferenças completas: `passo0/v200_vs_defaults_json.json`.

**Suplemento — testes** (fora do escopo pedido, mas o prompt deu pistas em `tests/test_boundary_padding.py`):

| tests/test_boundary_padding.py:linha | trecho |
|---|---|
| `27` | # ``boundary_padding`` (opt-in; default "zero" reproduces prior behaviour |
| `33` | #   1. The DEFAULT IS "reflect": omitting the parameter is byte-identical to |
| `169` | def test_default_argument_equals_explicit_reflect(n): |
| `185` | def test_default_differs_from_explicit_zero(n): |
| `186` | """...and the default is genuinely no longer 'zero'. |
| `204` | def test_process_vorticity_default_is_edge(cyclone_id, filter_params): |
| `230` | This is the coverage the old "default == zero" test used to provide: whatever |
| `231` | the default is, passing "zero" must still reproduce |
| `251` | def test_determine_periods_default_is_edge(cyclone_id): |
| `263` | def test_package_defaults_use_edge_end_to_end(): |
| `359` | def test_reflect_reduces_edge_dz_artifact_across_calibration_set(): |
| `390` | def test_reflect_changes_the_signal_only_where_expected(): |

Confirmação das pistas do prompt (conferidas, não copiadas): assinaturas em `determine_periods.py` :423 e :1369 (`"edge"`); docstrings :439, :881, :1409 (nota de defaults calibrados), :1044 e :1521 (`incipient_method`: `"reflect"` como regime calibrado, "as the current defaults are" — hoje o default é `"edge"`); `lanczos_filter.py:6` diz `"zero" (default)` e :39–56 dizem que o default é `"reflect"` — os dois textos divergem entre si e da assinatura de `process_vorticity`. Tabela do CHANGELOG [Unreleased] na linha 28. `tests/test_boundary_padding.py`: :204, :251 e :263 afirmam `"edge"` para `process_vorticity`/`determine_periods`; :169 afirma `"reflect"` para as funções do filtro; o comentário de cabeçalho :27 ainda diz `default "zero"`.

## 0.2 (e) Valores default escritos em texto

Localizador heurístico (`passo0/defaults_in_text.py`) — **364 linhas em 13 arquivos**, cada uma com o default da assinatura ao lado para o Passo 4. Tabela completa: `passo0/defaults_in_text.md`. `README.md` não escreve nenhum default.

| arquivo | linhas |
|---|---|
| `CHANGELOG.md` | 76 |
| `cyclophaser/determine_periods.py` | 129 |
| `cyclophaser/find_stages.py` | 32 |
| `cyclophaser/lanczos_filter.py` | 7 |
| `docs/api.rst` | 34 |
| `docs/calibration_tool.rst` | 10 |
| `docs/usage.rst` | 29 |
| `tools/calibration_app/README.md` | 3 |
| `tools/calibration_app/app.py` | 24 |
| `tools/calibration_app/benchmark_core.py` | 1 |
| `tools/calibration_app/label_tab.py` | 12 |
| `tools/calibration_app/layer_inspector.py` | 6 |
| `tools/calibration_app/package_args.py` | 1 |

**Defaults escritos como literal no código do app** (`.get("param", literal)`): 11 ocorrências, 6 divergem do default de `process_vorticity`/`get_periods`. Podem ser intencionais (semântica de YAML antigo sem a chave) — decidir no Passo 4:

| arquivo:linha | parâmetro | literal | assinatura | veredito |
|---|---|---|---|---|
| `tools/calibration_app/app.py:1436` | use_filter | `False` | process_vorticity='auto', determine_periods='auto' | **DIVERGE** |
| `tools/calibration_app/app.py:1437` | replace_endpoints_with_lowpass | `0` | process_vorticity=0, determine_periods=0 | igual |
| `tools/calibration_app/app.py:1438` | savgol_polynomial | `3` | process_vorticity=3, determine_periods=3 | igual |
| `tools/calibration_app/app.py:1439` | boundary_padding | `"reflect"` | process_vorticity='edge', determine_periods='edge', lanczos_filter='reflect', lanczos_bandpass_filter='reflect' | **DIVERGE** |
| `tools/calibration_app/app.py:1440` | cutoff_low | `168` | process_vorticity=168, determine_periods=168 | igual |
| `tools/calibration_app/app.py:1441` | cutoff_high | `48` | process_vorticity=18.0, determine_periods=18.0 | **DIVERGE** |
| `tools/calibration_app/app.py:1815` | mature_method | `_DEFAULTS["mature_method"]` | get_periods='amplitude', determine_periods='amplitude' | derivado (não é literal) |
| `tools/calibration_app/layer_inspector.py:879` | length_scale | `'global'` | get_periods='local', determine_periods='local' | **DIVERGE** |
| `tools/calibration_app/layer_inspector.py:880` | mature_method | `'derivative'` | get_periods='amplitude', determine_periods='amplitude' | **DIVERGE** |
| `tools/calibration_app/layer_inspector.py:881` | mature_amplitude_fraction | `0.90` | get_periods=0.9, determine_periods=0.9 | igual |
| `tools/calibration_app/layer_inspector.py:882` | mature_min_depth | `0.0` | get_periods=0.8, determine_periods=0.8 | **DIVERGE** |

## 0.2 (f) Caminhos absolutos versionados

`git grep -I -P '(/Users/|/home/|[A-Za-z]:\\)'` (arquivos de texto): **139 ocorrências em 41 arquivos**. Nenhuma em `cyclophaser/`, `tests/` ou `tools/`. PNG/binários não foram varridos.

| arquivo:linha | trecho |
|---|---|
| `docs/future_work.md:2658` | paths (`/Users/…`) in a public repository. |
| `docs/future_work.md:2724` | `/Users/…` paths) was honoured for this front's own outputs — its three scripts |
| `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:14` | `sys.prefix` = `<env>` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.json:2` | "worktree": "<repo>", |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.json:3` | "cyclophaser": "<repo>/cyclophaser/__init__.py", |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log:4` | cwd            : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log:5` | worktree       : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log:6` | sys.executable : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log:7` | sys.prefix     : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log:8` | cyclophaser    : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.json:2` | "worktree": "<repo>", |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.json:3` | "cyclophaser": "<repo>/cyclophaser/__init__.py", |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log:4` | cwd            : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log:5` | worktree       : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log:6` | sys.executable : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log:7` | sys.prefix     : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log:8` | cyclophaser    : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.log:4` | cwd            : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.log:6` | sys.executable : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.log:7` | sys.prefix     : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:9` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:11` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:13` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log:17` | current   : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_reverify/REPORT.md:28` | \| `sys.prefix` \| `<env>` \| |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_final_output_check.log:7` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_final_output_check.log:8` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_idx0_inventory.log:7` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_idx0_inventory.log:8` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_idx0_inventory.log:24` | config: ~/Downloads/cyclophaser_params-9.yaml |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_capture_pipeline_state.log:7` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_capture_pipeline_state.log:8` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_eval_raw.log:7` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_eval_raw.log:8` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_eval_raw.log:26` | config: ~/Downloads/cyclophaser_params-9.yaml |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:8` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:10` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:12` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:14` | config: <repo>/research/labels/configs/cyclophaser_params-9.yaml |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:21` | <repo>/research/labels/diagnostics/frontA_reverify/census_tip.py:273: PeakPropertyWarning: some peaks have a prominence  |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:23` | <repo>/research/labels/diagnostics/frontA_reverify/census_tip.py:273: PeakPropertyWarning: some peaks have a prominence  |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:25` | <repo>/research/labels/diagnostics/frontA_reverify/census_tip.py:273: PeakPropertyWarning: some peaks have a prominence  |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:27` | <repo>/research/labels/diagnostics/frontA_reverify/census_tip.py:273: PeakPropertyWarning: some peaks have a prominence  |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:29` | <repo>/research/labels/diagnostics/frontA_reverify/census_tip.py:273: PeakPropertyWarning: some peaks have a prominence  |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log:46` | wrote 4 files to <repo>/research/labels/diagnostics/frontA_reverify/outputs with tag 'step1b_params9' |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_eval_params9.log:3` | config: <repo>/research/labels/configs/cyclophaser_params-9.yaml |
| `research/labels/diagnostics/frontA_reverify/outputs/2_attribution.log:42` | wrote <repo>/research/labels/diagnostics/frontA_reverify/outputs/step2_attribution.csv |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:4` | cwd                  : <repo> |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:5` | sys.executable       : <env>/bin/python |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:6` | sys.prefix           : <env> |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:7` | cyclophaser.__file__ : <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:8` | determine_periods.py : <repo>/cyclophaser/determine_periods.py |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:10` | find_stages.py       : <repo>/cyclophaser/find_stages.py |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:12` | ASSERT OK: package loads from <repo> |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:14` | config: <repo>/research/labels/configs/cyclophaser_params-13.yaml |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log:36` | wrote 4 files to <repo>/research/labels/diagnostics/frontA_reverify/outputs with tag 'step2_params13' |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_fix_eval_before.txt:3` | config: ~/Downloads/cyclophaser_params-9.yaml |
| `research/labels/diagnostics/frontD/REPORT.md:11` | (`<env>/bin/python`), with |
| `research/labels/diagnostics/frontD/REPORT.md:537` | paths (`/Users/…`) in a public repository. |
| `research/labels/diagnostics/frontD/anchoring.txt:64` | wrote <repo>/research/labels/diagnostics/frontD/anchoring.json |
| `research/labels/diagnostics/frontD/census.txt:74` | wrote <repo>/research/labels/diagnostics/frontD/census.json |
| `research/labels/diagnostics/frontD/constant_baseline.txt:155` | wrote <repo>/research/labels/diagnostics/frontD/constant_baseline.json |
| `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:20` | `<repo>/cyclophaser/__init__.py` |
| `research/labels/diagnostics/item19/PROVENANCE.md:23` | <env>/bin/python |
| `research/labels/diagnostics/item19/PROVENANCE.md:25` | <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/item19/REPORT.md:23` | \| environment \| conda `cyclophaser`, `<env>/bin/python` \| |
| `research/labels/diagnostics/item19/REPORT.md:24` | \| cyclophaser imported from \| `<repo>/cyclophaser/__init__.py` — the working tree, **not** the published 1.7.3 \| |
| `research/labels/diagnostics/item20b/REPORT.md:22` | \| environment \| conda env `cyclophaser`, `<env>/bin/python` \| |
| `research/labels/diagnostics/item20b/REPORT_stage2.md:22` | \| environment \| conda env `cyclophaser`, `<env>/bin/python` \| |
| `research/labels/diagnostics/item20b/analyse_20b.txt:6` | wrote <repo>/research/labels/diagnostics/item20b/depth_table.csv (46 generating valleys) |
| `research/labels/diagnostics/item30/figs_cf_output.txt:1` | cyclophaser.__file__ = <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/item30/figs_cf_output.txt:2` | layer_inspector.__file__ = <repo>/tools/calibration_app/layer_inspector.py |
| `research/labels/diagnostics/item30/outside_signal_output.txt:1` | cyclophaser.__file__ = <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/item30/outside_signal_output.txt:2` | layer_inspector.__file__ = <repo>/tools/calibration_app/layer_inspector.py |
| `research/labels/diagnostics/item30/part3_eval_params14.txt:3` | config: <repo>/research/labels/configs/cyclophaser_params-14.yaml |
| `research/labels/diagnostics/item30/part3_eval_params15.txt:3` | config: <repo>/research/labels/configs/cyclophaser_params-15.yaml |
| `research/labels/diagnostics/item30/part3_measure_output.txt:1` | cyclophaser.__file__ = <repo>/cyclophaser/__init__.py |
| `research/labels/diagnostics/item30/part3_measure_output.txt:2` | layer_inspector.__file__ = <repo>/tools/calibration_app/layer_inspector.py |
| `research/labels/diagnostics/item31/gate_2a.txt:3` | G5 evaluator params-15: stdout identical to 33ea489 = True (3258 chars); package = ['PKG <repo>/cyclophaser/__init__.py' |
| `research/labels/diagnostics/item31/gate_2a.txt:4` | G5 evaluator package defaults: stdout identical to 33ea489 = True (3103 chars); package = ['PKG <repo>/cyclophaser/__ini |

## 0.2 (g) Os dois medidores de "mature correta" (nada medido)

| medidor | definição (arquivo:linha) | em uma frase |
|---|---|---|
| `evaluate_against_labels.py` → `labels_core.score_phase_sequences` | `research/labels/labels_core.py:803` | pontua **só séries cuja sequência de fases bate exatamente com o rótulo**; nelas, cada INÍCIO de fase (mature incluída, a primeira fase excluída, fronteiras `unsure` excluídas) acerta se |detectado − rótulo| ≤ o `tolerance_idx` daquela fronteira; séries com sequência diferente não geram distância nenhuma |
| `item19_core.pair_by_overlap` | `research/labels/diagnostics/item19/item19_core.py:142` (critério em `research/labels/diagnostics/item19/item19_core.py:221`) | pontua **todas** as séries: pareia o PRIMEIRO mature rotulado com o bloco mature detectado de maior sobreposição (sem sobreposição: o de ponto médio mais próximo) e acerta se início E fim estão a ≤ `MARGIN` = 6 passos |

Chamadas de `pair_by_overlap(` (12; inclui 3 REIMPLEMENTAÇÕES locais, em `frontC/measure_frontC.py`, `item20b/gate_stage2.py` e `item20b/measure_20b.py`):

* `research/labels/diagnostics/frontC/measure_frontC.py:75`
* `research/labels/diagnostics/frontC/measure_frontC.py:107`
* `research/labels/diagnostics/item19/item19_core.py:142`
* `research/labels/diagnostics/item19/item19_core.py:200`
* `research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md:68`
* `research/labels/diagnostics/item20b/gate_stage2.py:75`
* `research/labels/diagnostics/item20b/gate_stage2.py:113`
* `research/labels/diagnostics/item20b/measure_20b.py:129`
* `research/labels/diagnostics/item20b/measure_20b.py:245`
* `research/labels/diagnostics/item31/constant_train.py:78`
* `research/labels/diagnostics/item31/stage1_run.py:185`
* `tools/calibration_app/benchmark_core.py:479`

Chamadas de `score_phase_sequences(` (15):

* `research/labels/diagnostics/item31/constant_train.py:100`
* `research/labels/diagnostics/item31/stage1_run.py:199`
* `research/labels/evaluate_against_labels.py:341`
* `research/labels/evaluate_against_labels.py:349`
* `research/labels/evaluate_against_labels.py:361`
* `research/labels/evaluate_against_labels.py:371`
* `research/labels/labels_core.py:803`
* `tests/test_manual_labels.py:660`
* `tests/test_manual_labels.py:671`
* `tests/test_manual_labels.py:685`
* `tests/test_manual_labels.py:696`
* `tests/test_manual_labels.py:768`
* `tests/test_manual_labels.py:783`
* `tests/test_manual_labels.py:1283`
* `tools/calibration_app/benchmark_core.py:453`

O app (Benchmark) reporta os dois lado a lado, nomeados (`benchmark_core.py`: SEQUENCE_INSTRUMENT / MATURE_INSTRUMENT). Os dois contam populações diferentes; nenhum número foi medido aqui.

## 0.3 Manifesto de branches (somente leitura; nada apagado)

Remotas: **41** (`origin/*`, sem `HEAD`), ponta de develop `06d8550`. "em develop" = `git merge-base --is-ancestor`; à frente/atrás contra `origin/develop-v2.1`; citações = `git grep` do nome da branch na árvore de HEAD. Dados: `passo0/branches.json`.

"patch-eq." = NÃO ancestral, mas `git cherry origin/develop-v2.1 <branch>` só imprime `-` (todo commit tem um equivalente de patch em develop). Uma branch patch-equivalente NÃO está contida em develop: seus próprios hashes deixam de resolver se a ref sumir, por isso nunca é somada às ancestrais. "hashes citados" = `git grep` dos hashes curtos dos commits da branch que não estão em develop.

| branch | ponta | em develop? (ancestral) | patch-eq.? | +à frente/−atrás | conteúdo (arquivos alterados desde a base) | citada em | hashes citados | destino | motivo |
|---|---|---|---|---|---|---|---|---|---|
| `chore/b-remove-distance` | `2bb2bad` 2026-09-17 — test(front-b): drop a Streamlit-internal attribute from the distance-r | sim | — | +0/−103 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `chore/repo-cleanup` | `f17d802` 2026-09-28 — chore(cleanup): passo 0 — inventário somente leitura (manifesto de arq | **não** | não (+1) | +1/−0 | 19 arq.: research/cleanup/MANIFEST.md, research/cleanup/passo0 | — | — | **manter** | branch desta frente (em andamento) |
| `develop-v2.1` | `06d8550` 2026-09-28 — docs(item31): registrar o merge (0a469eb) no item 31 — suíte 1438/0 e  | sim | — | +0/−0 | — (nada fora de develop) | `CHANGELOG.md:297`, `CHANGELOG.md:402`, `docs/future_work.md:400` +118 | — | **manter** | branch de desenvolvimento |
| `diag/front-b-distance-inert` | `491a5d0` 2026-09-16 — diag(front-b): record the read-only diagnosis — `distance` is inert at | **não** | **sim** | +1/−106 | 21 arq.: research/labels/diagnostics | — | `research/labels/diagnostics/front_b/sensitivity_probe.py:27 (491a5d0)`, `research/labels/diagnostics/front_b/sweep_distance.py:53 (491a5d0)` | **tag de arquivo** | patch-equivalente a develop (git cherry só '-'), mas NÃO ancestral: o hash 491a5d0 é citado nos registros (ver 'hashes citados') e só resolve enquanto houver uma ref |
| `diag/series-sha256-mismatch` | `3ae6082` 2026-09-10 — diag(labels): measure series_sha256 mismatch for the 12 void synthetic | **não** | não (+1) | +1/−133 | 3 arq.: research/labels/diagnostics | `docs/future_work.md:846` | `docs/future_work.md:917 (3ae6082)` | **tag de arquivo** | decisão 6: branch de registro — script + relatório do item 10 só existem aqui; future_work cita a branch |
| `docs/front-a-findings` | `2ee2414` 2026-09-09 — docs: record Front A findings (index-0 boundary extremum type) | sim | — | +0/−143 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/front-f-i-ii-iii-findings` | `3aae83d` 2026-09-10 — docs: record F(i)(ii) and F(iii) findings in future_work.md | sim | — | +0/−134 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/front-g-closing` | `1ccb3db` 2026-09-15 — docs: front G closing record — verification, margin decision, mature b | sim | — | +0/−111 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/front-g-series-sha256-findings` | `02fe6f7` 2026-09-10 — docs: record the series_sha256 void-label investigation in future_work | sim | — | +0/−132 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/frontC-hash-provenance` | `e1b29cc` 2026-09-22 — docs(frontC): unattribute the legacy hash record, prove the layout dif | sim | — | +0/−74 | — (nada fora de develop) | `docs/future_work.md:2418` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/item13-close` | `1b99a57` 2026-09-23 — docs(item13): fechar o item 13 — resíduo "Frente E" encerrado por proc | sim | — | +0/−62 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/memory-g-e-closing` | `0f680c5` 2026-09-16 — docs: correct the mature rationale and the blindness claim in CLAUDE.m | sim | — | +0/−107 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/session-findings-register` | `e2ccdad` 2026-09-11 — docs: register the environment-dependence finding and the shadowed-det | sim | — | +0/−124 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `docs/session-findings-register-2` | `a06a2aa` 2026-09-11 — docs: register ABERTO 1, the CSV-format debt, and the CI coverage gap | sim | — | +0/−122 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `feat/app-flexible-track-reader` | `ba9af46` 2026-09-24 — docs(item29): registro final antes do merge — premissa (a) caída, dado | sim | — | +0/−50 | — (nada fora de develop) | `docs/future_work.md:3212`, `docs/future_work.md:3367` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `feat/dedicated-conda-env` | `d876a71` 2026-09-11 — docs: correct item 11(c)'s premise, decide the env front's gate, docum | sim | — | +0/−126 | — (nada fora de develop) | `docs/future_work.md:913`, `docs/future_work.md:1019` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `feat/freeze-synthetic-series` | `6e05467` 2026-09-10 — docs: record the synthetic-series-freeze front as closed, PASS (item 1 | sim | — | +0/−130 | — (nada fora de develop) | `docs/future_work.md:936` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `feat/front-g-manual-labels-source` | `727efd2` 2026-09-15 — test(synthetic): score phase timing against manual labels (front G) | sim | — | +0/−112 | — (nada fora de develop) | `docs/future_work.md:1397` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `feat/label-tab-navigation-overlays` | `f300420` 2026-09-14 — fix(label-tab): wrong-boundary drag, stale test selectors, viewport ov | sim | — | +0/−115 | — (nada fora de develop) | `docs/future_work.md:1300`, `docs/future_work.md:1479` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `feat/label-tab-toplevel` | `0c63145` 2026-09-15 — data: save 4 manual label re-labels made through the app (real, train  | **não** | não (+2) | +2/−113 | 6 arq.: research/labels/manual_labels.yaml, tests/browser_harness.py, tests/test_label_apptest.py, tests/test_manual_labels.py | — | — | **tag de arquivo** | decisão 1: 3 re-rotulagens de treino (0c63145) NÃO são recuperadas; entram como pendência aberta no documento único (Passo 2); código da UI superado |
| `fix/app-inert-params-signaling` | `20e003d` 2026-09-10 — docs: record the pytest gate exception before merging F(iii) | sim | — | +0/−137 | — (nada fora de develop) | `research/inert_params/REPORT_inertia_sweep.md:3` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `fix/idx0-boundary-extremum-type` | `6060c6d` 2026-09-09 — REFUTADO - NAO MERGEAR: forcar idx0 a peak, investigacao encerrada sem | **não** | não (+1) | +1/−144 | 31 arq.: cyclophaser/determine_periods.py, research/labels/diagnostics | `docs/future_work.md:579`, `docs/future_work.md:1121`, `research/labels/diagnostics/frontA_reverify/REPORT.md:70` +1 | `docs/future_work.md:1145 (6060c6d)`, `docs/future_work.md:2801 (6060c6d)`, `docs/future_work.md:2823 (6060c6d)` +54 | **tag de arquivo** | decisão 6: branch de registro — artefatos de Front A (6060c6d) contra os quais o item 27 comparou; commit marcado NÃO MERGEAR |
| `fix/inspector-crossing-layer-and-legend` | `7133570` 2026-09-09 — fix(app): inspector rel panel names the active signal and shows the cr | sim | — | +0/−141 | — (nada fora de develop) | — | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `fix/inspector-depth-params` | `52ecb04` 2026-09-25 — test(item30a): fixar só séries de treino nos testes de piso; guarda do | sim | — | +0/−45 | — (nada fora de develop) | `docs/future_work.md:3641`, `docs/future_work.md:3749`, `docs/future_work.md:3750` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `fix/inspector-min-depth-params` | `a2b639e` 2026-09-23 — fix(app): aceitar mature_min_depth e intensification_min_depth no Insp | **não** | não (+1) | +1/−60 | 3 arq.: docs/future_work.md, tests/test_layer_inspector.py, tools/calibration_app/layer_inspector.py | `docs/future_work.md:3715`, `docs/future_work.md:3761` | `docs/future_work.md:3715 (a2b639e)`, `docs/future_work.md:3761 (a2b639e)` | **tag de arquivo** | decisão 5: superada por 52ecb04 (item 30a) |
| `frontA-idx0-c2` | `e97eb17` 2026-09-24 — fix(item28): pontuar só o TREINO, documentar o no-op sem filtro, atrib | sim | — | +0/−54 | — (nada fora de develop) | `docs/future_work.md:2941`, `docs/future_work.md:3194`, `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:8` +1 | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `joss-submission` | `8348caf` 2024-10-29 — (auto) Paper PDF Draft | **não** | não (+22) | +26/−254 | 8 arq.: .github/workflows/generate_pdf.yml, paper/density_map_Aggregate.png, paper/life-cycle.png, paper/life_cycle.py | — | — | **tag de arquivo** | decisão 6: branch de registro — fonte do artigo JOSS (paper/); nada disso está em develop |
| `master` | `0df0ef5` 2026-06-16 — fix(deploy): pin Python via .python-version and relax app dependency p | sim | — | +0/−194 | — (nada fora de develop) | `.circleci/config.yml:111`, `README.md:17`, `docs/conf.py:4` +16 | — | **manter** | branch de release |
| `research/frontA-reverify` | `077d273` 2026-09-23 — research(frontA'): reverificação da frente A sob o detector correto —  | sim | — | +0/−65 | — (nada fora de develop) | `docs/future_work.md:2787`, `research/labels/diagnostics/frontA_reverify/REPORT.md:4` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/frontC-intensification-depth` | `38951f7` 2026-09-22 — docs(frontC): register front 24 — gate PASS, merged; three divergences | sim | — | +0/−77 | — (nada fora de develop) | `docs/future_work.md:2283`, `research/labels/diagnostics/frontC/REPORT.md:3` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/frontD-stage0-census` | `80e0551` 2026-09-23 — docs(frontD): record the later reading — ARTEFACT was unreachable by c | sim | — | +0/−71 | — (nada fora de develop) | `docs/future_work.md:2521`, `research/labels/diagnostics/frontD/REPORT.md:8` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/incipient-refusal-stage1` | `edb1a99` 2026-09-23 — research(refusal): fechamento — varredura completa de tau, sem estágio | sim | — | +0/−68 | — (nada fora de develop) | `docs/future_work.md:2664`, `research/labels/diagnostics/frontRefusal/REPORT.md:5` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item19-mature-prominence` | `f376a03` 2026-09-17 — diag(item20): closeout corrections — 20205386 blind spot, env-dependen | sim | — | +0/−96 | — (nada fora de develop) | `docs/future_work.md:1733`, `research/labels/diagnostics/item19/REPORT.md:18` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item20a-maf-090` | `eea6470` 2026-09-17 — docs(20a): register the front — future_work 20(a) + reference config d | sim | — | +0/−92 | — (nada fora de develop) | `research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md:114` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item20b-depth-rule` | `e686972` 2026-09-21 — docs(item20b): register front 22 — stage 1 FAIL (premise), stage 2 PAS | sim | — | +0/−80 | — (nada fora de develop) | `docs/future_work.md:2142`, `research/labels/diagnostics/item20b/REPORT.md:21`, `research/labels/diagnostics/item20b/REPORT.md:469` +2 | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item20c-duration-ratio` | `e7792d3` 2026-09-21 — docs(item20c): close the record — verdict completed, 20(e)(i) retired, | **não** | não (+3) | +3/−79 | 7 arq.: docs/future_work.md, research/labels/README.md, research/labels/diagnostics | `docs/future_work.md:2336` | — | **tag de arquivo (após Passo 2)** | decisão 5: o texto do item 23 de future_work só existe aqui; entra no documento único (Passo 2), depois tag |
| `research/item30-plateau-overwrite` | `2319609` 2026-09-27 — docs(item30): params-15 adotado como referência de calibração — "adota | sim | — | +0/−22 | — (nada fora de develop) | `docs/future_work.md:3615`, `docs/future_work.md:3755`, `docs/future_work.md:3766` +2 | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item31-params15-default` | `e31b727` 2026-09-28 — research(item31): etapa 2c — suíte 1438 passed / 0 failed (previsto 14 | sim | — | +0/−2 | — (nada fora de develop) | `docs/future_work.md:3825`, `research/labels/diagnostics/item31/DESIGN.md:5` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item31-stage2b-checkpoint` | `45f0600` 2026-09-28 — docs(item31): etapa 2b — CHECKPOINT pendente de aprovação do Danilo: s | sim | — | +0/−6 | — (nada fora de develop) | `research/labels/diagnostics/item31/DESIGN.md:758`, `research/labels/diagnostics/item31/gate_2b.py:3` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/item5-benchmark-tab` | `4c64ceb` 2026-09-18 — docs(item5): register front 21 — findings, open defect, remaining debt | sim | — | +0/−84 | — (nada fora de develop) | `docs/future_work.md:2006` | — | **apagar** | ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop |
| `research/v3-topology-proxy` | `c508730` 2026-09-16 — research(v3): constant baselines; retract the skeleton claim; mark pos | **não** | não (+4) | +4/−106 | 9 arq.: docs/future_work.md, research/v3_topology_proxy/PROTOCOL.md, research/v3_topology_proxy/RESULTS.md, research/v3_topology_proxy/baselines.py | `docs/future_work.md:1567`, `docs/future_work.md:1644`, `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:174` +3 | — | **tag de arquivo (após Passo 2)** | decisão 5: o texto do item 18 de future_work só existe aqui; entra no documento único (Passo 2), depois tag |

| destino | branches |
|---|---|
| apagar | 30 |
| manter | 3 |
| tag de arquivo | 6 |
| tag de arquivo (após Passo 2) | 2 |

**Contagem corrigida (Passo 1).** "apagar" = 30: **30 ancestrais** (`--is-ancestor`) e **0 só patch-equivalentes**. Branches patch-equivalentes não ancestrais no total: 1 (`diag/front-b-distance-inert`), todas com destino "tag de arquivo". O Passo 0 somava `diag/front-b-distance-inert` às 30 ancestrais como "apagar" (31); seu hash é citado nos registros, então ela não pode sumir sem ref.

Branches locais sem remota (fora do escopo, só registradas): `exp/pre-peak-normalization`, `fix/b-distance-length-scale`, `fix/core-bugs`, `input-data`. `exp/pre-peak-normalization` (`1faf0c8`) NÃO está em develop, nunca foi publicada e se declara "descartável, não mesclar"; está registrada em `docs/future_work.md` e `research/labels/swell_item30/README.md`.

## 0.4 Rastreabilidade (esqueleto): destino "remover" com achado

Para cada entrada que sai e contém achado: onde o achado já está registrado hoje. **SÓ AQUI** alimenta o documento consolidado do Passo 2 (o arquivo só sai depois). Registros em relatórios de frente contam porque esses relatórios são **consolidados**, não removidos.

| arquivo | achado | registrado em |
|---|---|---|
| `docs/_images/item5/*.png` | evidência visual (barra lateral/benchmark antes-depois) | `docs/future_work.md:2004` |
| `research/incipient_plateau/gen_geometric_vs_plateau.py` | gerador do checkpoint visual geometric×plateau (produz geometric_vs_plateau.csv); nenhum relatório o cita | **SÓ AQUI** |
| `research/incipient_plateau/geometric_vs_plateau.csv` | fronteira incipient por caso, reais e sintéticos: geometric vs plateau vs verdade de projeto | **SÓ AQUI** |
| `research/incipient_plateau/incipient_measurements.csv` | medições incipient por trajetória (caracterização) | `research/incipient_plateau/REPORT_incipient_characterisation.md:57` |
| `research/incipient_plateau/incipient_smoothing_real_rel0.csv` | rel(t0) nas trajetórias reais por janela de suavização | `research/incipient_plateau/REPORT_incipient_smoothing.md:118` |
| `research/incipient_plateau/incipient_smoothing_sweep.csv` | varredura de janela/critério da sonda incipient | `research/incipient_plateau/REPORT_incipient_smoothing.md:96` |
| `research/incipient_plateau/incipient_smoothing_tables.txt` | tabelas da varredura de suavização | `research/incipient_plateau/REPORT_incipient_smoothing.md:157` |
| `research/incipient_plateau/summary_tables.txt` | tabelas-resumo da caracterização | `research/incipient_plateau/REPORT_incipient_characterisation.md:302` |
| `research/inert_params/inertia_matrix.csv` | matriz de inércia parâmetro × config | `research/inert_params/REPORT_inertia_sweep.md:36` |
| `research/inert_params/inertia_matrix_full.csv` | matriz de inércia completa (com derivados) | `docs/future_work.md:756` |
| `research/inert_params/sweep_derived_summary.txt` | resumo da varredura derivada | `research/inert_params/REPORT_inertia_sweep.md:87` |
| `research/inert_params/sweep_summary.txt` | resumo da varredura de inércia | `research/inert_params/REPORT_inertia_sweep.md:26` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log` | log da figura de 20190639 (blocos C2 vs rótulo) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_blocks.csv` | blocos de 20190639: rótulo, base, C2 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_boundaries.csv` | erro por fronteira de 20190639: base vs C2 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_c2.png` | figura de 20190639 sob C2 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.json` | impressão digital do tree com a flag desligada | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log` | log da impressão digital (flag off) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.json` | impressão digital do tree com a flag ligada | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log` | log da impressão digital (flag on) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.json` | impressão digital de referência (c714451) para o gate da etapa 2 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429`, `docs/future_work.md:3108` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.log` | log da impressão digital de referência | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log` | M1/M2: como a proeminência do idx0 é computada e onde C2 dispararia | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:114`, `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:156` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2_c2_table.csv` | tabela por série de onde C2 dispara | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:156` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.csv` | o ramo peak->valley de C2 onde dispara (20190639) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:261` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log` | log do adendo M2 (ramo peak->valley) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:261` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.csv` | M3: forçar idx0 a peak sob params-13 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log` | log de M3 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.png` | figura de M3 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.csv` | M4: a sobrescrita incipient (defeito H) mascara o efeito em 20180608 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log` | log de M4 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.png` | figura de M4 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_head.csv` | cabeça da série 20180608 antes/depois de H (M4) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.csv` | M5: a fronteira incipient não depende do mapa de fases | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:314`, `docs/future_work.md:3048` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log` | log de M5 | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:314` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_changed_series.png` | figura das séries alteradas pela regra C2' | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.csv` | sob os defaults do pacote a nova regra não muda nada | `docs/future_work.md:3131` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log` | log da checagem sob defaults do pacote | `docs/future_work.md:3131` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log` | gate da etapa 2 (Q1–Q8) — PASS | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429`, `docs/future_work.md:3083` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_table.csv` | tabela por série da etapa 2 (dispara, ramo, sequências off/on) | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:467` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_final_output_check.log` | log (proveniência + corpo) da regeneração do final_output_check no passo 1a | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_idx0_inventory.log` | log da regeneração do inventário idx0 no passo 1a | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_capture_pipeline_state.log` | log da captura do estado do pipeline no passo 1a | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_eval_raw.log` | saída do avaliador no passo 1a (reprodução de A) | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_gate.log` | gate 1a: reprodução campo a campo dos artefatos de A — PASS | `research/labels/diagnostics/frontA_reverify/REPORT.md:135`, `docs/future_work.md:2799` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log` | censo do passo 1b na ponta com params-9 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179`, `docs/future_work.md:2817` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_diff_vs_A.log` | diff por trajetória contra A no passo 1b: nenhuma diferença | `research/labels/diagnostics/frontA_reverify/REPORT.md:195`, `docs/future_work.md:2817` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_eval_params9.log` | avaliador na ponta com params-9 (incipient, recusa) idêntico a A | `docs/future_work.md:2827` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_attribution.log` | atribuição chave-a-chave da perda de mature em 20191014 a mature_min_depth | `research/labels/diagnostics/frontA_reverify/REPORT.md:239`, `docs/future_work.md:2837` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log` | censo do passo 2 com params-13 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213`, `docs/future_work.md:2817` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_diff_vs_A.log` | diff contra A no passo 2 (params-13): nenhuma diferença | `research/labels/diagnostics/frontA_reverify/REPORT.md:220` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_final_output_check.csv` | tabela regenerada final_output_check (passo 1a) | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_fix_eval_before.txt` | avaliação regenerada 'antes do fix' de A (passo 1a) | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0_final_stage.csv` | tabela regenerada idx0_final_stage (passo 1a) | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0_inventory.csv` | tabela regenerada idx0_inventory (passo 1a) | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0b_prominence.csv` | tabela regenerada idx0b_prominence (passo 1a) | `research/labels/diagnostics/frontA_reverify/REPORT.md:135` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_V_table.csv` | tabela V (primeira fase não-incipient) sob params-9 | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0_final_stage.csv` | idx0_final_stage sob params-9 (passo 1b) | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0_inventory.csv` | idx0_inventory sob params-9 (passo 1b) | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0b_prominence.csv` | idx0b_prominence sob params-9 (passo 1b) | `research/labels/diagnostics/frontA_reverify/REPORT.md:179` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_attribution.csv` | tabela da atribuição chave-a-chave (passo 2) | `research/labels/diagnostics/frontA_reverify/REPORT.md:239` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_V_table.csv` | tabela V sob params-13 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0_final_stage.csv` | idx0_final_stage sob params-13 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0_inventory.csv` | idx0_inventory sob params-13 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0b_prominence.csv` | idx0b_prominence sob params-13 | `research/labels/diagnostics/frontA_reverify/REPORT.md:213` |
| `research/labels/diagnostics/frontC/d2_segments.csv` | segmentos de intensificação e sua profundidade D2 (separação no treino) | `research/labels/diagnostics/frontC/REPORT.md:41`, `docs/future_work.md:2366` |
| `research/labels/diagnostics/frontC/d2_segments.json` | mesmos segmentos D2, formato bruto | `docs/future_work.md:2366` |
| `research/labels/diagnostics/frontC/fig_20180654_before_after.png` | antes/depois do piso de intensificação em 20180654 | `research/labels/diagnostics/frontC/REPORT.md:41` |
| `research/labels/diagnostics/frontC/fig_20180733_before_after.png` | antes/depois do piso de intensificação em 20180733 | `research/labels/diagnostics/frontC/REPORT.md:41` |
| `research/labels/diagnostics/frontC/measurements.json` | medições brutas de treino params-12 → params-13 | `research/labels/diagnostics/frontC/REPORT.md:41`, `docs/future_work.md:2334` |
| `research/labels/diagnostics/frontD/anchoring.json` | teste de ancoragem artefato vs fase real (C1) | `research/labels/diagnostics/frontD/REPORT.md:158` |
| `research/labels/diagnostics/frontD/anchoring.txt` | teste de ancoragem artefato vs fase real (C1) | `research/labels/diagnostics/frontD/REPORT.md:158` |
| `research/labels/diagnostics/frontD/census.json` | censo incipient do treino sob params-13 | `research/labels/diagnostics/frontD/REPORT.md:61` |
| `research/labels/diagnostics/frontD/census.txt` | censo incipient do treino sob params-13 | `research/labels/diagnostics/frontD/REPORT.md:61` |
| `research/labels/diagnostics/frontD/constant_baseline.json` | baseline constante para o fim do incipient | `research/labels/diagnostics/frontD/REPORT.md:308` |
| `research/labels/diagnostics/frontD/constant_baseline.txt` | baseline constante para o fim do incipient | `research/labels/diagnostics/frontD/REPORT.md:308` |
| `research/labels/diagnostics/frontD/evaluate_params13_train.txt` | saída do avaliador (treino, params-13) | `research/labels/diagnostics/frontD/REPORT.md:243` |
| `research/labels/diagnostics/frontD/fig_*_opening.png` | figuras da abertura das séries C1 (bruta e filtrada) | `research/labels/diagnostics/frontD/REPORT.md:361` |
| `research/labels/diagnostics/frontD/verify_hashes.txt` | verificação dos hashes antes de medir — PASS | `research/labels/diagnostics/frontD/REPORT.md:29` |
| `research/labels/diagnostics/frontRefusal/classification.json` | classificação das recusas por causa (M1>M2>M3) | `research/labels/diagnostics/frontRefusal/REPORT.md:170` |
| `research/labels/diagnostics/frontRefusal/classification.txt` | classificação por causa; contagem do defeito I no conjunto | `research/labels/diagnostics/frontRefusal/REPORT.md:170`, `docs/future_work.md:672` |
| `research/labels/diagnostics/frontRefusal/evaluate_params13_train.txt` | saída do avaliador (treino, params-13) | `research/labels/diagnostics/frontRefusal/REPORT.md:46` |
| `research/labels/diagnostics/frontRefusal/fig_*_refusal.png` | figuras das séries recusadas | `research/labels/diagnostics/frontRefusal/REPORT.md:155` |
| `research/labels/diagnostics/frontRefusal/refusal.json` | caminhos de recusa por série | `research/labels/diagnostics/frontRefusal/REPORT.md:67` |
| `research/labels/diagnostics/frontRefusal/refusal.txt` | caminhos de recusa e as seis séries | `research/labels/diagnostics/frontRefusal/REPORT.md:102` |
| `research/labels/diagnostics/frontRefusal/separability.json` | separabilidade da recusa por tau | `research/labels/diagnostics/frontRefusal/REPORT.md:201` |
| `research/labels/diagnostics/frontRefusal/separability.txt` | separabilidade da recusa por tau | `research/labels/diagnostics/frontRefusal/REPORT.md:201` |
| `research/labels/diagnostics/frontRefusal/tau_sweep.json` | varredura completa de tau: nenhum tau leva o bastante à tolerância | `research/labels/diagnostics/frontRefusal/REPORT.md:334` |
| `research/labels/diagnostics/frontRefusal/tau_sweep.txt` | varredura completa de tau | `research/labels/diagnostics/frontRefusal/REPORT.md:334` |
| `research/labels/diagnostics/front_b/distance_sweep.txt` | varredura de `distance` nas séries de treino: parâmetro inerte na referência | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33`, `docs/future_work.md:1564` |
| `research/labels/diagnostics/front_b/headroom_and_hash.txt` | folga de `distance` e primeiro registro do digest default | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:267` |
| `research/labels/diagnostics/front_b/mature_pairing_audit.txt` | o que o n do pareamento mature conta e o que foi excluído | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:86` |
| `research/labels/diagnostics/front_b/reference_score_attribution.txt` | proveniência de cada número de referência (armadilha de atribuição) | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:149` |
| `research/labels/diagnostics/front_b/sensitivity.txt` | sonda causal: sensibilidade das fases a `distance`/`length_scale` | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:223` |
| `research/labels/diagnostics/front_b/sweep_distance.py` | docstring registra a menor folga sobrevivente e em que série | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:68` |
| `research/labels/diagnostics/front_b/target_tracks.txt` | as duas trajetórias-alvo: janelas mature e extremos antes/depois do filtro | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:100` |
| `research/labels/diagnostics/front_b/topology_run_gate_excerpt.txt` | trecho do gate de topologia citado como referência (score de pacote) | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:149` |
| `research/labels/diagnostics/front_b/train_aggregate.txt` | agregado do split de treino sob a config de referência da época | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:193` |
| `research/labels/diagnostics/front_b/train_raw.json` | dados brutos por série do diagnóstico de treino | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:193` |
| `research/labels/diagnostics/item19/closeout_measurements.txt` | as três medições de fechamento pedidas na revisão | `research/labels/diagnostics/item19/REPORT.md:405` |
| `research/labels/diagnostics/item19/evaluate_params10_train.txt` | saída do avaliador (treino, params-10) | `research/labels/diagnostics/item19/REPORT.md:45` |
| `research/labels/diagnostics/item19/fig_20160735_params10.png` | figura de 20160735 sob params-10 | `research/labels/diagnostics/item19/REPORT.md:41` |
| `research/labels/diagnostics/item19/fig_prominence_distributions.png` | distribuições de proeminência relativa | `research/labels/diagnostics/item19/REPORT.md:92` |
| `research/labels/diagnostics/item19/fig_tradeoff_pr060_maf090.png` | o trade-off desenhado | `research/labels/diagnostics/item19/REPORT.md:207` |
| `research/labels/diagnostics/item19/stage1_baseline.txt` | baseline constante do estágio 1 | `research/labels/diagnostics/item19/REPORT.md:76` |
| `research/labels/diagnostics/item19/stage2_cells.json` | grade de 45 células, bruto | `research/labels/diagnostics/item19/REPORT.md:143`, `docs/future_work.md:1731` |
| `research/labels/diagnostics/item20a/evaluate_params10_train.txt` | avaliador params-10 (antes) | `research/labels/diagnostics/item20a/REPORT.md:38` |
| `research/labels/diagnostics/item20a/evaluate_params11_train.txt` | avaliador params-11 (depois) | `research/labels/diagnostics/item20a/REPORT.md:52` |
| `research/labels/diagnostics/item20a/measurements.json` | medições brutas params-10 vs params-11 | `research/labels/diagnostics/item20a/REPORT.md:107` |
| `research/labels/diagnostics/item20b/analyse_20b.txt` | números do relatório do estágio 1 (profundidade dos vales) | `research/labels/diagnostics/item20b/REPORT.md:145`, `docs/future_work.md:2146` |
| `research/labels/diagnostics/item20b/defectH_watch.txt` | vigia do defeito H durante o piso de mature | `research/labels/diagnostics/item20b/REPORT_stage2.md:227` |
| `research/labels/diagnostics/item20b/denominator_robustness.txt` | robustez do denominador de D1 | `research/labels/diagnostics/item20b/REPORT_stage2.md:250` |
| `research/labels/diagnostics/item20b/depth_table.csv` | tabela dos vales geradores e suas profundidades | `research/labels/diagnostics/item20b/REPORT.md:145` |
| `research/labels/diagnostics/item20b/fig_20160735_before_after.png` | antes/depois de mature_min_depth em 20160735 | `research/labels/diagnostics/item20b/REPORT_stage2.md:114` |
| `research/labels/diagnostics/item20b/fig_20205386_before_after.png` | antes/depois de mature_min_depth em 20205386 | `research/labels/diagnostics/item20b/REPORT_stage2.md:112` |
| `research/labels/diagnostics/item20b/gate_stage2.txt` | gate (a)–(f) do estágio 2 — PASS | `research/labels/diagnostics/item20b/REPORT_stage2.md:191`, `docs/future_work.md:2191` |
| `research/labels/diagnostics/item20b/measurements.json` | dump por série do estágio 1 | `research/labels/diagnostics/item20b/REPORT.md:49` |
| `research/labels/diagnostics/item20b/stage2_measurements.json` | dump do gate do estágio 2 | `research/labels/diagnostics/item20b/REPORT_stage2.md:191` |
| `research/labels/diagnostics/item20b/supplement_20b.txt` | conteúdo DC da série que alimenta mature; recontagem | `research/labels/diagnostics/item20b/REPORT.md:96` |
| `research/labels/diagnostics/item30/census_train_params14.csv` | censo de treino sob params-14 | `research/labels/diagnostics/item30/REPORT.md:184` |
| `research/labels/diagnostics/item30/evaluate_params14_train_batch.txt` | avaliador params-14 com lote | `research/labels/diagnostics/item30/REPORT.md:118` |
| `research/labels/diagnostics/item30/figs_cf/*.png` | figuras rótulo × params-13 × params-14 × contrafactual (treino) | `research/labels/diagnostics/item30/REPORT_figs_cf.md:3`, `docs/future_work.md:3504` |
| `research/labels/diagnostics/item30/figs_cf_output.txt` | tabela rótulo × params-14 × contrafactual para os 8 casos | `research/labels/diagnostics/item30/REPORT_figs_cf.md:1` |
| `research/labels/diagnostics/item30/figs_part3/*.png` | antes/depois dos 5 adjudicados | `research/labels/diagnostics/item30/REPORT_part3.md:123` |
| `research/labels/diagnostics/item30/outside_signal.py` | docstring registra quantas trajetórias swell a regra muda | `research/labels/diagnostics/item30/REPORT_part3.md:45` |
| `research/labels/diagnostics/item30/outside_signal_output.txt` | as 5 fora do sinal e a variante estreita (medida, não adotada) | `research/labels/diagnostics/item30/REPORT_part3.md:130` |
| `research/labels/diagnostics/item30/part3_eval_params14.txt` | avaliador params-14 (parte 3) | `research/labels/diagnostics/item30/REPORT_part3.md:57` |
| `research/labels/diagnostics/item30/part3_eval_params15.txt` | avaliador params-15 (parte 3) | `research/labels/diagnostics/item30/REPORT_part3.md:57` |
| `research/labels/diagnostics/item30/part3_measure_output.txt` | medição da parte 3 (predições R1..) | `research/labels/diagnostics/item30/REPORT_part3.md:29` |
| `research/labels/diagnostics/item30/post_merge_checks_output.txt` | checagens pós-merge: avaliador e 51 séries idênticos | `docs/future_work.md:3619` |
| `research/labels/diagnostics/item30/prove_defaults_30c.txt` | 30c não muda caminhos default | `docs/future_work.md:3800` |
| `research/labels/diagnostics/item30/prove_defaults_part3_checkpoint.txt` | parte 3 não muda caminhos default (checkpoint) | `research/labels/diagnostics/item30/REPORT_part3.md:191` |
| `research/labels/diagnostics/item30/prove_defaults_part3_step2.txt` | parte 3 não muda caminhos default (passo 2) | `research/labels/diagnostics/item30/REPORT_part3.md:125` |
| `research/labels/diagnostics/item30/prove_defaults_part3_step3.txt` | parte 3 não muda caminhos default (passo 3) | `research/labels/diagnostics/item30/REPORT_part3.md:42` |
| `research/labels/diagnostics/item30/separability_criterion.json` | critério de separabilidade declarado | `research/labels/diagnostics/item30/REPORT_part2.md:15` |
| `research/labels/diagnostics/item30/separability_train_output.txt` | separabilidade no treino: sem separação | `research/labels/diagnostics/item30/REPORT_part2.md:77` |
| `research/labels/diagnostics/item30/separability_train_params14.csv` | tabela de separabilidade por série (params-14) | `research/labels/diagnostics/item30/REPORT_part2.md:77` |
| `research/labels/diagnostics/item31/benchmark_swap_mutation.txt` | mutação: colunas trocadas no teste do benchmark são detectadas | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/benchmark_swap_mutation_2c.txt` | mutação repetida na etapa 2c | `research/labels/diagnostics/item31/DESIGN.md:923` |
| `research/labels/diagnostics/item31/constant_train.json` | baseline constante no treino (params-15, defaults, constante) | `research/labels/diagnostics/item31/DESIGN.md:170` |
| `research/labels/diagnostics/item31/constant_train.txt` | baseline constante no treino | `research/labels/diagnostics/item31/DESIGN.md:170` |
| `research/labels/diagnostics/item31/exposure_table.json` | dados do registro de exposição do TESTE | `research/labels/diagnostics/item31/DESIGN.md:88` |
| `research/labels/diagnostics/item31/fix_use_filter_false_after.json` | registro depois do fix use_filter=False | `CHANGELOG.md:107` |
| `research/labels/diagnostics/item31/fix_use_filter_false_before.json` | registro antes do fix use_filter=False (crash) | `research/labels/diagnostics/item31/DESIGN.md:865` |
| `research/labels/diagnostics/item31/fix_use_filter_false_equivalence.py` | docstring descreve o defeito encontrado | `CHANGELOG.md:107` |
| `research/labels/diagnostics/item31/fix_use_filter_false_equivalence.txt` | o que rodava antes do fix roda igual; o que quebrava agora roda | `CHANGELOG.md:118` |
| `research/labels/diagnostics/item31/footprint_train.json` | pegada do default novo no treino | `research/labels/diagnostics/item31/DESIGN.md:442` |
| `research/labels/diagnostics/item31/footprint_train.txt` | pegada do default novo no treino | `research/labels/diagnostics/item31/DESIGN.md:442` |
| `research/labels/diagnostics/item31/future_work_numbers.json` | números do registro do item 31, regenerados | `docs/future_work.md:3823` |
| `research/labels/diagnostics/item31/gate_2a.txt` | gate 2a (remoção de params-1..14) — PASS | `research/labels/diagnostics/item31/DESIGN.md:595` |
| `research/labels/diagnostics/item31/gate_2b.json` | gate 2b (defaults viram params-15) | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/gate_2b.txt` | gate 2b | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/p15_expected_digest.txt` | digest esperado após a etapa 2 (layout front_b) | `research/labels/diagnostics/item31/DESIGN.md:375` |
| `research/labels/diagnostics/item31/reachability_train.json` | alcançabilidade no treino | `research/labels/diagnostics/item31/DESIGN.md:62` |
| `research/labels/diagnostics/item31/reachability_train.txt` | alcançabilidade no treino | `research/labels/diagnostics/item31/DESIGN.md:62` |
| `research/labels/diagnostics/item31/sidebar_table_2c.json` | barra lateral derivada da assinatura (2c) | `research/labels/diagnostics/item31/DESIGN.md:923` |
| `research/labels/diagnostics/item31/stage1_output.json` | a rodada única de pontuação do estágio 1 — PASS | `docs/future_work.md:3854` |
| `research/labels/diagnostics/item31/stage1_output.txt` | a rodada única de pontuação do estágio 1 — PASS | `docs/future_work.md:3854` |
| `research/labels/diagnostics/item31/stage1_smoke_train.txt` | smoke test do pontuador no treino | `research/labels/diagnostics/item31/DESIGN.md:547` |
| `research/labels/diagnostics/item31/stale_scripts.json` | lista dos scripts que param de rodar | `research/labels/diagnostics/item31/DESIGN.md:595` |
| `research/labels/diagnostics/item31/suite_2a.txt` | suíte após 2a | `research/labels/diagnostics/item31/DESIGN.md:595` |
| `research/labels/diagnostics/item31/suite_2b_final.txt` | suíte após 2b | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/suite_2b_measure.txt` | suíte com os defaults novos antes de tocar testes (falhas esperadas) | `research/labels/diagnostics/item31/DESIGN.md:815` |
| `research/labels/diagnostics/item31/suite_2b_prefix.txt` | suíte no prefixo de 2b (uma falha, a do use_filter=False) | `research/labels/diagnostics/item31/DESIGN.md:756` |
| `research/labels/diagnostics/item31/suite_2c.txt` | suíte após 2c | `docs/future_work.md:3983` |
| `research/labels/diagnostics/item31/test_label_census.json` | censo declarado dos rótulos de TESTE (contagens) | `research/labels/diagnostics/item31/DESIGN.md:124` |

Entradas: 166; **SÓ AQUI: 2** — `research/incipient_plateau/gen_geometric_vs_plateau.py` → gerador do checkpoint visual geometric×plateau (produz geometric_vs_plateau.csv); nenhum relatório o cita; `research/incipient_plateau/geometric_vs_plateau.csv` → fronteira incipient por caso, reais e sintéticos: geometric vs plateau vs verdade de projeto.

## Decisões aprovadas pelo Danilo (2026-09-28)

Texto escrito à mão; os números que sustentam cada item estão nas seções geradas acima e em "Dados gerados das
decisões" abaixo. A proposta original do Passo 0 (as perguntas) está no commit `f17d802`.

1. **`feat/label-tab-toplevel` → tag de arquivo.** As re-rotulagens de treino NÃO são recuperadas; entram como
   pendência aberta no documento único (Passo 2), com as três diferenças regeradas por
   `passo0/relabel_diff.py` (tabela em "Dados gerados": `20150656` fronteira `residual` 91→100; `20170409`
   fronteira `decay` 74→71; `20170154` veredito boundary(incipient_end_idx 6)→ambiguous).
2. **`.pypirc` → removido do versionamento** (commit 1 do Passo 1; conteúdo não aberto). A senha já foi trocada
   pelo Danilo; o histórico não é reescrito.
3. **Rótulo "2.0.0"**: os textos são corrigidos no Passo 1 (CHANGELOG, docstrings, `docs/usage.rst`) contra a tag
   `v2.0.0` real; o renome dos arquivos para "pre-item31" fica para o Passo 4, em commit próprio.
4. **App publicado × PyPI**: fora de escopo; registrado como insumo da frente de release.
5. **`fix/inspector-min-depth-params` → tag de arquivo.** `research/item20c-duration-ratio` e
   `research/v3-topology-proxy`: o texto dos itens 23 e 18 entra no documento único (Passo 2), depois tag de arquivo.
6. **Branches de registro → tags `archive/*`.** Remoção de branch remota só com autorização explícita por branch
   (Passo 6).
7. **Tag `archive/research-diagnostics-pre-cleanup`** antes de qualquer remoção (Passo 3).
8. **Dependências vivas em `diagnostics/` ficam onde estão.**
9. **Os dois medidores de "mature correta" ficam;** o documento único diz qual governa o quê. As três cópias
   locais de `pair_by_overlap` saem com seus diagnósticos.
10. **`Pipfile` sai. `requirements.txt` da raiz**: listar quem o lê (CI, docs, Streamlit, setup); sai se ninguém,
    senão fica. Só listado agora — ver "Dados gerados".
11. **Defaults literais do app**: decidir no Passo 4.
12. **C1 muda só `process_vorticity` e `determine_periods`**; as funções do filtro já usam `"reflect"` e não
    são tocadas.
13. **Migrações de texto aprovadas** (Passo 1, commits 3 e 4).
14. **`geometric_vs_plateau.csv`**: a tabela entra no documento único antes de remover.

Correções de destino no manifesto, pedidas junto com as decisões: `diag/front-b-distance-inert` → tag de
arquivo (patch-equivalente, NÃO ancestral; hash `491a5d0` citado em `front_b/sensitivity_probe.py` e
`front_b/sweep_distance.py`); `research/incipient_plateau/measure_incipient_smoothing.py` → manter (citado por
`cyclophaser/find_stages.py`).

## Desvios do prompt, e por quê

* **Suíte completa = `-m "not browser"`.** CLAUDE.md proíbe rodar `tests/test_label_browser.py`.
* **O gerador canônico escreve fora de `research/cleanup/`** (anexa ao livro-razão do digest). O registro
  anexado foi preservado em `passo0/` e o livro-razão restaurado; `run_baseline.sh` passou a fazer isso
  sozinho *depois* da rodada medida (na rodada, foi feito à mão logo em seguida).
* **(b)**: as opções do prompt (migrar / aposentar / recuperar de 33ea489) não cobrem menção puramente
  histórica que não carrega arquivo; para essas, a proposta é **manter**.
* **(c)**: o grep pega também `params_15`, `PARAMS_15` e `params15` (nomes de testes, constantes, campos),
  porque também quebram ou confundem no renome.
* **(d)**: incluí as assinaturas de `lanczos_filter.py` (default próprio `"reflect"`, fora das pistas do
  prompt) e um suplemento com `tests/test_boundary_padding.py`. `README*` não menciona o parâmetro.
* **(e)**: o localizador é heurístico (documentado em `defaults_in_text.py`); acrescentei os defaults
  literais no código do app, que não são texto, mas são exatamente a deriva que o Passo 4 procura.
* **Tipo**: acrescentei "script de pesquisa (vivo)" (`labels_core.py`, avaliador, etc.) para não chamá-los
  de "script de diagnóstico".
* **`.pypirc` não foi lido** (arquivo de credenciais; o classificador de permissões também bloqueou).
  No Passo 1 saiu do versionamento sem ser aberto.
* **Branches**: a contagem de remotas inclui `develop-v2.1` e `master`. As branches locais sem remota foram
  só registradas (fora do escopo), com destaque para `exp/pre-peak-normalization`, que não está em develop.
* **Achado fora do que foi pedido**: o rótulo "2.0.0" do item 31 (decisão 3), e as re-rotulagens fora de
  develop (decisão 1).
* **0.4**: um grupo homogêneo (ex.: `item30/figs_cf/*.png`) conta como uma entrada.
* **Passo 1 — regeração em HEAD novo.** O inventário foi regerado sobre a árvore do commit 1 do Passo 1 (sem
  `.pypirc`), e `branches.py` depois de `git fetch origin`: a contagem de remotas inclui agora
  `origin/chore/repo-cleanup` (publicada ao fim do Passo 0), com destino "manter".
* **Passo 1 — previsões gravadas neste commit.** `passo1/PREVISOES.md` vai no commit do manifesto (e não no de
  evidências) para que o git prove que as previsões precedem toda medição do Passo 1.


## Dados gerados das decisões

### Decisão 1 — re-rotulagens de treino fora de develop (`passo0/relabel_diff.py`)

`research/labels/manual_labels.yaml` em `origin/develop-v2.1` (`06d8550`) × `origin/feat/label-tab-toplevel` (`0c63145`), só ids de TREINO (54: `train:` + `batches.*.train`; entradas de teste descartadas antes de comparar; nenhuma série lida). Rótulos de treino: develop 54, branch 47 (só em develop: 7 — o lote swell, desenhado depois da branch).

| id | campo | develop | branch |
|---|---|---|---|
| `20150656` | fronteira `residual`.start_idx | 91 | 100 |
| `20170154` | veredito | kind=boundary, incipient_end_idx=6 | kind=ambiguous |
| `20170409` | fronteira `decay`.start_idx | 74 | 71 |

Com mudança de conteúdo: **3**. Re-salvamento sem mudança de rótulo: `20180170`. Não recuperadas (decisão 1); entram como pendência aberta no documento único (Passo 2).

### Decisão 10 — quem lê o `requirements.txt` da raiz (`passo0/requirements_readers.py`; só lista)

| consumidor | lê a raiz? | onde |
|---|---|---|
| CI | não | — |
| docs build (RTD) | não | — |
| setup / packaging | não | — |
| Streamlit app | não | — |
| conda env | não | — |
| user docs | **sim** | `docs/contribute.rst:43`, `docs/installation.rst:27`, `docs/installation.rst:66` |

O CI instala do wheel mais `pytest pyyaml`; o RTD lê `docs/requirements.txt`; `setup.py` declara `install_requires` próprio; o app tem `tools/calibration_app/requirements.txt` próprio. O serviço Streamlit Cloud escolhe o arquivo por regra própria, fora da árvore: não verificável daqui. Só as instruções de instalação/contribuição dos docs de usuário mandam rodar `pip install -r requirements.txt` na raiz — ou seja, **alguém o lê** (por instrução); pela decisão 10 ele fica. O `Pipfile` sai.


## Resumo para orquestração (gerado)

* Branch `chore/repo-cleanup`; base em develop-v2.1 `06d8550` (esperada `06d8550`); inventário em HEAD `c080f4d`. Hash do commit deste passo: ver a mensagem de entrega (um arquivo não contém o próprio hash).
* Linha de base: suíte previsto 1438/0 → obtido 1438/0; digest previsto `3a6de265…` → obtido `3a6de265…`.
* Arquivos versionados: 536 — manter 222, consolidar 40, remover 274. Scripts de stale_scripts.md confirmados: 40/40.
* Branches remotas: 41 — apagar 30, manter 3, tag de arquivo 6, tag de arquivo (após Passo 2) 2; das "apagar", 30 ancestrais e 0 só patch-equivalentes.
* SÓ AQUI: `research/incipient_plateau/gen_geometric_vs_plateau.py` → gerador do checkpoint visual geometric×plateau (produz geometric_vs_plateau.csv); nenhum relatório o cita; `research/incipient_plateau/geometric_vs_plateau.csv` → fronteira incipient por caso, reais e sintéticos: geometric vs plateau vs verdade de projeto.
* params-1..14 fora dos diagnósticos e de future_work.md: 103 ocorrências em 22 arquivos; propostas **migrar** em `CHANGELOG.md`, `tests/test_intensification_min_depth.py`, `tools/calibration_app/benchmark_core.py`, `tools/calibration_app/layer_inspector.py`.
* params-15: 317 ocorrências — vivas 66, históricas 251.
* boundary_padding: 126 ocorrências no escopo; assinaturas com default: `process_vorticity`='edge', `determine_periods`='edge', `lanczos_filter`='reflect', `lanczos_bandpass_filter`='reflect'; `get_periods` tem default próprio: não.
* Caminhos absolutos: 139 ocorrências em 41 arquivos; fora de `research/` e `docs/future_work.md`: 0.
* Decisões e desvios: seções acima.
