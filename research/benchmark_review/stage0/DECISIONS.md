# Revisão da aba Benchmark — etapa 0: decisões, inventário, achados, critério (e)

Frente: `docs/future_work.md` item **35** (próximo número livre, conferido em
`develop` @ `39e658c`: o último item é o 34). Branch `feat/benchmark-review`, criado
de `develop` @ `39e658c`. Etapa 0 aprovada pelo Danilo em 2026-10-08; este arquivo
registra o que foi aprovado, antes de qualquer código de interface.

## Decisão de estrutura

A aba Benchmark mistura duas ferramentas:

1. comparar configurações sobre os tracks do próprio usuário — pública;
2. validar contra os rótulos manuais — de desenvolvedor.

Elas viram duas páginas:

- **"Compare"** — pública, no menu "Calibration", logo depois de Calibrate;
- **"Validate against labels"** — no menu "Developer" (só com a chave de desenvolvedor).

Três incrementos:

| incremento | conteúdo |
|---|---|
| **I1** | página Compare. A Benchmark antiga **não muda de comportamento**; seus testes passam sem alteração. |
| I2 | página Validate against labels. |
| I3 | aposentar a Benchmark antiga; README do app; `docs/calibration_tool.rst`. |

A frente termina com um release **2.1.2** (o I1 sozinho não chega ao público). A
versão não é tocada em nenhum incremento antes disso.

## Decisões para a página Compare (I1)

Interface em inglês.

- **Topo**: título e uma frase com a pergunta que a página responde: o que muda nas
  fases dos meus tracks entre configurações.
- **Dados**: os tracks com que a Calibrate está rodando (amostra, exemplo e uploads).
  A Calibrate publica esse conjunto em `session_state` (`_compare_live_tracks`),
  escrito ao lado dos valores que de fato vão para a detecção, no mesmo padrão de
  `_bench_live_config`. Sem upload próprio. Sem tracks: estado vazio com
  `st.page_link` para Calibrate. Seleção: All / Invert / Clear + escolha individual.
- **Configurações (colunas)**: "Current settings" (de `_bench_live_config`),
  "Defaults" (a MESMA fonte do botão Defaults da Calibrate, sem re-derivar), "Upload
  YAML". Cartão: nome, diferenças vs referência, chaves ignoradas, chaves completadas
  (mesma regra e MESMA redação da importação de YAML da Calibrate — não chamar de
  "current defaults"), Edit, Remove, YAML completo. **Não exibir**: sha256, commit,
  pre-filter-fix, `bad_cases`/`evaluation`, snapshots, `research/labels/configs/`,
  nenhum caminho de repositório.
- **Referência**: seletor entre as colunas; sem opção de rótulo. Trocar a referência
  recalcula só as medidas relativas, sem nova detecção.
- **Resultados** (nenhum rótulo é lido nesta página):
  - tabela "relative to <referência>": sequence changed; boundary shift mediana e
    máx. (só onde a sequência bate); phases appeared / disappeared;
  - fora da tabela relativa, por coluna: "incipient absent (first phase is not
    incipient)" como contagem própria da coluna;
  - cada número diz o conjunto (N tracks selecionados) e a referência;
  - por ciclone: figuras Side by side / Stacked, legenda, erro por célula, nota
    "sequence differs from reference" quando for o caso;
  - checkbox "Show only cyclones whose sequence differs from the reference".
- **Run explícito** (nada recalcula ao editar); bloqueios explicados em texto
  visível; aviso de resultado desatualizado; barra de progresso.
- **Cache entre execuções** (`st.cache_data` ou equivalente) com chave = (sha256 da
  configuração efetiva, sha256 do conteúdo da série), não pelo nome; tamanho
  limitado.
- **Limite de colunas**: não fixar. Propor ao Danilo a partir da medição.
- **Persistência entre páginas**: as chaves da Compare entram em `_PAGE_WIDGET_STATE`.
- **A2**: só a docstring de `benchmark_core.reference_metrics` é corrigida no I1
  (texto); o comportamento da Benchmark antiga fica inalterado.
- Código de figura compartilhado pode ir para um módulo próprio, desde que a
  Benchmark antiga continue com o mesmo comportamento e os mesmos testes.

## Inventário 1-para-1 da Benchmark atual (`benchmark_tab.py` @ `39e658c`)

Destino: **P** = página pública Compare (I1); **D** = página Developer "Validate
against labels" (I2); **aposentado** = não vai para nenhuma das duas. Até o I3 a
Benchmark antiga continua inteira; o destino diz para onde cada função vai, não o que
o I1 remove (o I1 não remove nada).

### Linha de status

| controle | destino | motivo |
|---|---|---|
| linha de status (modo · nº configs · nº ciclones · "ground truth" · referência) | P (nº colunas, nº tracks selecionados, referência) / D (selo "ground truth") | conjunto e referência são o que todo número da Compare precisa declarar; disponibilidade de rótulo é assunto da Validate |

### 1 · Mode

| controle | destino | motivo |
|---|---|---|
| rádio Validation / Exploration | aposentado | as duas ferramentas viram duas páginas; o modo deixa de existir |
| legenda do modo | aposentado | idem |

### 2 · Data

| controle | destino | motivo |
|---|---|---|
| contagem "N selected — real/synthetic/uploaded" | P (N selecionados de M carregados) | conjunto de cada número |
| "Include swell_item30 batch" | D | lote rotulado, ferramenta de validação |
| erro / legenda do lote | D | idem |
| aviso "dropped… Validation offers labelled sources only" | aposentado | sem modo, não há o que descartar |
| botão "All real" | P como "All" | na Compare o conjunto é o da Calibrate; "All" seleciona todos |
| botão "All synthetic" | D | casos sintéticos são de desenvolvedor na Calibrate |
| botão "Train" | D | split é conceito da validação |
| botão "Invert" | P | decisão |
| botão "Clear" | P | decisão |
| "Choose individually" (multiselect) | P | decisão |
| upload de tracks do modo Exploration | aposentado | substituído pelos uploads da Calibrate (A6); a Compare não tem upload próprio |
| "Show manual labels as a first column" | D | rótulo |

### 3 · Configurations

| controle | destino | motivo |
|---|---|---|
| legenda "N × M runs, cached per config × cyclone pair" | P (corrigida) | A3: a legenda atual promete um cache que não existe entre execuções |
| "Add column from current sidebar state" | P como "Current settings" | decisão |
| "From a saved configuration" (`research/labels/configs/`) | D | caminho de repositório; configurações de calibração |
| "From an uploaded YAML" | P como "Upload YAML" | decisão |
| "From a frozen published version" (snapshots) | D | A7: só cobre as 63 séries embutidas |
| seletor de referência, opção "Manual label" | D | A1 |
| seletor de referência, colunas | P | decisão |
| legenda "manual label has no parameters… baseline" | D | só existe por causa do rótulo como referência |
| cartão: nome | P | decisão |
| cartão: sha256 curto · commit | D | proveniência de desenvolvedor; proibido na Compare |
| cartão: aviso pre-filter-fix | D | A5: dispara para qualquer YAML sem `boundary_padding` |
| cartão: legenda de snapshot | D | snapshots são D |
| cartão: "Parameter baseline" | P (como "Reference") | a coluna de referência se identifica |
| cartão: tabela "Differs from <ref>" | P | decisão |
| Provenance 1 · sha256 do YAML | D | proibido na Compare |
| Provenance 2 · commit | D | proibido na Compare |
| Provenance 3 · chaves ignoradas | P | decisão |
| Provenance 4 · chaves completadas | P | decisão (redação da importação de YAML da Calibrate) |
| Provenance 5 · pre-filter-fix | D | A5 |
| anotação histórica (`evaluation.bad_cases_count`) | D | proibido na Compare |
| snapshot congelado | D | A7 |
| configuração completa | P | decisão |
| Edit / Apply | P | decisão |
| Remove | P | decisão |
| Run + bloqueios + aviso de desatualizado + "Nothing has been run yet" | P | decisão |

### 4 · Results

| controle | destino | motivo |
|---|---|---|
| mensagens de "No results yet" | P | decisão |
| painel de pontuação Validation (expander Train split, tabela) | D | rótulo |
| expander "Adjudicated (item 30)" | D | rótulo |
| "Also score the labelled rows" + expander de pontuação (Exploration) | D | rótulo |
| tabela "Relative to reference": Cyclones compared | P ("Tracks compared") | denominador explícito |
| idem: Sequence changed | P | decisão |
| idem: Boundary shift median / max | P | decisão (só onde a sequência bate) |
| idem: Phases appeared / disappeared | P | decisão |
| idem: Refused incipient | P, fora da tabela relativa, renomeado "incipient absent (first phase is not incipient)" | A2: é contagem absoluta da coluna, não distância |
| legenda "Boundary shift is measured only…" | P | decisão |
| "Per cyclone" + rádio Figure layout | P | decisão |
| legenda de fases e curvas | P | decisão |
| cabeçalho por ciclone (id · fonte · split · lote) | P (só o nome do track) / D (fonte, split, lote) | split e lote são de validação |
| figura Stacked / células Side by side | P | decisão |
| erro por célula | P | decisão |
| coluna / painel do rótulo manual | D | rótulo |
| notas por célula ("unlabelled — not scored", sequência vs rótulo, nota de mature) | D | rótulo; na Compare a nota é "sequence differs from reference" |
| "no longer loaded (swell_item30 batch excluded)" | D | lote |

### Novo na Compare (sem equivalente na Benchmark)

Título e frase; estado vazio com link para Calibrate; coluna "Defaults"; filtro
"Show only cyclones whose sequence differs from the reference"; barra de progresso;
cache entre execuções; paginação das figuras por ciclone.

## Achados da etapa 0 (conferidos em `39e658c` antes de usar)

- **A1** — "Manual label" como referência é um terceiro instrumento sem nome contra
  rótulos; com o lote swell ligado, soma rótulos adjudicados com os de treino
  (`benchmark_tab.py`, `ref_results` quando `ref_name == REFERENCE_MANUAL`: usa
  `labels` sem filtrar `is_adjudicated`). Conferido.
- **A2** — `reference_metrics`: `n_refused_incipient` é absoluto, não relativo; a
  docstring diz que coluna vs ela mesma dá tudo zero — falso para essa linha e para
  `n_compared`. Conferido.
- **A3** — cada Run cria um `ColumnRunner` novo (`benchmark_tab.py`, `runner =
  bc.ColumnRunner()` dentro de `if run_clicked`): o cache só deduplica colunas
  idênticas dentro de uma execução; a legenda "cached per config × cyclone pair"
  engana. Sem indicação de progresso. Conferido.
- **A4** — não consta no texto da etapa 0 recebido por esta rodada. Não reconstruído.
- **A5** — o aviso pre-filter-fix dispara para qualquer YAML sem `boundary_padding`
  (`signature_audit`: `"pre_filter_fix": "boundary_padding" not in fp`). Conferido.
- **A6** — a Benchmark não vê os tracks da Calibrate (`_carry_uploads` /
  `_K_KEPT_UPLOADS`); usa `bc.load_all_series()` e o upload próprio. Conferido.
- **A7** — snapshots cobrem só as 63 séries embutidas (`v1.9.4.json` e
  `v2.0.0.json`: 63 registros cada). Conferido.
- **A8** — não consta no texto da etapa 0 recebido por esta rodada. Não reconstruído.
- **A9** — README do app desatualizado: "51 real + 12 synthetic" para Validation
  (linha 302) e "filled by the current default" (linha 258). Conferido.
- **A10** — a página não tem título nem explicação (nenhum `st.title`/`st.header` em
  `benchmark_tab.py`). Conferido.

Achado novo, desta rodada (registrado, não corrigido no I1 — a Benchmark antiga não
muda de comportamento):

- **A11** — na Benchmark, um track enviado pelo upload do modo Exploration perde o
  eixo de tempo: é guardado como `list(ser.values)` e reconstruído como
  `pd.Series(v)` (índice 0..n-1). `process_vorticity` decide a janela `'auto'` do
  Savitzky-Golay pela duração do índice (`index[-1] - index[0] > 8 dias`); com índice
  inteiro essa duração nunca passa de 8 dias, então um track enviado com mais de 8
  dias é suavizado com uma janela diferente da que a Calibrate usa para o mesmo
  arquivo. As séries embutidas não são afetadas (`load_real_series` lê `time` como
  índice). A Compare lê os tracks com o mesmo `track_io.read_track` da Calibrate e
  mantém o índice de tempo; um teste confere que as fases da Compare são as da
  Calibrate para os mesmos tracks.

## Critério de usabilidade (e) — declarado na etapa 0, orçamentos fixos

Interação = clique, escolha em seletor, upload ou digitação. Ponto de partida:
Calibrate com "Sample data" carregado.

| tarefa | orçamento |
|---|---|
| T1 — comparar Current settings × Defaults e ver a tabela relativa | ≤ 5 |
| T2 — enviar um YAML e comparar com Current settings | ≤ 5 |
| T3 — (após T1) ver só os ciclones com sequência diferente e a figura de um | ≤ 2 |
| T4 — (após T1) trocar a referência e ver a tabela atualizada | ≤ 3 |
| T5 — com Run bloqueado, ler o motivo | 0 (texto visível, sem hover) |

- **(e1)** teste Chromium executa T1–T5 a partir do zero e conta interações; teste
  novo de navegador roda 10 vezes seguidas sem falha antes de ser aceito.
- **(e2)** teste pela API pública do AppTest varre todo o texto da Compare e falha se
  achar (palavra inteira, sem diferenciar maiúsculas): `train`, `test split`,
  `adjudicated`, `manual label`, `swell`, `sha256`, `commit`, `bad_cases`,
  `ground truth`, `research/`. E um teste que faz a leitura de rótulos levantar erro e
  prova que a Compare renderiza e roda sem chamá-la.
- **(e3)** percurso do Danilo nas mesmas tarefas no checkpoint (d); cada problema
  corrigido ou com motivo aprovado por ele.

## Portão do I1 — PASS só com (a)–(g); FAIL em qualquer um

- (a) `git diff develop -- cyclophaser/` vazio. Se algo exigir mudar o pacote: PARAR.
- (b) inventário: toda função marcada P existe na Compare; nada da Benchmark antiga
  removido ou alterado em comportamento.
- (c) suíte completa sem falhas no env conda `cyclophaser` (`which python` antes;
  `cyclophaser.__file__` no repo), em streamlit 1.56.0 e 1.63, e na receita do CI.
  Interações em Chromium nas duas versões. `tests/test_label_browser.py` não é rodado.
- (d) checkpoint visual com capturas reais e PAUSA; nenhum commit de interface antes
  da aprovação explícita do Danilo.
- (e) evidência de e1 e e2.
- (f) todo número exibido declara conjunto e referência; nenhum rótulo lido; nenhum
  cálculo sobre o split de teste.
- (g) o relatório declara que o I1 não chega ao público sozinho e que a frente exige o
  release 2.1.2 no fim.
