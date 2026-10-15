# Release 2.1.3 — etapa 2: previsões (2026-10-15)

AUTORIZAÇÃO 1 (merge release/v2.1.3 -> develop): "sim" (Danilo, retorno da
PARADA 1). Commitadas e com push na release/v2.1.3 ANTES do merge em develop e
de qualquer medição da etapa 2; não serão ajustadas depois.

Estado antes do merge (lido): origin/develop = 4287d5b, ancestral da
release/v2.1.3; TestPyPI: 2.1.3 não existe (HTTP 404), última versão 2.1.2;
PyPI: 2.1.3 não existe (404).

Este commit traz, sobre f6daa41: as duas correções de texto do CHANGELOG pedidas
pelo Danilo, o registro do CI do pipeline 426 (etapa1/ci/f6daa41), o grep do
caso TestPyPI do clean_install.sh (passa a mostrar a troca do cmocean) e estas
previsões. Nada em cyclophaser/, setup.py, MANIFEST.in ou no app muda.

## Previsões

### Merge
- `git merge --no-ff release/v2.1.3` em develop: sem conflito; a árvore do
  commit de merge é IGUAL à árvore da ponta da release/v2.1.3.
- `git diff v2.1.2 <merge> -- cyclophaser`: vazio.

### Pipeline de develop no commit de merge
- build_test: success (wheel 1280 passed / 0 failed; source 1 passed / 0 failed).
- app_test_floor: success, 1507 passed / 0 failed.
- app_test_newest: success, 1507 passed / 0 failed.
- test_pypi_publish: **SUCCESS, com upload de verdade** (2 arquivos 2.1.3, sem
  "Skipping … already exists").
- pypi_publish: ausente do workflow (filtro de branch).

### Arquivos na TestPyPI vs build local do mesmo commit
- 2 arquivos: `cyclophaser-2.1.3-py3-none-any.whl` e `cyclophaser-2.1.3.tar.gz`.
- Wheel: os 6 arquivos `cyclophaser/` idênticos por conteúdo ao wheel local;
  Requires-Dist e Requires-Python iguais (os 6 + pytest extra; >=3.12).
- sdist: mesma lista de entradas; conteúdo idêntico em `cyclophaser/*`,
  `setup.py`, `MANIFEST.in`, `README.md`, `LICENSE`; 0 entradas em tests/.
- (Não prevejo identidade de bytes de WHEEL/PKG-INFO/RECORD nem do .tar.gz:
  dependem da versão do setuptools e de carimbos de tempo do build.)

### (b) a partir da TestPyPI (`--index-url https://test.pypi.org/simple/
`--no-deps cyclophaser==2.1.3`, dependências do PyPI)
- B1: cmocean 4.0.3; import + smoke OK.
- B2 (uv lowest-direct, only-binary, 6 pisos): cmocean 4.0.3, matplotlib 3.9.0,
  numpy 2.1.0, pandas 2.2.2, scipy 1.14.0, xarray 2024.9.0; import + smoke OK.
- B3 (cmocean==4.0.1 antes): o pip sobe 4.0.1 → 4.0.3; import + smoke OK.

### (d) no commit de merge de develop
- app_test_floor e app_test_newest verdes (os mesmos jobs do pipeline acima).
