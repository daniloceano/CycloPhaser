# Etapa 1 — testes do app de calibração no CI: implementação

Branch `ci/app-tests` (de `develop` @ `3f410df`). Desenho da etapa 0
(`etapa0/RELATORIO.md`, `9efc74f`) aprovado pelo Danilo em 2026-10-14 e
implementado sem reabrir. Data: 2026-10-14. **Nada foi mergeado; nenhum PR.**
Branches descartáveis `ci/app-tests-controls` e `ci/app-tests-stability`
mantidas (o destino delas se decide no fechamento).

## Hashes

| o quê | commit |
|---|---|
| previsões do passo 1 (+ scripts, grep dos globs) | `6d8f4f0` |
| **implementação** | **`425a72f`** |
| registros do passo 1 + previsões do passo 2 | `8e23520` |
| controles (branch `ci/app-tests-controls`): E1 / E2 / CD | `12a618d` / `7116992` / `cf92957` |
| registros do passo 2 + previsões do passo 3 | `8875ff6` |
| matriz (f) (branch `ci/app-tests-stability`) | `6fb3808` |
| documentação (passo 4) | `66ac34e` (verificado: pipeline 416) |
| registro da verificação final (ponta) | o commit deste texto |

Os commits só de registro levam `[skip ci]` no título, para não gastar duas
pernas do app em cada um. A ponta final não leva (ver verificação final).

## O que foi implementado

Exatamente o desenho: `app_test` com `leg` (floor | newest), nomes fixos
`app_test_floor` / `app_test_newest`, `medium`, só em `develop`, `master` e
`/^ci\/.*/`; publicação requer `build_test` + as duas pernas; `when: always` no
`store_test_results` dos dois jobs; `store_artifacts` com o `pip freeze` de
cada perna; trava (A) `CYCLOPHASER_REQUIRE_APP_DEPS` no `tests/conftest.py`
(docstring atualizado); `.circleci/check_app_skips.py` com os 5 ids; os 2 CSVs
em `tests/sample_tracks/` e só a linha do `SAMPLE_DIR` mudada no teste.
`git diff 3f410df <ponta> -- cyclophaser setup.py` vazio.

**Validação do config.** O CLI `circleci` não existe nesta máquina. No lugar:
`scripts/validate_config.py`, que valida contra o JSON schema do próprio
CircleCI (o do `circleci-yaml-language-server`, cópia em
`logs/passo1/circleci_schema_2026-10-14.json.gz`) e confere, no YAML lido, os
jobs por classe de branch, os `requires` e os filtros. Controles do validador:
o config antigo falha nos fatos (`requires`, `medium`, `when`), e um `when:
sometimes` falha no schema (`logs/passo1/validate_config_control_*.json`). Isso
é mais fraco que `circleci config validate`; o primeiro pipeline real foi a
validação de fato, e passou.

**Filtros relidos antes do push da implementação** (`validate_config_impl.json`):
`ci/app-tests` → `build_test`, `app_test_floor`, `app_test_newest`; `develop` →
+ `test_pypi_publish`; `master` → + `pypi_publish`; `feat/*` → só `build_test`.
**Nenhuma publicação em `ci/*`.**

## Passo 1 — construir e primeiro pipeline real

| id | previsão | medido | |
|---|---|---|---|
| Q1 (a) | diff `cyclophaser setup.py` vazio | vazio | ✔ |
| Q2 | enxuto local 1280 / 0; source 1 / 0 | **1280 / 0**; **1 / 0** | ✔ |
| Q3 | conda `-m "not browser"` 1508 / 0 | **1508 / 0** (`which python` = env `cyclophaser`; `cyclophaser.__file__` = árvore do repo) | ✔ |
| Q4 | floor local 1507 / 0, 5 pulos, travas OK | **1507 / 0**, `OK: skips are exactly the 5 allowed ids`, saída 0, sonda: todo `cyclophaser*` no venv | ✔ |
| Q5 | newest local idem | **1507 / 0**, idem | ✔ |
| Q6 (h) | jobs = `build_test`, `app_test_floor`, `app_test_newest`, nenhum de publicação | pipeline [411](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/411): exatamente esses 3 | ✔ |
| Q7 (b) | `build_test` 1280 / 0 + 1 / 0 | job [521](https://circleci.com/gh/daniloceano/CycloPhaser/521): **1280 / 0 + 1 / 0** (`large`, 163,8 s) | ✔ |
| Q8 (c)(g) | cada perna 1507 / 0, pulos OK, `/tests` com 1512 casos | [519](https://circleci.com/gh/daniloceano/CycloPhaser/519) floor e [520](https://circleci.com/gh/daniloceano/CycloPhaser/520) newest: **1507 / 0**, checagem OK, `/tests` = 1507 `success` + 5 `skipped` | ✔ |
| Q9 | duração registrada (estimativa 5,1–8,8 min) | floor **648,7 s = 10,8 min**, newest **691,1 s = 11,5 min** (`medium`) | acima da estimativa |

Versões (artefato `pip-freeze-*.txt` de cada perna): floor streamlit 1.56.0,
newest 1.65.0; nas duas pandas 3.0.6, numpy 2.5.4, plotly 7.1.0, PyYAML 6.0.3.
Local, as mesmas versões.

**Regra de parada: não disparou.** 10,8 e 11,5 min < 20,03 min por perna.
Projeção: 8 574 + 41 × (10,8 + 11,5) min × 10 ≈ **17 700** créditos/mês < 25 000.

Logs: `logs/passo1/local_425a72f/`, `logs/passo1/conda_425a72f/`,
`logs/passo1/ci_425a72f/`.

## Passo 2 — controles (branch `ci/app-tests-controls`)

**(e) Regressão declarada** (antes do push, `PREVISOES_passo2.md`): apagar a
entrada `vorticity_smoothed2` do `LABEL_OVERLAY_STYLE` em
`tools/calibration_app/label_overlays.py` — código do app, fora dos 4 módulos
que o `build_test` importa, alcançado só pela página Label (AppTest). Ids
previstos, descobertos antes por uma rodada local (`logs/passo2/local_discovery/`):
`tests/test_label_apptest.py::test_toggling_overlay_layers_does_not_move_any_phase`
e `::test_revealing_an_overlay_records_it_and_unblinds_the_case` (k = 2).

| id | previsão | medido | |
|---|---|---|---|
| R1, R2 | E1: as duas pernas vermelhas, 1505 / 2, exatamente os 2 ids | pipeline [412](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/412): floor [522](https://circleci.com/gh/daniloceano/CycloPhaser/522) e newest [524](https://circleci.com/gh/daniloceano/CycloPhaser/524) **failed, 1505 / 2**, os 2 ids; checagem de pulos não rodou | ✔ |
| R3 | E1: `build_test` verde 1280 / 0 + 1 / 0 | [523](https://circleci.com/gh/daniloceano/CycloPhaser/523): **1280 / 0 + 1 / 0** | ✔ |
| R4 (i) | `/tests` dos vermelhos lista os 2 como `failure` | 522 e 524: `{'success': 1505, 'failure': 2, 'skipped': 5}`, ids iguais; o passo "Uploading test results" rodou depois do passo de teste falho | ✔ |
| R5, R6 | E2 (revert): pernas 1507 / 0, `build_test` 1280 / 0 + 1 / 0 | pipeline [413](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/413): [525](https://circleci.com/gh/daniloceano/CycloPhaser/525) / [526](https://circleci.com/gh/daniloceano/CycloPhaser/526) **1507 / 0**, checagem OK; [527](https://circleci.com/gh/daniloceano/CycloPhaser/527) **1280 / 0 + 1 / 0** | ✔ |
| R7 (c) | perna sem plotly: `UsageError` citando plotly, 0 testes, vermelho | pipeline [414](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/414), job [528](https://circleci.com/gh/daniloceano/CycloPhaser/528): `ERROR: CYCLOPHASER_REQUIRE_APP_DEPS is set but these app dependencies do not import: plotly (ModuleNotFoundError: No module named 'plotly')`, exit 4, failed | ✔ |
| R8 (d) | `python -m pytest` da raiz: `UsageError` da trava de proveniência | job [532](https://circleci.com/gh/daniloceano/CycloPhaser/532): `ERROR: CYCLOPHASER_REQUIRE_INSTALLED is set but cyclophaser was imported from /home/circleci/project/cyclophaser/__init__.py, not from site-packages`, exit 4, failed | ✔ |
| R9 | no mesmo pipeline, pernas e `build_test` verdes | [531](https://circleci.com/gh/daniloceano/CycloPhaser/531) / [530](https://circleci.com/gh/daniloceano/CycloPhaser/530) 1507 / 0; [529](https://circleci.com/gh/daniloceano/CycloPhaser/529) 1280 / 0 + 1 / 0 | ✔ |
| R10 (h) | nenhuma publicação na branch | 412–414 sem job de publicação | ✔ |

As pernas extras (`app_control`, `scripts/add_negative_controls.py`) existem só
em `ci/app-tests-controls`; `ci/app-tests` não as tem.

## Passo 3 — estabilidade (f) (branch `ci/app-tests-stability`)

Commit `6fb3808` = ponta do passo 1 + `scripts/make_stability_config.py`
(parâmetro fictício `run`, matriz `leg × run(1..29)`, sem `build_test` e sem
publicação; passos do `app_test` idênticos). Pipeline
[415](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/415), 30
jobs simultâneos (limite do Free) e depois os outros 28.

| id | previsão | medido | |
|---|---|---|---|
| S1 | 58 jobs `app_test_*`, sem `build_test`, sem publicação | 58, todos `app_test_<leg>_<run>` | ✔ |
| S2 (f) | **58 / 58 verdes**, cada um 1507 / 0, checagem OK | **58 / 58 PASS** (`logs/passo3/stability_summary.json`, `scripts/stability_summary.py`): todos `success`, `1507 passed` sem failed/error, `OK: skips…` | ✔ |
| S4 | créditos ≈ 6 300–6 900 (refeito com as durações dos passos 1–2) | **6 181** (segundos exatos) / **6 460** (minuto arredondado para cima por job) | ver desvios |

Durações por perna (29 cada): floor 556,8 / 609,4 / 730,6 s (mín / mediana /
máx), newest 586,3 / 657,2 / 773,1 s. Maior job: 12,9 min, abaixo de 20,03.

## Créditos da frente (2026-10-14, API, `logs/cost/front_credits_2026-10-14.json`)

Estimados como duração × tarifa da classe (`medium` 10/min, `large` 20/min):
`ci/app-tests-stability` 58 jobs **6 184**; `ci/app-tests-controls` 11 jobs
**861**; `ci/app-tests` 5 jobs **383**. Total **≈ 7 430**. Outubro antes da
matriz: ≈ 4 000. O mês segue bem abaixo de 30 000.

## Passo 4 — documentação

* **(j)** `.circleci/config.yml`, comentário do cabeçalho: Chromium fora do CI
  com A12, F1 e o papel do `st.toggle`; a lacuna do Streamlit Cloud (reimplanta a
  cada push na `master` sem esperar o CI; o job detecta, não impede); por que o
  app roda só em `develop`, `master` e `ci/*` (plano Free); a regra de parada de
  custo, com as durações medidas (9,3–12,9 min por perna em 66 rodadas).
* **`CLAUDE.md`, "Fixed rules"** — **PARA REVISÃO DO DANILO**, uma linha:
  "Merge into `master` only with `app_test_floor` and `app_test_newest` green on
  the same commit in `develop`." (com a razão: Streamlit Cloud).
* **(k)** `docs/future_work.md` item 36: o medido nas etapas 0 e 1, a matriz, os
  controles com links, as lacunas (Chromium; app só depois do merge em
  `develop`; Streamlit Cloud), o backlog de empacotamento (`cmocean>=4.0`;
  pisos imprecisos de pandas e pyyaml; dívida de `install_requires`; pisos do
  app que não instalam juntos), os dois `insert(0)` da raiz em `research/labels`
  e a opção de ampliar o app para todas as branches.

## Verificação final (ponta de `ci/app-tests`)

Previsões, antes de medir: pipeline da ponta com `build_test` 1280 / 0 + 1 / 0 e
as duas pernas 1507 / 0 com a checagem OK, nenhuma publicação; local, receita
enxuta 1280 / 0 + 1 / 0; conda `-m "not browser"` 1508 / 0. (Desde `425a72f`
só mudaram comentários do config, `CLAUDE.md`, `docs/` e `research/`.)

Medido em **`66ac34e`** (commit de documentação do passo 4):

| o quê | previsto | medido | |
|---|---|---|---|
| pipeline [416](https://app.circleci.com/pipelines/gh/daniloceano/CycloPhaser/416) | 3 jobs, nenhuma publicação | `build_test`, `app_test_floor`, `app_test_newest` | ✔ |
| `build_test` ([593](https://circleci.com/gh/daniloceano/CycloPhaser/593)) | 1280 / 0 + 1 / 0 | **1280 / 0 + 1 / 0** | ✔ |
| `app_test_floor` ([592](https://circleci.com/gh/daniloceano/CycloPhaser/592)) | 1507 / 0, checagem OK | **1507 / 0**, OK, 605,4 s | ✔ |
| `app_test_newest` ([591](https://circleci.com/gh/daniloceano/CycloPhaser/591)) | 1507 / 0, checagem OK | **1507 / 0**, OK, 658,4 s | ✔ |
| local, receita enxuta | 1280 / 0 + 1 / 0 | **1280 / 0 + 1 / 0** | ✔ |
| local, conda `-m "not browser"` | 1508 / 0 | **1508 / 0** (`which python` = env `cyclophaser`, árvore limpa) | ✔ |

Logs: `logs/passo4/`. O commit seguinte (este registro) só muda `research/`
e roda o CI de novo, para que a própria ponta tenha pipeline; o resultado dele
fica no resumo da frente.

## Critérios (a)–(k)

| | critério | resultado |
|---|---|---|
| (a) | `cyclophaser/` e `setup.py` intactos | **PASS** — diff vazio |
| (b) | `build_test` mantém o comportamento | **PASS** — 1280 / 0 + 1 / 0 em 521, 523, 527, 529; passo de instalação inalterado |
| (c) | streamlit instalado, zero pulos por falta, job falha sem dependência | **PASS** — 5 pulos exatos em todo job do app; controle (c) vermelho com `UsageError` citando plotly |
| (d) | cyclophaser do wheel; trava de proveniência | **PASS** — sonda local e linha `cyclophaser.__file__` no CI em site-packages; controle (d) vermelho |
| (e) | regressão no código do app → vermelho; restaurar → verde | **PASS** — 412 vermelho com os 2 ids declarados, 413 verde |
| (f) | estabilidade | **PASS** — 58 / 58 |
| (g) | matriz do streamlit, cada perna verde | **PASS** — 1.56.0 e 1.65.0, 1507 / 0, freezes nos artefatos |
| (h) | nenhuma publicação sem querer | **PASS** — 411–415 sem job de publicação; validador por branch |
| (i) | `when: always`; `/tests` do job vermelho lista a falha | **PASS** — 522 / 524 |
| (j) | Chromium fora do CI, 3 defeitos e a lacuna escritos | **PASS** — comentário do config e item 36 |
| (k) | item 36 do `future_work.md` | **PASS** |

## Desvios das previsões

1. **Q9 (duração)**: a estimativa da etapa 0 (5,1–8,8 min) não valeu; as
   pernas levam 9,3–12,9 min em `medium`. A suposição A3 falhou: o passo de
   testes levou 560–642 s no CI contra 223–243 s locais. A regra de parada
   (20,03 min) não disparou.
2. **S4 (créditos do (f))**: previsto ≈ 6 300–6 900, medido 6 181 (segundos
   exatos), um pouco abaixo; 6 460 com arredondamento por minuto, dentro. As
   duas contagens ficam acima da estimativa da etapa 0 (2 999–5 023).
3. Nenhum teste falhou ou oscilou fora do controle (e). Nenhum teste errado
   ou instável foi encontrado.

### Desvios de instrumento (corrigidos, nenhuma previsão mudou)

1. `local_suite.sh` / `run_suite.sh`: com caminho de saída relativo, o
   `run_suite.sh` (que faz `cd` no clone) não achava a pasta. A primeira tentativa
   foi interrompida antes de qualquer resultado de pytest. Os caminhos passaram
   a ser absolutos e tudo foi refeito do zero.
2. `validate_config.py` quebrava (KeyError) no config antigo, que não tem
   `app_test`. Passou a tratar a ausência como fato falso.
3. Dois `python -c` de leitura de resumo tinham erros: um `git revert -q`
   inválido, que não commitou nada (refeito sem `-q`), e um filtro `Check` que
   casava com `Checkout`. Nenhum dado foi afetado.

## Arquivos

* `PREVISOES_passo1.md`, `PREVISOES_passo2.md`, `PREVISOES_passo3.md`
* `scripts/` — `common.sh`, `clone_at.sh`, `build_wheel.sh`, `make_venv.sh`,
  `run_suite.sh`, `local_suite.sh`, `conda_suite.sh`, `ci_probe.py`,
  `ci_pipeline.py`, `validate_config.py`, `add_negative_controls.py`,
  `make_stability_config.py`, `stability_summary.py`
* `logs/` — `grep_globs_before_sample_tracks.txt`, `passo1/`, `passo2/`,
  `passo3/`, `cost/`, `passo4/` (com gzip nos junit, saídas de pytest e
  `/tests` grandes)

## Correção antes do merge — `release/*` no filtro do `app_test` (2026-10-14)

Previsões: `PREVISOES_correcao.md` (`b30a176`, com push antes de medir).

**Motivo.** Releases saem de `release/*` direto para a `master`. Sem `app_test`
nessas branches, a regra "verde no mesmo commit em `develop`" não podia ser
cumprida numa release, e o Streamlit Cloud reimplanta assim que o commit chega
à `master`.

**Mudança.** No `.circleci/config.yml`, `/^release\/.*/` entrou no filtro do
`app_test`; esta é a única linha que não é comentário. O comentário do topo
passou a dar o motivo de cada branch do filtro. No `CLAUDE.md`, a linha do
Danilo, verbatim. No `docs/future_work.md` item 36, uma seção nova com a
correção e o motivo.

| id | previsão | medido | |
|---|---|---|---|
| K1 | config novo: schema OK; F1–F4 verdadeiros | schema 0 erros; `release/v9.9.9` e `ci/x` → `build_test` + as 2 pernas; `feat/x` → só `build_test`; `test_pypi_publish` só em `develop`, `pypi_publish` só em `master`; saída 0 | ✔ |
| K2 | controle, config de `fb516c5`: F1 falso | `release/v9.9.9` → só `build_test`; F1 False, F2–F4 True; saída 1 | ✔ |
| K3 | controle, `release/*` também no `test_pypi_publish`: F4 falso | `release/v9.9.9` ganha `test_pypi_publish`; F4 False; saída 1 | ✔ |
| K4 | diff do config, sem comentários: só `- /^release\/.*/` | só essa linha | ✔ |
| K6 (a) | diff `cyclophaser setup.py` vazio | vazio | ✔ |

O `validate_config.py` original também passa no config novo
(`logs/correcao/validate_config.json`). Nenhuma branch `release/*` foi criada no
remoto. K5 (pipeline da nova ponta) fica no resumo da frente; este commit é a
ponta e roda o CI.

Desvio de instrumento: o primeiro laço de shell não separou os argumentos (zsh
não quebra `$k` em palavras), e nenhum arquivo de resultado chegou a ser
escrito. A rodada foi refeita com chamadas explícitas.
