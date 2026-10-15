# Fechamento final — previsões do pipeline do merge da correção 3b (commitadas e com push ANTES do merge)

Autorização do Danilo: dada no enunciado do fechamento final (2026-10-14).
Pré-checagem: `origin/develop` = `06f56e8`,
`origin/ci/fix-apptest-expander-count` = `04ea018` (pipeline 420 verde).
Este arquivo entra em `develop` com `[skip ci]` antes do merge `--no-ff`, para
que o commit de merge seja a cabeça do pipeline.

| id | o quê | previsão |
|---|---|---|
| N1 | jobs do pipeline do commit de merge | `build_test`, `app_test_floor`, `app_test_newest`, `test_pypi_publish`; nenhum `pypi_publish` |
| N2 | `build_test` | 1280 / 0 + 1 / 0 |
| N3 | `app_test_floor` | 1507 / 0, checagem `OK`, streamlit 1.56.0 |
| N4 | `app_test_newest` | 1507 / 0, checagem `OK`, com o streamlit mais novo do dia (1.66.0 hoje; a versão vem do freeze) |
| N5 | ordem | o `started_at` do `test_pypi_publish` é ≥ o `stopped_at` dos três |
| N6 | `test_pypi_publish` | verde, **sem publicar**: 2.1.2 já existe no TestPyPI, então o `twine upload --skip-existing` pula o sdist e o wheel; a linha do log que mostra o pulo fica registrada |

Regra de parada: newest vermelho de novo, ou `test_pypi_publish` publicando
algo.
