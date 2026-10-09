# I1 (página Compare) — previsão (escrita, commitada e enviada antes de qualquer medição; não editar)

Data: 2026-10-08. Branch `feat/benchmark-review`, base `develop` @ `39e658c`.
Nenhum número desta frente foi medido antes deste arquivo ser commitado e enviado.
Os números de referência citados abaixo vêm do registro do item 34
(`docs/future_work.md`, `research/app_redesign/close/`), não de medição nova.

## 1. Suíte

Estado de partida, do registro (árvore de `6102b03`, igual à de `39e658c` fora de
`docs/`): env conda `cyclophaser` (streamlit 1.63.0) **1485 passed / 0 failed** com
`-m "not browser"`; receita do CI **1280 / 0** contra o wheel e **1 / 0** no
source tree.

Testes novos planejados (todos atrás de `pytest.importorskip("streamlit")`, só API
pública do AppTest):

`tests/test_compare_core.py` (8): relativo contra si mesmo sem mudança; mudança de
sequência e deslocamento de fronteira; contagem "incipient absent" por coluna;
diferenças de parâmetros tolerantes a ruído de float; chave da série pelo conteúdo,
não pelo nome; chave da configuração efetiva independente da ordem e da forma
(`use_filter` True vs `'auto'`); chaves completadas e ignoradas de um YAML; a frase
das chaves completadas é a mesma função na Calibrate e na Compare.

`tests/test_compare_apptest.py` (22): Compare no menu Calibration depois de
Calibrate; estado vazio com link para Calibrate; recebe os tracks da Calibrate, todos
selecionados; All / Invert / Clear e escolha individual; "Current settings" = o
`_bench_live_config` publicado; "Defaults" = o que o botão Defaults da Calibrate
põe; Run bloqueado sem colunas, motivo em texto visível; Run bloqueado sem seleção,
idem; nada recalcula ao editar e o resultado fica marcado desatualizado; tabela
relativa declara conjunto e referência; trocar a referência não roda detecção;
"incipient absent" fora da tabela relativa; fases da Compare = fases da Calibrate
para os mesmos tracks (controle positivo, cobre A11); cache acerta entre execuções e
erra quando o conteúdo muda; filtro "Show only cyclones whose sequence differs";
os dois layouts de figura com legenda e erro por célula; estado da Compare
sobrevive a uma ida à Calibrate; e2 sem termos proibidos; e2 controle positivo (o
varredor acha um termo plantado); e2 Compare renderiza e roda com a leitura de
rótulos quebrada; figuras da Benchmark idênticas byte a byte depois da extração do
módulo de figuras; Edit e Remove de uma coluna.

`tests/test_compare_browser.py` (3, marcados `browser`): e1 T5→T1→T3→T4 numa
sessão; e1 T2 (upload de YAML) noutra; estado da Compare sobrevive a uma ida à
Calibrate no navegador.

Previsão (só passed e failed):

| execução | passed | failed |
|---|---|---|
| env conda `cyclophaser`, streamlit 1.63.0, `pytest -m "not browser"` | **1515** (1485 + 30) | **0** |
| venv streamlit 1.56.0 (piso), mesmo comando | **1515** | **0** |
| receita do CI, wheel (`CYCLOPHASER_REQUIRE_INSTALLED=1 pytest --import-mode=append -m "not source_tree"`) | **1280** | **0** |
| receita do CI, source tree (`python -m pytest -m source_tree`) | **1** | **0** |
| Chromium, `tests/test_app_pages_browser.py` + `tests/test_compare_browser.py`, streamlit 1.63.0 | **11** (8 + 3) | **0** |
| idem, streamlit 1.56.0 | **11** | **0** |

Forma estrutural da mesma previsão, que é o que importa se a contagem de testes novos
mudar durante a construção: **nenhum teste existente quebra nem é alterado, e todo
teste novo passa**. Se o número final de testes novos for diferente de 30 / 3, a
previsão de `passed` conta como errada, e a diferença é explicada no relatório.

`tests/test_label_browser.py` não é rodado nem previsto.

## 2. Custo de Run

### Procedimento (fixado aqui)

Script `research/benchmark_review/i1/measure_run.py` (escrito depois deste
commit), AppTest, env conda `cyclophaser` (streamlit 1.63.0), esta máquina.

- Ponto de partida: Calibrate com "Sample data" (51 tracks).
- Quatro configurações distintas, iguais nas duas páginas, todas tomadas do painel
  da Calibrate: C1 = estado inicial (defaults do pacote); C2 = C1 com
  `cutoff_high = 48`; C3 = `cutoff_high = 30`; C4 = `cutoff_high = 24`.
  1 coluna = C1; 2 = C1, C2; 4 = C1..C4. Na Compare, cada uma entra como "Current
  settings"; na Benchmark, como "Add column from current sidebar state".
- Tracks: na Compare, os 51 da Calibrate, todos selecionados; na Benchmark, modo
  Exploration, "All real" (os mesmos 51 arquivos).
- Layout "Side by side" (padrão das duas); na Compare, a página de figuras padrão.
- **Frio**: `st.cache_data.clear()` imediatamente antes do clique em Run.
  **Quente**: um segundo clique em Run logo depois, sem mudar nada.
- Tempo: relógio de parede do `at.run()` que segue o clique (inclui o rerun que as
  duas páginas fazem depois de guardar o resultado e o desenho das figuras).
- 3 repetições por célula; vale a mediana.

### Previsão (segundos, mediana)

| página | colunas | frio | quente |
|---|---|---|---|
| Compare | 1 | 4 (faixa 2–8) | ≤ 2 |
| Compare | 2 | 7 (3,5–14) | ≤ 2 |
| Compare | 4 | 13 (6,5–26) | ≤ 2 |
| Benchmark | 1 | 6 (3–12) | 3,5 (1,75–7) |
| Benchmark | 2 | 12 (6–24) | 7 (3,5–14) |
| Benchmark | 4 | 24 (12–48) | 13 (6,5–26) |

Base do raciocínio: no item 34, 51 detecções custaram ~2,5 s por mudança no env conda
(5,0 s com 12 figuras − ~0,2 s por figura da Grid); a figura de célula da Benchmark é
menor que a da Grid. A Compare desenha só uma página de figuras; a Benchmark desenha
51 × colunas.

Previsões ordinais, que valem independentemente das faixas:

1. Compare quente ≤ 0,25 × Compare frio, para 1, 2 e 4 colunas (cache entre
   execuções; A3 corrigido).
2. Compare frio < Benchmark frio, para 1, 2 e 4 colunas.
3. Benchmark quente ≥ 0,4 × Benchmark frio (a Benchmark refaz a detecção a cada
   Run, A3; só as figuras vêm do cache).
4. Compare frio cresce aproximadamente linear: 4 colunas / 1 coluna entre 2,5 e 4,5.

Isto é observação, não critério do portão. A proposta de limite de colunas sai
dessa medição.

## 3. Interações (e1) e termos (e2)

| tarefa | orçamento | previsto |
|---|---|---|
| T1 | ≤ 5 | **4** (menu Compare, Add Current settings, Add Defaults, Run) |
| T2 | ≤ 5 | **4** (menu Compare, Add Current settings, upload do YAML, Run) |
| T3 | ≤ 2 | **1** (marcar o filtro; a figura do primeiro aparece sem outra ação) |
| T4 | ≤ 3 | **1** (escolher a nova referência; a tabela muda sem Run) |
| T5 | 0 | **0** |

Teste de navegador novo: 10 execuções seguidas sem falha em cada versão (1.56.0 e
1.63.0).

e2: **nenhum** termo proibido encontrado; a Compare renderiza e roda com a leitura de
rótulos levantando erro.
