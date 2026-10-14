# Fechamento, passo 3b — streamlit 1.66.0 deixou `develop` vermelho (previsões, commit + push ANTES de medir)

Branch **`ci/fix-apptest-expander-count`**, de `origin/develop` = `06f56e8` (o
merge). O prefixo `ci/` faz o `app_test` rodar antes de qualquer merge. Data:
2026-10-14. Decisão do Danilo: corrigir o teste dentro do fechamento; os passos
4–6 do fechamento ficam para depois.

Entram com este commit os logs do diagnóstico do pipeline 419
(`logs/fechamento/`):
* job 602, `app_test_newest` com streamlit 1.66.0: **1506 / 1**;
* reprodução local na mesma seleção, com 1.66.0: 1506 / 1, o mesmo id.

Este commit leva `[skip ci]`: sem a correção, a perna newest ficaria vermelha
de novo, pelo mesmo motivo.

## O defeito, como lido no código (antes de medir)

`tests/test_calibrate_i2_apptest.py::test_no_expander_inside_an_expander_in_the_sidebar`
assume que `.expander` num bloco expander lista o próprio bloco
(`len(exp.expander) == 1` = "nenhum aninhado"). No 1.66.0 o job leu
`len(exp.expander) == 0` para 'Filtering options'.

## Correção (só esse teste)

Contar os expanders **descendentes** de cada grupo, excluindo o próprio grupo
por identidade (`[e for e in exp.expander if e is not exp]`), e exigir **0**.
O controle positivo `len(groups) == 8` fica. O comentário do teste passa a dar o
motivo (mudança do AppTest no 1.66.0). Só API pública do AppTest.

## Instrumento

`scripts/diag_expander.py`, fora de `tests/`. Ele monta dois apps mínimos via
`AppTest.from_string` e roda em três venvs novos, com o wheel de `06f56e8` e
streamlit 1.56.0, 1.65.0 e 1.66.0:
* um app com um expander (na sidebar e no corpo) contendo um checkbox;
* um app com expander dentro de expander.

## Previsões

| id | o quê | previsão |
|---|---|---|
| D1 | app plano: `grupo.expander` contém o próprio grupo | **1.56.0 e 1.65.0: sim** (lista = [o grupo]); **1.66.0: não** (lista vazia). Igual na sidebar e no corpo |
| D2 | app plano: contagem corrigida | **0** nas três versões, nos dois lugares |
| D3 | aninhar expander em expander | **não previsto**: não sei se cada versão permite ou levanta `StreamlitAPIException`; fica registrado como medido |
| D4 (controle +) | onde aninhar é permitido: contagem corrigida do grupo externo | **≥ 1** (= 1). Onde é proibido, o controle é a exceção do próprio streamlit, com a mensagem registrada por versão |
| L1 | local, seleção do job (`-m "not browser and not source_tree"`, as duas travas ligadas), commit da correção, venvs 1.56.0 / 1.65.0 / 1.66.0 | **1507 / 0** em cada; checagem de pulos `OK` |
| L2 | local, receita enxuta | **1280 / 0 + 1 / 0** (o módulo do teste pula inteiro sem streamlit) |
| C1 | CircleCI, pipeline do push da correção | jobs `build_test`, `app_test_floor`, `app_test_newest`, nenhuma publicação; `build_test` 1280 / 0 + 1 / 0; as duas pernas 1507 / 0, checagem `OK`; freeze do newest com **streamlit 1.66.0** (a não ser que saia uma versão mais nova antes do job; se sair, fica registrado) |
| A | `git diff 06f56e8 <ponta> -- cyclophaser setup.py tools` | vazio |
