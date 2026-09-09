# Problema A — diagnóstico (somente leitura)

Repo: CycloPhaser, branch `develop-v2.1` @ `887c628`. Nenhum arquivo do pacote
foi alterado. Nenhum commit foi feito. Config usada: `~/Downloads/cyclophaser_params-9.yaml`
(51 tracks reais, `filter_params`/`phase_params` reproduzidos abaixo, sem
alteração de nenhum parâmetro).

```yaml
filter_params:
  use_filter: true
  cutoff_low: 168
  cutoff_high: 18
  replace_endpoints_with_lowpass: 0
  use_smoothing: false
  use_smoothing_twice: false
  savgol_polynomial: 3
  boundary_padding: edge
phase_params:
  threshold_intensification_length: 0.075
  threshold_intensification_gap: 0.075
  threshold_mature_distance: 0.18
  threshold_mature_length: 0.15
  threshold_decay_length: 0.075
  threshold_decay_gap: 0.075
  threshold_incipient_length: 0.4
  prominence_relative: 0.3
  distance: 5
  mature_amplitude_fraction: 0.95
  decay_tail_amplitude_fraction: 0.3
  incipient_plateau_tau: 0.2
  incipient_plateau_k: 5
  incipient_smooth_window: 5.0
  incipient_smooth_polyorder: 3.0
  length_scale: local
  mature_method: amplitude
  incipient_method: plateau
  incipient_plateau_signal: vorticity
  incipient_plateau_crossing: sustained
```

O arquivo de config não está no repositório (procurado e não encontrado em
nenhum caminho versionado); foi localizado em `~/Downloads/cyclophaser_params-9.yaml`.

---

## TAREFA 0 — comparador do argrelextrema

Chamada literal, com caminho e linha:

```
cyclophaser/determine_periods.py:122:    peaks   = argrelextrema(data, np.greater_equal)[0]
cyclophaser/determine_periods.py:123:    valleys = argrelextrema(data, np.less_equal)[0]
```

**Comparador não-estrito** (`np.greater_equal` / `np.less_equal`). A hipótese
do enunciado está **confirmada**: com `mode='clip'` (padrão do `argrelextrema`,
não sobrescrito em nenhuma das duas chamadas acima — `mode` não aparece como
argumento), o índice 0 é comparado contra ele mesmo à esquerda, o que sempre
passa sob um comparador não-estrito. Isso já está documentado no próprio
código, no docstring de `find_peaks_valleys` e num comentário `NOTE (#14 —
pending fix)`:

```
cyclophaser/determine_periods.py:69:    NOTE (#14 — pending fix): argrelextrema uses mode='clip' by default, which
cyclophaser/determine_periods.py:70:    compares boundary indices against themselves as the "missing" neighbour.
cyclophaser/determine_periods.py:71:    This means index 0 is marked as a peak whenever data[0] >= data[1], and
cyclophaser/determine_periods.py:72:    index N-1 whenever data[-1] >= data[-2], regardless of whether the boundary
cyclophaser/determine_periods.py:73:    is a true extremum or merely a smoothing artefact (most visible in dz and
cyclophaser/determine_periods.py:74:    dz2, whose boundary values are distorted by savgol_filter mode='nearest').
```

Como o comparador já é não-estrito, a segunda ramificação da tarefa (comparador
estrito ⇒ procurar outro trecho forçando o índice 0 a entrar na lista) não se
aplica.

### Série que alimenta a detecção de extremos

Confirmado no código, não assumido. Em `get_periods`:

```
cyclophaser/determine_periods.py:1026:    z = vorticity.vorticity_smoothed2
cyclophaser/determine_periods.py:1031:    df = z.to_dataframe().rename(columns={'vorticity_smoothed2': 'z'})
cyclophaser/determine_periods.py:1041:    df['z_peaks_valleys']   = find_peaks_valleys(df['z'],
```

`z_peaks_valleys` (a lista de extremos usada por `find_intensification_period`
e `find_decay_period`) vem de `df['z']` = `vorticity.vorticity_smoothed2`, **não**
da vorticidade bruta (`vorticity.zeta`, guardada à parte em `df['z_unfil']`,
linha 1032).

`vorticity_smoothed2` é produzido em `process_vorticity`. Com a config acima
(`use_filter=true`, `use_smoothing=false`), a série é o resultado do filtro de
Lanczos (banda 168–18 passos, `boundary_padding='edge'`) **sem** nenhuma
suavização Savgol adicional — a ramificação `use_smoothing=False` faz
`vorticity_smoothed2` apontar direto para a série filtrada:

```
cyclophaser/determine_periods.py:663:        # If use_smoothing is False, no smoothing is applied, so use filtered_vorticity directly
cyclophaser/determine_periods.py:664:        vorticity_smoothed = filtered_vorticity
cyclophaser/determine_periods.py:665:        vorticity_smoothed2 = vorticity_smoothed  # No further smoothing applied if use_smoothing is False
```

Resumo: **filtrada pelo Lanczos, não suavizada** (para esta config específica;
com `use_smoothing`/`use_smoothing_twice` truthy em outra config, `z` seria
também Savgol-suavizada — ver linhas 647–666 para a ramificação completa).

---

## TAREFA 1 — inventário nos 51 tracks reais

Script: `research/labels/diagnostics/build_idx0_inventory.py`. Somente leitura:
chama `process_vorticity`, `find_peaks_valleys` e as funções `find_*_period`
do pacote, sem alterar nenhum arquivo — reimplementa a sequência de chamadas
de `get_periods` (determine_periods.py:1073-1083) passo a passo, para poder
tirar um snapshot de `df['periods']` logo após `find_decay_period` (ver nota
metodológica abaixo). Ambiente usado: `~/miniconda3/envs/south_atlantic_cyclone_extremes`
(único ambiente local com `cyclophaser` + `xarray` instalados e apontando para
este checkout).

Tracks: os 51 arquivos de `tests/calibration_data/*.csv`, carregados via
`labels_core.load_real_series` (coluna `min_max_zeta_850`). Conferido: os 51
ids batem com `metadata.cyclones_used` do config (nenhuma divergência impressa
pelo script).

Saída: `idx0_inventory.csv` (51 linhas, schema pedido).

### Resultado de `idx0_tipo`

```
peak: 46
valley: 5
```

Bate com o esperado (46 peak / 5 valley).

Os 5 `valley`: `20180170`, `20180608`, `20190325`, `20191014`, `20206498`.
Em todos os 5, `sinal_dz_filtrada = +` (a série que alimenta a detecção sobe do
passo 0 para o passo 1) e `sinal_dz_bruta = -` (a vorticidade bruta desce) —
ou seja, o sinal usado pela classificação do índice 0 (`z`, filtrada) é
oposto ao sinal da vorticidade bruta nesses 5 casos. Isso é consistente com o
mecanismo do artefato de contorno do filtro de Lanczos documentado no próprio
docstring de `process_vorticity` (determine_periods.py:413-493, não
reproduzido aqui na íntegra — trata do mesmo boundary ramp, mas não foi
verificado neste diagnóstico se é a MESMA causa do sinal invertido; ver
"não determinado" abaixo).

**Não determinado**: por que `sinal_dz_bruta` é sempre `-` e `sinal_dz_filtrada`
sempre `+` nos 5 casos (isto é, se é sempre assim ou coincidência dos 5 tracks
observados, e qual mecanismo exato do filtro de Lanczos produz a inversão de
sinal no primeiro passo). Este diagnóstico mediu o sinal, não a causa da
inversão; investigar a causa exigiria instrumentar `lanczos_bandpass_filter`
separadamente, fora do escopo desta tarefa.

### Nota metodológica importante — em qual estágio `decai_no_idx0` foi medido

`get_periods` roda, nesta ordem (determine_periods.py:1074-1083):
`find_intensification_period` → `find_decay_period` → `find_mature_stage` →
`find_residual_period` → `post_process_periods` → `find_incipient_period`.

As colunas `decai_no_idx0`, `decai_comprimento_passos`, `decai_fracao_serie` e
`decai_fracao_amplitude` em `idx0_inventory.csv` foram medidas no snapshot de
`df['periods']` **imediatamente após `find_decay_period`** (antes de
`find_mature_stage`, `find_residual_period`, `post_process_periods` e,
principalmente, `find_incipient_period`).

Isso foi necessário porque, na saída FINAL do pipeline (a que `determine_periods()`
de fato retorna), a fase de decaimento que abre em 4 dos 5 tracks **deixa de
começar no índice 0**: `find_incipient_period`, sob `incipient_method='plateau'`
(o método desta config), sobrescreve incondicionalmente `df.iloc[:boundary]`
com `'incipient'`, sem checar o que já estava em `periods` ali:

```
cyclophaser/find_stages.py:979:        if boundary > 0:
cyclophaser/find_stages.py:980:            # [t0, boundary) — half-open, hence .iloc and not the label-based
cyclophaser/find_stages.py:981:            # (inclusive) .loc slicing the geometric branches use.
cyclophaser/find_stages.py:982:            df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'
```

Medido (script, `idx0_final_stage.csv`): o `boundary` da regra plateau consome
8–38 passos do início da série nesses 5 tracks, que é menor que o comprimento
do bloco de decaimento original em 4 deles. Resultado, no `df['periods']` FINAL:

| track_id | `periods[0]` final | passos de `incipient` no início | 1ª fase não-incipiente (final) |
|---|---|---|---|
| 20180170 | incipient | 8  | **decay** |
| 20180608 | incipient | 38 | intensification |
| 20190325 | incipient | 9  | **decay** |
| 20191014 | incipient | 9  | **decay** |
| 20206498 | incipient | 9  | **decay** |

Ou seja: na saída final desta config, o índice 0 nunca é literalmente `'decay'`
(a checagem ingênua `periods.iloc[0] == 'decay'` daria 0/51) — mas em 4 dos 5
tracks afetados pelo artefato do índice 0, a primeira fase **não-incipiente**
continua sendo `decay`, não `intensification`, que é o que os rótulos manuais
dizem que deveria ser em 50/51 tracks. O artefato de classificação do índice 0
como `valley` continua produzindo um resultado incorreto na saída final; ele
só deixa de ser visível como "decay no índice 0" literal porque o prefixo
plateau absorve os primeiros passos. `20180608` é o único dos 5 em que o
`boundary` do plateau consome o bloco de decaimento inteiro e a série passa a
abrir (após o prefixo incipiente) com `intensification` — coincide com
`20180608` **não** estar na lista `bad_cases` do próprio config
(`20160735, 20180170, 20190325, 20191014, 20203947, 20206498`), enquanto os
outros 4 valley-tracks estão todos lá.

Nota à parte: `20160735` e `20203947` estão em `bad_cases` do config mas
**não** têm `idx0_tipo=valley` neste diagnóstico — ou seja, sua má-avaliação
não vem do artefato do índice 0. **Não determinado**: a causa da má-avaliação
desses dois tracks; fora do escopo desta tarefa (que é especificamente sobre
o artefato do índice 0).

### Conferência com os números do enunciado

O enunciado cita, para o artefato medido "no índice 0, antes do prefixo
incipiente": 52%/46% (20190325), 57%/32% (20206498), 30%/11% (20180170). Medido
neste diagnóstico (mesma definição: fração da série = comprimento do bloco de
decay líder / n_passos_total; fração da amplitude = |z[fim_do_decay] − z[0]| /
(z.max() − z.min()), com z = série filtrada que alimenta a detecção):

| track_id | fração da série | fração da amplitude |
|---|---|---|
| 20190325 | 52.69% | 46.36% |
| 20206498 | 57.89% | 32.03% |
| 20180170 | 31.88% | 11.41% |

Dois batem quase exatamente (20190325, 20206498). O terceiro (20180170) bate
em ordem de grandeza mas não exatamente (31.88% medido vs. 30% citado no
enunciado) — **não determinado** se a diferença é arredondamento do enunciado
ou uma definição ligeiramente distinta de "fração da série"/"fração da
amplitude" usada na medição original; este diagnóstico documenta a definição
exata usada (acima) para que a diferença seja rastreável.

---

## TAREFA 1b — o artefato e o filtro de proeminência

Código relevante, `find_peaks_valleys` (determine_periods.py:118-151) e
`_refine_extrema` (determine_periods.py:154-224).

### (a) Antes ou depois do filtro?

**Antes.** O extremo do índice 0 já está em `peaks`/`valleys` na primeira
chamada de `argrelextrema` (linhas 122-123), antes de qualquer filtro de
proeminência/distância. O filtro só é aplicado depois, condicionalmente:

```
cyclophaser/determine_periods.py:140:    if prominence is not None or prominence_relative is not None or distance is not None:
cyclophaser/determine_periods.py:141:        peaks   = _refine_extrema(data,  data, peaks,   prominence, prominence_relative, distance, N)
cyclophaser/determine_periods.py:142:        valleys = _refine_extrema(data, -data, valleys, prominence, prominence_relative, distance, N)
```

### (b) Isenção explícita ou proeminência acima do limiar?

**Isenção explícita**, não proeminência. Dentro de `_refine_extrema`:

```
cyclophaser/determine_periods.py:181:    boundary = {i for i in (0, N - 1) if i in set(candidates)}
cyclophaser/determine_periods.py:182:    interior = np.array([i for i in candidates if i not in boundary])
```

`boundary` é retirado do conjunto antes de qualquer filtro. A proeminência só
é calculada para `interior`:

```
cyclophaser/determine_periods.py:186:    if len(interior) > 0 and (prominence is not None or prominence_relative is not None or distance is not None):
cyclophaser/determine_periods.py:187:        with warnings.catch_warnings():
cyclophaser/determine_periods.py:188:            warnings.simplefilter("ignore")
cyclophaser/determine_periods.py:189:            prom_vals = peak_prominences(signed_data, interior)[0]
```

— ou seja, **nenhuma proeminência é calculada para o índice 0 pelo código de
produção**; ele nunca passa pelo filtro de proeminência nem pelo de distância,
tanto no ramo absoluto (linhas 194-197) quanto no relativo (linhas 204-209)
quanto no de distância (linhas 212-220, onde `kept = list(boundary)` já
inclui o índice 0 incondicionalmente, linha 214). Ele reentra no resultado
final aqui, independente de tudo o resto:

```
cyclophaser/determine_periods.py:223:    result = np.array(sorted(boundary | set(surviving_interior.tolist())), dtype=np.intp)
```

### (c) Proeminência e distância ao próximo extremo sobrevivente (5 tracks `valley`)

O pacote não calcula proeminência para o índice 0 (ver "b" acima). Os valores
abaixo foram calculados **fora do código de produção**, pelo script de
diagnóstico, chamando `scipy.signal.peak_prominences` no índice 0 exatamente
como `_refine_extrema` faz para candidatos interiores (mesmo `signed_data =
-data` para valleys) — como medição diagnóstica adicional, não como algo que
o pacote calcula ou usa.

Saída: `idx0b_prominence.csv`.

| track_id | proeminência do índice 0 (medida) | proeminência interior máxima de `z` | limiar (`prominence_relative` × máx.) | sobreviveria por mérito próprio? | passos até o próximo extremo sobrevivente |
|---|---|---|---|---|---|
| 20180170 | 0.0 | 7e-06 | 2.1e-06 | não | 21 |
| 20180608 | 0.0 | 4.1e-05 | 1.23e-05 | não | 10 |
| 20190325 | 0.0 | 1.5e-05 | 4.5e-06 | não | 64 |
| 20191014 | 0.0 | 4.7e-05 | 1.41e-05 | não | 52 |
| 20206498 | 0.0 | 1.5e-05 | 4.5e-06 | não | 40 |

A proeminência medida do índice 0 é **exatamente 0.0** nos 5 casos. Isso não é
coincidência dos dados: é uma consequência mecânica da definição de
`scipy.signal.peak_prominences` para um ponto na borda esquerda do array — sem
nenhum vizinho à esquerda, a base esquerda usada no cálculo é a própria altura
do ponto, o que zera a proeminência por construção sempre que o candidato está
no índice 0. Ou seja: mesmo que o índice 0 passasse pelo filtro de
proeminência em vez de ser isento, ele sempre falharia (proeminência 0 <
qualquer limiar positivo) — a isenção de borda não é redundante com o filtro,
é o único motivo dele sobreviver.

---

## TAREFA 2

Ver `labels_affected.md`. Tracks com `decai_no_idx0=sim` e `split=treino`:
`20180170`, `20180608`, `20190325`, `20191014` (`20206498` é `split=teste` —
excluído, rótulos não abertos).

---

## Arquivos entregues (não versionados)

- `build_idx0_inventory.py` — script de diagnóstico (somente leitura)
- `idx0_inventory.csv` — Tarefa 1
- `idx0_final_stage.csv` — conferência de estágio final do pipeline (ver nota metodológica acima)
- `idx0b_prominence.csv` — Tarefa 1b(c)
- `labels_affected.md` — Tarefa 2
- `REPORT.md` — este arquivo

## Observação final

A mensagem original termina em "Depois" sem completar a frase — não há
instrução adicional visível após esse ponto. Se havia uma Tarefa 3 ou passo
seguinte pretendido, ele não chegou a este agente; nada foi inferido para
preenchê-lo.

---
---

# Adendo — rodada de continuação (Tarefas 2b, 3, 4, 5)

Este adendo complementa o relatório acima; nada acima foi reescrito.

## TAREFA 2b

Ver `labels_affected.md`, seção "TAREFA 2b" (adicionada nesta rodada).
Resposta: **não** — nenhum dos 4 tracks de treino tem `decay` como primeira
fase não-incipiente no rótulo manual; nos 4, é `intensification`.

## TAREFA 3 — código literal

Ver `code_excerpts.md` (arquivo novo desta rodada). Resumo factual:

- **(a)** Não há um loop único sobre lista intercalada; são dois loops
  simétricos (`find_intensification_period`, `cyclophaser/find_stages.py:396-408`,
  e `find_decay_period`, `cyclophaser/find_stages.py:468-482`), cada um parando
  no PRÓXIMO extremo do tipo oposto via `array[array > x].min()` — não no
  "vizinho" na lista combinada. Peak seguido de peak (sem valley entre eles):
  ambos apontam para a mesma valley seguinte; a segunda escrita em `df.loc[...,
  'periods'] = 'intensification'` é uma sobreposição redundante do mesmo valor
  sobre um subconjunto do intervalo já escrito — sem checagem de tipo
  consecutivo, sem erro, sem ramificação especial.
- **(b)** Não existe tratamento específico para vão no início da série, nem em
  `post_process_periods` (o preenchimento de vão entre blocos pula
  explicitamente o primeiro bloco — `if i != 0:`,
  `cyclophaser/determine_periods.py:259`; o preenchimento de singleton só
  atua sobre índices já não-`NaN`, `cyclophaser/determine_periods.py:273`) nem
  em `find_residual_period` (só preenche do fim do último bloco em diante,
  `cyclophaser/find_stages.py:621-628` e `cyclophaser/find_stages.py:682-683`).
  O único preenchimento de `NaN` inicial que de fato ocorre é o `fillna`
  genérico (qualquer posição, não só o início) em `find_incipient_period`,
  `cyclophaser/find_stages.py:950`.
- **(c)** A confirmação estrita de ordem da fase madura
  (`cyclophaser/find_stages.py:340-352`) está **inline** no corpo de
  `find_mature_stage`, não fatorada em helper.

## TAREFA 4 — `find_incipient_period` lê ou só escreve?

- **(a)** Lê, mas a leitura não afeta o modo `plateau`. No topo da função,
  antes de qualquer ramificação por `incipient_method`:

  ```
  cyclophaser/find_stages.py:946:    periods = df['periods']
  cyclophaser/find_stages.py:950:    df['periods'] = df['periods'].fillna('incipient')
  cyclophaser/find_stages.py:952:    phases_order = []
  cyclophaser/find_stages.py:953:    current_phase = None
  cyclophaser/find_stages.py:954:
  cyclophaser/find_stages.py:955:    for phase in periods:
  cyclophaser/find_stages.py:956:        if pd.notnull(phase) and phase != 'residual':
  cyclophaser/find_stages.py:957:            if phase != current_phase:
  cyclophaser/find_stages.py:958:                phases_order.append(phase)
  cyclophaser/find_stages.py:959:                current_phase = phase
  ```

  `periods` (linha 946) é lido e `phases_order` é construído a partir dele
  (linhas 952-959) incondicionalmente, antes do `if incipient_method ==
  'plateau':` (linha 961). Mas `phases_order` só é usado no ramo `geometric`
  (linhas 990-1016); no ramo `plateau` (linhas 961-983) ele nunca é
  referenciado — é uma leitura que acontece, mas cujo resultado é descartado
  para este método. A própria coluna `df['periods']` é lida de novo apenas
  para o `fillna` (linha 950), que preenche `NaN` com `'incipient'`
  independente do método.

- **(b)** `boundary` não depende do mapa de fases. É calculado só a partir de
  `df['dz']` ou `df['z_unfil']` (conforme `incipient_plateau_signal`) e dos
  parâmetros de config (`tau`, `crossing`, `k`):

  ```
  cyclophaser/find_stages.py:969:        rel = _incipient_plateau_rel(
  cyclophaser/find_stages.py:970:            df, args_periods.get('incipient_plateau_signal', 'derivative'),
  cyclophaser/find_stages.py:971:            args_periods.get('incipient_smooth_window', 0),
  cyclophaser/find_stages.py:972:            args_periods.get('incipient_smooth_polyorder', 3))
  cyclophaser/find_stages.py:973:        boundary = _incipient_plateau_boundary(
  cyclophaser/find_stages.py:974:            rel,
  cyclophaser/find_stages.py:975:            args_periods.get('incipient_plateau_tau', 0.20),
  cyclophaser/find_stages.py:976:            args_periods.get('incipient_plateau_crossing', 'single'),
  cyclophaser/find_stages.py:977:            args_periods.get('incipient_plateau_k', 3),
  cyclophaser/find_stages.py:978:        )
  ```

  `_incipient_plateau_rel` (`cyclophaser/find_stages.py:799-837`) só lê
  `df['dz']` ou `df['z_unfil']`. `_incipient_plateau_boundary`
  (`cyclophaser/find_stages.py:840-883`) recebe apenas o array `rel` e
  escalares (`tau`, `crossing`, `k`) — nenhum dos dois recebe ou lê
  `df['periods']`.

- **(c)** Não é incondicional: guardada por `if boundary > 0:`.

  ```
  cyclophaser/find_stages.py:979:        if boundary > 0:
  cyclophaser/find_stages.py:980:            # [t0, boundary) — half-open, hence .iloc and not the label-based
  cyclophaser/find_stages.py:981:            # (inclusive) .loc slicing the geometric branches use.
  cyclophaser/find_stages.py:982:            df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'
  cyclophaser/find_stages.py:983:        return df
  ```

  Quando `boundary == 0`, a linha 982 não executa e a função retorna sem
  tocar `periods` — o que já estava lá (por exemplo `'decay'`, escrito por
  `find_decay_period`) permanece intocado.

## TAREFA 5 — tabela final

Script: `build_final_output_check.py` (novo nesta rodada; reaproveita
`run_pipeline_with_snapshots` de `build_idx0_inventory.py` e chama
`cyclophaser.find_stages._incipient_plateau_rel` /
`_incipient_plateau_boundary` diretamente — as mesmas funções que
`find_incipient_period` chama em `find_stages.py:969-978` — para obter
`boundary` sem inferi-lo da coluna final).

Saída: `final_output_check.csv`.

| track_id | split | decai_comprimento_passos | incipient_boundary | bloco_sobrevive | 1ª fase não-incipiente (saída final) | 1ª fase não-incipiente (rótulo) |
|---|---|---|---|---|---|---|
| 20180170 | treino | 22 | 8 | sim | decay | intensification |
| 20180608 | treino | 11 | 38 | **não** | intensification | intensification |
| 20190325 | treino | 88 | 9 | sim | decay | intensification |
| 20191014 | treino | 124 | 9 | sim | decay | intensification |
| 20206498 | teste | 77 | 9 | sim | decay | (não aberto) |

O track com `bloco_sobrevive = não` é **`20180608`**: seu `incipient_boundary`
(38) excede o comprimento do bloco de decaimento original (11), então o
prefixo `incipient` consome o bloco de decaimento inteiro e mais um trecho
além dele; a saída final passa a abrir (após o prefixo) com `intensification`,
não `decay`.

Dos 4 tracks de treino, **3** divergem do rótulo na primeira fase
não-incipiente da saída final (`20180170`, `20190325`, `20191014` — saída diz
`decay`, rótulo diz `intensification`); `20180608` não diverge (ambos dizem
`intensification`, ainda que por um `boundary` que passa muito além do fim do
bloco de decaimento original, não porque o artefato do índice 0 tenha deixado
de agir).

## Arquivos gerados nesta rodada (não versionados)

- `code_excerpts.md`
- `build_final_output_check.py`
- `final_output_check.csv`
- Adendo a `REPORT.md` (este bloco) e a `labels_affected.md` (seção Tarefa 2b)

## Itens não determinados nesta rodada

Nenhum item novo além dos já listados na rodada anterior (causa da inversão de
sinal `sinal_dz_bruta`/`sinal_dz_filtrada`; a pequena divergência de 20180170
entre 30% citado e 31.88% medido; a causa da má-avaliação de `20160735` e
`20203947`, que não têm `idx0_tipo=valley`).

---
---

# Adendo — rodada de continuação (Tarefas 6, 7)

Este adendo complementa o relatório acima; nada acima foi reescrito. Nenhuma
medição anterior foi refeita — os números abaixo vêm de `idx0_inventory.csv`,
`labels_affected.md` e `final_output_check.csv`, já produzidos, mais uma
extração pontual de valores numéricos (`build_task6_values.py`) e de posições
de extremos (`build_span_ownership.py`).

## TAREFA 6 — inversão de sinal bruta vs. filtrada

Tabela 2×2, `idx0_tipo` × concordância de sinal (`sinal_dz_bruta ==
sinal_dz_filtrada`), sobre os 51 tracks reais de `idx0_inventory.csv`:

| idx0_tipo \ concordância | sim | não |
|---|---|---|
| peak (46) | 44 | 2 |
| valley (5) | 0 | 5 |

Os 2 casos `peak`/discordância: `20180759`, `20190397`. Os 5 casos
`valley`/discordância são os 5 já conhecidos: `20180170`, `20180608`,
`20190325`, `20191014`, `20206498`.

### z[0], z[1] e |z[1]−z[0]|, bruta vs. filtrada, para os 5 `valley`

Extraído via `build_task6_values.py` (lê `df['z']` — a série filtrada que
alimenta a detecção — e `df['z_unfil']` — vorticidade bruta — nos mesmos
`df` já produzidos por `run_pipeline_with_snapshots`, sem modificar o
pacote):

| track_id | z[0] filtrada | z[1] filtrada | \|Δz\| filtrada | z_unfil[0] bruta | z_unfil[1] bruta | \|Δz\| bruta |
|---|---|---|---|---|---|---|
| 20180170 | −2.812336×10⁻⁵ | −2.812047×10⁻⁵ | 2.896×10⁻⁹ | −3.575920×10⁻⁵ | −3.645330×10⁻⁵ | 6.941×10⁻⁷ |
| 20180608 | −3.284536×10⁻⁵ | −3.255766×10⁻⁵ | 2.877×10⁻⁷ | −5.398490×10⁻⁵ | −5.471000×10⁻⁵ | 7.251×10⁻⁷ |
| 20190325 | −2.851582×10⁻⁶ | −2.585492×10⁻⁶ | 2.661×10⁻⁷ | −1.204020×10⁻⁵ | −1.306720×10⁻⁵ | 1.027×10⁻⁶ |
| 20191014 | −1.767200×10⁻⁶ | −1.635034×10⁻⁶ | 1.322×10⁻⁷ | −2.608410×10⁻⁵ | −2.804000×10⁻⁵ | 1.956×10⁻⁶ |
| 20206498 | −1.610951×10⁻⁵ | −1.609565×10⁻⁵ | 1.386×10⁻⁸ | −2.979592×10⁻⁵ | −3.179347×10⁻⁵ | 1.998×10⁻⁶ |

Em todos os 5, a vorticidade bruta cai de z_unfil[0] para z_unfil[1] (fica
mais negativa: sinal `sinal_dz_bruta = -`) enquanto a série filtrada sobe
(fica menos negativa: `sinal_dz_filtrada = +`) — e em todos os 5, `|Δz|`
bruta é maior que `|Δz|` filtrada (de ~4× em 20180608 a ~1440× em 20206498),
i.e. o filtro não só inverte o sinal como também amortece bastante a
magnitude do primeiro passo. **Não determinado** (fora do escopo desta
tarefa, que pede os valores, não o mecanismo): por que o filtro de Lanczos
produz especificamente essa inversão de sinal nestes 5 casos.

**Resposta em uma linha:** a discordância de sinal **não é exclusiva** dos 5
`valley` — aparece também em 2 dos 46 `peak` (`20180759`, `20190397`), 7 dos
51 tracks reais no total.

## TAREFA 7 — o que o rótulo diz que ocupa o trecho

Script: `build_span_ownership.py`. `idx_primeiro_peak_sobrevivente` foi lido
diretamente de `df['z_peaks_valleys']` (posição do primeiro `'peak'`
sobrevivente em posição > 0) e conferido contra
`decai_comprimento_passos − 1` de `idx0_inventory.csv` — os dois bateram
exatamente nos 4 tracks (`cross_check_ok=True` para todos). Valores de rótulo
transcritos de `labels_affected.md` (não reabri `manual_labels.yaml` nesta
rodada); `detector_incipient_boundary` transcrito de `final_output_check.csv`.

Saída: `span_ownership.csv`.

| track_id | idx_primeiro_peak_sobrevivente | rótulo incipiente start_idx | rótulo incipiente end_idx (= start da 1ª fase não-incipiente) | rótulo incipiente tolerance_idx | rótulo 1ª fase não-incipiente | detector_incipient_boundary | comprimento total |
|---|---|---|---|---|---|---|---|
| 20180170 | 21 | 0 | 20 | 5 | intensification | 8 | 69 |
| 20180608 | 10 | 0 | 37 | 5 | intensification | 38 | 117 |
| 20190325 | 87 | 0 | 10 | 5 | intensification | 9 | 167 |
| 20191014 | 123 | (sem fase incipient no rótulo) | 0 | não determinado (sem fase incipient à qual associar tolerance_idx) | intensification | 9 | 206 |

`rotulo_incipiente_tolerance_idx` de `20191014`: **não determinado** — o
rótulo deste track não tem entrada `phase: incipient` (a sequência começa em
`intensification` no índice 0), então não existe um `tolerance_idx` de fase
incipiente para reportar.

### Dono majoritário do trecho `[0, idx_primeiro_peak_sobrevivente]`, segundo o rótulo

Contagem de índices dentro do trecho `[0, P]` atribuídos pelo rótulo a
`incipient` (`[0, E)`) vs. `intensification` (`[E, P]`), onde `E` = rótulo
incipiente end_idx:

- **20180170** (P=21, E=20): incipiente = 20 índices (0–19), intensificação =
  2 índices (20–21). **Majoritariamente incipiente.**
- **20180608** (P=10, E=37): E > P, o trecho inteiro (11 índices, 0–10) cai
  dentro do incipiente rotulado. **Majoritariamente incipiente** (100%).
- **20190325** (P=87, E=10): incipiente = 10 índices (0–9), intensificação =
  78 índices (10–87). **Majoritariamente intensificação.**
- **20191014** (P=123, E=0): sem fase incipiente rotulada, o trecho inteiro
  (124 índices, 0–123) é rotulado `intensification`. **Majoritariamente
  intensificação** (100%).

## Arquivos gerados nesta rodada (não versionados)

- `build_task6_values.py`
- `build_span_ownership.py`
- `span_ownership.csv`
- Adendo a `REPORT.md` (este bloco)

## Itens não determinados nesta rodada

- Mecanismo pelo qual o filtro de Lanczos inverte o sinal do primeiro passo
  nestes 5 (+2) casos (pedido era só os valores, não a causa).
- `rotulo_incipiente_tolerance_idx` para `20191014` (não existe fase
  `incipient` no rótulo deste track).
