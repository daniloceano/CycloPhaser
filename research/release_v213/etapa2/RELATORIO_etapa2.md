# Release 2.1.3 — etapa 2: relatório (2026-10-15)

AUTORIZAÇÃO 1 "sim" (Danilo). Previsões: PREVISOES_etapa2.md, b68425f, com push
antes do merge. Merge `--no-ff` release/v2.1.3 → develop = **1177c7e** (pai
4287d5b + b68425f), push em origin/develop.

| item | previsto | medido | bate? | fonte |
|---|---|---|---|---|
| árvore do merge = árvore da release | igual | bc249d34… nas duas | sim | git |
| diff `cyclophaser/` v2.1.2..1177c7e | vazio | 0 bytes | sim | git |
| build_test | success, 1280/0 + 1/0 | #623 success, 1280 passed + 1 passed, 0 failed | sim | ci/1177c7e |
| app_test_floor | 1507/0 | #622 success, 1507/0 | sim | idem |
| app_test_newest | 1507/0 | #621 success, 1507/0 | sim | idem |
| test_pypi_publish | SUCCESS com upload | #624 success; twine "Uploading … 200 OK" para o wheel e o sdist | sim | idem |
| pypi_publish | ausente | ausente | sim | idem |
| TestPyPI: 2 arquivos | whl + tar.gz | whl f38f44a4…, tar.gz 4d5dead5… (SHA256 da API conferido no download) | sim | logs/E2_testpypi_vs_local.log |
| wheel TestPyPI vs local (1177c7e) | 6 arquivos do pacote iguais; metadados iguais | TODOS os membros iguais por conteúdo (inclusive METADATA, WHEEL, RECORD) | sim (mais do que o previsto) | idem |
| sdist TestPyPI vs local | pacote, setup.py, MANIFEST.in, README.md, LICENSE iguais; 0 em tests/ | todos os membros iguais por conteúdo; 0 em tests/ | sim | idem |
| (b) B1 TestPyPI | cmocean 4.0.3, OK | 4.0.3, smoke OK | sim | logs/E2_b_B1_testpypi.log |
| (b) B2 TestPyPI | pisos | cmocean 4.0.3, mpl 3.9.0, numpy 2.1.0, pandas 2.2.2, scipy 1.14.0, xarray 2024.9.0; smoke OK | sim | logs/E2_b_B2_testpypi.log |
| (b) B3 TestPyPI | 4.0.1 → 4.0.3, OK | "Found existing installation: cmocean 4.0.1 … Successfully installed cmocean-4.0.3"; smoke OK | sim | logs/E2_b_B3_testpypi.log |
| (d) em 1177c7e | as 2 pernas verdes | pipeline 427: floor #622 e newest #621 success | sim | ci/1177c7e |

Pipeline 427: https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/427

Notas:
- O cyclophaser dos três venvs veio da TestPyPI: 2.1.3 não existe no PyPI (404)
  e a instalação usou só `--index-url https://test.pypi.org/simple/ --no-deps`;
  as dependências vieram do PyPI (B1/B3 por pip a partir do Requires-Dist
  instalado; B2 por uv com os 6 pisos). "Using cached" no B3 é o wheel da
  TestPyPI baixado no B1.
- Build local: macOS arm64, build 1.6.1, setuptools 84.0.0 (isolado). Os bytes
  dos dois arquivos diferem dos da TestPyPI (carimbos de tempo), o conteúdo não.
- Estes registros estão na release/v2.1.3, não em develop, para não mover o
  commit verificado em (d).
