# Release v2.1 — parte A, passo 1 (somente leitura)

Branch `fix/relabel-recovery`, criada de `develop-v2.1` @ `4660b9d`.
Nenhuma mudança em `cyclophaser/` nem em `research/labels/manual_labels.yaml`.

## 1. Split

As 3 séries estão em **treino**: `research/labels/split.yaml:23` (`20150656`),
`:26` (`20170154`), `:28` (`20170409`) @ `4660b9d`. Nenhuma é teste.

## 2. Schema e diff mínimo

`schema: 4` no `manual_labels.yaml` da tag (`0c63145`) e no atual (`4660b9d`).
Os campos são os mesmos; nenhum mapeamento é necessário.

| série | campo | tag `0c63145` | atual `4660b9d` |
|---|---|---|---|
| 20150656 | `phases[3]` (residual) `.start_idx` | 100 (linha 190) | 91 (linha 648) |
| 20170409 | `phases[3]` (decay) `.start_idx` | 71 (linha 446) | 74 (linha 845) |
| 20170154 | `verdict` | `{kind: ambiguous}` (linhas 347–348) | `{kind: boundary, incipient_end_idx: 6}` (linhas 775–777) |

O diff mínimo do passo 2 (não aplicado):

```diff
 # 20150656
-    start_idx: 91        # linha 648
+    start_idx: 100
 # 20170409
-    start_idx: 74        # linha 845
+    start_idx: 71
 # 20170154
   verdict:
-    kind: boundary       # linha 776
-    incipient_end_idx: 6 # linha 777
+    kind: ambiguous
```

No terceiro campo, `incipient_end_idx` precisa sair junto: `labels_core.validate_verdict`
devolve só `{"kind": kind}` para `ambiguous` (`labels_core.py:409`).

Fora do diff mínimo, a tag também traz, nas 3 séries, `labeled_at` novo,
`open_unsure`/`close_unsure`/`overlays_shown` e um bloco `superseded` com o
registro anterior. Esse bloco é igual, campo a campo, ao registro atual de cada série.
A tag também difere do atual em `20180170` (só metadados: `labeled_at`, `open_unsure`,
`close_unsure`, `overlays_shown`, `superseded`) e em `s5dcc0f79` (só histórico `superseded`).
Nenhuma dessas diferenças muda um valor que o escore lê.

Os 10 rótulos de `swell_item30` estão presentes: `manual_labels.yaml:5,26,83,136,206,239,308,338,368,396`.

## 3. Veredito `ambiguous`

* `labels_core.score_labels` (`labels_core.py:775-792`): `boundary` entra em B, H,
  MAE e falsa recusa. `none` entra em N0/R. `ambiguous` sai de B, de H e do MAE.
  Ele só conta em `n_ambiguous` e, se o detector recusa, em `n_ambiguous_detector_none`.
* `stage1_run.per_series` (`stage1_run_5075e49.py:167-175`): `C` vira `None` para
  `ambiguous`. A série sai do numerador e do denominador de C = H + R sobre B + N0.
* `score_phase_sequences` (`labels_core.py:819-893`) e MAT não leem `verdict`.
  Q, erro de fronteira por fase e MAT de 20170154 não dependem dele.

## 4. Linha de base

O script de escore é `research/labels/diagnostics/item31/stage1_run.py@5075e49`
(blob `b6fae997`, cópia literal verificada em execução). Ele foi usado da mesma forma
que `stage1_smoke_train.py` usou no treino. A configuração é params-track,
sha256 `5aa61f2d…ccf04`. Ver `baseline_train.txt`.
O agregado nas 35 reais originais reproduz `stage1_smoke_train.txt` (P15, current):
C 22/33, Q 19/35, MAT 27/33.

Saídas: `baseline_train.txt`, `baseline_train.json`,
`scores_per_series_train.csv` (54 séries de treino),
`boundaries_per_series_train.csv`.
