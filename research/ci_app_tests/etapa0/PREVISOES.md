# Etapa 0 — previsões (commitadas e com push ANTES de qualquer medição)

Frente: testes do app de calibração no CI (CircleCI). Branch `ci/app-tests`,
criada de `develop` = `origin/develop` = `3f410df` (conferido com `git rev-parse`
antes de criar a branch). Data: 2026-10-13.

Nenhuma rodada de pytest, `--collect-only`, build de wheel ou consulta a
resultado de CI desta branch foi feita antes deste commit. O que foi lido antes:
código-fonte (`.circleci/config.yml`, `setup.py`, `tests/conftest.py`, os
`requirements*.txt` do app, `grep` de `importorskip`/`sys.path`/marcadores) e
registros (`docs/future_work.md` itens 34–35, `CLAUDE.md`). Também foi lido,
antes deste commit, o build 514 do CircleCI (develop, `3f410df`, build_test,
155 s) ao testar se a API pública responde sem token — anotado aqui para não
ser apresentado depois como medição desta etapa.

Todas as previsões de suíte são **passed / failed** apenas (regra do
`CLAUDE.md`); pulos e desselecionados são registrados, nunca previstos.

## De onde vêm os números previstos

* `git diff --stat 8eb04c8 3f410df -- tests tools cyclophaser setup.py .circleci`
  é vazio: nada de código, teste ou CI mudou desde as contagens do item 35.
* Item 35 (registro): "CI 1280 / 0 + 1 / 0"; suíte conda `-m "not browser"`
  1508 / 0; 15 testes Chromium nos testes das páginas novas.
* `CLAUDE.md` (registro): `tests/test_label_browser.py` tem 29 testes.
* Logo: testes que só passam com as dependências do app = 1508 − 1280 − 1
  (o `source_tree`) = **227**; total browser coletado = 15 + 29 = **44**.

## Commit medido

Todas as medições locais rodam no commit deste arquivo (chamado **C0** no
relatório), num clone limpo fora do repositório, como o `checkout` do CI. O
wheel é construído de `git archive C0` num diretório temporário, nunca de `dist/`.

## Conferência dos filtros do workflow (antes do primeiro push)

Lido em `.circleci/config.yml` @ `3f410df`, workflow `build_test_publish`:
`build_test` sem filtro de branch; `test_pypi_publish` requer `build_test`,
só `develop`; `pypi_publish` requer `build_test`, só `master`.
`store_test_results` sem `when: always`. **Um push em `ci/app-tests` roda só
`build_test`; nenhuma publicação.**

## Previsões

| id | o quê | previsão |
|---|---|---|
| P1 | 0.1 conteúdo do wheel | só `cyclophaser/` e `cyclophaser-2.1.2.dist-info/`; **sem** `tools/`, `research/`, `tests/` |
| P2 | 0.2 pipeline do push de `ci/app-tests` | um único job, `build_test`, `success`; nenhum job de publicação criado |
| P2a | 0.2 passo "Run tests against the installed wheel" | **1280 passed / 0 failed** |
| P2b | 0.2 passo "Run source-tree tests against the checkout" | **1 passed / 0 failed** |
| P3 | 0.3 receita do CI local (venv enxuto: wheel + pytest + pyyaml), `-m "not source_tree"` com a trava | **1280 passed / 0 failed**; passo source_tree **1 / 0** |
| P4 | 0.3 suíte conda (`cyclophaser` env, `which python` conferido), `-m "not browser"` | **1508 passed / 0 failed** |
| P5 | 0.3 inventário | testes não-browser que passam no venv do app e não passam no enxuto: **227**; browser coletados no conda: **44** (29 Label + 15 demais) |
| P6 | 0.4 venv novo + wheel + streamlit/plotly/pyyaml/pytest (mais novos), `-m "not browser and not source_tree"`, trava ligada | **1507 passed / 0 failed**; trava passa (código de saída 0, nenhuma linha `CYCLOPHASER_REQUIRE_INSTALLED: FAIL`, sonda: todo módulo `cyclophaser*` dentro do `sys.prefix` do venv); módulos do app carregados de `<clone>/tools/calibration_app/` |
| P7 | 0.5 (i) `streamlit==1.56.0`, resto mais novo | **1507 / 0** |
| P8 | 0.5 (i′) todos os pisos do `requirements.txt` (streamlit 1.56.0, pandas 2.2.0, matplotlib 3.9.0, plotly 5.24.0, xarray 2024.9.0, numpy 2.1.0, scipy 1.14.0, cmocean 4.0, pyyaml 6.0) | **o pip recusa** (conflito de resolução: pandas 2.2.0 declara `numpy<2`, o piso numpy é 2.1) → nenhuma rodada; os pisos declarados são **conjuntamente insatisfazíveis** |
| P8b | 0.5 (i′b, variante extra declarada aqui) pisos com `pandas==2.2.2` (primeiro pandas compatível com numpy 2) | **1507 / 0** |
| P9 | 0.5 (ii) mais nova sem fixar | **1507 / 0**; pandas resolvido é **3.x** |
| P10 | 0.5 (iii) pins de `requirements-app.txt` (wheel em vez de `-e ../..`) | **1507 / 0** |
| P11 | 0.6 estabilidade: N = 29 rodadas por versão, piso (`floor_st`) e mais nova (`newest`), cada série num venv novo, rodadas sequenciais | **0 rodadas com falha** nas 58; cada rodada **1507 / 0** |

### N da estabilidade (0.6)

N = **29 por versão**. Probabilidade de ver ao menos uma falha de um defeito
intermitente que falha com probabilidade p por rodada: 1 − (1 − p)^N
(calculado por script, `python3 -c`):

| p por rodada | detecção com N = 29 |
|---|---|
| 10 % | 0,953 |
| 5 % | 0,774 |
| 2 % | 0,443 |

O menor p detectável com 95 % é **9,81 %** (1 − 0,05^(1/29)). Intermitências
abaixo de ~10 % por rodada podem passar despercebidas; isso fica dito no
relatório, não é corrigido aumentando N depois de ver o resultado. N não muda
em função da duração medida.

## Critérios de leitura (fixados agora)

* Uma rodada é **PASS** se `failed == 0` e `error == 0` no junit e o código de
  saída é 0. Qualquer `error` conta como falha.
* A **trava passa** se: código de saída 0, nenhuma linha
  `CYCLOPHASER_REQUIRE_INSTALLED: FAIL` no log, e `all_cyclophaser_in_venv`
  verdadeiro na sonda (`scripts/ci_probe.py`).
* Uma previsão de contagem **confere** só se passed e failed forem exatamente
  iguais aos previstos. Qualquer diferença é desvio, registrado com a causa
  diagnosticada, sem mudar o número previsto.
* Teste que falhar ou oscilar é **registrado e levado ao Danilo**; nenhum teste
  é corrigido nesta etapa.
* Se o pipeline do push aparecer sem workflow, é "ainda não rodou", não falha;
  reconsultar ao longo de horas antes de concluir.

## Scripts (escritos antes de qualquer medição)

`scripts/common.sh`, `build_wheel.sh`, `make_venv.sh`, `ci_probe.py`,
`run_suite.sh`, `summarize_junit.py`, `stability.sh`, `ci_baseline.py`.
Venvs, wheel e clone ficam fora do repositório (`$CIAPP_WORK`).
