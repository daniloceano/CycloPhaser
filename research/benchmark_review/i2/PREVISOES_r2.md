# I2, rodada 2 (correções do checkpoint) — previsão (commitada e enviada antes de qualquer medição desta rodada; não editar)

Data: 2026-10-09. Branch `feat/benchmark-review`; etapa 1 do I2 = `b197124`. A
interface do I2 continua não commitada. Nenhuma execução de suíte, de navegador ou de
captura desta rodada aconteceu antes deste commit, e nenhum código desta rodada foi
escrito ainda.

## Mudanças (resumo)

- **R1** — `config_text.breakable` (U+200B) sai. Os avisos de chaves completadas e de
  chaves ignoradas, na Compare e na Validate, passam a `st.markdown(…,
  unsafe_allow_html=True)` num bloco com aparência de aviso legível nos dois temas,
  com `<wbr>` só depois de "." e "_" (a mesma regra de `differences_html`). As frases
  (`filled_keys_sentence`, `ignored_keys_sentence`) não mudam; a Calibrate não muda.
- **R2** — o cabeçalho de cada lista de desacordo dá contagens por instrumento
  (sequência: diferente / fronteira fora da tolerância; mature: fora da margem) e
  nenhum número que combine os dois.
- **R3** — célula de snapshot sem o track = "not in this snapshot", separada de
  "detection failed" no bloco por configuração, nas listas de desacordo, nos blocos de
  concordância (nota sob cada tabela afetada) e sob a tabela "relative to"; nunca conta
  como desacordo no filtro.
- **F2** — linha "Results are current: …" também na Compare, e um teste da Compare que
  verifica o sumiço de "Results out of date" depois de um novo Run.

## Testes existentes alterados (previsto)

- `tests/test_validate_apptest.py::test_the_card_shows_differences_and_full_provenance` — R1 (o aviso deixa de ser `st.warning`).
- `tests/test_validate_apptest.py::test_card_format_and_filled_warning_shared_by_both_pages` — R1 (sem `breakable`; o bloco HTML com `<wbr>`).
- `tests/test_validate_apptest.py::test_disagreeing_tracks_listed_per_column_and_instrument` — R2 (formato do cabeçalho).
- `tests/test_validate_browser.py::test_the_filled_keys_warning_breaks_no_word_in_a_narrow_card` — R1 (o aviso já não é `stAlert`; acrescenta a ida e volta no DOM: o texto do aviso contém a chave real).

Nenhum teste existente da Compare muda (nenhum lê os avisos de chaves; F2 entra como
teste novo). Nenhum teste de `tests/test_validate_core.py` muda.

## Testes novos: 6 (sem navegador), 0 de navegador

1. `tests/test_compare_apptest.py::test_a_new_run_clears_the_out_of_date_warning` (F2)
2. `tests/test_validate_apptest.py::test_no_rendered_text_contains_a_zero_width_space` (R1, as duas páginas, controle: o varredor acha o caractere plantado)
3. `tests/test_validate_apptest.py::test_a_key_copied_from_a_warning_is_the_real_key` (R1, ida e volta: texto sem tags → chave; a chave copiada não é listada como ignorada)
4. `tests/test_validate_apptest.py::test_a_published_release_without_the_batch_tracks_says_so` (R3)
5. `tests/test_validate_apptest.py::test_validate_says_results_are_current_after_a_run` (F2 na Validate)
6. `tests/test_validate_core.py::test_snapshot_missing_tracks_are_not_failures` (R3)

## Suíte (só passed e failed)

| execução | passed | failed |
|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0, `-m "not browser"` | **1557** (1551 + 6) | **0** |
| venv streamlit 1.56.0, mesmo comando | **1557** | **0** |
| receita do CI, wheel | **1280** | **0** |
| receita do CI, source tree | **1** | **0** |
| Chromium (`test_app_pages_browser.py` + `test_compare_browser.py` + `test_validate_browser.py`), 1.63.0 | **14** | **0** |
| idem, 1.56.0 | **14** | **0** |

`tests/test_validate_browser.py` (alterado): 10 execuções seguidas sem falha em cada
versão. `tests/test_label_browser.py` não é rodado.

## e1 (mesmos orçamentos)

T6 **5** (≤ 6), T7 **2** (≤ 3), T8 **1** (≤ 2), T9 **0**.

## e2

Nenhum id do split de teste e nenhum "hit rate", "accuracy" ou "score" (fora de "not
a score") na Validate; nenhum termo proibido do I1 na Compare; nenhum U+200B em texto
renderizado das duas páginas.

## Custo de Run

Não remedido (caminho de detecção inalterado).
