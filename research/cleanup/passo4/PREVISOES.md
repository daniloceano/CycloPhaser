# Passo 4 — previsões declaradas ANTES de qualquer medição ou edição

Do prompt do Passo 4 (2026-09-29), sem ajuste. Versionadas no commit 16 (Fase A),
antes de qualquer edição de documentação ou do app.

| id | previsão |
|---|---|
| D1 | verificador `passo4/check_documented_defaults.py`, rodado ANTES das edições: 0 divergências dentro de `cyclophaser/` (se houver: PARAR e reportar). DEPOIS das edições: 0 divergências no conjunto verificado. |
| D2 | nenhum texto vivo atribui ao default atual escores medidos sob `edge` (lista dos trechos revisados, arquivo:linha). |
| D3 | build da documentação sem erros; avisos depois ≤ avisos antes. |
| D4 | suíte (`-m "not browser"`) 0 falhas; diff de `cyclophaser/` vazio; R4 (scanner corrigido do Passo 3) continua 0. |
| D5 | número de configurações mantidas no repo que chegam aos caminhos de reserva do app (`.get` com literal): **1**. Resultados do app para essas configurações: inalterados. |

## D5 — raciocínio declarado (leitura de código, antes de medir)

* Caminhos de reserva com literal (MANIFEST 0.2(e)): `tools/calibration_app/app.py`
  `_preset_to_widgets` (`.get` de `use_filter`, `replace_endpoints_with_lowpass`,
  `savgol_polynomial`, `boundary_padding`, `cutoff_low`, `cutoff_high`, e o `.get`
  de `use_smoothing`/`use_smoothing_twice` com `"auto"`), e
  `tools/calibration_app/layer_inspector.py` `mature_ledger` (`length_scale`,
  `mature_method`, `mature_amplitude_fraction`, `mature_min_depth`).
* `mature_ledger` só recebe no app `args` montados por `build_args_periods`, que
  preenche todas as chaves de `_ARGS_PERIODS_DEFAULTS`: nenhuma configuração chega
  a esses literais pelo app.
* `_preset_to_widgets` só recebe os dois presets sintéticos de
  `tests/synthetic/cases.py`. Previsão: o preset "clean" (Lanczos desligado) não
  traz todas as chaves de filtragem e chega a pelo menos um literal; o "noisy" traz
  todas. YAMLs (`params-track`) e snapshots entram por outro caminho (decisão (a),
  tabela congelada), não por esses literais. Logo **1**.
* Resultados inalterados porque, no preset que chega à reserva, as chaves ausentes
  são de filtragem com o filtro desligado (inertes).

## Definições operacionais

* **Conjunto verificado (D1):** `docs/*.rst`, `README.md`,
  `tools/calibration_app/README.md`, textos do app (`tools/calibration_app/*.py`:
  comentários e strings com espaço), `CHANGELOG.md` apenas na seção
  `[Unreleased]`, `research/labels/README.md`; e, só leitura, as docstrings e
  comentários de `cyclophaser/*.py`.
* **Afirmação de default (D1):** um trecho que declara o valor ATUAL do default de
  um parâmetro das funções públicas (`get_periods`, `process_vorticity`,
  `determine_periods`, `find_peaks_valleys`, `lanczos_filter`,
  `lanczos_bandpass_filter`): "Default is X", "Default: X", "**Default**: X",
  "defaults to X", "Default X since …", um valor marcado "(default)", ou a
  coluna "now" das tabelas do CHANGELOG. Valores históricos que acompanham a
  afirmação ("48.0 up to 2.0.0", "it was 24 …", "before item 31") não são
  afirmações do default atual. O parâmetro é o nomeado na mesma linha ou, em
  docstrings/listas, o do cabeçalho de parâmetro mais próximo acima.
* **Divergência (D1):** o valor afirmado difere do default da assinatura (números
  comparados numericamente; `True`/`False`/`None` e strings comparados após tirar
  aspas e crases). Quando o parâmetro tem defaults diferentes em funções
  diferentes (ex.: `reclassify_index0`), conta como divergência só se o valor não
  for o default de nenhuma delas.
* **Avisos/erros da build (D3):** linhas de saída do `sphinx-build` com
  `WARNING:` / `ERROR:` (ou `CRITICAL:`), contadas por script, ambiente separado
  instalado de `docs/requirements.txt`.
* **Configuração que chega a um caminho de reserva (D5):** uma configuração
  versionada que, passada ao caminho do app, faz ao menos um `.get(chave,
  literal)` usar o literal (chave ausente).

## Mudança de portão (decisão do Danilo, 2026-09-29) — seção acrescentada no commit 16c

As previsões acima não foram editadas.

> "Única mudança de comportamento no pacote: C1 (742e685). Fora dele, um único
> commit só de docstring em cyclophaser/, verificado por (i) árvore sintática sem
> docstrings idêntica antes e depois e (ii) digest default igual na mesma sessão."

Motivo: D1 "antes" achou docstring falsa em `cyclophaser/determine_periods.py:948`
(nota de `decay_tail_amplitude_fraction`: "default None"; o default é 0.3).
O commit só de docstring é o 16b.

## Medições "antes" de D1 — duas, registradas sem ajuste

* Oficial (commit 16, `before.json`): 14 divergências, 1 em `cyclophaser/`.
* Corrigida (commit 16c, `before_corrected.json`, remedida sobre a árvore de
  `b9991c4` com o verificador corrigido): o widget do app passa a vir antes do
  nome citado no parágrafo; `app.py:1630` era falso positivo e `app.py:2005` é de
  `mature_min_depth`.

## Previsão intermediária (declarada no commit 16c, antes de medir)

| id | previsão |
|---|---|
| D1a | 0 divergências FORA de `docs/*.rst` após o commit 17 (verificador corrigido) |

## Mudança de portão (2) — decisão do Danilo, 2026-09-29 — seção acrescentada no commit 16d

As previsões e a seção anterior não foram editadas.

> "Única mudança de comportamento no pacote: C1 (742e685). Fora dele, só commits
> de docstring ou comentário em cyclophaser/, cada um verificado por (i) árvore
> sintática sem docstrings idêntica antes e depois e (ii) digest default igual na
> mesma sessão."

Motivo: a varredura de docstrings e comentários de `cyclophaser/` (commit 16d,
`passo4/sweep_16d.py`), que acha afirmações de default e de "opt-in" defasadas
desde o item 31. Comentários não entram na árvore sintática, então o critério
(i) cobre também os commits só de comentário.

## Redeclaração de D4 (decisão do Danilo, 2026-10-01) — acrescentada no commit 16h, antes de qualquer medição da Fase C

A previsão D4 do Passo 4 replanejado ("diff de `cyclophaser/` desde 16g vazio")
é substituída por:

| id | previsão |
|---|---|
| D4 | suíte (`-m "not browser"`) 0 falhas; **diff de `cyclophaser/` desde 16h vazio**; R4 (scanner corrigido do Passo 3) continua 0. |

Motivo: a página da API do site passou a incluir `process_vorticity`, e a tabela
rst da nota sobre `replace_endpoints_with_lowpass` na sua docstring era
malformada (1 ERROR na build). O Danilo autorizou a correção como commit só de
docstring (16h), com o mesmo portão. A previsão anterior não foi medida.
