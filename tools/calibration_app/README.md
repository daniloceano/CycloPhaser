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
  sombreado de fases é a única exceção (uma faixa de altura total é uma
  *shape* do layout, que o Plotly não coloca na legenda) e ganhou um botão
  próprio acima do gráfico, que também é client-side.
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

**Escala compartilhada (`Shared y scale`, ligada por padrão).** Com tudo
ligado, um painel carrega séries de magnitudes bem diferentes (o `zeta` cru é
2–3× mais largo que a curva suavizada que a detecção lê). Um segundo eixo
(`twinx`) está descartado — foi o que causou o bug de zorder na figura compacta
da grade —, então cada curva é dividida pelo **próprio `max|y|`** e todas
cabem em um eixo só. Divide-se por `max|y|` (e não min–max) para preservar
sinal e a posição do zero: min–max deslocaria cada série para a própria
linha de base e faria curvas genuinamente diferentes parecerem coincidentes.
A normalização está escrita no título do eixo, e **cada hover carrega o valor
bruto e o divisor** — nada dela é implícito. Desmarque para ler as séries nas
unidades próprias.

**Fidelidade.** Toda a conta vive em funções puras
(`layer_inspector.py`, sem Streamlit e sem biblioteca de plot), que só
*chamam* as funções do próprio pacote — a fita executa as seis funções em
sequência sobre uma cópia do df, e o ledger é comparado, em teste, com a
máscara que a função do pacote produz sozinha (`tests/test_layer_inspector.py`).
Os mesmos helpers alimentam o renderizador Plotly do app e o render estático
matplotlib de conferência em
`research/app_layer_inspector/gen_inspector_figures.py`.

## Escopo atual (Etapa 1)

- Upload de 1 arquivo CSV
- Controle interativo de filtro Lanczos e suavização Savgol
- Visualização de ζ original, filtrada, suavizada 1× e suavizada 2×
- Cache automático: o filtro só re-executa quando os parâmetros mudam

**Próximas etapas (não implementadas aqui):** calibração de thresholds de
fase (Etapa 2), grade multi-ciclone, export de parâmetros.
