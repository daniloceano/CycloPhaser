# Release v2.1 — parte B, passo 2 (preparar, sem publicar)

Branch `release/v2.1`, a partir de `6d968a4`. Nada foi publicado. Não houve merge em
`develop-v2.1` nem em `master`. A branch `develop` não foi criada e nenhuma tag foi criada.
O CHANGELOG **não** foi commitado: o diff está em `changelog.diff`, para revisão.

## Commits (um por item)

| item | commit | o quê |
|---|---|---|
| 1 | `bc26902` | `VERSION = '2.1.0'` em `setup.py:6`; `release = '2.1.0'` em `docs/conf.py:12`. Nenhum outro lugar. |
| 2 | `32d9fd4` | `python_requires=">=3.12"` e o classifier `Programming Language :: Python :: 3.12`. `install_requires` intocado. |
| 3 | `7b820df` | `license_files=["LICENSE"]`, com a evidência em `03_license_twine_check.txt`. |
| 4 | `32cbcf1` | CI: suíte contra o wheel com trava; marcador `source_tree`; passo separado para a fonte. |
| 5 | `0faf708` | `tools/calibration_app/requirements.txt:21` → `cyclophaser>=2.1.0`. |

## Item 3 — LICENSE

* **Origem de `license_files=[]`.** `git log -S license_files -- setup.py` encontra um único commit:
  `f423476` (2026-06-15), *"fix: suppress License-File wheel metadata and pin twine>=6.0 in CI"*.
  A mensagem diz que o setuptools≥69 escreve `License-File` (metadata 2.4) e que o
  `twine<6`, via `pkginfo<1.10`, não reconhece o campo, o que fazia o `twine check` falhar.
  O mesmo commit fixou `twine>=6.0` no CI, o que elimina essa causa. A supressão ficou redundante.
* **Resultado.** Build com setuptools 84.0.0 (isolado). `twine check --strict`, twine 7.0.0:
  wheel **PASSED**, sdist **PASSED**, exit 0. O wheel contém
  `cyclophaser-2.1.0.dist-info/licenses/LICENSE` e o METADATA traz `License-File: LICENSE`.
  O sdist contém `cyclophaser-2.1.0/LICENSE`. Não foi preciso reverter.

## Item 4 — CI (`.circleci/config.yml`, job `build_test`)

O passo "Run tests" (`python -m pytest --junitxml=test-reports/results.xml`) foi substituído por dois passos:

1. **Run tests against the installed wheel.** Usa `CYCLOPHASER_REQUIRE_INSTALLED=1` e roda
   `pytest --import-mode=append -m "not source_tree" --junitxml=test-reports/results.xml`.
   Usa `pytest` sem `python -m`, que poria o CWD em `sys.path[0]`. O `append` põe a raiz depois
   do site-packages.
2. **Run source-tree tests against the checkout.** Roda
   `python -m pytest -m source_tree --junitxml=test-reports/results-source-tree.xml`, sem a trava.

`store_test_results` continua lendo `test-reports/`, agora com os dois junit. Os jobs
`test_pypi_publish` e `pypi_publish` e o workflow não foram tocados.

**Trava (`tests/conftest.py`).** Só age com a variável definida e não vazia nem `0`:

* Em `pytest_configure`, importa `cyclophaser`. Se `__file__` não tiver `site-packages` no
  caminho, lança `pytest.UsageError` com o caminho. A sessão termina com exit 4.
* O cabeçalho da sessão imprime `cyclophaser.__file__`.
* Em `pytest_sessionfinish`, relê todos os módulos `cyclophaser*` de `sys.modules`. Se algum
  veio de fora do site-packages, a sessão falha (exit 1) e cada um é listado no resumo.
* Sem a variável, nada é importado nem verificado. Em todo run o resumo final imprime
  `cyclophaser.__file__ (in session)`, lido de `sys.modules`.

**Testes marcados `source_tree`: um só.** É
`tests/test_item30_spare_intensification.py::test_params_track_reproduces_the_counterfactual_in_the_five`.
Ele importa `research/labels/diagnostics/item30/item30_core.py`, cuja linha 66 faz
`assert Path(cyclophaser.__file__).resolve().is_relative_to(REPO)`. Essa guarda
anti-sombreamento recusa por desenho qualquer cópia instalada. Os outros 19 testes do mesmo
módulo passam contra o wheel e continuam no passo principal. Procurei nos testes importações
de todo módulo de pesquisa com guarda desse tipo (`item30_core`, `figs_cf`, `item31_core`,
`hygiene_train`, `params_track_vs_defaults`, `default_behaviour_hash` e os de `research/cleanup/`).
Só esse teste importa um deles. Isso é coerente com o A2 do passo 1, que deu exatamente essa
1 falha.

## Item 7 — verificação local

Feita por `run_ci_steps.sh 0faf708`, com saída bruta em `07_ci_steps_raw.txt` e contagens do
junit em `07_ci_steps_summary.json`.

* Worktree destacada e limpa de `0faf708` (0 arquivos alterados) e venv **novo** com Python 3.12.9.
* Os comandos do job, copiados do `config.yml` desse commit e rodados na raiz da worktree:
  `pip install --upgrade pip build`, `python -m build`, `pip install dist/*.whl` e
  `pip install pytest pyyaml`, seguidos dos dois passos.
* Sem playwright, como no CI.

| passo | `cyclophaser.__file__` impresso | passed | failed | skipped |
|---|---|---|---|---|
| principal (wheel, com trava) | `<venv>/lib/python3.12/site-packages/cyclophaser/__init__.py` (no cabeçalho e no resumo) | **1278** | **0** | 35 |
| fonte (`-m source_tree`) | `<wt>/cyclophaser/__init__.py` | **1** | **0** | 8 |

* Os 8 skips do passo da fonte são os 8 módulos pulados na **coleta**: os 7 de app/streamlit
  mais `test_label_browser`. Um pulo na coleta acontece antes da seleção por marcador, por isso
  reaparece. Todos estão contidos nos 35 do passo principal, e a união dos dois passos é
  **35**, como esperado.
* **Wheel:** `cyclophaser-2.1.0-py3-none-any.whl`, que contém
  `cyclophaser-2.1.0.dist-info/licenses/LICENSE`. sha256 `c0ae777c28aadcbb…`.

Controles da trava, fora do job, rodados na mesma venv depois dos dois passos:

* **C1:** `CYCLOPHASER_REQUIRE_INSTALLED=1 python -m pytest …` importa a fonte. A sessão é
  **recusada**, com exit 4 e o caminho `<wt>/cyclophaser/__init__.py` impresso.
* **C2:** um teste temporário apaga `cyclophaser*` de `sys.modules` e reimporta da fonte.
  O teste em si **passa**, mas a sessão sai com **exit 1** e lista os 5 módulos vindos de `<wt>`.
  Isso mostra que a checagem de fim de sessão pega uma troca tardia.

## Item 8 — CircleCI

Ver a seção "CircleCI" no fim. O status e as contagens foram lidos da API pública v2 do
CircleCI e da API de status do GitHub, sem token.

## Item 6 — CHANGELOG (não commitado)

`changelog.diff` aplica limpo sobre `0faf708` (`git apply --check`). O que o diff faz:

* `[Unreleased]` fica vazio no topo, e abaixo dele entra `## [2.1.0] - 2026-10-03`.
* No topo da 2.1.0 entra a seção "Changed default results": `params-15` (hoje `params-track`)
  virou default, `boundary_padding` passou a `"reflect"`, e os mesmos dados podem dar fases
  diferentes das da 2.0.0.
* Seguem as entradas que faltavam, listadas no passo 1:
  * `prominence`/`prominence_relative` (`9e44c48`);
  * `length_scale`, `mature_method`, `mature_amplitude_fraction` e
    `decay_tail_amplitude_fraction` (`7d489ab`);
  * `incipient_plateau_spare_intensification` (`5434d87`);
  * app: Layer Inspector, aba Label e aba Benchmark, mais os parâmetros inertes;
  * build/CI: os commits pós-2.0.0 e as mudanças deste passo;
  * remoção de `.pypirc` e `Pipfile`.
* Os blocos que já estavam em `[Unreleased]` passam, sem edição, a pertencer à 2.1.0.
* Entram os links `[Unreleased]` e `[2.1.0]`. Eles só resolvem depois que a tag `v2.1.0` existir.

## CircleCI

`build_test` **#464**, de 0faf708 na branch `release/v2.1`. O status e as contagens foram
lidos sem token: o job pela API v2, a saída dos passos pela API v1.1 e o status do commit
pela API de status do GitHub.

* **Status:** `success`. O passo "Install package from wheel" saiu com 0.
* **Passo principal (wheel, com trava):** `__file__` =
  `/home/circleci/.pyenv/versions/3.12.3/lib/python3.12/site-packages/cyclophaser/__init__.py`,
  impresso no cabeçalho e no resumo. Resultado: **1278 passed, 0 failed**, 35 skipped, 1 deselected.
* **Passo da fonte:** `__file__` = `/home/circleci/project/cyclophaser/__init__.py`.
  Resultado: **1 passed, 0 failed**, 8 skipped, 1305 deselected.
* **Relatório de testes do job:** junta os dois junit. São 1322 casos: 1279 `success`
  (1278 + 1), 43 `skipped` (35 + os mesmos 8 pulos de coleta) e 0 falhas.

O commit deste relatório também dispara um `build_test`. O resultado desse job está na
mensagem de entrega, não aqui.
