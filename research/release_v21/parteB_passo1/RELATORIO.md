# Release v2.1 — parte B, passo 1 (somente leitura)

Branch `release/v2.1`, criada de `develop-v2.1` @ `76b7932`. Nada foi alterado em versão,
CI, CHANGELOG, app ou branches. Este passo só acrescenta esta pasta. Não houve merge nem PR.
Não proponho número de versão.

| item | arquivo | resultado em uma linha |
|---|---|---|
| 1 | `01_pypi_versions.txt` | PyPI: 1.2.1 … 2.0.0 (34 versões). TestPyPI: 1.2.0 … 1.9.4 (31), sem 2.0.0. **2.1.0 não existe em nenhum dos dois.** |
| 2 | `02_version_strings.md` | `setup.py:6` `VERSION = '2.0.0'` (única fonte da distribuição) e `docs/conf.py:12` `release = '2.0.0'`. Não há `__version__`, `CITATION.cff` nem codemeta. |
| 3 | `03_master_vs_develop.txt` | master `0df0ef5` é ancestral de develop. 0 commits só em master. 256 só em develop (52 first-parent). 603 arquivos, +139295/−1283. |
| 4 | `04_ci.md` | Só CircleCI, Python 3.12.3. `build_test` roda em todo push. TestPyPI só na branch `develop`, que não existe. PyPI em todo push em `master`, com `--skip-existing`. Autenticação por credencial em variável de ambiente do CircleCI; não é trusted publishing. |
| 5 | `05_import_mode.md` | O CI importa a **fonte**. A1 (`pytest --import-mode=importlib`) e A2 (`pytest --import-mode=append`), ambos na raiz, importam o **wheel** com 1278/1/35. A falha é a guarda de `item30_core.py:66`. Fora da raiz há +19 falhas por caminhos relativos ao CWD. |
| 6 | `06_wheel_contents.md` | Nenhum arquivo da fonte do pacote falta no wheel; os 6 são byte-idênticos. Ficam de fora `LICENSE` (`license_files=[]`) e, no sdist, os dados de `tests/`. |
| 7 | `07_python_requires.md` | Sem `python_requires`; o único classifier de Python é `:: 3`. O CI testa só 3.12. As dependências já exigem ≥3.10. |
| 8 | `08_app.md` | `tools/calibration_app/requirements.txt:21` `cyclophaser>=2.0.0`. O import é por nome. O app mostra a versão lida do `setup.py` da checkout. O CI pula 146 testes em 7 módulos inteiros, mais 26 parciais e o módulo de browser. Descrevo a receita contra o PyPI, sem rodá-la. |
| 9 | `09_changelog.md` | `[Unreleased]` tem 21 blocos. Faltam entradas para os parâmetros de `9e44c48`, `7d489ab` e `5434d87`, para 6 mudanças do app e para todo o build/CI pós-`v2.0.0`. |

Scripts: `run_import_and_wheel.sh` (itens 5 e 6, com worktree destacada e venv novo) e
`cp_import_probe.py` (plugin de pytest que lê `cyclophaser.__file__` dentro da sessão).
