# Passo 5 — dívidas menores: previsões declaradas ANTES de qualquer correção

Do prompt do Passo 5 (2026-10-02), sem ajuste. Versionadas no commit 20, antes de
qualquer correção e antes de rodar qualquer coisa no ambiente com versões fixadas.

| id | previsão |
|---|---|
| E1 | suíte (`-m "not browser"`, ambiente `cyclophaser`) 0 falhas; diff de `cyclophaser/` desde `32651c8` vazio. |
| E2 | testes do app 0 falhas no ambiente `cyclophaser` **e** no ambiente com as versões fixadas de `tools/calibration_app/requirements-app.txt`. Dos 23 testes do Benchmark que falham hoje nas versões fixadas: **0 de ambiente, 23 de código**. |
| E3 | build da documentação numa cópia limpa da branch (git worktree), no ambiente que espelha o `.readthedocs.yml`: 0 erros, 0 avisos. |
| E4 | caminhos absolutos (`/Users/`, `/home/`, `C:\`) em arquivos versionados: 0 ocorrências, exceto em `research/cleanup/` quando a ocorrência é parte de saída bruta já anonimizada com marcador. |
| E5 | o gerador do digest não abre nenhum arquivo do split de teste (registro dos arquivos abertos); digest igual a `7552bc67…` antes e depois da correção, na mesma sessão. |
| E6 | D1 (verificador de defaults do Passo 4) e R4 (scanner do Passo 3) continuam 0. |

## Raciocínio de E2 (leitura de código, sem executar nas versões fixadas)

A aba Benchmark usa só APIs básicas do Streamlit (`caption`, `button`, `markdown`,
`expander`, `columns`, `dataframe`, `selectbox`, `radio`, `multiselect`,
`file_uploader`, `cache_data`), todas presentes no streamlit 1.58.0 fixado.
Uma falha comum a 23 dos 53 testes do arquivo indica um erro que interrompe a
renderização da aba, vindo do próprio código sob as versões fixadas (por exemplo
pandas 2.3 × 3.0), e não uma diferença do harness `AppTest`. Daí 23 de código.

## Definições operacionais

* **Ambiente × código (E2).** "Código": o app falha sob as versões fixadas, também
  fora do `AppTest` (o app real quebraria nessas versões). "Ambiente": só o
  harness de teste se comporta diferente; o app real nessas versões está certo.
* **Testes do app (E2).** Os arquivos de `tests/` que importam
  `streamlit.testing` ou o código de `tools/calibration_app/`, listados por script
  em `passo5/app_tests.txt`.
* **Ambiente fixado (E2).** venv Python 3.12 com `pip install -r
  tools/calibration_app/requirements-app.txt` (instala o pacote da árvore em modo
  editável) mais `pytest` e `pyyaml`.
* **Ocorrência (E4).** Uma linha de arquivo versionado (`git grep -I`) que contém
  `/Users/`, `/home/` ou `C:\`. A exceção vale só em `research/cleanup/`, quando o
  caminho já foi trocado por um marcador (`<repo>`, `<env>`, `<tmp>`, `~`,
  `<docs-venv>`) e o que resta não identifica a máquina.
* **Arquivos abertos (E5).** Registro por `sys.addaudithook` (evento `open`) durante
  a execução do gerador. Contam-se os arquivos de `tests/calibration_data/` e,
  deles, quantos têm id do split de teste — só contagens, nenhum id.
* **E5 "antes".** O gerador atual lê todos os CSVs do diretório e filtra o treino
  depois. Para medir o digest "antes" sem abrir o split de teste, o gerador atual
  roda numa cópia da branch (git worktree) da qual os CSVs do split de teste foram
  retirados; ele filtra o treino de qualquer forma, então o digest não depende
  deles. Os arquivos que ele abriria na árvore normal são contados pela leitura do
  código (todo `*.csv` do diretório), sem executá-lo lá.
