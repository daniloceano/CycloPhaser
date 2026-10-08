# I1 — navegação por páginas, tema, página Label, Benchmark sem painel de teste

Branch `feat/app-redesign` (de `origin/develop` @ d339c7d). **Nada commitado:** PAUSA
do portão (d), aguardando aprovação do Danilo. Data: 2026-10-05.

## O que mudou

- **Páginas** (`st.navigation` + `st.Page`, ícones Material): seção "Calibration" com
  Calibrate (padrão) e Benchmark; seção "Developer" com Manual labelling, só com a
  chave. Entrada continua `tools/calibration_app/app.py`. O corpo de Calibrate segue
  inline no app.py (as declarações que os testes leem do fonte ficaram no lugar);
  para outra página o app.py executa o arquivo da página e chama `st.stop()`, então
  o laço de detecção de Calibrate não roda. Arquivos: `app_pages/{calibrate,benchmark,label}.py`.
- **Chave de desenvolvedor:** `CYCLOPHASER_APP_DEV=1` ou `developer_mode = true` em
  `st.secrets`. Sem arquivo de secrets não há erro: `st.secrets.load_if_toml_exists()`
  primeiro, qualquer exceção = desligado. `.streamlit/secrets.toml` entrou no `.gitignore`.
- **Tema:** `.streamlit/config.toml` na **raiz**: `baseRadius = "12px"`,
  `[theme.sidebar]` escura (cores do app de referência), sem a fonte externa dele.
- **Página Manual labelling:** decisões de 2c9ab1d reimplementadas sobre o código atual,
  sem cherry-pick: (i) sem seletor Inspection/Labelling; (ii) overlays sempre
  disponíveis, revelar registra em `overlays_shown` e a linha de status vira
  "👁 overlays revealed"; (iii) overlays em min-máx sobre a faixa da série bruta, só
  na exibição; (iv) o gráfico só se acomoda quando tem tamanho real (ResizeObserver).
  O campo "Default ± steps" saiu da barra lateral para a página. Overlays usam os
  filtros da barra lateral de Calibrate (como antes), lidos de `_bench_live_config`;
  sem Calibrate na sessão, os defaults da assinatura, e a ajuda diz qual.
- **Benchmark:** página própria; sem painel "Test split (frozen)" e sem botão "Test".
- **Calibrate:** seletor de modo perdeu "Label". Inspector, marcação de caso ruim,
  sintéticos e textos inalterados.

### Interpretação a confirmar: decisão (iii)
2c9ab1d normalizava cada overlay sozinho. O item 30c (posterior) passou a escalar as
três camadas **juntas** para não apagar a amplitude que cada passada remove. Fiz as
duas coisas valerem: as três camadas juntas, mapeadas para [mín, máx] da série bruta,
em unidades da bruta. A caixa "Shared 0-1 scale" virou o rádio "Overlay scale":
**Raw range** (padrão, decisão iii), **Shared 0-1** (30c, mantido) e **Physical** (o
antigo desligado). Se a intenção era por curva, é uma linha em `_overlay_controls`.

## Preservação de estado entre páginas (item 4) — mecanismo

O Streamlit apaga o estado dos widgets não desenhados na execução. `app.py` lista as
chaves de widget de cada página (`_PAGE_WIDGET_STATE`: chaves de `_DEFAULTS` + dados
de Calibrate + prefixos `badcase__` e `track_custom_`; as do Benchmark; as da Label)
e, em `_keep_page_state`, reescreve `st.session_state[k] = st.session_state[k]`:

1. **a cada execução, para as páginas que não estão abertas** — tira as chaves da limpeza;
2. **na primeira execução da página em que o usuário acabou de chegar, para as
   chaves dela** — sem isso o servidor guardava o valor certo, mas o navegador
   redesenhava o widget com o default de `value=`/`index=` e o clique seguinte
   devolvia o default. Achado no Chromium (o YAML importado voltava a `reflect`);
   o AppTest não tem o lado do navegador e passava. Controle negativo: desligar só
   esta escrita faz os dois testes de navegador falharem.

Uploads não voltam por chave: `_carry_uploads` guarda as faixas aceitas e as reaplica
quando o uploader volta vazio por troca de página (não quando o usuário o esvazia),
com legenda e botão "Forget them". O YAML: os valores são chaves de widget e a
mensagem "Loaded N parameters" é estado de usuário; ambos ficam.

"Add column from current sidebar state" lê `_bench_live_config`, que Calibrate publica
a cada execução, e por isso reflete a barra lateral. Antes de Calibrate rodar na
sessão (URL direta para /benchmark) o botão fica desabilitado com o motivo: um
documento vazio seria preenchido com os defaults congelados pré-item-31.

Custo conhecido, resolvido pelo piso: o valor escrito na mesma execução de um widget
com default dispara o aviso do Streamlit "created with a default value but also had
its value set via the Session State API". Até 1.55 ele aparecia como caixa amarela na
página (uma vez por processo); desde **1.56.0** vai só para o log. Por isso o piso do
app é 1.56.0 (portão f). O bloco de preset sintético do develop já disparava o mesmo
aviso.

## Benchmark: nenhuma pontuação contra rótulo de teste

Além do painel, pontuavam séries de teste: as notas por célula ("sequence: match/
differs", deslocamento do maduro), o bloco "Adjudicated" e, em Exploration, as
métricas contra a referência "Manual label". Regra aplicada na fonte: os rótulos do
split de teste (16 + os 3 de teste do lote swell) são **retidos na página inteira**.
Consequências: **Validation não oferece mais as séries de teste** (47 selecionáveis,
54 com o lote); em Exploration uma série de teste roda como não rotulada, comparada
à coluna de referência e nunca pontuada. Teste com controle positivo: com o rótulo não
retido, a mesma corrida compararia as duas séries.

## Portão

**(a)** `git diff origin/develop -- cyclophaser/`: vazio (0 bytes).

**(b)** `INVENTARIO.md` + `check_inventory.py` → `inventory_check.txt`. Sumiram só as
quatro aposentadorias aprovadas (`_mode_switch` e suas chaves; `bench_pick_test`; o
painel de teste; "Label" de `_VIEW_MODES`), mais `lab_overlay_shared__…`, substituída
por `lab_overlay_scale__…` (a opção 0-1 continua lá). Movidas: `_LABEL_OVERLAY_STYLE`,
`_label_overlays` → `label_overlays.py`; `label_default_tolerance` → página Label.

**(c)** Suíte:
- env conda `cyclophaser` (`which python` = env; `cyclophaser.__file__` = árvore do
  repo; streamlit 1.63.0), `-m "not browser"`: **1456 passed, 0 failed** (`suite_conda_raw.txt`).
- receita do CI (`run_ci_recipe.sh`: worktree limpo de HEAD + patch da árvore de
  trabalho, venv novo 3.12, wheel construída, comandos do `.circleci/config.yml`):
  **1278 passed, 0 failed** contra a wheel (`cyclophaser.__file__` no site-packages)
  e **1 passed, 0 failed** em `-m source_tree` (`ci_recipe_raw.txt`, `ci_recipe_summary.json`).
- Chromium (`browser_raw.txt`): `tests/test_label_browser.py` + `tests/test_app_pages_browser.py`:
  **34 passed, 0 failed**.

Testes novos: `tests/test_app_navigation_apptest.py` (AppTest, API pública:
`switch_page` só alcança página registrada): menu com Calibrate e Benchmark; Developer
ausente sem chave, com `developer_mode = false`, presente com o segredo e com a
variável; barra lateral, dados e marca preservados após Benchmark→Calibrate, com
**controle negativo** (cópia do app sem `_keep_page_state` perde); coluna da barra
lateral reflete Calibrate, inclusive após nova mudança; Validation sem teste;
Exploration roda série de teste sem pontuar. `tests/test_app_pages_browser.py`
(Chromium): menu público sem Developer; menu com a chave; **Label: arrastar fronteira,
revelar `vorticity_smoothed2`, salvar** — gravação numa cópia temporária
(`AppServer(labels_path=…)` aponta `labels_core.LABELS_PATH` para a cópia dentro do
processo do servidor); confere `start_idx` arrastado e `overlays_shown ==
["vorticity_smoothed2"]` no registro salvo, sha256 do arquivo real igual antes e
depois e `git status` dele vazio; upload + YAML sobrevivem a duas viagens; barra
lateral alterada pela UI sobrevive a duas viagens e a um clique depois.

`git status --porcelain research/labels/manual_labels.yaml`: vazio; sha256 35a61fd2…
antes e depois de todas as execuções.

Testes existentes ajustados à estrutura nova (cada mudança comentada no arquivo):
`test_label_apptest.py` (entra pela página; o gatilho de rerun cedo que o modo dava
agora vem da tabela; "Shared 0-1 scale" → "Overlay scale"), `test_benchmark_apptest.py`
e `test_app_passo5_fixes.py` (Calibrate→Benchmark; 63→47 e 73→54 em Validation; botão
Test aposentado), `test_inspector_apptest.py`, `test_sidebar_defaults.py`,
`test_track_upload_apptest.py`, `browser_harness.py`.

**Achado pré-existente corrigido no harness:** `tests/test_label_browser.py` falhava
no **develop** (d339c7d: 16 failed, 5 passed, 8 errors, mesmo ambiente). A página abre
no primeiro caso não rotulado; desde o item 30 a fila termina no lote de validação
gasto, e esse caso (19960808) tem 30 passos, enquanto as fixtures digitam posições até
100. `LabelPage.open` agora avança (Next ▸, que nunca salva) até um caso destravado de
≥110 passos.

**(d)** Capturas em `captures/before/` e `captures/after/` (`calibrate.png`,
`benchmark.png`, `label.png`, `manifest.json`), viewport 1600×1000, geradas por
`capture_screenshots.py`. Pedidas depois, mesmo script com `--extras`, em
`captures/after_extras/`: `label_full.png` (página Manual labelling de cima a baixo;
viewport 1600 de largura com a altura do conteúdo, 1561 px, porque o Streamlit rola
dentro do próprio contêiner e um full-page daria só uma tela) e `calibrate_public.png`
(sem a chave; o script falha se o menu tiver "Developer" ou "Manual labelling"; menu
registrado no manifest: Calibration | Calibrate | Benchmark). **PAUSA: aguardando
aprovação do Danilo.** — **Aprovado pelo Danilo** no retorno da pausa, com três
ajustes antes do commit (registrados em "Retorno da pausa (d)", abaixo).

**(e)** Não aplicável (rodada de usabilidade é o I4).

**(f)** Nada exige release do pacote: `cyclophaser/` intocado. Só muda o piso do
streamlit do app: **`streamlit>=1.56.0`** em `tools/calibration_app/requirements.txt`,
e o mesmo valor em `environment.yml` (era `>=1.30`).

Fonte do piso: notas de versão 1.56.0 (31 mar 2026), "Widget state duplication
warnings are now logged to the console instead of displayed in the app UI"
(streamlit#14141) — https://docs.streamlit.io/develop/quick-reference/release-notes/2026.
Conferido nos wheels: `elements/lib/policies.py` chama `st.warning` em 1.44.0, 1.46.0,
1.50.0, 1.53.0, 1.54.0 e 1.55.0, e só `_LOGGER.warning` em 1.56.0, 1.58.0 e 1.60.0.

As outras funções usadas são mais antigas e ficam cobertas: `[theme.sidebar]` desde
1.44.0 (notas de versão do GitHub 1.44.0, "support `theme.sidebar` custom theme",
streamlit#10772; ausente no wheel 1.43.2); seções em `st.navigation` e ícones Material
em `st.Page` desde 1.36.0. O comentário ">=2.0.0" virou ">=2.1.0, the floor below".
(A primeira versão deste relatório propunha 1.44.0; o piso subiu no retorno da pausa.)

## Onde o Cloud lê o config.toml

Na raiz do repositório: "When your entrypoint file is in a subdirectory, the
configuration file must stay at the root" e "On Community Cloud, the working directory
is always the root of your repository" —
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization.
Por isso o tema está em `/.streamlit/config.toml`. Localmente o streamlit 1.63 também
lê `.streamlit/` ao lado do script; os READMEs passaram a rodar o app da raiz.
`docs/calibration_tool.rst` não mudou (ver "Retorno da pausa").

## Previsão × medido (observação, não critério)

`measure_interactions.py`, 51 tracks carregados, 5 repetições, streamlit 1.63.0;
`measure_before.json` (develop d339c7d) e `measure_after.json` (branch).

| Interação | chamadas a `_run_get_periods` antes → depois | mediana servidor antes → depois |
|---|---|---|
| Label, "Next ▸" | 102 → **0** (todas as 5) | 1,60 s → **0,48 s** (×0,30) |
| Benchmark, "Show manual labels…" | 51 → **0** (todas as 5) | 1,01 s → **0,44 s** (×0,43) |

A previsão de PREVISOES.md vale nas duas partes: zero detecção, mediana ≤ 0,5× a de
antes. Antes eram 102 por clique na Label (duas chamadas por track) e não 51; a
previsão dizia "≥ 51". Uma repetição do Benchmark depois levou 1,73 s (as outras
0,34–0,45 s); não investiguei.

## Desvios do escopo e por quê

- **Rodei os testes de navegador**, contra a regra do CLAUDE.md do repo ("Do not run
  the browser tests"), porque a frente exige teste Chromium verificado. Os números
  estão acima; decida se a regra fica como está.
- **Harness do navegador corrigido** (falha pré-existente, acima): sem isso a página
  Label não era verificável no Chromium.
- **Status "👁 overlays revealed" atualiza no mesmo clique:** a linha é desenhada acima
  das caixas e atrasava uma execução (`_overlays_revealed` lê também as caixas).
- **Botão "Add column from current sidebar state" desabilitado** quando Calibrate
  ainda não rodou na sessão (antes não podia acontecer).
- **Docs:** READMEs (rodar da raiz, páginas, regra do teste no Benchmark).

## Pendências

- **Pendência do I2 — perda da marca de caso ruim em Grid → Inspector → Grid.** As
  caixas "⚠️ Mark as bad" só são desenhadas no Grid; enquanto o Inspector está na tela
  o Streamlit limpa o estado delas, e a marca não volta. **Já ocorre na develop**,
  idêntico: `check_badmark_loss.py` → `badmark_evidence.txt`, AppTest em um worktree
  de `origin/develop` @ d339c7d e na branch, mesma saída nas duas ("marked in
  Grid=True | still marked in Inspector=False | still marked back in Grid=False").
  Fora do I1; a marcação de caso ruim é assunto do I2.
- Textos visíveis ainda dizem "tab" (`track_format_ui`, ajuda do upload do Benchmark):
  limpeza de textos é do I2.
- `tools/calibration_app/.streamlit/config.toml` (`gatherUsageStats = false`) não é
  lido pelo Cloud; ficou como estava.
- Abrir `/label` direto na URL faz o frontend procurar `/label/_stcore/health` e
  registrar dois 404 no console antes de achar o servidor; não afeta o app.
- **"Overlay scale" sem aprovação explícita registrada.** O retorno da pausa aprova
  as capturas, que mostram o seletor, mas não diz que aprova a troca da caixa
  "Shared 0-1 scale" pelo rádio. O INVENTARIO.md a lista como substituída, **sem**
  marcá-la como aprovada; falta a palavra do Danilo.
- Texto do checkbox de overlays cortado com "(…" na coluna estreita (visível em
  `captures/after_extras/label_full.png`); texto/layout, para o I2.

## Retorno da pausa (d)

Capturas aprovadas pelo Danilo. Ajustes pedidos antes do commit, aplicados:

1. `docs/calibration_tool.rst` restaurado da develop (`git checkout origin/develop --`):
   o Read the Docs será atualizado uma vez, no fim da frente, com revisão do Danilo num
   build local. `git diff origin/develop -- docs/calibration_tool.rst`: vazio.
2. Piso do streamlit do app subiu para 1.56.0, com fonte (portão f).
3. `environment.yml`: `streamlit>=1.56.0`, mesmo valor.

Suítes rodadas de novo depois dos ajustes: ver `suite_conda_raw.txt`,
`ci_recipe_raw.txt` / `ci_recipe_summary.json` e `browser_raw.txt` (seção final).

## Correção após verificação independente (portão c: FAIL)

**Defeito, nos testes e não no app:** três testes de
`tests/test_app_navigation_apptest.py` falhavam com streamlit 1.56.0 (o piso) e
1.58.0, e passavam só em versões mais novas. Os resultados de (c) acima foram
medidos só com 1.63.0, por isso não pegaram o problema.

1. `…absent_without_the_key` e `…absent_when_the_secret_is_false`: o helper
   `_registered` usava `AppTest.switch_page`, que até pelo menos 1.58 só confere se o
   ARQUIVO existe. Os testes falhavam com o app correto, e o de "presente com a chave"
   ficava vazio nessas versões. Agora `_rendered` troca de página, roda e diz qual
   página DE FATO apareceu, pelo widget que só ela desenha (`view_mode`, `bench_run`,
   `label_default_tolerance`). Sem a chave, ou com o segredo falso, pedir a página
   Label a partir de Calibrate renderiza Calibrate, nas duas versões (a 1.63 recusa a
   troca e fica na página atual; a 1.56 deixa trocar e o `st.navigation` cai na página
   padrão). Com a chave renderiza a Label.
2. `…exploration_runs_a_test_series_but_never_scores_it`: passava ao multiselect os
   rótulos formatados ("20150069 (real/train)"); agora passa os ids, que é o que
   `set_value` recebe em todas as versões (os testes do Benchmark já faziam assim).

**Testes de app em duas versões** (`run_app_tests.sh`; os `test_*apptest*.py` e
`test_sidebar_defaults.py` pedidos, mais os outros três arquivos que usam AppTest:
`test_app_passo5_fixes.py`, `test_app_distance_removed.py`, `test_sidebar_coverage.py`):
- streamlit **1.56.0** (venv novo, Python 3.12.9, `pip check` limpo):
  **173 passed, 0 failed** — `app_tests_st1.56.0.txt`;
- streamlit **1.63.0** (env conda `cyclophaser`): **173 passed, 0 failed** —
  `app_tests_conda_st1.63.0.txt`.

**Suítes de novo, depois da correção:**
- env conda, `-m "not browser"`: **1456 passed, 0 failed** (`suite_conda_raw.txt`);
- receita do CI: **1278 passed, 0 failed** (wheel) e **1 passed, 0 failed**
  (`source_tree`) (`ci_recipe_raw.txt`, `ci_recipe_summary.json`);
- Chromium: **34 passed, 0 failed** (`browser_raw.txt`).

### O que a receita do CI não testa

Na receita do CI não há streamlit, plotly nem playwright (só a wheel, pytest e
pyyaml, de propósito). **Só o env conda testa o app.** A receita tem 36 skips no
passo da wheel (`ci_recipe_summary.json`, por motivo e por arquivo):

| Pulado na receita do CI | Contado como | Testes que contém |
|---|---|---|
| 8 módulos inteiros por `importorskip("streamlit")`: `test_app_distance_removed`, `test_app_navigation_apptest`, `test_benchmark_apptest`, `test_inspector_apptest`, `test_label_apptest`, `test_sidebar_coverage`, `test_sidebar_defaults`, `test_track_upload_apptest` | 8 skips (um por módulo, na coleta) | 152 |
| 2 módulos de navegador, pulados antes por falta de playwright (também exigem streamlit): `test_label_browser`, `test_app_pages_browser` | 2 skips | 34 |
| testes de AppTest em `test_app_passo5_fixes` (sem streamlit) | 6 | 6 |
| testes de `test_manual_labels` que exigem o código do app ("the labelling tab is calibration-app code") | 15 | 15 |
| testes de `test_layer_inspector` que exigem plotly (dependência do app) | 4 | 4 |
| `test_synthetic_lifecycles`, caso observacional (não é do app) | 1 | 1 |

São 35 dos 36 skips ligados ao app, que escondem **211 testes**: 177 que o env conda
roda e os 34 de navegador, que só rodam à mão. Um módulo pulado na coleta conta como
UM skip, por isso o número de skips subestima o que fica de fora. (Contagem válida
para esta receita e este commit: com playwright instalado, os dois módulos de
navegador mudariam de forma, como explica o CLAUDE.md.)

## Segunda correção — testes de Chromium em streamlit 1.56.0 (portão c: FAIL)

**Defeito, nos testes e não no app:** na ponta 8197a46, 3 dos 34 testes de Chromium
davam timeout com streamlit 1.56.0 e passavam com 1.63.0. A rodada anterior em duas
versões cobriu só o AppTest; o Chromium tinha rodado só em 1.63.0.

**Diagnóstico antes da correção** (`diag_chromium/diagnose.py`, capturas e dump dos
controles em `diag_chromium/st1.56.0/` e `diag_chromium/conda_st1.63.0/`, tabela em
`diag_chromium/DIAGNOSTICO.md`). **Os três são TESTE:** em 1.56.0 o controle está na
tela e mostra o valor certo, mas com outra estrutura de DOM.

| Teste | Esperava | Em 1.56.0 | Classe |
|---|---|---|---|
| `test_label_browser::test_the_table_shows_a_row_per_phase` | combobox de nome `phase, row 0` | combobox de nome `Selected incipient. phase, row 0`, `<input>` vazio | TESTE |
| `test_app_pages_browser::test_an_uploaded_track_and_an_imported_yaml_…` | combobox de nome `Boundary padding` | `Selected reflect. Boundary padding`, `<input>` vazio | TESTE |
| `test_app_pages_browser::test_sidebar_values_set_in_the_ui_…` | `<input type="range">` | `<div role="slider">` com `aria-valuenow` (17 sliders, valores certos) | TESTE |

**Correção (só testes; piso inalterado em 1.56.0):** `tests/browser_harness.py`
ganhou `selectbox`, `selectbox_value` e `SLIDER_HANDLE`, que acham e leem os dois
formatos. `LabelPage.phase_name` e `tests/test_app_pages_browser.py` passaram a
usá-los, e o retrato da barra lateral lê os dois tipos de slider. Como não houve caso
APP, o piso não precisou subir e a busca por versões intermediárias não se aplicou.

**No piso final (1.56.0) e no env conda (1.63.0):**

| | streamlit 1.56.0 (venv novo, playwright 1.62.0) | streamlit 1.63.0 (env conda) |
|---|---|---|
| testes de app (`run_app_tests.sh`, 10 arquivos: os 5 `test_*apptest*.py`, `test_sidebar_defaults`, `test_sidebar_coverage`, `test_app_passo5_fixes`, `test_app_distance_removed`, `test_app_yaml_null_export`) | **177 passed, 0 failed** — `app_tests_st1.56.0.txt` | **177 passed, 0 failed** — `app_tests_conda_st1.63.0.txt` |
| 34 de Chromium (`run_browser_tests.sh`) | **34 passed, 0 failed** — `browser_tests_st1.56.0.txt` | **34 passed, 0 failed** — `browser_tests_conda_st1.63.0.txt` |

`research/labels/manual_labels.yaml` continuou intocado nas duas rodadas de navegador.
Depois da correção:
- suíte conda completa, `-m "not browser"`: **1456 passed, 0 failed** (`suite_conda_raw.txt`);
- receita do CI: **1278 passed, 0 failed** (wheel, 36 pulados, a mesma divisão por
  motivo da seção anterior) e **1 passed, 0 failed** (`source_tree`)
  (`ci_recipe_summary.json`, `ci_recipe_raw.txt`).

