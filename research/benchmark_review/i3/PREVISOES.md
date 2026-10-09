# I3 — aposentar a Benchmark antiga + documentação: previsão (commitada e enviada antes de qualquer medição; não editar)

Data: 2026-10-09. Branch `feat/benchmark-review`, base `c1617a0` (I1 e I2 commitados).
Nenhum código do I3 foi escrito e nenhuma execução de suíte, navegador, inventário,
captura ou build de documentação do I3 aconteceu antes deste commit. As únicas execuções
até aqui foram leituras: `pytest --collect-only` na base, para contar os testes por
arquivo (`TESTES.md`).

## O que muda (resumo)

- **Sai**: `tools/calibration_app/app_pages/benchmark.py`, `tools/calibration_app/benchmark_tab.py`,
  o item de menu, a entrada em `_PAGE_WIDGET_STATE`, o `import benchmark_tab` de `app.py`.
  Sem página provisória: `/benchmark` cai no comportamento padrão do `st.navigation`.
- **Fica**: `benchmark_core.py`, sem nenhuma função removida nem alterada; só a docstring
  do módulo muda, dizendo quem o usa.
- **Menu final**: Calibration = Calibrate, Compare; Developer (só com a chave) = Manual
  labelling, Validate against labels.
- **F5**: o cabeçalho de desacordo da Validate passa a "sequence: N tracks differ, N tracks
  with a boundary outside its tolerance · mature: N not within the margin". A parte do
  mature não muda: o briefing só fala das duas contagens de sequência.
- **Textos vivos** que citam a Benchmark como página existente: docstrings e comentários
  do app e dos testes, e a ajuda do controle "Custom track format" da Calibrate (a última
  frase cita "the Benchmark page's Exploration upload"). Essa ajuda é o único texto de
  interface fora da Validate que muda.
- **Documentação**: `tools/calibration_app/README.md`, `docs/calibration_tool.rst`,
  `CHANGELOG.md` (Unreleased), `research/labels/README.md`, `research/snapshots/README.md`.
  Também as duas figuras da documentação que mostram o menu (`docs/generated/app_start.png`,
  `docs/generated/app_sidebar.png`), regeneradas por `docs/figures/make_app_screenshots.py`.
  Nada disso é commitado antes da revisão do Danilo.

## Testes

A migração completa está em `TESTES.md`: 62 testes removidos (coberto 21, migrado 27,
aposentado 14), 13 novos sem navegador, 1 novo de navegador, e a lista de testes alterados.

## Suíte (só passed e failed)

| execução | passed | failed |
|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0, `-m "not browser"` | **1508** (1557 − 62 + 13) | **0** |
| venv streamlit 1.56.0, mesmo comando | **1508** | **0** |
| receita do CI, wheel | **1280** | **0** |
| receita do CI, source tree | **1** | **0** |
| Chromium (`test_app_pages_browser.py` + `test_compare_browser.py` + `test_validate_browser.py`), 1.63.0 | **15** (14 + 1) | **0** |
| idem, 1.56.0 | **15** | **0** |

O CI não muda: todo teste removido, alterado ou novo depende de `streamlit`, que a receita
do CI não instala, e o arquivo novo `tests/test_phase_figures.py` também pula sem ele.

**Repetição**: os testes de navegador novos ou alterados — os 5 alterados de
`tests/test_app_pages_browser.py` e o novo — rodam 10 vezes seguidas, sem falha, em cada
versão. `tests/test_label_browser.py` não é rodado.

## e1 de regressão (Chromium, mesmos orçamentos, nas duas versões)

| tarefa | orçamento | previsto |
|---|---|---|
| T1 | ≤ 5 | 4 |
| T2 | ≤ 5 | 4 |
| T3 | ≤ 2 | 1 |
| T4 | ≤ 3 | 1 |
| T5 | 0 | 0 |
| T6 | ≤ 6 | 5 |
| T7 | ≤ 3 | 2 |
| T8 | ≤ 2 | 1 |
| T9 | 0 | 0 |

## e2, rodado de novo (dentro das suítes, nas duas versões)

- Compare: nenhum termo proibido do I1 em nenhum estado
  (`test_e2_no_forbidden_term_anywhere_on_the_compare_page`); o controle do varredor passa a
  achar termos na Validate; a Compare roda com a leitura de rótulos quebrada e a Validate,
  sob o mesmo patch, falha.
- Validate: nenhum id do split de teste, nenhum "hit rate", "accuracy" ou "score" (fora de
  "not a score"); o controle do varredor de ids acha ids de teste na página Manual
  labelling; nenhum U+200B em texto renderizado das duas páginas.

## Inventário (portão b)

Um script do I3 (`research/benchmark_review/i3/check_inventory.py`) roda, nesta árvore, a
parte 1 de cada script anterior, sem alterá-los:

- `i1/check_inventory.py` parte 1: os **34** itens P presentes na Compare, **0** faltando;
- `i2/check_inventory.py` parte 1: os **24** itens D presentes na Validate, **2** REPLACED
  (A1, como no I2), **0** faltando;

e duas comparações novas contra `c1617a0`, cada checkout no seu processo:

- Compare: a mesma vista do I2 (widgets, textos, tabelas, resultados, imagens,
  expanders) **idêntica, sem normalização**;
- Validate: as mesmas interações nas duas árvores; diferenças cruas **só** nos cabeçalhos
  de desacordo (F5), e **nenhuma** depois de desfazer só o F5. Isso é a evidência de (f):
  mesmos números, mesmos conjuntos.

`TESTES.md` completo, nenhuma garantia sem teste nomeado. `REFERENCIAS.md`: a varredura
final não acha referência viva à página Benchmark fora das que ficarem listadas como
ambíguas, à espera da decisão do Danilo.

## Documentação

Build como o Read the Docs, em checkout limpo (worktree de `HEAD` + as mudanças de
`docs/` e `tools/calibration_app/`, venv nova, `docs/requirements.txt`, `pip install .`,
`sphinx-build -b html -E`): **0 warnings**, saída 0.

## Portão

(a) `git diff develop -- cyclophaser/` vazio. (b)–(f) como acima. (g) declarado: a frente
exige o release 2.1.2 depois do merge; versão não tocada (`docs/conf.py` continua 2.1.1).
(d) e (e3) ficam pendentes: param no checkpoint, com capturas do menu público, do menu
Developer, do cabeçalho F5 e de `/benchmark` depois da remoção, e com a revisão do build
local da documentação pelo Danilo.
