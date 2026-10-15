# Release 2.1.3 — etapa 3: relatório (2026-10-15)

DATA DO CHANGELOG: 2026-10-15. AUTORIZAÇÃO 2 (merge develop → master, tag v2.1.3,
publicação): "sim" (Danilo, retorno da PARADA 2). AUTORIZAÇÃO NOMEADA para remover
a branch remota release/v2.1.3 depois do registro final: "sim".

## Passos, na ordem, cada um conferido antes do próximo

| passo | resultado | fonte |
|---|---|---|
| 1. data do CHANGELOG | commit `0dcc57a` em develop (só o cabeçalho `## [2.1.3] - 2026-10-15`), sem [skip ci], push | git |
| 2. (d) definitivo | pipeline [428](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/428) em `0dcc57a`: build_test #627 1280/0 + 1/0; app_test_floor #625 1507/0 com **streamlit 1.56.0**; app_test_newest #626 1507/0 com **streamlit 1.66.0** (pip freeze dos artefatos); test_pypi_publish #628 success **sem upload**: `400 File already exists` → `WARNING Skipping cyclophaser-2.1.3-py3-none-any.whl …` e `… cyclophaser-2.1.3.tar.gz …` | ci/develop_0dcc57a |
| 3. merge na master | `git rev-parse origin/develop` = `0dcc57a3…` (o commit verde); merge `--no-ff` = **`b1c2df7`** "Release 2.1.3" (pais `aa7ee3a` = v2.1.2 e `0dcc57a`); árvore de b1c2df7 = árvore de 0dcc57a (`7b01f353…`); diff `cyclophaser/` vs v2.1.2: 0 bytes; push (GitHub: "Bypassed rule violations … pull request", o contorno da conta do Danilo). Tag anotada **v2.1.3** (objeto `5c5b598`) → b1c2df7, push | git |
| 4. pipeline da master | [429](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/429) em `b1c2df7`: build_test #629 1280/0 + 1/0; app_test_floor #630 1507/0; app_test_newest #631 1507/0; **pypi_publish #632 success**, `Uploading … 200 OK` nos dois arquivos | ci/master_b1c2df7 |
| 4. dependência do pypi_publish | arquivo: `.circleci/config.yml` em b1c2df7, `pypi_publish.requires` = build_test, app_test_floor, app_test_newest. Grafo: `dependencies` do job na API v2 = os três; `blocked` enquanto as pernas rodavam; começou 12:04:00Z, depois da última perna (newest, 12:03:58Z) | idem |
| 5. PyPI × TestPyPI | todos os membros iguais por conteúdo (wheel 11, sdist 18); 0 entradas em tests/ | logs/E3_pypi_vs_testpypi.log |
| 5. PyPI × master | build local de b1c2df7 (macOS arm64, build 1.6.1): todos os membros iguais por conteúdo (wheel 11, sdist 18) | logs/E3_pypi_vs_master.log |
| 5. (b) B1 do PyPI | cmocean 4.0.3, smoke OK | logs/E3_b_B1_pypi.log |
| 5. (b) B3 do PyPI | "Found existing installation: cmocean 4.0.1 … Successfully installed cmocean-4.0.3 cyclophaser-2.1.3", smoke OK | logs/E3_b_B3_pypi.log |

SHA256 dos arquivos do PyPI (conferidos contra a API no download): wheel
`88ef3c328fd9…`, sdist `02a3af0829ff…`. Os bytes diferem dos da TestPyPI (carimbos
de tempo de builds diferentes); o conteúdo de cada membro, não.

## Passo 6 — dispensado o reboot; conferências feitas pelo Claude (2026-10-15, ~10:45)

Relatadas pelo Danilo como conferidas de forma independente por uma sessão do
Claude, não por esta:
- App público: estava dormindo; ao ser acordado voltou com "CycloPhaser 2.1.3" e
  "Made with Streamlit v1.66.0", **sem reboot**. "Try example data": 3 figuras,
  0 stException, 0 alertas.
- PyPI 2.1.3: wheel (11 membros) e sdist (18 membros) idênticos por conteúdo a um
  build Linux independente de f6daa41; B3 a partir do PyPI em Linux OK (pip subiu
  cmocean 4.0.1 → 4.0.3).
- Read the Docs latest e stable: "CycloPhaser 2.1.3 documentation".
- Pipeline 429: Success; duração 12m12s = perna mais lenta 11m22s + publish 46s,
  coerente com a dependência.

(g) = PASS.

## Achado (lacuna)

Acordar o app do sono do Streamlit Cloud o fez subir com as versões mais novas do
PyPI, sem push nem reboot. Isso explica o M8 da etapa 0 (o app já estava no
1.66.0 antes de qualquer push na master). Uma dependência nova, ou um cyclophaser
novo no PyPI, pode entrar em produção num wake-up sem passar pelo CI; a perna
newest detecta no próximo push, não impede.

## Desvios

- `compare_dists.py` e `clean_install.sh` só existiam na release/v2.1.3 durante a
  etapa 3; usei cópias extraídas de 67b126d por `git show` (registrado no
  cabeçalho dos logs).
- A mensagem da tag v2.1.3 ("CycloPhaser 2.1.3") é mais curta que a da v2.1.2;
  mantida porque já tinha push.
