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

O topo da aba **Calibration** tem um seletor de modo. Ambos são **pura
visualização**: nenhum controle deles altera a detecção, e nada do estado
deles entra no YAML exportado.

### Grade (padrão)

A grade multi-ciclone histórica, **inalterada**: figuras matplotlib
renderizadas em PNG e cacheadas, 1–6 colunas, e o mesmo PNG dentro do ZIP de
export. Renderizar 51 figuras Plotly na mesma página trava o navegador, e o
PNG exportado precisa continuar determinístico — por isso este modo continua
em matplotlib.

### Inspetor (um track por vez)

Um gráfico Plotly de painéis empilhados (`z` / `dz` / `dz2`, eixo x
compartilhado e zoom sincronizado) para **um** track escolhido no selectbox.
A escolha do renderizador é o ponto do modo: clicar na legenda liga e desliga
uma série **no cliente**, sem rerun do Streamlit.

Há dois tipos de controle, e a diferença é deliberada:

- **Camadas de série** — `zeta`, `filtered_vorticity`, `vorticity_smoothed`,
  `vorticity_smoothed2`, `dz_dt_filt`, `dz_dt_smoothed2`, `dz_dt2_filt`,
  `dz_dt2_smoothed2`, os três `*_peaks_valleys` e a fronteira `Ic` de ground
  truth dos casos sintéticos. Estão **sempre** no gráfico, com
  `visible="legendonly"` quando desligadas: alternar é um clique na legenda,
  de graça. O sombreado de fases é a única exceção (uma faixa de altura total
  é uma *shape* do layout, que o Plotly não coloca na legenda) e ganhou um
  botão próprio acima do gráfico, que também é client-side.
- **Sobreposições de decisão** — exigem cálculo no servidor, então são
  `st.checkbox` e só são computadas quando marcadas:
  - **Fita do pipeline** — seis faixas, uma por etapa, coloridas pelas fases
    vigentes *depois* daquela etapa. As seis funções rodam em ordem fixa e
    sobrescrevem umas às outras; ler uma coluna de cima para baixo mostra um
    trecho mudando de dono.
  - **Ledger de candidatos** — cada segmento que
    `find_intensification_period` e `find_decay_period` consideram, com a
    escala usada, o mínimo exigido, o veredito sob os sliders atuais, os gaps
    e o teste de preenchimento, e (cruzando com a fita) se um candidato aceito
    foi sobrescrito por uma etapa posterior.
  - **Camadas mature** — picos/vales de `z` aceitos e rejeitados sob o limiar
    de proeminência efetivo, e as janelas maduras, **incluindo as que a
    confirmação estrita descartou** — que hoje somem sem deixar rastro no
    resultado.
  - **Camadas incipiente** — sondagem suavizada, perfil `rel = |dz|/max|dz|`
    contra τ, joelho de `|dz2|` e a fronteira incipiente que o run produziu
    (lida de `df['periods']`, não recomputada). Fora de
    `incipient_method="plateau"` as camadas de rel/τ/sondagem não existem e
    são omitidas com um aviso; `dz` e `dz2` crus continuam.

O estado inicial do inspetor reproduz a figura de fases da Grade
(`vorticity_smoothed2` + sombreado de fases): nada se perde ao abrir.

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
