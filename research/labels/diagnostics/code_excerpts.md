# TAREFA 3 — trechos de código na íntegra

## (a) Loop que constrói os segmentos de fase a partir da lista filtrada de extremos

Não há um único loop combinado sobre uma lista intercalada peak/valley; são dois
loops simétricos, cada um sobre uma das duas listas filtradas separadas
(`z_peaks`, `z_valleys`), cada um construindo o próprio tipo de segmento.

### `find_intensification_period` (constrói segmentos de `intensification`, peak → valley seguinte)

`cyclophaser/find_stages.py:389-408`:

```python
    # Find z peaks and valleys
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index

    length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Find intensification periods between z peaks and valleys
    for z_peak in z_peaks:
        next_z_valley = z_valleys[z_valleys > z_peak].min()
        if not pd.isna(next_z_valley):
            intensification_start = z_peak
            intensification_end = next_z_valley

            # Intensification needs to meet the minimum length threshold
            # (fraction of the series length, or of the local cycle scale).
            scale = (_local_cycle_scale(df, intensification_start, intensification_end)
                     if length_scale == 'local' else length)
            if intensification_end-intensification_start > scale * threshold_intensification_length:
                df.loc[intensification_start:intensification_end, 'periods'] = 'intensification'
```

### `find_decay_period` (constrói segmentos de `decay`, valley → peak seguinte)

`cyclophaser/find_stages.py:460-482`:

```python
    # Find z peaks and valleys
    z_peaks = df[df['z_peaks_valleys'] == 'peak'].index
    z_valleys = df[df['z_peaks_valleys'] == 'valley'].index

    length = df.index[-1] - df.index[0]
    dt = df.index[1] - df.index[0]

    # Find decay periods between z valleys and peaks
    for z_valley in z_valleys:
        next_z_peak = z_peaks[z_peaks > z_valley].min()
        if not pd.isna(next_z_peak):
            decay_start = z_valley
            decay_end = next_z_peak
        else:
            decay_start = z_valley
            decay_end = df.index[-1]  # Last index of the DataFrame

        # Decay needs to meet the minimum length threshold (fraction of the
        # series length, or of the local cycle scale).
        scale = (_local_cycle_scale(df, decay_start, decay_end)
                 if length_scale == 'local' else length)
        if decay_end - decay_start > scale * threshold_decay_length:
            df.loc[decay_start:decay_end, 'periods'] = 'decay'
```

### Pareamento de extremos consecutivos, e o que acontece com peak → peak

O pareamento não é "próximo extremo na lista intercalada"; é, para cada
elemento de UMA lista, o menor elemento da OUTRA lista que seja maior que ele:
`z_valleys[z_valleys > z_peak].min()` (linha 397) e
`z_peaks[z_peaks > z_valley].min()` (linha 469). Cada peak busca
independentemente a próxima valley em toda a série (não necessariamente a
"vizinha imediata" num sentido de lista combinada), e vice-versa.

Quando dois peaks aparecem em sequência sem uma valley entre eles (`P1 < P2`,
nenhuma valley em `(P1, P2)`), o próximo valley `V` depois de `P1`
(`z_valleys[z_valleys > P1].min()`) é o mesmo `V` que é o próximo valley depois
de `P2` (`z_valleys[z_valleys > P2].min()`), já que não há valley entre eles.
O loop então executa, para `P1`: `df.loc[P1:V, 'periods'] = 'intensification'`
(linha 408), e, na iteração seguinte para `P2`: `df.loc[P2:V, 'periods'] =
'intensification'` (mesma linha 408) — um subconjunto do intervalo já
escrito, com o mesmo valor. Não há checagem de tipo consecutivo, não há erro,
não há ramificação especial: a segunda escrita é uma sobreposição idêntica e
redundante sobre a primeira. Cada segmento ainda passa pelo próprio teste de
comprimento mínimo (linha 407) independentemente — um dos dois pode passar e o
outro não, sem que isso afete o outro.

---

## (b) Tratamento de vão não atribuído no INÍCIO da série

**Não existe** tratamento específico para um vão (`NaN`) que começa no índice
0, nem em `post_process_periods` nem em `find_residual_period`.

### `post_process_periods` — preenchimento de vão entre blocos

`cyclophaser/determine_periods.py:249-266`:

```python
    # Find consecutive blocks of intensification and decay
    intensification_blocks = np.split(df[df['periods'] == 'intensification'].index, np.where(np.diff(df[df['periods'] == 'intensification'].index) != dt)[0] + 1)
    decay_blocks = np.split(df[df['periods'] == 'decay'].index, np.where(np.diff(df[df['periods'] == 'decay'].index) != dt)[0] + 1)
    
    # Fill NaN periods between consecutive intensification or decay blocks
    for blocks in [intensification_blocks, decay_blocks]:
        if len(blocks) > 1:
            phase = df.loc[blocks[0][0], 'periods']
            for i in range(len(blocks)):
                block = blocks[i]
                if i != 0:
                    if len(block) > 0:
                        last_index_prev_block = blocks[i -1][-1]
                        first_index_current_block = block[0]
                        preiods_between = df.loc[
                            (last_index_prev_block + dt):(first_index_current_block - dt)]['periods']
                        if all(pd.isna(preiods_between.unique())):
                            df.loc[preiods_between.index, 'periods'] = phase
```

`if i != 0:` (linha 259) explicitamente pula o primeiro bloco de cada lista —
o preenchimento só ocorre ENTRE `blocks[i-1]` e `blocks[i]` para `i >= 1`.
Não há iteração que preencha o vão ANTES de `blocks[0]`, isto é, antes do
primeiro bloco de `intensification`/`decay` já atribuído. Um vão que começa no
índice 0 e termina antes do primeiro bloco não é tocado por este trecho.

### `post_process_periods` — substituição de períodos-ilha (singleton)

`cyclophaser/determine_periods.py:271-282`:

```python
    for index in df.index:
        period = df.loc[index, 'periods']
        if pd.notna(period):
            prev_index = index - dt
            next_index = index + dt
            prev_same = prev_index in df.index and df.loc[prev_index, 'periods'] == period
            next_same = next_index in df.index and df.loc[next_index, 'periods'] == period
            if not prev_same and not next_same:
                if prev_index in df.index and prev_index != df.index[0]:
                    df.loc[index, 'periods'] = df.loc[prev_index, 'periods']
                elif next_index in df.index:
                    df.loc[index, 'periods'] = df.loc[next_index, 'periods']
```

`if pd.notna(period):` (linha 273) só atua sobre índices JÁ atribuídos
(não-`NaN`); um vão `NaN` no início da série nunca entra neste ramo.

### `find_residual_period` — só preenche o final da série

`cyclophaser/find_stages.py:600-628` (caso de fase única) e
`cyclophaser/find_stages.py:661-683` (caso de múltiplas fases) — os dois
únicos pontos em que a função escreve `'residual'` sobre `NaN` — em ambos, a
escrita é `df.loc[<último_bloco> + dt:, 'periods'] = ...fillna('residual')`,
isto é, sempre a partir do FIM do último bloco relevante até o fim da série,
nunca antes do início de um bloco:

```python
        # Find the index right after the last block
        if len(last_phase_block) > 0:
            last_phase_block_end = last_phase_block[-1]
            df.loc[last_phase_block_end + dt:, 'periods'] = df.loc[last_phase_block_end + dt:, 'periods'].fillna('residual')
        else:
            # B4 fix: fillna with inplace=True on a slice is a no-op in pandas; use
            # assignment instead.
            last_phase_block_end = phase_blocks[-2][-1]
            df.loc[last_phase_block_end + dt:, 'periods'] = df.loc[last_phase_block_end + dt:, 'periods'].fillna('residual')
```
(`cyclophaser/find_stages.py:621-628`)

```python
        dt = df.index[1] - df.index[0]
        df.loc[last_decay_index + dt:, 'periods'] = df.loc[last_decay_index + dt:, 'periods'].fillna('residual')
```
(`cyclophaser/find_stages.py:682-683`)

Nenhum dos dois pode preencher um vão que precede o primeiro bloco atribuído
— ambos operam a partir de `<algum índice já atribuído> + dt` em diante.

O único ponto do pipeline que de fato preenche um `NaN` inicial é o
`fillna('incipient')` incondicional em `find_incipient_period`
(`cyclophaser/find_stages.py:950`, ver TAREFA 4) — mas essa não é uma regra
específica para vão INICIAL: é um preenchimento genérico de qualquer `NaN`
remanescente em qualquer posição da série, que apenas cobre o caso inicial
como caso particular, sem tratá-lo de forma diferenciada.

---

## (c) `find_mature_stage` — confirmação estrita de ordem para a fase madura

**Inline**, não fatorada em helper reutilizável (ao contrário de
`_amplitude_mature_bounds` e `_local_cycle_scale`, que são helpers dedicados
usados por esta mesma função).

`cyclophaser/find_stages.py:340-352`:

```python
    mature_periods = df[df['periods'] == 'mature'].index
    if len(mature_periods) > 0:
        blocks = np.split(mature_periods, np.where(np.diff(mature_periods) != dt)[0] + 1)
        for block in blocks:
            block_start, block_end = block[0], block[-1]
            prev_idx = block_start - dt
            next_idx = block_end + dt
            # A mature block at the series boundary cannot have required neighbours —
            # treat missing neighbour as "condition not satisfied" and clear the block.
            if prev_idx not in df.index or next_idx not in df.index or \
               df.loc[prev_idx, 'periods'] != 'intensification' or \
               df.loc[next_idx, 'periods'] != 'decay':
                df.loc[block_start:block_end, 'periods'] = np.nan
```

Este bloco está no corpo de `find_mature_stage` (que termina em
`cyclophaser/find_stages.py:354`), depois do laço que constrói as janelas
maduras candidatas (linhas 253-312); não chama nenhuma função auxiliar própria
— é a checagem final inline da própria função.
