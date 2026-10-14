# Etapa 0 — testes do app de calibração no CI: medição e desenho

Branch `ci/app-tests`, criada de `develop` = `origin/develop` = `3f410df`
(conferido). Previsões commitadas e com push antes de qualquer medição:
**`c5174d1`** (= C0, o commit medido em todas as rodadas locais e na linha de
base do CI). Data: 2026-10-13.

**Nada de CI, pacote, `setup.py`, `tests/`, `tools/` ou app foi alterado.** Só há
arquivos novos em `research/ci_app_tests/etapa0/`. Nenhum teste `browser` foi
rodado. Esta etapa para aqui: a implementação depende da aprovação do desenho
pelo Danilo.

## Resumo

| | resultado |
|---|---|
| Wheel (0.1) | 11 arquivos, só `cyclophaser/` + dist-info; sem `tools/`, `research/`, `tests/` |
| CI real (0.2) | pipeline [408](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/408), job [516](https://circleci.com/gh/daniloceano/CycloPhaser/516), só `build_test`, success, 155,6 s; wheel **1280 passed / 0 failed** (40 skipped, 1 deselected); source **1 / 0** (18 skipped, 1302 deselected) |
| Inventário (0.3) | 226 testes de app não-browser (181 AppTest em 12 arquivos, 45 "core" em 6) + 44 browser (4 arquivos); todos os 226 pulam no enxuto |
| Proveniência (0.4) | trava passa em todas as rodadas; o app vem de `<checkout>/tools/calibration_app` por `sys.path.insert`; **a raiz do repo entra no `sys.path` antes do site-packages, já no CI de hoje** |
| Versões (0.5) | streamlit mais novo hoje: **1.65.0**. (i) 1.56.0: 1506/0; (i′) pisos declarados: **não instalam**; (ii) mais nova: 1506/0, pandas **3.0.6**; (iii) pins locais: 1506/0 |
| Pisos | `pandas>=2.2` e `pyyaml>=6.0`: **imprecisos, inofensivos** (o pip nunca os escolhe com numpy ≥ 2.1 / Python 3.12). `cmocean>=4.0`: **defeito real do pacote publicado** (4.0.1 pré-instalado quebra o `import cyclophaser`); corrigir viola (a), então fica **fora desta frente**, no backlog de empacotamento |
| Estabilidade (0.6) | N = 29 por versão (detecta p ≥ 9,81 % com 95 %): **58 / 58 rodadas PASS**, 0 falhas, 1506 / 0 em todas (1.56.0 e 1.65.0) |
| Custo (0.7) | plano **Free** (confirmado pelo líder técnico). Desenho recomendado (app só em `develop`/`master`/`ci/*`, `medium`): **4 239–7 101** créditos/30 d; com o CI atual (8 574): **12 813–15 675**. Critério (f) no CI (58 jobs): 2 999–5 023 pontuais; mês + (f): **15 812–20 698** < 30 000 |
| Trava (c) (0.8) | recomendada a **(A)**, variável de ambiente no `tests/conftest.py` |

## Desvios das previsões

| id | previsto | medido | causa |
|---|---|---|---|
| P5 | 227 testes de app não-browser | **226** | `test_compare_core.py::test_the_series_key_is_the_content_not_the_name` lê `tools/calibration_app/sample_tracks/`, que está no `.gitignore` (`tools/calibration_app/.gitignore:5`). Passa no conda porque a árvore local tem os CSVs; **pula em qualquer clone limpo**, inclusive no CI. A previsão contou-o porque veio da diferença conda − CI |
| P6, P7, P8b, P9, P10 | 1507 / 0 | **1506 / 0** | o mesmo teste: pula com "sample tracks not present" |
| P8b | 1507 / 0 | **INTERNALERROR, 0 testes** | `cmocean==4.0.1` não contém `cmocean/rgb/inverted/`; `import cmocean` falha (`FileNotFoundError: …/thermal_i-rgb.txt`) |

Todas as demais previsões conferem (P1, P2, P2a, P2b, P3, P4, P5 browser = 44,
P8, P9 pandas 3.x, P11: 0 falhas em 58 rodadas). Nenhum teste falhou em nenhuma rodada. O teste dos
`sample_tracks` **não é instável**: é determinístico e depende de arquivo não
versionado. Vai ao Danilo (ver "Para o Danilo").

### Desvios de instrumento (corrigidos e registrados, nenhuma previsão mudou)

1. `make_venv.sh` pedia `cmocean==4.0`, que não existe no PyPI (a primeira 4.x
   é 4.0.1). O pip parou antes de resolver, então P8 ainda não tinha sido
   testada. Corrigido para "o menor release que satisfaz `>=`". Log:
   `logs/versions/pip_floors_all_attempt1_cmocean40.log`.
2. Com 4.0.1, o pip quebrou em `pyyaml==6.0`: sem wheel para cp312, e o build
   do sdist falha (`AttributeError: 'build_ext' object has no attribute
   'cython_sources'`). Isso é **achado** sobre o piso, não só instrumento; para
   medir o resto, passou-se a usar 6.0.1. Log: `…_attempt2_pyyaml60.log`.
3. `run_all.sh`: o `keep()` abortava sob `set -e` quando uma rodada morria sem
   junit (P8b). As rodadas restantes foram retomadas por `run_rest.sh`, na mesma
   ordem e do mesmo jeito; nenhuma rodada foi repetida.
4. `ci_baseline.py`: a API devolvia corpo vazio ao User-Agent padrão do urllib, e
   os logs de passo vêm em gzip. Corrigido antes de qualquer leitura de
   resultado.
5. `inventory.py`: contava linhas de código-fonte com `::` dos avisos da coleta
   (1555/46 em vez de 1553/44), e não lia o motivo dos pulos de módulo (no
   junit ele está no corpo do `<skipped>`, não em `message`). Corrigido; os
   números do pytest (`1553 tests collected`, `44/1553`) são a referência.
6. Variante **não prevista**, exploratória: `floors_all_cm403` (pisos com
   cmocean 4.0.3, pandas 2.2.2, pyyaml 6.0.1), criada depois do P8b para ainda
   medir pandas 2.2.2 / plotly 5.24 / numpy 2.1 / scipy 1.14 / matplotlib 3.9 /
   xarray 2024.9. Resultado 1506 / 0. Não conta como previsão conferida.

## 0.1 Wheel

`scripts/build_wheel.sh c5174d1`: `git archive` → diretório temporário →
`python -m build --outdir <tmp>` (sdist e wheel, como no CI). `dist/` não foi
usado. `logs/wheel_contents.txt`, `logs/wheel_check.json`:
`cyclophaser-2.1.2-py3-none-any.whl`, 11 arquivos, nível de topo
`cyclophaser/` e `cyclophaser-2.1.2.dist-info/`; `tools/` **não**, `research/`
**não**, `tests/` **não**.

Conferências do líder técnico, confirmadas: `find_packages(exclude=['tests',
'tests.*'])`; `tools/` e `research/` sem `__init__.py`; `dist/` local com
2.0.0 (ignorado pelo git).

## 0.2 Linha de base real do CI

Reconferido antes do push: `build_test` sem filtro; `test_pypi_publish` só
`develop`; `pypi_publish` só `master`; `store_test_results` sem `when: always`.
O push de `c5174d1` criou o pipeline 408 com **um** job (`build_test`, 516) —
`logs/ci_baseline/workflow_e8ff3e70_jobs.json`. Nenhuma publicação.

| passo | tempo (s) | resultado |
|---|---|---|
| Spin up environment | 5,4 | |
| Checkout code | 1,3 | |
| Install build tools | 4,4 | |
| Build sdist and wheel | 5,0 | |
| Install package from wheel | 29,9 | |
| Install test dependencies | 3,0 | |
| Run tests against the installed wheel | 100,3 | `1280 passed, 40 skipped, 1 deselected, 1 warning in 96.98s` |
| Run source-tree tests against the checkout | 5,5 | `1 passed, 18 skipped, 1302 deselected, 88 warnings in 4.60s` |
| Uploading test results | 0,3 | |
| **job** | **155,6** | success; resource class `large` (4 CPU, 8 GB), segundo a API |

Os 58 pulos que o CircleCI registra (40 + 18) são, em boa parte, pulos de
módulo inteiro: cada módulo pulado conta 1, por isso "40 skipped" esconde 226
testes. Fonte: `logs/ci_baseline/summary_ci_app-tests.json`, `build_516*.json`.

## 0.3 Inventário dos testes do app

Ambiente conda (`which python` = `…/envs/cyclophaser/bin/python`;
`cyclophaser.__file__` = árvore do repo; streamlit 1.63.0, pandas 3.0.5):
`--collect-only` = **1553** testes; `-m browser` = **44**; `-m source_tree` = 1.
Suíte `-m "not browser"`: **1508 passed / 0 failed**, 452 s
(`logs/conda/`).

"Teste de app" = passa no venv do app e não passa no enxuto, sob a mesma
seleção `-m "not browser and not source_tree"` (`scripts/inventory.py`,
`logs/inventory/`). A divisão AppTest/core é **por arquivo** (arquivo que usa
`AppTest` em algum lugar conta como AppTest).

| tipo | arquivos | testes | tempo nos testcases (s, venv newest) |
|---|---|---|---|
| AppTest | 12 | 181 | 174,7 |
| core (streamlit/plotly, sem AppTest) | 6 | 45 | 3,4 |
| **não-browser, total** | **18** | **226** | **178,1** |
| browser | 4 | 44 (Label 29, páginas 9, Compare 3, Validate 3) | não rodados |

Por arquivo (tabela completa em `logs/inventory/inventory_table.md`):

| arquivo | tipo | app | importorskip | pulo no enxuto |
|---|---|---|---|---|
| test_app_distance_removed | AppTest | 16 | streamlit | módulo |
| test_app_navigation_apptest | AppTest | 10 | streamlit, yaml | módulo |
| test_app_passo5_fixes | AppTest | 1 (os outros do arquivo são do pacote) | streamlit | 1 teste, motivo próprio |
| test_calibrate_i2_apptest | AppTest | 13 | streamlit, yaml | módulo |
| test_calibrate_i3_apptest | AppTest | 14 | pandas, streamlit, yaml | módulo |
| test_compare_apptest | AppTest | 30 | streamlit, yaml | módulo |
| test_inspector_apptest | AppTest | 2 | streamlit | módulo |
| test_label_apptest | AppTest | 16 | streamlit | módulo |
| test_sidebar_coverage | AppTest | 38 | streamlit | módulo |
| test_sidebar_defaults | AppTest | 5 | streamlit | módulo |
| test_track_upload_apptest | AppTest | 8 | streamlit | módulo |
| test_validate_apptest | AppTest | 28 | streamlit, yaml | módulo |
| test_compare_core | core | 8 | streamlit, yaml | módulo |
| test_layer_inspector | core | 4 | plotly | 4 testes |
| test_manual_labels | core | 15 | streamlit, yaml (skipif `_have`) | 15 testes, motivo "the labelling tab is calibration-app code" |
| test_phase_colors | core | 1 | streamlit | 1 teste |
| test_phase_figures | core | 4 | streamlit, yaml | módulo |
| test_validate_core | core | 13 | streamlit, yaml | módulo |

No enxuto (receita do CI, local): **1280 passed / 0 failed**, 40 pulos = 18
módulos + 15 (`test_manual_labels`) + 4 (plotly) + 1 (`test_phase_colors`) + 1
(`test_app_passo5_fixes`) + 1 (caso observacional, legítimo). Todos os 226
testes de app pulam lá. Pulos que sobram no venv do app: 6 = 4 módulos browser
("playwright is not installed") + o caso observacional + o dos `sample_tracks`.

Tempo: no venv newest, a seleção inteira leva 236 s de parede (210 s de
pytest), dos quais 178 s são dos 226 testes de app; os 1280 do pacote, 27 s.
`--durations=0` está no log de cada rodada única.

## 0.4 Proveniência

Venv novo fora do repo, wheel de C0 + streamlit, plotly, pyyaml, pytest;
`pytest --import-mode=append -m "not browser and not source_tree"` a partir da
raiz de um clone limpo (como o `checkout` do CI), `CYCLOPHASER_REQUIRE_INSTALLED=1`,
`PYTHONPATH` vazio. Em **todas** as rodadas (enxuto, newest, floor_st,
pins_local, floors_all_cm403): saída 0, nenhuma linha
`CYCLOPHASER_REQUIRE_INSTALLED: FAIL`, a sonda (`scripts/ci_probe.py`, plugin
copiado para o site-packages do venv) registra todos os 5 módulos
`cyclophaser*` dentro do `sys.prefix` do venv, `which python` = o do venv.
**A trava passa** e cobre o app: o AppTest executa o app no mesmo processo,
e o `pytest_sessionfinish` vê os mesmos `sys.modules`.

**Como o código do app é importado.** Do clone, nunca de um pacote:
* os testes fazem `sys.path.insert(0, <repo>/tools/calibration_app)` (e
  `research/labels`) e importam os módulos pelo nome;
* o AppTest roda `tools/calibration_app/app.py` (ou uma página) como `__main__`,
  e o próprio app faz `sys.path.insert(0, <dir do app>)` antes de importar os
  irmãos;
* `cyclophaser` é importado pelo nome e resolvido pelo `sys.modules`, onde já
  está o do wheel.

A sonda registrou 17 módulos de `tools/calibration_app` (`benchmark_core`,
`compare_core`, `compare_tab`, `config_text`, `inspector_mpl`,
`inspector_plotly`, `label_overlays`, `label_tab`, `layer_inspector`,
`package_args`, `phase_figures`, `set_stats`, `track_format_ui`, `track_io`,
`validate_core`, `validate_tab`, e o `__main__` do AppTest) e 5 de
`research/labels`.

**Achado: a raiz do repo fica à frente do site-packages.** No `sys.path` final
da rodada newest, a raiz do clone aparece nas posições 32 e 39, e o
site-packages na 51 (no enxuto: 4 e 18 contra 32). Quem a põe na frente, com
`insert(0)`: `research/labels/evaluate_against_labels.py:83` e
`research/labels/diagnostics/item19/item19_core.py:23`, importados por testes
e por `tools/calibration_app/benchmark_core.py`. Isso **já acontece no CI de
hoje**. Não sombreia nada porque `cyclophaser` já está em `sys.modules`
quando eles rodam e os submódulos se resolvem pelo `__path__` do pacote. Se a
ordem de importação mudar, a trava falha a sessão (é para isso que ela existe).
A ordem de importação, sozinha, não garante nada.

`sys.path.insert/append` de `tools/` e `tests/` que tocam a raiz do repo
(lista completa por `grep`, em `logs/inventory/sys_path_edits.txt`):
* `tools/calibration_app/benchmark_core.py:90` — **append** da raiz (depois do
  site-packages: inofensivo) e de `research/labels`, `…/item19`;
* nenhum arquivo em `tests/` insere a raiz diretamente (inserem `tests/`,
  `tools/calibration_app`, `research/labels`, `research/labels/swell_item30`,
  `research/labels/diagnostics/item30`);
* o `--import-mode=append` faz o pytest **anexar** a raiz (porque
  `tests/__init__.py` existe): posição 52/33, depois do site-packages;
* indiretos, via `research/`: os dois `insert(0)` acima.

## 0.5 Versões

`pip index versions` em 2026-10-13 (`logs/versions/pip_index_versions_2026-10-13.txt`):
streamlit **1.65.0**, pandas 3.0.6, plotly 7.1.0, numpy 2.5.4, pyyaml 6.0.3,
cmocean 4.0.3.

| combinação | streamlit | pandas | numpy | plotly | resultado |
|---|---|---|---|---|---|
| (i) piso do streamlit (`floor_st`) | 1.56.0 | 3.0.6 | 2.5.4 | 7.1.0 | **1506 / 0** |
| (i′) todos os pisos do `requirements.txt` | 1.56.0 | 2.2.0 | 2.1.0 | 5.24.0 | **não instala**: `ResolutionImpossible` — `pandas 2.2.0 depends on numpy<2`, `cyclophaser 2.1.2 depends on numpy>=2.1` |
| (i′b) pisos com pandas 2.2.2 (prevista) | 1.56.0 | 2.2.2 | 2.1.0 | 5.24.0 | **INTERNALERROR**: `cmocean 4.0.1` sem `rgb/inverted/` |
| (i′c) pisos com pandas 2.2.2, cmocean 4.0.3, pyyaml 6.0.1 (exploratória) | 1.56.0 | 2.2.2 | 2.1.0 | 5.24.0 | 1506 / 0 |
| (ii) mais nova, sem fixar (`newest`) | 1.65.0 | **3.0.6** | 2.5.4 | 7.1.0 | **1506 / 0** |
| (iii) pins de `requirements-app.txt` (wheel em vez de `-e ../..`) | 1.58.0 | 2.3.3 | 2.4.0 | 7.0.0 | **1506 / 0** |

Na (ii) o pandas **vira 3.x** (3.0.6). O enxuto do CI também resolve pandas
3.0.6: o job do pacote já roda em pandas 3. Falhas por teste: nenhuma em
nenhuma combinação que instalou. Freezes em `logs/versions/freeze_*.txt`.

**Pisos declarados: classificação** (em `tools/calibration_app/requirements.txt`;
pandas e cmocean também em `setup.py`):
1. `pandas>=2.2`: **impreciso, inofensivo**. Com `numpy>=2.1` (piso do próprio
   pacote), o pip nunca escolhe 2.2.0 nem 2.2.1, que exigem `numpy<2`; o piso
   real conjunto é 2.2.2.
2. `pyyaml>=6.0`: **impreciso, inofensivo**. No Python 3.12, o pip nunca
   escolhe o 6.0 por conta própria: um pedido sem versão resolve para o mais novo
   (6.0.3), e 6.0 não tem wheel cp312. O piso real é 6.0.1.
3. `cmocean>=4.0`: **defeito real do pacote publicado**. O 4.0.1 satisfaz o piso,
   o pip o mantém se já estiver instalado, e com ele `import cmocean` — e,
   portanto, `import cyclophaser` — quebra (`FileNotFoundError:
   …/cmocean/rgb/inverted/thermal_i-rgb.txt`). O piso real é 4.0.3. Corrigir
   exige mudar `install_requires` no `setup.py` e publicar uma versão nova, o
   que viola o critério (a). Fica **fora desta frente**, como item de backlog
   de empacotamento, registrado em (k).

O app público não é afetado, porque o Streamlit Cloud instala o mais novo de
tudo.

## 0.6 Estabilidade

N = 29 por versão, declarado em `PREVISOES.md` antes de medir. Cada série teve
um venv novo e rodadas em sequência, nunca duas suítes ao mesmo tempo. As
rodadas foram no mesmo clone, em C0, com a seleção e a trava da 0.4
(`scripts/stability.sh`, `scripts/stability_report.py`,
`logs/stability/stability_report.json`). Período: 2026-10-13T23:58Z a
2026-10-14T03:24Z.

| série | streamlit / pandas / numpy / plotly | rodadas PASS | passed | failed + error | pulos | parede (s) mín / mediana / máx |
|---|---|---|---|---|---|---|
| `floor_st` | 1.56.0 / 3.0.6 / 2.5.4 / 7.1.0 | **29 / 29** | 1506 em todas | **0** | 6 em todas | 191,0 / 209,1 / 226,9 |
| `newest` | 1.65.0 / 3.0.6 / 2.5.4 / 7.1.0 | **29 / 29** | 1506 em todas | **0** | 6 em todas | 204,4 / 210,1 / 271,5 |

**P11 confere: 0 rodadas com falha nas 58.** Nenhum teste falhou em nenhuma
rodada, então não há intermitência a listar por teste ou por rodada. Nas 58, a
trava passou (saída 0, todos os `cyclophaser*` no venv) e o clone ficou limpo
depois da rodada (`git status --porcelain` vazio: nenhum teste escreve na
árvore).

Alcance: com N = 29, uma intermitência com probabilidade p por rodada seria
vista com 95 % se p ≥ **9,81 %**. Para p = 5 %, a chance de vê-la é 77,4 %; para
p = 2 %, 44,3 %. Intermitências mais raras que isso podem existir sem
aparecer aqui. Isso vale para esta máquina (arm64, 8 núcleos, sem carga
concorrente). A estabilidade no CircleCI é o critério (f), medido na etapa de
implementação.

## 0.7 Custo

Tarifa lida hoje (`logs/cost/pricing_2026-10-13.md`): Docker x86 `medium` 10
créditos/min, `large` 20; plano Free 30 000 créditos/mês; open source até
400 000/mês (Linux/Docker); Performance US$ 15 por 25 000 créditos extras. Os
jobs deste projeto rodam em **`large`** (API, build 516), sem `resource_class`
no config. **O plano do projeto não aparece sem login: o Danilo precisa
confirmar** — isso decide se o custo abaixo importa.

Frequência real (API, `logs/cost/`): de 2026-09-13 a 2026-10-13, **172
pipelines** (um por push; 4 deles de tag, sem trabalho), **168 jobs
`build_test`** (média 150,2 s, máx. 215,3 s), 10 `test_pypi_publish`, 3
`pypi_publish`: **428,7 min = 8 574 créditos** em `large`. O `git log` do
mesmo período tem 247 commits em `develop`/`master`; commit não é push, e a
contagem de pipelines é a medida certa.

Estimativa para um job de app com duas pernas (piso + mais nova), feita por
`scripts/cost_estimate.py` (`logs/cost/cost_estimate.json`) com duas
suposições nomeadas: (A1) parte fixa = a do `build_test` + uma instalação a
mais do tamanho de "Install package from wheel" (79,2 s); (A2) razão de
velocidade CI/local entre 1,0 e 1,91 (a razão medida nos testes do pacote:
100,3 s no CI contra 52,6 s locais).

| | por job | por push (2 pernas) | créditos/push `large` | créditos/30 d `large` | créditos/30 d `medium` |
|---|---|---|---|---|---|
| inferior | 5,1–5,3 min | 10,3 min | 207 | **34 742** | 17 371 |
| superior | 8,5–8,8 min | 17,3 min | 346 | **58 195** | 29 098 |

**Destaque:** no plano Free, o job do app sozinho, mesmo no limite inferior,
passa dos 30 000 créditos/mês. Somado ao atual (8 574), fica entre **43 316** e **66 769**.
No plano open source (400 000), cabe com folga. Medidas que reduzem: `medium`
(metade, se o tempo couber), ou a perna "mais nova" só em `develop`/`master`
(ver 0.9 (4)). A duração real só vem na etapa 1, do primeiro job.

### 0.7b Adendo: plano Free (30 000 créditos/mês) — desenho recomendado

O líder técnico confirmou o plano **Free**. Contas refeitas por
`scripts/cost_free_plan.py` (`logs/cost/cost_free_plan.json`), a partir de
`logs/cost/pipelines_since_2026-09-13.json` e dos minutos por perna de
`cost_estimate.json`.

Pipelines em 30 dias, por classe de branch (conferido por script; bate com o
adendo): **40** em branches permanentes (`develop` 10, `develop-v2.1` 27,
`master` 3), **128** nas demais (127 de feature/pesquisa + 1 em `ci/app-tests`),
**4** em tags. Total 172.

Desenho: o job do app (duas pernas) roda só em `develop`, `master` e
`/^ci\/.*/`, com `resource_class: medium` explícito. Pela página de preços,
`medium` está disponível no Free (Docker x86 Small–Large: "Yes";
`logs/cost/free_plan_exhaustion_2026-10-14.md`). O `build_test` fica como está,
em todo push e em `large`. Pushes que levariam o app: 40 + 1 = **41** em 30 dias.

Suposição nova, **A3** (não medida): em `medium`, os testes rodam na velocidade
dos limites de 0.7. O pytest roda num só processo, mas `medium` tem 2 vCPU
contra 4. A duração real sai do primeiro job da etapa 1, e a regra de parada
abaixo cobre o caso.

| | por push (2 pernas, `medium`) | app em 30 d | **total com o CI atual (8 574)** |
|---|---|---|---|
| inferior | 103 créditos | 4 239 | **12 813** |
| superior | 173 créditos | 7 101 | **15 675** |

**Perda registrada.** Uma quebra do app numa branch de feature só aparece no CI
depois do merge em `develop` (127 dos 172 pipelines do mês não rodariam o app).
A cobertura antes do merge continua sendo a regra que já existe: rodar os
testes do app no ambiente conda antes de cada merge. A perna `ci/*` existe
para testar o próprio CI.

**Critério (f) no CI, custo pontual.** São 29 jobs por perna, pelo mecanismo da
matriz com um parâmetro fictício (`run: [1..29]`) numa branch `ci/...`, mesmo
commit, em `medium`. Isso dá 58 jobs: **2 999** créditos (inferior) a **5 023**
(superior). Mês normal + (f): **15 812** a **20 698** créditos, **abaixo de
30 000** também no limite superior (folga de 9 302).

**Free com os créditos esgotados.** A doc oficial
([credits](https://circleci.com/docs/guides/plans-pricing/credits/)) diz:
"When your available credits reach 0, personal builds are blocked until your
credits refill at the start of the next month." Ou seja, **param todos os
jobs**: `build_test`, `test_pypi_publish` e `pypi_publish`, até o mês seguinte.
Os créditos do Free "expire after a month and do not roll over"
([pricing](https://circleci.com/pricing/)). Um artigo de suporte
([15091234](https://support.circleci.com/en/articles/15091234-upgrade-your-plan-to-unblock-build))
**contradiz** a doc e fala em renovação **semanal** ("Free Plan credits are
allocated on a weekly basis"). Fica registrado como conflito entre fontes; a
doc oficial é a referência aqui.

**Cota de open source: não confirmável.** A
mesma doc oficial diz: "Organizations on our Free Plan can use up to 400,000
credits per month, for free, for Linux open source builds. Using our Free Plan
and keeping your repository public will enable this for you." E também: "Open
source builds are not subject to this block and continue to run even if your
credit balance is exhausted." O repositório é **público** (`api.github.com`:
`private: false`, conferido em 2026-10-14), e os jobs são Docker Linux. Se o
teto real for o de open source, ele é 400 000 e os jobs não param com saldo
zerado. **Isso não dá para confirmar pelo painel.** A própria doc diz: "Open
source credit availability and limits are not visible in the CircleCI web
app" (e, no FAQ, "will not be visible in the UI"). Por isso o desenho
conservador (`develop`, `master`, `ci/*`) fica como **o recomendado**: ele é
seguro nos dois cenários. Ampliar o job do app para todas as branches vira
**opção futura**, a reavaliar com o consumo real observado, registrada em (k).

**Regra de parada para a etapa 1.** Se a duração real do primeiro job do app
projetar mais de **25 000** créditos/mês no total (CI atual + app), parar e
levar ao Danilo antes de seguir. Com 41 pushes/mês em `medium` e 8 574 de CI
atual, o limiar é **40,06 min por push = 20,03 min por perna**
(`cost_free_plan.json`, `stop_rule_*`). A conta usa a duração medida no job
real, não estas estimativas.

## 0.8 Trava contra pulos (critério c)

Medido nesta etapa: no enxuto, os 226 testes de app somem em 40 pulos, e o
motivo de **16** deles não cita a dependência — "the labelling tab is
calibration-app code" ×15 (`test_manual_labels`) e "AppTest drives the
calibration app; the CI installs only the wheel, pytest and pyyaml" ×1
(`test_app_passo5_fixes`). Os 18 pulos de módulo têm `message="collection
skipped"` no junit; o motivo real ("could not import 'streamlit'…") está só
no corpo do elemento `<skipped>`.

**(A) Variável de ambiente lida no `tests/conftest.py`** (por exemplo
`CYCLOPHASER_REQUIRE_APP_DEPS=1`): no `pytest_configure`, importa streamlit,
plotly e yaml e levanta `pytest.UsageError` se algum faltar. É o mesmo padrão da
`CYCLOPHASER_REQUIRE_INSTALLED`: desligada, não muda nada; ligada, para a
sessão antes de coletar.
* Pega: dependência ausente, **e também dependência instalada mas quebrada**
  (o `import` levanta no próprio processo do pytest, como o cmocean 4.0.1 fez).
  Pega pelos 3 nomes, sem depender de texto de motivo.
* Deixa passar: pulos por outro motivo (o dos `sample_tracks`, o caso
  observacional, os 4 módulos browser); um teste de app novo que dependa de
  um módulo fora da lista; um teste de app que alguém marque `skip`.
* Custo: ~10 linhas em `tests/conftest.py`, que o próprio `conftest` diz ser
  "deliberadamente mínimo"; a importação só acontece com a variável ligada,
  então o job do pacote não muda.

**(B) Passo de CI** `python -c "import streamlit, plotly, yaml"` antes do
pytest + checagem do junit exigindo zero pulos cujo motivo cite essas
dependências.
* Pega: dependência ausente no passo de importação (processo separado, mesmo
  venv).
* Deixa passar: os 16 pulos de motivo próprio já hoje; os 18 de módulo se o
  verificador ler só `message` (precisa ler o corpo); qualquer motivo
  reescrito no futuro; um import que funciona no passo e falha dentro do pytest
  (por exemplo por `sys.path` diferente — no pytest há 47 entradas do clone à
  frente do site-packages, no `python -c` não).
* Custo: não toca em `tests/`, mas é um verificador de texto no
  `.circleci/config.yml`, que ninguém vê falhar até falhar.

**Recomendação: (A).** Não depende de texto, roda no mesmo processo e
`sys.path` que os testes, e pega o caso medido de dependência instalada que não
importa. O que (A) deixa passar é o mesmo que (B) deixa passar (pulos por outro
motivo). Para isso, recomendo somar a (A) uma **lista fechada de pulos
permitidos no job do app**: um passo que lê o junit e exige que os pulos sejam
exatamente os 5 listados em 0.10 (eram 6 em C0; ver a decisão sobre os `sample_tracks`). Essa checagem é por id de teste, não por
texto de motivo. Ela pega também um teste de app que comece a pular sem
motivo novo. Um pulo novo e legítimo exige atualizar a lista, e isso é
intencional.

## 0.9 Desenho proposto

| # | decisão | recomendação | custo / risco |
|---|---|---|---|
| (1) | job separado | `app_test` novo, mesma imagem `cimg/python:3.12.3`, **`resource_class: medium` explícito**; constrói o wheel do mesmo commit, instala wheel + streamlit/plotly/pyyaml/pytest, roda com `CYCLOPHASER_REQUIRE_INSTALLED=1` + a trava de (c) + `--import-mode=append`, a partir da raiz do checkout. `build_test` fica intocado | 79 s fixos estimados + testes; ver 0.7 |
| (2) | matriz de versões | duas pernas (`parameters` + `matrix` do CircleCI): **piso** `streamlit==1.56.0` (resto livre) e **mais nova sem fixar**. A mais nova sem fixar é o que o app público instala a cada deploy, então um vermelho sem mudança de código é justamente o aviso que se quer; o `pip freeze` de cada job vai para os artefatos, para atribuir o vermelho. Perna "todos os pisos": só depois de corrigir os 3 pisos de 0.5 (decisão do Danilo; hoje ela nem instala). Pins locais (iii): fora do CI (são de uso local) | 2× o tempo; vermelho de origem externa possível (não visto hoje: 1.65.0 passa) |
| (3) | Chromium | **fora do CI por push**; manual como hoje. Os 3 defeitos que só o navegador pegou (registro, `docs/future_work.md` item 35, "Lessons" 1): valores de widget perdidos na troca de página (A12); widget desenhado pela primeira vez numa rodada posterior mostra o próprio default (F1); o papel do `st.toggle` difere entre versões (sem `switch` em 1.56.0). Um job agendado (semanal) com Chromium pode ser uma frente própria; o registro mostra intermitência real em teste de navegador (grade paginada, I3) | job agendado: instalar Chromium (~minutos) + 44 testes; não medido aqui |
| (4) | branches e eventos | **(substituída pelo adendo, plano Free)** as duas pernas só em `develop`, `master` e `/^ci\/.*/` (filtro de branch do CircleCI); `build_test` em todo push, sem mudança nenhuma (nem de `resource_class`) | 12 813–15 675 créditos/mês no total (0.7b); perda: quebra do app em feature só aparece depois do merge em `develop`, e a cobertura pré-merge fica com a regra do conda |
| (5) | publicação exige o app? | **sim** (as duas pernas rodam em `develop` e `master`, onde se publica, então o `requires` é satisfazível): `test_pypi_publish` e `pypi_publish` passam a requerer `build_test` + as duas pernas do app. O app público instala `cyclophaser>=2.1.0` do PyPI, então uma versão que quebre o app chega ao app público. Contra: um vermelho só de origem externa (mais nova) bloqueia publicar uma correção do pacote. Nesse caso, a saída é decidir, não desligar. **Lacuna:** o Streamlit Cloud reimplanta o app a cada push na `master` **sem esperar o CI**. O job do app **detecta, não impede**. A proteção real é só fazer merge na `master` com o job do app verde **no mesmo commit em `develop`**. Esta lacuna entra no comentário do config e no item do `future_work.md` exigidos em (j)/(k) | atraso de publicação até o app ficar verde |
| (6) | seleção de testes | **suíte inteira menos `browser`/`source_tree`** (a seleção medida aqui: 1506). Não exige mudança em `tests/` e testa também o pacote contra as dependências mais novas com o app instalado. Contra: repete os 1280 do pacote (27 s locais, 100,3 s no CI por perna: **11 234** créditos/30 d em `large` nas duas pernas, `cost_estimate.json`). A alternativa "só app" exige um marcador novo em 18 arquivos (mudança em `tests/`) e mantê-lo | ver 0.7 |

## 0.10 Critérios de aprovação das etapas seguintes

Critérios (a)–(k) do bloco de abertura (texto do Danilo, enviados pelo líder
técnico na correção consolidada). PASS = (a)–(k); FAIL = qualquer um, ou o
Danilo não aprovar o desenho. Toda conta abaixo é refeita por
`scripts/reach_check.py` a partir dos logs desta etapa (`logs/reach_check.json`).

**Decisão do Danilo (2026-10-13).** O teste
`tests/test_compare_core.py::test_the_series_key_is_the_content_not_the_name`
**será corrigido nesta frente**, na etapa de implementação, e não agora. A
correção aprovada: copiar 2 arquivos de `tools/calibration_app/sample_tracks/`
(formato TRACK, por exemplo `track_19800580.csv`) para uma pasta versionada nova
em `tests/` e apontar o `SAMPLE_DIR` do teste para ela. Antes, conferir por
`grep` que nenhum outro teste faz `glob`/`rglob` que passaria a enxergar a pasta
nova. Nada mais muda no teste. Base nos logs (`reach_check.py`): ele **passou**
na suíte conda (a árvore local tem os CSVs), **pulou** em todo clone limpo, e o
módulo inteiro pula no enxuto. Por isso o `build_test` não muda.

Contagem esperada no job do app (`-m "not browser and not source_tree"`, sem
playwright), **depois da correção**:
* passed = 1280 (pacote, linha de base 516) + 227 (226 de app medidos em C0 + o
  dos `sample_tracks`) = **1507**; failed = **0**. Medido em C0, antes da
  correção: 1506 / 0;
* lista fechada de pulos permitidos, por id (**5**; vale para um job **sem**
  playwright, como o proposto — com playwright, os 4 de módulo viram 44
  coletados e desselecionados, e por isso a contagem de pulos não é critério
  fora desse ambiente):
  1. `tests/test_app_pages_browser.py` — módulo, playwright ausente
  2. `tests/test_compare_browser.py` — módulo, playwright ausente
  3. `tests/test_label_browser.py` — módulo, playwright ausente
  4. `tests/test_validate_browser.py` — módulo, playwright ausente
  5. `tests/synthetic/test_synthetic_lifecycles.py::test_lifecycle_phase_timing[IcIt_observational]` — por desenho
* `build_test` inalterado: **1280 / 0** (o teste é só de app);
* a coleta fecha: em C0, 1506 + 6 + 1 − 4 + 44 = 1553; depois da correção,
  **1507 + 5 + 1 desselecionado − 4 pulos de módulo + 44 browser = 1553** =
  coleta conda.

| | critério | forma mensurável (números desta etapa) | PASS alcançável | FAIL alcançável |
|---|---|---|---|---|
| (a) | `cyclophaser/` e `install_requires` do `setup.py` inalterados | `git diff --stat 3f410df <ponta> -- cyclophaser setup.py` vazio | sim: vazio em `ci/app-tests` hoje (conferido) | sim: qualquer edição; por exemplo, corrigir o piso do cmocean (por isso ele fica fora, ver 0.5) |
| (b) | job do wheel mantém o comportamento; enxuto continua enxuto | passo do wheel **1280 passed / 0 failed** e passo source **1 / 0**, como no job 516; passo "Install test dependencies" segue `pip install pytest pyyaml`; nenhum streamlit/plotly no job | sim: é a linha de base 516 | sim: se as dependências do app vazarem para o job do wheel, ele passa a **1507** (= 1280 + 227) ≠ 1280 |
| (c) | streamlit realmente instalado, zero pulos por falta dele; o job **falha** se faltar | (A) `CYCLOPHASER_REQUIRE_APP_DEPS=1` no job: sessão para com `UsageError` sem streamlit/plotly/yaml; junit do job com exatamente os **5** pulos acima e **1507** passed | sim: em C0, 1506/0 com 6 pulos em 4 combinações; o 6º pulo é o teste que a correção aprovada faz passar (passou no conda) | sim: sem streamlit e sem trava, passed = **1280** (227 perdidos; medido no enxuto, 40 pulos) → lista de pulos não fecha; com a trava, a sessão para (controle a rodar na etapa 1, num job descartável sem streamlit) |
| (d) | cyclophaser do wheel, mesma trava de proveniência; documentar a importação do app | `CYCLOPHASER_REQUIRE_INSTALLED=1`, saída 0, nenhuma linha `…: FAIL`, `cyclophaser.__file__` em site-packages; a importação do app está documentada em 0.4 | sim: medido em 5 venvs (0.4) | sim: `python -m pytest` a partir da raiz põe o CWD à frente → `cyclophaser` do checkout → `UsageError` no `pytest_configure` (mecanismo do `conftest`; controle a rodar na etapa 1) |
| (e) | controle positivo no CircleCI real: **regressão no código do app** → vermelho; restaurar → verde | numa branch descartável `ci/...`, o commit 1 introduz uma **regressão em `tools/calibration_app`** (não uma edição de teste), escolhida para ser pega por AppTest e **fora** dos 4 módulos que os testes do `build_test` importam (`benchmark_core`, `layer_inspector`, `package_args`, `track_io`, lidos na sonda do enxuto). Antes do push, o relatório da etapa declara a mudança e os **k** ids que devem falhar. Vermelho: job do app com **failed = k ≥ 1**, ids que falharam = **exatamente** os declarados, passed = **1507 − k**; `build_test` **1280 / 0**. O commit 2 restaura e o job volta a **1507 / 0**. Registrar os dois links | sim: 1507/0 é o esperado depois da correção (1506/0 medido em C0); 1 ≤ k ≤ 227 (`reach_check.py`) | sim: o próprio commit 1. Falha se ficar verde, se os ids diferirem dos declarados, ou se o `build_test` sair de 1280/0 |
| (f) | estabilidade: N vezes seguidas no mesmo commit, sem intermitência | **N = 29 por perna** (piso e mais nova), matriz com parâmetro fictício numa branch `ci/...`, mesmo commit, `medium`: **58 jobs, todos verdes com 1507 / 0**. Detecta p ≥ 9,81 % com 95 %. **Regra de contagem, fixada agora:** qualquer um dos 58 jobs que não termine verde conta como falha, **seja qual for a causa**, inclusive infraestrutura (download, rede, timeout). Uma falha leva ao diagnóstico variando rede e CPU, **nunca** a reclassificar o job depois | sim: localmente, 58/58 PASS (0.6) | sim: qualquer dos 58 jobs não verde |
| (g) | matriz do streamlit conforme aprovado, cada versão verde | pernas `streamlit==1.56.0` e mais nova sem fixar: cada uma **1507 / 0**; `pip freeze` de cada job nos artefatos | sim: 1.56.0 e 1.65.0 medidos 1506/0 em C0 (+1 com a correção) | sim: qualquer perna com failed ≥ 1 (a mais nova muda sem mudança de código) |
| (h) | nenhuma mudança dispara publicação sem querer | filtros relidos antes do primeiro push de cada etapa; pipeline de cada push em `ci/*` contém só `build_test` + `app_test`, nenhum job de publicação (lido na API do workflow) | sim: pipeline 408 só com `build_test` (conferido na API) | sim: um filtro que inclua `ci/*` nos jobs de publicação faria `test_pypi_publish` aparecer na lista de jobs do workflow |
| (i) | `store_test_results` com `when: always` | o config tem `when: always` nos dois jobs; no job **vermelho** do (e), o endpoint `/tests` da API lista o teste quebrado como `failure` | sim: é configuração + o job do (e) | sim: hoje o config **não** tem `when: always` (`.circleci/config.yml:64`), e com um passo de teste falho o upload não roda, então `/tests` não traz a falha |
| (j) | decisão sobre Chromium executada; se fora do CI, lacuna escrita no config e na documentação, com os 3 defeitos | recomendação: fora do CI por push. O comentário no `.circleci/config.yml` e o item do `future_work.md` citam A12 (valores de widget perdidos na troca de página), F1 (widget desenhado pela primeira vez numa rodada posterior mostra o próprio default) e o papel do `st.toggle` que difere entre versões; e também a lacuna do deploy do Streamlit Cloud (0.9 (5)) | sim: é texto verificável por `grep` | sim: faltar qualquer um dos 3 defeitos ou a lacuna |
| (k) | registro em `docs/future_work.md` | item **36** (próximo livre; o último é o 35) com: o medido (linha de base, inventário, versões, estabilidade), a matriz, o controle positivo (dois links), as lacunas que sobram (Chromium; app só depois do merge em `develop`; Streamlit Cloud reimplanta sem esperar o CI; e o **backlog de empacotamento**: `cmocean>=4.0` como defeito do pacote publicado, `pandas>=2.2` e `pyyaml>=6.0` como imprecisos e inofensivos, junto com a dívida de `install_requires`), a correção do teste dos `sample_tracks` e a opção futura de ampliar o app para todas as branches com o consumo real | sim | sim: item ausente ou sem uma das partes |

**Leitura do (e).** O texto do Danilo diz "quebrar de propósito um teste do
app". A leitura foi trocada por uma regressão no **código** do app, que é mais
forte: prova que os testes pegam um defeito do app, e não só que um teste
editado falha. A troca é recomendação do líder técnico e depende da aprovação
do Danilo.

**Itens informativos para o Danilo (fora da tabela de critérios):**
* Custo do desenho recomendado (0.7b): 12 813–15 675 créditos/mês no total;
  critério (f) pontual: 2 999–5 023; mês + (f): 15 812–20 698 < 30 000.
* Regra de parada da etapa 1: se a duração real do primeiro job do app projetar
  mais de 25 000 créditos/mês (CI atual + app), parar e levar ao Danilo. O
  limiar é 20,03 min por perna em `medium`.

## Decisões tomadas e pendentes

1. **Plano do CircleCI**: Free (adendo). A cota de open source (até 400 000/mês
   para repositório público) não pode ser confirmada: a doc diz que ela não
   aparece no painel. Por isso o recomendado é o desenho conservador, e ampliar
   para todas as branches fica como opção futura, com consumo real (0.7b).
2. **Teste dos `sample_tracks`** — decidido (Danilo, 2026-10-13): será corrigido
   nesta frente, na implementação, com 2 CSVs versionados em `tests/` (ver 0.10).
   Não tocado nesta etapa.
3. **Pisos** — decidido (Danilo, 2026-10-13): `cmocean>=4.0` é defeito do pacote
   publicado e fica **fora desta frente**, por violar (a). `pandas>=2.2` e
   `pyyaml>=6.0` ficam registrados como imprecisos e inofensivos. Os três vão
   para o backlog de empacotamento no item 36 do `docs/future_work.md`, junto
   com a dívida de `install_requires`.
4. **A raiz do repo entra à frente do site-packages** por dois `insert(0)` em
   `research/labels`. Hoje é inofensivo graças à ordem de importação e à trava.
   Trocar por `append` é uma frente pequena, fora desta. Pendente.
5. **Pendente**: aprovação do desenho (1)–(6), da trava (A) + lista fechada de
   pulos, e da leitura mais forte do (e).

## Arquivos

* `PREVISOES.md` — previsões (commit `c5174d1`, antes de medir)
* `scripts/` — `common.sh`, `build_wheel.sh`, `make_venv.sh`, `ci_probe.py`,
  `run_suite.sh`, `run_all.sh`, `run_rest.sh`, `stability.sh`,
  `summarize_junit.py`, `inventory.py`, `ci_baseline.py`, `ci_jobs_window.py`,
  `cost_estimate.py`, `cost_free_plan.py` (adendo), `stability_report.py`
* `logs/` — `wheel_*`, `ci_baseline/` (API bruta do build 516),
  `conda/`, `runs/` (junit e log de cada rodada única, gz), `inventory/`,
  `versions/` (logs do pip e freezes), `stability/`, `cost/`
