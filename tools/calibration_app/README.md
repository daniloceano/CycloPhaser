# CycloPhaser — Calibration App

Ferramenta interativa para calibrar os parâmetros de filtragem e suavização
do CycloPhaser antes de rodar a detecção de fases.

## Instalação

Execute a partir do diretório `tools/calibration_app/`:

```bash
cd tools/calibration_app
pip install -r requirements-app.txt
```

O `-e ../..` em `requirements-app.txt` instala o CycloPhaser em modo
editável a partir da raiz do repositório.

## Como rodar

```bash
streamlit run app.py
```

Abra http://localhost:8501 no navegador.

## Formato do track

Os dois campos de envio (Calibration e Benchmark → Exploration) aceitam `.csv`
e `.txt`. O formato é reconhecido pelo **conteúdo**, nunca pela extensão
(`track_io.py`, a única função de leitura do app).

**Formato padrão** — primeira linha com nomes de colunas separados por `;`,
incluindo:

- `time` — datas **ano primeiro** (`YYYY-MM-DD…`, ex. `2015-01-27 04:00:00` ou
  `2008-08-15-2100`);
- `min_max_zeta_850` — vorticidade relativa em 850 hPa (s⁻¹), convenção do
  hemisfério sul (ciclônica = negativa).

Outras colunas são ignoradas. Compatível com o `example_file.csv` em
`cyclophaser/example_data/`.

**Formato customizado** (opt-in, expander *Custom track format*, desligado por
padrão) — separador (`auto`, `;`, `,`, tab, whitespace), linha de cabeçalho
sim/não, coluna de data e de vorticidade (nome, ou número a partir de 1 sem
cabeçalho) e formato de data strftime opcional. Datas que não começam pelo ano
exigem o formato explícito: a inferência do pandas lê `05/01/2015` como 1º de
maio sem aviso. Cada arquivo lido assim é mostrado numa pré-visualização
(primeiras linhas, primeira/última data, nº de pontos, mín./máx. da
vorticidade, avisos de sinal e de magnitude) e só é usado depois de confirmado.
O arquivo é normalizado para o formato padrão; o resto do app não muda.

**Validação, em qualquer caminho** — datas interpretadas, estritamente
crescentes e sem duplicatas; vorticidade numérica float64 sem NaN; pelo menos
2 pontos. Um arquivo que falha é recusado com a causa, nunca aceito em silêncio.

## Modos de exibição

O topo da aba **Calibration** tem um seletor de modo (a interface do app é
toda em inglês). Ambos são **pura visualização**: nenhum controle deles altera
a detecção, e nada do estado deles entra no YAML exportado.

### Grid (padrão)

A grade multi-ciclone histórica, **inalterada**: figuras matplotlib
renderizadas em PNG e cacheadas, 1–6 colunas, e o mesmo PNG dentro do ZIP de
export. Renderizar 51 figuras Plotly na mesma página trava o navegador, e o
PNG exportado precisa continuar determinístico — por isso este modo continua
em matplotlib.

### Inspector (um track por vez)

Um gráfico Plotly de painéis empilhados (`z` / `dz` / `dz2`, eixo x
compartilhado e zoom sincronizado) para **um** track escolhido no selectbox
*Track to inspect*. A escolha do renderizador é o ponto do modo: clicar na
legenda liga e desliga uma camada **no cliente**, sem rerun do Streamlit.

**O inspetor abre com tudo ligado.** Todas as camadas de série estão visíveis
e as quatro sobreposições de decisão vêm marcadas — o trabalho é por *track*
(um ciclone selecionado), não pela grade inteira, então calcular as quatro de
saída é barato. Desmarcar uma derruba o custo dela.

Há dois tipos de controle, e a diferença é deliberada:

- **Camadas de série** — `zeta`, `filtered_vorticity`, `vorticity_smoothed`,
  `vorticity_smoothed2`, `dz_dt_filt`, `dz_dt_smoothed2`, `dz_dt2_filt`,
  `dz_dt2_smoothed2`, os três `*_peaks_valleys` e a fronteira `Ic` de ground
  truth dos casos sintéticos. Estão **sempre** no gráfico: desligar uma é um
  clique na legenda (ela vira `legendonly` e continua na figura), de graça. O
  sombreado de fases é a única exceção — uma faixa de altura total é uma
  *shape* do layout, que o Plotly não coloca na legenda — e fica **sempre
  ligado**: é o fundo contra o qual todas as outras camadas são lidas.

  As cores seguem o padrão do próprio pacote (`cyclophaser/plots.py`,
  `plot_didactic`): ζ cru em cinza, `filtered_vorticity` em âmbar,
  `vorticity_smoothed` em azul-marinho e `vorticity_smoothed2` em vermelho.
  Nos painéis de derivada vale a cor por *quantidade* do mesmo arquivo
  (`series_colors`: dz vermelho, dz2 âmbar), com o estágio intermediário
  `*_filt` num tom claro e o estágio que a detecção lê na cor cheia e no
  traço mais grosso.
- **Sobreposições de decisão** — exigem cálculo no servidor, então são
  `st.checkbox`:
  - **Pipeline ribbon** — seis faixas, uma por etapa, coloridas pelas fases
    vigentes *depois* daquela etapa. As seis funções rodam em ordem fixa e
    sobrescrevem umas às outras; ler uma coluna de cima para baixo mostra um
    trecho mudando de dono.
  - **Candidate ledger** — cada segmento que `find_intensification_period` e
    `find_decay_period` consideram, com a escala usada, o mínimo exigido, o
    veredito sob os sliders atuais, os gaps e o teste de preenchimento, e
    (cruzando com a fita) se um candidato aceito foi sobrescrito por uma etapa
    posterior.
  - **Mature layers** — picos/vales de `z` aceitos e rejeitados sob o limiar
    de proeminência efetivo, e as janelas maduras, **incluindo as que a
    confirmação estrita descartou** — que hoje somem sem deixar rastro no
    resultado.
  - **Incipient layers** — sondagem suavizada, perfil `rel = |dz|/max|dz|`
    contra τ, joelho de `|dz2|` e a fronteira incipiente que o run produziu
    (lida de `df['periods']`, não recomputada). Fora de
    `incipient_method="plateau"` as camadas de rel/τ/sondagem não existem e
    são omitidas com um aviso; `dz` e `dz2` crus continuam.

**Escala compartilhada (`Shared y scale`, ligada por padrão).** As curvas são
reescaladas para uma faixa **0–1**, nos **mesmos grupos** que a figura do modo
Grid coloca nos seus dois eixos (`plots.plot_all_periods` usa `twinx`: o `zeta`
cru num eixo, `filtered_vorticity` + `vorticity_smoothed` +
`vorticity_smoothed2` juntos no outro). Os painéis de derivada seguem a mesma
regra: `*_filt` e `*_smoothed2` dividem uma faixa.

As duas metades do agrupamento importam:

- dar ao **cru uma faixa própria** é o que faz ele **se sobrepor** à filtrada
  em vez de esmagá-la — ele tem 2–3× mais amplitude, e numa escala comum
  achataria as outras contra o eixo;
- manter os **estágios do pipeline juntos** é o que preserva a amplitude que
  cada passada de suavização tirou. Escalando cada um por conta própria, todo
  estágio passa a ocupar a altura inteira e todos ficam idênticos — medido em
  20190325 com os defaults do pacote, `filtered_vorticity` tem 1,25× a
  amplitude de `vorticity_smoothed2`, e a escala por série apagava isso.

O painel passa então a ser lido pela **forma** — onde cada série vira, e quando
—, que é a única coisa sobre a qual as regras de fase agem. A magnitude sai do
eixo, mas **cada hover continua mostrando o valor bruto**. Efeito colateral: o
zero fica numa altura diferente para cada faixa, então a linha de zero dos
painéis dz/dz2 não é desenhada nesse modo. Desmarque para ler unidades
verdadeiras e um zero real.

(Um `twinx` de verdade continua descartado no inspetor: foi ele que causou o
bug de zorder na figura compacta da grade. O que se reproduz aqui é o
*agrupamento* que o `twinx` do pacote produz, num eixo só.)

**Fidelidade.** Toda a conta vive em funções puras
(`layer_inspector.py`, sem Streamlit e sem biblioteca de plot), que só
*chamam* as funções do próprio pacote — a fita executa as seis funções em
sequência sobre uma cópia do df, e o ledger é comparado, em teste, com a
máscara que a função do pacote produz sozinha (`tests/test_layer_inspector.py`).
Os mesmos helpers alimentam o renderizador Plotly do app e o render estático
matplotlib de conferência em
`research/app_layer_inspector/gen_inspector_figures.py`.

## Benchmark tab

Compares N configurations side by side, over the cyclones you choose, aligned by
cyclone. A column is created from the current sidebar state, an uploaded YAML, a
file in `research/labels/configs/` (all eleven) or a frozen published-version
snapshot, and stays editable in the tab itself.

**Each column's header** — one identity line (source hash · running commit), the
pre-filter-fix warning when it applies, and a `Provenance` drop-down holding all
five mandatory items:

1. sha256 of the source YAML, or `edited in session` if it was changed;
2. the commit of the code actually running (`git rev-parse HEAD`). **Not**
   `metadata.cyclophaser_version`: it reads `2.0.0` in all eleven files and
   distinguishes nothing;
3. keys present in the YAML and ignored by the current signature (`distance`);
4. keys absent from the YAML and filled by the current default, with the value;
5. the **"pre-filter-fix config"** warning when `boundary_padding` is missing.
   This is not cosmetic: the v1–v5 YAMLs carry `use_filter: true`, and in the
   code of that period `True` was read as the integer window 1 (bool is a
   subclass of int), so the Lanczos filter was **never** applied. The same line
   applies the filter today. Without the warning the column shows a result
   nobody saw at the time and presents it as history.

**Both measurements** are always shown, each named by its instrument: the phase
sequence from `evaluate_against_labels.py / score_phase_sequences` (starts only,
`tolerance_idx` per label, refuses to pair when the sequence does not match) and
the mature pairing from `item19_core.pair_by_overlap` (largest overlap, both
ends, fixed margin 6). They are different instruments and are never summed.

**`evaluation.bad_cases_count` is not a score.** It appears only as a labelled
historical annotation under `Provenance`: these were visual marks made at
different times with different knowledge of the problem (v5 and v6 record 0; v9
records 6).

**Leakage.** Every aggregate is computed over the train split. Aggregates
involving the 16 real cyclones of the frozen test split appear in a separate,
labelled block and are never added into the train one. Manual labels are opt-in.

Frozen reference columns come from `research/snapshots/` (see that directory's
README): the tab **reads files** and never runs a published version live.

### Modes, reference column and Run

**Reading order.** A one-line status bar (configs · cyclones · ground-truth
badge · reference column), then four numbered sections, each an expander:
**1 Mode → 2 Data → 3 Configurations → 4 Results**. Each section owns everything
it governs — the configuration cards render inside section 3, so collapsing the
section hides them.

**Mode is not independent state.** `Validation` and `Exploration` filter what is
selectable and what is emphasised; they never decide whether a number is
produced. That is decided per cyclone by whether it carries a manual label, in
`benchmark_core.scoreable`. A row with no label yields no scoring number in
either mode.

* **Validation** — only labelled sources selectable (51 real + 12 synthetic);
  scoring panel visible. Switching back from Exploration drops any uploaded
  track from the selection rather than carrying it into a scored run.
* **Exploration** — every source selectable, cyclone uploads included; scoring
  panel collapsed. If labelled rows are in the selection, a note offers to score
  those rows only.

**Without ground truth**, each column is measured against the **reference
column**, never against truth, and the block is labelled `relative to reference`.
Four measures: cyclones whose phase sequence changed; boundary displacement in
timesteps (median and max) for those whose sequence matches; phases that
appeared or disappeared, per type; and cyclones that refused an incipient phase.
Boundary displacement is computed only where the sequence matches — pairing
boundaries across a mismatch would compare two different transitions.

**Reference column** is chosen explicitly. It defaults to the manual label when
one exists, otherwise the first configuration column. The manual label has no
parameters, so the card diffs fall back to the first configuration column as
their parameter baseline, and the card says so.

**A card shows only the parameters that DIFFER from the reference.** The eleven
YAMLs share roughly fifteen identical parameters; listing all of them hides the
two or three that separate one configuration from another. The full
configuration sits behind the card's `Provenance` drop-down.

**Nothing recomputes on edit.** Results come from an explicit **Run**. A
fingerprint of (columns × selection × reference) is stored with them; when it
stops matching, the results are flagged **out of date** instead of being
silently replaced.

**Figures** come in two arrangements over the same data: `Side by side`
(default) and `Stacked`, which puts the panels on a shared x axis and a shared y
scale so a boundary that moved is read straight down the figure. The choice is
kept in session state.

## Sidebar order

The controls are grouped by the order in which the detector actually **executes**,
not by phase name:

| group | step | function |
|---|---|---|
| 1 Lanczos Filter | 1 | `process_vorticity` |
| 2 Savitzky-Golay Smoothing | 2 | `process_vorticity` |
| 3 Extrema Filtering | 3 | `find_peaks_valleys(z)` |
| 4 Intensification | 4 | `find_intensification_period` |
| 5 Decay | 5 | `find_decay_period` |
| 6 Mature | 6 | `find_mature_stage` |
| 7 Residual | 7 | `find_residual_period` |
| 8 Incipient | 9 | `find_incipient_period` |

Step 8, `post_process_periods`, takes no parameter.

Two consequences of reading the real order instead of assuming it: **extrema
filtering is step 3** — it runs before every stage, and the extrema that survive
there are the ones all of them see — and `decay_tail_amplitude_fraction` is read
by `find_residual_period` (`find_stages.py:588`), not by `find_decay_period`,
which is why it sits under Residual.

Two parameters span groups and carry a note in their own widget: `length_scale`
(scales the intensification and decay duration thresholds,
`find_stages.py:387`, and changes detected phases on 20160735, 20191014 and
20203947 under params-9) and `boundary_padding` (a filter parameter that governs
the incipient phase: under `reflect` no series refuses an incipient phase, 0/51;
under `edge`, 33/51 refuse).

This layout's coverage is verified by an automatic test, not by eye:
`tests/test_sidebar_coverage.py` enumerates the package's public signature and
requires every parameter to have a control and no widget key to repeat.

## Escopo atual (Etapa 1)

- Upload de tracks `.csv`/`.txt` (formato padrão ou customizado — ver "Formato do track")
- Controle interativo de filtro Lanczos e suavização Savgol
- Visualização de ζ original, filtrada, suavizada 1× e suavizada 2×
- Cache automático: o filtro só re-executa quando os parâmetros mudam

**Próximas etapas (não implementadas aqui):** calibração de thresholds de
fase (Etapa 2), grade multi-ciclone, export de parâmetros.
