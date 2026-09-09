> **⚠️ NÃO MERGEAR ESTA BRANCH.** `fix/idx0-boundary-extremum-type` existe
> apenas como registro de uma investigação encerrada sem solução. A alteração
> de código que ela carrega em `cyclophaser/determine_periods.py` (forçar o
> índice 0 a `'peak'` incondicionalmente) está **REFUTADA** — pela medição M7
> (4 casos sintéticos de decaimento genuíno regrediram) e, na variante
> condicional por sinal, pelo contraexemplo `IcDItMD_residual_noisy` no
> portão da rodada 4. Ver a seção "Encerramento da frente A", ao final deste
> arquivo, para o resumo completo e as próximas pistas não perseguidas. Nada
> nesta branch deve ir para `develop-v2.1` ou para qualquer release.

# Rodada 4 — teste do portão (sinal bruta × filtrada) para a regra condicional

Branch: `fix/idx0-boundary-extremum-type` (inalterada desde `FIX_REPORT.md`).
Baseline: `develop-v2.1` @ `887c628`. **Nada commitado.**

`FIX_REPORT.md` (rodada anterior) preservado sem alteração — a refutação da
regra incondicional pela M7 continua registrada lá. Esta rodada só chegou até
a Tarefa 1 (o portão), que **FALHOU**. As Tarefas 2 e 3 não foram executadas,
por instrução explícita do critério de parada.

---

## Metodologia

`git stash push -- CHANGELOG.md cyclophaser/determine_periods.py` antes de
medir (código volta ao baseline `develop-v2.1`, sem a regra incondicional
nem nenhuma outra alteração); `git stash pop` logo depois, restaurando o
working tree exatamente ao estado em que a rodada anterior o deixou (a regra
incondicional ainda no working tree, não commitada — conferido:
`git diff --stat` mostra os mesmos 2 arquivos, mesmas contagens de linha,
antes e depois desta rodada).

`build_synthetic_sign_table.py` roda `process_vorticity` + `get_periods`
(código do pacote, inalterado, com `cyclophaser_params-9.yaml` sem
modificação) sobre os 12 casos sintéticos de `tests/synthetic/cases.py`
(`CASES`, já gerados, série `series` de cada caso = "série bruta"). "Série
filtrada" = `df['z']` = `vorticity.vorticity_smoothed2`, mesma definição já
usada para os reais na Tarefa 6 da rodada 3. `abre_com_decaimento_genuino` =
`segments[0]["type"] == "D"` do caso (construção do gerador, não a saída do
CycloPhaser). `mudou_na_regra_incondicional` foi lido de
`fix_state_before.json`/`fix_state_after.json`, já produzidos na rodada
anterior (comparação completa do array `periods`) — não recalculado aqui.

---

## TAREFA 1 — tabela dos 12 sintéticos

Arquivo: `research/labels/diagnostics/synthetic_sign_table.csv`.

| caso | abre_com_decaimento_genuino | idx0_tipo | sinal bruta | sinal filtrada | concordam | mag bruta | mag filtrada | mudou (regra incond.) |
|---|---|---|---|---|---|---|---|---|
| ItMD_clean | não | valley | 0 | + | não | 0.0 | 3.041×10⁻⁷ | não |
| IcItMD_residual_noisy | não | peak | − | − | sim | 2.152×10⁻⁵ | 2.235×10⁻⁶ | não |
| ItMD_noisy | não | peak | − | − | sim | 7.547×10⁻⁶ | 5.920×10⁻⁶ | não |
| **IcDItMD_noisy** | **sim** | valley | + | + | **sim** | 1.443×10⁻⁵ | 1.407×10⁻⁵ | sim |
| **IcDItMD_residual_noisy** | **sim** | valley | **−** | **+** | **NÃO** | 2.648×10⁻⁶ | 1.935×10⁻⁵ | sim |
| **DItMD_noisy** | **sim** | valley | + | + | **sim** | 9.651×10⁻⁵ | 4.632×10⁻⁵ | sim |
| **DItMD_residual_noisy** | **sim** | valley | + | + | **sim** | 7.750×10⁻⁵ | 4.745×10⁻⁵ | sim |
| IcItMD_ItMD_noisy | não | peak | − | − | sim | 7.355×10⁻⁵ | 9.471×10⁻⁶ | não |
| ItMD_ItMD_noisy | não | peak | − | − | sim | 3.990×10⁻⁶ | 2.568×10⁻⁵ | não |
| IcIt_observational | não | valley | 0 | + | não | 0.0 | 3.151×10⁻⁷ | não |
| quase_ItD | não | peak | − | − | sim | 1.926×10⁻⁶ | 3.120×10⁻⁶ | não |
| IcItMD_residual_clean | não | peak | 0 | − | não | 0.0 | 1.072×10⁻⁶ | não |

### Tabela 2×2 agregada — `idx0_tipo` × `sinais_concordam` (12 sintéticos)

| idx0_tipo \\ concordam | sim | não |
|---|---|---|
| peak | 5 | 1 |
| valley | 3 | 3 |

(Nota: nos casos `_clean`/`_observational` sem ruído a série bruta tem
`sinal_dz_bruta = 0` — `z_unfil[1] == z_unfil[0]` exatamente, plateau inicial
de fato plano — o que conta como discordância contra a filtrada, que nunca é
exatamente 0.)

---

## Os 4 casos com `abre_com_decaimento_genuino=sim`

| caso | sinais_concordam | mag_dz_bruta | mag_dz_filtrada |
|---|---|---|---|
| IcDItMD_noisy | sim | 1.4427×10⁻⁵ | 1.4073×10⁻⁵ |
| **IcDItMD_residual_noisy** | **não** | **2.6479×10⁻⁶** | **1.9350×10⁻⁵** |
| DItMD_noisy | sim | 9.6505×10⁻⁵ | 4.6319×10⁻⁵ |
| DItMD_residual_noisy | sim | 7.7500×10⁻⁵ | 4.7449×10⁻⁵ |

**3 de 4 concordam. 1 de 4 (`IcDItMD_residual_noisy`) discorda**: bruta `-`
(decaimento, correto), filtrada `+` (leitura errada, mesma direção do
artefato de borda dos tracks reais). A magnitude bruta desse caso
(2.648×10⁻⁶) é a MENOR das 4 — quase uma ordem de grandeza abaixo das outras
três (1.44×10⁻⁵, 9.65×10⁻⁵, 7.75×10⁻⁵).

## Casos não ruidosos equivalentes entre os 12

**Não existe.** `CLEAN_CASE_IDS` (`tests/synthetic/cases.py:465-466`,
conferido por execução) = `('ItMD_clean', 'IcIt_observational', 'quase_ItD',
'IcItMD_residual_clean')` — nenhum dos 4 tem `segments[0]["type"] == "D"`
(primeiros segmentos: `Ic`, `Ic`, `It`, `Ic`, respectivamente). Os 4 casos
`_noisy` que abrem com decaimento genuíno (`DItMD_noisy`,
`DItMD_residual_noisy`, `IcDItMD_noisy`, `IcDItMD_residual_noisy`) não têm
nenhuma contraparte sem ruído no conjunto de 12 — todos os 4 usam
`noise_frac=0.02` (`cases.py:164,194,233,268`).

**Pergunta "o ruído inverte o sinal?": não determinado por comparação direta**
(não há par limpo/ruidoso para nenhum dos 4). Há, porém, um padrão medido e
diretamente relevante, já apontado no comentário do próprio arquivo de casos
(`tests/synthetic/cases.py:481-490`, conferido por execução, não só lido): o
segmento D de `DItMD_noisy`/`DItMD_residual_noisy` usa forma `"linear"`
(derivada não nula desde o passo 0 por construção), e o de
`IcDItMD_noisy`/`IcDItMD_residual_noisy` usa forma `"sine"` (derivada
próxima de zero no início, por construção — mesmo mecanismo do "initial
plateau" documentado nessas linhas). Isso é consistente com a magnitude
bruta medida: os dois casos `linear` têm mag_dz_bruta grande (9.65×10⁻⁵,
7.75×10⁻⁵) e concordam; os dois casos `sine` têm mag_dz_bruta muito menor
(1.44×10⁻⁵, 2.65×10⁻⁶) e um deles (o de menor magnitude dos quatro) discorda.
Isto é um padrão medido, não uma inferência sobre causa — não chega a provar
que o ruído é o mecanismo específico da inversão em `IcDItMD_residual_noisy`
(isso exigiria, por exemplo, rodar o mesmo caso com seeds de ruído diferentes
ou com `noise_frac=0`, o que não foi feito aqui — fora do escopo desta
tarefa, que pediu comparação contra equivalentes já existentes entre os 12,
não a geração de casos novos).

---

## CRITÉRIO DE PARADA — PORTÃO FALHOU

Dos 4 casos com `abre_com_decaimento_genuino=sim`, **1 (`IcDItMD_residual_noisy`)
tem `sinais_concordam=não`**. Por instrução explícita: **parar imediatamente.
Nada foi implementado. Tarefas 2 e 3 não foram executadas.**

A hipótese testada — "a discordância de sinal separa artefato de decaimento
genuíno" — está **refutada** por este caso: a regra condicional proposta
(forçar peak só quando os sinais discordam) tomaria `IcDItMD_residual_noisy`
por um artefato de borda e reclassificaria seu índice 0 de `valley` para
`peak`, exatamente o mesmo dano que a M7 da rodada anterior já mediu para a
regra incondicional — só que agora em 1 dos 4 casos genuínos em vez de 4,
porque o portão a mede corretamente e some com aviso em vez de aplicar a
regra às cegas.

---

## Estado

**AGUARDANDO instrução do Danilo. Nenhuma implementação foi tentada nesta
rodada.** Working tree devolvido exatamente ao estado da rodada anterior
(`git stash pop` aplicado; `git diff --stat` idêntico antes/depois desta
rodada: `CHANGELOG.md` +4, `cyclophaser/determine_periods.py` +16, regra
INCONDICIONAL ainda no working tree, não commitada — a mesma que a M7 já
refutou). Nenhum commit, push, merge ou PR.

## Itens não determinados nesta rodada

- Se o ruído (especificamente) é o mecanismo da inversão de sinal em
  `IcDItMD_residual_noisy` — não há par limpo/ruidoso entre os 12 para testar
  isso diretamente; só o padrão de magnitude por forma de segmento (`linear`
  vs `sine`) foi medido, o que é consistente com a hipótese mas não a prova.

---
---

# Encerramento da frente A

Registro final. Nenhuma investigação ou medição nova nesta seção — todos os
números abaixo já foram medidos e reportados em rodadas anteriores
(`REPORT.md`, `FIX_REPORT.md`, e as seções acima deste arquivo), aqui só
consolidados num único lugar de fechamento. Esta branch
(`fix/idx0-boundary-extremum-type`) **não vai ser mergeada**; a alteração de
código que ela carrega está refutada. Fica como registro autoexplicativo de
uma investigação encerrada sem solução.

## Causa mecânica

`argrelextrema` é chamado com comparadores não-estritos (`np.greater_equal` /
`np.less_equal`) e `mode='clip'` (padrão, não sobrescrito):

```
cyclophaser/determine_periods.py:122:    peaks   = argrelextrema(data, np.greater_equal)[0]
cyclophaser/determine_periods.py:123:    valleys = argrelextrema(data, np.less_equal)[0]
```

Com `mode='clip'`, o índice 0 é comparado contra ele mesmo à esquerda, o que
sob um comparador não-estrito sempre passa — o índice 0 é marcado como
extremo em 51/51 tracks reais, e o TIPO dele sai só do sinal de
`z[1]-z[0]` na série filtrada:
- desce → `'peak'` (a intensificação abre o track — 46 casos, comportamento
  correto);
- sobe → `'valley'` (o decaimento abre o ciclo — 5 casos: `20180170`,
  `20180608`, `20190325`, `20191014` no treino; `20206498` no split de teste
  congelado, fora de qualquer critério).

Esse extremo tem proeminência calculada exatamente `0.0` nos 5 casos
`valley` e só sobrevive ao filtro de proeminência/distância por isenção
explícita de borda (`determine_periods.py:181-223`, ver `REPORT.md` e
`code_excerpts.md` para a citação completa). Série bruta e filtrada
discordam sobre o sinal de `z[1]-z[0]` em 7/51 tracks reais, incluindo 5/5
dos casos `valley` (ver `research/labels/diagnostics/idx0_inventory.csv` e
a Tarefa 6 em `REPORT.md`).

## Quatro rotas descartadas

1. **Remover o extremo do índice 0.** Testado e rejeitado antes da rodada 1
   deste registro (contexto herdado, não re-medido nestes arquivos): 40/51
   tracks passam a abrir com decaimento — piora, não conserta.
2. **Guard em `find_decay_period` rejeitando decaimento que começa no índice
   0.** Não existe tratamento de vão inicial em nenhum ponto do pipeline
   (`post_process_periods`, `determine_periods.py:259` no baseline
   `develop-v2.1` @ `887c628` — nesta branch, com a regra refutada aplicada,
   o mesmo trecho está em `determine_periods.py:275`, deslocado pelas 16
   linhas inseridas pela correção que este registro documenta;
   `find_residual_period`, `find_stages.py:621-628`). Um guard aqui deixaria
   um buraco de até 52% da série sem fase atribuída (ver `REPORT.md`,
   medição de `decai_fracao_serie` em `idx0_inventory.csv`).
3. **Forçar `'peak'` incondicionalmente** (a alteração que está de fato no
   working tree desta branch, `determine_periods.py:125-138`).
   Mecanicamente limpa nos reais: 46/46 no-op nos tracks `peak`, fronteira da
   incipiente idêntica campo a campo (8/17 e 14/16), 3/3 de acerto na
   primeira fase não-incipiente dos 4 tracks de treino afetados. **Mas**: os
   4 casos sintéticos que abrem com decaimento genuíno por construção
   (`DItMD_noisy`, `DItMD_residual_noisy`, `IcDItMD_noisy`,
   `IcDItMD_residual_noisy`) regrediram de bate perfeito para não-bate — a
   medição M7 (ver seção correspondente em `FIX_REPORT.md`). Refutada.
4. **Condicionar a rota 3 pela discordância de sinal bruta/filtrada.**
   Testada no portão desta rodada (Tarefa 1, acima) antes de qualquer
   implementação: refutada pelo contraexemplo `IcDItMD_residual_noisy`, que
   abre com decaimento genuíno E tem sinais discordantes
   (`sinal_dz_bruta='-'`, `sinal_dz_filtrada='+'`) — a mesma assinatura que a
   regra usaria para identificar (erradamente, neste caso) um artefato de
   borda. Nunca chegou a ser implementada.

## Os 12 sintéticos não representam os reais na borda em t0

Tabela 2×2 `idx0_tipo` × `sinais_concordam`:

- **Reais** (51 tracks, `idx0_inventory.csv`): `valley` × discorda = **5**,
  `valley` × concorda = **0**. Separação limpa.
- **Sintéticos** (12 casos, `synthetic_sign_table.csv`, esta rodada):
  `valley` × discorda = **3**, `valley` × concorda = **3**. Sem separação.

Portanto: **um resultado sobre o comportamento de borda em t0 medido só nos
12 sintéticos não é evidência sobre os tracks reais, e vice-versa** — os dois
conjuntos têm estruturas de sinal diferentes nessa borda. Isso vale para
qualquer frente futura que reabra o problema do índice 0.

## A frente A não bloqueia o release da v2.1

A fronteira da fase incipiente é **idêntica**, campo a campo, com e sem a
correção (`fix_eval_before.txt` vs. `fix_eval_after.txt`, `TRAIN · real`:
17 rótulos de fronteira, 8 acertos dentro da margem, MAE 4.82, pior caso 26;
recusa 16/14 — todos os números idênticos). Isso não é coincidência: o
`boundary` da fase incipiente depende só de `dz`/`z_unfil` e dos parâmetros
de config, nunca do mapa de fases já atribuído
(`find_stages.py:969-978`) — matematicamente invariante à mudança do tipo do
extremo no índice 0 em `z_peaks_valleys`. O problema do índice 0 afeta a
fase de decaimento/intensificação de abertura em 5/51 tracks reais (4 no
treino), não a fronteira da incipiente, que é o que a v2.1 está fechando.

## Pista não perseguida: magnitude em vez de sinal

O sintético que refutou a rota 4 (`IcDItMD_residual_noisy`) tem
`|z[1]-z[0]|` bruto = 2.6×10⁻⁶ contra filtrado = 1.9×10⁻⁵ — o filtro
**amplifica** essa diferença em ~7×. Os três casos de decaimento genuíno que
passaram no portão têm magnitude bruta grande e o filtro **atenua** (não
amplifica) a diferença (`synthetic_sign_table.csv`). Uma regra baseada em
"o filtro amplificou ou atenuou a magnitude de `z[1]-z[0]`" não foi
perseguida nesta investigação porque exigiria um limiar numérico de
amplificação/atenuação — ou seja, um parâmetro novo, fora do que as rodadas
anteriores autorizaram implementar (nenhum parâmetro novo, nenhuma opção de
config). Fica registrada como pista para quem reabrir a frente A.

## Defeitos abertos, fora do escopo desta frente

- **Defeito H**: `find_incipient_period` sobrescreve `df.iloc[:boundary]`
  incondicionalmente:

  ```
  cyclophaser/find_stages.py:982:        df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'
  ```

  Isso mascara um mapa de fases errado atrás de uma saída aparentemente
  correta — caso observado: `20180608`, onde o `boundary` da incipiente
  consome o bloco de decaimento espúrio inteiro e a saída final aparenta
  estar correta (abre com `intensification`) mesmo com o índice 0
  classificado errado por baixo. Ver `REPORT.md`, seção Tarefa 5.

- **Defeito I**: o filtro de Lanczos com `boundary_padding='edge'` inverte o
  sinal da primeira diferença finita (`z[1]-z[0]`) em relação à série bruta
  em 7 dos 51 tracks reais (`idx0_inventory.csv`, Tarefa 6 em `REPORT.md`).
  É a causa de fundo por trás da divergência de sinal que motivou (e depois
  refutou) as rotas 3 e 4 acima.

## Estado final desta branch

Registro fechado. `cyclophaser/determine_periods.py` carrega a alteração
refutada; `CHANGELOG.md` foi revertido para ficar idêntico ao de
`develop-v2.1` @ `887c628` (a correção descrita nele não vai existir).
Committed nesta branch como registro; **não mergear, não abrir PR**.
