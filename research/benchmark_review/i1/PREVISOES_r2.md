# I1, rodada 2 (correções do checkpoint) — previsão (commitada e enviada antes de qualquer medição desta rodada; não editar)

Data: 2026-10-08. Branch `feat/benchmark-review`; commit da etapa 1 da rodada 1 =
`2eeb85d`. A interface do I1 continua não commitada. Nenhuma execução de suíte, de
navegador ou de captura desta rodada aconteceu antes deste commit. Duas leituras
foram feitas antes, nenhuma de medição: o md5 e a altura de `full_page.png`
(confirmam o achado da verificação independente), e um `grep` nos testes atrás de
quem lê a frase de chaves completadas.

## Mudanças (resumo)

1. Cartão: diferenças como lista "`section.key`: este → referência".
2. Seletor de referência no topo da seção 4, visível com ≥ 1 coluna, antes ou
   depois do primeiro Run.
3. `config_text.filled_keys_sentence` lista só as chaves completadas cujo valor
   difere do default atual da assinatura (`benchmark_core.current_defaults`), com a
   tolerância de `compare_core._same` e depois de `package_use_filter`. A regra de
   completar (`fill_missing`) e a lista `filled` não mudam.
4. Limite de 4 colunas, controles de adicionar desabilitados com motivo visível.
5. "Invert" → "Invert selection" + ajuda, só na Compare.
6. Captura de página inteira de verdade; `manifest.json` com dimensões.

## Testes existentes que mudam por causa do item 3

- **Em `develop` (39e658c): nenhum.** Os testes que tocam chaves completadas
  (`tests/test_config_defaults.py`, `tests/test_item30_spare_intensification.py`)
  leem a lista `res["filled"]` de `_load_yaml_config`, que não muda; nenhum lê a
  frase.
- **Entre os testes novos da rodada 1 (ainda não commitados): um**,
  `tests/test_compare_core.py::test_the_filled_keys_sentence_is_one_function_for_both_pages`
  — afirma a frase exata para uma lista dada, e a frase passa a depender do default
  atual (e a dizer qual é). Nenhum outro teste muda.
- Fora dos testes: `research/benchmark_review/i1/check_inventory.py` procura a
  tabela "this configuration" no cartão (item 1) e passa a procurar a lista.

## Testes novos: 5

1. diferenças do cartão como lista, sem tabela no cartão (AppTest);
2. seletor de referência no topo da seção 4, antes e depois do Run, acima de
   "Relative to" (AppTest);
3. a frase de chaves completadas só lista o que difere do default atual: some
   `phase_params.prominence=None`; fica `prominence_relative` ausente → None
   (default atual 0.3); `use_filter` e float com ruído não aparecem (núcleo);
4. com 4 colunas, os três controles de adicionar desabilitados e o motivo em texto
   visível (AppTest);
5. "Invert selection" com a ajuda na Compare, "Invert" inalterado na Benchmark
   (AppTest).

Nenhum teste de navegador novo ou alterado previsto (os de e1 acham o seletor pelo
rótulo, que não muda).

## Suíte (só passed e failed)

| execução | passed | failed |
|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0, `-m "not browser"` | **1520** (1515 + 5) | **0** |
| venv streamlit 1.56.0, mesmo comando | **1520** | **0** |
| receita do CI, wheel | **1280** | **0** |
| receita do CI, source tree | **1** | **0** |
| Chromium (`test_app_pages_browser.py` + `test_compare_browser.py`), 1.63.0 | **11** | **0** |
| idem, 1.56.0 | **11** | **0** |

`test_compare_browser.py` 10 vezes seguidas sem falha em cada versão.

## e1

| tarefa | orçamento | previsto |
|---|---|---|
| T1 | ≤ 5 | 4 |
| T2 | ≤ 5 | 4 |
| T3 | ≤ 2 | 1 |
| T4 | ≤ 3 | 1 |
| T5 | 0 | 0 |

## e2

Nenhum termo proibido.

## Custo de Run

Não remedido: o caminho de detecção e o cache não mudam nesta rodada.
