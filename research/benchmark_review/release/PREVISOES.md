# Release 2.1.2 — fase 1 (preparar, não publicar): previsão (commitada e enviada antes de qualquer medição; não editar)

Data: 2026-10-09 (Brasília). Branch `release/v2.1.2`, criada de `develop` @ `33d3f08`
(merge da frente item 35). Autorização para mudar a versão 2.1.1 → 2.1.2, escrita pelo
Danilo: "autorizo". Nenhuma execução de suíte, navegador, CI, figura ou build de
documentação desta fase aconteceu antes deste commit; nenhuma mudança de versão foi
feita ainda.

Item 0 (pré-condição, já verificado pela API pública do CircleCI): pipeline 399, workflow
`build_test_publish` success; `build_test` **#503** success (1281 com sucesso, 58 pulados,
0 falhas); `test_pypi_publish` **#504** success. Detalhes e a discrepância das 21:26Z em
`RELATORIO.md`.

## Arquivos que o release muda (lista exata)

| arquivo | mudança |
|---|---|
| `setup.py` | `VERSION = '2.1.2'` |
| `docs/conf.py` | `release = '2.1.2'` |
| `CHANGELOG.md` | `## [Unreleased]` vira `## [2.1.2] - <data do commit>`, com um `## [Unreleased]` vazio acima; links: `[Unreleased]` = `v2.1.2...HEAD`, `[2.1.2]` = `v2.1.1...v2.1.2` |
| `docs/generated/app_start.png` | regenerada; mostra "CycloPhaser 2.1.2" |
| `docs/generated/app_sidebar.png`, `app_grid.png`, `app_statistics.png`, `app_save.png` | regeneradas pelo mesmo script (ele escreve as cinco). **Nenhuma das quatro mostra o número da versão** (a legenda da versão fica no topo da área principal, que só `app_start` enquadra). Se os bytes mudam não é previsto: o script declara que capturas de navegador não são reproduzíveis byte a byte |
| `research/benchmark_review/release/` | esta previsão, evidências, `RELATORIO.md` |

Nenhum outro arquivo. `git diff develop -- cyclophaser/` continua vazio. Data do
CHANGELOG: a data local (−03:00) do commit da versão; se passar da meia-noite, 2026-10-10.

## Versão instalada

Depois de `pip install -e . --no-deps` no env conda `cyclophaser`:
`importlib.metadata.version("cyclophaser") == "2.1.2"`.

## Execuções (só passed e failed)

| execução | passed | failed |
|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0, `-m "not browser"` | **1508** | **0** |
| venv streamlit 1.56.0, mesmo comando | **1508** | **0** |
| receita do CI, wheel | **1280** | **0** |
| receita do CI, source tree | **1** | **0** |
| Chromium (`test_app_pages_browser.py` + `test_compare_browser.py` + `test_validate_browser.py`), 1.63.0 | **15** | **0** |
| idem, 1.56.0 | **15** | **0** |

Nenhum teste muda nesta fase. O único teste que lê a versão
(`test_calibrate_i2_apptest.py::test_the_displayed_version_is_the_installed_package`)
compara a legenda do app com a versão instalada no mesmo interpretador, então passa com
2.1.1 ou 2.1.2. `tests/test_label_browser.py` não é rodado.

## Documentação

Build como o Read the Docs, em checkout limpo da branch: **0 warnings**, saída 0; a
página mostra a versão 2.1.2.
