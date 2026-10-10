# I1 — página pública "Compare": relatório

> **Rodada 1** (abaixo, até "Mudanças não commitadas") e **rodada 2** (no fim). Os
> arquivos de saída da rodada 1 foram movidos para `r1/`; as capturas da rodada 1
> foram substituídas pelas da rodada 2.

Frente `docs/future_work.md` item 35 (número reservado; o item ainda não foi escrito
no arquivo, isso acontece no fechamento da frente). Branch `feat/benchmark-review`, de
`develop` @ `39e658c`.

**Estado: PARADO no checkpoint (d).** A interface **não está commitada**: só a etapa 1
foi commitada e enviada (`2eeb85d`). Todas as execuções abaixo rodaram sobre a árvore
de trabalho = `2eeb85d` + as mudanças não commitadas listadas no fim (3 arquivos
rastreados alterados, os novos arquivos não rastreados).

## Etapa 1

- `2eeb85d` — `research/benchmark_review/stage0/DECISIONS.md` (decisões, inventário
  1-para-1, achados A1–A10 conferidos em `39e658c`, A11 novo, critério (e)) e
  `research/benchmark_review/i1/PREVISOES.md`. Commitado e enviado antes de qualquer
  medição.
- O texto da etapa 0 recebido não traz **A4** nem **A8**; estão registrados como
  ausentes, não reconstruídos.

## O que foi construído

| arquivo | papel |
|---|---|
| `tools/calibration_app/compare_core.py` (novo) | lógica sem Streamlit e sem rótulos: leitura do track (o mesmo `track_io.read_track` da Calibrate, com índice de tempo), chave da série pelo conteúdo, chave da configuração efetiva, diferenças com tolerância de float, medidas relativas, "incipient absent" por coluna |
| `tools/calibration_app/compare_tab.py` (novo) | a página |
| `tools/calibration_app/app_pages/compare.py` (novo) | registro da página |
| `tools/calibration_app/phase_figures.py` (novo) | código de figura extraído da Benchmark, sem mudar a lógica; cada página passa a sua paleta |
| `tools/calibration_app/config_text.py` (novo) | as frases "Ignored keys: …" e "… filled with the earlier defaults …", usadas pela importação de YAML da Calibrate e pelos cartões da Compare (mesma redação por construção) |
| `tools/calibration_app/app.py` | menu Calibration = Calibrate, **Compare**, Benchmark; `_PAGE_WIDGET_STATE` com as chaves da Compare; publica `_compare_live_tracks` (os bytes que a detecção lê, ao lado de `cyclone_names`) e `_compare_defaults_config`; publica `_app_arrived`; a importação de YAML usa `config_text` |
| `tools/calibration_app/benchmark_tab.py` | as funções de figura passam a delegar a `phase_figures` (mesmos nomes, mesma paleta própria) |
| `tools/calibration_app/benchmark_core.py` | **só a docstring** de `reference_metrics` (A2) |

Decisões de construção que não estavam escritas na etapa 0 (para aprovação):

1. **"Defaults"** = o `_bench_live_config` publicado pela própria Calibrate sempre que
   ela mostra "Defaults" sem edição (primeira execução da sessão, e logo depois do
   botão Defaults). Tentei primeiro montar a partir das defaults da assinatura do
   pacote e o teste de igualdade falhou: a assinatura dá `cutoff_high = 18.0`, o
   slider dá `18` — iguais em `==`, chaves de cache diferentes. Capturar a saída do
   próprio sidebar elimina a segunda derivação. Teste: depois do botão Defaults,
   `_bench_live_config == _compare_defaults_config` e as chaves de configuração são
   iguais, com o controle de que antes do botão elas diferem.
2. **"Current settings"** é uma fotografia tirada quando a coluna é adicionada (como
   a coluna "sidebar" da Benchmark). Se a Calibrate mudar depois, o cartão diz
   "Calibrate's settings have changed since; add Current settings again…".
3. **Paginação das figuras por track** (12 / 24 / 48 por página, como a Grid do item
   34 I3). A detecção roda em todos os tracks selecionados; só a página é desenhada.
4. **Persistência entre páginas no navegador.** Medido em Chromium (1.63.0): numa ida
   Compare → Calibrate → Compare, um valor que o usuário mudou num widget da Compare
   não volta. A referência já não estava no `session_state` quando a primeira
   execução da Calibrate começou, então o shield de `_keep_page_state` não tinha o que
   reescrever; o layout voltou com o valor que o `setdefault` tinha posto. O AppTest
   não vê isso (o teste equivalente de AppTest passava). Correção: cópia em chave
   comum (`_cmp_kept_*`) de cada valor de widget, reaplicada na primeira execução
   depois de chegar à página (`_app_arrived`, publicado por app.py) e quando a chave
   some. Teste novo de navegador cobre: referência e "Stacked" sobrevivem à ida e a
   uma interação depois da volta.
5. O YAML enviado entra só com as duas seções de parâmetros (`metadata` e
   `evaluation` não são guardados nem exibidos). O cartão "Full configuration (YAML)"
   mostra a configuração como roda (chaves completadas incluídas, chaves ignoradas
   fora).

## Previsão × medido

### Suíte (só passed e failed)

| execução | previsto | medido | arquivo |
|---|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0, `-m "not browser"` | 1515 / 0 | **1515 / 0** | `r1/suite_conda_st1.63.0.txt` |
| venv streamlit 1.56.0, mesmo comando | 1515 / 0 | **1515 / 0** | `r1/suite_st1.56.0.txt` |
| CI, wheel | 1280 / 0 | **1280 / 0** | `r1/ci_recipe_summary.json`, `r1/ci_recipe_raw.txt` |
| CI, source tree | 1 / 0 | **1 / 0** | idem |
| Chromium (`test_app_pages_browser.py` + `test_compare_browser.py`), 1.63.0 | 11 / 0 | **11 / 0** | `r1/browser_conda_st1.63.0.txt` |
| idem, 1.56.0 | 11 / 0 | **11 / 0** | `r1/browser_st1.56.0.txt` |

Testes novos: 30 sem navegador (8 em `test_compare_core.py`, 22 em
`test_compare_apptest.py`) e 3 de navegador — os números planejados. Nenhum teste
existente foi alterado (`git diff develop -- tests/` só lista arquivos novos). Em
cada execução de suíte, `which python` foi registrado (é o Python base; o
interpretador usado é passado explicitamente) e `cyclophaser.__file__` foi
**afirmado** dentro do repositório. `tests/test_label_browser.py` não foi rodado.

Durante a construção, quatro testes novos falharam na primeira execução e foram
corrigidos **nos testes** (o app não mudou por eles): um esvaziava a seleção com
Invert e esperava o aviso de desatualizado; um comparava duas colunas idênticas e
esperava o dobro de detecções (o cache deduplicou, como deve); um controle de A11
rodava sem suavização 'auto', em que o eixo de tempo não muda nada; e um contava
imagens pelo nome de elemento errado (`imgs` em 1.56.0, `image` em 1.63.0 — os dois
são contados agora). Dois testes de navegador falharam por causa do auxiliar de
seletor (o dropdown fechava com a rolagem do próprio clique) e por causa do defeito
real da decisão 4.

### Custo de Run (s, mediana de 3; AppTest, conda, 1.63.0, x86_64)

| página | colunas | frio previsto | frio medido | quente previsto | quente medido |
|---|---|---|---|---|---|
| Compare | 1 | 4 (2–8) | **3,04** | ≤ 2 | **0,20** |
| Compare | 2 | 7 (3,5–14) | **5,82** | ≤ 2 | **0,25** |
| Compare | 4 | 13 (6,5–26) | **11,37** | ≤ 2 | **0,34** |
| Benchmark | 1 | 6 (3–12) | **6,54** | 3,5 (1,75–7) | **2,68** |
| Benchmark | 2 | 12 (6–24) | **12,18** | 7 (3,5–14) | **4,56** |
| Benchmark | 4 | 24 (12–48) | **23,83** | 13 (6,5–26) | **8,49** |

Todas as 12 células caíram dentro da faixa prevista. Previsões ordinais:

1. Compare quente ≤ 0,25 × frio — **acertou** (0,066; 0,043; 0,030).
2. Compare frio < Benchmark frio — **acertou** (3,04 < 6,54; 5,82 < 12,18; 11,37 < 23,83).
3. Benchmark quente ≥ 0,4 × Benchmark frio — **errou** em 2 e 4 colunas (0,41; 0,37;
   0,36). A parte das figuras no custo frio da Benchmark é maior do que eu supus;
   o quente (só a detecção refeita) fica abaixo de 40 %.
4. Compare frio 4/1 entre 2,5 e 4,5 — **acertou** (3,74).

Dados brutos: `measure_run.json` (`measure_run.py`, procedimento da PREVISOES §2).

### e1 — interações (Chromium, a partir do zero)

Ponto de partida, não contado: Calibrate, High cutoff cinco passos acima (18 → 48),
"Sample data". Sem essa mudança "Current settings" e "Defaults" seriam a mesma
configuração e T3 não teria o que mostrar — fica declarado como parte do ponto de
partida.

| tarefa | orçamento | previsto | medido (1.63.0 e 1.56.0) |
|---|---|---|---|
| T1 | ≤ 5 | 4 | **4** (menu Compare, Add Current settings, Add Defaults, Run) |
| T2 | ≤ 5 | 4 | **4** (menu Compare, Add Current settings, upload, Run) |
| T3 | ≤ 2 | 1 | **1** (filtro) |
| T4 | ≤ 3 | 1 | **1** (seletor de referência; abrir e escolher contam como uma escolha — são dois cliques físicos) |
| T5 | 0 | 0 | **0** ("To run, add at least one configuration." visível) |

Repetição: `tests/test_compare_browser.py` **10 vezes seguidas sem falha em 1.63.0 e
10 em 1.56.0** (`r1/browser_repeat_*.txt`), contagens idênticas em todas as execuções.
Não variei rede nem CPU porque não houve falha intermitente a diagnosticar.

### e2

- Varredura de todo o texto da Compare (títulos, markdown, legendas, avisos, erros,
  código, rótulos e ajudas de widgets, opções, expanders, tabelas, uploader, link) em
  cinco estados: estado vazio, sem colunas, resultados lado a lado, filtrado +
  empilhado + outra referência, desatualizado. **Nenhum termo encontrado.**
- Controle positivo: o mesmo varredor na página Benchmark acha `train`, `manual
  label`, `swell` (e acha `research/` e `test split` numa string plantada, sem acusar
  "trainee").
- Leitura de rótulos quebrada (`labels_core.read_labels`/`read_split`,
  `benchmark_core.read_labels`/`read_split`/`labels_for_display`/`split_membership`
  levantam erro): a Compare renderiza, adiciona colunas e roda. Controle: com o mesmo
  patch, a página Benchmark falha.

## Portão do I1

| | | evidência |
|---|---|---|
| (a) | **PASS** | `git diff develop -- cyclophaser/` vazio (0 linhas) |
| (b) | **PASS** | `r1/inventory_check.txt`: 34 itens P achados na Compare (0 faltando); a página Benchmark, dirigida pelas mesmas interações nesta árvore e num checkout de `39e658c` (cada um no seu processo), dá widgets, textos, tabelas, resultados por célula, nº de imagens e expanders **idênticos**; `tests/test_benchmark_apptest.py` passa sem alteração; PNGs da Benchmark idênticos byte a byte aos de `39e658c` (teste) |
| (c) | **PASS** | tabela de suítes acima |
| (d) | **PENDENTE — checkpoint** | capturas em `research/benchmark_review/i1/captures/` (abaixo); nenhum commit de interface |
| (e) | e1 e e2 **PASS**; e3 pendente (acontece no checkpoint) | acima |
| (f) | **PASS, com uma leitura a confirmar** | todo número diz o conjunto ("Over the N selected track(s) of the last run", "k of N") e a referência ("Relative to X", "not relative to X"); nenhum rótulo lido (teste e2). A Compare roda sobre os tracks que a Calibrate carrega — com "Sample data", os 51, **inclusive os 16 do split de teste** — sem nenhum rótulo e sem pontuação. Leio "nenhum cálculo sobre o split de teste" como "nenhuma pontuação contra rótulo do split de teste"; se a intenção for outra, é decisão sua |
| (g) | declarado | o I1 **não chega ao público sozinho**; a frente exige o release **2.1.2** no fim. Versão não tocada |

**Resultado: o portão não está completo** — (d) e (e3) dependem do checkpoint.

## Checkpoint (d) — capturas

`research/benchmark_review/i1/captures/` (Chromium 1600×1000, streamlit 1.63.0, app
público; `manifest.json`, nenhum erro de navegador):

- `01_empty.png` — sem tracks, link para Calibrate
- `02_run_blocked.png` — tracks, nenhuma coluna, motivo visível
- `03_columns.png` — Current settings, Defaults e um YAML enviado
- `04_results.png` — tabela relativa e contagens por configuração
- `05_side_by_side.png`, `06_stacked.png`, `07_filter.png`, `08_reference.png`
- `full_page.png` — **afirmado na rodada 1 como a página inteira, e não era**: a
  verificação independente achou o arquivo idêntico byte a byte a `04_results.png`
  (md5 `b6f496ab…`, 1600×1000). O Streamlit rola o seu contêiner principal, não o
  documento, e `full_page=True` sozinho captura só a viewport. Corrigido na rodada 2.

## Achados novos

- **A11** (registrado no DECISIONS): na Benchmark, track enviado perde o eixo de
  tempo. Medido nesta rodada: com as defaults do pacote (`use_smoothing: False`) isso
  **não muda nada**; muda com suavização 'auto' (o teste de controle mostra ≥ 1 track
  com fases diferentes). 5 dos 51 tracks de amostra têm mais de 8 dias.
- **A12** — a Benchmark antiga perde seus valores de widget numa ida à Calibrate no
  navegador: o modo "Exploration" volta para "Validation", **em 1.56.0 e em 1.63.0**
  (sondado em Chromium). Mesmo mecanismo da decisão 4. Não corrigido (a Benchmark não
  muda no I1); a página Validate (I2) deve nascer com a mesma correção da Compare.

## Proposta de limite de colunas

O custo frio cresce linear: ~2,8 s por coluna para 51 tracks (3,04 → 5,82 → 11,37 s),
e o quente fica abaixo de 0,4 s com 4 colunas. O tempo não é o que limita; a leitura
é: os cartões vão 4 por linha, e no layout lado a lado cada figura com 4 colunas tem
~280 px de largura (com 6, ~190 px). **Proposta: limite de 4 colunas**, com o botão
de adicionar desabilitado e o motivo em texto visível ao chegar nele. Alternativa: 6,
aceitando figuras estreitas. Decisão sua.

## Pedidos ao Danilo no checkpoint

1. Aprovar ou corrigir a interface (capturas) e fazer o percurso e3 (T1–T5).
2. Problemas que eu mesmo vi nas capturas, sem corrigir (corrigir agora invalidaria
   as evidências já rodadas):
   - a tabela "Differs from …" dentro dos cartões fica apertada: valores cortados
     (`'ed…`, `this configu…`);
   - depois de rolar até as figuras, o seletor de referência fica longe (T4 continua
     em 1 interação, mas exige rolar);
   - o YAML de calibração mostra "1 key(s) absent … phase_params.prominence=None" — é
     a mesma regra e a mesma frase da Calibrate, mas é ruído para um arquivo
     exportado com `prominence_relative`.
3. Limite de colunas (acima).
4. Leitura de (f) sobre os tracks do split de teste.
5. Decisões de construção 1–5 acima.

## Mudanças não commitadas (aguardando aprovação)

Rastreados: `tools/calibration_app/app.py`, `benchmark_core.py` (docstring),
`benchmark_tab.py`. Novos: os 5 módulos e a página listados acima, 3 arquivos de
teste, e em `research/benchmark_review/i1/`: scripts (`measure_run.py`,
`check_inventory.py`, `capture_screenshots.py`, `run_suite.sh`, `run_browser.sh`,
`run_repeat_browser.sh`), saídas (`measure_run.json`, `r1/inventory_check.txt`,
`suite_*.txt`, `browser_*.txt`, `ci_recipe_*`), `captures/` e este relatório. A
receita do CI foi rodada com `research/app_redesign/i1/run_ci_recipe.sh`
(`OUT_DIR=research/benchmark_review/i1`).

---

# Rodada 2 — correções do checkpoint (d) da rodada 1

## Decisões do Danilo no checkpoint da rodada 1 (2026-10-08)

- Corrigir antes do commit da interface os três problemas relatados (abaixo).
- Limite de colunas: **4**.
- Leitura de (f) aceita: nenhuma pontuação contra rótulo; detecção sem rótulo nos 51
  tracks de amostra é permitida.
- A12: a Benchmark antiga não é corrigida (sai no I3); a Validate do I2 nasce com a
  correção.

## e3 — percurso do Danilo (registro)

Data: 2026-10-08. Ponto de partida: Calibrate com "Sample data" e High cutoff 48.
T1–T5: tudo certo. Um problema relatado: **não fica claro o que "Invert" faz.**
Correção: rótulo "Invert selection" e ajuda "Selects the tracks that are not selected
and clears the ones that are." (só na Compare; a Benchmark mantém "Invert").

## Achado da verificação independente

`full_page.png` da rodada 1 era cópia de `04_results.png` (corrigido na seção da
rodada 1 acima). Agora o script deixa a viewport tão alta quanto o conteúdo antes de
capturar: **`full_page.png` = 1600 × 6258 px** (do título ao último track da página
1, com 3 colunas). O `manifest.json` traz as dimensões reais de cada arquivo, lidas
do cabeçalho PNG.

## Previsão

`research/benchmark_review/i1/PREVISOES_r2.md`, commit **`cfd3a87`**
(2026-10-08T23:14:43Z), enviado. Primeira medição desta rodada: capturas, depois a
suíte conda às 23:22:12Z.

## Mudanças

1. Cartão: diferenças como lista, uma linha por parâmetro, "`section.key`: este →
   referência", com quebra de linha em nomes e valores longos (mesmo conteúdo de
   `compare_core.config_differences`).
2. Seletor "Reference" no topo de "4 · Results", visível com ≥ 1 coluna, antes e
   depois do Run. A referência é resolvida antes dos cartões (que medem a partir
   dela); mesma chave e mesma regra `_restore`/`_remember`.
3. `config_text.filled_keys_sentence` lista só as chaves completadas que diferem do
   default atual do pacote (`filled_keys_that_matter`: `benchmark_core.current_defaults`,
   tolerância de `compare_core._same`, `package_use_filter`), e diz o default de cada
   uma. Vale para a Compare e para a importação de YAML da Calibrate (que agora não
   mostra o aviso quando a frase fica vazia). `fill_missing` e a lista `filled` não
   mudam. Com params-track o aviso some (só faltava `prominence`, None = default);
   `prominence_relative` ausente continua listado (None, default 0.3).
4. Limite de 4 colunas: "Add Current settings", "Add Defaults" e o upload
   desabilitados, com "4 configurations is the limit: remove one to add another." em
   texto visível; `_append` também recusa acima do limite.
5. "Invert selection" + ajuda (e3).
6. Captura de página inteira de verdade; manifest com dimensões.

## Previsão × medido

| execução | previsto | medido | arquivo |
|---|---|---|---|
| conda, streamlit 1.63.0 | 1520 / 0 | **1520 / 0** | `suite_conda_st1.63.0.txt` |
| venv, streamlit 1.56.0 | 1520 / 0 | **1520 / 0** | `suite_st1.56.0.txt` |
| CI, wheel | 1280 / 0 | **1280 / 0** | `ci_recipe_summary.json` |
| CI, source tree | 1 / 0 | **1 / 0** | idem |
| Chromium 1.63.0 | 11 / 0 | **11 / 0** | `browser_conda_st1.63.0.txt` |
| Chromium 1.56.0 | 11 / 0 | **11 / 0** | `browser_st1.56.0.txt` |

`which python` (Python base) e `cyclophaser.__file__` (afirmado no repositório)
registrados no topo de cada `suite_*.txt`. `tests/test_label_browser.py` não foi
rodado.

**Testes existentes alterados:** previsto "nenhum em `develop`; entre os novos da
rodada 1, só `test_the_filled_keys_sentence_is_one_function_for_both_pages`".
Medido: **igual**. `git diff develop -- tests/` só lista os três arquivos novos;
dentro deles, só aquele teste mudou (a frase esperada). **Testes novos: 5**, como
previsto (1 em `test_compare_core.py`, 4 em `test_compare_apptest.py`). Nenhum teste
de navegador novo ou alterado.

**Desvio fora dos testes:** a previsão dizia que `check_inventory.py` mudaria só pelo
item 1. Mudou também pelo item 3: na primeira execução desta rodada o inventário deu
**FAIL** (1 item: "card: filled keys"), porque o cenário do script removia
`boundary_padding`, completado com `'reflect'` = default do pacote, que pela regra
nova não é mais listado. O app estava certo; o cenário passou a remover
`prominence_relative` e a exigir "prominence_relative=None (package default 0.3)". A
segunda execução deu PASS.

## e1 (Chromium, 1.63.0 e 1.56.0)

| tarefa | orçamento | previsto | medido |
|---|---|---|---|
| T1 | ≤ 5 | 4 | **4** |
| T2 | ≤ 5 | 4 | **4** |
| T3 | ≤ 2 | 1 | **1** |
| T4 | ≤ 3 | 1 | **1** (o seletor agora está logo acima da tabela que ele muda) |
| T5 | 0 | 0 | **0** |

`tests/test_compare_browser.py`: **10/10 em 1.63.0 e 10/10 em 1.56.0**
(`browser_repeat_*.txt`), contagens idênticas em todas.

## e2

O teste de varredura (sem termos proibidos, cinco estados, controle positivo na
Benchmark) e o de leitura de rótulos quebrada passaram nas duas versões, dentro das
suítes acima. Nenhum termo encontrado.

## Portão

| | | evidência |
|---|---|---|
| (a) | **PASS** | `git diff develop -- cyclophaser/` vazio |
| (b) | **PASS** | `inventory_check.txt`: 34 itens P (lista no cartão, "Invert selection", aviso só com `prominence_relative`); a Benchmark nesta árvore e em `39e658c` idêntica em widgets, textos, tabelas, resultados, imagens e expanders. Primeira execução FAIL, explicada acima |
| (c) | **PASS** | tabela acima; 10 repetições por versão |
| (d) | **PENDENTE — checkpoint** | capturas abaixo; nenhum commit de interface |
| (e) | **PASS** | e1 e e2 acima; e3 registrado |
| (f) | **PASS** | todo número diz o conjunto e a referência; nenhum rótulo lido; nenhuma pontuação |
| (g) | declarado | a frente exige o release **2.1.2** no fim; versão não tocada |

## Capturas (checkpoint d)

`research/benchmark_review/i1/captures/` — 1600 × 1000, exceto `full_page.png`
(1600 × 6258); streamlit 1.63.0; nenhum erro de navegador (`manifest.json`):

- `03_columns.png` — cartões com a lista de diferenças; o cartão do params-track sem
  aviso de chaves completadas
- `04_results.png` — seletor "Reference" no topo de "4 · Results"
- `09_filled_warning.png` — 4ª coluna (params-track sem `prominence_relative` e sem
  `boundary_padding`, arquivo temporário escrito pelo script): o aviso lista só
  `prominence_relative=None (package default 0.3)`
- `10_limit.png` — 4 colunas: controles desabilitados, motivo visível
- `11_invert_help.png` — "Invert selection" com a ajuda aberta
- `full_page.png` — a página inteira
- e as demais da rodada 1, refeitas (`01_empty`, `02_run_blocked`, `05`–`08`)

## Checkpoint (d) — aprovado

Aprovação escrita pelo Danilo: "aprovo" (2026-10-08). Com ela: interface, testes
novos e evidências das rodadas 1 e 2 (com `r1/`) commitados em
`feat/benchmark-review` e enviados. Sem merge, sem PR, versão não tocada; o item 35
de `docs/future_work.md` só é escrito no fechamento da frente.

Os resultados da rodada 1 estão em `r1/`; as capturas da rodada 1 não foram
guardadas (substituídas pelas da rodada 2).

## Pendências para o I2

1. A seta do cartão, "este → referência", pode ser lida como "mudou de → para".
   Trocar por uma forma inequívoca (por exemplo "48 (reference: 18)") na Compare e
   na Validate.
2. O aviso de chave completada quebra palavra no meio em coluna estreita
   (cosmético; visível em `09_filled_warning.png`: "prominence_rel / ative").
3. A Validate nasce com a correção de A12 (cópias `_cmp_kept_*` reaplicadas na
   chegada à página), decisão do Danilo na rodada 1.
