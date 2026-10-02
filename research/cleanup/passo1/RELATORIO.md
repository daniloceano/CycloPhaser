# Passo 1 — relatório (gerado)

Gerado por `passo1/make_report.py` a partir das saídas de `passo1/`. Previsões: `passo1/PREVISOES.md`, versionado em `d8a19cc` antes de qualquer medição deste passo.

## Previsões

| id | previsto | obtido | confere |
|---|---|---|---|
| P1 | digest pré-C1 = `3a6de265…`; pós-C1 ≠ `3a6de265…` | pré `3a6de265…` (HEAD `f17d802`, 47 séries); pós `7552bc67…` (HEAD `742e685`) | sim |
| P2 | sha256(params-track) = sha256(params-15 antes) | `5aa61f2dec71…` → `5aa61f2dec71…`, bytes idênticos: True | sim |
| P3 | 0 exceções; todas as sequências válidas | exceções default/edge 0/0; inválidas 0/0 (n=54) | sim |
| P4 | recusas de incipient sob reflect = 0 | **28/54** (edge: 28/54, as mesmas séries) | **NÃO** |
| P5 | mapas que mudam entre default e edge > 0 | 19/54 (sequências: 3) | sim |
| P6 | suíte pós-C1: 0 falhas | 1438 passed / 0 failed (HEAD `742e685`) | sim |

## Higiene (treino, sem pontuação)

`passo1/hygiene_train.md` (tabela por série) e `.json`. Séries: 54 (batch swell_item30: 7, top-level real: 35, top-level synthetic: 12).

| medida | default (reflect) | edge |
|---|---|---|
| exceptions | 0 | 0 |
| invalid_sequences | 0 | 0 |
| refusals | 28 | 28 |
| defect_I | 11 | 10 |
| dz_t0_rel_zero | 0 | 0 |
| dz_t0_rel mediana / máx | 0.065 / 0.172 | 0.295 / 0.802 |

Mapas que mudam: 19; sequências que mudam: 3.

**Por que P4 falhou (post-hoc, `refusal_mechanism.py`, declarado depois da medição):** o default `incipient_plateau_signal="vorticity"` mede o platô na série BRUTA, onde o padding não chega. Recusas por sinal × padding: vorticity/reflect: 28/54; vorticity/edge: 28/54; derivative/reflect: 2/54; derivative/edge: 32/54.

## Rastreabilidade

* Portão (a): commits que tocam `cyclophaser/` desde origin/develop-v2.1: `742e685` (C1 = `742e685`) — confere. Saída: `passo1/gate_a.txt`.
* params-15: vivas restantes **0**; históricas 251 em `d8a19cc` → 251 em HEAD, idênticas: True; notas de correspondência: 12 (`passo1/params15_refs.json`).
* params-track × defaults: diferem só em `filter_params.use_filter` (yaml True, default 'auto'), `filter_params.boundary_padding` (yaml 'edge', default 'reflect'); chaves de detecção ausentes do YAML: `prominence`.
* Baselines do CI: `passo1/rebaseline_ci_raw.txt` (gerador `item31/regenerate_baselines_2b.py`).
* Manifesto: "apagar" 30 = 30 ancestrais + 0 só patch-equivalentes.
* requirements.txt da raiz — quem lê: user docs: docs/contribute.rst:43; user docs: docs/installation.rst:27; user docs: docs/installation.rst:66.
* Suíte: linha final `1438 passed, 1 skipped, 29 deselected, 89 warnings in 413.23s (0:06:53)`, medida em `742e685` (o C1). O commit seguinte só muda comentários, docstrings e textos de ajuda: `passo1/commit4_ast_check.txt` → 742e685..052a876: 4 .py file(s); code unchanged: True.
