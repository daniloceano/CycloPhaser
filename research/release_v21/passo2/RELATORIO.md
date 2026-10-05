# Release v2.1 — parte A, passo 2 (aplicar e medir)

Branch `fix/relabel-recovery`, a partir de `0c4dbe6` (passo 1). Não houve merge e nenhum PR foi aberto.
**Resultado: PASS.** A detecção é idêntica nas 54 séries de treino. Só as 3 séries reetiquetadas
mudam, e os 20 itens da previsão batem. A suíte pela receita do CI deu 1279 passed / 0 failed.

## 1. Edição (`4b3b86e`)

Fiz a edição com `apply_relabels.py`. O script troca no texto atual só os blocos de `20150656`,
`20170409` e `20170154` pelos blocos da tag `0c63145` e confere que o resto do arquivo ficou idêntico
byte a byte. Isso inclui o cabeçalho (`updated` mantido), `20180170` e `s5dcc0f79`. O arquivo da tag
não foi copiado.

Antes de escrever, o script também confere, parseado, que cada bloco da tag é o registro atual mais
estas mudanças: o valor corrigido, o `labeled_at` novo e os campos de interface. O `superseded[0]` de
cada bloco é igual, campo a campo, ao registro de `develop-v2.1`.

`open_unsure`, `close_unsure` e `overlays_shown` **foram trazidos**, porque já existem em outros
registros do arquivo atual: são 48 ocorrências antes da edição.

## 2. Verificações — `checks.txt` (PASS)

* a. Os 82 registros (73 casos, vigentes e `superseded`) passam por `validate_phases`
  (com `n_steps`) e por `validate_verdict` sem erro e sem mudar, e nenhum é legado.
  `schema` continua 4 e `n_labels` continua 73.
* b. Diff parseado contra `develop-v2.1`: exatamente 3 ids mudam. Campos alterados:
  * `20150656`: `phases[3].start_idx` 91→100.
  * `20170409`: `phases[3].start_idx` 74→71.
  * `20170154`: `verdict.kind` boundary→ambiguous e `verdict.incipient_end_idx` 6→ausente.
  * Nos 3: `labeled_at` mudou, e `open_unsure`, `close_unsure`, `overlays_shown` e `superseded`
    passaram de ausente a presente.
* c. `first_blind_record` devolve os valores originais: residual 91, decay 74 e
  `{boundary, incipient_end_idx: 6}`. O registro vigente devolve os corrigidos.
* d. `swell_item30` está com 10/10 presentes e inalterados.

## 3–4. Medição e previsão — `baseline_train.txt`, `comparison.txt` (PASS)

`baseline_train.py` é a cópia do passo 1. Só mudam o título e o caminho no docstring. As saídas vão
para esta pasta, e `stage1_run_5075e49.py` foi copiado sem mudança. A configuração (`params-track`,
`5aa61f2d…`), o scorer e o `cyclophaser.__file__` em processo são os mesmos do passo 1.

| população | métrica | passo 1 | passo 2 |
|---|---|---|---|
| 35 reais | H/B | 8/17 | 7/16 |
| | C | 22/33 | 21/32 |
| | Q | 19/35 | 19/35 |
| | MAT | 27/33 | 28/33 |
| | fronteiras | 33/42 | 33/42 |
| | ambíguos (recusados) | 2 (1) | 3 (1) |
| | decay n/acertos/soma de erros | 17/15/38 | 17/15/35 |
| 54 treino | H/B | 19/30 | 18/29 |
| | C | 39/52 | 38/51 |
| | Q | 37/54 | 37/54 |
| | MAT | 44/50 | 45/50 |
| | fronteiras | 92/104 | 92/104 |

Linhas de CSV que mudaram:
* `20170154` em `scores`: veredito, `incipient_end_idx`, C e erro do incipiente.
* `20170409` em `scores` (MAT, erros, MAE) e em `boundaries` k3.
* `20150656` só em `boundaries` k3, e só a coluna do rótulo (91→100). Nenhum escore dessa série
  muda: a sequência não casa, então o residual não é pontuado.

## 5. Suíte — receita do CI (`run_suite_ci.sh`, `suite_ci_raw.txt`)

Rodei em uma worktree destacada de `7e12a49`, com venv novo em Python 3.12.9. Passos: build, wheel,
`pytest pyyaml` e `python -m pytest` na raiz, sem filtro de marcadores.
Resultado: **1279 passed, 0 failed**, exit 0.
