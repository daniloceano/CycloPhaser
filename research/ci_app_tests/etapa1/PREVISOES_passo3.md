# Etapa 1, passo 3 — previsões da estabilidade (f) (commitadas e com push ANTES do push da matriz)

Branch descartável **`ci/app-tests-stability`**, criada da ponta do passo 1 em
`ci/app-tests` (o commit deste arquivo; o código e o CI são os de `425a72f`,
`git diff 425a72f <este commit> -- .circleci tests tools cyclophaser setup.py`
vazio). Um único commit S muda só o `.circleci/config.yml` desta branch, por
`scripts/make_stability_config.py`:

* `app_test` ganha um parâmetro inteiro fictício `run`, que nenhum passo usa —
  todo passo do job fica idêntico ao do passo 1;
* o workflow vira **um só** item de matriz, `leg` × `run` (1..29) = **58 jobs**,
  `app_test_<leg>_<run>`, `medium`, filtro só `ci/app-tests-stability`;
* **sem `build_test` e sem nenhum job de publicação** (economia de créditos;
  o `build_test` não é objeto do (f)).

## Previsões

| id | o quê | previsão |
|---|---|---|
| S1 | jobs no pipeline do commit S | **58**, todos `app_test_*`, nenhum `build_test`, nenhum de publicação |
| S2 (f) | resultado | **58 de 58 verdes**; cada um **1507 passed / 0 failed** e o passo de checagem de pulos com `OK` |
| S3 | regra de contagem (fixada na etapa 0) | qualquer job não verde conta como falha, **seja qual for a causa**, inclusive infraestrutura; diagnóstico variando rede e CPU, nunca reclassificação |
| S4 | créditos gastos (registro, não critério) | estimativa da etapa 0: 2 999–5 023. **Refeita com as durações medidas no passo 1 e no passo 2** (pernas de 10,8 a 11,9 min, jobs 519, 520, 522, 524, 525, 526), a 10 créditos/min em `medium`: **≈ 6 300–6 900** créditos, **acima** da estimativa da etapa 0 (a suposição A3 — `medium` na velocidade dos limites de 0.7 — não se confirmou: o passo de testes levou 578–642 s contra 210 s locais). Consumo de outubro até agora, estimado pela API (83 jobs, durações × tarifa da classe): **≈ 4 000**. Com o (f), o mês fica bem abaixo de 30 000 |

Alcance do (f) (da etapa 0): N = 29 por perna detecta, com 95 %, uma
intermitência com p ≥ 9,81 % por rodada.
