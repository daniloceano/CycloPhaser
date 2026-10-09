# I2 — página Developer "Validate against labels": relatório

Frente `docs/future_work.md` item 35 (o item só é escrito no fechamento da frente).
Branch `feat/benchmark-review`, base `f3008fc` (I1 commitado).

**Estado: PARADO no checkpoint (d).** A interface **não está commitada**: só a etapa 1
foi commitada e enviada (`b197124`). Todas as execuções abaixo rodaram sobre a árvore
de trabalho = `b197124` + as mudanças não commitadas listadas no fim (5 arquivos
rastreados alterados, novos arquivos não rastreados).

## Etapa 1

- `research/benchmark_review/i2/PREVISOES.md` — commit **`b197124`**, 2026-10-09T02:11:48Z,
  enviado. Nenhum código do I2 existia antes. A primeira execução de código do I2 (uma
  carga da população, sem detecção) veio depois; a primeira medição prevista (custo de
  Run, rodada 1) às 02:41Z; a primeira suíte às 02:47:38Z.

## O que foi construído

| arquivo | papel |
|---|---|
| `tools/calibration_app/validate_core.py` (novo) | sem Streamlit: população oferecida (ids de teste tirados do split primeiro, arquivos de teste nunca abertos, rótulos de teste descartados logo após a leitura, conferência `series_sha256`), blocos TRAIN / ADJUDICATED via `benchmark_core.metrics_by_split` (levanta erro se aparecer bloco de teste), notas por track, listas de desacordo por instrumento, faixas de tolerância |
| `tools/calibration_app/validate_tab.py` (novo) | a página |
| `tools/calibration_app/app_pages/validate.py` (novo) | registro da página |
| `tools/calibration_app/app.py` | `_PAGE_VALIDATE`; menu Developer = Manual labelling, **Validate against labels** (só com a chave); `_PAGE_WIDGET_STATE` com as chaves da Validate |
| `tools/calibration_app/phase_figures.py` | opção nova `tolerances` (padrão None → nada muda) |
| `tools/calibration_app/config_text.py` | `differences_html` (formato "`section.key`: este (reference: ref)") e `breakable` (pontos de quebra só depois de "." e "_") — usados pelas duas páginas |
| `tools/calibration_app/compare_tab.py` | pendências 1–2: o cartão chama `config_text.differences_html`; avisos passam por `config_text.breakable` |

Reuso da Compare: `compare_tab._cell` (o mesmo cache por conteúdo), `_cell_png`,
`_legend`, `_render_relative`, `_render_per_column`, `INVERT_HELP`.

### Decisões de construção (para aprovação)

1. **"Train" (botão da Benchmark, item D).** A população oferecida *é* o split de
   treino, toda selecionada na chegada; "All real" e "All synthetic" a dividem por
   fonte. Não pus um botão "Train" porque o briefing fixa os controles de seleção. O
   inventário registra o item como entregue por construção. Decisão sua.
2. **Conferência `series_sha256`** (não pedida): um rótulo escrito contra outros dados
   não é usado e o track não é oferecido, com o motivo em texto. Hoje os 54 batem
   (como previsto); o teste usa um rótulo adulterado como controle.
3. **Ao ligar o lote**, os tracks novos entram na seleção e os demais ficam como
   estavam (a Compare reinicia tudo; aqui isso desfaria uma seleção manual).
4. **Cartões 3 por linha** (6 colunas = 2 linhas), para que o cartão não fique mais
   estreito que o da Compare.
5. **Snapshot** = coluna lida do arquivo, sem Edit, sem diferenças de parâmetros; a
   procedência mostra os dados do snapshot.
6. **`_mark` (achado F1 abaixo)**: os controles por track e a referência têm o valor
   reescrito no run que os desenha.
7. **"Results are current: N configuration(s) × M track(s)."** ao lado de Run quando
   o resultado está em dia (achado F2 abaixo). Só na Validate; a Compare não muda.
8. Pendência 2 aplicada também ao aviso "Ignored keys" (mesmo defeito, mesma função).

## Previsão × medido

### Suíte (só passed e failed)

| execução | previsto | rodada 1 | **rodada 2 (final)** | arquivo |
|---|---|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0 | 1551 / 0 | 1551 / 0 | **1551 / 0** | `suite_conda_st1.63.0.txt` |
| venv streamlit 1.56.0 | 1551 / 0 | **1550 / 1** | **1551 / 0** | `suite_st1.56.0.txt` |
| CI, wheel | 1280 / 0 | 1280 / 0 | **1280 / 0** | `ci_recipe_summary.json` |
| CI, source tree | 1 / 0 | 1 / 0 | **1 / 0** | idem |
| Chromium (pages + Compare + Validate), 1.63.0 | 14 / 0 | 14 / 0 | **14 / 0** | `browser_conda_st1.63.0.txt` |
| idem, 1.56.0 | 14 / 0 | **13 / 1** | **14 / 0** | `browser_st1.56.0.txt` |

Saídas da rodada 1 em `r1/` (suítes, CI, inventário, custo, capturas) e a primeira
execução Chromium da rodada 2 em `r2/`. `which python` (Python base) e
`cyclophaser.__file__` (afirmado dentro do repositório) no topo de cada `suite_*.txt`.
`tests/test_label_browser.py` não foi rodado. `manual_labels.yaml` intocado (0 linhas
de `git status` depois de cada execução Chromium).

**A previsão de 1.56.0 errou duas vezes; registro, não apago:**

- *Suíte 1.56.0, rodada 1*: `test_nothing_recomputes_on_edit_and_the_cache_holds_across_runs`
  falhou — o aviso "Results out of date" continuava na árvore depois do Run. O
  resultado estava em dia (impressão digital guardada = recalculada, `f10dd0…`); no
  Chromium o aviso some nas duas versões (sondado). Causa: no AppTest 1.56.0, um slot
  que o passe depois de `st.rerun()` deixa vazio guarda o elemento do passe do clique.
  Correção **no app** (decisão 7), não no teste. Depois dela, a rodada 2 inteira foi
  refeita: conda, 1.56.0, CI, Chromium, repetições, inventário, custo e capturas.
- *Chromium 1.56.0, rodada 2*: `test_the_validate_state_survives_a_trip_to_calibrate_in_the_browser`
  falhou ao procurar o toggle pelo papel `switch`. Em 1.56.0 `st.toggle` é um
  `<input type="checkbox">` sem esse papel (medido no DOM); o app estava certo (ligado
  por padrão, desliga no clique). **Desvio de instrumento**, corrigido no teste: o input
  passa a ser achado por `aria-label`. Esse arquivo é só de navegador (desmarcado em
  `-m "not browser"`), então as suítes da rodada 2 continuam válidas; as duas execuções
  Chromium foram refeitas.

Durante a construção (antes de qualquer medição prevista), testes novos falharam e
foram corrigidos nos testes: opções do multiselect vêm formatadas no AppTest; a quebra
`<wbr>` também cai dentro de `filter_params`; o toggle tem papel `switch` em 1.63.0. Um
teste de navegador falhou por defeito **real do app** (achado F1), corrigido no app.

**Testes novos: 31 sem navegador (9 + 22) e 3 de navegador — os números planejados,
com os nomes da previsão.**

**Testes existentes alterados:** previsto só
`tests/test_compare_apptest.py::test_card_differences_are_a_compact_list_not_a_table`.
Medido: **igual** — `git diff f3008fc -- tests/` lista só esse arquivo (12 linhas, só
esse teste). `tests/test_benchmark_apptest.py` e `tests/test_compare_browser.py`
passaram sem alteração.

### e1 (Chromium)

| tarefa | orçamento | previsto | medido (1.63.0 e 1.56.0) |
|---|---|---|---|
| T6 | ≤ 6 | 5 | **5** (menu Validate, Add Defaults, escolher params-track, Add file, Run) |
| T7 | ≤ 3 | 2 | **2** (checkbox do lote, Run) |
| T8 | ≤ 2 | 1 | **1** (filtro; a primeira figura aparece sem outra ação) |
| T9 | 0 | 0 | **0** ("To run, add at least one configuration." visível) |

`tests/test_validate_browser.py`: **10/10 em 1.63.0 e 10/10 em 1.56.0**
(`browser_repeat_*.txt`), contagens idênticas em todas.

### Custo de Run (s, mediana de 3; procedimento da PREVISOES §3)

| colunas | frio previsto | frio medido | quente previsto | quente medido |
|---|---|---|---|---|
| 2 | 6,5 (3,25–13) | **6,44** | ≤ 2 | **0,37** |
| 6 | 17 (8,5–34) | **17,03** | ≤ 2 | **0,75** |

Ordinais: quente/frio = 0,057 e 0,044 (≤ 0,25: **acertou**); frio 6/2 = 2,64 (entre
2,0 e 3,5: **acertou**). Rodada 1 (`r1/measure_run.json`): 6,48 / 0,37 e 17,17 / 0,81.
Dados brutos: `measure_run.json`.

### e2 (dentro das suítes, nas duas versões)

- (i) `test_validate_is_absent_without_the_developer_key` (controle: presente com a
  chave); o teste do I1 de termos proibidos na Compare passou sem alteração.
- (ii) `test_e2_no_test_id_and_no_forbidden_word_anywhere`: seis estados (sem colunas;
  resultados lado a lado; empilhado + filtro; lote ligado e desatualizado; resultados
  com lote; seleção invertida), > 500 textos: **nenhum** dos 19 ids de teste, **nenhum**
  "hit rate"/"accuracy"/"score" fora de "not a score".
- (iii) `test_e2_the_scanners_find_planted_terms_on_the_benchmark_page`: o varredor de
  ids acha ≥ 16 ids de teste na Benchmark (Exploration); o de palavras acha "hit rate"
  nos resultados da Benchmark; e acha termos plantados.

## Portão do I2

| | | evidência |
|---|---|---|
| (a) | **PASS** | `git diff develop -- cyclophaser/` vazio (0 linhas) |
| (b) | **PASS** | `inventory_check.txt`: 24 itens D presentes, 0 faltando; 2 itens marcados **REPLACED** (opção "Manual label" do seletor e a legenda de "parameter baseline", que só existiam pelo rótulo como referência — removidos pelo briefing, A1); Benchmark nesta árvore × `39e658c`: widgets, textos, tabelas, resultados, imagens e expanders **idênticos**; Compare × `f3008fc`: diferenças cruas só nas linhas de diferença e nos dois avisos, e **nenhuma** depois de desfazer só as pendências 1–2 |
| (c) | **PASS** (rodada 2) | tabela acima; rodada 1 teve 1 falha em 1.56.0, explicada e corrigida no app, tudo refeito |
| (d) | **PENDENTE — checkpoint** | capturas abaixo; nenhum commit de interface |
| (e) | e1 e e2 **PASS**; e3 pendente (checkpoint) | acima |
| (f) | **PASS** | todo número traz instrumento e conjunto ("train, n = 47" no título do bloco, na linha de cabeçalho de cada tabela e em cada rótulo de linha); treino e adjudicados em blocos separados, nunca somados (teste); nenhum id de teste chega à página (teste com espião dos arquivos lidos); a referência é sempre uma coluna |
| (g) | declarado | a frente exige o release **2.1.2** no fim; versão não tocada |

**Resultado: o portão não está completo** — (d) e (e3) dependem do checkpoint.

## Capturas (checkpoint d)

`research/benchmark_review/i2/captures/` — Chromium 1600 × 1000, streamlit 1.63.0, chave
de desenvolvedor; `full_page.png` 1600 × 8732; `manifest.json` sem erro de navegador:

- `01_arrival.png`, `02_run_blocked.png` — chegada; Run bloqueado com motivo
- `03_cards.png`, `04_provenance.png` — cartões (Defaults,
  params-track, published v2.0.0, um YAML antigo enviado) e a procedência completa
- `05_train_block.png` — referência no topo, nota dos instrumentos, bloco train
- `06_disagreements.png` — lista de desacordos de uma coluna
- `07_side_by_side.png`, `08_stacked.png` — painel do rótulo primeiro, com as faixas
- `09_filter.png`, `10_adjudicated.png` (train n = 49, adjudicated n = 5), `11_limit.png`
- `12_validate_filled_warning.png`, `13_compare_filled_warning.png` — pendência 2:
  "phase_params. / prominence_relative=None", sem palavra cortada (o teste de navegador
  mede isso no DOM, com controle positivo)
- `full_page.png`

## Achados novos

- **F1** — no navegador, um widget desenhado pela primeira vez num run posterior ao que
  pôs seu valor em `session_state` aparece com o default do próprio widget, e a
  interação seguinte manda esse default de volta (medido: o toggle "Show the label
  panel" nascia desligado em Chromium; o AppTest dizia ligado). Mesmo mecanismo de A12.
  Corrigido na Validate (`_mark`). A Compare não mostra o efeito porque os defaults
  dela são os dos próprios widgets; não mexi nela.
- **F2** — AppTest 1.56.0 mantém, depois de `st.rerun()`, o elemento de um slot que o
  passe seguinte deixa vazio (o navegador limpa). A Compare tem o mesmo padrão e o
  teste equivalente dela passa em 1.56.0; não investiguei por quê.
- **F3** — com o lote ligado, a coluna de snapshot fica com denominador 47 dentro do
  bloco "train, n = 49" (os 2 tracks do lote não estão no snapshot, A7) e o bloco "Per
  configuration" (da Compare) conta esses 2 como "Detection failed", embora nada tenha
  sido detectado — o texto da célula diz "not in snapshot". Correto como número, mas a
  palavra engana. Decisão sua.

## Pedidos ao Danilo no checkpoint

1. Aprovar ou corrigir a interface (capturas) e fazer o percurso e3 (T6–T9).
2. Decisões de construção 1–8, em especial 1 (sem botão "Train") e 7 (linha "Results
   are current", só na Validate).
3. F3: renomear "Detection failed" para colunas de snapshot, ou deixar.

## Mudanças não commitadas (aguardando aprovação)

Rastreados: `tools/calibration_app/app.py`, `compare_tab.py`, `config_text.py`,
`phase_figures.py`, `tests/test_compare_apptest.py`. Novos: `validate_core.py`,
`validate_tab.py`, `app_pages/validate.py`, `tests/test_validate_core.py`,
`tests/test_validate_apptest.py`, `tests/test_validate_browser.py`, e em
`research/benchmark_review/i2/`: scripts (`check_inventory.py`, `measure_run.py`,
`capture_screenshots.py`, `run_suite.sh`, `run_browser.sh`, `run_repeat_browser.sh`),
saídas, `captures/`, `r1/`, `r2/` e este relatório. Receita do CI rodada com
`research/app_redesign/i1/run_ci_recipe.sh` (`OUT_DIR=research/benchmark_review/i2`).

---

# Rodada 2 — correções do checkpoint (d) da rodada 1

As saídas finais da rodada 1 foram movidas para `rodada1_final/` (suítes, CI,
Chromium, repetições, inventário, custo, capturas). Os arquivos no topo de
`research/benchmark_review/i2/` são da rodada 2.

## Decisões do Danilo e e3 da rodada 1 (registro)

- **e3** (percurso T6–T9, escrito por ele): "nenhum problema". Nada a corrigir.
- Sem botão "Train": aceito. Decisões 2–6: aceitas. Decisão 8: substituída por R1.
- **F2**: a linha "Results are current: …" vai para as duas páginas, com um teste na
  Compare que verifica o sumiço de "Results out of date" depois de um novo Run.
- **F3**: separar "not in this snapshot" (R3).

## Previsão

`research/benchmark_review/i2/PREVISOES_r2.md`, commit **`f0d2c33`**
(2026-10-09T11:26:41Z), enviado antes de qualquer código desta rodada. Primeira
medição: a suíte conda às 11:42:18Z.

## Mudanças

- **R1** — `config_text.breakable` (U+200B) foi removido. `config_text.warning_html`
  desenha os avisos de chaves completadas e de chaves ignoradas como um bloco HTML com
  aparência de aviso (fundo âmbar translúcido, borda à esquerda, texto na cor do tema),
  com `<wbr>` só depois de "." e "_". O texto do bloco sem as tags é a frase exata:
  ela só escapa `& < >`, porque `'` virava `&#x27;` no texto sem tags (pego pelo teste
  na construção). Isso vale para a Compare e para a Validate; a Calibrate não muda.
  Nenhum U+200B sobra nas fontes do app. Os que existiam em scripts e testes desta
  frente passaram a escapes `​` explícitos.
- **R2** — o cabeçalho de cada lista de desacordo diz, por exemplo, "sequence: 17
  differ, 10 with a boundary outside its tolerance · mature: 6 not within the margin".
  As duas contagens de sequência são de tracks. "detection failed: k" e "not in this
  snapshot: k" aparecem só quando há. Nenhum número soma os instrumentos.
- **R3** — `validate_core.snapshot_cell` marca `missing` um track que o release não
  rodou. Esses tracks aparecem:
  - em uma lista própria nas listas de desacordo, e nunca como desacordo no filtro;
  - em uma nota sob cada tabela de concordância afetada, por exemplo "published v2.0.0:
    2 of 49 tracks are not in this snapshot (published releases cover the 51 + 12
    bundled series) and are not counted.";
  - em uma nota sob "relative to" ("… "Tracks compared" leaves them out.");
  - numa linha "Not in this snapshot (not counted)" no bloco por configuração. Ali
    "Detection failed" deixa de contá-los. A linha vem de um parâmetro opcional de
    `compare_tab._render_per_column`, que a Compare não passa: a saída dela não muda;
  - por track, numa nota no lugar de um erro.
- **F2** — "Results are current: N configuration(s) × M track(s)." ao lado do Run,
  agora também na Compare, quando o resultado está em dia.

## Previsão × medido

| execução | previsto | medido | arquivo |
|---|---|---|---|
| conda, streamlit 1.63.0 | 1557 / 0 | **1557 / 0** | `suite_conda_st1.63.0.txt` |
| venv, streamlit 1.56.0 | 1557 / 0 | **1557 / 0** | `suite_st1.56.0.txt` |
| CI, wheel | 1280 / 0 | **1280 / 0** | `ci_recipe_summary.json` |
| CI, source tree | 1 / 0 | **1 / 0** | idem |
| Chromium 1.63.0 | 14 / 0 | **14 / 0** | `browser_conda_st1.63.0.txt` |
| Chromium 1.56.0 | 14 / 0 | **14 / 0** | `browser_st1.56.0.txt` |

`which python` (Python base) e `cyclophaser.__file__` (afirmado no repositório)
estão no topo de cada `suite_*.txt`. `tests/test_label_browser.py` não foi rodado.
`manual_labels.yaml` ficou intocado. Os testes que gravam arquivos os removem; o
`git status` não mostra nada novo fora do previsto.

**Testes novos: 6**, os nomes da previsão. **Testes existentes alterados**, iguais
ao previsto:
- `test_validate_apptest.py`: `test_the_card_shows_differences_and_full_provenance`
  (R1), `test_card_format_and_filled_warning_shared_by_both_pages` (R1) e
  `test_disagreeing_tracks_listed_per_column_and_instrument` (R2: o cabeçalho por
  instrumento, e nenhum cabeçalho termina em ": <número>");
- `test_validate_browser.py::test_the_filled_keys_warning_breaks_no_word_in_a_narrow_card`
  (R1: o seletor do bloco, e a ida e volta no DOM — o `innerText` do aviso contém
  `phase_params.prominence_relative=None` e nenhum U+200B).

Nenhum teste existente da Compare mudou: `git diff f3008fc -- tests/` só mostra a
mudança da rodada 1 e o teste novo F2.

Na construção, um teste novo falhou uma vez: o texto sem tags trazia `&#x27;`.
Corrigi no app (escape só de `& < >`); o teste não mudou.

**Uma ocorrência de instrumento, registrada:** a primeira tentativa de rodar Chromium
e repetições não chegou a rodar teste nenhum. O zsh não dividiu a variável de
argumentos e os scripts pararam no argumento ausente (`set -u`), sem gravar nada.
Rodei de novo com argumentos explícitos; os números acima são dessa execução.

## e1 (1.63.0 e 1.56.0)

T6 **5** (≤ 6), T7 **2** (≤ 3), T8 **1** (≤ 2), T9 **0**: igual ao previsto.
`tests/test_validate_browser.py` (alterado): **10/10 em 1.63.0 e 10/10 em 1.56.0**
(`browser_repeat_*.txt`), contagens idênticas em todas. Os T1–T5 da Compare seguem
4/4/1/1/0.

## e2

- Dentro das suítes, nas duas versões: nenhum id de teste e nenhuma palavra proibida
  na Validate; nenhum termo proibido na Compare (teste do I1 sem alteração).
- Novo: `test_no_rendered_text_contains_a_zero_width_space` varre as duas páginas com
  os dois avisos na tela: nenhum U+200B. Controle: o mesmo varredor acha o caractere
  plantado.
- `test_a_key_copied_from_a_warning_is_the_real_key`: o nome copiado do aviso (texto
  sem tags) é `phase_params.prominence_relative` e, colado num YAML, não é listado
  como ignorado. Controle: o nome da rodada 1, com U+200B, é listado como ignorado.

## Portão

| | | evidência |
|---|---|---|
| (a) | **PASS** | `git diff develop -- cyclophaser/` vazio |
| (b) | **PASS** | `inventory_check.txt`: 24 itens D presentes, 2 REPLACED (A1), 0 faltando; Benchmark × `39e658c` idêntica; Compare × `f3008fc`: diferenças cruas só nas linhas de diferença, nos dois avisos (agora bloco HTML) e na linha "Results are current"; nenhuma depois de desfazer só pendências 1–2, R1 e essa linha |
| (c) | **PASS** | tabela acima; 10 repetições por versão |
| (d) | **PENDENTE — checkpoint** | capturas abaixo; nenhum commit de interface |
| (e) | **PASS** | e1, e2 acima; e3 registrado ("nenhum problema", nada a levar) |
| (f) | **PASS** | todo número traz instrumento e conjunto; nenhum número combina os instrumentos (cabeçalhos por instrumento, teste); treino e adjudicados separados; denominadores do snapshot explicados em nota visível; nada sobre o split de teste |
| (g) | declarado | a frente exige o release **2.1.2** no fim; versão não tocada |

## Capturas (checkpoint d)

`research/benchmark_review/i2/captures/` — Chromium 1600 × 1000, streamlit 1.63.0,
nenhum erro de navegador (`manifest.json`), arquivo temporário removido. As capturas
01–13 e `full_page.png` foram refeitas; as novas são:

- `12_validate_filled_warning.png`, `13_compare_filled_warning.png` — o bloco de aviso
  (tema claro), "phase_ / params.prominence_ / relative=None": quebra só depois de "_"
  e ".";
- `18_validate_warning_dark.png`, `19_compare_warning_dark.png` — o mesmo no tema
  escuro (`STREAMLIT_THEME_BASE=dark`);
- `14_disagreement_headers.png` — cabeçalhos por instrumento (lote ligado, com
  "not in this snapshot: 2" na coluna do release);
- `15_snapshot_note.png` — as notas "2 of 49 … not in this snapshot … not counted"
  sob as tabelas;
- `16_validate_results_current.png`, `17_compare_results_current.png`;
- `full_page.png`.

## Achados novos

- **F4** — `html.escape` escapava `'` no texto do aviso. É inofensivo no navegador,
  mas faria o texto sem tags diferir da frase. Corrigido (escape só de `& < >`).
- **F5** — nos cabeçalhos, "10 with a boundary outside its tolerance" conta tracks,
  não fronteiras. As fronteiras estão na tabela ("Boundaries within the label's
  tolerance"). Se preferir explicitar "tracks", é uma palavra.

## Pedidos ao Danilo no checkpoint

1. Aprovar ou corrigir a interface (capturas, em especial o bloco de aviso nos dois
   temas, 12/13/18/19).
2. F5: deixar "10 with a boundary outside its tolerance" ou escrever "10 tracks with
   …".

---

# Fechamento do I2

## Checkpoint (d) — aprovado

Aprovação escrita pelo Danilo: "aprovo" (2026-10-09). Com ela, a interface, os testes
novos e alterados e as evidências das rodadas 1 e 2 (`r1/`, `r2/`, `rodada1_final/`
e as saídas da rodada 2 no topo desta pasta) foram commitados em
`feat/benchmark-review` e enviados. Não houve merge nem PR, e a versão não foi tocada.
O item 35 de `docs/future_work.md` só será escrito no fechamento da frente.

## Desvios mantidos no registro

- **Rodada 1, streamlit 1.56.0 (previsão errada):**
  - suíte 1550 / 1: um aviso ficava na árvore do AppTest depois de `st.rerun()` (F2).
    Corrigi no app e refiz tudo;
  - Chromium 13 / 1: em 1.56.0 o toggle não tem o papel `switch`. Foi desvio de
    instrumento, corrigido no teste.
- **F4:** `'` virava `&#x27;` no texto do aviso sem tags. Um teste pegou na construção
  e a correção foi no app (escape só de `& < >`).
- **Rodada 2, instrumento:** a primeira tentativa de Chromium e repetições não rodou
  teste nenhum. O zsh não dividiu a variável de argumentos e os scripts pararam em
  `set -u`, sem gravar saída. Refiz com argumentos explícitos.

## Pendências para o I3

1. **F5:** no cabeçalho de desacordo, escrever "17 tracks differ" e "10 tracks with a
   boundary outside its tolerance" — a contagem é de tracks, não de fronteiras.
2. As já registradas para a frente: aposentar a Benchmark antiga; README do app;
   `docs/calibration_tool.rst`; release 2.1.2 no fim.
