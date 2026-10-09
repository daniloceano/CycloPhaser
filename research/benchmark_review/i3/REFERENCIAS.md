# I3 — referências a "benchmark" (gerado por `sweep_references.py`; não editar à mão)

Base (antes): `ae3a6c7` · depois: árvore de trabalho. Varredura sem distinguir maiúsculas, em texto (`git grep -i`) e em nomes de arquivo. Classes e regras no cabeçalho do script.

Na tabela **antes**, cada VIVA é uma referência à página Benchmark como existente; o arquivo dela está na coluna nota quando foi alterado nesta rodada. Na tabela **depois**, VIVA deve ser 0.

## Resultado

- antes: VIVA 112, AMBÍGUA 2, CORRETA 81, HISTÓRICA 939
- depois: VIVA **0**, AMBÍGUA 0, CORRETA 123, HISTÓRICA 1051

## Antes (base)

| classe | ocorrências |
|---|---|
| HISTÓRICA | 939 |
| CORRETA | 81 |
| AMBÍGUA | 2 |
| VIVA | 112 |

### HISTÓRICA — por arquivo (233 arquivos, não tocados)

| arquivo | linhas/nome |
|---|---|
| `CHANGELOG.md` | 11 |
| `docs/findings.md` | 5 |
| `docs/future_work.md` | 34 |
| `research/app_redesign/close/RELATORIO.md` | 1 |
| `research/app_redesign/i1/INVENTARIO.md` | 8 |
| `research/app_redesign/i1/PREVISOES.md` | 3 |
| `research/app_redesign/i1/RELATORIO.md` | 19 |
| `research/app_redesign/i1/capture_screenshots.py` | 8 |
| `research/app_redesign/i1/captures/after/benchmark.png` | 1 |
| `research/app_redesign/i1/captures/after/manifest.json` | 1 |
| `research/app_redesign/i1/captures/after_extras/manifest.json` | 1 |
| `research/app_redesign/i1/captures/before/benchmark.png` | 1 |
| `research/app_redesign/i1/captures/before/manifest.json` | 1 |
| `research/app_redesign/i1/inventory_check.txt` | 5 |
| `research/app_redesign/i1/measure_after.json` | 3 |
| `research/app_redesign/i1/measure_before.json` | 3 |
| `research/app_redesign/i1/measure_interactions.py` | 7 |
| `research/app_redesign/i2/INVENTARIO.md` | 4 |
| `research/app_redesign/i2/RELATORIO.md` | 3 |
| `research/app_redesign/i2/badmark_after.txt` | 2 |
| `research/app_redesign/i2/check_badmark.py` | 3 |
| `research/app_redesign/i3/INVENTARIO.md` | 2 |
| `research/app_redesign/i3/RELATORIO.md` | 6 |
| `research/app_redesign/i3/diag/after2_cpu4_conda_st1.63.0.jsonl` | 9 |
| `research/app_redesign/i3/diag/after2_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after2_cpu4_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after2_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after2_normal_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after2_normal_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after2_normal_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after2_normal_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_cpu4_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_cpu4_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_normal_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_normal_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_normal_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_normal_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/before2_cpu4_conda_st1.63.0.jsonl` | 15 |
| `research/app_redesign/i3/diag/before2_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/before2_cpu4_st1.56.0.jsonl` | 20 |
| `research/app_redesign/i3/diag/before2_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/control_injected_error_conda.jsonl` | 1 |
| `research/app_redesign/i3/diag/control_injected_error_conda_summary.txt` | 1 |
| `research/app_redesign/i3/diag/control_tolerated_media404_conda.jsonl` | 3 |
| `research/app_redesign/i3/diag/control_tolerated_media404_conda_summary.txt` | 1 |
| `research/app_redesign/i3/diag/exec_cpu4_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/exec_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/exec_cpu4_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/exec_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag_paged_grid_plugin.py` | 1 |
| `research/benchmark_review/i1/PREVISOES.md` | 13 |
| `research/benchmark_review/i1/PREVISOES_r2.md` | 5 |
| `research/benchmark_review/i1/RELATORIO.md` | 36 |
| `research/benchmark_review/i1/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/capture_screenshots.py` | 2 |
| `research/benchmark_review/i1/captures/01_empty.png` | 1 |
| `research/benchmark_review/i1/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i1/captures/03_columns.png` | 1 |
| `research/benchmark_review/i1/captures/04_results.png` | 1 |
| `research/benchmark_review/i1/captures/05_side_by_side.png` | 1 |
| `research/benchmark_review/i1/captures/06_stacked.png` | 1 |
| `research/benchmark_review/i1/captures/07_filter.png` | 1 |
| `research/benchmark_review/i1/captures/08_reference.png` | 1 |
| `research/benchmark_review/i1/captures/09_filled_warning.png` | 1 |
| `research/benchmark_review/i1/captures/10_limit.png` | 1 |
| `research/benchmark_review/i1/captures/11_invert_help.png` | 1 |
| `research/benchmark_review/i1/captures/full_page.png` | 1 |
| `research/benchmark_review/i1/captures/manifest.json` | 1 |
| `research/benchmark_review/i1/check_inventory.py` | 14 |
| `research/benchmark_review/i1/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i1/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i1/inventory_check.txt` | 3 |
| `research/benchmark_review/i1/measure_run.json` | 5 |
| `research/benchmark_review/i1/measure_run.py` | 11 |
| `research/benchmark_review/i1/r1/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/r1/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/r1/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/r1/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/r1/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i1/r1/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i1/r1/inventory_check.txt` | 3 |
| `research/benchmark_review/i1/r1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/r1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/run_browser.sh` | 3 |
| `research/benchmark_review/i1/run_repeat_browser.sh` | 3 |
| `research/benchmark_review/i1/run_suite.sh` | 4 |
| `research/benchmark_review/i1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/PREVISOES.md` | 10 |
| `research/benchmark_review/i2/PREVISOES_r2.md` | 2 |
| `research/benchmark_review/i2/RELATORIO.md` | 19 |
| `research/benchmark_review/i2/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/capture_screenshots.py` | 2 |
| `research/benchmark_review/i2/captures/01_arrival.png` | 1 |
| `research/benchmark_review/i2/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i2/captures/03_cards.png` | 1 |
| `research/benchmark_review/i2/captures/04_provenance.png` | 1 |
| `research/benchmark_review/i2/captures/05_train_block.png` | 1 |
| `research/benchmark_review/i2/captures/06_disagreements.png` | 1 |
| `research/benchmark_review/i2/captures/07_side_by_side.png` | 1 |
| `research/benchmark_review/i2/captures/08_stacked.png` | 1 |
| `research/benchmark_review/i2/captures/09_filter.png` | 1 |
| `research/benchmark_review/i2/captures/10_adjudicated.png` | 1 |
| `research/benchmark_review/i2/captures/11_limit.png` | 1 |
| `research/benchmark_review/i2/captures/12_validate_filled_warning.png` | 1 |
| `research/benchmark_review/i2/captures/13_compare_filled_warning.png` | 1 |
| `research/benchmark_review/i2/captures/14_disagreement_headers.png` | 1 |
| `research/benchmark_review/i2/captures/15_snapshot_note.png` | 1 |
| `research/benchmark_review/i2/captures/16_validate_results_current.png` | 1 |
| `research/benchmark_review/i2/captures/17_compare_results_current.png` | 1 |
| `research/benchmark_review/i2/captures/18_validate_warning_dark.png` | 1 |
| `research/benchmark_review/i2/captures/19_compare_warning_dark.png` | 1 |
| `research/benchmark_review/i2/captures/full_page.png` | 1 |
| `research/benchmark_review/i2/captures/manifest.json` | 1 |
| `research/benchmark_review/i2/check_inventory.py` | 11 |
| `research/benchmark_review/i2/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i2/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i2/inventory_check.txt` | 3 |
| `research/benchmark_review/i2/measure_run.json` | 2 |
| `research/benchmark_review/i2/measure_run.py` | 4 |
| `research/benchmark_review/i2/r1/captures/01_arrival.png` | 1 |
| `research/benchmark_review/i2/r1/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i2/r1/captures/03_cards.png` | 1 |
| `research/benchmark_review/i2/r1/captures/04_provenance.png` | 1 |
| `research/benchmark_review/i2/r1/captures/05_train_block.png` | 1 |
| `research/benchmark_review/i2/r1/captures/06_disagreements.png` | 1 |
| `research/benchmark_review/i2/r1/captures/07_side_by_side.png` | 1 |
| `research/benchmark_review/i2/r1/captures/08_stacked.png` | 1 |
| `research/benchmark_review/i2/r1/captures/09_filter.png` | 1 |
| `research/benchmark_review/i2/r1/captures/10_adjudicated.png` | 1 |
| `research/benchmark_review/i2/r1/captures/11_limit.png` | 1 |
| `research/benchmark_review/i2/r1/captures/12_validate_filled_warning.png` | 1 |
| `research/benchmark_review/i2/r1/captures/13_compare_filled_warning.png` | 1 |
| `research/benchmark_review/i2/r1/captures/full_page.png` | 1 |
| `research/benchmark_review/i2/r1/captures/manifest.json` | 1 |
| `research/benchmark_review/i2/r1/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i2/r1/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i2/r1/inventory_check.txt` | 3 |
| `research/benchmark_review/i2/r1/measure_run.json` | 2 |
| `research/benchmark_review/i2/r1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/r1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/r2/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/r2/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/01_arrival.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/03_cards.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/04_provenance.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/05_train_block.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/06_disagreements.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/07_side_by_side.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/08_stacked.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/09_filter.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/10_adjudicated.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/11_limit.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/12_validate_filled_warning.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/13_compare_filled_warning.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/full_page.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/manifest.json` | 1 |
| `research/benchmark_review/i2/rodada1_final/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i2/rodada1_final/inventory_check.txt` | 3 |
| `research/benchmark_review/i2/rodada1_final/measure_run.json` | 2 |
| `research/benchmark_review/i2/rodada1_final/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/run_browser.sh` | 3 |
| `research/benchmark_review/i2/run_repeat_browser.sh` | 3 |
| `research/benchmark_review/i2/run_suite.sh` | 4 |
| `research/benchmark_review/i2/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i3/PREVISOES.md` | 12 |
| `research/benchmark_review/i3/TESTES.md` | 32 |
| `research/benchmark_review/stage0/DECISIONS.md` | 19 |
| `research/cleanup/MANIFEST.md` | 49 |
| `research/cleanup/final/b_app_tests.txt` | 1 |
| `research/cleanup/final/f_post_6b.json` | 2 |
| `research/cleanup/final/streamlit_guards_after.json` | 2 |
| `research/cleanup/final/streamlit_guards_before.json` | 2 |
| `research/cleanup/passo0/branches.json` | 1 |
| `research/cleanup/passo0/defaults_in_text.json` | 1 |
| `research/cleanup/passo0/defaults_in_text.md` | 1 |
| `research/cleanup/passo0/inventory.json` | 45 |
| `research/cleanup/passo0/judgements.py` | 8 |
| `research/cleanup/passo0/make_manifest.py` | 6 |
| `research/cleanup/passo0/manifest_summary.json` | 3 |
| `research/cleanup/passo1/commit4_ast_check.txt` | 2 |
| `research/cleanup/passo1/params15_refs.json` | 1 |
| `research/cleanup/passo2/findings_src.md` | 2 |
| `research/cleanup/passo2/make_findings.py` | 1 |
| `research/cleanup/passo2/traceability.json` | 5 |
| `research/cleanup/passo3/removed_files.txt` | 5 |
| `research/cleanup/passo4/fix_stale_200_texts.py` | 4 |
| `research/cleanup/passo4/fix_stale_200_texts_log.json` | 4 |
| `research/cleanup/passo4/rtd_map.md` | 1 |
| `research/cleanup/passo5/PREVISOES.md` | 2 |
| `research/cleanup/passo5/RELATORIO.md` | 2 |
| `research/cleanup/passo5/app_tests.txt` | 1 |
| `research/cleanup/passo5/b_test_ids_after.json` | 1 |
| `research/cleanup/passo5/b_test_ids_before.json` | 1 |
| `research/cleanup/passo5/e2_benchmark_pinned_before.txt` | 121 |
| `research/cleanup/passo5/e2_probe_multiselect.py` | 1 |
| `research/cleanup/passo5/e2_probe_pinned.txt` | 1 |
| `research/cleanup/passo5/make_report.py` | 6 |
| `research/cleanup/passo6/branches.json` | 2 |
| `research/cleanup/passo6/branches.md` | 2 |
| `research/cleanup/passo6/delete_6b.json` | 2 |
| `research/cleanup/passo6/delete_6b_check.json` | 1 |
| `research/cleanup/passo6/future_work_item32.md` | 2 |
| `research/cleanup/passo6/future_work_item32.py` | 3 |
| `research/cleanup/passo6/post_6b.json` | 2 |
| `research/cleanup/passo6/removal_list.md` | 1 |
| `research/labels/diagnostics/item19/item19_core.py` | 1 |
| `research/labels/diagnostics/item30/item30_core.py` | 1 |
| `research/labels/split.yaml` | 1 |
| `research/labels/swell_item30/README.md` | 1 |
| `research/labels/swell_item30/freeze_validation_batch.py` | 1 |
| `research/release_v21/parteB_passo1/06_sdist_files.txt` | 1 |
| `research/release_v21/parteB_passo1/08_app.md` | 5 |
| `research/release_v21/parteB_passo1/09_changelog.md` | 1 |
| `research/release_v21/parteB_passo2/07_ci_steps_summary.json` | 2 |
| `research/release_v21/parteB_passo2/RELATORIO.md` | 1 |
| `research/release_v21/parteB_passo2/changelog.diff` | 2 |

### VIVA — por linha (112)

| arquivo:linha | texto | nota |
|---|---|---|
| `docs/calibration_tool.rst:18` | * Compare configurations side by side (the **Benchmark** page). | atualizada nesta rodada |
| `docs/calibration_tool.rst:29` | * **Benchmark** — run configurations side by side on the same tracks. | atualizada nesta rodada |
| `docs/calibration_tool.rst:170` | The app's own documentation (input formats, the developer key, the Benchmark | atualizada nesta rodada |
| `research/labels/README.md:90` | Benchmark shows that hash as a column's provenance, and every later record | atualizada nesta rodada |
| `research/labels/README.md:98` | by `evaluate_against_labels.py` (stderr), by the Benchmark column's provenance | atualizada nesta rodada |
| `research/snapshots/README.md:5` | cases). They are the Benchmark tab's reference columns: what the detector did | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:10` | Benchmark `bench_run`, Manual labelling `label_default_tolerance`. | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:14` | * the menu has Calibrate and Benchmark, and Calibrate is the default page; | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:19` | trip to Benchmark and back — with a NEGATIVE control showing the same trip | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:22` | * the Benchmark page shows no score or metric against a test-split label. | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:87` | "benchmark": any(b.key == "bench_run" for b in at.button), | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:103` | def test_the_menu_has_calibrate_and_benchmark_and_calibrate_is_the_default(): | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:107` | assert _rendered(at, BENCHMARK) == "benchmark" | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:115` | assert _rendered(at, BENCHMARK) == "benchmark"   # positive control: switching works | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:179` | def test_calibrate_state_survives_a_trip_to_benchmark_and_back(): | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:182` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:190` | def test_a_bad_case_mark_survives_a_trip_to_benchmark_and_back(): | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:198` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:222` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:233` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:243` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:250` | # ── Benchmark: no score against a test-split label, anywhere ────────────────── | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:260` | at = _go(_app(), BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_navigation_apptest.py:271` | at = _go(_app(), BENCHMARK) | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:11` | imported YAML must survive a trip to Benchmark and back. | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:117` | def test_the_public_menu_has_calibrate_and_benchmark_and_no_developer(public_server, pw): | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:123` | assert "Calibrate" in nav and "Benchmark" in nav, nav | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:135` | for word in ("Calibrate", "Benchmark", "Developer", "Manual labelling"): | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:251` | _go(page, "Benchmark", "1 · Mode") | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:312` | _go(page, "Benchmark", "1 · Mode") | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:474` | Inspector and the Benchmark page, the browser shows the kept page size, the | atualizada nesta rodada |
| `tests/test_app_pages_browser.py:523` | _go(page, "Benchmark", "1 · Mode") | atualizada nesta rodada |
| `tests/test_app_passo5_fixes.py:6` | (I1) Calibrate and Benchmark are separate pages, and this is checked per page. | atualizada nesta rodada |
| `tests/test_app_passo5_fixes.py:7` | * The Benchmark preset buttons (All real, All synthetic, Train, Invert, Clear; | atualizada nesta rodada |
| `tests/test_app_passo5_fixes.py:56` | # ── AppTest: upload placement and the Benchmark selection ───────────────────── | atualizada nesta rodada |
| `tests/test_app_passo5_fixes.py:80` | no-data screen is in Calibrate's main area; neither may show on Benchmark. | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py` | (nome de arquivo) | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py:1` | """Streamlit-level tests for the Benchmark tab — public API only. | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py:73` | """The app on its Benchmark page — opened the way a user opens it: Calibrate | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py:75` | Benchmark from the menu (app redesign I1; Benchmark used to be a tab that | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py:79` | at.switch_page(BENCHMARK_PAGE).run() | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py:112` | at.switch_page(BENCHMARK_PAGE).run() | atualizada nesta rodada |
| `tests/test_benchmark_apptest.py:763` | import benchmark_tab as bt  # noqa: E402 | atualizada nesta rodada |
| `tests/test_calibrate_i3_apptest.py:167` | def test_a_bad_case_mark_on_page_one_survives_page_two_the_inspector_and_benchmark( | atualizada nesta rodada |
| `tests/test_compare_apptest.py:15` | Benchmark page, with the same scanner. | atualizada nesta rodada |
| `tests/test_compare_apptest.py:16` | * Compare runs with the label readers raising — and the Benchmark page, under | atualizada nesta rodada |
| `tests/test_compare_apptest.py:174` | '_PAGE_BENCHMARK]}') in src | atualizada nesta rodada |
| `tests/test_compare_apptest.py:521` | def test_e2_the_scanner_finds_planted_terms_on_the_benchmark_page(): | atualizada nesta rodada |
| `tests/test_compare_apptest.py:522` | at = _go(_app(None), BENCHMARK) | atualizada nesta rodada |
| `tests/test_compare_apptest.py:550` | # control: the same patch does reach the app — the Benchmark page fails | atualizada nesta rodada |
| `tests/test_compare_apptest.py:551` | at.switch_page(BENCHMARK).run() | atualizada nesta rodada |
| `tests/test_compare_apptest.py:555` | # ── the Benchmark is unchanged ──────────────────────────────────────────────── | atualizada nesta rodada |
| `tests/test_compare_apptest.py:556` | def test_benchmark_pngs_are_byte_identical_to_before_the_move(tmp_path): | atualizada nesta rodada |
| `tests/test_compare_apptest.py:559` | import benchmark_tab as new | atualizada nesta rodada |
| `tests/test_compare_apptest.py:672` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_config_defaults.py:4` | `research/labels/config_defaults.py` holds the rule; the evaluator, the Benchmark | atualizada nesta rodada |
| `tests/test_config_defaults.py:12` | * evaluator and Benchmark resolve a config to the same arguments; | atualizada nesta rodada |
| `tests/test_phase_colors.py:9` | The Benchmark and Manual labelling pages still carry copies of their own | atualizada nesta rodada |
| `tests/test_phase_colors.py:10` | (benchmark_tab.PHASE_COLORS, research/labels/labels_core.PHASE_COLORS); they are | atualizada nesta rodada |
| `tests/test_phase_colors.py:62` | import benchmark_tab | atualizada nesta rodada |
| `tests/test_phase_colors.py:64` | assert benchmark_tab.PHASE_COLORS == _package_palette() | atualizada nesta rodada |
| `tests/test_sidebar_defaults.py:12` | * the published live config (what the Grid and a Benchmark sidebar column run) | atualizada nesta rodada |
| `tests/test_sidebar_defaults.py:132` | """What the Grid and a Benchmark sidebar column actually run.""" | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:17` | (northern-hemisphere) vorticity. The Benchmark Exploration upload follows the | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:132` | def _to_benchmark(at) -> AppTest: | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:133` | """Benchmark is a page of its own since the app redesign (I1); the custom | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:139` | def test_benchmark_upload_accepts_txt_and_has_help(): | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:140` | at = _to_benchmark(_app()) | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:198` | # ── the Benchmark Exploration uploader, same settings ───────────────────────── | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:199` | def test_benchmark_exploration_uses_the_same_custom_format(): | atualizada nesta rodada |
| `tests/test_track_upload_apptest.py:200` | at = _to_benchmark(_enable_custom(_app())) | atualizada nesta rodada |
| `tests/test_validate_apptest.py:11` | * The agreement numbers are the Benchmark's — the Benchmark page itself, run | atualizada nesta rodada |
| `tests/test_validate_apptest.py:14` | page — and the same scanners find them on the Benchmark page. | atualizada nesta rodada |
| `tests/test_validate_apptest.py:487` | def test_validate_numbers_equal_the_benchmark_train_table(): | atualizada nesta rodada |
| `tests/test_validate_apptest.py:494` | _go(at, BENCHMARK) | atualizada nesta rodada |
| `tests/test_validate_apptest.py:668` | def test_e2_the_scanners_find_planted_terms_on_the_benchmark_page(): | atualizada nesta rodada |
| `tests/test_validate_apptest.py:670` | at = _go(_app(), BENCHMARK) | atualizada nesta rodada |
| `tests/test_validate_core.py:6` | Controls: the instruments are checked against direct calls of the Benchmark's | atualizada nesta rodada |
| `tests/test_validate_core.py:222` | import benchmark_tab | atualizada nesta rodada |
| `tests/test_validate_core.py:223` | for colors in (li.PHASE_COLORS, benchmark_tab.PHASE_COLORS): | atualizada nesta rodada |
| `tools/calibration_app/README.md:42` | - **Benchmark** — configurations side by side (below). | atualizada nesta rodada |
| `tools/calibration_app/README.md:86` | Both upload fields (Calibrate and Benchmark → Exploration) accept `.csv` and | atualizada nesta rodada |
| `tools/calibration_app/README.md:102` | default; Benchmark's upload reuses its settings) — | atualizada nesta rodada |
| `tools/calibration_app/README.md:241` | ## Benchmark page | atualizada nesta rodada |
| `tools/calibration_app/README.md:373` | the sidebar, the Grid and Inspector display modes, the Benchmark page, the | atualizada nesta rodada |
| `tools/calibration_app/app.py:36` | import benchmark_tab  # noqa: E402 | atualizada nesta rodada |
| `tools/calibration_app/app.py:1402` | _PAGE_BENCHMARK = st.Page(_APP_PAGES_DIR / "benchmark.py", title="Benchmark", | atualizada nesta rodada |
| `tools/calibration_app/app.py:1461` | _PAGE_BENCHMARK.url_path: (benchmark_tab.WIDGET_STATE_KEYS, | atualizada nesta rodada |
| `tools/calibration_app/app.py:1462` | benchmark_tab.WIDGET_STATE_PREFIXES), | atualizada nesta rodada |
| `tools/calibration_app/app.py:1485` | _pages = {"Calibration": [_PAGE_CALIBRATE, _PAGE_COMPARE, _PAGE_BENCHMARK]} | atualizada nesta rodada |
| `tools/calibration_app/app.py:2594` | # Benchmark page can spawn a column from "the current sidebar" without | atualizada nesta rodada |
| `tools/calibration_app/app_pages/benchmark.py:1` | """Benchmark page — N configurations over the same cyclones, aligned in columns. | atualizada nesta rodada |
| `tools/calibration_app/app_pages/benchmark.py:13` | import benchmark_tab  # noqa: E402 | atualizada nesta rodada |
| `tools/calibration_app/app_pages/benchmark.py:15` | benchmark_tab.render() | atualizada nesta rodada |
| `tools/calibration_app/benchmark_core.py:1` | """Pure machinery behind the Benchmark tab — no Streamlit, no globals mutated. | atualizada nesta rodada |
| `tools/calibration_app/benchmark_tab.py` | (nome de arquivo) | atualizada nesta rodada |
| `tools/calibration_app/benchmark_tab.py:1` | """The Benchmark tab — N configurations over the same cyclones, aligned in columns. | atualizada nesta rodada |
| `tools/calibration_app/compare_core.py:17` | filling and dropping the Benchmark and the evaluator apply, and after the | atualizada nesta rodada |
| `tools/calibration_app/compare_tab.py:111` | # its own key is missing (`_restore`) — the rule the Benchmark page already | atualizada nesta rodada |
| `tools/calibration_app/package_args.py:4` | "Apply Lanczos filter" checkbox, the YAML export and import, the Benchmark's | atualizada nesta rodada |
| `tools/calibration_app/phase_figures.py:1` | """The per-cyclone phase figures of the Benchmark and Compare pages — no Streamlit. | atualizada nesta rodada |
| `tools/calibration_app/phase_figures.py:4` | page draws exactly what the Benchmark draws. The only addition is the `colors` | atualizada nesta rodada |
| `tools/calibration_app/phase_figures.py:5` | argument: the Benchmark passes its own copy of the phase palette, as before, and | atualizada nesta rodada |
| `tools/calibration_app/phase_figures.py:8` | tests/test_compare_apptest.py checks that the Benchmark's PNGs are byte-identical | atualizada nesta rodada |
| `tools/calibration_app/track_format_ui.py:3` | Shared by the Calibrate page's uploader and the Benchmark page's Exploration | atualizada nesta rodada |
| `tools/calibration_app/track_format_ui.py:25` | # Widget keys of the custom-format controls (Calibration page). The Benchmark | atualizada nesta rodada |
| `tools/calibration_app/validate_core.py:14` | the rule the Benchmark page follows, applied here to every test id whether or | atualizada nesta rodada |
| `tools/calibration_app/validate_core.py:21` | the Benchmark's own function. No test block exists: a test id never reaches | atualizada nesta rodada |
| `tools/calibration_app/validate_core.py:23` | * **The instruments.** Both are the Benchmark's, called unchanged: the sequence | atualizada nesta rodada |
| `tools/calibration_app/validate_core.py:121` | # ── cells, in the Benchmark's shape ─────────────────────────────────────────── | atualizada nesta rodada |
| `tools/calibration_app/validate_core.py:124` | Benchmark's instruments read: `runs` and the `starts` derived from them.""" | atualizada nesta rodada |
| `tools/calibration_app/validate_tab.py:15` | the Benchmark's own functions called unchanged. | atualizada nesta rodada |

### AMBÍGUA — por linha (2)

| arquivo:linha | texto | nota |
|---|---|---|
| `research/snapshots/make_published_snapshot.py:4` | This is the generator behind the Benchmark tab's reference columns. It must be run | docstring de script vivo em research/snapshots/, fora da lista do briefing (que cita só os dois README) |
| `tools/calibration_app/benchmark_core.py:552` | path `tests/test_benchmark_apptest.py` drives for its positive control. | docstring de função de benchmark_core; o briefing restringe a mudança à docstring do MÓDULO |

### CORRETA — por linha (81)

| arquivo:linha | texto | nota |
|---|---|---|
| `research/labels/README.md:119` | `MARGIN`, which the Benchmark imports, are unchanged. `load_config()` without a | decisão do Danilo (checkpoint do I3): fica como está — registro do item 31 |
| `research/labels/config_defaults.py:18` | benchmark_core.split_config` / `signature_audit`, and the app's YAML import. |  |
| `research/labels/labels_core.py:54` | # `load_real_series`, the benchmark, make_split, the tests, the Grid loader. |  |
| `research/labels/labels_core.py:267` | the 47/16 split, and every existing reader of them (benchmark, evaluator, |  |
| `tests/test_app_navigation_apptest.py:43` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_app_navigation_apptest.py:46` | BENCHMARK = "app_pages/benchmark.py" |  |
| `tests/test_app_passo5_fixes.py:4` | above the tabs, they also showed in the Benchmark tab with a caption that is |  |
| `tests/test_app_passo5_fixes.py:73` | at.switch_page("app_pages/benchmark.py").run() |  |
| `tests/test_benchmark_apptest.py:47` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_benchmark_apptest.py:69` | BENCHMARK_PAGE = "app_pages/benchmark.py" |  |
| `tests/test_benchmark_apptest.py:369` | """Detector output for one config, computed straight from benchmark_core.""" |  |
| `tests/test_calibrate_i2_apptest.py:234` | at.switch_page("app_pages/benchmark.py") |  |
| `tests/test_calibrate_i3_apptest.py:182` | at.switch_page("app_pages/benchmark.py") |  |
| `tests/test_calibrate_i3_apptest.py:202` | at.switch_page("app_pages/benchmark.py") |  |
| `tests/test_calibrate_i3_apptest.py:219` | at.switch_page("app_pages/benchmark.py") |  |
| `tests/test_compare_apptest.py:1` | """The Compare page (benchmark review, I1) — AppTest, public API only. |  |
| `tests/test_compare_apptest.py:40` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_compare_apptest.py:45` | BENCHMARK = "app_pages/benchmark.py" |  |
| `tests/test_compare_apptest.py:562` | ["git", "show", "39e658c:tools/calibration_app/benchmark_tab.py"], |  |
| `tests/test_compare_apptest.py:566` | (tmp_path / "old_benchmark_tab.py").write_text(old_src) |  |
| `tests/test_compare_apptest.py:567` | spec = importlib.util.spec_from_file_location("old_benchmark_tab", |  |
| `tests/test_compare_apptest.py:568` | tmp_path / "old_benchmark_tab.py") |  |
| `tests/test_compare_browser.py:1` | """The Compare page in a real browser (benchmark review, I1) — criterion (e1). |  |
| `tests/test_compare_browser.py:3` | Usability tasks of research/benchmark_review/stage0/DECISIONS.md, run from |  |
| `tests/test_compare_core.py:1` | """compare_core — the label-free logic behind the Compare page (benchmark review, I1). |  |
| `tests/test_config_defaults.py:5` | (`benchmark_core`) and the app's YAML import all go through it. What is pinned: |  |
| `tests/test_config_defaults.py:112` | def test_evaluator_and_benchmark_resolve_a_config_identically(capsys): |  |
| `tests/test_config_defaults.py:113` | import benchmark_core as bc |  |
| `tests/test_sidebar_defaults.py:37` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_sidebar_defaults.py:177` | at.switch_page("app_pages/benchmark.py").run()   # a page of its own since I1 |  |
| `tests/test_swell_batch.py:117` | def test_validation_is_not_in_the_benchmark_even_with_the_batch_on(): |  |
| `tests/test_swell_batch.py:119` | import benchmark_core as bc |  |
| `tests/test_track_upload_apptest.py:135` | at.switch_page("app_pages/benchmark.py") |  |
| `tests/test_validate_apptest.py:1` | """The Validate page (benchmark review, I2) — AppTest, public API only. |  |
| `tests/test_validate_apptest.py:39` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_validate_apptest.py:48` | BENCHMARK = "app_pages/benchmark.py" |  |
| `tests/test_validate_browser.py:1` | """The Validate page in a real browser (benchmark review, I2) — criterion (e1). |  |
| `tests/test_validate_core.py:1` | """validate_core — the label-side logic behind the Validate page (benchmark review, I2). |  |
| `tests/test_validate_core.py:28` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_validate_core.py:134` | def test_agreement_uses_the_two_benchmark_instruments_unchanged(): |  |
| `tools/calibration_app/README.md:299` | `benchmark_core.scoreable`. A row with no label yields no scoring number in |  |
| `tools/calibration_app/app.py:729` | import config_defaults   # research/labels — on sys.path via benchmark_core |  |
| `tools/calibration_app/app.py:1894` | # disagree on what "the loaded tracks" are (benchmark review, A6). |  |
| `tools/calibration_app/app_pages/benchmark.py` | (nome de arquivo) |  |
| `tools/calibration_app/app_pages/benchmark.py:3` | All of it lives in benchmark_tab.py (the Streamlit surface) and benchmark_core.py |  |
| `tools/calibration_app/benchmark_core.py` | (nome de arquivo) |  |
| `tools/calibration_app/benchmark_core.py:222` | """One benchmark column: a configuration plus where it came from.""" |  |
| `tools/calibration_app/benchmark_core.py:592` | compared against itself does not return all zeros (benchmark review, A2): |  |
| `tools/calibration_app/benchmark_tab.py:3` | All logic lives in `benchmark_core`; this file is the Streamlit surface over it. |  |
| `tools/calibration_app/benchmark_tab.py:20` | the existence of a manual label for that cyclone, in `benchmark_core.scoreable`. |  |
| `tools/calibration_app/benchmark_tab.py:62` | import benchmark_core as bc  # noqa: E402 |  |
| `tools/calibration_app/benchmark_tab.py:168` | # The drawing code lives in phase_figures.py since the benchmark review (I1), so |  |
| `tools/calibration_app/compare_core.py:6` | parts of `benchmark_core` (`split_config`, `signature_audit`, `run_series`, |  |
| `tools/calibration_app/compare_core.py:23` | smoothing window from the length of that index (benchmark review, A11). |  |
| `tools/calibration_app/compare_core.py:38` | import benchmark_core as bc  # noqa: E402 |  |
| `tools/calibration_app/compare_core.py:40` | from config_defaults import fill_missing  # noqa: E402  (research/labels, via benchmark_core) |  |
| `tools/calibration_app/compare_core.py:86` | `benchmark_core.split_config` (fill the absent keys, drop the ones the |  |
| `tools/calibration_app/compare_core.py:117` | `ignored` is `benchmark_core.signature_audit`'s (keys the current package |  |
| `tools/calibration_app/compare_core.py:185` | `benchmark_core.reference_metrics`, without its fourth measure, which is a |  |
| `tools/calibration_app/compare_core.py:186` | count of the column's own and not a distance (benchmark review, A2; see |  |
| `tools/calibration_app/compare_tab.py:4` | configuration changes? It is the public half of the old Benchmark page (benchmark |  |
| `tools/calibration_app/compare_tab.py:6` | research/benchmark_review/stage0/DECISIONS.md). The logic is in compare_core.py; |  |
| `tools/calibration_app/compare_tab.py:33` | after one change recomputes only the cells that changed. (The old Benchmark's |  |
| `tools/calibration_app/compare_tab.py:632` | # Always an element in this slot (benchmark review I2, F2): with |  |
| `tools/calibration_app/config_text.py:7` | (benchmark review, I2) shows the same cards, so it calls them too, and the |  |
| `tools/calibration_app/config_text.py:53` | import benchmark_core as bc               # sibling module; lazy, keeps this light |  |
| `tools/calibration_app/label_overlays.py:58` | the same document the Benchmark's "Add column from current sidebar state" |  |
| `tools/calibration_app/phase_figures.py:3` | Moved out of benchmark_tab.py unchanged (benchmark review, I1) so the Compare |  |
| `tools/calibration_app/track_format_ui.py:62` | "on. The Benchmark page's Exploration upload uses these same settings." |  |
| `tools/calibration_app/validate_core.py:3` | The Validate page (benchmark review, I2; developer key only) measures how |  |
| `tools/calibration_app/validate_core.py:20` | with by construction) are kept apart by `benchmark_core.metrics_by_split`, |  |
| `tools/calibration_app/validate_core.py:24` | instrument (`benchmark_core.SEQUENCE_INSTRUMENT`) and the mature instrument |  |
| `tools/calibration_app/validate_core.py:25` | (`benchmark_core.MATURE_INSTRUMENT`). They have different definitions and are |  |
| `tools/calibration_app/validate_core.py:39` | import benchmark_core as bc  # noqa: E402 |  |
| `tools/calibration_app/validate_core.py:40` | import labels_core as lc  # noqa: E402  (research/labels, via benchmark_core) |  |
| `tools/calibration_app/validate_core.py:139` | `benchmark_core.metrics_by_split`, with every id given membership "train": |  |
| `tools/calibration_app/validate_core.py:161` | """A published release's cell, read from its file (`benchmark_core.snapshot_series`). |  |
| `tools/calibration_app/validate_tab.py:4` | Benchmark page (benchmark review, I2; the decisions and the control-by-control |  |
| `tools/calibration_app/validate_tab.py:5` | inventory are in research/benchmark_review/stage0/DECISIONS.md). It answers: how |  |
| `tools/calibration_app/validate_tab.py:22` | The reference is chosen among the COLUMNS only. The old Benchmark also offered |  |
| `tools/calibration_app/validate_tab.py:48` | import benchmark_core as bc  # noqa: E402 |  |

## Depois (árvore de trabalho) — varredura final

| classe | ocorrências |
|---|---|
| HISTÓRICA | 1051 |
| CORRETA | 123 |
| AMBÍGUA | 0 |
| VIVA | 0 |

### HISTÓRICA — por arquivo (262 arquivos, não tocados)

| arquivo | linhas/nome |
|---|---|
| `CHANGELOG.md` | 11 |
| `docs/findings.md` | 5 |
| `docs/future_work.md` | 34 |
| `research/app_redesign/close/RELATORIO.md` | 1 |
| `research/app_redesign/i1/INVENTARIO.md` | 8 |
| `research/app_redesign/i1/PREVISOES.md` | 3 |
| `research/app_redesign/i1/RELATORIO.md` | 19 |
| `research/app_redesign/i1/capture_screenshots.py` | 8 |
| `research/app_redesign/i1/captures/after/benchmark.png` | 1 |
| `research/app_redesign/i1/captures/after/manifest.json` | 1 |
| `research/app_redesign/i1/captures/after_extras/manifest.json` | 1 |
| `research/app_redesign/i1/captures/before/benchmark.png` | 1 |
| `research/app_redesign/i1/captures/before/manifest.json` | 1 |
| `research/app_redesign/i1/inventory_check.txt` | 5 |
| `research/app_redesign/i1/measure_after.json` | 3 |
| `research/app_redesign/i1/measure_before.json` | 3 |
| `research/app_redesign/i1/measure_interactions.py` | 7 |
| `research/app_redesign/i2/INVENTARIO.md` | 4 |
| `research/app_redesign/i2/RELATORIO.md` | 3 |
| `research/app_redesign/i2/badmark_after.txt` | 2 |
| `research/app_redesign/i2/check_badmark.py` | 3 |
| `research/app_redesign/i3/INVENTARIO.md` | 2 |
| `research/app_redesign/i3/RELATORIO.md` | 6 |
| `research/app_redesign/i3/diag/after2_cpu4_conda_st1.63.0.jsonl` | 9 |
| `research/app_redesign/i3/diag/after2_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after2_cpu4_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after2_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after2_normal_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after2_normal_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after2_normal_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after2_normal_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_cpu4_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_cpu4_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_normal_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_normal_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/after3_normal_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/after3_normal_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/before2_cpu4_conda_st1.63.0.jsonl` | 15 |
| `research/app_redesign/i3/diag/before2_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/before2_cpu4_st1.56.0.jsonl` | 20 |
| `research/app_redesign/i3/diag/before2_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/control_injected_error_conda.jsonl` | 1 |
| `research/app_redesign/i3/diag/control_injected_error_conda_summary.txt` | 1 |
| `research/app_redesign/i3/diag/control_tolerated_media404_conda.jsonl` | 3 |
| `research/app_redesign/i3/diag/control_tolerated_media404_conda_summary.txt` | 1 |
| `research/app_redesign/i3/diag/exec_cpu4_conda_st1.63.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/exec_cpu4_conda_st1.63.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag/exec_cpu4_st1.56.0.jsonl` | 10 |
| `research/app_redesign/i3/diag/exec_cpu4_st1.56.0_summary.txt` | 1 |
| `research/app_redesign/i3/diag_paged_grid_plugin.py` | 1 |
| `research/benchmark_review/i1/PREVISOES.md` | 13 |
| `research/benchmark_review/i1/PREVISOES_r2.md` | 5 |
| `research/benchmark_review/i1/RELATORIO.md` | 36 |
| `research/benchmark_review/i1/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/capture_screenshots.py` | 2 |
| `research/benchmark_review/i1/captures/01_empty.png` | 1 |
| `research/benchmark_review/i1/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i1/captures/03_columns.png` | 1 |
| `research/benchmark_review/i1/captures/04_results.png` | 1 |
| `research/benchmark_review/i1/captures/05_side_by_side.png` | 1 |
| `research/benchmark_review/i1/captures/06_stacked.png` | 1 |
| `research/benchmark_review/i1/captures/07_filter.png` | 1 |
| `research/benchmark_review/i1/captures/08_reference.png` | 1 |
| `research/benchmark_review/i1/captures/09_filled_warning.png` | 1 |
| `research/benchmark_review/i1/captures/10_limit.png` | 1 |
| `research/benchmark_review/i1/captures/11_invert_help.png` | 1 |
| `research/benchmark_review/i1/captures/full_page.png` | 1 |
| `research/benchmark_review/i1/captures/manifest.json` | 1 |
| `research/benchmark_review/i1/check_inventory.py` | 14 |
| `research/benchmark_review/i1/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i1/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i1/inventory_check.txt` | 3 |
| `research/benchmark_review/i1/measure_run.json` | 5 |
| `research/benchmark_review/i1/measure_run.py` | 11 |
| `research/benchmark_review/i1/r1/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/r1/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/r1/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/r1/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/r1/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i1/r1/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i1/r1/inventory_check.txt` | 3 |
| `research/benchmark_review/i1/r1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/r1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i1/run_browser.sh` | 3 |
| `research/benchmark_review/i1/run_repeat_browser.sh` | 3 |
| `research/benchmark_review/i1/run_suite.sh` | 4 |
| `research/benchmark_review/i1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/PREVISOES.md` | 10 |
| `research/benchmark_review/i2/PREVISOES_r2.md` | 2 |
| `research/benchmark_review/i2/RELATORIO.md` | 19 |
| `research/benchmark_review/i2/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/capture_screenshots.py` | 2 |
| `research/benchmark_review/i2/captures/01_arrival.png` | 1 |
| `research/benchmark_review/i2/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i2/captures/03_cards.png` | 1 |
| `research/benchmark_review/i2/captures/04_provenance.png` | 1 |
| `research/benchmark_review/i2/captures/05_train_block.png` | 1 |
| `research/benchmark_review/i2/captures/06_disagreements.png` | 1 |
| `research/benchmark_review/i2/captures/07_side_by_side.png` | 1 |
| `research/benchmark_review/i2/captures/08_stacked.png` | 1 |
| `research/benchmark_review/i2/captures/09_filter.png` | 1 |
| `research/benchmark_review/i2/captures/10_adjudicated.png` | 1 |
| `research/benchmark_review/i2/captures/11_limit.png` | 1 |
| `research/benchmark_review/i2/captures/12_validate_filled_warning.png` | 1 |
| `research/benchmark_review/i2/captures/13_compare_filled_warning.png` | 1 |
| `research/benchmark_review/i2/captures/14_disagreement_headers.png` | 1 |
| `research/benchmark_review/i2/captures/15_snapshot_note.png` | 1 |
| `research/benchmark_review/i2/captures/16_validate_results_current.png` | 1 |
| `research/benchmark_review/i2/captures/17_compare_results_current.png` | 1 |
| `research/benchmark_review/i2/captures/18_validate_warning_dark.png` | 1 |
| `research/benchmark_review/i2/captures/19_compare_warning_dark.png` | 1 |
| `research/benchmark_review/i2/captures/full_page.png` | 1 |
| `research/benchmark_review/i2/captures/manifest.json` | 1 |
| `research/benchmark_review/i2/check_inventory.py` | 11 |
| `research/benchmark_review/i2/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i2/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i2/inventory_check.txt` | 3 |
| `research/benchmark_review/i2/measure_run.json` | 2 |
| `research/benchmark_review/i2/measure_run.py` | 4 |
| `research/benchmark_review/i2/r1/captures/01_arrival.png` | 1 |
| `research/benchmark_review/i2/r1/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i2/r1/captures/03_cards.png` | 1 |
| `research/benchmark_review/i2/r1/captures/04_provenance.png` | 1 |
| `research/benchmark_review/i2/r1/captures/05_train_block.png` | 1 |
| `research/benchmark_review/i2/r1/captures/06_disagreements.png` | 1 |
| `research/benchmark_review/i2/r1/captures/07_side_by_side.png` | 1 |
| `research/benchmark_review/i2/r1/captures/08_stacked.png` | 1 |
| `research/benchmark_review/i2/r1/captures/09_filter.png` | 1 |
| `research/benchmark_review/i2/r1/captures/10_adjudicated.png` | 1 |
| `research/benchmark_review/i2/r1/captures/11_limit.png` | 1 |
| `research/benchmark_review/i2/r1/captures/12_validate_filled_warning.png` | 1 |
| `research/benchmark_review/i2/r1/captures/13_compare_filled_warning.png` | 1 |
| `research/benchmark_review/i2/r1/captures/full_page.png` | 1 |
| `research/benchmark_review/i2/r1/captures/manifest.json` | 1 |
| `research/benchmark_review/i2/r1/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i2/r1/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i2/r1/inventory_check.txt` | 3 |
| `research/benchmark_review/i2/r1/measure_run.json` | 2 |
| `research/benchmark_review/i2/r1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/r1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/r2/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/r2/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/01_arrival.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/02_run_blocked.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/03_cards.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/04_provenance.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/05_train_block.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/06_disagreements.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/07_side_by_side.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/08_stacked.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/09_filter.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/10_adjudicated.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/11_limit.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/12_validate_filled_warning.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/13_compare_filled_warning.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/full_page.png` | 1 |
| `research/benchmark_review/i2/rodada1_final/captures/manifest.json` | 1 |
| `research/benchmark_review/i2/rodada1_final/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i2/rodada1_final/inventory_check.txt` | 3 |
| `research/benchmark_review/i2/rodada1_final/measure_run.json` | 2 |
| `research/benchmark_review/i2/rodada1_final/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/rodada1_final/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i2/run_browser.sh` | 3 |
| `research/benchmark_review/i2/run_repeat_browser.sh` | 3 |
| `research/benchmark_review/i2/run_suite.sh` | 4 |
| `research/benchmark_review/i2/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i2/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i3/PREVISOES.md` | 12 |
| `research/benchmark_review/i3/REFERENCIAS.md` | 1 |
| `research/benchmark_review/i3/RELATORIO.md` | 22 |
| `research/benchmark_review/i3/TESTES.md` | 32 |
| `research/benchmark_review/i3/browser_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i3/browser_repeat_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i3/browser_repeat_st1.56.0.txt` | 1 |
| `research/benchmark_review/i3/browser_st1.56.0.txt` | 1 |
| `research/benchmark_review/i3/build_docs_clean.sh` | 3 |
| `research/benchmark_review/i3/capture_screenshots.py` | 9 |
| `research/benchmark_review/i3/captures/01_public_menu.png` | 1 |
| `research/benchmark_review/i3/captures/02_public_benchmark_address.png` | 1 |
| `research/benchmark_review/i3/captures/03_public_after_notice.png` | 1 |
| `research/benchmark_review/i3/captures/04_developer_menu.png` | 1 |
| `research/benchmark_review/i3/captures/05_developer_benchmark_address.png` | 1 |
| `research/benchmark_review/i3/captures/06_f5_headers.png` | 1 |
| `research/benchmark_review/i3/captures/07_f5_header_open.png` | 1 |
| `research/benchmark_review/i3/captures/manifest.json` | 10 |
| `research/benchmark_review/i3/check_inventory.py` | 7 |
| `research/benchmark_review/i3/ci_recipe_raw.txt` | 1 |
| `research/benchmark_review/i3/ci_recipe_summary.json` | 1 |
| `research/benchmark_review/i3/docs_build_i3_review.txt` | 1 |
| `research/benchmark_review/i3/docs_build_i3_review_warnings.txt` | 1 |
| `research/benchmark_review/i3/inventory_check.txt` | 1 |
| `research/benchmark_review/i3/r1/inventory_check.txt` | 1 |
| `research/benchmark_review/i3/r1/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i3/r1/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i3/run_browser.sh` | 3 |
| `research/benchmark_review/i3/run_repeat_browser.sh` | 4 |
| `research/benchmark_review/i3/run_suite.sh` | 4 |
| `research/benchmark_review/i3/suite_conda_st1.63.0.txt` | 1 |
| `research/benchmark_review/i3/suite_st1.56.0.txt` | 1 |
| `research/benchmark_review/i3/sweep_references.py` | 30 |
| `research/benchmark_review/stage0/DECISIONS.md` | 19 |
| `research/cleanup/MANIFEST.md` | 49 |
| `research/cleanup/final/b_app_tests.txt` | 1 |
| `research/cleanup/final/f_post_6b.json` | 2 |
| `research/cleanup/final/streamlit_guards_after.json` | 2 |
| `research/cleanup/final/streamlit_guards_before.json` | 2 |
| `research/cleanup/passo0/branches.json` | 1 |
| `research/cleanup/passo0/defaults_in_text.json` | 1 |
| `research/cleanup/passo0/defaults_in_text.md` | 1 |
| `research/cleanup/passo0/inventory.json` | 45 |
| `research/cleanup/passo0/judgements.py` | 8 |
| `research/cleanup/passo0/make_manifest.py` | 6 |
| `research/cleanup/passo0/manifest_summary.json` | 3 |
| `research/cleanup/passo1/commit4_ast_check.txt` | 2 |
| `research/cleanup/passo1/params15_refs.json` | 1 |
| `research/cleanup/passo2/findings_src.md` | 2 |
| `research/cleanup/passo2/make_findings.py` | 1 |
| `research/cleanup/passo2/traceability.json` | 5 |
| `research/cleanup/passo3/removed_files.txt` | 5 |
| `research/cleanup/passo4/fix_stale_200_texts.py` | 4 |
| `research/cleanup/passo4/fix_stale_200_texts_log.json` | 4 |
| `research/cleanup/passo4/rtd_map.md` | 1 |
| `research/cleanup/passo5/PREVISOES.md` | 2 |
| `research/cleanup/passo5/RELATORIO.md` | 2 |
| `research/cleanup/passo5/app_tests.txt` | 1 |
| `research/cleanup/passo5/b_test_ids_after.json` | 1 |
| `research/cleanup/passo5/b_test_ids_before.json` | 1 |
| `research/cleanup/passo5/e2_benchmark_pinned_before.txt` | 121 |
| `research/cleanup/passo5/e2_probe_multiselect.py` | 1 |
| `research/cleanup/passo5/e2_probe_pinned.txt` | 1 |
| `research/cleanup/passo5/make_report.py` | 6 |
| `research/cleanup/passo6/branches.json` | 2 |
| `research/cleanup/passo6/branches.md` | 2 |
| `research/cleanup/passo6/delete_6b.json` | 2 |
| `research/cleanup/passo6/delete_6b_check.json` | 1 |
| `research/cleanup/passo6/future_work_item32.md` | 2 |
| `research/cleanup/passo6/future_work_item32.py` | 3 |
| `research/cleanup/passo6/post_6b.json` | 2 |
| `research/cleanup/passo6/removal_list.md` | 1 |
| `research/labels/split.yaml` | 1 |
| `research/labels/swell_item30/README.md` | 1 |
| `research/labels/swell_item30/freeze_validation_batch.py` | 1 |
| `research/release_v21/parteB_passo1/06_sdist_files.txt` | 1 |
| `research/release_v21/parteB_passo1/08_app.md` | 5 |
| `research/release_v21/parteB_passo1/09_changelog.md` | 1 |
| `research/release_v21/parteB_passo2/07_ci_steps_summary.json` | 2 |
| `research/release_v21/parteB_passo2/RELATORIO.md` | 1 |
| `research/release_v21/parteB_passo2/changelog.diff` | 2 |

### VIVA — por linha (0)

nenhuma

### AMBÍGUA — por linha (0)

nenhuma

### CORRETA — por linha (123)

| arquivo:linha | texto | nota |
|---|---|---|
| `CHANGELOG.md:35` | * The **Benchmark** page. Its public part is the Compare page, its developer | [Unreleased]: a entrada que registra a remoção |
| `CHANGELOG.md:42` | again after one change recomputes only what changed. The Benchmark's caption | [Unreleased]: a entrada que registra a remoção |
| `CHANGELOG.md:45` | Benchmark showed for any uploaded YAML without `boundary_padding`, whatever | [Unreleased]: a entrada que registra a remoção |
| `CHANGELOG.md:50` | the Benchmark lost its time axis, and with smoothing set to 'auto' a track | [Unreleased]: a entrada que registra a remoção |
| `research/labels/README.md:119` | `MARGIN`, which the Benchmark imports, are unchanged. `load_config()` without a | decisão do Danilo (checkpoint do I3): fica como está — registro do item 31 |
| `research/labels/config_defaults.py:18` | benchmark_core.split_config` / `signature_audit`, and the app's YAML import. |  |
| `research/labels/labels_core.py:54` | # `load_real_series`, the benchmark, make_split, the tests, the Grid loader. |  |
| `research/labels/labels_core.py:267` | the 47/16 split, and every existing reader of them (benchmark, evaluator, |  |
| `tests/test_app_navigation_apptest.py:15` | * the old Benchmark page is gone (benchmark review, I3): its files are deleted, |  |
| `tests/test_app_navigation_apptest.py:50` | OLD_BENCHMARK = "app_pages/benchmark.py"   # retired in I3; the file is gone |  |
| `tests/test_app_navigation_apptest.py:115` | def test_the_benchmark_page_is_gone(monkeypatch): |  |
| `tests/test_app_navigation_apptest.py:116` | """Benchmark review, I3: the page and its module are deleted, app.py names |  |
| `tests/test_app_navigation_apptest.py:120` | assert not (app_dir / OLD_BENCHMARK).exists() |  |
| `tests/test_app_navigation_apptest.py:121` | assert not (app_dir / "benchmark_tab.py").exists() |  |
| `tests/test_app_navigation_apptest.py:122` | assert (app_dir / "benchmark_core.py").exists()          # the module stays |  |
| `tests/test_app_navigation_apptest.py:124` | assert "benchmark_tab" not in src and "_PAGE_BENCHMARK" not in src |  |
| `tests/test_app_navigation_apptest.py:133` | assert _rendered(at, OLD_BENCHMARK) == "calibrate" |  |
| `tests/test_app_navigation_apptest.py:257` | """Compare's "Add Current settings" (the Benchmark's "Add column from |  |
| `tests/test_app_pages_browser.py:6` | absent without the key; the old Benchmark page in no menu, and its address |  |
| `tests/test_app_pages_browser.py:7` | (`/benchmark`) opening the default page (benchmark review, I3); |  |
| `tests/test_app_pages_browser.py:12` | imported YAML must survive a trip to Compare and back (to Benchmark until I3). |  |
| `tests/test_app_pages_browser.py:126` | "Benchmark"): |  |
| `tests/test_app_pages_browser.py:141` | assert "Benchmark" not in nav, nav |  |
| `tests/test_app_pages_browser.py:146` | def test_the_old_benchmark_address_opens_the_default_page(public_server, dev_server, pw): |  |
| `tests/test_app_pages_browser.py:147` | """Benchmark review, I3: no provisional page. `/benchmark` falls to what |  |
| `tests/test_app_pages_browser.py:157` | page.goto(server.url.rstrip("/") + "/benchmark") |  |
| `tests/test_app_pages_browser.py:163` | assert "Calibrate" in nav and "Benchmark" not in nav, nav |  |
| `tests/test_app_pages_browser.py:166` | print(f"/benchmark ({'developer' if server is dev_server else 'public'}): " |  |
| `tests/test_app_pages_browser.py:510` | Inspector and the Compare page (the Benchmark page until I3), the browser |  |
| `tests/test_app_passo5_fixes.py:4` | above the tabs, they also showed in the Benchmark tab with a caption that is |  |
| `tests/test_app_passo5_fixes.py:7` | Benchmark page was retired in the benchmark review, I3). |  |
| `tests/test_app_passo5_fixes.py:8` | * (Until I3: the Benchmark preset buttons. Their defect — a selection kept apart |  |
| `tests/test_compare_apptest.py:1` | """The Compare page (benchmark review, I1) — AppTest, public API only. |  |
| `tests/test_compare_apptest.py:21` | Since the Benchmark page was retired (benchmark review, I3), the column |  |
| `tests/test_compare_apptest.py:47` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_compare_apptest.py:569` | # ── the figures are the old Benchmark's ─────────────────────────────────────── |  |
| `tests/test_compare_apptest.py:570` | def test_compare_pngs_are_byte_identical_to_the_benchmark_of_39e658c(tmp_path): |  |
| `tests/test_compare_apptest.py:572` | Benchmark page's own drawing code as it was at 39e658c (read with git show; |  |
| `tests/test_compare_apptest.py:580` | ["git", "show", "39e658c:tools/calibration_app/benchmark_tab.py"], |  |
| `tests/test_compare_apptest.py:584` | (tmp_path / "old_benchmark_tab.py").write_text(old_src) |  |
| `tests/test_compare_apptest.py:585` | spec = importlib.util.spec_from_file_location("old_benchmark_tab", |  |
| `tests/test_compare_apptest.py:586` | tmp_path / "old_benchmark_tab.py") |  |
| `tests/test_compare_apptest.py:687` | """(Until I3 this also checked that the Benchmark kept its own "Invert"; |  |
| `tests/test_compare_apptest.py:712` | # ── column guarantees, migrated from the retired Benchmark page (I3) ────────── |  |
| `tests/test_compare_apptest.py:719` | """{id: (runs, z)} computed straight from benchmark_core, outside the app: |  |
| `tests/test_compare_browser.py:1` | """The Compare page in a real browser (benchmark review, I1) — criterion (e1). |  |
| `tests/test_compare_browser.py:3` | Usability tasks of research/benchmark_review/stage0/DECISIONS.md, run from |  |
| `tests/test_compare_core.py:1` | """compare_core — the label-free logic behind the Compare page (benchmark review, I1). |  |
| `tests/test_config_defaults.py:5` | `benchmark_core` (the app's Compare and Validate pages) and the app's YAML |  |
| `tests/test_config_defaults.py:13` | * evaluator and `benchmark_core` resolve a config to the same arguments; |  |
| `tests/test_config_defaults.py:113` | def test_evaluator_and_benchmark_resolve_a_config_identically(capsys): |  |
| `tests/test_config_defaults.py:114` | import benchmark_core as bc |  |
| `tests/test_phase_colors.py:12` | Benchmark page's copy, benchmark_tab.PHASE_COLORS, left with that page in the |  |
| `tests/test_phase_colors.py:13` | benchmark review, I3.) |  |
| `tests/test_phase_figures.py:4` | `phase_figures.cell_figure` / `stacked_figure`. These pins were the Benchmark |  |
| `tests/test_phase_figures.py:5` | page's (tests/test_benchmark_apptest.py, retired with that page in the benchmark |  |
| `tests/test_phase_figures.py:31` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_sidebar_defaults.py:20` | the swell batch since the Benchmark page was retired (benchmark review, I3). |  |
| `tests/test_sidebar_defaults.py:39` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_swell_batch.py:117` | def test_validation_is_not_in_the_benchmark_even_with_the_batch_on(): |  |
| `tests/test_swell_batch.py:119` | import benchmark_core as bc |  |
| `tests/test_track_upload_apptest.py:17` | (northern-hemisphere) vorticity. (The Benchmark page's Exploration upload |  |
| `tests/test_track_upload_apptest.py:18` | followed the same settings until that page was retired, benchmark review I3; |  |
| `tests/test_validate_apptest.py:1` | """The Validate page (benchmark review, I2) — AppTest, public API only. |  |
| `tests/test_validate_apptest.py:11` | * The agreement numbers are benchmark_core's — computed outside the app the |  |
| `tests/test_validate_apptest.py:12` | way the retired Benchmark page computed them (`run_series`, |  |
| `tests/test_validate_apptest.py:44` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_validate_apptest.py:497` | def test_validate_numbers_equal_benchmark_core_on_the_train_split(): |  |
| `tests/test_validate_apptest.py:498` | """Until I3 the reference was the Benchmark page's train table; that page is |  |
| `tests/test_validate_apptest.py:500` | `benchmark_core.split_config` + `run_series` on the 47 train series, then |  |
| `tests/test_validate_apptest.py:688` | (until I3 also on the Benchmark page's "hit rate", retired with it).""" |  |
| `tests/test_validate_apptest.py:860` | # ── migrated from the retired Benchmark page's tests (I3) ───────────────────── |  |
| `tests/test_validate_browser.py:1` | """The Validate page in a real browser (benchmark review, I2) — criterion (e1). |  |
| `tests/test_validate_core.py:1` | """validate_core — the label-side logic behind the Validate page (benchmark review, I2). |  |
| `tests/test_validate_core.py:6` | Controls: the instruments are checked against direct calls of benchmark_core's |  |
| `tests/test_validate_core.py:11` | Since the Benchmark page was retired (benchmark review, I3) the label-side |  |
| `tests/test_validate_core.py:33` | import benchmark_core as bc  # noqa: E402 |  |
| `tests/test_validate_core.py:139` | def test_agreement_uses_the_two_benchmark_instruments_unchanged(): |  |
| `tests/test_validate_core.py:227` | # the palette both pages pass (benchmark_tab's own copy left with it in I3; |  |
| `tests/test_validate_core.py:283` | # ── migrated from the retired Benchmark page's tests (benchmark review, I3) ──── |  |
| `tools/calibration_app/app.py:728` | import config_defaults   # research/labels — on sys.path via benchmark_core |  |
| `tools/calibration_app/app.py:1889` | # disagree on what "the loaded tracks" are (benchmark review, A6). |  |
| `tools/calibration_app/benchmark_core.py` | (nome de arquivo) |  |
| `tools/calibration_app/benchmark_core.py:5` | The Benchmark page this module was written for was retired (benchmark review, |  |
| `tools/calibration_app/benchmark_core.py:240` | """One benchmark column: a configuration plus where it came from.""" |  |
| `tools/calibration_app/benchmark_core.py:611` | compared against itself does not return all zeros (benchmark review, A2): |  |
| `tools/calibration_app/compare_core.py:6` | parts of `benchmark_core` (`split_config`, `signature_audit`, `run_series`, |  |
| `tools/calibration_app/compare_core.py:17` | filling and dropping benchmark_core and the evaluator apply, and after the |  |
| `tools/calibration_app/compare_core.py:23` | smoothing window from the length of that index (benchmark review, A11). |  |
| `tools/calibration_app/compare_core.py:38` | import benchmark_core as bc  # noqa: E402 |  |
| `tools/calibration_app/compare_core.py:40` | from config_defaults import fill_missing  # noqa: E402  (research/labels, via benchmark_core) |  |
| `tools/calibration_app/compare_core.py:86` | `benchmark_core.split_config` (fill the absent keys, drop the ones the |  |
| `tools/calibration_app/compare_core.py:117` | `ignored` is `benchmark_core.signature_audit`'s (keys the current package |  |
| `tools/calibration_app/compare_core.py:185` | `benchmark_core.reference_metrics`, without its fourth measure, which is a |  |
| `tools/calibration_app/compare_core.py:186` | count of the column's own and not a distance (benchmark review, A2; see |  |
| `tools/calibration_app/compare_tab.py:4` | configuration changes? It is the public half of the old Benchmark page (benchmark |  |
| `tools/calibration_app/compare_tab.py:6` | research/benchmark_review/stage0/DECISIONS.md). The logic is in compare_core.py; |  |
| `tools/calibration_app/compare_tab.py:33` | after one change recomputes only the cells that changed. (The old Benchmark's |  |
| `tools/calibration_app/compare_tab.py:111` | # its own key is missing (`_restore`) — the rule the old Benchmark page |  |
| `tools/calibration_app/compare_tab.py:632` | # Always an element in this slot (benchmark review I2, F2): with |  |
| `tools/calibration_app/config_text.py:7` | (benchmark review, I2) shows the same cards, so it calls them too, and the |  |
| `tools/calibration_app/config_text.py:53` | import benchmark_core as bc               # sibling module; lazy, keeps this light |  |
| `tools/calibration_app/phase_figures.py:3` | Moved out of the old Benchmark page's benchmark_tab.py unchanged (benchmark |  |
| `tools/calibration_app/phase_figures.py:5` | the Benchmark drew. The `colors` argument was the only addition: both pages pass |  |
| `tools/calibration_app/phase_figures.py:8` | PNGs are byte-identical to the ones benchmark_tab.py produced at 39e658c. The |  |
| `tools/calibration_app/track_format_ui.py:3` | Used by the Calibrate page's uploader (the old Benchmark page's Exploration |  |
| `tools/calibration_app/validate_core.py:3` | The Validate page (benchmark review, I2; developer key only) measures how |  |
| `tools/calibration_app/validate_core.py:14` | the rule the retired Benchmark page followed, applied here to every test id |  |
| `tools/calibration_app/validate_core.py:20` | with by construction) are kept apart by `benchmark_core.metrics_by_split`, |  |
| `tools/calibration_app/validate_core.py:23` | * **The instruments.** Both are benchmark_core's, called unchanged: the sequence |  |
| `tools/calibration_app/validate_core.py:24` | instrument (`benchmark_core.SEQUENCE_INSTRUMENT`) and the mature instrument |  |
| `tools/calibration_app/validate_core.py:25` | (`benchmark_core.MATURE_INSTRUMENT`). They have different definitions and are |  |
| `tools/calibration_app/validate_core.py:39` | import benchmark_core as bc  # noqa: E402 |  |
| `tools/calibration_app/validate_core.py:40` | import labels_core as lc  # noqa: E402  (research/labels, via benchmark_core) |  |
| `tools/calibration_app/validate_core.py:121` | # ── cells, in benchmark_core's shape ────────────────────────────────────────── |  |
| `tools/calibration_app/validate_core.py:124` | instruments of benchmark_core read: `runs` and the `starts` derived from them.""" |  |
| `tools/calibration_app/validate_core.py:139` | `benchmark_core.metrics_by_split`, with every id given membership "train": |  |
| `tools/calibration_app/validate_core.py:161` | """A published release's cell, read from its file (`benchmark_core.snapshot_series`). |  |
| `tools/calibration_app/validate_tab.py:4` | Benchmark page, retired in I3 (benchmark review, I2; the decisions and the |  |
| `tools/calibration_app/validate_tab.py:5` | control-by-control inventory are in research/benchmark_review/stage0/DECISIONS.md). |  |
| `tools/calibration_app/validate_tab.py:16` | benchmark_core's functions, called unchanged. |  |
| `tools/calibration_app/validate_tab.py:23` | The reference is chosen among the COLUMNS only. The old Benchmark also offered |  |
| `tools/calibration_app/validate_tab.py:49` | import benchmark_core as bc  # noqa: E402 |  |

