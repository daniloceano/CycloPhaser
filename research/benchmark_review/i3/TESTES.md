# I3 — migração dos testes (commitada com a previsão, antes de qualquer código do I3)

Frente `docs/future_work.md` item 35, incremento I3: aposentar a Benchmark antiga.
Base: `feat/benchmark-review` @ `c1617a0`. Contagens de coleta medidas na base
(conda `cyclophaser`, `-m "not browser"`, `--collect-only`): `test_benchmark_apptest.py`
53, `test_app_navigation_apptest.py` 11, `test_app_passo5_fixes.py` 21,
`test_track_upload_apptest.py` 10, `test_compare_apptest.py` 27,
`test_validate_apptest.py` 26, `test_validate_core.py` 10.

Destinos:
- **coberto por `<teste>`**: um teste que já existe na base garante a mesma coisa na
  Compare ou na Validate;
- **migrado para `<teste>`**: a garantia passa para um teste novo ou alterado, nomeado
  abaixo;
- **aposentado: `<motivo>`**: a função testada deixou de existir por decisão registrada
  (etapa 0, I1, I2 ou este briefing). Nenhuma das garantias exigidas pelo briefing está
  nesta categoria.

Abreviações: `cmp` = `tests/test_compare_apptest.py`, `val` = `tests/test_validate_apptest.py`,
`vcore` = `tests/test_validate_core.py`, `nav` = `tests/test_app_navigation_apptest.py`,
`pf` = `tests/test_phase_figures.py` (arquivo novo), `pages` = `tests/test_app_pages_browser.py`,
`cbr` = `tests/test_compare_browser.py`, `vbr` = `tests/test_validate_browser.py`.

## 1. `tests/test_benchmark_apptest.py` — removido inteiro (53 testes)

| # | teste removido | destino |
|---|---|---|
| 1 | `test_two_configurations_load_as_two_columns` | coberto por `cmp::test_the_relative_table_declares_the_set_and_the_reference` (duas colunas, uma por fonte) e `val::test_the_column_sources` (quatro colunas, com a origem de cada uma) |
| 2 | `test_a_third_column_is_added_on_demand_without_disturbing_the_first_two` | migrado para `cmp::test_adding_editing_or_removing_a_column_leaves_the_others_untouched` (novo) |
| 3 | `test_every_column_reports_on_exactly_the_selected_cyclones` | migrado para `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo: toda coluna reporta exatamente a seleção, na mesma ordem) |
| 4 | `test_changing_the_selection_repoints_every_column_together` | migrado para `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo: depois de mudar a seleção e rodar, toda coluna reporta a seleção nova) |
| 5 | `test_no_results_exist_before_run` | migrado para `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo: nenhum resultado antes de Run) |
| 6 | `test_editing_a_column_after_a_run_marks_the_results_out_of_date` | coberto por `cmp::test_nothing_recomputes_on_edit_and_results_go_stale` e `val::test_nothing_recomputes_on_edit_and_the_cache_holds_across_runs` |
| 7 | `test_default_mode_is_validation` | aposentado: o modo Validation/Exploration deixou de existir; as duas ferramentas viraram duas páginas (etapa 0, "1 · Mode") |
| 8 | `test_exploration_mode_switches_and_persists` | aposentado: idem |
| 9 | `test_cyclone_upload_is_offered_only_in_exploration_mode` | aposentado: o upload do modo Exploration saiu (etapa 0, A6; a Compare usa os tracks da Calibrate). A garantia por trás dele — a página de rótulos só oferece fontes rotuladas — é coberta por `val::test_the_offered_tracks_are_the_train_split_all_selected` e `vcore::test_population_offers_train_only_and_withholds_test_labels` |
| 10 | `test_reference_defaults_to_the_manual_label_when_labels_exist` | aposentado: o rótulo deixou de ser referência (A1; I2) |
| 11 | `test_reference_can_be_pointed_at_a_configuration_column` | coberto por `val::test_the_reference_selector_lists_columns_only_and_tops_the_results` e `cmp::test_changing_the_reference_runs_no_detection` |
| 12 | `test_figure_layout_defaults_to_side_by_side_and_switches_to_stacked` | coberto por `cmp::test_both_layouts_render_with_the_legend_and_errors_per_cell` e `val::test_per_track_label_panel_first_notes_layouts_filter_and_pages` |
| 13 | `test_figure_layout_does_not_change_any_result` | **migrado para** `cmp::test_the_figure_layout_does_not_change_any_result` (novo) e `val::test_layout_and_label_panel_do_not_change_any_result` (novo) |
| 14 | `test_manual_label_overlay_is_off_by_default` | aposentado: decisão do I2 (aprovada no checkpoint) — na Validate o painel do rótulo vem **ligado** (`val::test_per_track_label_panel_first_notes_layouts_filter_and_pages` fixa isso); a Compare não lê rótulo nenhum (`cmp::test_e2_compare_renders_and_runs_with_label_reading_broken`) |
| 15 | `test_manual_label_overlay_switches_on_and_back_off` | coberto por `val::test_per_track_label_panel_first_notes_layouts_filter_and_pages` (desliga e religa o painel) |
| 16 | `test_toggling_the_label_overlay_does_not_change_any_column_result` | **migrado para** `val::test_layout_and_label_panel_do_not_change_any_result` (novo) |
| 17 | `test_the_sidebar_differs_from_params_track_in_a_declared_parameter` | migrado para `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo: Current settings e Defaults diferem no parâmetro declarado, `filter_params.cutoff_high` 48 × 18, e 48 não é o default da assinatura) |
| 18 | `test_the_two_configurations_are_actually_distinguishable` | migrado para o mesmo teste novo (controle: as duas colunas diferem em pelo menos um track) |
| 19 | `test_each_column_carries_its_own_configuration_not_its_neighbours` | **migrado para** `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo; cada coluna = `benchmark_core.run_series` da própria configuração, chamado fora do app) |
| 20 | `test_swapping_the_columns_would_fail_the_pin` | migrado para o mesmo teste novo (controle: as colunas trocadas não passam o pino) |
| 21 | `test_editing_one_column_leaves_the_other_untouched` | **migrado para** `cmp::test_adding_editing_or_removing_a_column_leaves_the_others_untouched` (novo) |
| 22 | `test_an_edited_column_reports_edited_instead_of_a_source_hash` | coberto por `val::test_edit_marks_the_card_edited_in_session_and_remove` ("edited in session" no lugar do sha256) e `cmp::test_edit_and_remove_a_column` ("Edited on this page."); e o teste novo `cmp::test_adding_editing_or_removing_a_column_leaves_the_others_untouched` verifica que **só** a coluna editada fica marcada |
| 23 | `test_removing_a_column_leaves_the_others_intact` | migrado para `cmp::test_adding_editing_or_removing_a_column_leaves_the_others_untouched` (novo) |
| 24 | `test_the_uploaded_row_really_has_no_label` | migrado para `vcore::test_an_unlabelled_row_is_never_scored` (novo: a guarda do fixture — o id não tem rótulo) |
| 25 | `test_an_unlabelled_row_is_computed_but_never_scored` | **migrado para** `vcore::test_an_unlabelled_row_is_never_scored` (novo) e `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` (novo). Na Compare toda linha é sem rótulo, é calculada e nunca pontuada: coberto por `cmp::test_e2_compare_renders_and_runs_with_label_reading_broken` |
| 26 | `test_scoring_counts_only_the_labelled_rows` | migrado para `vcore::test_an_unlabelled_row_is_never_scored` (novo: os dois instrumentos contam só a linha rotulada) |
| 27 | `test_the_unlabelled_guard_would_catch_a_leak` | migrado para `vcore::test_an_unlabelled_row_is_never_scored` (novo: controle positivo — com um rótulo plantado no id, a contagem sobe) |
| 28 | `test_configuration_cards_render_inside_section_three` | aposentado: o defeito (cartões órfãos ao recolher o expander "3 · Configurations") dependia das seções recolhíveis da Benchmark; Compare e Validate não têm seção recolhível — os cartões ficam no bloco "2 · Configurations", sob um `st.subheader` |
| 29 | `test_run_button_lives_in_section_three_and_results_in_section_four` | aposentado: idem (estrutura de seções da página removida). A ordem do topo dos resultados é coberta por `cmp::test_the_reference_selector_tops_the_results_before_and_after_run` e `val::test_the_reference_selector_lists_columns_only_and_tops_the_results` |
| 30 | `test_the_individual_pill_list_is_collapsed_by_default` | aposentado: propriedade de layout da página removida; o layout da Validate e da Compare foi aprovado pelo Danilo nas capturas do I1 e do I2 |
| 31 | `test_switching_back_to_validation_drops_the_unlabelled_rows` | **migrado para** `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` (novo) |
| 32 | `test_run_is_disabled_and_explains_itself_when_nothing_is_set_up` | coberto por `val::test_run_blocked_says_why_in_visible_text`, `cmp::test_run_without_columns_is_blocked_and_says_why_in_visible_text` e, no navegador, T5 (`cbr`) e T9 (`vbr`) |
| 33 | `test_run_names_the_missing_configuration` | coberto por `val::test_run_blocked_says_why_in_visible_text` ("To run, add at least one configuration.") e `cmp::test_run_without_columns_is_blocked_and_says_why_in_visible_text` |
| 34 | `test_run_names_the_missing_selection` | coberto por `val::test_run_blocked_says_why_in_visible_text` ("To run, select at least one track.") e `cmp::test_run_without_a_selected_track_is_blocked_and_says_why` |
| 35 | `test_run_is_enabled_once_both_preconditions_are_met` | coberto por `val::test_run_blocked_says_why_in_visible_text` (Run habilitado depois de "All real") |
| 36 | `test_the_blocked_message_keeps_the_section_name_readable` | aposentado: a mensagem de bloqueio não cita mais nome de seção ("To run, …") |
| 37 | `test_forcing_an_unlabelled_row_back_into_a_validation_run_is_rejected` | **migrado para** `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` (novo: um id sem rótulo e um id de teste escritos direto na seleção não ficam nela e não chegam ao resultado do Run) |
| 38 | `test_the_mode_leak_guard_is_sensitive` | migrado para o mesmo teste novo (controle: um id oferecido escrito do mesmo jeito fica e roda) |
| 39 | `test_the_parameter_baseline_card_is_labelled_not_diffed_against_itself` | aposentado: sem rótulo como referência não existe "parameter baseline" (A1; item REPLACED do inventário do I2) |
| 40 | `test_a_non_baseline_card_still_shows_its_differences` | coberto por `cmp::test_card_differences_are_a_compact_list_not_a_table` e `val::test_the_card_shows_differences_and_full_provenance` |
| 41 | `test_the_two_columns_smooth_differently` | migrado para `pf::test_two_configurations_smooth_differently` (novo) |
| 42 | `test_each_cell_draws_its_own_columns_smoothed_series` | migrado para `pf::test_each_cell_draws_its_own_columns_smoothed_series` (novo; `phase_figures.cell_figure`, a função que a Compare e a Validate desenham) |
| 43 | `test_a_cell_without_a_smoothed_series_draws_raw_only` | migrado para `pf::test_a_cell_without_a_smoothed_series_draws_raw_only` (novo; a coluna de release publicado da Validate é a que não tem `z`) |
| 44 | `test_each_stacked_panel_draws_its_own_columns_smoothed_series` | migrado para `pf::test_each_stacked_panel_draws_its_own_columns_smoothed_series` (novo) |
| 45 | `test_a_run_keeps_each_columns_own_smoothed_series` | migrado para `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo: o `z` guardado de cada coluna é o da própria configuração) |
| 46 | `test_the_batch_is_what_split_yaml_records` | coberto por `vcore::test_batch_adds_seven_train_tracks_and_never_its_test_ones` (7 de treino, 3 de teste, lidos do split) e `tests/test_swell_batch.py` |
| 47 | `test_the_default_population_does_not_contain_the_batch` | coberto por `vcore::test_population_offers_train_only_and_withholds_test_labels` (47, `batch_ids == []`) |
| 48 | `test_the_batch_is_off_by_default_and_not_selectable` | **migrado para** `val::test_the_batch_checkbox_adds_its_train_tracks_only` (alterado: a caixa começa desmarcada e as 47 opções não têm id do lote) |
| 49 | `test_the_batch_appears_with_the_control_on_and_goes_with_it_off` | **migrado para** `val::test_the_batch_checkbox_adds_its_train_tracks_only` (alterado: ao desligar, nenhum id do lote fica na seleção) |
| 50 | `test_the_train_button_treats_the_batch_like_the_split` | aposentado: sem botão Train (decisão 1 do I2, aceita); a população oferecida é o treino, inteira selecionada na chegada (`val::test_the_offered_tracks_are_the_train_split_all_selected`), e com o lote são 54 selecionados (`val::test_the_batch_checkbox_adds_its_train_tracks_only`) |
| 51 | `test_the_batch_test_cases_are_never_scored` | coberto por `vcore::test_batch_adds_seven_train_tracks_and_never_its_test_ones` (os 3 nunca são lidos) e `val::test_adjudicated_block_only_with_the_batch_and_never_pooled` (blocos train n = 49 e adjudicated n = 5, nenhum bloco de teste) |
| 52 | `test_adjudicated_labels_have_their_own_block_with_the_batch_on` | coberto por `val::test_adjudicated_block_only_with_the_batch_and_never_pooled` e `vcore::test_blocks_train_and_adjudicated_are_disjoint_and_never_summed` |
| 53 | `test_the_adjudicated_guard_would_catch_a_pooling` | **migrado para** `vcore::test_the_adjudicated_guard_would_catch_a_pooling` (novo; o mesmo controle, por `validate_core.agreement`) |

## 2. Referências em outros arquivos

### Testes removidos (9)

| teste removido | destino |
|---|---|
| `nav::test_validation_does_not_offer_the_test_split` | coberto por `val::test_the_offered_tracks_are_the_train_split_all_selected` (nenhuma opção é id gasto) e `vcore::test_population_offers_train_only_and_withholds_test_labels` (os arquivos de teste nunca são abertos) |
| `nav::test_exploration_runs_a_test_series_but_never_scores_it` | aposentado: o modo Exploration saiu. A garantia ("uma série de teste nunca é pontuada") fica com `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` (novo) e `vcore::test_population_offers_train_only_and_withholds_test_labels`; a Compare não lê rótulo (`cmp::test_e2_compare_renders_and_runs_with_label_reading_broken`) |
| `tests/test_app_passo5_fixes.py::test_a_second_preset_click_gives_what_the_button_gives_on_its_own` (4 parametrizações) | coberto por `val::test_all_real_all_synthetic_invert_and_clear` (sequência All real → Invert → Clear → All synthetic, cada clique conferido) e `cmp::test_all_invert_clear_and_individual_selection`. O mecanismo do defeito — uma seleção guardada à parte do multiselect — não existe nas páginas novas: o estado da seleção é a própria chave do widget (`val_tracks`, `cmp_tracks`) |
| `tests/test_app_passo5_fixes.py::test_clear_empties_both_the_selection_and_the_widget` | coberto pelos mesmos dois testes (Clear → `[]` na chave do widget) |
| `tests/test_track_upload_apptest.py::test_benchmark_upload_accepts_txt_and_has_help` | aposentado: o upload da Benchmark (Exploration) saiu (A6). O upload que resta, o da Calibrate, já é coberto por `test_upload_field_accepts_txt_and_has_help` e `test_standard_content_with_txt_extension_reaches_the_grid` (mesmo arquivo); a Compare recebe esses tracks (`cmp::test_compare_receives_the_calibrate_tracks_all_selected`) |
| `tests/test_track_upload_apptest.py::test_benchmark_exploration_uses_the_same_custom_format` | aposentado: idem. Um arquivo em formato próprio entra pela Calibrate (`test_custom_file_is_previewed_and_used_only_after_confirmation`), e a Compare roda os tracks com o mesmo leitor e eixo de tempo da Calibrate (`cmp::test_compare_phases_are_the_calibrate_phases`) |

### Testes alterados (mesmo número, nome novo quando o antigo cita a Benchmark)

| arquivo | teste (nome final) | mudança |
|---|---|---|
| `nav` | helper `_rendered` | reconhece a Compare (título "Compare configurations") no lugar da Benchmark (`bench_run`) |
| `nav` | `test_the_menu_has_calibrate_and_compare_and_calibrate_is_the_default` (era `…_and_benchmark_…`) | Compare no lugar da Benchmark |
| `nav` | `test_the_developer_page_is_absent_without_the_key` | controle positivo: a troca para a Compare funciona |
| `nav` | `test_calibrate_state_survives_a_trip_to_compare_and_back` (era `…_to_benchmark_…`) | ida e volta pela Compare |
| `nav` | `test_a_bad_case_mark_survives_a_trip_to_compare_and_back` (era `…_to_benchmark_…`) | idem |
| `nav` | `test_the_trip_loses_the_state_without_the_shield` | controle negativo pela Compare |
| `nav` | `test_add_column_from_the_sidebar_reflects_the_calibrate_sidebar` | "Add Current settings" da Compare (`cmp_add_current`, `cmp_columns`) |
| `tests/test_app_passo5_fixes.py` | `test_the_track_upload_and_its_caption_are_in_the_calibration_tab_only` | confere a Compare no lugar da Benchmark |
| `tests/test_calibrate_i2_apptest.py` | `test_a_bad_case_mark_survives_grid_inspector_grid_and_a_page_trip` | viagem pela Compare |
| `tests/test_calibrate_i3_apptest.py` | `test_a_bad_case_mark_on_page_one_survives_page_two_the_inspector_and_compare` (era `…_and_benchmark`) | idem |
| `tests/test_calibrate_i3_apptest.py` | `test_the_page_size_survives_the_inspector_and_a_page_trip`, `test_the_grid_columns_survive_the_inspector_and_a_page_trip` | idem |
| `tests/test_sidebar_defaults.py` | `test_an_untouched_sidebar_column_equals_determine_periods_without_arguments`, `test_the_equivalence_above_can_fail` | a coluna "Current settings" é rodada na Validate (chave de desenvolvedor, lote ligado: os 3 tracks de treino, 1 do lote), não mais na Benchmark |
| `tests/test_phase_colors.py` | `test_the_other_pages_copies_have_not_drifted` | sem `benchmark_tab`; confere `labels_core.PHASE_COLORS` e que a Compare e a Validate desenham com `layer_inspector.PHASE_COLORS` |
| `vcore` | `test_figures_without_tolerances_are_byte_identical_and_with_them_differ` | só a paleta `layer_inspector.PHASE_COLORS` (a cópia de `benchmark_tab` some; era igual, `test_phase_colors.py`) |
| `cmp` | `test_compare_is_in_the_calibration_menu_after_calibrate` | menu `[_PAGE_CALIBRATE, _PAGE_COMPARE]` |
| `cmp` | `test_e2_the_scanner_finds_planted_terms_on_the_validate_page` (era `…_on_the_benchmark_page`) | o controle do varredor passa a ser a Validate (chave de desenvolvedor), que tem os termos |
| `cmp` | `test_e2_compare_renders_and_runs_with_label_reading_broken` | controle: sob o mesmo patch, a **Validate** falha |
| `cmp` | `test_compare_pngs_are_byte_identical_to_the_benchmark_of_39e658c` (era `test_benchmark_pngs_are_byte_identical_to_before_the_move`) | compara `phase_figures` (com `layer_inspector.PHASE_COLORS`, o que a Compare passa) com o `benchmark_tab.py` de `39e658c`, lido por `git show`; não importa `benchmark_tab` atual |
| `cmp` | `test_invert_selection_is_labelled_and_explained` (era `…_on_compare_only`) | sem a metade da Benchmark; confere o rótulo e a ajuda nas duas páginas que restam |
| `val` | `test_validate_numbers_equal_benchmark_core_on_the_train_split` (era `test_validate_numbers_equal_the_benchmark_train_table`) | a referência independente deixa de ser a página Benchmark e passa a ser o que ela calculava: `benchmark_core.run_series` + `benchmark_core.metrics_by_split` com `labels_for_display` e `split_membership`, chamados fora do app |
| `val` | `test_e2_the_scanners_find_planted_terms_on_the_labelling_page` (era `…_on_the_benchmark_page`) | controle do varredor de ids: a página Manual labelling lista os ids de teste ("[TEST split — locked]"); o de palavras, por textos plantados |
| `val` | `test_disagreeing_tracks_listed_per_column_and_instrument` | F5: "N tracks differ", "N tracks with a boundary outside its tolerance" |
| `val` | `test_the_batch_checkbox_adds_its_train_tracks_only` | começa desmarcada; ao desligar, nenhum id do lote fica selecionado |
| `pages` | `test_the_public_menu_has_calibrate_and_compare_and_no_developer` (era `…_and_benchmark_…`) | Calibrate e Compare; sem Developer, Manual labelling, Validate against labels e Benchmark |
| `pages` | `test_the_developer_menu_has_the_labelling_and_validate_pages` (era `test_the_developer_menu_has_the_labelling_page`) | Calibrate, Compare, Developer, Manual labelling, Validate against labels; sem Benchmark |
| `pages` | `test_an_uploaded_track_and_an_imported_yaml_survive_a_page_trip` | viagem pela Compare |
| `pages` | `test_sidebar_values_set_in_the_ui_are_shown_after_page_trips` | idem |
| `pages` | `test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser` | idem |

Só docstring/comentário: `tests/test_config_defaults.py`, `tests/test_track_upload_apptest.py`
(cabeçalho), os cabeçalhos de `cmp`, `val`, `vcore`, `nav`, `pages`, `tests/test_app_passo5_fixes.py`,
`tests/test_sidebar_defaults.py`. `tests/test_swell_batch.py::test_validation_is_not_in_the_benchmark_even_with_the_batch_on`
testa `benchmark_core` (que fica) e não muda.

## 3. Testes novos (13 sem navegador, 1 de navegador)

| teste novo | garantia |
|---|---|
| `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` | cada coluna com a própria configuração (pino + controles: distinguíveis, trocadas falham), alinhamento à seleção, nenhum resultado antes de Run, `z` da própria coluna |
| `cmp::test_adding_editing_or_removing_a_column_leaves_the_others_untouched` | coluna editada marcada (e só ela); as outras não se movem ao acrescentar, editar ou remover |
| `cmp::test_the_figure_layout_does_not_change_any_result` | layout de figura não muda resultado (Compare) |
| `val::test_layout_and_label_panel_do_not_change_any_result` | layout de figura e painel de rótulo não mudam resultado (Validate) |
| `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` | linha sem rótulo e id do split de teste nunca chegam a um Run, nem forçados (controle: um id oferecido forçado do mesmo jeito fica e roda) |
| `vcore::test_an_unlabelled_row_is_never_scored` | linha sem rótulo nunca pontuada pelos dois instrumentos (controle: com rótulo plantado, conta) |
| `vcore::test_a_track_without_a_label_is_not_offered` | um track de treino sem rótulo não é oferecido, com o motivo (controle: com o rótulo, é) |
| `vcore::test_the_adjudicated_guard_would_catch_a_pooling` | controle positivo da separação treino × adjudicados |
| `pf::test_two_configurations_smooth_differently` | controle dos três abaixo |
| `pf::test_each_cell_draws_its_own_columns_smoothed_series` | célula desenha o `z` da própria coluna |
| `pf::test_a_cell_without_a_smoothed_series_draws_raw_only` | coluna sem `z` desenha só o bruto |
| `pf::test_each_stacked_panel_draws_its_own_columns_smoothed_series` | painel empilhado desenha o `z` do próprio painel |
| `nav::test_the_benchmark_page_is_gone` | a página e o módulo saíram; o caminho antigo cai na página padrão (controle: a Compare abre) |
| `pages::test_the_old_benchmark_address_opens_the_default_page` (navegador) | `/benchmark` cai no comportamento padrão do `st.navigation` (a Calibrate desenha) e nenhum menu cita a Benchmark |

## 4. Garantias exigidas pelo briefing → teste nomeado

| garantia | teste(s) |
|---|---|
| split de teste nunca pontuado | `vcore::test_population_offers_train_only_and_withholds_test_labels`, `vcore::test_batch_adds_seven_train_tracks_and_never_its_test_ones`, `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` (novo), `val::test_e2_no_test_id_and_no_forbidden_word_anywhere` |
| linha sem rótulo nunca pontuada | `vcore::test_an_unlabelled_row_is_never_scored` (novo), `vcore::test_a_track_without_a_label_is_not_offered` (novo), `val::test_a_forced_unlabelled_or_test_id_never_reaches_a_run` (novo), `cmp::test_e2_compare_renders_and_runs_with_label_reading_broken` |
| adjudicados nunca somados ao treino | `vcore::test_blocks_train_and_adjudicated_are_disjoint_and_never_summed`, `val::test_adjudicated_block_only_with_the_batch_and_never_pooled`, `vcore::test_the_adjudicated_guard_would_catch_a_pooling` (novo, controle) |
| lote swell desligado por padrão e separado ao ligar | `val::test_the_batch_checkbox_adds_its_train_tracks_only` (alterado), `val::test_adjudicated_block_only_with_the_batch_and_never_pooled`, `vcore::test_population_offers_train_only_and_withholds_test_labels` |
| estado sobrevive a ida/volta de página — Compare | AppTest `cmp::test_the_compare_state_survives_a_trip_to_calibrate`; Chromium `cbr::test_the_compare_state_survives_a_trip_to_calibrate_in_the_browser` |
| estado sobrevive a ida/volta de página — Validate | AppTest `val::test_the_validate_state_survives_a_trip_to_calibrate`; Chromium `vbr::test_the_validate_state_survives_a_trip_to_calibrate_in_the_browser` |
| menu público sem Developer, Validate e Benchmark | `pages::test_the_public_menu_has_calibrate_and_compare_and_no_developer` (alterado), `val::test_validate_is_absent_without_the_developer_key`, `nav::test_the_benchmark_page_is_gone` (novo), `pages::test_the_old_benchmark_address_opens_the_default_page` (novo) |
| Run bloqueado com motivo visível | `cmp::test_run_without_columns_is_blocked_and_says_why_in_visible_text`, `cmp::test_run_without_a_selected_track_is_blocked_and_says_why`, `val::test_run_blocked_says_why_in_visible_text`; Chromium T5 (`cbr::test_e1_tasks_t5_t1_t3_t4_within_budget`) e T9 (`vbr::test_e1_tasks_t9_t6_t8_t7_within_budget`) |
| cada coluna com a própria configuração | `cmp::test_each_column_carries_its_own_configuration_not_its_neighbours` (novo), `pf::test_each_cell_draws_its_own_columns_smoothed_series` (novo), `pf::test_each_stacked_panel_draws_its_own_columns_smoothed_series` (novo) |
| coluna editada marcada | `val::test_edit_marks_the_card_edited_in_session_and_remove`, `cmp::test_edit_and_remove_a_column`, `cmp::test_adding_editing_or_removing_a_column_leaves_the_others_untouched` (novo) |
| layout de figura e painel de rótulo não mudam resultado | `cmp::test_the_figure_layout_does_not_change_any_result` (novo), `val::test_layout_and_label_panel_do_not_change_any_result` (novo) |

Nenhuma garantia sem teste nomeado.

## 5. Contagem

- Removidos: **62** (53 de `test_benchmark_apptest.py`; 2 de `nav`; 5 de
  `test_app_passo5_fixes.py`, 4 parametrizações + 1; 2 de `test_track_upload_apptest.py`).
- Destino dos 62: coberto **21** (15 + 6), migrado **27** (27 + 0), aposentado **14** (11 + 3)
  (contagem por linha das tabelas 1 e 2; o arquivo de medição confere a soma).
- Novos sem navegador: **13** (`cmp` 3, `val` 2, `vcore` 3, `pf` 4, `nav` 1).
- Novo de navegador: **1** (`pages`).
- Suíte sem navegador: 1557 − 62 + 13 = **1508**.
- Chromium (`pages` + `cbr` + `vbr`): 14 + 1 = **15**.
