# Etapa 1, fechamento — previsões do pipeline do merge em `develop` (commitadas ANTES do push do merge)

Autorização do Danilo para o merge: dada no enunciado do fechamento
(2026-10-14). Pré-checagem: `origin/ci/app-tests` = `5273750`,
`origin/develop` = `3f410df`, `git diff origin/develop origin/ci/app-tests --
cyclophaser setup.py` vazio. Este arquivo entra em `ci/app-tests` com
`[skip ci]` e o merge (`--no-ff`) o leva para `develop`.

| id | o quê | previsão |
|---|---|---|
| M1 | jobs do pipeline do commit de merge em `develop` | `build_test`, `app_test_floor`, `app_test_newest`, `test_pypi_publish`; **nenhum** `pypi_publish` |
| M2 | `build_test` | 1280 / 0 + 1 / 0 |
| M3 | `app_test_floor`, `app_test_newest` | 1507 / 0 cada, checagem de pulos `OK` |
| M4 | ordem | `test_pypi_publish` começa (`started_at`) **depois** do `stopped_at` dos três |
| M5 | `test_pypi_publish` | verde, **sem publicar nada**: a versão 2.1.2 já existe no TestPyPI, então `twine upload --skip-existing` pula o sdist e o wheel |

Regra de parada: se o `test_pypi_publish` começar antes dos três ou publicar
algo, parar e levar ao Danilo.
