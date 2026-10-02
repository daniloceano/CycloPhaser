# Critério (b) na sequência do CI — previsões declaradas ANTES de qualquer correção

Do prompt de 2026-10-02 ("correção antes do merge"), sem ajuste. Versionadas
antes de medir (b-ci) e antes de qualquer edição de teste ou arquivo; a ordem é
verificável por `git log`.

| id | previsão |
|---|---|
| (b-ci) | sequência do CI, reproduzida localmente num ambiente novo com Python 3.12: `pip install --upgrade pip build`; `python -m build`; `pip install dist/*.whl`; `pip install pytest pyyaml`; `python -m pytest` na raiz, sem filtro de marcadores. **Antes** da correção: **7 falhas, todas em `tests/test_app_passo5_fixes.py`**. **Depois**: **0 falhas**. |
| (b-conda) | suíte `-m "not browser"` no ambiente conda `cyclophaser`: **0 falhas** antes e depois. |
| digest | digest default (gerador canônico) igual a `7552bc67…` na mesma sessão. |

## Definições operacionais (fixadas aqui, antes de medir)

* **Sequência do CI:** os passos do job `build_test` de `.circleci/config.yml`,
  na mesma ordem e com os mesmos comandos, numa cópia limpa da branch (git
  worktree destacado no commit medido), dentro de um venv novo criado com
  `python3.12 -m venv` (o CI usa a imagem `cimg/python:3.12.3`; aqui a versão de
  patch é a do Python 3.12 local, registrada na saída). O `--junitxml` do CI é
  mantido, gravado fora da cópia. Nada mais é instalado no venv.
* **Falhas:** testes com `failure` ou `error` no junit; erros de coleta contam
  como falha. Só passed/failed são previstos; skipped é registrado, não previsto
  (CLAUDE.md).
* **(b-conda):** `python -m pytest -m "not browser"` numa cópia limpa, no
  ambiente `cyclophaser`, com `cyclophaser.__file__` conferido dentro da cópia.
* **"Antes"** = commit desta previsão; **"depois"** = commit da correção.
* **Critério (b) do portão final:** PASS só se (b-ci) depois e (b-conda) depois
  derem 0 falhas.
