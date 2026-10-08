# I3 — inventário 1-para-1 (portão b)

Antes: 6016486 (ponta do I2, checkout separado). Agora: árvore de trabalho do I3.

**Gerado por script:** `make_inventory.py`, em duas partes.

1. **Chaves de widget** (barra lateral, área central, diálogos): o coletor do I2
   (`research/app_redesign/i2/make_inventory.py`), reaproveitado sem mudança →
   `inventory_main_widgets.md` (dados em `inventory_{before,after}_widgets.json`).
2. **Área central, função por função** → `inventory_main.md` (dados em
   `inventory_{before,after}.json`). A página Calibrate roda pelo AppTest (API
   pública) com os 51 tracks de amostra nos estados que desenham toda a área
   central:
   - sem dados (público);
   - Grid de 2 colunas, com e sem a chave;
   - Grid de 1 coluna (downloads por track, análise passo a passo, diagnóstico
     detalhado);
   - sonda incipiente ligada;
   - Inspector.

   Cada elemento vira uma função (subheader, expansor, download, imagem, tabela
   com as colunas, métrica, widget com a chave) e é atribuído a um TRACK (o que é
   desenhado sob o nome dele na grade) ou à PÁGINA. Onde há páginas de grade (I3),
   o coletor percorre todas com o botão público "Next ▶" e junta os registros por
   track. Assim, "por track" quer dizer "acessível para aquele track em alguma
   página".

## Resultado

- **Por track, em todos os estados com dados: 51/51 tracks com as mesmas funções
  antes e depois.**
  - Grid de 2 colunas com a chave: figura, "⚠️ Mark as bad" e o nome do track,
    51 cada.
  - Grid de 1 coluna: figura, "Step-by-step analysis", "Detailed diagnostics",
    tabela de fases, "⬇ Download CSV" e "⬇ Download PNG", 51 cada, mais os mesmos
    11 avisos.
  - Sonda ligada: o expansor "Incipient probe" nos 51.
- **Por página: nenhuma função marcada GONE.**
  - Seletor de modo, "Grid columns", tabela consolidada (com os 51 tracks, em toda
    página), resumo de casos ruins e "Clear bad-case marks" (com a chave): todos
    continuam.
  - Inspector: os mesmos 11 elementos antes e depois. Não mudou.
- **Chaves de widget:**
  - nenhuma some;
  - novas: `start_example`, `start_sample`, `grid_page_size`, `grid_prev_top`,
    `grid_next_top`;
  - `grid_prev_bottom` e `grid_next_bottom` também são novas. Elas só são
    desenhadas com mais de uma página, e o coletor do I2 usa o exemplo (1 track);
    por isso aparecem na tabela por página de `inventory_main.md`, não na lista de
    widgets.
- **`_DEFAULTS`:** 45 = 45, nenhuma diferença. As 45 chaves e as 39 de
  `_PARAM_WIDGET_KEYS` continuam desenhadas.

## Aposentadoria (aprovada na frente)

| O quê | Onde estava | Agora |
|---|---|---|
| Linha única "No tracks loaded — use step 1 in the sidebar." | área central, sem dados | tela inicial: título, duas frases, os 4 passos, "Try example data" e "Sample data (51 TRACK cyclones)" (mesmas ações do passo 1), link para a documentação. Continua sem detecção: `test_the_start_screen_explains_and_runs_no_detection` |

Ela não aparece como GONE na tabela porque o inventário não registra texto
corrido (markdown e legendas). A troca está registrada aqui e nas capturas
(`captures/{before,after}/start.png`). Os quatro testes que procuravam a linha
foram ajustados para o título da tela inicial, com o motivo em comentário:

- `test_app_passo5_fixes.py`;
- `test_calibrate_i2_apptest.py::test_without_data_no_detection_runs`;
- dois pontos de `test_app_pages_browser.py`.

## Mudou de forma, função mantida

| O quê | Antes | Agora |
|---|---|---|
| Figuras da grade | todos os tracks numa página só | só a página atual (12/24/48, padrão 12); todo track continua acessível pela navegação (51/51 acima). Detecção, tabela consolidada e estatísticas continuam sobre todos |
| "⬇ Download CSV" / "⬇ Download PNG" (Grid de 1 coluna) | sob cada track | iguais, sob cada track da página |
| "⚠️ Mark as bad" (com a chave) | sob cada figura | igual, sob cada figura da página. As marcas de tracks fora da página sobrevivem (testado: página 2, Inspector, Benchmark → Calibrate) |
| Aviso do YAML importado | "Ignored unknown keys: …" | "Ignored keys: …". A lista agora também pode trazer "evaluation (developer only)", que não é uma chave desconhecida |
| Seção `evaluation` de um YAML importado sem a chave | restaurava as marcas | ignorada e listada como "evaluation (developer only)". Com a chave, igual a antes |

## Novo

- Tela inicial (acima).
- Controles de página: "Tracks per page", "◀ Previous" e "Next ▶" (em cima, e
  embaixo quando há mais de uma página) e "Page N of M · tracks a–b of T".
- "Set statistics", no fim da grade, depois da tabela consolidada:
  - métricas Analysed, Failed e "Whole cycle, median (h)";
  - tabela por chave de fase do pacote ("intensification", "intensification 2",
    …, sem juntar ocorrências): n e % de tracks, mediana da duração e n das
    durações;
  - box com pontos por chave, e para o ciclo inteiro, com o n no rótulo;
  - legenda das durações, com quantos tracks entram e quantos ficam fora por não
    ter datas;
  - as 5 sequências mais comuns, numa tabela HTML (markdown nativo do
    Streamlit): um quadrado por fase, com as cores das figuras e o número da
    repetição dentro do quadrado; os nomes em texto; o número de tracks.

  Só no modo Grid: o Inspector não muda.

## Ajustes da pausa (d)

- **`n_cols` ("Grid columns")** entrou na preservação de estado
  (`_CALIBRATE_KEEP_KEYS`): agora sobrevive a Grid → Inspector → Grid e à troca
  de página do app. Antes do I3 se perdia ao passar pelo Inspector. O teste
  falhou antes da correção (`assert 2 == 3`) e passa depois.
- **Cores de fase:** `app.py` não tem mais cópia própria; lê
  `layer_inspector.PHASE_COLORS`, de onde o Inspector já lia.
  - `tests/test_phase_colors.py` compara essa fonte com o `colors_phases` de
    `cyclophaser/plots.py`, lido do arquivo com `ast`;
  - confere que `app.py` e `set_stats.py` não redigitam as cores;
  - confere que as cópias das páginas Benchmark e Label, fora do escopo, não
    divergiram.
- Nenhuma função muda de lugar por esses ajustes. A tabela de sequências deixou
  de ser um `st.dataframe` e virou markdown; por isso o inventário a registra como
  texto, não como tabela.
