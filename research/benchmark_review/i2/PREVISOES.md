# I2 (página Developer "Validate against labels") — previsão (escrita, commitada e enviada antes de qualquer medição; não editar)

Data: 2026-10-08. Branch `feat/benchmark-review`, base `f3008fc` (I1 commitado).
Nenhum código de interface do I2 existe ainda e nada desta rodada foi executado antes
deste commit. Leituras feitas antes, nenhuma de medição do detector nem da suíte:
o código do app e dos testes; o registro do I1 (`research/benchmark_review/i1/`);
e uma contagem estrutural da população (split e rótulos, sem detecção):
`split.yaml` treino 47 (35 reais + 12 sintéticos), teste 16; lote `swell_item30`
7 treino + 3 teste; rótulos com a nota de adjudicação: 5, todos entre os 7 de treino
do lote, nenhum nos 47 nem no teste.

Conjuntos previstos daí: lote desligado → bloco TRAIN n = 47, sem bloco
ADJUDICATED; lote ligado → TRAIN n = 49 (47 + 2 do lote não adjudicados) e
ADJUDICATED n = 5, nunca somados. Previsão: todo rótulo oferecido tem
`series_sha256` igual ao da série carregada do disco (a página vai conferir; se
algum não bater, o n acima muda e isso conta como desvio).

## 1. Suíte (só passed e failed)

Estado de partida, do registro da rodada 2 do I1 (árvore que virou `f3008fc`):
conda 1.63.0 **1520 / 0**; venv 1.56.0 **1520 / 0**; CI wheel **1280 / 0**; CI
source tree **1 / 0**.

### Testes novos planejados (todos atrás de `pytest.importorskip("streamlit")`)

`tests/test_validate_core.py` (9, sem Streamlit no código testado):
1. `test_population_offers_train_only_and_withholds_test_labels`
2. `test_batch_adds_seven_train_tracks_and_never_its_test_ones`
3. `test_blocks_train_and_adjudicated_are_disjoint_and_never_summed`
4. `test_agreement_uses_the_two_benchmark_instruments_unchanged`
5. `test_track_notes_sequence_and_mature_offsets`
6. `test_disagreement_lists_per_instrument`
7. `test_tolerance_spans_from_a_label`
8. `test_figures_without_tolerances_are_byte_identical_and_with_them_differ`
   (PNGs de `phase_figures` sem a opção nova = os de `f3008fc`, com a paleta da
   Compare; o teste existente já cobre a Benchmark contra `39e658c`)
9. `test_a_label_whose_series_hash_differs_is_not_used`

`tests/test_validate_apptest.py` (22, API pública do AppTest):
1. `test_validate_is_absent_without_the_developer_key` (controle: presente com a chave)
2. `test_validate_sits_in_the_developer_menu_with_title_and_sentence`
3. `test_the_offered_tracks_are_the_train_split_all_selected`
4. `test_all_real_all_synthetic_invert_and_clear`
5. `test_the_batch_checkbox_adds_its_train_tracks_only`
6. `test_the_column_sources` (Current settings, Defaults, arquivo de configs/,
   snapshot; Upload YAML vai para o navegador)
7. `test_six_columns_disable_every_add_control_with_a_visible_reason`
8. `test_the_card_shows_differences_and_full_provenance`
9. `test_edit_marks_the_card_edited_in_session_and_remove`
10. `test_the_reference_selector_lists_columns_only_and_tops_the_results`
11. `test_run_blocked_says_why_in_visible_text`
12. `test_nothing_recomputes_on_edit_and_the_cache_holds_across_runs`
13. `test_train_block_shows_both_instruments_with_set_and_n`
14. `test_validate_numbers_equal_the_benchmark_train_table` (controle cruzado)
15. `test_adjudicated_block_only_with_the_batch_and_never_pooled`
16. `test_disagreeing_tracks_listed_per_column_and_instrument`
17. `test_per_track_label_panel_first_notes_layouts_filter_and_pages`
18. `test_the_validate_state_survives_a_trip_to_calibrate`
19. `test_e2_no_test_id_and_no_forbidden_word_anywhere`
20. `test_e2_the_scanners_find_planted_terms_on_the_benchmark_page`
21. `test_relative_table_and_per_configuration_block_match_compare`
22. `test_card_format_and_filled_warning_shared_by_both_pages` (pendências 1–2)

`tests/test_validate_browser.py` (3, marcados `browser`, servidor com a chave):
1. e1 T9 → T6 → T8 → T7 numa sessão, contando interações;
2. estado da Validate sobrevive a uma ida à Calibrate no navegador (A12);
3. o aviso de chave completada não quebra palavra no meio, num cartão estreito da
   Compare (4 colunas) e da Validate (6 colunas) — medido no DOM (cada palavra
   alfanumérica do aviso ocupa um só retângulo de linha); YAML temporário escrito e
   removido pelo próprio teste.

Total: **31** novos sem navegador, **3** de navegador.

### Testes existentes alterados (previsto)

Só um: `tests/test_compare_apptest.py::test_card_differences_are_a_compact_list_not_a_table`
— pendência 1: a linha esperada passa de "`filter_params.cutoff_high`: 18 → 48" para
"…: 18 (reference: 48)", e o estilo de quebra passa de `overflow-wrap:anywhere` para
pontos de quebra só depois de "." e "_" (pendência 2 aplicada também à lista). Nenhum
outro teste existente muda; `tests/test_benchmark_apptest.py` e
`tests/test_compare_browser.py` passam sem alteração.

### Previsão

| execução | passed | failed |
|---|---|---|
| env conda `cyclophaser`, streamlit 1.63.0, `pytest -m "not browser"` | **1551** (1520 + 31) | **0** |
| venv streamlit 1.56.0 (piso), mesmo comando | **1551** | **0** |
| receita do CI, wheel | **1280** | **0** |
| receita do CI, source tree | **1** | **0** |
| Chromium, `test_app_pages_browser.py` + `test_compare_browser.py` + `test_validate_browser.py`, 1.63.0 | **14** (8 + 3 + 3) | **0** |
| idem, 1.56.0 | **14** | **0** |

Forma estrutural, que vale se a contagem de testes novos mudar na construção: nenhum
teste existente quebra além do listado acima, e todo teste novo passa. Contagem final
diferente de 31 / 3 conta como previsão errada, explicada no relatório.
`tests/test_label_browser.py` não é rodado nem previsto.

## 2. e1 (Chromium, 1.56.0 e 1.63.0)

Ponto de partida, não contado: servidor com a chave de desenvolvedor, Calibrate
aberta uma vez (sem carregar dados).

| tarefa | orçamento | previsto |
|---|---|---|
| T6 Defaults × params-track no treino, ver os dois blocos de instrumento | ≤ 6 | **5** (menu Validate, Add Defaults, escolher params-track, adicionar o arquivo, Run) |
| T7 (após T6) ligar o lote, ver o bloco adjudicated | ≤ 3 | **2** (checkbox, Run) |
| T8 (após T6) só os tracks em desacordo e a figura de um | ≤ 2 | **1** (filtro) |
| T9 Run bloqueado, ler o motivo | 0 | **0** |

`tests/test_validate_browser.py`: 10 execuções seguidas sem falha em cada versão.

## 3. Custo de Run

### Procedimento (fixado aqui)

Script `research/benchmark_review/i2/measure_run.py` (escrito depois deste commit),
AppTest, env conda `cyclophaser` (streamlit 1.63.0), esta máquina,
`CYCLOPHASER_APP_DEV=1`.

- Ponto de partida: Calibrate aberta uma vez, sem dados.
- Seis configurações, todas "Current settings" tomadas da Calibrate: C1 = estado
  inicial; C2..C6 = C1 com `cutoff_high` = 48, 30, 24, 36, 42. 2 colunas = C1, C2;
  6 colunas = C1..C6.
- Séries: as 47 de treino oferecidas, todas selecionadas; lote desligado.
- Layout "Side by side", painel do rótulo ligado, página de figuras padrão (12).
- **Frio**: `st.cache_data.clear()` imediatamente antes do clique em Run (limpa
  também o cache das séries do disco e das figuras). **Quente**: um segundo clique
  em Run logo depois, sem mudar nada.
- Tempo: relógio de parede do `at.run()` que segue o clique (inclui o rerun
  depois de guardar o resultado, o cálculo dos dois instrumentos e o desenho).
- 3 repetições por célula; vale a mediana.

### Previsão (segundos, mediana)

| colunas | frio | quente |
|---|---|---|
| 2 | 6,5 (faixa 3,25–13) | ≤ 2 |
| 6 | 17 (8,5–34) | ≤ 2 |

Base: na Compare (I1), ~2,8 s por coluna sobre 51 tracks com 12 figuras por
coluna; aqui 47 séries, mais o painel do rótulo (12 figuras), a releitura das
séries do disco depois do `clear()` e os dois instrumentos por coluna.

Ordinais: (1) quente ≤ 0,25 × frio, nas duas larguras; (2) frio 6 / frio 2 entre
2,0 e 3,5.

Observação, não critério do portão.

## 4. e2

- (i) sem a chave, a Validate não está no menu; o teste do I1 da Compare (termos
  proibidos) passa sem alteração;
- (ii) na Validate, em todos os estados varridos, **nenhum** id do split de teste
  (os 16 e os 3 de teste do lote) aparece em texto algum, e nenhum texto contém
  "hit rate", "accuracy" ou "score" (palavra inteira) fora de "not a score";
- (iii) controle positivo: os dois varredores acham o termo na página Benchmark
  (id de teste no modo Exploration; "hit rate" nos resultados de Validation).

## 5. (g)

A frente exige o release **2.1.2** no fim; o I2 não toca a versão.
