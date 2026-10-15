# Release 2.1.3 — etapa 1: relatório (2026-10-14)

Branch `release/v2.1.3`, criada de 4287d5b (= origin/develop na hora).
Previsões: PREVISOES_etapa1.md, commit 20cfafe, com push antes das mudanças e
das medições. Mudanças: commit 6ce1bb5. Todas as medições locais abaixo são em
6ce1bb5; a ponta final da etapa 1 acrescenta só research/release_v213/ (este
relatório e os logs) sobre ele.

Plataforma local: macOS 14 (Darwin 23.1.0) arm64. Suíte e Chromium no env conda
`cyclophaser` (python 3.12.14). Instalações limpas: `/opt/homebrew/bin/python3.12`
(3.12.9), venv novo por linha, CWD fora do repo, `python -I`, smoke.py da etapa 0.

## Resultado por item

| item | previsto | medido | bate? | log |
|---|---|---|---|---|
| suíte base (develop 4287d5b) | — | 1508 passed, 0 failed | — | E1_base_suite_develop_4287d5b.log |
| suíte na ponta | 1508 / 0 | 1508 passed, 0 failed | sim | E1_suite_tip_6ce1bb5.log |
| (a) diff `cyclophaser/` v2.1.2..ponta | vazio | 0 bytes | sim | E1_a_diff_and_digest.log |
| (a) caminhos do diff completo | só os permitidos | .circleci (2), CHANGELOG.md, CLAUDE.md, MANIFEST.in, docs/conf.py, docs/future_work.md, research/ci_app_tests, research/release_v213, setup.py, tests/conftest.py, tests/sample_tracks (2), 2 testes, tools/calibration_app/requirements.txt | sim | idem |
| (a) digest v2.1.2 vs ponta | iguais | 7552bc67…aa500f nos dois (mesmo blob do gerador d060277, mesma sessão, mesmo env, main checkout; .txt restaurado após cada execução) | sim | idem |
| (b) B1 | cmocean 4.0.3, OK | cmocean 4.0.3 (numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, matplotlib 3.11.2, xarray 2026.9.0); smoke OK, `pip check` limpo | sim | E1_b_B1_local.log |
| (b) B2 | 4.0.3 / 3.9.0 / 2.1.0 / 2.2.2 / 1.14.0 / 2024.9.0, OK | exatamente esses (uv 0.13.1); smoke OK | sim | E1_b_B2_local.log |
| (b) B3 | pip sobe 4.0.1 → 4.0.3, OK | "Found existing installation: cmocean 4.0.1 … Successfully installed cmocean-4.0.3"; smoke OK | sim | E1_b_B3_local.log |
| (c) Requires-Dist | as 7 linhas | exatamente as 7 linhas; Requires-Python >=3.12; LICENSE presente | sim | E1_c_inspect_dists.log |
| (c) sdist tests/ | 0 entradas | 0 (22 entradas no total) | sim | idem |
| (c) wheel do sdist vs wheel direto | idênticos | 6/6 arquivos do pacote iguais por SHA256; METADATA igual | sim | idem |
| (c) instalação a partir do sdist | OK | smoke OK | sim | E1_c_sdist_install.log |
| (e) coleta | 15 | 15 | sim | E1_e_browser_*.log |
| (e) streamlit mais novo (1.66.0) | 15 / 0 | 15 passed, 0 failed, uma rodada | sim | E1_e_browser_newest.log |
| (e) streamlit 1.56.0 | 15 / 0 | 15 passed, 0 failed, uma rodada | sim | E1_e_browser_floor.log |
| (e) env devolvido | 1.63.0 | 1.63.0 (conda-forge pyhd8ed1ab_0); `pip list` e `conda list` idênticos aos de antes | sim | E1_e_restore.log |

`twine check --strict` nos dois artefatos: PASSED (E1_c_inspect_dists.log).

## Controle extra, sem previsão commitada

Como a plataforma mudou (Linux na etapa 0, macOS aqui), reproduzi a M2 no macOS:
cyclophaser 2.1.2 do PyPI com cmocean 4.0.1 pré-instalado → pip mantém 4.0.1,
`import cyclophaser` falha com o mesmo FileNotFoundError
(E1_b_control_M2_macos.log). Logo o B3 é um controle válido também nesta
plataforma. Neste log o `smoke_exit` é o do `tail` do pipe, não o do smoke.py;
o traceback mostra a falha.

## Desvios

- Plataforma das instalações limpas: macOS arm64 em vez de container Linux
  (daemon do Docker inativo). Declarado na previsão antes de medir.
- `uv` instalado num venv de ferramentas à parte, só para B2.
- O streamlit do env é do conda-forge; para (e) o pip o substituiu
  temporariamente, e a devolução foi `pip uninstall` + `conda install
  --force-reinstall --no-deps streamlit=1.63.0=pyhd8ed1ab_0`, para o metadado do
  conda continuar coerente.

## Documentação de usuário que cita dependências (não editada)

- `docs/installation.rst:26`: "pip installs the dependencies (NumPy, SciPy,
  pandas, xarray, Matplotlib, among others)". Continua verdadeira (o "among
  others" cobre o cmocean), mas é uma lista parcial.
- `docs/requirements.txt` (ambiente do build do Read the Docs, versões fixas,
  lido por `.readthedocs.yaml` antes de `pip install .`) fixa Sphinx e também
  as bibliotecas do pacote, incluindo cmocean==4.0.3, pandas==2.2.3 e várias
  das 15 que saíram do install_requires. Não é doc de usuário e não muda o que
  o pacote declara; satisfaz os pisos novos; fica registrado, não editado.
