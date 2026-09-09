# TAREFA 2 — rótulos dos tracks afetados

Escopo: tracks com `decai_no_idx0=sim` (ver `idx0_inventory.csv`, coluna medida
imediatamente após `find_decay_period`, antes de `find_incipient_period`) **e**
`split=treino`.

Dos 5 tracks com `decai_no_idx0=sim`, um é de teste (`20206498`, split=teste) —
excluído aqui por regra da tarefa. Não foi aberto nem inspecionado.

Os 4 tracks abaixo são transcrição literal do bloco YAML correspondente em
`research/labels/manual_labels.yaml` (schema 3). Nenhuma interpretação foi
adicionada.

---

## 20180170

```yaml
- id: '20180170'
  source: real
  series_sha256: 973acda6e116b414aef211b4ad5a16c3824b0923c2f899c0e43c307f85508b03
  labeled_at: '2026-09-08T13:47:44+00:00'
  n_steps: 69
  phases:
  - phase: incipient
    start_idx: 0
    tolerance_idx: 5
    unsure: false
  - phase: intensification
    start_idx: 20
    tolerance_idx: 1
    unsure: true
  - phase: mature
    start_idx: 34
    tolerance_idx: 1
    unsure: true
  - phase: decay
    start_idx: 43
    tolerance_idx: 1
    unsure: true
  verdict:
    kind: ambiguous
  tolerance_idx: 1
```

## 20180608

```yaml
- id: '20180608'
  source: real
  series_sha256: 98dfcca3c33b414cf53207c9bfefdd946774edaee99f4ed1ca23be0db92e1e99
  labeled_at: '2026-09-08T13:40:02+00:00'
  n_steps: 117
  phases:
  - phase: incipient
    start_idx: 0
    tolerance_idx: 5
    unsure: false
  - phase: intensification
    start_idx: 37
    tolerance_idx: 1
    unsure: false
  - phase: mature
    start_idx: 61
    tolerance_idx: 2
    unsure: false
  - phase: decay
    start_idx: 74
    tolerance_idx: 2
    unsure: false
  verdict:
    kind: boundary
    incipient_end_idx: 37
  tolerance_idx: 1
```

## 20190325

```yaml
- id: '20190325'
  source: real
  series_sha256: 9d30120f4f65621a20493b8410eede8113007087890931841a6f62761d7f328b
  labeled_at: '2026-09-08T13:37:37+00:00'
  n_steps: 167
  phases:
  - phase: incipient
    start_idx: 0
    tolerance_idx: 5
    unsure: false
  - phase: intensification
    start_idx: 10
    tolerance_idx: 1
    unsure: false
  - phase: mature
    start_idx: 95
    tolerance_idx: 2
    unsure: false
  - phase: decay
    start_idx: 110
    tolerance_idx: 2
    unsure: false
  verdict:
    kind: boundary
    incipient_end_idx: 10
  tolerance_idx: 1
```

## 20191014

```yaml
- id: '20191014'
  source: real
  series_sha256: 9008e9adf81a9c5915cd996d86d021687e6905b50819cd1dd24588c957a0201a
  labeled_at: '2026-09-08T14:04:33+00:00'
  n_steps: 206
  phases:
  - phase: intensification
    start_idx: 0
    tolerance_idx: 5
    unsure: false
  - phase: mature
    start_idx: 43
    tolerance_idx: 4
    unsure: false
  - phase: decay
    start_idx: 69
    tolerance_idx: 7
    unsure: false
  verdict:
    kind: none
  tolerance_idx: 0
```

---

Note: `20191014` não tem fase `incipient` rotulada (a sequência rotulada começa
em `intensification` no índice 0). Os outros três têm `incipient` rotulado
começando em 0. Nenhum destes 4 rótulos tem `decay` como primeira fase — em
todos, a primeira fase rotulada (após `incipient`, quando presente) é
`intensification`. Transcrição literal do YAML acima; nenhuma comparação com
a saída do detector foi feita neste arquivo (ver `REPORT.md` para isso).

---

## TAREFA 2b (rodada de continuação) — pergunta pendente

Pergunta: entre os 4 tracks afetados do treino, existe algum cuja primeira
fase não-incipiente, segundo o rótulo manual, seja decaimento?

**Não.** Nenhum dos 4.

Nos quatro blocos YAML acima, a primeira fase listada depois de `incipient`
(ou a primeira fase de todas, no caso de `20191014`, que não tem `incipient`
rotulado) é sempre `intensification`:

- `20180170`: `intensification` (`start_idx: 20`)
- `20180608`: `intensification` (`start_idx: 37`)
- `20190325`: `intensification` (`start_idx: 10`)
- `20191014`: `intensification` (`start_idx: 0`, sem fase `incipient` rotulada)

Nenhuma linha `phase: decay` aparece antes de uma linha `phase: intensification`
em nenhum dos 4 blocos. O track de teste equivalente (`20206498`) não foi
aberto nem procurado.
