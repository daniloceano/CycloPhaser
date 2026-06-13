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
