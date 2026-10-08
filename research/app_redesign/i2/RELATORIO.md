# I2 — barra lateral guiada, Save results, funções de desenvolvedor, textos

Branch `feat/app-redesign`, sobre 83a5114 (ponta do I1, 63f074f, mais o registro da
aprovação de "Overlay scale" no inventário do I1, commit próprio já enviado).
**Nada do I2 commitado:** PAUSA do portão (d), aguardando aprovação do Danilo.
Data: 2026-10-05/06.

## O que mudou (só Calibrate, mais o rótulo cortado da Label)

**Barra lateral de Calibrate**, logo abaixo do menu de páginas:

1. **Data**: upload de tracks (veio da área central); "Custom format…" abre um
   `st.dialog` com os campos e a prévia/confirmação de sempre; "Try example data";
   "Sample data (51 TRACK cyclones)" (substitui "Load all test cyclones"); os
   sintéticos só com a chave; com dados, "N tracks loaded" e "Clear data".
2. **Starting configuration**: "Defaults" (o antigo "Reset to defaults") com a legenda
   pedida; a importação de YAML com as mensagens de chaves ignoradas/preenchidas; a
   linha "Active: Defaults" ou "Active: <arquivo>.yaml", com "edited (N changes)"
   quando algo mudou desde a carga.
3. **Filtering**: só Lanczos, low cutoff e high cutoff, com o texto: "Only the
   filtering was calibrated, and only for TRACK-filtered 850 hPa vorticity. For other
   sources, adjust the cutoffs and check the figures."

**Advanced**: o aviso "N advanced parameters differ from defaults", sempre visível,
com "Show which" para listar quais e os valores. Abaixo, oito expansores no mesmo
nível, nenhum dentro de outro, na ordem de execução do detector: Filtering options,
Extrema, Threshold scale, Intensification, Decay, Mature, Residual, Incipient (com a
sonda). Todos os controles continuam lá, com as mesmas chaves e os mesmos defaults.

4. **Save results**: botão em destaque no fim da barra lateral. O diálogo traz:
   - Configuration (YAML), sempre incluída;
   - Phase tables (CSV por ciclone), marcada;
   - Figures (PNG), desmarcada;
   - "Prepare package", que monta o ZIP só quando o usuário pede, e o download.

   O `parameters.yaml` tem o conteúdo do antigo export. Save results substitui
   "Export parameters (YAML)" e "Export all (ZIP)". Os downloads por ciclone da grade
   de 1 coluna ficam.

**Outras mudanças:**

- **Funções de desenvolvedor**, só com a chave: a caixa "⚠️ Mark as bad", o resumo de
  casos ruins com "Clear bad-case marks", a seção `evaluation` do YAML e os
  sintéticos. Sem a chave nada disso aparece nem entra no YAML.
- **Sem dados**: a área central mostra só "No tracks loaded — use step 1 in the
  sidebar." e nenhuma detecção roda (nem o exemplo é carregado em silêncio).
- **Textos visíveis de Calibrate** sem números de item, caminhos, nomes de função
  interna, nomes de preset e a palavra "tab". Conferido por varredura de AST das
  strings passadas a chamadas em `app.py`, `inspector_plotly.py`, `layer_inspector.py`
  e `inspector_mpl.py`. Os únicos acertos que sobram não são texto visível: os nomes
  de arquivo das páginas passados a `st.Page`, uma chave de sessão e a palavra comum
  "preset" (a busca não diferencia maiúsculas, e nenhum NOME de preset ficou).
  Rótulos curtos; a explicação ficou nos tooltips.
- **Versão exibida**: a do pacote instalado (`importlib.metadata`), no cabeçalho e no
  `metadata` do YAML.
- **Página Label**: o rótulo da caixa virou "Show filtered/smoothed overlays
  (unblinds this case)", com a explicação no tooltip. Nada mais mudou nela.

## Marca de caso ruim (item 3)

Evidência antes de corrigir (`badmark_before.txt`, o script do I1): a mesma perda na
develop (d339c7d) e na ponta do I1 — "marked in Grid=True | still marked in
Inspector=False | still marked back in Grid=False".

Causa: as caixas de marca só são desenhadas no Grid, e o Streamlit apaga o estado de
um widget que não foi desenhado na execução. Correção: em toda execução de Calibrate,
as chaves `badcase__*` (e as dos dois diálogos, também não desenhadas sempre) são
reescritas em `session_state` (`_keep_calibrate_state`), o mesmo mecanismo que o I1
usa para as páginas fechadas. A troca de página já era coberta por
`_PAGE_WIDGET_STATE`.

Depois (`check_badmark.py` → `badmark_after.txt`, mesmo procedimento nos três):

| | Grid | Inspector | volta ao Grid | Benchmark → Calibrate |
|---|---|---|---|---|
| develop d339c7d | True | **False** | **False** | — |
| ponta do I1 63f074f | True | **False** | **False** | **False** |
| I2 | True | True | True | True |

## Previsão × medido (observação, não critério)

`PREVISOES.md` foi escrito antes de qualquer medição. As medidas vêm de
`measure_slider.py` → `measure_before.json` (63f074f) e `measure_after.json` (I2):
51 tracks, 5 passos do slider High cutoff com valores novos, streamlit 1.63.0.

| | gerações de PNG por passo | por função | mediana no servidor |
|---|---|---|---|
| I1 (63f074f) | 102 (todos os 5) | `_render_periods_png` 102 | 39,06 s |
| I2 | **51** (todos os 5) | `_render_periods_png` 51 | **13,16 s** (×0,34) |

A previsão vale nas duas partes. As 51 figuras do pacote de exportação deixaram de ser
geradas a cada mudança e ficaram só as 51 da tela. O tempo caiu, e ×0,34 também fica
abaixo dos ×0,75 que eu tinha escrito como expectativa minha.

## Portão

**(a)** `git diff 63f074f -- cyclophaser/`: vazio.

**(b)** `INVENTARIO.md` + `make_inventory.py` → `inventory_controls.md`.

- `_DEFAULTS`: 45 = 45, sem nenhuma diferença.
- As 45 chaves e as 39 de `_PARAM_WIDGET_KEYS` são desenhadas no I2.
- Toda chave antiga mantém o default.
- **Aposentadas:** o carregamento silencioso do example_file, "Export parameters
  (YAML)" e "Export all (ZIP)" (com `_build_zip`).
- **Substituídas:** "Load all test cyclones" → "Sample data", com o estado sob o mesmo
  nome; "Reset to defaults" → "Defaults"; o expansor de formato customizado → o
  diálogo, com as mesmas chaves.
- **Movidas:** todo o resto, com a tabela no inventário.
- Nenhuma outra função sumiu.

**(c)** Ver "Execuções finais" abaixo.

Testes novos em `tests/test_calibrate_i2_apptest.py` (13):
- ordem dos passos;
- nenhum expansor dentro de outro, com um controle feito à mão em 1.56 e 1.63 (um
  expansor com outro dentro conta 2);
- só os três de filtragem fora do Advanced;
- o aviso muda com um parâmetro avançado mas não com um básico;
- o aviso e a linha "Active" seguem um YAML importado e marcam "edited";
- "Defaults" restaura a assinatura;
- funções de desenvolvedor ausentes sem a chave (inclusive `evaluation` fora do YAML)
  e presentes com ela;
- sem dados nenhuma detecção roda, com controle positivo;
- a marca sobrevive a Grid → Inspector → Grid e à troca de página;
- a versão exibida é `importlib.metadata.version("cyclophaser")`;
- Save results empacota o que as opções dizem;
- o YAML salvo é o conteúdo do export antigo.

No Chromium (`tests/test_app_pages_browser.py`):
- Save results baixa o arquivo, e o ZIP tem YAML + CSV por padrão e o PNG só quando
  marcado;
- o diálogo de formato customizado lê um arquivo fora do padrão: recusado → campos →
  prévia → confirmação → entra na grade.

Testes existentes ajustados ao I2, com o porquê em comentário em cada um:
- navegação, Inspector e upload: carregam dados explicitamente; o upload abre o
  diálogo;
- "Reset to defaults" → `btn_defaults`;
- os dois testes de numeração "N · grupo / Step N" de `test_sidebar_coverage.py` foram
  trocados por um de ordem dos grupos Advanced: a numeração foi aposentada pelo
  próprio I2, e a intenção (ordem de execução) continua testada;
- harness e testes de navegador: esperam "1 · Data" e localizam os uploaders pelo
  rótulo;
- a caixa de overlays é procurada pelo papel `checkbox`, porque o tooltip novo cria um
  botão "Help for …" com o mesmo texto.

**(d)** Capturas em `captures/before/` (63f074f) e `captures/after/`, viewport
1600×1000, geradas por `capture_screenshots.py`:
- `sidebar_public_NN` e `sidebar_dev_NN`: a barra lateral inteira, em partes;
- `save`: o diálogo Save results; antes, o "Export all (ZIP)";
- `advanced_notice`: o aviso com um valor mudado e "Show which" ligado;
- `main_no_data`: a área central sem dados;
- `label_overlays`: a caixa de overlays.

**PAUSA: nada de commit de interface até a aprovação explícita do Danilo.**

**(e)** Não aplicável (a rodada de usabilidade é o I4).

**(f)** Nada exige release: `cyclophaser/` está intocado. O piso do streamlit fica em
1.56.0, porque tudo o que o I2 usa existe ali: `st.dialog` com `on_dismiss`,
`st.toggle`, `st.download_button(on_click="ignore")` e `importlib.metadata`. Testado
inteiro no piso: testes de app e Chromium.

## Execuções finais (código final, em sequência, sem nada concorrendo)

| | streamlit 1.56.0 (piso; venv novo, playwright 1.62.0) | streamlit 1.63.0 (env conda `cyclophaser`) |
|---|---|---|
| testes de app (os 6 `test_*apptest*.py`, `test_sidebar_defaults`, `test_sidebar_coverage`, `test_app_passo5_fixes`, `test_app_distance_removed`, `test_app_yaml_null_export`) | **189 passed, 0 failed** — `app_tests_st1.56.0.txt` | **189 passed, 0 failed** — `app_tests_conda_st1.63.0.txt` |
| Chromium (`test_label_browser.py` + `test_app_pages_browser.py`) | **36 passed, 0 failed** — `browser_tests_st1.56.0.txt` | **36 passed, 0 failed** — `browser_tests_conda_st1.63.0.txt` |

- suíte conda completa, `-m "not browser"`: **1468 passed, 0 failed** (`suite_conda_raw.txt`);
- receita do CI (`run_ci_recipe.sh`, `OUT_DIR=research/app_redesign/i2`): **1278 passed,
  0 failed** contra a wheel (37 pulados; o arquivo de teste novo é o 11º módulo pulado
  na coleta por falta de streamlit) e **1 passed, 0 failed** em `source_tree`
  (`ci_recipe_summary.json`, `ci_recipe_raw.txt`). Só o env conda testa o app;
- `research/labels/manual_labels.yaml`: sha256 igual antes e depois
  (`labels_sha_before.txt` = `labels_sha_after.txt`) e `git status` vazio.

## Desvios e por quê

- **Diálogos ficam abertos até serem fechados**: uma flag de sessão é limpa pelo
  "Done" ou pelo ✕ (`on_dismiss`). Assim um rerun vindo de outro lugar não fecha o
  diálogo, e o conteúdo dele fica testável pelo AppTest (que reroda o script inteiro).
- **"Defaults" não reaplica um YAML que ainda está no uploader.** O antigo "Reset to
  defaults" reimportava o arquivo na hora, o que desfaria o "Defaults".
- **`UPLOAD_HELP` ("below is enabled" → "is enabled")**: o texto é compartilhado com o
  upload do Benchmark, a única mudança visível fora de Calibrate/Label.
- **Rótulos com nomes de parâmetro viraram nomes curtos** ("use_smoothing" →
  "Savitzky-Golay pass 1", etc.). As chaves não mudaram. Os nomes de parâmetro seguem
  na lista "Show which", porque são os do YAML salvo.
- **"Which?" → "Show which"**: um popover ficou ilegível (texto escuro sobre a barra
  lateral escura, visto na captura) e foi trocado por um toggle com a lista na própria
  barra lateral.

## Pendências

- Na rodada intermediária dos testes de app no env conda, 2 testes falharam uma vez
  (`test_add_column_from_the_sidebar_reflects_the_calibrate_sidebar` e
  `test_previous_and_next_move_through_the_queue_without_saving`). Eles passaram
  isolados 3 vezes, numa reprodução do mesmo comando (189/0) e na suíte conda inteira
  feita logo depois (1468/0). O texto do erro não ficou guardado, porque o executor
  filtrava as linhas `E`; os executores agora as guardam. **Não voltou a ocorrer** nas
  execuções finais (189/0 nas duas versões, 1468/0 na suíte conda). A causa segue
  desconhecida.
- A tela inicial completa, paginação e estatísticas são do I3.

## Retorno da pausa (d)

Capturas aprovadas pelo Danilo. Antes do commit:

1. **Falha intermitente.** Os dois testes que falharam uma vez na rodada intermediária
   no env conda foram
   `tests/test_app_navigation_apptest.py::test_add_column_from_the_sidebar_reflects_the_calibrate_sidebar`
   e `tests/test_label_apptest.py::test_previous_and_next_move_through_the_queue_without_saving`.
   Seis rodadas seguidas de todos os arquivos com AppTest (`run_app_tests.sh`, agora
   guardando as linhas de erro), sem nada concorrendo:

   | rodada | streamlit 1.56.0 | streamlit 1.63.0 (conda) |
   |---|---|---|
   | 1 | 189 passed, 0 failed | 189 passed, 0 failed |
   | 2 | 189 passed, 0 failed | 189 passed, 0 failed |
   | 3 | 189 passed, 0 failed | 189 passed, 0 failed |

   Saídas: `app_tests_st1.56.0_round{1,2,3}.txt` e
   `app_tests_conda_st1.63.0_round{1,2,3}.txt`. Nenhuma falha, portanto nada a
   classificar como TESTE ou APP. A falha original não se reproduziu em 6 rodadas
   completas, nem antes em 5 execuções isoladas ou completas. Com o texto do erro
   perdido, a causa continua desconhecida; se voltar a ocorrer, o executor guarda o
   texto.
2. `INVENTARIO.md`: registrado que o texto de ajuda do upload, compartilhado, mudou
   também na página Benchmark.
3. Nenhum ajuste visual pedido, então nenhuma captura refeita. As suítes finais acima
   valem para o código commitado: depois delas só mudaram `RELATORIO.md` e
   `INVENTARIO.md`.

