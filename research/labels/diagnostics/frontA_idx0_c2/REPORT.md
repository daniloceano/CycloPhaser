# Front A / item 28 — conditional reclassification of the extremum at index 0 (rule C2), stage 1

**Measurement only. Nothing under `cyclophaser/` or `tests/` was touched.** The
one behavioural variant measured here — index 0 forced from `valley` to `peak`,
commit `6060c6d` — lives as a local copy in `common.py` and is injected by an
explicit replay of `get_periods`' body.

Branch `frontA-idx0-c2`, cut from `develop-v2.1` @ `c714451` (working tree
clean). Config `research/labels/configs/cyclophaser_params-13.yaml`,
sha256 `c1ab8ce02631f1270b3a633cff2ef43fb5caff64dd492642f56cf5a96e483973` —
the signature filter dropped **no** key from `phase_params` (21 of 21 accepted).

Environment: the dedicated `cyclophaser` conda env, never base.
`sys.prefix` = `/Users/danilocoutodesouza/miniconda3/envs/cyclophaser`
(python 3.12.14, numpy 2.5.3, scipy 1.18.0, pandas 3.0.5).
`cyclophaser.__file__` = this checkout, asserted in-process before every script
body (`common.provenance`), with the sha256 of the two modules actually loaded:

| module | sha256 |
|---|---|
| `cyclophaser/determine_periods.py` | `2c6eaae8494a54e972fef087076a5df677f46bad4ca5d4a219ce97aee77b1cb9` |
| `cyclophaser/find_stages.py` | `a0c65358c841a05e9d5c5ba958bb75cd9ff6c5c4c02002affc7aecbc8ec1c9ea` |

No worktree was used, so `run_in_worktree.py` was not needed; the equivalent
in-process assertion runs anyway.

**Replay fidelity.** Every measurement is taken from a replay of `get_periods`'
body, not from the function itself, so the intermediate states can be
snapshotted. The unforced replay was compared with the real `get_periods`
field by field on **63 of 63** series and matched on all of them. The H step of
M4 is re-executed from the package's own `_incipient_plateau_rel` /
`_incipient_plateau_boundary` and asserted equal to the replay's final column.

**TEST split.** All 63 series were run through the detector, which includes the
16 held-out tracks — the census is mechanical and reads no label. No TEST label
was read, compared or printed anywhere in this front. `20206498` appears with
its sequences only, as the brief directs.

---

## Headline

**C2 as specified does not do the job it was commissioned for, and it is not a
threshold problem.**

- It fires on **4 of 63** series, not the predicted 5.
- Of the 5 tracks whose index 0 is typed `valley` and that motivated the front,
  C2 reaches **3**; the two it misses (`20180170`, `20180608`) are missed
  because their E1 is a `peak`, i.e. by the rule's own definition.
- On the two train-split series where C2 fires, the resulting sequence is
  **still wrong** against the label — 0 sequence matches gained.
- The one real track where forcing index 0 to `peak` *does* buy a sequence
  match (`20180170`) is exactly one C2 does **not** fire on.
- The `peak->valley` branch, predicted dead, fires on one train track
  (`20190639`): the sequence gains a `decay` block over `[13, 26)` and stops
  matching the label. **The maintainer ruled this change acceptable on
  2026-09-23** — see "Maintainer ruling" below — so it is a reclassification,
  not a loss.

Net effect of C2 at params-13 on the train split, after that ruling: **0 gained
by the sequence metric, 0 lost.** C2 is harmless and does not reach the case
that motivated the front.

---

## Maintainer ruling — `20190639` (2026-09-23)

Danilo inspected the figure and **accepted C2's change on this track**: with the
`decay` arriving after the `incipient`, the opening was ambiguous, and the new
reading is a reclassification rather than a regression.

What the change actually is:

| | blocks |
|---|---|
| label | `incipient[0,25)` `intensification[25,81)` `mature[81,106)` `decay[106,180)` |
| base | `incipient[0,13)` `intensification[13,88)` `mature[88,105)` `decay[105,180)` |
| C2 | `incipient[0,13)` **`decay[13,26)`** `intensification[26,88)` `mature[88,105)` `decay[105,180)` |

`mature` and the final `decay` do not move. The `intensification` start moves
from **13 (error 12, outside the label's ±5)** to **26 (error 1, inside it)**.
What C2 adds is a 13-step `decay` over `[13, 26)`, a stretch where the vorticity
does weaken before the real deepening and which the label calls `incipient`.
H's `boundary` is 13 with and without C2, so H covers `[0, 13)` and leaves
`[13, 26)` exposed.

**Mechanism, and why this firing is not about index 0 at all.** The z candidates
before the prominence filter are `peak@0`, `valley@9`, `peak@25`; under
`prominence_relative = 0.3` the `valley@9` is removed, leaving two consecutive
peaks. So on this track C2's `peak->valley` branch keys on *a valley the
prominence filter deleted*, not on a mistyped index 0. Measured, not inferred
(`fig_20190639.py`).

### Two consequences

1. **The verdict on the rule does not change.** C2 still converts 0 of its
   `valley->peak` firings into a match and still misses `20180170`, the one
   track where the correction is worth a sequence match. The ruling removes the
   loss, not the absence of a gain.
2. **The sequence metric will keep calling this track a mismatch.**
   `manual_labels.yaml` says `incipient[0,25)`, and `score_phase_sequences`
   refuses to pair any boundary once an extra phase appears — so any future gate
   scoring C2 (or C1, if it moves this track the same way) reads `20190639` as a
   loss, against the maintainer's own judgement. Either the label is revisited
   or a gate on this front must state that this track is scored against a label
   the maintainer has superseded. **`manual_labels.yaml` was not touched** — it
   is the maintainer's file and relabelling is his call.

Figure: `outputs/fig_20190639_c2.png`. Blocks and per-boundary errors:
`outputs/fig_20190639_blocks.csv`, `outputs/fig_20190639_boundaries.csv`.

---

## M1 — how the prominence of index 0 is computed

**The package does not compute one.** `_refine_extrema`
(`cyclophaser/determine_periods.py:180-181`) splits the candidates into

```python
boundary = {i for i in (0, N - 1) if i in set(candidates)}
interior = np.array([i for i in candidates if i not in boundary])
```

and only `interior` is ever passed to `peak_prominences`
(`determine_periods.py:188`). Index 0 is then re-added unconditionally in
the returned union (`determine_periods.py:212`). No prominence value for index 0
exists anywhere in the pipeline, and no threshold is ever applied to it.

The number Front A reported as "prominence 0.0" is what
`peak_prominences(signed, [0])` returns when asked anyway. Measured on all 63
series, in both sign conventions:

| quantity | result |
|---|---|
| `peak_prominences(z, [0])` == 0.0 | **63 / 63** |
| `peak_prominences(-z, [0])` == 0.0 | **63 / 63** |
| largest absolute value seen | 0.0 |

This is structural, not empirical: scipy's base search cannot cross the array
edge, so for index 0 the left base **is** index 0, the height above it is 0, and
the prominence is 0.0 for any data whatsoever. It is confirmed here as a
measured fact on the 63 series *and* as a property of the algorithm.

**Correction this forces onto the record:** a prominence of 0.0 at index 0 is
**not** evidence that the extremum is an artefact. It is what the formula
returns at a boundary, for a real extremum and a spurious one alike, and the
package never reads it. Any argument of the form "index 0's prominence is 0.0,
therefore it is spurious" is void — including the one in Front A's original
write-up. Every column in `outputs/m2_c2_table.csv` named `prom_idx0_*` is a
re-derivation of that constant, kept only to close the question.

Outputs: `outputs/m2_c2_table.csv`, `outputs/m1_m2_census.log`.

---

## M2 — where C2 would fire

For each series: the type of index 0 in the **final** z extremum list — the
column `find_stages` consumes, after the prominence filter and after the
boundary exception — the next extremum E1 in that same list, and the C2
decision, exactly as the brief defines it.

Full 63-row table: **`outputs/m2_c2_table.csv`**.

Index 0 is in the final list on 63 of 63 series (no boundary plateau was ever
collapsed away from it, and no series has a tie that puts it in both
populations). Its type:

| type of index 0 | series |
|---|---|
| `peak` | 52 |
| `valley` | 11 |

The C2 decision:

| branch | series |
|---|---|
| alternating types → does not fire | 52 |
| `peak`/`peak`, E1 not strictly higher → does not fire | 7 |
| **fires, `valley->peak`** | **3** |
| **fires, `peak->valley`** | **1** |
| E1 does not exist / index 0 absent | 0 |

The 4 firings:

| id | source | split | idx0 | E1 | E1 type | z[0] | z[E1] | z[E1]−z[0] | branch |
|---|---|---|---|---|---|---|---|---|---|
| 20190325 | real | train | valley | 64 | valley | −3.0e−06 | −2.68e−05 | −2.4e−05 | valley→peak |
| 20191014 | real | train | valley | 52 | valley | −2.0e−06 | −4.91e−05 | −4.7e−05 | valley→peak |
| 20206498 | real | **test** | valley | 40 | valley | −1.6e−05 | −4.29e−05 | −2.7e−05 | valley→peak |
| 20190639 | real | train | peak | 25 | peak | −9.0e−06 | +6.90e−07 | +1.0e−05 | **peak→valley** |

The 5 Front A targets:

| id | idx0 | E1 | E1 type | C2 fires | why |
|---|---|---|---|---|---|
| 20180170 | valley | 21 | **peak** | **no** | alternating types |
| 20180608 | valley | 10 | **peak** | **no** | alternating types |
| 20190325 | valley | 64 | valley | yes | valley→peak |
| 20191014 | valley | 52 | valley | yes | valley→peak |
| 20206498 | valley | 40 | valley | yes | valley→peak |

All 12 synthetic series: **C2 fires on none of them**. The four genuine-decay
cases (`DItMD_noisy`, `DItMD_residual_noisy`, `IcDItMD_noisy`,
`IcDItMD_residual_noisy`) all have index 0 typed `valley` with E1 a `peak`, so
the rule declines on exactly the population it was designed to protect.

### Two facts the brief's problem statement did not anticipate

1. **Under params-13 only 4 of the 5 targets still open with a spurious decay.**
   `20180608`'s final sequence is `incipient>intensification>mature>decay` — the
   artefact is present inside the pipeline but invisible in the output. M4
   explains why.
2. **A leading decay does not require a `valley` at index 0.** `20170756` (test
   split) opens with decay while its index 0 is typed `peak`. Index-0 typing is
   one route to the symptom, not the only one.

---

## M3 — forcing index 0 to `peak` under params-13

The `6060c6d` variant re-measured at the current tip under params-13, on the 5
targets and the 4 genuine-decay synthetics. Where C2 fires on `valley->peak`,
these rows **are** what C2 would produce.

Two channels were measured, because `6060c6d` patched `find_peaks_valleys`
itself and so hit z, dz and dz2, while C2 is defined on the z list alone. The
two are **identical on 9 of 9** series: under params-13
(`incipient_method: plateau`) nothing reads `dz_peaks_valleys`, so the
distinction does not exist at this config. Measured, not assumed.

| id / case | label | base (params-13) | forced | changed | seq. match base → forced |
|---|---|---|---|---|---|
| 20180170 | Ic>It>M>D | Ic>**D**>It>M>D | Ic>It>M>D | yes | ✗ → **✓** |
| 20180608 | Ic>It>M>D | Ic>It>M>D | Ic>It>M>D | **no** | ✓ → ✓ |
| 20190325 | Ic>It>M>D | Ic>**D**>It>M>D | Ic>It>**D**>It>M>D | yes | ✗ → ✗ |
| 20191014 | It>M>D | Ic>**D**>It>D | **Ic**>It>M>D>**R** | yes | ✗ → ✗ |
| 20206498 | *test — not read* | Ic>D>It>D | Ic>It>D>It>D | yes | — |
| DItMD_noisy | D>It>M>D | D>It>M>D | **It>M>D** | yes | ✓ → ✗ |
| DItMD_residual_noisy | D>It>M>D>R | D>It>M>D>R | **It>M>D>R** | yes | ✓ → ✗ |
| IcDItMD_noisy | Ic>D>It>M>D | Ic>D>It>M>D | **Ic>It>M>D** | yes | ✓ → ✗ |
| IcDItMD_residual_noisy | Ic>D>It>M>D>R | Ic>D>It>M>D>R | **Ic>It>M>D>R** | yes | ✓ → ✗ |

Scored series (8; `20206498` excluded): sequence match **5/8 → 2/8**.

Two readings matter:

- **Front A's M7 refutation reproduces at params-13.** All four genuine-decay
  synthetics currently match their label sequence and all four regress when
  index 0 is forced. This is the damage C2's conditional is meant to avoid —
  and it does avoid it, since it fires on none of them.
- **The only gain is on a track C2 cannot reach.** `20180170` goes from mismatch
  to match, and C2 does not fire there. Note also that all three of that track's
  scoreable boundaries are flagged `unsure` by the labeller (the
  `intensification` start is off by 12 steps), so the gain is a *sequence* match
  with no boundary evidence behind it.

Figure: `outputs/m3_force_peak.png` (per series: lower band = base, upper band =
forced). Table: `outputs/m3_force_peak.csv`. Log: `outputs/m3_force_peak.log`.

### Addendum — what the `peak->valley` branch does where it fires

Predicted dead (P4), it fires on `20190639` (train). The mirror operation —
index 0 forced to `valley`, which no version of the package has ever contained —
was measured on that track:

| | sequence | matches label sequence |
|---|---|---|
| label | `incipient>intensification>mature>decay` | — |
| base | `incipient>intensification>mature>decay` | **yes** |
| C2 `peak->valley` applied | `incipient>`**`decay`**`>intensification>mature>decay` | **no** |

C2's second branch manufactures precisely the artefact the front exists to
remove. Table: `outputs/m2b_peak_to_valley.csv`.

---

## M4 — 20180608: does the incipient overwrite (H) mask the effect?

H is `find_stages.py:1134`, inside the `incipient_method="plateau"` branch:

```python
if boundary > 0:
    df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'
```

It overwrites `[0, boundary)` with `incipient` **after** every other phase has
been assigned, so a spurious `decay` block opening at index 0 reaches the output
only if it extends past `boundary`.

On `20180608`, `boundary = 38` in both variants:

| | sequence **before** H | first block before H | sequence **after** H (= final) |
|---|---|---|---|
| base | `decay>intensification>mature>decay` | `decay` × **11** | `incipient>intensification>mature>decay` |
| index 0 forced to `peak` | `intensification>mature>decay` | `intensification` × 62 | `incipient>intensification>mature>decay` |

**H masks it completely.** The spurious `decay` block is 11 steps long and H
overwrites the first 38, so the artefact is fully present inside the pipeline
and fully invisible in the output. The two final outputs are identical step by
step: at params-13 the Front A variant is a **no-op** on `20180608`.

This is why the brief's "5 tracks open with spurious decay" is a params-9
statement. At params-13 the count is 4, and the fifth is masked rather than
fixed — the mechanical defect is untouched. Any future config that shortens
`boundary` on this track re-exposes it.

Figure: `outputs/m4_20180608_H.png` (four panels: before/after H × base/forced).
Step-by-step head of the series: `outputs/m4_20180608_head.csv`. Summary:
`outputs/m4_20180608_H.csv`.

---

## M5 — does `boundary` depend on the phase map?

**No.** Two independent checks, both clean.

*Static.* The plateau branch computes the boundary at
`find_stages.py:1121-1130`:

```python
rel      = _incipient_plateau_rel(df, signal, smooth_window, smooth_polyorder)
boundary = _incipient_plateau_boundary(rel, tau, crossing, k)
```

- `_incipient_plateau_rel` (`find_stages.py:951-989`) — the only string
  subscripts on the frame in its whole body are `'dz'` and `'z_unfil'`
  (`find_stages.py:976` and `:979`). It never reads `'periods'`.
- `_incipient_plateau_boundary` (`find_stages.py:992-1035`) — no frame access at
  all; a pure function of `(rel, tau, crossing, k)`.
- `'periods'` first appears in that branch at `find_stages.py:1134`, the
  **write**. `'dz_peaks_valleys'` is read only by the geometric branch
  (`find_stages.py:1155`, `:1164`), which params-13 does not take.

*Measured.* `boundary` recomputed on all 63 series with and without index 0
forced — forcing changes `z_peaks_valleys` and therefore the phase map:
**identical on 63/63**. Table: `outputs/m5_boundary_independence.csv`.

So the incipient boundary is upstream of everything this front touches: no
reclassification of index 0 can move it, and H's masking power is fixed
independently of the artefact it masks.

---

## Declared predictions

| | prediction | measured | verdict |
|---|---|---|---|
| **P1** | prominence of index 0 = 0.0 by construction, 63/63 | 63/63 in both sign conventions — and the package computes none at all | **CONFIRMED** (with the correction above) |
| **P2** | on the 4 genuine-decay synthetics E1 = `peak`, C2 does not fire (4/4) | 4/4 E1 = `peak`, 0/4 fire | **CONFIRMED** |
| **P3** | on the 5 targets E1 = deeper `valley`, C2 fires (5/5) | **3/5**; `20180170` and `20180608` have E1 = `peak` | **REFUTED** |
| **P4** | C2 fires on exactly 5/63; `peak->valley` on 0/63 | **4/63**; `peak->valley` on **1/63** (`20190639`) | **REFUTED** (both clauses) |
| **P5** | `boundary` does not depend on the phase map | static + 63/63 measured | **CONFIRMED** |

The confidence ordering inside P3 was also wrong in its detail: the two misses
are `20180170` (not flagged as doubtful) and `20180608` (flagged), while
`20191014` (flagged) does fire.

---

## Which pre-declared retreat applies

Neither, cleanly. Reported, not executed.

- **(a) — "any of the 4 synthetics fires → go to C1".** Does **not** apply:
  0 of 4 fire. C2's conditional protects the genuine-decay population exactly as
  designed.
- **(e) — "FAIL only in the `peak->valley` branch → next stage tests
  unidirectional C2".** Does **not** apply, and after the maintainer ruling it
  applies even less than it did when this section was first written. (e)
  presupposes that the `peak->valley` branch is where the harm is; the one
  firing of that branch was inspected and **accepted**, so there is no harm to
  retreat from. Dropping the branch would drop the only change C2 makes that the
  maintainer endorses, while the surviving `valley->peak` branch fires on 2
  scoreable train series and converts **neither** into a sequence match.
  Unidirectional C2 is therefore a strictly worse version of a rule that already
  has no measured benefit.

The reason is visible in M2 and is not a threshold: C2 discriminates on the
**type of E1**, and the type of E1 does not separate the spurious openings from
the genuine ones. On the 5 targets it splits 3/2 with the wrong member on each
side — it misses the one track (`20180170`) where the correction is worth a
sequence match, and reaches two where the correction is not enough.

That is the argument for **C1** (relative depth `D1 = (z_max − z[0]) / (z_max −
z_min)`), whose discriminant is the *magnitude* of the opening excursion rather
than the type of the next extremum — and it is exactly the "magnitude lead"
Front A's closing report recorded and did not pursue. C1 is reached here by
measurement, not by rule (a). Note `20180608` warns that a fix measured on the
final output alone will look like a no-op there: any future gate on this front
should be read **before** H, not after it.

**C3** (relative size of the rise to the next peak) remains recorded only.

---

# Stage 2 — rule C2' as default behaviour (`reclassify_index0`)

**This stage changes the package.** Branch `frontA-idx0-c2`, continuing from
stage 1. Gate: **PASS** — Q1 to Q8 confirmed, suite green.

## What was implemented

`reclassify_index0`, a bool on `get_periods` and `determine_periods`,
**default True**. On the final z extremum list, with E1 the next extremum after
index 0 **of either type**: a `valley` at index 0 with `z[E1] < z[0]` strictly
becomes a `peak`; a `peak` with `z[E1] > z[0]` strictly becomes a `valley`; a
tie or a missing E1 changes nothing. Only index 0 is touched.

Dropping C2's same-type restriction is the whole point: C2 reached 3 of the 5
motivating tracks and missed `20180170`, the one worth a sequence match, purely
because its E1 is a peak (stage 1, M2).

| where | what |
|---|---|
| `determine_periods.py` | `_reclassify_index0` (the rule), the `reclassify_index0` keyword on `find_peaks_valleys` (**default False**), `get_periods` and `determine_periods` (**default True**) |
| | applied to `z` only — the two derivative calls pass `reclassify_index0=False` explicitly |
| `research/labels/configs/cyclophaser_params-14.yaml` | params-13 + `reclassify_index0: true` |
| `tools/calibration_app/app.py` | sidebar checkbox (section 3, on by default), YAML import/export, `_PARAM_WIDGET_KEYS` |
| `tools/calibration_app/layer_inspector.py` | `build_working_frame` and `mature_lens` follow the pipeline |
| `tests/test_reclassify_index0.py` | 14 tests |
| `CHANGELOG.md` | change-of-default entry |

**The default asymmetry is deliberate.** `find_peaks_valleys` keeps the old
behaviour unless asked; the two pipeline entry points apply the rule. The rule
is a statement about the vorticity series a life cycle is read from, not a
property of extremum detection in general.

## The gate

Measured with `stage2_reference.py`, which fingerprints the `periods` column
per series (sha256, not a sequence summary) for a **named** cyclophaser tree and
hard-asserts in-process which package it imported. Three runs: `develop-v2.1 @
c714451` in a pinned `git worktree`, and the working tree with the flag forced
off and on.

| tree | `determine_periods.py` sha256 |
|---|---|
| c714451 (reference) | `2c6eaae8494a54e972fef087076a5df677f46bad4ca5d4a219ce97aee77b1cb9` |
| working tree | `5e11f622e264d66f5f84973c9bf59cc10fd6820c63f4e8c433c4ceacef8f3442` |

| | prediction | measured | verdict |
|---|---|---|---|
| **Q1** | `False` == c714451, 63/63 | 63/63 identical `periods` sha256 | **CONFIRMED** |
| **Q2** | fires on exactly 5/63; the other 58 byte-identical | fires on exactly those 5; 58 byte-identical; **0 of 12 synthetics** | **CONFIRMED** |
| **Q3** | `20180170` → `Ic>It>M>D`, matches the label | exactly that, and it matches | **CONFIRMED** |
| **Q4** | `20190325` → `Ic>It>D>It>M>D` | exactly that | **CONFIRMED** |
| **Q5** | `20191014` → `Ic>It>M>D>R` | exactly that | **CONFIRMED** |
| **Q6** | `20190639` blocks exactly as ruled | `incipient[0,13) decay[13,26) intensification[26,88) mature[88,105) decay[105,180)` | **CONFIRMED** |
| **Q7** | `20180608` unchanged, before and after H | final output identical; before H, `decay[0,11) intensification[11,62) mature[62,71) decay[71,117)` **both ways**; boundary 38 both ways | **CONFIRMED** |
| **Q8** | incipient `boundary` identical, 63/63 | 63/63 | **CONFIRMED** |
| **Q9** | suite green | see below | **CONFIRMED** |

Q7 is worth reading twice: on `20180608` the rule does **not** fire — its E1 is
a peak at `z[10] = -3.0e-5`, higher than `z[0] = -3.3e-5`, so neither branch
applies — and the opening `decay[0,11)` survives inside the pipeline exactly as
stage 1 found it. H masks it, as before. **The one target the front never
reached is still unreached**; the change is that this is now visible in a
measurement rather than hidden behind H.

`20206498` is in the frozen TEST split: its sequence is reported
(`Ic>D>It>D` → `Ic>It>D>It>D`) and its label was not read.

Table (63 rows): `outputs/stage2_table.csv`. Figures for the 5 changed series:
`outputs/stage2_changed_series.png`. Log: `outputs/stage2_gate.log`.

## Sequence-match count, and the exception

Over the 62 label-carrying series: **42 → 42**. That counter charges
`20190639` as a loss and credits `20180170` as a gain. Per Danilo's ruling of
2026-09-23, `20190639` is scored by its blocks (Q6) and not by
`score_phase_sequences`, which refuses to pair boundaries once an extra phase
appears. Read that way the change is **+1 sequence match and one accepted
reclassification**. `manual_labels.yaml` was not edited.

## The CI reference baselines did not need updating — and why

The brief provided for a separate commit updating them. It was not needed, and
the reason is a measurement, not the absence of a failure: under the **package's
own defaults** — where `prominence` and `prominence_relative` are both None —
`determine_periods(series)` is **identical with and without the rule on all 64**
series tried (51 calibration tracks, 12 synthetic series, the packaged example
file). `outputs/stage2_defaults_check.csv`.

That is not a coincidence, and it is the most useful thing this stage learned:

**Rule C2' can only fire where something has already removed the extremum
between index 0 and E1.** Raw `argrelextrema` output alternates, so the
extremum right after a valley at index 0 is a peak the series rose to, which
cannot lie below index 0 — and symmetrically for a peak. What breaks the
alternation is the prominence filter. On `20190639` it deletes the `valley@9`
and leaves two consecutive peaks; on `20180170` it deletes the early bumps and
leaves a peak at index 21 already below `z[0]`.

So: **the new default bites only when a prominence filter is in use.** Every
CI baseline runs without one, which is why they are untouched, and any user
running package defaults sees no change at all. This also sets the scope of the
change honestly — it is a change to the *calibrated* configuration, not to the
out-of-the-box one.

Measured on this corpus (0 of 64 under no filtering) and argued from the
alternation property; not proved in general — a plateau collapse is a second way
to break alternation and was not exercised here.

## Suite

Run in the dedicated `cyclophaser` env, `-m "not browser"`. The only failures
the change produced anywhere in the suite were 6 in
`test_mature_lens_accepted_extrema_are_the_detector_s`, and they were correct
failures: the Inspector's lens was still reading index 0 the old way while
`get_periods` had moved. Fixed by having `mature_lens` apply the rule to its
ACCEPTED set (the pipeline's) and by excluding index 0 from the REJECTED sets,
which keeps "rejected" meaning "rejected by prominence" now that a boundary
extremum's kind can change. Browser tests are not run here, by standing rule.

## Deviations from the brief, declared

1. **No separate CI-hash commit** (brief item 5): nothing to update. Measured
   above.
2. **`params-14.yaml` differs from params-13 in two lines, not one**: the new
   key and `metadata.timestamp` (2026-09-22 → 2026-09-23). No detector
   parameter differs. A config's timestamp records when it was made, and
   copying a date the file does not have would be the worse error.

---

## Files

| file | what |
|---|---|
| `common.py` | provenance assert, the local `6060c6d` copy (+ its mirror), the verified replay |
| `m1_m2_census.py` | M1 + M2 over 63 series |
| `m3_force_peak.py` | M3 over the 9 series, both force channels, + figure |
| `m2b_peak_to_valley.py` | M2 addendum: the `peak->valley` branch on `20190639` |
| `m4_20180608_H.py` | M4: before/after H, base and forced, + figure |
| `m5_boundary_independence.py` | M5: static + measured |
| `fig_20190639.py` | the accepted reclassification, drawn |
| **stage 2** | |
| `stage2_reference.py` | per-series `periods` fingerprint for a NAMED tree (worktree-safe) |
| `stage2_gate.py` | Q1-Q8, the 63-row table, the figures |
| `stage2_defaults_check.py` | the rule under the package's own defaults (64/64 unchanged) |
| `outputs/` | every table, log and figure above |

**Stage 1's scripts are a frozen record — do not re-run them against the new
default.** Their replay builds the extrema itself, through `find_peaks_valleys`
with no flag (so: the rule off), and then asserts the replay equals
`get_periods`. `get_periods` now applies the rule, so on the 5 series where it
fires that assertion is now FALSE — verified: `replay_ok=False` for `20180170`
and `20190639`, `True` for a series the rule leaves alone. That is the check
doing its job, not a defect, but it means their `replay_ok` no longer reads as
"this replay is the pipeline" unless `reclassify_index0=False` is passed
through. `stage2_gate.py` is the one to extend; its own replay (Q7) passes the
flag explicitly and was verified against `get_periods` both ways.
