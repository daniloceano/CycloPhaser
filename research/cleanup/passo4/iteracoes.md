# Passo 4, Fase B — iterações com o Danilo

Cada rodada: pedido, o que mudou, pedidos não executados e por quê. Nada desta
fase é commitado antes de "aprovo a documentação".

## Rodada 0 — entrega inicial (2026-10-01), a partir de `8dc2159`

**Entregue para revisão local**

* Site: `docs/_build/html/index.html` (build no ambiente que espelha o
  `.readthedocs.yml`, pacote reinstalado a partir de HEAD).
* App: `streamlit run tools/calibration_app/app.py` (ambiente `cyclophaser`),
  em http://localhost:8501. Aba Documentation removida; link para o site sob o título.
* Figura: `docs/figures/make_methodology_figure.py` → `docs/_static/methodology.png`.
  O replay das funções públicas de estágio reproduz o `periods` do `get_periods`
  (assert). Nenhum painel usou função privada nem reimplementou lógica.
* Exemplos do guia de uso: `docs/figures/make_noisy_example.py`; tabelas da
  página de defaults: `docs/figures/make_doc_tables.py`.

**Pontos que dependem do Danilo (não executados)**

1. **Erro de build na docstring de `process_vorticity`.** A tabela rst da nota
   sobre `replace_endpoints_with_lowpass` é malformada (uma linha mais larga que a
   borda da coluna) → 1 ERROR, agora que a página da API inclui
   `process_vorticity`. Corrigir exige um commit de docstring em `cyclophaser/`
   (passaria pelo portão: árvore sintática, digest, suíte). Isso contradiz a
   previsão de D4 da Fase C ("diff de `cyclophaser/` desde 16g vazio"). Não
   executado; decisão do Danilo: (a) commit de docstring 16h, registrando que D4
   muda; (b) tirar `process_vorticity` da página da API; (c) manter e D3 falha.
2. **Ramo dos links do site.** Os links para o repositório (CHANGELOG, YAML do
   params-track, README do app, registros de pesquisa) apontam para `master`,
   num único lugar (`REPO_BLOB` em `docs/conf.py`). O conteúdo novo só chega a
   `master` no merge/release (Q4, em aberto).
3. **PyPI × documentação.** A página Installation manda instalar do PyPI, cuja
   versão (2.0.0) não tem vários parâmetros documentados (S11). Depende da Q4.
4. **Série de exemplo com passo de 3 h.** A série de exemplo do pacote tem passo
   de 3 h; os defaults foram calibrados para séries horárias e alguns parâmetros
   contam passos de tempo (página Defaults). O guia usa a série com os defaults,
   como pedido; falta decidir se o guia deve dizer isso explicitamente.
5. **Legenda da figura.** Mantidas as cores (amostradas da figura de 2024,
   `passo4/sample_old_figure_colors.py`), o layout e a legenda; acrescentadas três
   entradas (Peak, Valley, Discarded (weak)), porque o extremo riscado é novo.
6. **O extremo descartado.** A série tem exatamente um extremo fraco descartado
   (um vale cujo pico vizinho sobrevive). Numa série lisa, uma oscilação fraca no
   meio de um trecho monótono dá um par pico/vale; e qualquer ruído que vaze pelo
   filtro nos trechos planos cria extremos minúsculos, também descartados. Por
   isso o ruído é de alta frequência (senóides de período 2,5–8 h, abaixo do
   corte do filtro) e a semente foi escolhida por varredura
   (`passo4/methodology_series_search.py`, saída `.txt`); o script da figura
   confere a estrutura com assert.
7. **Ferramentas de rastreio.** A Home antiga citava uma ferramenta e uma base de
   trajetórias externas; saíram (regra: sem nomes de projetos externos). Fica a
   revisão de Walker et al. (2020).
8. **Imagens antigas.** `docs/_images/` (figura de 2024 e as três figuras de
   exemplo de 2024) deixam de ser usadas; serão removidas no commit do site
   (Fase C). O amostrador de cores passa a ler a figura de 2024 do histórico do git.
9. **Licença.** `docs/license.rst` inalterado até a decisão GPL-3.0-only ×
   or-later.

## Rodada 1 — decisões do Danilo (2026-10-01) e o que mudou

| # | decisão | o que mudou |
|---|---|---|
| 1 | Documentação do app sai e vira link para o site | Confirmado; já feito na rodada 0 (aba Documentation removida, link sob o título). |
| 2 | Licença GPL-3.0-or-later; alinhar `docs/license.rst` e `README.md` ao `setup.py`; `LICENSE` não muda | `docs/license.rst:4, :13, :15` e `README.md` (selo e frase da seção License) passam a dizer GPL-3.0-or-later. `LICENSE` e `setup.py` intocados. |
| 3 | Erro da tabela rst em `process_vorticity`: commit 16h só de docstring, mesmo portão; redeclarar D4 antes da Fase C | Feito e com push: `32651c8` (16h + redeclaração de D4 em `PREVISOES.md`: "diff de `cyclophaser/` desde 16h vazio") e `37fab35` (git log do portão). Árvore sintática idêntica, digest `7552bc67…` antes e depois, suíte 1438/0. Build depois: 0 erros, 0 avisos. |
| 4 | Exemplo do guia com série HORÁRIA, CSV pequeno em `docs/`, origem indicada; o guia diz que os defaults pressupõem passo horário | Opções levantadas em `passo4/hourly_series_options.md` (ver abaixo). Escolhida, **provisoriamente**, `20150436` → `docs/data/example_track_hourly.csv` (cópia byte a byte de `tests/calibration_data/20150436.csv`; origem em `docs/data/README.md`). Guia de uso: aviso "The defaults assume one value per hour" e conversão dos parâmetros em passos de tempo. Os exemplos com ruído usam a mesma série. |
| 5 | Home: restaurar como referências científicas a ferramenta de rastreio e a base de trajetórias | `docs/index.rst`: CyTRACK (Pérez-Alarcón et al., 2024) e a base de Gramcianinov et al. (2020) voltam ao texto e às referências, com os textos e links da Home antiga (`8dc2159`). |
| 6 | App grava os parâmetros desligados como null; teste exporta, relê e confirma a mesma detecção; tirar o contorno da página | `_build_yaml` escreve todo valor `None` como `null` (os três: `prominence`, `prominence_relative`, `decay_tail_amplitude_fraction`; nenhum outro parâmetro do app pode ser `None`). `_load_yaml_config` lê `null` ou chave ausente como desligado. Teste novo `tests/test_app_yaml_null_export.py` (4 testes; falha 2 contra o `app.py` antigo, passa 4 com o novo; controle positivo: sem os nulls, a detecção do track de treino `20160735` muda). Contorno retirado de `docs/calibration_tool.rst`. Testes do app: 170 passed / 0 failed. |
| 7 | Figura com durações realistas; extremo fraco dentro do decaimento; reportar frações; manter asserts | Série nova (busca registrada em `passo4/methodology_series_search.py` e `.txt`). Frações na figura gerada (`docs/generated/methodology_phase_fractions.csv`): incipient 0.062, intensification 0.217, mature 0.117, decay 0.550, residual 0.054. Asserts mantidos: replay = `get_periods`; figura idêntica byte a byte em duas execuções. |

**Desvios desta rodada (para o Danilo decidir)**

* **Item 7 — o extremo descartado é um par.** Dentro de um decaimento que continua
  subindo, uma oscilação fraca é um vale seguido de um pico. Se só um dos dois for
  descartado, o que sobra parte o decaimento (medido na rodada 0: o pico que sobrou
  encerrou o decaimento e o resto virou resíduo). A figura tem uma oscilação fraca
  (um vale e um pico) descartada dentro do decaimento, os dois riscados; o assert
  confere exatamente isso. O texto do painel E diz "the crossed-out valley and peak,
  during the decay".
* **Item 7 — maturidade 0.117**, um pouco acima de "cerca de um décimo"; é o menor
  valor que a busca achou junto com as outras metas.
* **Item 4 — escolha provisória da série.** Das 42 séries horárias de treino, 10
  dão a sequência limpa com os defaults; 4 saíram por estarem na lista de defeito
  do incipient (`passo1/hygiene_train.json`) e 2 por terem re-rotulagens pendentes
  (S11). Restam `20150436`, `20190870`, `20191014`, `20191155`; usei `20150436`
  (112 pontos). Trocar é uma linha (`docs/data/`) e um script.
* **Saídas geradas fora de `docs/_static/`.** `docs/_static/` está no `.gitignore`
  (regra de modelo de 2023), então figuras e tabelas não chegariam ao Read the
  Docs. Passaram para `docs/generated/` (não ignorado), sem mexer no `.gitignore`.

**Opções horárias no repositório (item 4, resumo de `passo4/hourly_series_options.md`)**

* 42 trajetórias reais ERA5, horárias, com `min_max_zeta_850`, em split de TREINO:
  35 em `tests/calibration_data/` (adicionadas em `11e530a`, 2026-07-08, "51 real
  ERA5 cyclone tracks (2015-2020)") e 7 do lote swell em
  `tests/calibration_data/swell_item30/` (`7a480a5`, 2026-09-25).
* Fora de cogitação: 19 de TESTE (não abertas), 5 de validação gasta e travada
  (`swell_item30_val`), e as séries de 3 h (`cyclophaser/example_data/example_file.csv`,
  `tests/test.csv`, as 12 sintéticas).

## Rodada 2 — "aprovo a documentação" (Danilo, 2026-10-01)

Aprovada sem pedidos novos. Antes das medições da Fase C, e só em texto fora do
site aprovado:

* `CHANGELOG.md` [Unreleased]: duas entradas novas (site reescrito; exportação do
  app com `null`) e duas afirmações de default defasadas corrigidas, achadas ao
  preparar o D2 (`:330`: "which is what the package defaults give you" sobre
  `prominence`/`prominence_relative` = None, falso desde o item 31; `:662`: r(t₀)
  "under package defaults", medido sob os defaults da época).
* Imagens antigas: removidas `docs/_images/cyclophaser_methodology.jpg`,
  `test_default.png` e `test_steps_default.png` (sem referência). Mantida
  `docs/_images/test_custom.png`: o `README.md` a mostra por um link para `master`.
