# Etapa 1, passo 2 — previsões dos controles (commitadas e com push ANTES de cada push de controle)

Branch descartável **`ci/app-tests-controls`**, criada da ponta de
`ci/app-tests` que contém este arquivo. Casa com `/^ci\/.*/`: roda
`build_test` + as duas pernas, e nenhum job de publicação (conferido pelo
`validate_config.py` no passo 1, linha `ci/app-tests-controls`). As pernas e
jobs extras desta branch **nunca** entram em `ci/app-tests`.

Previsões: passed / failed por job, os ids que falham, e o motivo da parada nos
controles negativos. Base: passo 1 no CircleCI (pipeline 411, jobs 519/520/521:
1507 / 0 nas duas pernas, 1280 / 0 + 1 / 0 no `build_test`) e a descoberta local
abaixo.

## Controle positivo (e) — regressão no código do app

**Mudança declarada (commit E1):** em `tools/calibration_app/label_overlays.py`,
apagar a entrada `"vorticity_smoothed2"` do `LABEL_OVERLAY_STYLE`. Efeito no app:
a página Manual labelling deixa de oferecer a camada que a detecção de fases
realmente usa (o 2º Savitzky-Golay). É código do app, fora dos 4 módulos que o
`build_test` importa (`benchmark_core`, `layer_inspector`, `package_args`,
`track_io`); `label_overlays` só é alcançado pela página `app_pages/label.py`,
isto é, por AppTest.

**Descoberta local, feita antes desta previsão** (permitida pelo enunciado; a
previsão é sobre o CircleCI): clone de `425a72f` + a mudança, venvs floor e
newest do passo 1, mesma seleção e travas do job
(`logs/passo2/local_discovery/`): nas duas pernas, **2 failed / 1505 passed**,
ids:

1. `tests/test_label_apptest.py::test_toggling_overlay_layers_does_not_move_any_phase`
2. `tests/test_label_apptest.py::test_revealing_an_overlay_records_it_and_unblinds_the_case`

| id | push | job | previsão |
|---|---|---|---|
| R1 | E1 | `app_test_floor` | **vermelho**; **1505 passed / 2 failed**; ids que falham = exatamente os 2 acima; o passo de checagem de pulos **não roda** (passo anterior falhou, `when` padrão) |
| R2 | E1 | `app_test_newest` | idem: **1505 / 2**, os mesmos 2 ids |
| R3 | E1 | `build_test` | **verde**, 1280 / 0 + 1 / 0 |
| R4 (i) | E1 | endpoint `/tests` dos jobs vermelhos | lista os 2 ids com resultado `failure` (prova o `when: always` do `store_test_results`); 1512 testcases (1505 `success` + 2 `failure` + 5 `skipped`) |
| R5 | E2 (reverte E1) | `app_test_floor`, `app_test_newest` | **verdes, 1507 / 0** cada, checagem de pulos OK |
| R6 | E2 | `build_test` | verde, 1280 / 0 + 1 / 0 |

## Controles negativos (c) e (d) — commit CD, sobre E2

Um job extra `app_control`, parâmetro `control`, duas instâncias só nesta
branch, mesma imagem e `medium`:

* `app_control_noplotly` — instala `dist/*.whl streamlit pyyaml pytest`
  (**sem plotly**; conferido por `pip install --dry-run --report` local que nada
  o puxa: 54 pacotes, nenhum plotly) e roda a seleção do `app_test` com as duas
  variáveis.
* `app_control_python_m` — instalação do floor completa, mas roda
  **`python -m pytest`** da raiz do checkout, com as duas variáveis.

| id | job | previsão |
|---|---|---|
| R7 (c) | `app_control_noplotly` | **vermelho**; o pytest sai com `UsageError` (código 4) antes de coletar, mensagem citando `plotly` (`CYCLOPHASER_REQUIRE_APP_DEPS is set but these app dependencies do not import: plotly (ModuleNotFoundError: …)`); **0 testes** executados |
| R8 (d) | `app_control_python_m` | **vermelho**; `UsageError` da trava de proveniência: `CYCLOPHASER_REQUIRE_INSTALLED is set but cyclophaser was imported from /home/circleci/project/cyclophaser/__init__.py, not from site-packages`; 0 testes |
| R9 | `app_test_floor`, `app_test_newest`, `build_test` no mesmo pipeline | verdes: 1507 / 0, 1507 / 0, 1280 / 0 + 1 / 0 |
| R10 (h) | todos os pipelines desta branch | nenhum job de publicação |
