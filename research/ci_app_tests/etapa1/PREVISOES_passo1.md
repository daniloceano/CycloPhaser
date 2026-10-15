# Etapa 1, passo 1 — previsões (commitadas e com push ANTES do commit de implementação)

Frente: testes do app de calibração no CI (CircleCI). Branch `ci/app-tests`,
ponta antes deste commit = `9efc74f` (desenho da etapa 0, aprovado pelo Danilo
em 2026-10-14). Data: 2026-10-14.

Nada foi implementado nem medido antes deste commit. O que foi lido antes:
`research/ci_app_tests/etapa0/RELATORIO.md`, `logs/reach_check.json`,
`.circleci/config.yml`, `tests/conftest.py`, `tests/test_compare_core.py`,
`setup.py` (`install_requires` não contém streamlit, plotly nem pyyaml), o junit
`etapa0/logs/runs/floor_st.xml.gz` (para ver como o junit escreve os ids dos
pulos), e o `grep` de globs em `logs/grep_globs_before_sample_tracks.txt`.

Previsões de suíte: **passed / failed** apenas (regra do `CLAUDE.md`). A lista de
pulos do job do app é a exceção aprovada no desenho: ela é critério (c) **por id**,
num ambiente sem playwright, conferida pelo próprio job.

## O que será implementado (o desenho aprovado, sem reabrir)

1. `.circleci/config.yml`
   * job novo `app_test`, parâmetro `leg` (enum `floor` | `newest`),
     `cimg/python:3.12.3`, `resource_class: medium`; passos: checkout →
     `pip install --upgrade pip build` → `python -m build` → um único
     `pip install dist/*.whl <streamlit> plotly pyyaml pytest`, com
     `<streamlit>` = `streamlit==1.56.0` (floor) ou `streamlit` (newest) →
     `pip freeze` para `artifacts/` → `pytest --import-mode=append -m "not browser
     and not source_tree"` da raiz do checkout, com
     `CYCLOPHASER_REQUIRE_INSTALLED=1` e `CYCLOPHASER_REQUIRE_APP_DEPS=1` →
     checagem de pulos (`.circleci/check_app_skips.py`) → `store_test_results`
     (`when: always`) → `store_artifacts` (`when: always`).
   * no workflow, matriz `leg: [floor, newest]` com `name:
     app_test_<< matrix.leg >>` (nomes fixos `app_test_floor`, `app_test_newest`),
     filtro de branch `develop`, `master`, `/^ci\/.*/`.
   * `test_pypi_publish` e `pypi_publish`: `requires` = `build_test`,
     `app_test_floor`, `app_test_newest`; filtros inalterados (`develop` e
     `master`).
   * `build_test`: só ganha `when: always` no `store_test_results`.
2. `.circleci/check_app_skips.py` (só biblioteca padrão): lê o junit e exige que
   o conjunto de testcases com `<skipped>` seja **exatamente** estes 5 ids
   (`classname` + `name` do junit; módulo pulado na coleta tem `classname` vazio):
   1. `tests.test_app_pages_browser`
   2. `tests.test_compare_browser`
   3. `tests.test_label_browser`
   4. `tests.test_validate_browser`
   5. `tests.synthetic.test_synthetic_lifecycles` ::
      `test_lifecycle_phase_timing[IcIt_observational]`
3. `tests/conftest.py`: `CYCLOPHASER_REQUIRE_APP_DEPS`. Ligada, o
   `pytest_configure` importa `streamlit`, `plotly` e `yaml` e levanta
   `pytest.UsageError` listando cada um que falhou (inclusive import que levanta
   outro erro que não `ImportError`). Desligada, nada muda e nada é importado.
   Docstring atualizado.
4. `tests/sample_tracks/` (nova, versionada): `track_19800580.csv` e
   `track_19800725.csv`, copiados byte a byte de
   `tools/calibration_app/sample_tracks/` (formato TRACK; são os dois primeiros
   em ordem, os mesmos que o teste lia na árvore local). Em
   `tests/test_compare_core.py`, só a linha do `SAMPLE_DIR` muda. O `grep`
   (`logs/grep_globs_before_sample_tracks.txt`) mostra que nenhum outro teste faz
   glob que veja `tests/sample_tracks/`.

Nada mais muda em `cyclophaser/`, `setup.py`, `tests/`, `tools/` ou no app.

## Conferência dos filtros (feita agora, refeita antes do push da implementação)

Config atual (`9efc74f`): `build_test` sem filtro; `test_pypi_publish` só
`develop`; `pypi_publish` só `master`. **O push deste commit (só previsões) roda
apenas `build_test`** em `ci/app-tests`: previsto 1280 / 0 + 1 / 0, nenhuma
publicação.

## Previsões

Fonte de cada número: `etapa0/logs/reach_check.json` e a linha de base
(job 516), não a memória.

| id | o quê | previsão | fonte |
|---|---|---|---|
| Q1 (a) | `git diff --stat 3f410df <ponta> -- cyclophaser setup.py` | **vazio** | `reach_check` / desenho |
| Q2 | local, receita enxuta (venv novo, wheel do commit de implementação, `pytest pyyaml`), `-m "not source_tree"` com a trava | **1280 passed / 0 failed**; passo source_tree (`python -m pytest -m source_tree`, sem trava) **1 / 0** | `b_baseline_wheel_passed` = 1280; job 516. O teste repontado está num módulo que pula inteiro sem streamlit, e a variável nova está desligada |
| Q3 | local, conda `cyclophaser` (`which python` conferido), `-m "not browser"` | **1508 passed / 0 failed** | etapa 0 P4 mediu 1508 / 0 em C0. Nenhum teste é adicionado ou removido; o único teste tocado já **passava** no conda (a árvore local tem os CSVs, `etapa0` desvio P5) e continua passando, agora lendo `tests/sample_tracks/`; a variável nova fica desligada |
| Q4 | local, venv do app **floor** (`streamlit==1.56.0`), mesma seleção do job, `CYCLOPHASER_REQUIRE_INSTALLED=1` + `CYCLOPHASER_REQUIRE_APP_DEPS=1` | **1507 passed / 0 failed**; pulos = os 5 ids (`check_app_skips.py` sai 0); trava de proveniência passa (saída 0, nenhuma linha `…: FAIL`, `cyclophaser.__file__` no site-packages do venv) | `c_expected_app_job_passed` = 1507 = 1506 medido + o teste dos `sample_tracks` |
| Q5 | local, venv do app **newest** (streamlit sem fixar), idem | **1507 / 0**; pulos = os 5 ids; trava passa | idem |
| Q6 (h) | CircleCI, pipeline do push de implementação em `ci/app-tests` | jobs = **`build_test`, `app_test_floor`, `app_test_newest`** e **nenhum** de publicação | filtros do desenho |
| Q7 (b) | `build_test` nesse pipeline | wheel **1280 / 0**; source **1 / 0** | job 516 |
| Q8 (c)(g) | cada perna do app nesse pipeline | **1507 / 0**; passo de checagem de pulos verde; resultados no endpoint `/tests` da API (1512 testcases = 1507 + 5 pulos, todos `success` ou `skipped`) | `reach_check` |
| Q9 | duração de cada perna | registrada; **sem previsão de gate**. Estimativa da etapa 0 (não medida em `medium`): 5,1–8,8 min por perna | `cost_estimate.json`, suposição A3 |

**Regra de parada (da etapa 0, `cost_free_plan.json`):** perna com duração real
acima de **20,03 min** → parar e levar ao Danilo antes do passo 2.

**Validação do config:** o CLI `circleci` não está instalado nesta máquina
(`which circleci` vazio, conferido). Será registrado; no lugar, o YAML é lido
por `yaml.safe_load` e a estrutura (jobs, matriz, `requires`, filtros) é
conferida por script antes do push. Isso não substitui o `circleci config
validate`; o primeiro pipeline real é a validação de fato.
