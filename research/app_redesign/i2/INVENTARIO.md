# I2 — inventário 1-para-1 (portão b)

Antes: 63f074f (ponta do I1). Agora: árvore de trabalho do I2.

**Tabela gerada por script:** `make_inventory.py` → `inventory_controls.md`
(dados em `inventory_before.json`, `inventory_after.json`). O script roda a página
Calibrate pelo AppTest nos estados que desenham todo controle condicional (janelas
manuais, proeminência absoluta, amplitude, geométrico/plateau, sinal vorticity,
cruzamento sustained, visão Inspector, Grid de 1 coluna, formato customizado,
diálogo Save results, com e sem a chave). Para cada chave de widget, registra tipo,
rótulo, onde está (barra lateral › cabeçalho › expansor, área central ou diálogo) e o
valor com que é desenhado. Também cruza `_DEFAULTS` e `_PARAM_WIDGET_KEYS` lidos do
fonte, e lista downloads e botões sem chave.

Resultado do cruzamento:
- `_DEFAULTS`: 45 chaves antes e depois, **nenhuma** diferença de chave ou valor; toda
  chave de `_DEFAULTS` é desenhada por um widget no I2.
- `_PARAM_WIDGET_KEYS`: as 39 chaves são desenhadas no I2.
- Toda chave de widget que existia continua existindo com o **mesmo default**, exceto
  `load_all_test_cyclones` (substituída, abaixo).

## Aposentadorias (aprovadas pelo Danilo)

| O quê | Onde estava | Prova |
|---|---|---|
| Carregamento silencioso do example_file | `app.py`: sem nenhum dado, `files = {"example_file": …}` e a legenda "No file uploaded — using example_file.csv as default" | sem dados, a área central mostra só "No tracks loaded — use step 1 in the sidebar." e nenhuma detecção roda (`test_without_data_no_detection_runs`); o exemplo virou o botão "Try example data" |
| "📥 Export parameters (YAML)" | barra lateral, no fim | download ausente no I2; substituído por Save results (YAML sempre incluído) |
| "📦 Export all (ZIP)" | área central, ao lado do seletor de modo | download ausente no I2; substituído por Save results; `_build_zip` removida |

## Substituídas (pelo próprio escopo do I2)

| Antes | Agora |
|---|---|
| checkbox "Load all test cyclones" (chave `load_all_test_cyclones`, área central) | botão "Sample data (51 TRACK cyclones)" (`btn_sample`, passo 1). O estado continua sob o mesmo nome: o botão grava `st.session_state["load_all_test_cyclones"] = True` |
| botão "↺ Reset to defaults" (sem chave, barra lateral) | botão "Defaults" (`btn_defaults`, passo 2), com a legenda pedida. Mesma função (`_reset`), com uma diferença: um YAML ainda no uploader não é reaplicado logo depois (antes, o reset apagava o hash e o arquivo era reimportado na mesma hora, desfazendo o "Defaults") |
| expansor "Custom track format" na área central (`track_custom_*`) | diálogo "Custom format…" (`open_custom_format`) com os mesmos campos, as mesmas chaves e a mesma prévia/confirmação (`track_custom_ok_*`) |

## Movidas (mesma chave, mesmo default)

| Controle | Onde estava | Onde está |
|---|---|---|
| upload de tracks (`track_upload`) | área central | passo 1 |
| sintéticos (`load_synthetic_clean`, `load_synthetic_noisy`) | área central | passo 1, só com a chave |
| importação de YAML (`yaml_import`) e mensagens | barra lateral, "Import configuration" | passo 2 |
| `use_filter`, `cutoff_low`, `cutoff_high` | "1 · Lanczos Filter" | passo 3 · Filtering |
| `boundary_padding` | "1 · Lanczos Filter" | Advanced › Filtering options |
| `replace_endpoints` | "Advanced — Lanczos" | Advanced › Filtering options |
| `sm_mode`, `sm_val`, `sm2_mode`, `sm2_val` | "2 · Savitzky-Golay Smoothing" | Advanced › Filtering options |
| `savgol_poly` | "Advanced — Savgol" | Advanced › Filtering options |
| `reclassify_index0`, `extrema_prominence_*` | "3 · Extrema Filtering" (e o expansor "Prominence filtering") | Advanced › Extrema |
| `length_scale` | "Threshold scale (spans steps 4-6)" | Advanced › Threshold scale |
| `thr_int_len`, `thr_int_gap`, `intensification_min_depth` | "4 · Intensification" (+ "Advanced — intensification") | Advanced › Intensification |
| `thr_dec_len`, `thr_dec_gap` | "5 · Decay" (+ "Advanced — decay") | Advanced › Decay |
| `mature_method`, `thr_mat_len`, `thr_mat_dist`, `mature_amplitude_fraction`, `mature_min_depth` | "6 · Mature" | Advanced › Mature |
| `decay_tail_enabled`, `decay_tail_fraction_val` | "7 · Residual" › expansor | Advanced › Residual |
| `incipient_*`, `thr_inc_len`, `show_incipient_probe` | "9 · Incipient" › expansor | Advanced › Incipient |
| "🗑 Clear bad-case marks" | barra lateral, topo | área central, no resumo de casos ruins (só com a chave) |
| "⚠️ Mark as bad" (`badcase__*`) | sob cada figura do Grid | igual, só com a chave |
| resumo "Bad-case evaluation" | área central | igual, só com a chave |
| seção `evaluation` do YAML | sempre | só com a chave (`_build_yaml(..., include_evaluation=_DEV)`) |
| downloads por ciclone ("⬇ Download CSV"/"⬇ Download PNG") | Grid de 1 coluna | iguais; o PNG é a figura da tela (acerto de cache) em vez da cópia gerada para o ZIP |

Os rótulos mudaram onde tinham jargão ("use_smoothing" → "Savitzky-Golay pass 1",
"incipient_method" → "Incipient method", etc.; a coluna "Kind/label" do
`inventory_controls.md` tem todos). Chaves e defaults não mudaram.

## Novas

`btn_example`, `btn_sample`, `btn_clear_data`, `open_custom_format`,
`custom_format_done`, `btn_defaults`, `btn_save_results` e, no diálogo Save results,
`save_include_yaml` (fixo em True), `save_include_csv` (True), `save_include_png`
(False), `save_prepare`, `save_download`, `save_close`. Em `app.py`:
`_apply_defaults`, `_set_config_source`, `_changed_keys`, `_advanced_differences`,
`_keep_calibrate_state`, `_close_dialogs`/`_open_dialog`, `_custom_format_dialog`,
`_save_results_dialog`, `_build_package`, `_save_signature`, `_load_example`,
`_load_sample`, `_clear_data`. Em `track_format_ui.py`: `classify_uploads`,
`_confirm_key`, `_format_fields`, `format_controls(in_expander=…)`.

## Fora de Calibrate

- Página Label: só o rótulo da caixa de overlays ("Show filtered/smoothed overlays
  (unblinds this case)", com a explicação no tooltip). Nada mais mudou nela.
- **Texto de ajuda do upload, compartilhado — mudou também na página Benchmark.**
  `track_format_ui.UPLOAD_HELP` é o tooltip (?) de dois uploads: o de tracks em
  Calibrate (passo 1) e o "Add cyclone track(s)" da página Benchmark, modo Exploration.
  O trecho "…is refused unless **Custom track format** below is enabled and describes
  it." virou "…is refused unless the **Custom track format** is enabled and describes
  it." (o formato customizado não fica mais abaixo do upload). No Benchmark o "below"
  já era impreciso antes. É a única mudança visível fora de Calibrate e Label; o
  restante do Benchmark não mudou.
- `cyclophaser/`: nada.
