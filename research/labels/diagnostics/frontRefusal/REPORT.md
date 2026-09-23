# Front "incipient refusal" — stage 1: why the plateau rule refuses, on TRAIN

**Status: diagnostic only, closed. No parameter moved, no file under
`cyclophaser/` or `tests/` was touched.**
Branch `research/incipient-refusal-stage1`, from `develop-v2.1` @ `559dd64`.
Config `research/labels/configs/cyclophaser_params-13.yaml`,
sha256 `c1ab8ce02631f1270b3a633cff2ef43fb5caff64dd492642f56cf5a96e483973`.
Measured in the dedicated `cyclophaser` conda environment against the working
tree (`sys.prefix` = the env, `cyclophaser.__file__` = this repo), not the
installed 2.0.0 wheel. All 47 TRAIN labels verified against their recorded
`series_sha256` — 47/47 match. The TEST split was never loaded into the
detector; `diagnose.py::_assert_train_only` raises before any detection runs.

The problem, restated: under `incipient_method="plateau"` and `params-13` the
detector produces no `incipient` phase on 6 of the 17 real TRAIN series whose
manual label says there is one (`20160587`, `20160735`, `20171179`, `20180628`,
`20181046`, `20202023`). This stage asks only **why**, and whether **any**
threshold move could fix it without regression.

---

## Predictions, copied verbatim from the commissioning brief

> P1: estágio 1 dá PARCIAL ou HETEROGÊNEO (nenhuma causa cobre >= 4/6).
>
> P2: >= 1 das 6 está no conjunto do defeito I.
>
> P3: a separabilidade falha — nenhum limiar recupera >= 3 das 6 sem
>     mexer em algum dos 14.

## Stage 2 gate, copied verbatim — *declared before any change, not applied in this stage*

> G1: >= 3 das 6 com incipient dentro da tolerância.
>
> G2: 0 novas recusas entre os 11; 0 dos 8 dentro da tolerância perdem.
>
> G3: 0 dos 14 ambos-não ganham incipient.
>
> G4: sintéticos (fronteira e sequência) não abaixo do params-13; suíte
>     0 falhas.
>
> Nota: >= 6/17 (linha de base constante) é implicado por G1+G2.

---

## Step 0 — state check

| check | result |
|---|---|
| (a) tip of `develop-v2.1` | `559dd648bc4b951a7840f17e68a0179b6602466d` — **matches** |
| (b) config sha256 | `c1ab8ce0…6e483973` (`cyclophaser_params-13.yaml`) |
| (c) 2×2 on the 33 non-ambiguous real TRAIN series | **11 / 2 / 6 / 14 — reproduced** |
| (c) real incipient boundary | **8 of 17 (47.1%) — reproduced** |
| (d) boundary tolerance the evaluator uses | **per-label `tolerance_idx`**, not a fixed margin — `research/labels/labels_core.py:692` (`if err <= int(rec["tolerance_idx"])`), read from the record at `labels_core.py:373`. On the 17 real TRAIN boundary labels it runs 0–5. |

The evaluator's raw output is in `evaluate_params13_train.txt`. The 2×2 is
recomputed independently in `diagnose.py` from the same detector run and the
derived refusal set is **asserted** equal to front D's C2 list before anything
is printed.

Note on (d): the fixed margin of 6 named in `CLAUDE.md` belongs to the
**synthetic pytest timing test**, which is a different instrument.
`evaluate_against_labels.py` uses the per-label margin and computes no fixed one.

---

## Step 1 — the refusal paths

The plateau rule is self-contained: `find_stages.py:1113–1135` ignores
`phases_order`, the next dz extremum and `threshold_incipient_length`, and runs
**last** in the pipeline (`determine_periods.py:1123`), so nothing downstream can
undo it. Every way it ends without an incipient phase:

| path | site | what decides | against what |
|---|---|---|---|
| **R1** | `find_stages.py:1035` (`hits[0]` is 0) | the first sustained run of `k` samples with `rel >= tau` begins at index 0, i.e. `min(rel[0:k]) >= tau` | `incipient_plateau_tau`, `incipient_plateau_k` |
| **R2** | `find_stages.py:1030–1035` (`hits.size == 0`) | there is **no** run of `k` consecutive samples `>= tau` anywhere: `max_i min(rel[i:i+k]) < tau` | same two |
| **R3** | `find_stages.py:1025–1028` (`k > n`) | the series is shorter than `k` | `incipient_plateau_k` vs series length |
| **R4** | `find_stages.py:986–988` (`amax <= 0`) | the probe signal is flat/non-finite, so `rel` is all zeros; falls through to R2's return | none — degenerate input |

There is one further site that *looks* like a refusal path and is not:
`find_stages.py:1102` fills **every** NaN in `periods` with `'incipient'` before
the plateau rule runs. A boundary of 0 therefore does not by itself mean the
output has no incipient phase — if the frame arrived with a leading run of NaN,
that run is labelled `incipient` and the evaluator counts it. A **refusal** is
`boundary == 0` **and** `periods[0]` non-NaN on arrival.

**Measured on the 35 real TRAIN series: the fill-in never fires** — the leading
NaN run is 0 on all 35, so the plateau boundary *is* the detector's leading
incipient count. Asserted per series (`diagnose.py`, "replay verified against
`get_periods` on all 35"); `separability.py` re-derives the stored boundary from
the stored `rel` on 35/35 as a second check. Every statistic below is read out
of the real run — `find_incipient_period` is wrapped to capture the frame it was
handed, and the package's own `_incipient_plateau_rel` /
`_incipient_plateau_boundary` are then called on that same frame.

**A single path fires.** All 6 refusals are **R1**, as are all 14 agreed-none.
R2, R3 and R4 fire on nothing in the real TRAIN split.

---

## Step 2 — the six series

`head_min` = `min(rel[0:k])`, k = 5, τ = 0.20. Refused ⟺ `head_min >= τ`.
Relative margin = `|head_min − τ| / |τ|`. `rel` is the savgol-smoothed
(window 5, order 3) **raw** vorticity derivative, normalised by its own maximum
— `incipient_plateau_signal="vorticity"`.

| id | path | head_min | τ | rel. margin | N_lab | n | N_lab/n | detected opening | defect I |
|---|---|---|---|---|---|---|---|---|---|
| `20160587` | R1 | 0.207669 | 0.20 | **0.0383** | 26 | 79 | 0.33 | intensification @0 → mature @50 | no |
| `20171179` | R1 | 0.217839 | 0.20 | **0.0892** | 11 | 62 | 0.18 | intensification @0 → mature @36 | no |
| `20202023` | R1 | 0.287663 | 0.20 | 0.4383 | 11 | 78 | 0.14 | intensification @0 → mature @54 | no |
| `20180628` | R1 | 0.412693 | 0.20 | 1.0635 | 9 | 94 | 0.10 | intensification @0 → mature @29 | no |
| `20181046` | R1 | 0.449635 | 0.20 | 1.2482 | 9 | 30 | 0.30 | intensification @0 → mature @19 | no |
| `20160735` | R1 | 0.461140 | 0.20 | 1.3057 | 19 | 259 | 0.07 | intensification @0 → decay @9 | no |

Signs at t0 — raw first difference `z[1]−z[0]` against the filtered one, and
against `dz[0]`, the first sample of the smoothed-derivative array `find_stages`
consumes:

| id | `d_raw[t0]` | `d_filt[t0]` | `dz[t0]` | filt vs raw | dz vs raw |
|---|---|---|---|---|---|
| `20160587` | −1.1417e−06 | −3.0208e−07 | −3.0208e−07 | same | same |
| `20160735` | −2.0560e−06 | −1.6277e−06 | −1.6277e−06 | same | same |
| `20171179` | −1.2560e−06 | −4.1617e−07 | −4.1617e−07 | same | same |
| `20180628` | −2.4152e−06 | −7.4442e−07 | −7.4442e−07 | same | same |
| `20181046` | −2.8195e−06 | −6.9276e−07 | −6.9276e−07 | same | same |
| `20202023` | −3.0270e−06 | −8.2858e−07 | −8.2858e−07 | same | same |

All six agree on sign under both readings, and all six are deepening at t0
(negative, i.e. vorticity going more negative). `dz[t0]` equals `d_filt[t0]`
exactly here, which is expected: `params-13` sets `use_smoothing=False`, so
`dz_dt_smoothed2` at the edge is the forward difference of the filtered curve.

### Defect I

Defect I (`docs/future_work.md` item 8(d)) is `sign(z[1]−z[0])` disagreeing
between the raw and the filtered series under `boundary_padding='edge'`, in
**7 of the 51** real tracks. Re-measured here over the **35 real TRAIN** series:
**6 members** — `20180170` (ambiguous), `20180608`, `20180759`, `20190325`,
`20190397` (all four detector-yes/label-yes), `20191014` (false positive).

**The full list of 7 is not produced here.** The remaining member lies in the
TEST split, which this stage's rules forbid loading. That does not weaken the
intersection: all 6 refusals are TRAIN series and defect I was evaluated on
every one of the 35 real TRAIN series, so the intersection is complete as
computed.

> **Intersection of defect I with the 6 refusals: empty (0 of 6).**

Every defect-I member on TRAIN is a series where the detector *did* produce an
incipient phase. The sign flip is associated with detection, not with refusal.

### Figures

One per series, three panels each — full series, the opening zoom where the
decision is made, and the `rel` probe with τ, the k-window at index 0, and every
sustained run:

`fig_20160587_refusal.png`, `fig_20160735_refusal.png`, `fig_20171179_refusal.png`,
`fig_20180628_refusal.png`, `fig_20181046_refusal.png`, `fig_20202023_refusal.png`.

The figures are regenerated from a fresh detector run and each asserts its
boundary against the value in `refusal.json`, so a figure cannot drift from the
table above.

---

## Step 3 — classification by cause

Categories and the precedence order **M1 > M2 > M3** are the brief's, applied
verbatim. M1 was evaluated under the *more permissive* of the two readings of
"the filtered signal at t0" (it fires if **either** `d_filt[t0]` **or** `dz[t0]`
disagrees in sign with `d_raw[t0]`, or the series is in defect I), so M1's
precedence is not narrowed by that choice. M3's "already intensifies from t0" is
read off the detector's own pre-fill-in label at t0, which is the pipeline's own
statement about the filtered curve.

| id | M1 | M2 | M3 | → cause |
|---|---|---|---|---|
| `20160587` | no | **yes** (0.038) | — | **M2** |
| `20171179` | no | **yes** (0.089) | — | **M2** |
| `20202023` | no | no (0.438) | **yes** | **M3** |
| `20180628` | no | no (1.064) | **yes** | **M3** |
| `20181046` | no | no (1.248) | **yes** | **M3** |
| `20160735` | no | no (1.306) | **yes** | **M3** |

Counts: **M1 = 0, M2 = 2, M3 = 4, M4 = 0.** Largest group 4/6.

> ### Verdict: **COMUM** — M3 (genuine disagreement) covers 4 of 6.

The refusal is, in the majority, the rule working as specified on a series that
has no plateau *by this probe's definition of one*. `20160735` is the extreme:
`rel[0:6]` = 0.46, 0.65, 0.92, **1.00**, 0.84, 0.66 — the fastest deepening in
the whole 259-step record occurs at index 3, inside the window the criterion
reads, while the label puts the incipient phase at `[0, 19)`.

---

## Step 4 — separability

Because a single path (R1) fires and the fill-in never does, the whole
refusal/no-refusal decision on real TRAIN reduces to one inequality per series,
`head_min >= τ`, in which **τ is the only knob**. Raising τ shortens the `above`
mask, breaks the run at index 0 and creates an incipient phase; lowering τ
removes one. `rel` itself does not depend on τ, so the three conditions are
exact arithmetic, not a sweep.

| condition | requirement on τ | set by |
|---|---|---|
| (i) ≥ 3 of the 6 recovered | τ > **0.287663** | 3rd smallest refusal `head_min` (`20202023`) |
| (ii) none of the 14 changes | τ ≤ **0.231229** | smallest TN `head_min` (`20180263`) |
| (iii) none of the 11 becomes refused | τ > **0.177080** | largest TP `head_min` (`20203947`) |

(i) ∧ (iii) requires τ > 0.287663; (ii) requires τ ≤ 0.231229.

> ### Separability: **no range exists**, for the single path R1.

Blocked by four agreed-none series whose `head_min` sits **below** the τ that
(i) needs: `20180263` (0.231229), `20170794` (0.247438), `20150656` (0.249824),
`20150528` (0.250195).

The two populations are not merely close, they **interleave** — ascending
`head_min`, refusals and agreed-nones alternate:

```
0.207669  REFUSAL 20160587      0.368554  TN      20150069
0.217839  REFUSAL 20171179      0.412693  REFUSAL 20180628
0.231229  TN      20180263      0.449635  REFUSAL 20181046
0.247438  TN      20170794      0.461140  REFUSAL 20160735
0.249824  TN      20150656      0.483727  TN      20150532
0.250195  TN      20150528      0.488685  TN      20190879
0.287663  REFUSAL 20202023      0.534281  TN      20201245
0.339388  TN      20170520      0.556185  TN      20207822
0.342176  TN      20191104      0.613920  TN      20180733
                                0.659159  TN      20170342
                                0.716760  TN      20180300
```

**Refusals recoverable before the first TN flips: 2 of 6** (τ ∈ (0.217839,
0.231229] recovers `20160587` and `20171179`).

### Would a recovered series land inside the tolerance?

This **is** calculable without running the detector, for the reason above: the
stored `rel` is τ-independent and the boundary is the leading incipient count
(both asserted, 35/35). So, ignoring (ii) and (iii) **entirely** — recovering all
six at each one's own minimum τ:

| id | N_lab | tol | min τ to recover | N_det at that τ | \|err\| | within tol |
|---|---|---|---|---|---|---|
| `20160587` | 26 | 1 | 0.207669 | 5 | 21 | no |
| `20171179` | 11 | 1 | 0.217839 | 11 | 0 | **yes** |
| `20202023` | 11 | 1 | 0.287663 | 42 | 31 | no |
| `20180628` | 9 | 1 | 0.412693 | 1 | 8 | no |
| `20181046` | 9 | 1 | 0.449635 | 9 | 0 | **yes** |
| `20160735` | 19 | 5 | 0.461140 | 1 | 18 | no |

**2 of 6, at best, and only by giving up conditions (ii) and (iii) completely.**
Under the reachable move — τ ∈ (0.217839, 0.231229], the only one that spares the
14 — exactly one series (`20171179`) recovers *and* lands in tolerance.

Reported outside the verdict, as instructed. False positives:
`20191014` `head_min` = 0.022490, `20191155` = 0.169169. Ambiguous:
`20180170` = 0.160852, `20170760` = 0.458137. (`20191155` at 0.169169 sits below
the largest TP's 0.177080, so no τ that spares the 11 can suppress it either.)

---

## Predictions scored

| | prediction | outcome |
|---|---|---|
| **P1** | stage 1 gives PARCIAL or HETEROGÊNEO (no cause covers ≥ 4/6) | **WRONG** — verdict is COMUM; M3 covers 4/6 |
| **P2** | ≥ 1 of the 6 is in the defect-I set | **WRONG** — the intersection is empty; all 6 defect-I members on TRAIN are series the detector *did* label |
| **P3** | separability fails — no threshold recovers ≥ 3 of the 6 without touching one of the 14 | **CORRECT** — (i) needs τ > 0.287663, (ii) needs τ ≤ 0.231229; four TN series lie in between |

Two of three predictions were wrong in the same direction: the refusals were
expected to be an edge artefact or a near miss, and they are mostly neither.

---

## What this stage establishes, for whoever opens stage 2

1. **τ alone cannot do it.** Not "τ is badly tuned" — the two populations
   interleave on the decisive statistic, so no value of the one knob in the
   inequality separates them. The margin of failure is not small: (i) and (ii)
   are on opposite sides of four series.
2. **Even unconstrained, τ tops out at 2 of 6 within tolerance**, so **G1 is
   unreachable by a τ move**, independently of G2 and G3. A stage 2 that only
   moves `incipient_plateau_tau` can be predicted to fail its own gate before it
   is run.
3. **The remaining free parameters of this path are `incipient_plateau_k` and
   the probe's smoothing** (`incipient_smooth_window`/`_polyorder`), plus
   `incipient_plateau_signal`; `_crossing` changes *which* statistic is decisive
   rather than moving `head_min`. None of these was varied here — `head_min` is a
   function of k, the signal and the probe smoothing, so the arithmetic above
   holds only at k = 5, window 5, signal `vorticity`, crossing `sustained`. Whether any of them separates the
   populations is **unmeasured** and is the obvious next question.
4. **Defect I is not the mechanism** for these six, and the edge-artefact
   hypothesis for incipient refusal should be retired unless re-opened with new
   evidence. Defect I remains open on its own terms (item 8(d)).
5. **The dominant cause is a definitional disagreement**, not a bug: on the 4
   M3 series the raw derivative never drops below 29–46% of that series' own
   maximum rate at any of the first five steps (and starts the window at
   41–68%), while the human label puts an incipient phase there. Any stage 2 has to
   decide whether the probe is measuring the right thing — the labels were drawn
   against a curve, the probe reads the *raw* series' derivative — rather than
   whether its threshold is at the right place.
6. **The `fillna('incipient')` fill-in is inert on real TRAIN** (leading NaN run
   = 0 on all 35). Defect H (item 8(c)) is about that same fill-in; it cannot be
   masking anything in this split.

Nothing here proposes a mechanism or a parameter change, by instruction.
