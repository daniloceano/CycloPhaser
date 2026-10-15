# Release 2.1.3 — etapa 1: previsões (2026-10-14)

Commitadas e com push ANTES de qualquer mudança em setup.py, MANIFEST.in,
docs/conf.py, CHANGELOG.md ou tools/calibration_app/requirements.txt, e antes de
qualquer medição da etapa 1 além da linha de base. Não serão ajustadas depois.

## Linha de base (medida, não prevista)

develop 4287d5b, env conda `cyclophaser` (python 3.12.14, streamlit 1.63.0),
`python -m pytest -m "not browser"`: **1508 passed, 0 failed**
(logs/E1_base_suite_develop_4287d5b.log).

## Plataforma das medições locais (desvio declarado da etapa 0)

A etapa 0 mediu em container Linux. Nesta máquina o daemon do Docker não está
ativo; as instalações limpas de (b)/(c) serão feitas em macOS 14 arm64, com
`/opt/homebrew/bin/python3.12`, um venv NOVO por linha, CWD fora do repo,
`python -I`, e o smoke.py da etapa 0 conferindo `cyclophaser.__file__` no
site-packages do venv. `uv` não está instalado: será instalado num venv de
ferramentas à parte, só para B2.

## Previsões

### Suíte na ponta (env conda, `-m "not browser"`)
- **1508 passed, 0 failed** (= base).

### (a)
- `git diff v2.1.2 <ponta> -- cyclophaser`: **vazio**.
- Diff completo v2.1.2..ponta toca só os caminhos permitidos pelo critério.
- `default_behaviour_hash.py` em v2.1.2 e na ponta, mesma sessão, mesmo env,
  main checkout: **digests iguais**. (Não prevejo o valor: o pacote mudou depois
  do último registro do .txt.)

### (b) local (wheel construído aqui)
- B1 (pip escolhe as mais novas): **cmocean 4.0.3**; import + smoke OK.
- B2 (uv `--resolution lowest-direct --only-binary :all:` com os 6 pisos):
  **cmocean 4.0.3, matplotlib 3.9.0, numpy 2.1.0, pandas 2.2.2, scipy 1.14.0,
  xarray 2024.9.0**; import + smoke OK.
- B3 (cmocean==4.0.1 pré-instalado, depois o wheel): o pip **sobe o cmocean
  4.0.1 → 4.0.3**; import + smoke OK.

### (c)
- Requires-Dist do wheel, exatamente estas 7 linhas:
  `cmocean>=4.0.3`, `matplotlib>=3.9`, `numpy>=2.1`, `pandas>=2.2.2`,
  `scipy>=1.14`, `xarray>=2024.9`, `pytest>=8.3; extra == "test"`.
- Requires-Python `>=3.12`; LICENSE presente no wheel.
- sdist: **0 entradas em tests/**.
- Wheel construído a partir do sdist: arquivos do pacote **idênticos por
  conteúdo** ao wheel direto.
- Instalação a partir do sdist num venv limpo: import + smoke OK.

### (e) Chromium, env conda
- Coleta dos 3 arquivos: **15** testes.
- streamlit mais novo do dia (previsto 1.66.0): **15 passed, 0 failed**.
- streamlit 1.56.0: **15 passed, 0 failed**.
- Depois, streamlit do env devolvido a **1.63.0**.

### CI da branch (push da ponta sem [skip ci])
- build_test: success (wheel 1280 passed / 0 failed; source 1 passed / 0 failed).
- app_test_floor: success, 1507 passed / 0 failed.
- app_test_newest: success, 1507 passed / 0 failed.
- test_pypi_publish e pypi_publish: **ausentes** do workflow (filtros de branch).
