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

## Escopo atual (Etapa 1)

- Upload de 1 arquivo CSV
- Controle interativo de filtro Lanczos e suavização Savgol
- Visualização de ζ original, filtrada, suavizada 1× e suavizada 2×
- Cache automático: o filtro só re-executa quando os parâmetros mudam

**Próximas etapas (não implementadas aqui):** calibração de thresholds de
fase (Etapa 2), grade multi-ciclone, export de parâmetros.

## Lentes de foco por fase (`Focus`)

O seletor **Focus**, no topo da aba *Calibration*, troca o **sinal que as
figuras mostram** — para que o parâmetro em ajuste e a curva que o governa
fiquem na tela ao mesmo tempo. É **pura visualização**: nenhuma opção do
seletor altera a detecção de fases, e o foco **não** entra no YAML exportado
(é estado de UI, em `session_state`, como `Grid columns`).

| Foco | O que a figura passa a mostrar |
|------|--------------------------------|
| **Overview** (padrão) | A figura de fases de sempre, inalterada. |
| **Mature** | `z` com os picos/vales que o detector **de fato consome**, e a proeminência de cada candidato contra o limiar efetivo — dá para ver o slider de `prominence` aceitando e rejeitando extremos ao vivo. |
| **Incipient** | `dz` e `dz2` no início da série, a sondagem suavizada sobreposta ao `dz` cru, o perfil `rel = \|dz\|/max` contra `tau`, e o joelho `argmax\|dz2\|` como diagnóstico. |

Os painéis pesados só são desenhados no foco ativo — o **Overview** nunca
paga por eles. Nas lentes o layout é limitado a 3 colunas (os painéis
empilhados ficam ilegíveis abaixo disso).

**Fidelidade da lente Mature.** Os extremos marcados como *aceitos* são lidos
da mesma chamada de `find_peaks_valleys` que o `get_periods` faz para montar
`df['z_peaks_valleys']` — a coluna que o `find_mature_stage` percorre. A lente
não reimplementa o critério, e `tests/test_phase_focus.py` trava essa
igualdade (mesmos índices) em 5 tracks reais × 3 configurações de filtro.

**Fora do modo plateau.** Com `incipient_method="geometric"`, `tau` e a
sondagem não se aplicam: a lente Incipient degrada para os painéis `dz`/`dz2`
crus mais a fronteira que a regra geométrica produziu, com legenda explicando
a ausência.

As contas ficam em `phase_focus.py` (funções puras, sem Streamlit), o que
permite testá-las e re-renderizar as lentes offline:

```bash
python research/app_phase_focus/gen_focus_figures.py
```
