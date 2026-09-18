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

## Formato do CSV

- Separador: `;`
- Coluna de índice: `time` (datetime)
- Coluna de vorticidade: `min_max_zeta_850`

Compatível com o `example_file.csv` em `cyclophaser/example_data/`.

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

## Aba Benchmark

Compara N configurações lado a lado, sobre os ciclones que você escolher,
alinhadas por ciclone. Cada coluna é criada a partir do estado atual da sidebar,
de um YAML enviado, de um arquivo de `research/labels/configs/` (os onze) ou de
um snapshot congelado de versão publicada, e continua editável na própria aba.

**Cabeçalho de cada coluna** — cinco itens, sempre:

1. sha256 do YAML de origem, ou `editado na sessão` se foi alterado;
2. commit do código que está rodando (`git rev-parse HEAD`). **Não** o campo
   `metadata.cyclophaser_version`: ele diz `2.0.0` nos onze arquivos e não
   distingue nada;
3. chaves presentes no YAML e ignoradas pela assinatura atual (`distance`);
4. chaves ausentes preenchidas pelo default atual, com o valor;
5. aviso **"config anterior à correção do filtro"** quando falta
   `boundary_padding`. Não é cosmético: os YAMLs de v1 a v5 trazem
   `use_filter: true`, e no código daquela época `True` era lido como a janela
   inteira 1 (bool é subclasse de int), de modo que o filtro **nunca** era
   aplicado. A mesma linha hoje aplica o filtro. Sem o aviso, a coluna mostra um
   resultado que ninguém viu na época e o apresenta como histórico.

**Os dois medidores** aparecem sempre, cada um com o nome do instrumento:
sequência de fases por `evaluate_against_labels.py / score_phase_sequences`
(só os inícios, `tolerance_idx` por rótulo, recusa parear quando a sequência não
bate) e pareamento do maduro por `item19_core.pair_by_overlap` (maior
sobreposição, as duas pontas, margem fixa 6). São instrumentos diferentes e
nunca são somados.

**`evaluation.bad_cases_count` não é placar.** Aparece só como anotação
histórica rotulada: são marcações visuais feitas em épocas diferentes, com
conhecimento diferente do problema (v5 e v6 marcam 0; v9 marca 6).

**Vazamento.** Todo número agregado é calculado sobre o split de treino.
Agregados envolvendo os 16 ciclones reais do split de teste congelado aparecem
em bloco separado, rotulado, e nunca somados ao de treino. Os rótulos manuais
são opt-in.

Colunas de referência congeladas vêm de `research/snapshots/` (ver o README de
lá): a aba **lê arquivos**, nunca roda uma versão publicada ao vivo.

## Ordem da sidebar

Os controles são agrupados pela ordem em que o detector **executa**, não por
nome de fase:

| grupo | etapa | função |
|---|---|---|
| 1 Filtro Lanczos | 1 | `process_vorticity` |
| 2 Suavização Savitzky-Golay | 2 | `process_vorticity` |
| 3 Filtragem de extremos | 3 | `find_peaks_valleys(z)` |
| 4 Intensificação | 4 | `find_intensification_period` |
| 5 Decaimento | 5 | `find_decay_period` |
| 6 Maduro | 6 | `find_mature_stage` |
| 7 Residual | 7 | `find_residual_period` |
| 8 Incipiente | 9 | `find_incipient_period` |

A etapa 8, `post_process_periods`, não tem parâmetro.

Duas consequências de ler a ordem real em vez de supô-la: a **filtragem de
extremos é a etapa 3** — roda antes de todas as fases, e os extremos que
sobrevivem ali são os que todas elas enxergam — e
`decay_tail_amplitude_fraction` é lido por `find_residual_period`
(`find_stages.py:588`), não por `find_decay_period`, por isso está sob Residual.

Dois parâmetros atravessam grupos e trazem nota no próprio widget:
`length_scale` (escala os limiares de comprimento de intensificação e
decaimento, `find_stages.py:387`, e muda fases detectadas em 20160735, 20191014
e 20203947 sob params-9) e `boundary_padding` (é parâmetro de filtro, mas
governa o incipiente: com `reflect` nenhuma série recusa incipiente, 0/51; com
`edge`, 33/51 recusam).

A cobertura desse layout é verificada por teste automático, não a olho:
`tests/test_sidebar_coverage.py` enumera a assinatura pública do pacote e exige
que cada parâmetro tenha controle e que nenhuma chave de widget se repita.

## Escopo atual (Etapa 1)

- Upload de 1 arquivo CSV
- Controle interativo de filtro Lanczos e suavização Savgol
- Visualização de ζ original, filtrada, suavizada 1× e suavizada 2×
- Cache automático: o filtro só re-executa quando os parâmetros mudam

**Próximas etapas (não implementadas aqui):** calibração de thresholds de
fase (Etapa 2), grade multi-ciclone, export de parâmetros.
