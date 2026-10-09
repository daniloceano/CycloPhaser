# I3 — aposentar a Benchmark antiga + documentação: relatório

Frente `docs/future_work.md` item 35 (o item só é escrito no fechamento da frente).
Branch `feat/benchmark-review`, base `c1617a0` (I1 e I2 commitados).

**Estado: PARADO no checkpoint (d).** Commitado e enviado só a previsão (`ae3a6c7`).
Interface, testes, documentação e estas evidências **não estão commitados**.

## Previsão

`PREVISOES.md` + `TESTES.md`, commit **`ae3a6c7`**, 2026-10-09T14:25:15Z, enviado antes
de qualquer código do I3. Primeira medição: a suíte conda, 14:48:14Z. (Entre as duas,
só execuções de construção de arquivos de teste isolados, como no I2.)

## O que mudou (não commitado)

- **Saiu**: `app_pages/benchmark.py`, `benchmark_tab.py`, `tests/test_benchmark_apptest.py`;
  em `app.py`, o import, `_PAGE_BENCHMARK`, a entrada em `_PAGE_WIDGET_STATE` e o item de
  menu. Menu: Calibration = Calibrate, Compare; Developer = Manual labelling, Validate
  against labels. `/benchmark`: comportamento padrão do `st.navigation` (medido abaixo).
- **`benchmark_core.py`**: só a docstring do módulo (quem o usa); nenhuma função mudou.
- **F5**: "sequence: N tracks differ, N tracks with a boundary outside its tolerance ·
  mature: N not within the margin".
- **Textos vivos**: docstrings/comentários de `compare_core`, `compare_tab`,
  `label_overlays`, `package_args`, `phase_figures`, `track_format_ui`, `validate_core`,
  `validate_tab`, `app.py`; e **um texto de interface fora da Validate**: a ajuda do
  controle "Custom track format" da Calibrate perdeu a frase "The Benchmark page's
  Exploration upload uses these same settings."
- **Testes**: como em `TESTES.md` (62 removidos, 13 novos, 1 novo de navegador, os
  alterados listados lá).
- **Documentação**: `tools/calibration_app/README.md` (seções "Compare page" e "Validate
  against labels"; corrigidos o "51 real + 12 synthetic" e o "filled by the current
  default"), `docs/calibration_tool.rst` (Benchmark → Compare, seção curta "Compare",
  menção à validação na frase que já falava de funções de desenvolvedor),
  `CHANGELOG.md` [Unreleased] (Added / Removed / Fixed), `research/labels/README.md` (2
  frases) e `research/snapshots/README.md` (1 frase). Quatro figuras da documentação que
  mostravam "Benchmark" no menu foram regeneradas por `docs/figures/make_app_screenshots.py`:
  `app_start.png`, `app_sidebar.png`, `app_grid.png`, `app_statistics.png` (a quinta,
  `app_save.png`, não mostra o menu e foi restaurada). Elas agora mostram "CycloPhaser
  2.1.1" (versão instalada no env), antes "2.1.0".

## Previsão × medido

| execução | previsto | rodada 1 | **final** | arquivo |
|---|---|---|---|---|
| conda, streamlit 1.63.0 | 1508 / 0 | **1507 / 1** | **1508 / 0** | `suite_conda_st1.63.0.txt` (r1 em `r1/`) |
| venv streamlit 1.56.0 | 1508 / 0 | **1507 / 1** | **1508 / 0** | `suite_st1.56.0.txt` |
| CI, wheel | 1280 / 0 | — | **1280 / 0** | `ci_recipe_summary.json` |
| CI, source tree | 1 / 0 | — | **1 / 0** | idem |
| Chromium 1.63.0 | 15 / 0 | — | **15 / 0** | `browser_conda_st1.63.0.txt` |
| Chromium 1.56.0 | 15 / 0 | — | **15 / 0** | `browser_st1.56.0.txt` |
| repetição (6 testes de navegador novos/alterados) | 10/10 cada | — | **10/10 e 10/10** | `browser_repeat_*.txt` |
| documentação | 0 warnings | — | **0 warnings**, saída 0 | `docs_build_i3_review*.txt` |
| inventário | PASS | **FAIL** | **PASS** | `inventory_check.txt` (r1 em `r1/`) |

`which python` e `cyclophaser.__file__` (no repositório) no topo de cada `suite_*.txt`.
`tests/test_label_browser.py` não foi rodado. `manual_labels.yaml` intocado (0 linhas de
`git status` depois de cada execução de navegador). Testes que gravam arquivos os removem:
`git status` não mostra nada fora do previsto.

Contagem por arquivo medida na construção igual à de `TESTES.md`: navegação 10, Compare
30, Validate 28, `test_validate_core` 13, `test_phase_figures` 4, `test_track_upload` 8,
`test_app_passo5_fixes` 16.

### Desvios registrados (não apagados)

1. **Suíte, rodada 1 (as duas versões): 1507 / 1.** Falhou
   `test_compare_apptest.py::test_e2_compare_renders_and_runs_with_label_reading_broken`,
   na metade de **controle** que eu reescrevi (sob o patch, a Validate deve falhar). Isolado
   passava; depois de qualquer teste da Validate no mesmo processo, falhava (reproduzido
   com o par mínimo). Causa: a população da Validate fica em `st.cache_data`, então os
   leitores de rótulo corrigidos nem são chamados. **Defeito do instrumento**, corrigido
   no teste (`st.cache_data.clear()` antes do controle); a parte da Compare sempre passou.
   As duas suítes foram refeitas inteiras.
2. **Inventário, rodada 1: FAIL.** (a) Três detectores do `i1/check_inventory.py` (rodado
   sem alteração) leem os textos no formato do I1 ("→", `st.warning`), que o I2 trocou
   pelos formatos aprovados; acusaram MISSING para funções presentes (a parte 3 mostra a
   Compare idêntica a `c1617a0`). Acrescentei a parte **1b** no script do I3, que repete as
   três com os formatos atuais (3/3 OK); o script do I1 não foi editado. (b) Na Validate,
   além do F5, diferia o commit do código em execução mostrado na proveniência — diferente
   entre dois checkouts por construção; a normalização passou a incluí-lo. Depois disso:
   PASS. A previsão dizia "34 P presentes pelo script do I1" e "nenhuma diferença depois de
   desfazer só o F5": as duas erraram no instrumento.
3. Construção (antes de medir): o teste da coluna "Current settings" na navegação precisava
   de tracks carregados (a Compare só desenha os botões com tracks); o controle do teste e2
   precisava da chave de desenvolvedor desde o primeiro run (o AppTest 1.63 só troca para
   páginas registradas); o teste de `/benchmark` precisava fechar o aviso modal antes de
   clicar no menu. Corrigidos nos testes.

## e1 (Chromium, as duas versões)

T1 **4**, T2 **4**, T3 **1**, T4 **1**, T5 **0**, T6 **5**, T7 **2**, T8 **1**, T9 **0** —
iguais ao previsto, nas duas versões, dentro dos orçamentos.

## e2 (dentro das suítes, as duas versões)

- Compare: nenhum termo proibido (teste do I1 sem alteração); o varredor acha na Validate
  {train, test split, swell, adjudicated} (medido: também research/ e ground truth); a
  Compare roda com a leitura de rótulos quebrada e a Validate, sob o mesmo patch, falha.
- Validate: nenhum id de teste, nenhum "hit rate"/"accuracy"/"score"; o varredor de ids
  acha os 19 ids gastos na página Manual labelling (≥ 16 exigido); nenhum U+200B nas duas
  páginas.

## Portão do I3

| | | evidência |
|---|---|---|
| (a) | **PASS** | `git diff develop -- cyclophaser/` vazio (0 linhas) |
| (b) | **PASS** | `inventory_check.txt`: P 31 + 3 (1b) presentes, D 24 presentes + 2 REPLACED, 0 faltando; `TESTES.md` completo, toda garantia com teste nomeado; `REFERENCIAS.md`: varredura final **VIVA 0**, 3 AMBÍGUAS (abaixo) |
| (c) | **PASS** (rodada final) | tabela acima; 10/10 em cada versão |
| (d) | **PENDENTE — checkpoint** | capturas abaixo; build local da documentação para revisão; nada de interface ou documentação commitado |
| (e) | e1, e2 **PASS**; e3 pendente | acima |
| (f) | **PASS** | Compare idêntica a `c1617a0` sem normalização; Validate idêntica (células, tabelas, ids, imagens, widgets) depois de desfazer o F5 e o commit em execução; nenhuma pontuação sobre o split de teste |
| (g) | declarado | a frente exige o release **2.1.2** depois do merge; versão não tocada (`docs/conf.py` 2.1.1) |

## Capturas (checkpoint d)

`captures/` — Chromium 1600 × 1000, streamlit 1.63.0; `manifest.json`:

- `01_public_menu.png` — Calibration: Calibrate, Compare; sem Developer
- `02_public_benchmark_address.png` — `/benchmark`: aviso modal do Streamlit "Page not
  found — The page that you have requested does not seem to exist. Running the app's main
  page." sobre a Calibrate; o endereço volta para `/`
- `03_public_after_notice.png` — depois de fechar o aviso
- `04_developer_menu.png` — + Developer: Manual labelling, Validate against labels
- `05_developer_benchmark_address.png` — o mesmo aviso com a chave
- `06_f5_headers.png`, `07_f5_header_open.png` — "sequence: 16 tracks differ, 10 tracks
  with a boundary outside its tolerance · mature: 6 not within the margin"

Erros de navegador no manifesto: só no acesso a `/benchmark` (dois 404 de recurso e a
própria mensagem do Streamlit no console); nenhum `pageerror`, nenhum nos menus e na Validate.

## Documentação para revisão

Build local (checkout limpo de `HEAD` + as mudanças de `docs/` e `tools/calibration_app/`):

    open /private/tmp/claude-501/-Users-danilocoutodesouza-Documents-Programs-and-scripts-CycloPhaser/572ae7dd-46f6-447b-85ad-6703f6f171e9/scratchpad/docs_i3_review/docs/_build/html/calibration_tool.html

Os demais textos (README do app, CHANGELOG, READMEs de research) estão na árvore de
trabalho: `git diff -- tools/calibration_app/README.md CHANGELOG.md research/labels/README.md research/snapshots/README.md`.

## Achados novos

- **F6** — `/benchmark` não cai em silêncio: o Streamlit mostra um aviso modal "Page not
  found" e loga dois 404 no console antes de abrir a Calibrate. É o comportamento padrão
  pedido; quem tiver o link antigo vê o aviso uma vez.
- **F7** — os controles do inventário e do e2 que dependiam da página Benchmark ficaram
  sem alvo natural; foram trocados pela Validate e pela Manual labelling. O controle de
  palavras proibidas da Validate ("hit rate") agora só tem textos plantados: nenhuma página
  do app mostra essas palavras.

## Pedidos ao Danilo

1. Checkpoint (d): aprovar ou corrigir os menus, o cabeçalho F5 e `/benchmark` (capturas)
   e a documentação (build local + diffs). Percurso e3.
2. **Mature no F5**: o briefing só mudou as duas contagens de sequência; "mature: 6 not
   within the margin" também conta tracks. Escrever "6 tracks not within the margin"?
3. **Referências ambíguas** (não alteradas; `REFERENCIAS.md`):
   - `research/labels/README.md:119` — "`pair_by_overlap` and `MARGIN`, which the Benchmark
     imports" (fala do import, num registro do item 31);
   - `research/snapshots/make_published_snapshot.py:4` — "the generator behind the
     Benchmark tab's reference columns" (docstring de script, fora da lista do briefing);
   - `tools/calibration_app/benchmark_core.py:559-570` — docstring de `scoreable` cita o modo
     Exploration e `tests/test_benchmark_apptest.py` (o briefing restringiu
     `benchmark_core` à docstring do módulo).
4. **CHANGELOG, "Fixed" R1**: o U+200B nasceu e morreu dentro desta frente (nunca
   publicado). Escrevi a entrada pelo comportamento ("wrap only after '.' or '_' … a name
   copied is exactly the name"). Manter em Fixed, mover para Added, ou tirar?
5. A ajuda do "Custom track format" na Calibrate mudou (frase removida) — único texto de
   interface pública alterado além do menu.

---

# Fechamento do I3

## Checkpoint (d) — aprovado

Aprovação visual (d), escrita pelo Danilo: "sim". Aprovação da documentação (build
local do Read the Docs), escrita pelo Danilo: "sim" (2026-10-09).

## Ajustes aprovados (só texto), aplicados

1. **F5, mature**: "mature: N tracks not within the margin" (`validate_tab.py`; o teste
   `test_disagreeing_tracks_listed_per_column_and_instrument` acompanha). As capturas
   06/07 são de antes deste ajuste.
2. **Referências ambíguas**: `research/labels/README.md:119` fica como está (registro do
   item 31); a docstring de `research/snapshots/make_published_snapshot.py` cita a página
   Validate against labels (os snapshots não guardam hash do gerador); a docstring de
   `benchmark_core.scoreable` deixa de apontar para `tests/test_benchmark_apptest.py` e
   cita `tests/test_validate_core.py::test_an_unlabelled_row_is_never_scored` (nenhum
   código mudou). `sweep_references.py` registra a decisão (`DECIDED`) e
   `REFERENCIAS.md` foi regenerado: **VIVA 0, AMBÍGUA 0**.
3. **CHANGELOG, Fixed**: fica a quebra só depois de "." ou "_"; saiu a frase do nome
   copiado (R1 nunca publicado); o item do track sem eixo de tempo diz "with smoothing set
   to 'auto'" (A11 do I1: com os defaults do pacote nada muda).
4. **Pendência para o release** (registrada abaixo).

As saídas do checkpoint da receita do CI foram movidas para `checkpoint/`; as demais
saídas pós-ajustes têm o sufixo `_pos_ajustes`.

## Resultados pós-ajustes (argumentos explícitos)

| execução | resultado | arquivo |
|---|---|---|
| conda `cyclophaser`, streamlit 1.63.0, `-m "not browser"` | **1508 passed / 0 failed** | `suite_conda_st1.63.0_pos_ajustes.txt` |
| venv streamlit 1.56.0, mesmo comando | **1508 / 0** | `suite_st1.56.0_pos_ajustes.txt` |
| receita do CI, wheel | **1280 / 0** | `ci_recipe_summary.json` (checkpoint: `checkpoint/`) |
| receita do CI, source tree | **1 / 0** | idem |
| Chromium `tests/test_validate_browser.py`, 1.63.0 | **3 / 0**; e1 T6 5, T7 2, T8 1, T9 0 | `browser_validate_conda_st1.63.0_pos_ajustes.txt` |
| idem, 1.56.0 | **3 / 0**; e1 igual | `browser_validate_st1.56.0_pos_ajustes.txt` |
| documentação, checkout limpo | **0 warnings**, saída 0 | `docs_build_pos_ajustes*.txt` |

`which python` e `cyclophaser.__file__` no topo de cada `suite_*`. `manual_labels.yaml`
intocado. `tests/test_label_browser.py` não foi rodado. Com tudo passando, interface,
testes, documentação e evidências do I3 foram commitados em `feat/benchmark-review` e
enviados. Sem merge, sem PR, versão não tocada; o item 35 de `docs/future_work.md` ainda
não foi escrito.

## Pendências para o merge e o release

- **Merge** de `feat/benchmark-review` em `develop`: só com autorização escrita do
  Danilo; nunca por PR.
- **Release 2.1.2** depois do merge (a frente exige): aumento de versão, e então
  **regenerar as 4 figuras** de `docs/generated/` (`app_start.png`, `app_sidebar.png`,
  `app_grid.png`, `app_statistics.png`) com `docs/figures/make_app_screenshots.py`, para
  mostrarem a versão publicada (hoje mostram 2.1.1, a instalada no env).
- **Item 35** de `docs/future_work.md`: escrito no fechamento da frente.
