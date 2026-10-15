# Etapa 1, correção antes do merge — `release/*` no filtro do `app_test` (previsões, commit + push ANTES de medir)

Branch `ci/app-tests`, ponta antes deste commit = `fb516c5` (pipeline 417 verde).
Data: 2026-10-14.

## Problema

Releases são feitas em `release/*` (ex.: `release/v2.1.2`, item 35) e vão direto
para a `master`. O filtro aprovado (`develop`, `master`, `ci/*`) não roda
`app_test` em `release/*`. Por isso a regra do `CLAUDE.md` ("green on the same
commit in develop") não pode ser cumprida numa release, e o Streamlit Cloud
reimplanta assim que o commit chega à `master`.

## Mudança (nada mais muda nos jobs)

1. `.circleci/config.yml`: `/^release\/.*/` entra no filtro de branches do
   `app_test`. O comentário do topo passa a dar o motivo do filtro para
   `develop`, `master`, `release/*` e `ci/*`.
2. `CLAUDE.md`: a linha nova do "Fixed rules" passa a ser o texto do Danilo:
   "Merge into `master` only after `app_test_floor` and `app_test_newest` are
   green on the exact commit being merged (develop or a release/* branch). …"
3. `docs/future_work.md` item 36: a correção e o motivo.

Nenhuma branch `release/*` é criada no remoto para testar.

## Instrumento

`scripts/check_filters.py` (novo; o `validate_config.py` não é editado). Ele
valida contra o schema do CircleCI (a mesma cópia de
`logs/passo1/circleci_schema_2026-10-14.json.gz`) e lista os jobs que rodam em
cada branch, lidos do YAML com as funções `expand`/`branch_runs` do
`validate_config.py`. Fatos conferidos:

* F1: `app_test_floor` e `app_test_newest` rodam em `release/v9.9.9`;
* F2: rodam em `ci/x`;
* F3: **não** rodam em `feat/x`;
* F4: `test_pypi_publish` roda só em `develop`, e `pypi_publish` só em `master`,
  entre `develop`, `master`, `release/v9.9.9`, `ci/x` e `feat/x`.

## Previsões

| id | o quê | previsão |
|---|---|---|
| K1 | `check_filters.py` no config **novo** | schema sem erro; F1–F4 verdadeiros; saída 0. Jobs por branch: `release/v9.9.9` e `ci/x` → `build_test`, `app_test_floor`, `app_test_newest`; `feat/x` → `build_test`; `develop` → os 3 + `test_pypi_publish`; `master` → os 3 + `pypi_publish` |
| K2 | controle: o mesmo script no config **atual** (`fb516c5`) | **F1 falso** (em `release/v9.9.9` só `build_test`); F2–F4 verdadeiros; saída 1 |
| K3 | controle: config novo com `/^release\/.*/` também no filtro do `test_pypi_publish` (arquivo temporário, nunca commitado) | **F4 falso**; saída 1 |
| K4 | `git diff fb516c5 <ponta> -- .circleci/config.yml`, sem as linhas de comentário | só a linha `- /^release\/.*/` acrescentada |
| K5 | pipeline da nova ponta em `ci/app-tests` | jobs = `build_test`, `app_test_floor`, `app_test_newest`, nenhum de publicação; `build_test` 1280 / 0 + 1 / 0; cada perna 1507 / 0 com a checagem de pulos OK |
| K6 (a) | `git diff --stat 3f410df <ponta> -- cyclophaser setup.py` | vazio |
