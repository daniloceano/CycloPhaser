# Release 2.1.2 — fase 1 (preparar, não publicar): relatório

Frente: revisão da aba Benchmark (`docs/future_work.md` item 35, escrito depois do
release). Branch `release/v2.1.2`, criada de `develop` @ `33d3f08`. Autorização para
mudar a versão 2.1.1 → 2.1.2, escrita pelo Danilo: "autorizo".

## Item 0 — CircleCI `build_test` de `develop` @ `33d3f08`

### Primeira leitura (2026-10-09T21:26Z) — registro, não apagado

Pela API pública do CircleCI: a pipeline **399** (`develop`, `33d3f08`, criada às
20:09:59Z pelo webhook do push) estava em `created`, **sem nenhum workflow** e sem erro;
no GitHub, nenhum status para o commit. Todas as pipelines anteriores (388–398) tinham
rodado. Parei e relatei: nem passou nem falhou, não rodou.

### Segunda leitura (2026-10-10T02:22Z)

| | valor |
|---|---|
| pipeline | **399**, `f7731e24-…`, revisão `33d3f0838ca912d0e796891020dbd2622cb5a9cf`, criada 2026-10-09T20:09:59Z |
| workflow `build_test_publish` | **success**, criado **22:20:39Z**, terminado 23:01:41Z |
| job `build_test` | **#503**, success, 22:35:38Z → 22:38:49Z; relatório de testes: **1281 success, 0 failed, 58 skipped** (1339 itens) |
| job `test_pypi_publish` | **#504**, success, 23:00:45Z → 23:01:41Z |

### A discrepância

A leitura das 21:26Z estava certa para aquele momento: o workflow só foi criado às
**22:20:39Z**, 2 h 10 min depois da pipeline e quase uma hora depois da consulta. Foi
atraso do CircleCI. A tela do Danilo (23:21 de Brasília = 02:21Z, "Triggered 6h ago")
mostra a hora de disparo da pipeline (20:09Z), não a do workflow; nada foi disparado de
novo (um só workflow na pipeline). Item 0 cumprido.

## Previsão

`PREVISOES.md`, commit **`865e9a2`**, 2026-10-10T02:23:13Z (2026-10-09 23:23 em
Brasília), enviado antes de qualquer mudança de versão ou medição.

## O que mudou

| arquivo | mudança |
|---|---|
| `setup.py` | `VERSION = '2.1.2'` |
| `docs/conf.py` | `release = '2.1.2'` |
| `CHANGELOG.md` | `## [2.1.2] - 2026-10-09` (data local do commit), `## [Unreleased]` vazio acima; links `[Unreleased]` = `v2.1.2...HEAD`, `[2.1.2]` = `v2.1.1...v2.1.2`. A data substituiu um marcador depois das execuções (só texto) |
| `docs/generated/app_start.png` | regenerada; mostra **"CycloPhaser 2.1.2"** |
| `docs/generated/app_save.png` | regenerada; não mostra a versão; os bytes mudaram (captura de navegador não é reproduzível byte a byte), conteúdo igual |
| `research/benchmark_review/release/` | previsão, evidências, este relatório |

O script escreveu as cinco figuras: `app_sidebar.png`, `app_grid.png` e
`app_statistics.png` saíram **byte a byte idênticas** e não mudam. Nenhuma delas mostra a
versão; só `app_start.png` mostra (a previsão dizia isso e deixava os bytes sem previsão).
`git diff develop -- cyclophaser/`: vazio.

## Versão instalada

Env conda `cyclophaser`, `pip install -e . --no-deps`: `importlib.metadata.version` =
**2.1.2**, `cyclophaser.__file__` no repositório, um único `cyclophaser-2.1.2.dist-info`.
**Achado sem explicação**: antes da reinstalação, `pip show` dizia 2.1.0, enquanto as
figuras do I3, geradas nesse env, mostravam 2.1.1. A reinstalação substituiu os metadados
antigos e não dá mais para reconstruir a causa (dois dist-info, provavelmente). Não afeta
nenhuma medição desta fase.

## Previsão × medido

| execução | previsto | medido | arquivo |
|---|---|---|---|
| conda, streamlit 1.63.0 | 1508 / 0 | **1508 / 0** | `suite_conda_st1.63.0.txt` |
| venv streamlit 1.56.0 | 1508 / 0 | **1508 / 0** | `suite_st1.56.0.txt` |
| CI, wheel (`cyclophaser-2.1.2-py3-none-any.whl`) | 1280 / 0 | **1280 / 0** | `ci_recipe_summary.json` |
| CI, source tree | 1 / 0 | **1 / 0** | idem |
| Chromium 1.63.0 | 15 / 0 | **15 / 0**; e1 T1 4, T2 4, T3 1, T4 1, T5 0, T6 5, T7 2, T8 1, T9 0 | `browser_conda_st1.63.0.txt` |
| Chromium 1.56.0 | 15 / 0 | **15 / 0**; e1 igual | `browser_st1.56.0.txt` |
| documentação, checkout limpo da branch (diff inteiro, `setup.py` incluído) | 0 warnings | **0 warnings**, saída 0; o índice mostra "CycloPhaser 2.1.2" | `docs_build_release_2.1.2*.txt` |

`which python` e `cyclophaser.__file__` no topo de cada `suite_*`. `tests/test_label_browser.py`
não rodado; `manual_labels.yaml` intocado.

## Parado aqui (item 9)

Sem merge em `develop` nem em `master`, sem tag, item 35 não escrito. Próximos passos, só
com autorização: merge em `develop` e `master`, tag `v2.1.2`, publicação (CircleCI
`pypi_publish`), conferência no PyPI e no Read the Docs, item 35.
