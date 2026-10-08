# Fechamento da frente de redesenho do app (sem o I4) — preparação, sem merge

Branch `feat/app-redesign`, ponta **4f83334**. Data: 2026-10-08.

Decisão do Danilo (2026-10-08): a frente fecha sem o I4, porque a rodada com os
três amigos não voltou a tempo.
- Critério (e) não cumprido: a usabilidade foi conferida só pelo desenvolvedor.
- I1, I2 e I3 em PASS.
- Se o retorno chegar depois, abre-se uma frente nova só para ele, com as mesmas
  7 tarefas e o mesmo critério; esta frente não reabre.

**Nada desta preparação está commitado.** `docs/` espera a revisão do build local
pelo Danilo. O CHANGELOG e estes registros ficaram junto, para entrar no mesmo
commit depois da revisão.

## 1. Read the Docs

Páginas mudadas:
- **`docs/calibration_tool.rst`**, reescrita. Cobre:
  - o menu de páginas (Calibrate e Benchmark), e o fato de que páginas e funções
    de desenvolvedor não existem no app público;
  - a tela inicial;
  - a barra lateral em passos (1 · Data, 2 · Starting configuration,
    3 · Filtering, Advanced, 4 · Save results);
  - Grid paginada e Inspector;
  - Set statistics;
  - Save results e o conteúdo do ZIP;
  - o `parameters.yaml` num script;
  - como rodar localmente.
- **`docs/future_work.md`**: item 34 (abaixo).
- `index.rst` e `testing.rst` mencionam o app, mas o que dizem continua certo
  (o link do app hospedado; os testes marcados `browser`). Ficaram como estavam.

Figuras novas, em `docs/generated/`:
- `app_start.png`, `app_sidebar.png`, `app_grid.png`, `app_statistics.png`,
  `app_save.png`;
- geradas por **`docs/figures/make_app_screenshots.py`**, um script versionado
  que segue o padrão dos outros de `docs/figures/`. Ele sobe o app **público**
  deste checkout (sem `CYCLOPHASER_APP_DEV`), usa os 51 tracks de amostra, os
  defaults e uma janela de 1440×900 (2300 de altura para a barra lateral);
- geradas no env conda `cyclophaser`, streamlit 1.63.0.

**Build num checkout limpo**, com `build_docs_clean.sh`:
- worktree destacada de HEAD, mais as mudanças sem commit de `docs/` e
  `tools/calibration_app/`;
- venv nova com `docs/requirements.txt` e o pacote instalado do checkout, como no
  `.readthedocs.yaml`;
- `sphinx-build -b html -E`.

| build | avisos do Sphinx |
|---|---|
| base, 4f83334 sem mudanças (`docs_build_base_4f83334*.txt`) | 0 |
| com as mudanças, árvore final (`docs_build_review_final*.txt`) | **0** |

No HTML gerado entram as 5 figuras. O `:repo:` do README do app aponta para
`master`, então só resolve depois do merge, como os outros links do site.

**Como o Danilo constrói localmente** (da raiz do repositório, na branch, com as
mudanças ainda sem commit):

```bash
SCRATCH=/tmp/cp_docs bash research/app_redesign/close/build_docs_clean.sh danilo
open /tmp/cp_docs/docs_danilo/docs/_build/html/calibration_tool.html
```

Ou direto na árvore de trabalho, sem checkout limpo, com o env que tiver Sphinx
7.2.6 e o tema (`pip install -r docs/requirements.txt`):

```bash
python -m sphinx -b html -E docs docs/_build/html
open docs/_build/html/calibration_tool.html
```

## 2. Registro: `docs/future_work.md`, item 34

Contém:
- o que cada incremento entregou e o veredito: I1, I2 e I3 em PASS, mais as duas
  correções da falha intermitente;
- (e) não cumprido, com o motivo e a regra de reabertura;
- as medições 39,1 → 13,2 → 5,0 s;
- as pendências: as execuções sobrepostas sem explicação; o CI não testa o app;
- as quatro lições.

O que o CI não testa:
- no I1 eram 211 testes;
- agora são **241**: a suíte conda passa 1485, e a receita do CI 1281 (1280 + 1);
  204 só rodam no env conda, e os 37 de Chromium não rodam em nenhuma das duas.

## 3. `CHANGELOG.md`

Entrada `[Unreleased]` só com o app:
- páginas; Calibrate (passos, Save results, tela inicial, grade paginada,
  estatísticas, versão exibida, `evaluation` sem a chave); dois Fixed;
- diz que o pacote não muda e que o app pede `streamlit>=1.56.0`;
- a versão do pacote não mudou (2.1.0).

## 4. Suítes sobre a ponta final

Ponta: 4f83334 mais as mudanças sem commit acima, que não tocam código. Rodadas
em sequência, sem nada concorrendo.

| | streamlit 1.56.0 (piso) | streamlit 1.63.0 (env conda) |
|---|---|---|
| testes de app | **203 passed, 0 failed** (`app_tests_st1.56.0.txt`) | **203 passed, 0 failed** (`app_tests_conda_st1.63.0.txt`) |
| Chromium completo | **37 passed, 0 failed** (`browser_tests_st1.56.0.txt`) | **37 passed, 0 failed** (`browser_tests_conda_st1.63.0.txt`) |

- **Suíte conda** (`-m "not browser"`): **1485 passed, 0 failed**
  (`suite_conda_raw.txt`).
- **Receita do CI**: **1280 passed, 0 failed** contra a wheel e **1 passed,
  0 failed** em `source_tree` (`ci_recipe_summary.json`, `ci_recipe_raw.txt`).
- `manual_labels.yaml` não foi tocado (0 linhas de `git status` nos executores do
  Chromium).
