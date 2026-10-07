# I3 — tela inicial, grade paginada, estatísticas do conjunto

Branch `feat/app-redesign`. Base: 6016486 (ponta do I2). Data: 2026-10-06.

**Previsão commitada e enviada antes de qualquer medição:** 3428512
(`PREVISOES.md`, sozinho no commit). **Nada mais do I3 está commitado:** estamos
na PAUSA do portão (d), pela segunda vez, depois dos ajustes pedidos na primeira
pausa (seção "Ajustes da pausa (d)"). Aguardando a aprovação do Danilo.

## O que mudou (só Calibrate)

1. **Tela inicial** (sem dados), no lugar da linha única do I2:
   - título;
   - duas frases sobre o que o app faz;
   - os 4 passos: carregar tracks, conferir as figuras, ajustar a filtragem se a
     fonte não for TRACK, salvar com Save results;
   - os botões "Try example data" e "Sample data (51 TRACK cyclones)", com chaves
     próprias (`start_example`, `start_sample`) e as mesmas funções dos botões do
     passo 1 (`_load_example`, `_load_sample`);
   - link para a documentação.

   Continua sem nenhuma detecção sem dados.
2. **Grade paginada:**
   - "Tracks per page": 12, 24 ou 48, padrão 12;
   - "◀ Previous", "Page N of M · tracks a–b of T" e "Next ▶" acima da grade, e de
     novo abaixo dela quando há mais de uma página;
   - só as figuras da página são geradas; a detecção roda para todos os tracks;
   - downloads por track e marca de caso ruim valem para os tracks da página;
   - mudar o conjunto carregado volta para a página 1, e trocar o tamanho de
     página mantém o primeiro track da página na tela;
   - `grid_page_size` e `n_cols` entram na preservação de estado do I1/I2.
     Sobrevivem a Grid → Inspector → Grid e à troca de página do app.

   O Inspector não muda.
3. **Estatísticas do conjunto** ("Set statistics"), no fim do modo Grid, abaixo da
   tabela consolidada, em módulo próprio (`tools/calibration_app/set_stats.py`):
   - legenda: "Descriptive statistics of the detected phases — not a quality score.";
   - métricas: Analysed, Failed (com os nomes, se houver) e "Whole cycle, median
     (h)";
   - **cada chave de fase do pacote separada** ("intensification",
     "intensification 2", …, para qualquer fase), com o nome igual ao das figuras
     e dos CSVs;
   - tabela por chave: "Tracks with it (n)", "Tracks with it (%)", "Median
     duration (h)" e "Durations (n)";
   - box com todos os pontos por chave e para o ciclo inteiro, com o n no rótulo;
   - legenda das durações, com quantos tracks entram e quantos ficam fora por não
     ter datas;
   - as **5 sequências mais comuns**: um quadrado por fase, na ordem, com as
     cores das figuras (uma repetição leva a cor da fase base e o número dentro
     do quadrado), os nomes em texto e o número de tracks;
   - o ciclo inteiro vai do início da primeira fase ao fim da última.

   Tudo vem do `periods_dict` já calculado; não há chamada de detecção.
4. **YAML sem a chave de desenvolvedor:**
   - a seção `evaluation` não é restaurada e aparece em "Ignored keys" como
     "evaluation (developer only)";
   - a mensagem passou de "Ignored unknown keys:" para "Ignored keys:";
   - com a chave, nada muda.
5. **Uma fonte de cores de fase no app:** `app.py` lê
   `layer_inspector.PHASE_COLORS`, de onde o Inspector já lia, e não tem mais
   cópia própria.
6. README do app atualizado.

Fora do escopo e intocados: barra lateral (exceto o item 4), Benchmark, Label,
`cyclophaser/`, defaults, params-track, Read the Docs, versão do pacote.

## Ajustes da pausa (d)

1. **Versão.**
   - O pacote foi reinstalado no env conda (`pip install -e .` na raiz).
   - Agora `site-packages` tem `cyclophaser-2.1.0.dist-info`, e
     `importlib.metadata.version("cyclophaser") == "2.1.0"`, mesmo fora do
     repositório.
   - Só o cyclophaser mudou: numpy, scipy, pandas, matplotlib, xarray e
     streamlit continuam com a data de instalação de 2026-09-11.
   - As capturas "antes" (6016486) e "depois" saíram desse env. O script lê da
     página a versão do cabeçalho e a grava no `manifest.json`:

     | capturas | commit servido | versão no cabeçalho | `importlib.metadata` |
     |---|---|---|---|
     | `captures/before/` | 6016486 | **2.1.0** | 2.1.0 |
     | `captures/after/` | 3428512 + árvore do I3 | **2.1.0** | 2.1.0 |

2. **Fases repetidas** (decisão do Danilo): cada chave do pacote é contada
   separada.
   - A soma das ocorrências e a legenda que falava dela foram retiradas.
   - O teste independente passou a calcular os valores esperados por chave.
   - Nos 51 tracks de amostra, **10** têm alguma fase repetida: 20150656,
     20160735, 20180628, 20180733, 20190325, 20190639, 20190691, 20203947,
     20205386 e 20206498.
   - As chaves e o n de tracks com cada uma:

     | chave | n |
     |---|---|
     | intensification | 51 |
     | decay | 50 |
     | mature | 48 |
     | incipient | 20 |
     | decay 2 | 10 |
     | intensification 2 | 9 |
     | mature 2 | 6 |
     | residual | 6 |
     | intensification 3 | 1 |
     | decay 3 | 1 |
     | intensification 4 | 1 |
     | decay 4 | 1 |

3. **Quadrados nas sequências.**
   - Feitos com um `st.markdown(unsafe_allow_html=True)` (tabela HTML nativa do
     Streamlit), sem dependência nova.
   - Cor: `layer_inspector.PHASE_COLORS`, a fonte única.
   - `tests/test_phase_colors.py` (3 testes):
     - compara essa fonte com o `colors_phases` de `cyclophaser/plots.py`, lido do
       arquivo com `ast` (o pacote não é importado nem alterado);
     - confere que `app.py` e `set_stats.py` não redigitam as cores, e que os
       renderizadores do Inspector não definem paleta própria;
     - confere que as cópias das páginas Benchmark e Label, fora do escopo, não
       divergiram.
   - Contraste:
     - o número dentro do quadrado é preto ou branco, o que contrastar mais com o
       preenchimento (razões de 5,0 a 11,6);
     - um contorno cinza-médio mantém os quadrados claros visíveis no fundo claro
       e os escuros no fundo escuro;
     - o texto segue o tema;
     - captura no tema escuro: `stats_sequences_dark.png` (servidor com
       `--theme.base dark`).
4. **`n_cols`** entrou em `_CALIBRATE_KEEP_KEYS`.
   - O teste `test_the_grid_columns_survive_the_inspector_and_a_page_trip` (API
     pública do AppTest) falhou antes da correção (`assert 2 == 3`, depois de Grid
     → Inspector → Grid) e passa depois.
   - Ele também cobre Benchmark → Calibrate.
5. Suítes, inventário, medições e capturas refeitos sobre o código final (abaixo).

Também mudou nos ajustes, por consequência:
- a tabela por fase ganhou colunas e passou a ocupar a largura toda, com altura
  para todas as linhas: com 5 colunas e 12 chaves, ela ficava cortada na coluna
  estreita;
- o gráfico de durações foi para baixo da tabela;
- o box do ciclo inteiro ganhou um tom neutro próprio (#7a809c), porque o cinza
  #555 sumia no tema escuro.

## Previsão × medido (observação, não critério)

`measure_slider.py` gerou `measure_{i2,i3,i3_nostats}.json`, as três na mesma
sessão e em sequência, sem nada concorrendo, sobre o código final. Condições:
- 51 tracks, Grid de 2 colunas, página 1, tamanho 12;
- 5 passos do slider "High cutoff" para valores novos;
- streamlit 1.63.0 (env conda).

| | figuras por passo | detecções por passo | mediana no servidor | bloco de estatísticas (mediana) |
|---|---|---|---|---|
| I2 (6016486) | 51 (os 5 passos) | 51 | 13,27 s | — |
| I3 | **12** (os 5 passos) | 51 | **5,03 s** (×0,38) | 0,016 s |
| I3, estatísticas trocadas por nada | 12 | 51 | 4,96 s | 0 |

Contra a previsão:
1. **Figuras:** 12 em vez de 51, todas de `_render_periods_png`. Confere.
2. **Detecção:** 51 chamadas nas três variantes; as estatísticas não fazem nenhuma
   chamada extra. Confere.
3. **Tempo:** cai de 13,27 s para 5,03 s, ×0,38, abaixo da minha expectativa de
   ≤ 0,6. Confere.
4. **Custo das estatísticas:** 0,016 s por passo (cerca de 0,3 % da mediana),
   contra a expectativa de ≤ 0,5 s e < 10 %. A diferença entre as medianas com e
   sem o bloco é de 0,08 s, dentro do ruído entre passos. Confere.

As rodadas anteriores, feitas antes dos ajustes, deram 13,93 / 5,23 / 5,16 s e
13,21 / 5,04 / 5,03 s. Os números da tabela são os da rodada final.

## Portão

**(a)** `git diff 6016486 -- cyclophaser/`: vazio (0 linhas).

**(b)** `INVENTARIO.md`, gerado por `make_inventory.py` →
`inventory_main.md` + `inventory_main_widgets.md` (refeito sobre o código final).

- 51/51 tracks com as mesmas funções por track antes e depois, somando todas as
  páginas, nos 4 estados com dados:
  - Grid de 2 colunas, com e sem a chave;
  - Grid de 1 coluna, com downloads, passo a passo e diagnóstico;
  - sonda incipiente ligada.
- Nenhuma função por página marcada GONE, e o Inspector ficou idêntico.
- Chaves de widget: nenhuma some, 5 novas. `_DEFAULTS` 45 = 45, sem diferença.
- Única aposentadoria: a linha de tela vazia do I2, que é a aprovada.

**(c)** Execuções finais, em sequência, sobre o código final:

| | streamlit 1.56.0 (piso; venv novo, playwright 1.62.0) | streamlit 1.63.0 (env conda `cyclophaser`) |
|---|---|---|
| testes de app (todos os `test_*apptest*.py` + `test_sidebar_defaults`, `test_sidebar_coverage`, `test_app_passo5_fixes`, `test_app_distance_removed`, `test_app_yaml_null_export`) | **203 passed, 0 failed** (`app_tests_st1.56.0.txt`) | **203 passed, 0 failed** (`app_tests_conda_st1.63.0.txt`) |
| Chromium (`test_label_browser.py` + `test_app_pages_browser.py`) | **37 passed, 0 failed** (`browser_tests_st1.56.0.txt`) | **37 passed, 0 failed** (`browser_tests_conda_st1.63.0.txt`) |

- **Suíte conda completa** (`-m "not browser"`): **1485 passed, 0 failed**
  (`suite_conda_raw.txt`; `cyclophaser.__file__` = árvore de trabalho).
- **Receita do CI** (`research/app_redesign/i1/run_ci_recipe.sh`,
  `OUT_DIR=research/app_redesign/i3`): **1280 passed, 0 failed** contra a wheel, e
  **1 passed, 0 failed** em `source_tree` (`ci_recipe_summary.json`,
  `ci_recipe_raw.txt`). Só o env conda testa o app.
- **`research/labels/manual_labels.yaml`:** o sha256 é o mesmo antes e depois
  (`labels_sha_before.txt` = `labels_sha_after.txt`), e o blob é o de HEAD.

Testes novos:
- `tests/test_calibrate_i3_apptest.py`: 12 testes, 14 casos, só pela API pública;
- `tests/test_phase_colors.py`: 3;
- `tests/test_app_pages_browser.py`: 1, no Chromium.

O que eles cobrem:
- a tela inicial: os 4 passos e o link, só os dois botões dela, nenhuma figura e
  nenhuma chamada a `get_periods`, com controle positivo;
- cada botão da tela inicial tem o mesmo efeito do botão da barra lateral
  (parametrizado: exemplo e amostra);
- só os tracks da página têm figura:
  - 51 detecções, 12 nomes e 12 imagens;
  - a tabela consolidada com 51;
  - com 24 por página, 24 imagens.

  As imagens são contadas por `at.get("image")` + `at.get("imgs")`, porque 1.63
  e 1.56 nomeiam o tipo de forma diferente. No Chromium, conta as imagens no DOM;
- navegação:
  - as 5 páginas cobrem os 51 tracks, uma vez cada;
  - Previous em cima e embaixo funcionam;
  - trocar o conjunto volta à página 1;
- a marca de um track da página 1 sobrevive à página 2, ao Inspector e a
  Benchmark → Calibrate;
- o tamanho de página e o número de colunas sobrevivem ao Inspector e à troca de
  página do app;
- as estatísticas batem com um cálculo independente feito no teste:
  - cada CSV lido com pandas;
  - fases por `determine_periods` + `periods_to_dict` do cyclophaser, por chave
    do pacote, sem juntar e sem usar `set_stats`;
  - compara n analisados e n que falharam, n e % por chave, n e mediana das
    durações por chave, mediana do ciclo, as 5 sequências com contagem e ordem, a
    cor e o número de cada quadrado (cores lidas de `cyclophaser/plots.py`) e
    "0 left out";
  - controles positivos: a amostra tem chave repetida, e há quadrado numerado
    entre as 5;
- as estatísticas não fazem chamada própria de detecção;
- um track sem datas fica fora só das durações, e uma fase repetida é contada
  pela própria chave (função, entrada feita à mão);
- YAML com `evaluation`: sem a chave, marcas não restauradas e o aviso; com a
  chave, restauradas.

Testes existentes ajustados, com o motivo em comentário:
- os quatro pontos que procuravam a linha aposentada passaram a procurar o título
  da tela inicial;
- dois cliques em "Try example data" no Chromium agora procuram o botão só na
  barra lateral (a tela inicial repete o nome);
- `test_track_upload_apptest.py::test_grid_with_filter_on_and_many_cyclones_shows_no_use_filter_warning`
  pedia mais de 50 nomes numa página só. Agora percorre todas as páginas: confere
  os 51 e procura o aviso sob cada track, como antes. A falha da primeira rodada
  foi classificada como TESTE e está guardada em `app_tests_*_before_test_fix.txt`.

**(d)** Capturas em `captures/before/` (6016486) e `captures/after/`:
- viewport 1600×1000, app público, env conda reinstalado (2.1.0 nas duas,
  tabela acima), geradas por `capture_screenshots.py`;
- `start`: antes a linha única, depois a tela inicial;
- `grid_page1`: 51 tracks, topo da grade, com os controles de página;
- `grid_page2`: só depois, porque antes não havia páginas;
- `grid_page1_end`: o fim da página 1. Depois, os controles de baixo; antes, as
  últimas figuras da grade única;
- `stats`: depois, as métricas e a tabela por chave; antes, o fim da página, onde
  não havia bloco;
- só depois:
  - `stats_durations`: o box por chave, com o n;
  - `stats_sequences`: as 5 sequências, com a fase repetida (3ª linha:
    "intensification → mature → decay → intensification 2 → mature 2 → decay 2",
    4 tracks; 5ª linha: "… → decay 2", 1 track);
  - `stats_sequences_dark`: o mesmo no tema escuro.

**PAUSA: nada de commit de interface até a aprovação explícita do Danilo.**

**(e)** Não aplicável (a rodada de usabilidade é o I4).

**(f)** Nada exige release: `cyclophaser/` está intocado. O piso do streamlit fica
em 1.56.0. Além do que o I2 já usava, o I3 usa:
- `st.columns(vertical_alignment=…)`;
- `st.metric(help=…)`, `st.dataframe(height=…)`, `st.plotly_chart`;
- `st.markdown(unsafe_allow_html=True)`;
- plotly, que já era dependência (7.0.0 nos dois ambientes).

Testes de app e Chromium passam inteiros no piso.

## Desvios e por quê

- **As estatísticas ficam só no modo Grid.** A frente pede "abaixo da tabela
  consolidada" e também "O Inspector não muda"; a tabela consolidada só existe no
  Grid.
- **A mediana do ciclo inteiro é uma métrica**, não uma linha da tabela por fase.
  Na tabela, as colunas de n e % dessa linha não teriam valor.
- **Desempate das 5 sequências:** a contagem decide, e o empate fica em ordem
  alfabética do texto. Na amostra, o 5º lugar é um empate de várias sequências com
  1 track cada.
- **Sequências como tabela HTML em markdown**, não `st.dataframe`: o
  `st.dataframe` não desenha quadrados coloridos. A tabela continua legível como
  texto, e o teste a lê pela API pública (`at.main.markdown`).
- **Fonte única de cores:** é `layer_inspector.PHASE_COLORS`, que já existia, não
  uma constante nova. As cópias de Benchmark e Label ficaram, porque essas páginas
  estão fora do escopo; o teste garante que não divergem.
- **"Ignored unknown keys:" → "Ignored keys:".** É a única mudança de texto na
  barra lateral, consequência do item 4.

## Pendências e observações

- O env conda foi reinstalado em modo editável (item 1 dos ajustes). Isso mudou
  só os metadados do cyclophaser no env.
- A venv do piso (streamlit 1.56.0) está no scratch desta sessão e é descartável.

## Retorno da pausa (d)

- **Capturas aprovadas pelo Danilo** (2026-10-06), sem ajuste visual. Nenhuma
  captura foi refeita.
- As suítes finais acima valem para o código commitado. Depois delas só mudaram
  `RELATORIO.md` e `INVENTARIO.md`.
- Commit e push em `feat/app-redesign`, separados por assunto. Sem merge, sem PR.

## Falha intermitente no Chromium (verificação independente, ponta 8e2b052)

A verificação independente rodou o Chromium completo em streamlit 1.56.0 e teve
36 passed e 1 failed:
`test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser`. O console
registrou "Failed to load resource … 404" e "Client Error: Image source error
…/media/<hash>.png". Isolado, o teste passou 3 vezes.

### Diagnóstico (antes de qualquer correção)

**Ferramenta.** O plugin de pytest `diag_paged_grid_plugin.py` e o executor
`run_diag_paged_grid.sh`, ambos em `research/`. O teste e o harness não mudaram.
- O plugin roda o teste real N vezes numa sessão, com o servidor do módulo
  compartilhado.
- Antes do `browser.close()` do teste, ele registra o **estado final** da página:
  espera até 20 s que toda imagem da área central termine (carregada ou falha).
  Para cada imagem que não carregou, pergunta ao servidor o status da URL.
  - 404: figura quebrada de vez, **APP**;
  - 200: só estava atrasada.
- Também registra os erros do console e uma captura de tela.
- Saídas em `diag/` (um `.jsonl` por execução e um resumo).

| execução | rodadas | falhas | estado final das falhas |
|---|---|---|---|
| 1.56.0, normal | 20 | **0** | — |
| 1.63.0 (conda), normal | 20 | **0** | — |
| 1.56.0, imagens com +1500 ms por pedido HTTP | 20 | **20** | 24/24 figuras carregadas, 0 URLs quebradas, nas 20 |
| 1.63.0, imagens com +1500 ms por pedido HTTP | 20 | **20** | 24/24 figuras carregadas, 0 URLs quebradas, nas 20 |

**Por que o atraso.** Nas condições normais a falha não apareceu em 40 rodadas.
A verificação a viu na execução completa, com a máquina mais carregada.
- A variante com atraso usa a emulação de rede do Chromium
  (`Network.emulateNetworkConditions`): cada pedido HTTP, inclusive
  `/media/*.png`, chega 1,5 s depois. O websocket que comanda o app não muda.
- Isso reproduz a condição da hipótese: o teste clica enquanto as figuras da
  página anterior ainda carregam.
- O resultado é a mesma mensagem da verificação ("404" e "Image source error"),
  em 40 de 40.

**Classificação: TESTE.**
- Em todas as 40 falhas, o estado final é íntegro: as 24 figuras da página
  carregam, e nenhuma URL da página final responde 404.
- O erro é transitório. O Streamlit só serve `/media/<hash>.png` enquanto a
  execução que desenhou a figura é a atual. Um clique que começa outra execução
  descarta as figuras da página anterior, e os pedidos ainda em curso dão 404.
  As figuras da nova execução carregam todas.
- Capturas no momento da falha: `diag/before_stress1500_st1.56.0_1.png` e
  `diag/before_stress1500_conda_st1.63.0_1.png`. Guardei uma por versão, porque
  as 40 mostram o mesmo estado final íntegro e somavam 6,8 MB; o registro de
  cada rodada está nos `.jsonl`.

### Correção (só no teste)

O teste agora chama `_settled(lp)` antes de cada clique que reroda o app. Ela
espera a execução terminar (`lp.settle()`) **e** toda imagem da área central
carregar (`complete` e `naturalWidth > 0`).
- Uma figura quebrada de vez nunca satisfaz a espera, então um defeito APP
  futuro falharia por timeout.
- `assert not lp.errors` continua estrito, e nenhum erro foi posto em lista de
  ignorados.
- O app não mudou, e nada do que se vê na tela mudou.

### Depois da correção

| execução | rodadas | falhas |
|---|---|---|
| 1.56.0, normal | 20 | **0** |
| 1.63.0 (conda), normal | 20 | **0** |
| 1.56.0, +1500 ms (a condição que falhava 20/20) | 20 | **0** |
| 1.63.0, +1500 ms (a condição que falhava 20/20) | 20 | **0** |

| | streamlit 1.56.0 | streamlit 1.63.0 (conda) |
|---|---|---|
| Chromium completo | **37 passed, 0 failed** (`browser_tests_st1.56.0.txt`) | **37 passed, 0 failed** (`browser_tests_conda_st1.63.0.txt`) |
| testes de app | **203 passed, 0 failed** (`app_tests_st1.56.0.txt`) | **203 passed, 0 failed** (`app_tests_conda_st1.63.0.txt`) |

`manual_labels.yaml` não foi tocado: 0 linhas de `git status` nos executores do
Chromium.

## Segunda correção da falha intermitente (verificação na ponta 0a2ed3a)

A verificação independente rodou o teste do Chromium isolado em streamlit
1.63.0: 2 falhas em 6 rodadas, com o mesmo "404" e "Client Error: Image source
error". A espera pelas figuras antes de cada clique fechava o caminho reproduzido
com atraso de rede, mas não o de uma máquina com CPU mais lenta.

**Diagnóstico encurtado por decisão do Danilo:** sem o nível de CPU 6×, e 10
rodadas por versão em vez de 20. A execução de 20+20 com 4× e 6× já tinha 35
rodadas com 4× concluídas (20 em 1.56.0 e 15 na conda) quando foi parada, e
todas contam.

### Diagnóstico

O instrumento continua só no diagnóstico; o app commitado não foi tocado.
- `diag_paged_grid_plugin.py` desacelera a CPU do navegador
  (`Emulation.setCPUThrottlingRate`), marca o instante de cada clique do teste
  (`Locator.click`) e de cada resposta 404 de `/media/`.
- `diag_server/sitecustomize.py` entra só no servidor do diagnóstico (via
  `PYTHONPATH` e `DIAG_RUNLOG`) e registra cada execução do script.
- Cada execução é atribuída ao último clique antes dela.

**Ponto cego da primeira versão do contador, corrigido.**
- A primeira versão registrava só o início e o fim de
  `ScriptRunner._run_script`.
- Nas duas versões do Streamlit, um pedido que chega enquanto o script roda
  interrompe a execução, e a seguinte roda **dentro da mesma chamada** (um
  `while True`). Uma execução interrompida mais a seguinte contavam como 1, e
  isso é justamente o caso A.
- O contador corrigido registra também `_on_script_finished`, chamado uma vez por
  execução com o tipo de término (`SCRIPT_STOPPED_FOR_RERUN` se interrompida), e
  a thread de cada evento.
- As contagens das rodadas `before2_*`, `after2_*` e `after3_*` foram feitas com
  a versão cega. Os resultados de passou/falhou delas valem; as contagens de
  execução não. A contagem que decide é a das rodadas `exec_cpu4_*`, abaixo.

**Execuções do script por clique**, contador corrigido, CPU 4×, 10 rodadas por
versão (`diag/exec_cpu4_*`). As 200 execuções registradas terminaram todas em
`SCRIPT_STOPPED_WITH_SUCCESS`: nenhuma interrompida. Nas duas versões:

| controle | execuções por clique |
|---|---|
| Sample data | 1 em todas |
| ⚠️ Mark as bad | 1 em todas |
| Tracks per page → 24 | 1 em todas (abrir a lista: 0) |
| Next ▶ | 1 em todas |
| ◀ Previous | 1 em todas |
| modo → Inspector | 1 em todas |
| modo → Grid | 1 em todas |
| menu → Benchmark | 1 em todas |
| menu → Calibrate | 1 em todas |

Nenhum clique disparou mais de uma execução. No app há três `st.rerun`: no
diálogo de formato customizado, na importação de YAML e no diálogo Save results.
Nenhum fica nos caminhos de grade ou de modo.

**404 antes da correção, com CPU 4×:**
- 1.56.0: 20 rodadas, 0 falhas, 0 respostas 404 de mídia;
- conda: 15 rodadas, 0 falhas, 0 respostas 404 de mídia.

Aqui a falha não se reproduziu antes da correção. A máquina da verificação é
mais lenta em CPU.

**Decisão: caso B.** Todo clique dispara uma execução, e nenhuma é interrompida,
então a corrida é do Streamlit. A melhor evidência do mecanismo veio depois da correção, numa rodada
com CPU 4× na conda em que o 404 aconteceu sem provocação:
- o clique em "Inspector" disparou 1 execução, de +2,94 s a +4,32 s depois do
  clique;
- o 404 de uma figura da grade veio a +4,44 s;
- ou seja, o navegador pediu uma figura da execução anterior logo depois que a
  nova execução terminou e o Streamlit a descartou;
- o estado final tinha 24/24 figuras, todas com status 200.

**Observação sem explicação completa.** Nessa mesma rodada, ainda com o contador
antigo:
- o clique em "Next" ficou com 0 execuções atribuídas;
- o log do servidor tem duas execuções sobrepostas (`START`, `START`, `END`,
  `END`), ou seja, duas threads de script ao mesmo tempo, não uma reexecução
  dentro da mesma chamada;
- o log antigo não registrava a thread, então não dá para dizer mais.

Nas 20 rodadas com o contador novo, que registra a thread, não houve
sobreposição: 100 inícios e 100 términos por versão, alternados. O teste
corrigido não depende disso. Ele só aceita 404 de mídia quando o estado final
está íntegro, e essa rodada passou nessas condições.

### Correção (caso B, só no teste)

`test_the_paged_grid_keeps_page_size_page_and_marks_in_the_browser`, com o
critério escrito no docstring:
- **Estado final, sempre, URL a URL.** Depois que o app termina e todo pedido de
  imagem acaba, as 24 figuras da página final estão carregadas
  (`complete && naturalWidth > 0`). O servidor responde 200 a cada uma das URLs
  delas, perguntado com `fetch`. Uma figura quebrada de vez termina com largura 0
  e reprova o teste.
- **Tolerância única.** Só um erro de console que seja um 404 de uma URL
  `/media/` (`_is_media_404`): o "Failed to load resource … 404" do navegador cuja
  origem é `/media/`, ou o "Image source error - …/media/…" do Streamlit. Ele só
  é tolerado porque o estado final acima é verificado.
- **Todo o resto derruba o teste:** qualquer outro erro de console, qualquer erro
  de página, e qualquer erro que o harness viu e o ouvinte do teste não.
- Não há lista genérica de erros ignorados; o harness não mudou.
- **A espera antes de cada clique** também passou a exigir o número esperado de
  figuras da página atual (12, 24, ou 0 no Inspector), além de todas carregadas.
  Com a CPU 4×, a primeira versão aceitou uma página momentaneamente vazia
  ("toda imagem carregada" é verdade para zero imagens) e falhou com
  `assert 0 == 12` (`diag/after2_cpu4_conda_st1.63.0_8.png`, em que a página
  final mostra as 12 figuras). Foi uma falha de sincronia do teste, e esta mudança
  a corrige.

**Controles do critério**, pelo plugin, sem mudar o teste:
- **tolerância:** sem a espera pelas figuras e com +1500 ms por pedido, os 404 de
  mídia acontecem. Resultado: 3 passed, com 0, 25 e 39 respostas 404 e o estado
  final íntegro (`diag/control_tolerated_media404_conda.jsonl`);
- **erro qualquer:** um `console.error` injetado. Resultado: o teste falha e
  aponta o erro (`diag/control_injected_error_conda.jsonl`).

### Depois da correção

| condição | 1.56.0 | 1.63.0 (conda) |
|---|---|---|
| normal, 10 rodadas | **0 falhas** | **0 falhas** |
| CPU 4×, 10 rodadas | **0 falhas** | **0 falhas** (1 rodada com 404 de mídia tolerado, estado final 24/24 e 200) |
| CPU 4×, 10 rodadas com o contador corrigido (`exec_cpu4_*`) | **0 falhas** | **0 falhas** |

Saídas: `diag/after3_*`. A rodada `after2_*` é a da versão intermediária, que
falhou pela contagem de figuras e foi corrigida acima.

| | streamlit 1.56.0 | streamlit 1.63.0 (conda) |
|---|---|---|
| Chromium completo | **37 passed, 0 failed** | **37 passed, 0 failed** |
| testes de app | **203 passed, 0 failed** | **203 passed, 0 failed** |

O app não mudou, então não há tempo por clique a comparar (isso só valeria no
caso A) nem captura nova. `manual_labels.yaml` não foi tocado.
