# I1 — inventário 1-para-1 (portão b)

Base: `origin/develop` @ d339c7d. Agora: árvore de trabalho da branch `feat/app-redesign`.
Metade mecânica: `check_inventory.py` → `inventory_check.txt` (AST: nomes de topo,
chaves de widget e `_VIEW_MODES`, por arquivo de `tools/calibration_app/`). Toda
linha "gone" daquele arquivo está explicada abaixo. Nenhum arquivo do app sumiu.

## Aposentadorias (aprovadas pelo Danilo)

| O quê | Onde estava | Prova mecânica |
|---|---|---|
| Seletor Inspection/Labelling (com Confirm/Cancel) | `label_tab._mode_switch`, barra lateral do modo Label | `_mode_switch` GONE; chaves `lab_mode_radio__…`, `lab_mode_confirm`, `lab_mode_cancel` GONE |
| Painel "Test split (frozen)" | `benchmark_tab._render_scoring`, último expander | (não é nome de topo nem chave; ver diff de `_render_scoring`) |
| Botão "Test" | `benchmark_tab.render`, seção 2 · Data | chave `bench_pick_test` GONE |
| Opção "Label" do seletor de modo | `app._VIEW_MODES` | `['Grid','Inspector','Label'] -> ['Grid','Inspector']`; substituída pela página Developer → Manual labelling |

Consequências diretas da aposentadoria do seletor (não são funções novas que somem):
o bloqueio de salvar "switch to Labelling mode" saiu de `render`; o nome do caso
sintético, antes mostrado no seletor de casos só em Inspection, agora aparece
quando aquele caso já teve overlay revelado (decisão de 2c9ab1d).

## Substituída, aprovada pelo Danilo

| O quê | Antes | Agora |
|---|---|---|
| Escala dos overlays da página Label | checkbox "Shared 0-1 scale" (`lab_overlay_shared__…`, item 30c) | rádio "Overlay scale" (`lab_overlay_scale__…`): "Raw range" (padrão, decisão iii de 2c9ab1d), "Shared 0-1" (o 30c, mantido), "Physical" (o antigo desligado) |

Aprovação explícita do Danilo registrada na abertura do I2 (2026-10-05). Até ali a
troca estava listada como "aprovação explícita pendente": o retorno da pausa (d) do
I1 aprovou as capturas, onde o rádio aparece, sem dizer que aprovava a troca.

## Movidas

| Função / elemento | Onde estava | Onde está agora |
|---|---|---|
| `_LABEL_OVERLAY_STYLE` | `app.py` | `label_overlays.LABEL_OVERLAY_STYLE` |
| `_label_overlays(values)` (lia os widgets da barra lateral como globais) | `app.py` | `label_overlays.label_overlays(values, filter_params)`; os parâmetros vêm de `label_overlays.live_filter_params` (barra lateral publicada por Calibrate em `_bench_live_config`; sem ela, defaults da assinatura de `process_vorticity`) |
| Campo "Default ± steps for a new boundary" (chave `label_default_tolerance`) | barra lateral de Calibration (`app.py`) | dentro da página, `label_tab._default_tolerance_input`, à direita do seletor de casos |
| Chamada `label_tab.render(...)` | `app.py`, ramo `elif view_mode == "Label"` | `app_pages/label.py` |
| Chamada `benchmark_tab.render()` | `app.py`, `with tab_bench` | `app_pages/benchmark.py` |
| Corpo da aba Calibration | `app.py`, `with tab_cal` (2 blocos) | `app.py`, `with st.container()` (mesma indentação, mesmo conteúdo); página registrada por `app_pages/calibrate.py` |
| `st.tabs(["Calibration", "Benchmark"])` | `app.py` | `st.navigation` com seções "Calibration" (Calibrate, Benchmark) e "Developer" (Manual labelling, só com a chave) |

## Tocadas (continuam existindo, com mudança)

| Função | Arquivo | Mudança |
|---|---|---|
| radio "Display mode" (texto de ajuda) | `app.py` | sem o parágrafo da opção Label |
| resumo "Bad-case evaluation" | `app.py` | condição `if view_mode != "Label"` removida (sempre mostrado; só existem Grid e Inspector) |
| `_case_navigation` | `label_tab.py` | sem o parâmetro `mode`; nome sintético revelado por caso (`_overlays_revealed`) |
| `_overlay_controls` | `label_tab.py` | sem `mode`, disponível sempre (decisão ii); checkbox "Shared 0-1 scale" virou radio "Overlay scale" com "Raw range" (padrão, decisão iii), "Shared 0-1" (item 30c, mantido) e "Physical" (o antigo desligado) |
| `unit_band` | `label_tab.py` | mesma aritmética, agora via `_finite_range` (o teste que a amarra ao inspector continua passando) |
| `render` | `label_tab.py` | assinatura igual (`default_tolerance`, `overlay_provider`; `default_tolerance=None` desenha o campo na página); linha de status 🙈/👁 no lugar de "Mode:"; texto de ajuda; `lc.LABELS_PATH.relative_to` → `_display_path` |
| `_draw`, `_load_synthetic_names` | `label_tab.py` | só docstrings |
| `_CHART_JS` (montagem) | `label_tab.py` | gráfico só se acomoda quando o host tem tamanho real; ResizeObserver (decisão iv) |
| `_render_scoring` | `benchmark_tab.py` | sem o painel de teste |
| `render` | `benchmark_tab.py` | rótulos do split de teste retidos na página inteira; Validation não oferece séries de teste; "Add column from current sidebar state" desabilitado (com o motivo) antes de Calibrate rodar na sessão; textos de ajuda de Validation e do lote swell |

## Novas

`app.py`: `_developer_mode`, `_PAGE_CALIBRATE/_BENCHMARK/_LABEL`, `_APP_PAGES_DIR`,
`_PAGE_WIDGET_STATE`, `_keep_page_state`, `_carry_uploads`, `_forget_kept_uploads`
(+ botão `forget_kept_uploads`), `_K_KEPT_*`, `_pages`, `_page`, `_PREVIOUS_PAGE`.
`label_tab.py`: `OVERLAY_SCALES`, `onto_raw_range`, `_finite_range`,
`_overlays_revealed`, `_default_tolerance_input`, `_display_path`.
`benchmark_tab.py`: `WIDGET_STATE_KEYS`, `WIDGET_STATE_PREFIXES`.
`label_overlays.py`: `FILTER_KEYS`, `live_filter_params`.
`app_pages/label.py`: `_overlay_provider`.

## Fora de `tools/calibration_app/`

`.streamlit/config.toml` (novo, raiz), `tools/calibration_app/requirements.txt`
(piso streamlit 1.56.0, comentário), READMEs (app, `research/labels/`),
`.gitignore` (`secrets.toml`), `environment.yml` (piso do streamlit). `cyclophaser/`
e `docs/calibration_tool.rst`: nada.
