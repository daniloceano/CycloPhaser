# Implementação e medição — correção do tipo de extremo no índice 0

Branch: `fix/idx0-boundary-extremum-type`, criada a partir de `develop-v2.1` @
`887c628`. **Nada commitado.** Estado: AGUARDANDO APROVAÇÃO.

Diagnóstico de base: `research/labels/diagnostics/REPORT.md` (rodadas
anteriores). Não re-verificado aqui.

---

## Diff literal

`cyclophaser/determine_periods.py`, logo após `argrelextrema` (linhas
122-123 originais), antes do bloco de `zeros`/`_collapse_plateaux`/filtro de
proeminência-distância:

```diff
     # Detect raw extrema (>= / <= catches flat-top plateaux as multiple indices)
     peaks   = argrelextrema(data, np.greater_equal)[0]
     valleys = argrelextrema(data, np.less_equal)[0]
+
+    # Index 0's extremum type is an artefact of mode='clip' (see the NOTE #14
+    # in this function's docstring): with no real left neighbour, argrelextrema
+    # compares data[0] against itself, which always passes under a non-strict
+    # comparator, so index 0 is marked as an extremum regardless of the data.
+    # Its TYPE (peak vs valley) then falls out of the sign of data[1]-data[0]
+    # alone -- a single boundary finite difference, not a reliable signal about
+    # the cyclone's actual state at t0. A cyclone life cycle opens with
+    # intensification, never decay, so index 0 is forced to 'peak': dropped
+    # from valleys if present, and added to peaks unless it is already there
+    # (it may already be in both, on a data[0]==data[1] tie).
+    if 0 in valleys:
+        valleys = valleys[valleys != 0]
+        if 0 not in peaks:
+            peaks = np.sort(np.append(peaks, 0))
+
     zeros   = np.where(data == 0)[0]
```

Nenhum outro arquivo do pacote foi tocado. `find_decay_period`,
`find_mature_stage`, `post_process_periods`, `find_incipient_period`: intactos
(conferido — `git diff --stat` mostra só `determine_periods.py` e
`CHANGELOG.md`).

---

## Metodologia das medições

`capture_pipeline_state.py before` foi rodado ANTES da edição acima (código
original de `develop-v2.1`), salvando `fix_state_before.json` (períodos e
`z_peaks_valleys` completos, 51 tracks reais + 12 sintéticos). Depois de
aplicada a edição, `capture_pipeline_state.py after` gerou
`fix_state_after.json`. `compare_before_after.py` faz o diff programático dos
dois. `investigate_m5.py` investiga a divergência da M5, track a track.
`evaluate_against_labels.py --config cyclophaser_params-9.yaml` (sem
`--test`, então só TREINO é tocado) rodou antes (`fix_eval_before.txt`) e
depois (`fix_eval_after.txt`) da edição.

---

## M1 — no-op nos 46

**Previsto:** 46/46 idênticos. **Medido: 46/46 idênticos.** Sem divergência.

Comparação do array `periods` completo (não só o placar), track a track, nos
46 tracks reais com `idx0_tipo=peak` (`compare_before_after.py`, saída em
`fix_compare_before_after.txt`): `identical: 46/46`, `diverging: 0/46`.

## M2 — o peak forçado sobrevive ao filtro

**Previsto:** presente em 5/5. **Medido: presente em 5/5** — mas ver nota de
escopo abaixo sobre `20206498`.

| track_id | split | `z_peaks_valleys[0]` antes | depois |
|---|---|---|---|
| 20180170 | treino | valley | **peak** |
| 20180608 | treino | valley | **peak** |
| 20190325 | treino | valley | **peak** |
| 20191014 | treino | valley | **peak** |
| 20206498 | teste | valley | **peak** |

Nota de escopo: esta linha é saída mecânica do detector (`z_peaks_valleys`),
sem abrir nenhum rótulo — mesma categoria de medição já permitida para
`20206498` nas rodadas 1-3 (`idx0_inventory.csv`, `final_output_check.csv`).
Ela não é usada em nenhum critério de aprovação da correção; o critério de
aprovação real (M3/M4/M5) usa só os 4 tracks de treino, como pedido pela
restrição desta rodada.

## M3 — primeira fase não-incipiente, saída final, treino afetados

**Previsto:** 20180170/20190325/20191014 passam de `decay` para
`intensification` (0/3 → 3/3); 20180608 não muda.
**Medido: exatamente como previsto.**

| track_id | antes | depois |
|---|---|---|
| 20180170 | decay | **intensification** |
| 20180608 | intensification | intensification (sem mudança) |
| 20190325 | decay | **intensification** |
| 20191014 | decay | **intensification** |

## M4 — incipiente, treino real

**Previsto:** idênticos (fronteira 8/17, recusa 14/16).
**Medido: idênticos**, campo a campo (`fix_eval_before.txt` vs.
`fix_eval_after.txt`, seção `TRAIN · real`, bloco `── incipient boundary ──`):

```
    boundary labels    17   hit within margin   8  ( 47.1%)      [antes e depois, idêntico]
    raw distance      MAE   4.82   worst     26   (over 11 comparable)   [idêntico]
    refusal           detector found no incipient phase on 6 of those 17  [idêntico]
                      label says none:  16, detector agreed on 14 ( 87.5%) [idêntico]
                      label ambiguous:   2, detector found none on 1       [idêntico]
```

Sem divergência. Consistente com o previsto: `boundary` depende só de
`dz`/`z_unfil` e da config (`find_stages.py:969-978`, já verificado nas
rodadas anteriores), nunca do mapa de fases — logo é matematicamente
invariante à mudança de tipo do extremo em `z_peaks_valleys`. (O mesmo vale
para `TRAIN · synthetic` e `TRAIN · ALL`: idênticos também, não pedido
explicitamente mas conferido.)

## M5 — sequência inteira, treino real

**Previsto:** +2 (18/35 → 20/35): 20190325 e 20191014 passam a bater;
20180170 continuaria reprovando pela fronteira curta da incipiente.
**Medido: +1 (18/35 → 19/35). DIVERGE do previsto — investigado.**

Track a track (`investigate_m5.py`, saída em `fix_investigate_m5.txt`):

- **Vira bate (1):** `20180170` — label
  `['incipient','intensification','mature','decay']`; detector antes
  `['incipient','decay','intensification','mature','decay']`; detector depois
  `['incipient','intensification','mature','decay']`. Bate.
- **Vira não-bate (0):** nenhuma. Nenhuma regressão entre os 35 de treino
  real.
- **Continuam não batendo, entre os 4 afetados:**
  - `20190325`: label `['incipient','intensification','mature','decay']`;
    detector depois `['incipient','intensification','mature','decay',
    'intensification','mature','decay']` — ciclo duplicado.
  - `20191014`: label `['intensification','mature','decay']`; detector depois
    `['incipient','intensification','mature','decay','intensification',
    'mature','decay']` — ciclo duplicado (e também ganhou um `incipient` que
    o rótulo não tem, uma divergência à parte da fronteira já conhecida).

### Causa investigada: o `20180170` bateu por um motivo diferente do previsto, e um ciclo espúrio duplicado aparece em `20190325`/`20191014`

**Por que `20180170` bateu (não pela razão prevista):** `score_phase_sequences`
compara só os NOMES das fases em ordem (`labels_core.py:636`,
`[p for p,_ in lab] != [p for p,_ in det]`) — a POSIÇÃO da fronteira não entra
nesse critério (isso é `boundary error`, uma métrica separada). A previsão
assumia que a fronteira curta da incipiente (rótulo ~20, detector 8)
reprovaria `20180170` na sequência inteira, mas fronteira errada não é
sequência errada quando os NOMES batem — e batem. A suposição da previsão
estava errada nesse ponto específico, não a implementação.

**Por que `20190325` e `20191014` NÃO bateram (mecanismo novo, mecânico,
confirmado):** `find_intensification_period`/`find_mature_stage` pareiam
"o extremo mais próximo do tipo oposto em toda a série" (já documentado em
`code_excerpts.md`, rodada 3), não "o vizinho na lista intercalada". Ao forçar
o índice 0 a `peak`, ele passa a se casar com a PRIMEIRA valley real da série
(mesma valley que antes só delimitava o fim do decaimento espúrio) e
`find_mature_stage` ganha, para essa valley, um `previous_z_peak` que antes
não existia (`z_peaks[z_peaks < z_valley]` era vazio antes; agora inclui o 0).
Isso satisfaz a confirmação estrita de ordem
(`find_stages.py:340-352`, intensification→mature→decay) e cria um SEGUNDO
ciclo completo (intensification+mature+decay) no início da série, ANTES do
ciclo genuíno que já existia. Medido (`z_peaks_valleys`, `compare_before_after.py`):

```
20190325 antes: valley(0) valley(64) peak(87)  valley(103) peak(121) peak(166)
20190325 depois: peak(0)  valley(64) peak(87)  valley(103) peak(121) peak(166)
  -> novo bloco mature em (59,67), somado ao original (101,104)

20191014 antes: valley(0) valley(52) peak(123) valley(137) peak(205)
20191014 depois: peak(0)  valley(52) peak(123) valley(137) peak(205)
  -> novo bloco mature em (47,56), somado ao original (135,139)
```

**Por que `20180170` e `20180608` NÃO ganham esse ciclo duplicado:** nos dois,
já existia um peak genuíno ENTRE o índice 0 e a primeira valley interior
(peak em 21 antes da valley em 39, em `20180170`; peaks em 10 e 37 antes da
valley em 66, em `20180608`) — esse peak já era o `previous_z_peak` mais
próximo dessa valley antes da correção, então adicionar o peak em 0 não muda
`z_peaks[z_peaks < z_valley][-1]` (o mais próximo, não o primeiro). Confirmado
via `z_peaks_valleys`:

```
20180170 antes: valley(0) peak(21) valley(39) peak(68)
20180170 depois: peak(0)  peak(21) valley(39) peak(68)   (peak mais próximo de valley39 continua sendo 21)

20180608 antes: valley(0) peak(10) peak(37) valley(66) peak(97) peak(116)
20180608 depois: peak(0)  peak(10) peak(37) valley(66) peak(97) peak(116)  (peak mais próximo de valley66 continua sendo 37)
```

Observação mecânica adicional (sem abrir rótulo, `20206498`, teste, **fora de
qualquer critério**): o mesmo padrão se repete — antes não havia
`previous_z_peak` para a valley em 40 (nenhum peak antes dela), depois passa a
haver (peak em 0), e surge um novo bloco `mature` em (34,46) onde antes não
havia nenhum. Consistente com o mecanismo acima, três ocorrências
independentes confirmando o mesmo efeito estrutural.

**Conclusão da investigação:** o ganho de +1 em vez de +2 tem duas causas
distintas e já totalmente explicadas, nenhuma delas um bug da implementação
(que fez exatamente o que foi pedido): (1) a previsão original errou o motivo
do `20180170` bater — bateu, só que por causa errada; (2) `20190325` e
`20191014` não batem porque a correção — junto com a lógica de pareamento de
extremos já existente e documentada — cria um ciclo intensification-mature-
decay espúrio adicional no início da série sempre que a primeira valley
interior não tinha nenhum peak genuíno antes dela. Isso é uma interação nova
e não-óbvia entre a correção e o código de pareamento existente,
não coberta pelas medições M1-M4.

(Detalhe lateral, não um problema: o número de fronteiras "not sure" no
relatório de `TRAIN · real` sobe de 2 para 5 entre antes e depois — não é uma
mudança nos rótulos, é consequência direta de `20180170` (3 fronteiras
`unsure=true`, ver `labels_affected.md`) passar a entrar no grupo "bate", que
é o único grupo cujas fronteiras `unsure` são contadas,
`labels_core.py:628-641`.)

## M6 — fase madura nos 5 tracks (sem julgamento, só reporte)

| track_id | split | mature antes | mature depois |
|---|---|---|---|
| 20180170 | treino | [(37, 45)] | [(37, 45)] — sem mudança |
| 20180608 | treino | [(63, 69)] | [(63, 69)] — sem mudança |
| 20190325 | treino | [(101, 104)] | [(59, 67), (101, 104)] — **novo bloco adicionado antes do original** |
| 20191014 | treino | [(135, 139)] | [(47, 56), (135, 139)] — **novo bloco adicionado antes do original** |
| 20206498 | teste — fora de critério | [] (nenhum bloco) | [(34, 46)] — **novo bloco onde antes não havia nenhum** |

Mecanismo: ver investigação da M5 acima (mesmo efeito: o peak forçado em 0
passa a servir de `previous_z_peak` para a primeira valley interior nos
tracks em que essa valley não tinha peak genuíno antes dela).

## M7 — sintéticos

**Previsto:** nenhuma mudança. **Medido: 8/12 idênticos, 4/12 DIFERENTES.
DIVERGE do previsto — investigado, causa identificada com certeza.**

| opaque_id | nome do caso | antes | depois |
|---|---|---|---|
| s0596ea57 | IcIt_observational | igual | igual |
| s46657891 | quase_ItD | igual | igual |
| s4e7ff65c | ItMD_clean | igual | igual |
| s5b8aa46f | **DItMD_residual_noisy** | igual | **diferente** |
| s5dcc0f79 | IcItMD_residual_clean | igual | igual |
| s6b1e8245 | **IcDItMD_noisy** | igual | **diferente** |
| s6b542eee | ItMD_ItMD_noisy | igual | igual |
| s8001f17b | **DItMD_noisy** | igual | **diferente** |
| s9ddbc53c | IcItMD_residual_noisy | igual | igual |
| sbceec644 | ItMD_noisy | igual | igual |
| sbd6c6920 | IcItMD_ItMD_noisy | igual | igual |
| scfcf1387 | **IcDItMD_residual_noisy** | igual | **diferente** |

### Causa: os 4 casos que mudam são, por construção, os únicos com `D` (decay) como primeira letra do nome — decaimento GENUÍNO no início, não artefato

Os 4 nomes que mudam (`DItMD_noisy`, `DItMD_residual_noisy`, `IcDItMD_noisy`,
`IcDItMD_residual_noisy`) são exatamente os 4 dos 12 casos sintéticos cujo
nome começa a sequência de fases com `D` — construídos deliberadamente para
abrir com decaimento genuíno (ver `labels_core.py:10-17`: "IcDItMD_noisy (D
in sine) and DItMD_noisy (D in linear) have the same segments and different
answers"). Comparado contra o rótulo manual desses 4 casos (`manual_labels.yaml`,
não é split de teste, é sintético/treino):

```
s8001f17b DItMD_noisy:            label=[decay,intensification,mature,decay]                    antes=bate  depois=[intensification,mature,decay]              NÃO bate
s5b8aa46f DItMD_residual_noisy:   label=[decay,intensification,mature,decay,residual]            antes=bate  depois=[intensification,mature,decay,residual]     NÃO bate
s6b1e8245 IcDItMD_noisy:          label=[incipient,decay,intensification,mature,decay]           antes=bate  depois=[incipient,intensification,mature,decay]    NÃO bate
scfcf1387 IcDItMD_residual_noisy: label=[incipient,decay,intensification,mature,decay,residual]  antes=bate  depois=[incipient,intensification,mature,decay,residual] NÃO bate
```

Os 4 batiam PERFEITAMENTE antes da correção (o detector corretamente
identificava o decaimento genuíno de abertura nesses casos construídos para
isso) e os 4 **regridem** para não-bate depois: a fase `decay` inicial
desaparece da sequência detectada, substituída por nada (a série passa a
abrir direto em `intensification`). Isto é consequência direta, mecânica e
esperada da correção: ela assume incondicionalmente que "o ciclo de vida
sempre abre com intensificação, nunca com decaimento" — verdadeiro nos 51
tracks reais (diagnóstico já estabelecido), **falso por construção** nestes 4
casos sintéticos, que existem especificamente para testar decaimento genuíno
de abertura.

Isso reflete diretamente no placar de `TRAIN · synthetic` em
`fix_eval_after.txt` vs. `fix_eval_before.txt`: sequência 11/12 → 7/12 (queda
de 4, exatamente os 4 casos acima).

**Isto não é um bug de implementação** — a correção foi feita exatamente como
especificada, incondicional, sem parâmetro novo. É uma consequência direta e
esperada, uma vez examinada, da regra assumida ("nunca decaimento em t0") ser
falsa para esse subconjunto do corpus sintético. Reportado sem ajuste, como
pedido.

---

## Figuras

`research/labels/diagnostics/figures/`:

- `20180170_before_after.png`
- `20180608_before_after.png`
- `20190325_before_after.png`
- `20191014_before_after.png`

Cada uma: série `z` com os extremos detectados (índice 0 destacado com borda
preta e linha vertical vermelha), barra de fases antes, barra de fases
depois, barra de fases do rótulo manual — mesma paleta de cores de
`labels_core.PHASE_COLORS`.

---

## CHANGELOG

Entrada adicionada em `CHANGELOG.md`, seção `## [Unreleased]` → `### Fixed`
(nova entrada, topo da seção). Versão não alterada — continua `2.0.0`
(`setup.py:6`, conferido, não tocado).

---

## Itens não determinados

Nenhum item novo de "não determinado" nesta rodada além dos já registrados em
`REPORT.md` (rodadas anteriores). O mecanismo do ciclo duplicado (M5/M6) e a
causa da regressão sintética (M7) foram totalmente identificados, não ficaram
como "não determinado".

---

## Estado

**AGUARDANDO APROVAÇÃO EXPLÍCITA. Nenhum commit foi feito.** `git status`
mostra `CHANGELOG.md` e `cyclophaser/determine_periods.py` modificados
(não staged, não commitados) e `research/labels/diagnostics/` como
untracked. Nenhum merge, nenhum push, nenhum PR.
