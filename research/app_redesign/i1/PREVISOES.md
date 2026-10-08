# I1 — previsão (escrita antes de qualquer medição; não editar)

Data: 2026-10-05. Branch `feat/app-redesign`, base `origin/develop` @ d339c7d.
Nenhum número de tempo ou de contagem foi medido antes deste arquivo ser escrito.

## O que será medido

Com os 51 tracks de amostra carregados em Calibrate ("Load all test cyclones"),
duas interações, cada uma **antes** (develop @ d339c7d) e **depois** (esta branch):

1. **Label** — um clique em "Next ▸" na tela de rotulagem.
   - antes: aba Calibration, modo de exibição "Label";
   - depois: página "Manual labelling" (seção Developer, chave ligada).
2. **Benchmark** — um clique no checkbox "Show manual labels as a first column".
   - antes: aba Benchmark;
   - depois: página Benchmark.

Para cada interação, duas grandezas:

- **tempo**: do clique até o Streamlit terminar a execução (o indicador de
  execução `stStatusWidget` sai da página), no Chromium, viewport 1600×1000;
  5 repetições, reporta-se a mediana (e as 5).
- **detecção de Calibrate disparada**: número de chamadas à função cacheada
  `_run_get_periods` do app (acerto ou falta de cache, ambos contam) durante a
  interação. Contadas por um lançador de medição que envolve `st.cache_data`
  antes de o script rodar; o código do app não é alterado para medir.

## Previsão (a da frente, literal)

> Depois, as duas interações não disparam a detecção dos ciclones de Calibrate e
> ficam muito mais rápidas que antes.

Operacionalização, fixada aqui:

- "não disparam a detecção": 0 chamadas a `_run_get_periods` durante a
  interação, nas duas páginas, depois. (Antes, espera-se ≥ 51 por interação,
  uma por track carregado, porque o laço de pré-processamento roda antes da
  escolha do modo e das abas.)
- "muito mais rápidas": mediana depois ≤ 0,5 × mediana antes, em cada uma das
  duas interações.

Registro como observação. Não é critério de aprovação do portão.
