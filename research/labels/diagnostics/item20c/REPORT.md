# Front 20(c), stage 1 — proportional duration floor for `mature`

**Verdict: FAIL (premise).** The front closes here. No line of `cyclophaser/`
was touched.

The prediction registered before the measurement — *FAIL of premise, because in
20205386 anchor A probably lands on a spurious block* — is confirmed, and by
exactly that mechanism. It is not adjusted here.

---

## 1. What was measured and how

`item20c_measure.py` replays the detector under
`research/labels/configs/cyclophaser_params-12.yaml` on the **train split only**
(47 series: 35 real + 12 synthetic; `split.yaml`, seed 20260905). The test split
is never read.

Attributing a final `mature` block to the `z_valley` that generated it is not
something `get_periods` reports, so the pipeline is replayed a second time with
the real package functions, pausing after `find_decay_period` to record the
window `find_mature_stage` builds around each eligible valley via the real
`_amplitude_mature_bounds`. The replay is then **verified against the
single-call `get_periods` output**: the two `periods` columns are identical on
**47/47 series**, so the attribution rests on the detector's own arithmetic and
not on a re-implementation of it.

`pair_by_overlap` is imported from the frozen item 19/20 instrument
(`diagnostics/item19/item19_core.py:130`); that module's own `CONFIG` still
points at params-10 and is never used — params-12 is loaded independently.

**Duration convention, declared once and used throughout:**
`duration = end_idx − start_idx + 1` (number of timesteps; a one-step block has
duration 1, never 0).

**Depth:** `D1 = (z_max − z_valley) / (z_max − z_min)`, computed on
`df['z'] = vorticity_smoothed2` — the same filtered series the detector reads —
never on the raw series.

---

## 2. Series with more than one `mature` block under params-12

**7 of 47** — 5 real, 2 synthetic.

### Real (5 of 35)

| series | block | start | end | dur | valley | D1 | label | Δstart | Δend | ratio/A | ratio/B | ratio/C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20150656 | 0 `[ABC]` | 34 | 48 | 15 | v42 | 1.0000 | L0 | 0 | −4 | 1.000 | 1.000 | 1.000 |
| 20150656 | 1 | 140 | 147 | 8 | v143 | 0.8351 | — | — | — | 0.533 | 0.533 | 0.533 |
| 20180628 | 0 `[ABC]` | 29 | 40 | 12 | v37 | 1.0000 | L0 | −1 | −6 | 1.000 | 1.000 | 1.000 |
| 20180628 | 1 | 70 | 75 | 6 | v72 | 0.9980 | — | — | — | 0.500 | 0.500 | 0.500 |
| 20180733 | 0 `[B]` | 31 | 43 | 13 | v37 | 0.9303 | — | — | — | 1.083 | 1.000 | 1.083 |
| 20180733 | 1 `[AC]` | 135 | 146 | 12 | v140 | 1.0000 | L0 | +6 | −4 | 1.000 | 0.923 | 1.000 |
| 20203947 | 0 `[AB]` | 129 | 136 | 8 | v132 | 1.0000 | — | — | — | 1.000 | 1.000 | 1.000 |
| 20203947 | 1 `[C]` | 181 | 188 | 8 | v185 | 0.9422 | L1 | +3 | 0 | 1.000 | 1.000 | 1.000 |
| 20205386 | 0 `[B]` | 36 | 42 | 7 | v41 | 0.8687 | — | — | — | 1.167 | 1.000 | 1.750 |
| 20205386 | 1 `[C]` | 60 | 63 | 4 | v61 | 0.8805 | L0 | +4 | −1 | 0.667 | 0.571 | 1.000 |
| 20205386 | 2 `[A]` | 80 | 85 | 6 | v82 | 1.0000 | — | — | — | 1.000 | 0.857 | 1.500 |

Manual labels: 20150656 `[[34,52]]`; 20180628 `[[30,46]]`; 20180733 `[[129,150]]`;
20203947 `[[122,144],[178,188]]` (second `unsure`); 20205386 `[[56,64]]`.

### Synthetic (2 of 12) — reported separately, never pooled with the reals

| series | block | start | end | dur | valley | D1 | label | Δstart | Δend | ratio/A | ratio/B | ratio/C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s6b542eee | 0 `[BC]` | 12 | 19 | 8 | v16 | 0.9999 | L0 | 0 | +1 | 1.000 | 1.000 | 1.000 |
| s6b542eee | 1 `[A]` | 44 | 51 | 8 | v48 | 1.0000 | L1 | +1 | 0 | 1.000 | 1.000 | 1.000 |
| sbd6c6920 | 0 `[ABC]` | 14 | 20 | 7 | v17 | 1.0000 | L0 | +1 | −1 | 1.000 | 1.000 | 1.000 |
| sbd6c6920 | 1 | 45 | 51 | 7 | v48 | 0.9922 | L1 | +2 | −1 | 1.000 | 1.000 | 1.000 |

Labels: s6b542eee `[[12,18],[43,51]]`; sbd6c6920 `[[13,21],[43,52]]`. Both
synthetics genuinely have two labelled matures, **both blocks match**, and both
series already pass the sequence test. Every ratio is exactly 1.000, so any
floor `r ≤ 1.0` leaves all four blocks untouched.

---

## 3. The central result — the three anchors disagree

| series | A (max D1) | B (max duration) | C (label-matched) | A=B | A=C | B=C |
|---|---|---|---|---|---|---|
| 20150656 | block 0 (34,48) | block 0 (34,48) | block 0 (34,48) | yes | yes | yes |
| 20180628 | block 0 (29,40) | block 0 (29,40) | block 0 (29,40) | yes | yes | yes |
| **20180733** | block 1 (135,146) | block 0 (31,43) | block 1 (135,146) | **NO** | yes | **NO** |
| **20203947** | block 0 (129,136) | block 0 (129,136) | block 1 (181,188) | yes | **NO** | **NO** |
| **20205386** | block 2 (80,85) | block 0 (36,42) | block 1 (60,63) | **NO** | **NO** | **NO** |
| **s6b542eee** | block 1 (44,51) | block 0 (12,19) | block 0 (12,19) | **NO** | **NO** | yes |
| sbd6c6920 | block 0 (14,20) | block 0 (14,20) | block 0 (14,20) | yes | yes | yes |

**The anchors diverge in 4 of the 7 series: 20180733, 20203947, 20205386,
s6b542eee.** In 20205386 all three point at three *different* blocks.

**Instrument gap, recorded against this front's own measurement.** Anchor B
ties in **3 of the 7** series — 20203947 (8 and 8), s6b542eee (8 and 8),
sbd6c6920 (7 and 7) — and **no tie-break rule was declared before measuring**.
The driver's `max()` breaks a tie at the lowest index, which is an implicit rule
rather than a stated one, and one reported divergence is an artefact of it:
**s6b542eee's "A≠B" is not a real divergence**, only `max()` taking block 0
while anchor A takes block 1 on a D1 margin of 0.9999 vs 1.0000. The other two
ties resolve to the block anchor A picks anyway. **The verdict is unaffected** —
all three tied pairs have ratio exactly 1.000, so no floor `r ≤ 1.0` touches
them under either resolution, and criterion (a) fails on 20205386, which has no
tie. But a tie here is not rare (43 % of the multi-block series), so any future
duration rule must declare its tie-break **before** measuring.

### Why this kills the rule

The decisive fact is that in **20205386 the anchor is itself a spurious block**
under both implementable definitions:

- **Anchor A (deepest valley):** the deepest valley of the series (D1 = 1.0000,
  v82) generates block 2 (80,85) — which matches no label. The brief anticipated
  this: 20205386's true valley v61 has D1 = 0.8805 and is *not* the deepest of
  its own series.
- **Anchor B (longest block):** the longest block is block 0 (36,42), duration 7
  — also spurious. The true block (60,63) is the **shortest** of the three, at
  duration 4.

A proportional floor never rejects its own anchor (its ratio is 1 by
construction). So in 20205386 one spurious block survives by definition under
either anchor, and the other one is *longer* than the anchor under A
(ratio 1.167), so no floor reaches it either. Under A, to reject block 0 a floor
would have to exceed 1.1667 — which would reject the true block (0.667), both
synthetics' second blocks (1.000) and essentially everything else.

Under 20205386 the rule is not merely badly tuned; it is **pointing the wrong
way**. The block a duration floor most wants to discard is the one the label
says is correct.

**And 20205386 is not alone.** 20180733 inverts duration against veracity too:
its spurious block (31,43) runs **13** steps against the **12** of the true
block (135,146), label 129–150. So in **2 of the 5** real multi-block series
duration and veracity point in opposite directions. The anti-correlation is a
property of the population, not an outlier — which is why this is a failure of
premise rather than of calibration.

---

## 4. Gate, criterion by criterion

Anchor C does not count toward the verdict (not implementable — production has
no labels). It is reported anyway: even as a diagnostic its band is empty
(needs `r > 1.7500` to clear 20205386, but `r ≤ 1.0000` to keep the synthetics).

| criterion | anchor A | anchor B |
|---|---|---|
| **(a)** removes both spurious blocks of 20205386 | **FAIL** — anchor *is* spurious block 2; block 0 has ratio 1.167 > 1, unreachable | **FAIL** — anchor *is* spurious block 0, can never be removed |
| **(b)** cuts no label-matched block in any of the 47 | PASS for `r ≤ 0.6667` | PASS for `r ≤ 0.5714` |
| **(c)** preserves both detected blocks of 20203947 | PASS for `r ≤ 1.0000` | PASS for `r ≤ 1.0000` |
| **(d)** removes no block of the 12 synthetics | PASS for `r ≤ 1.0000` | PASS for `r ≤ 1.0000` |
| **(e)** generalises beyond 20205386 | PASS — 20150656 and 20180628 | PASS — 20150656 and 20180628 |

**Stage-1 verdict: FAIL.** The gate requires all five together for at least one
of A or B. **(a) fails under both.** The front closes without touching code.

### Bands, for the record

- **Whole-band emptiness.** To remove *every* spurious non-anchor block:
  anchor A needs `r > 1.1667` while preserving all matched blocks needs
  `r ≤ 0.6667` — band **empty**. Anchor B needs `r > 0.8571` against
  `r ≤ 0.5714` — band **empty**. Anchor C needs `r > 1.7500` against
  `r ≤ 1.0000` — band **empty**.
- **A cost-free floor does exist**, it simply does not do the job it was
  proposed for: `r ∈ (0.5333, 0.6667]` under anchor A (or `(0.5333, 0.5714]`
  under B) removes the spurious second blocks of **20150656** and **20180628**
  and cuts nothing that matches a label, in any of the 47. It does not touch
  20205386, 20180733 or 20203947 at all. That satisfies (b)–(e) and fails (a).

### A correction to the premise's arithmetic

The brief expected the usable band to be squeezed *below 0.48*, from
20203947's labelled duration ratio. The measurement says otherwise: 20203947's
two **labelled** matures have durations 23 and 11 (ratio 0.4783), but its two
**detected** blocks both have duration 8 — **detected ratio exactly 1.000**. The
detected amplitude windows do not reproduce the labelled duration ratio at all,
so 0.48 never enters as a constraint. The real ceiling is 20205386's own true
block at 0.667 (anchor A) or 0.571 (anchor B). This widens the band relative to
the prediction and changes nothing about the verdict, because the binding
failure is (a), which is structural rather than numerical.

---

## 5. Case apart — series where no block matches any label

Required by point 4 of the brief; none of these is discarded. **All five have a
single mature block**, so a proportional floor is a no-op on them (a lone block
is its own anchor under A and B and is never rejected).

| series | blocks | label | best overlap | Δstart | Δend | why no match |
|---|---|---|---|---|---|---|
| 20170154 | 1: (35,43) d=9, D1=1.0000 | [31,76] | 9 | +4 | **−33** | end far inside the label |
| 20170409 | 1: (60,66) d=7, D1=1.0000 | [55,73] | 7 | +5 | **−7** | end 1 step past margin 6 |
| 20190639 | 1: (88,104) d=17, D1=1.0000 | [81,105] | 17 | **+7** | −1 | start 1 step past margin 6 |
| 20171179 | 1: (36,48) d=13, D1=1.0000 | *none* | — | — | — | series has no labelled mature |
| 20181046 | 1: (19,26) d=8, D1=1.0000 | *none* | — | — | — | series has no labelled mature |

Three further series produce **no mature block at all**: 20170760 (label
[26,39]), 20191014 (label [43,68]), s0596ea57 (no labelled mature). Also
unaffected by a floor.

**Census reconciliation:** 42 series have both blocks and labels; 39 of them
have at least one block matching some label within the fixed margin 6 on both
ends, and 3 do not (the first three rows above). 2 series have blocks but no
labelled mature, 2 have a labelled mature but no block, 1 has neither —
39+3+2+2+1 = 47.

---

## 6. Baseline — unmoved, as expected for a measurement-only stage

| quantity | brief | measured | |
|---|---|---|---|
| mature boundary within ±6 | 38/47 | **38/47** | ✓ |
| sequence match | 31/47 | **31/47** | ✓ |
| synthetics | 12/12 | **12/12** | ✓ |
| `series_sha256` verified | — | **47/47** | ✓ |

The incipient boundary was recorded for all 47 series and is archived in
`item20c_facts.json` under `incipient` for comparison by a later front.

**One instrument note, not a divergence.** The 38/47 above is the item 19/20
convention: `pair_by_overlap` against the **first** labelled mature only. The
per-block census in §5 reports **39** series with a matched block, because it
scans *every* label rather than only L0 — the one-series difference is
20203947, which matches on L1. Both numbers are correct for their own
instrument; the baseline number 38 reproduces exactly.

Of the 16 sequence failures, only 5 are multi-mature-block series, so
fragmentation of `mature` is a minority cause of sequence mismatch on this
split.

---

## 7. Latent defects in `find_stages.py` — zero firings, recomputed

Both were confirmed by **recomputing the firing condition on every valley**, not
by the absence of an exception.

In `_amplitude_mature_bounds`:

- `find_stages.py:152-154` — `seg_prev = df.loc[previous_z_peak:z_valley]`, then
  `seg_prev.index[violations_prev[-1] + 1]`. This indexes past the segment
  exactly when the **last** element of `seg_prev` (z at the valley itself)
  violates `level_prev`, i.e. `z[valley] > level_prev`.
- `find_stages.py:159-161` — `seg_next = df.loc[z_valley:next_z_peak]`, then
  `seg_next.index[violations_next[0] - 1]`. This wraps to `index[-1]` (silently
  returning `next_z_peak` as `mature_end`) exactly when the **first** element of
  `seg_next` violates `level_next`, i.e. `z[valley] > level_next`.

Substituting `level_prev = z_pp − maf·(z_pp − z_v)` gives an identity:

> `margin_152 ≡ z_v − level_prev = −(1 − maf)·amplitude_prev`

and likewise for `margin_159`. This identity was checked numerically and holds
to a relative error of **3.67e-16** across all valleys. With
`maf = 0.90 < 1` it collapses the trigger to a **sign test**: either defect can
fire only if the corresponding amplitude is `≤ 0` — that is, only if a valley's
z sits at or above its own bounding peak's z.

Measured over the 47 train series:

- **81** z-valleys in total after the prominence filter;
- **59** reach the window code (the other 22 lack a bounding peak on one side
  and hit the `continue` at `find_stages.py:328-329`);
- **52** of the 59 are eligible after `mature_min_depth = 0.80`.

All **59** were checked, not just the 52 eligible ones:

| | value |
|---|---|
| firings of 152 | **0 / 59** |
| firings of 159/160 | **0 / 59** |
| min `amplitude_prev` | **+5.116e-06** |
| min `amplitude_next` | **+2.353e-07** |

Both minima are strictly positive, so neither condition is met anywhere on this
split. The nearest valleys to the sign flip are 20205386 v61 (`amplitude_prev`
5.116e-06) and 20181046 v26 (`amplitude_next` 2.353e-07). Fixing the defects
remains out of scope for this front.

---

## 8. Environment

| | |
|---|---|
| python | `/Users/danilocoutodesouza/miniconda3/envs/cyclophaser/bin/python` (dedicated `cyclophaser` env) |
| `cyclophaser` resolved from | the working tree (`.../CycloPhaser/cyclophaser`), not an installed release |
| numpy | **2.5.3** |
| scipy | **1.18.0** |
| pandas | 3.0.5 |
| params-12 sha256 | `39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3` (verified in-script before measuring) |
| frozen | `mature_amplitude_fraction = 0.90`, `mature_min_depth = 0.80` — neither swept, tuned nor tested for sensitivity |

This is the numpy 2.5.3 / scipy 1.18.0 side of the known divergence. The
measurement was not repeated under numpy 2.4.4 / scipy 1.17.1.

`git diff develop-v2.1 -- cyclophaser/` is **empty** — confirmed on the branch, and re-confirmed by the independent run in §10.

---

## 9. What is still open

1. **The result is a necessary condition, not a sufficient one.** The ratios
   above are computed on the blocks as they stand. Whether *removing* a block
   would displace a surviving block's boundaries downstream — `find_mature_stage`
   writes into `periods`, which `find_residual_period`, `post_process_periods`
   and `find_incipient_period` then read — is **not measured here**, because
   measuring it requires implementing the rule. This is the 20(b)/20205386
   lesson (watch the boundary, not the presence) and it would have been the
   first thing stage 2 had to check. The front fails before reaching it.
2. **20205386 is unexplained and still broken.** Its three valleys all clear the
   0.80 depth floor and its true valley is neither the deepest nor the one
   generating the longest block. Nothing in depth or duration separates the true
   block from the spurious pair. A future front needs a different discriminator;
   composite depth×duration scores were explicitly out of scope here and remain
   unmeasured.
3. **The cost-free floor at `r ∈ (0.5333, 0.6667]` is STOPPED backlog** —
   Danilo's ruling, 2026-09-21. It would clean up 20150656 and 20180628 at no
   measured cost, but it is not implemented and is not handed on as ready work:
   its ceiling is pinned by 20205386's own *true* mature (0.6667), its 0.13 of
   slack is defined by exactly two series, and its sequence gain is
   unverifiable without implementing (item 1 above — the 20(b) fill-in lesson).
   **Reopening requires a new front with its premise redeclared; loosening this
   gate after seeing the result is forbidden.** Recorded so the number is not
   lost.
4. **20180733** has a spurious block that is *longer* than the true one
   (13 vs 12) — no duration rule in either direction separates them.
5. **20170409 and 20190639** each miss the fixed margin 6 by a single step
   (Δend −7, Δstart +7). Unrelated to this front; noted because they sit right
   at the instrument's edge.
6. The **latent defects** at `find_stages.py:154` and `:161` are still present.
   Confirmed dormant on this split only.
7. 20160735's remaining defect — two false intensification/decay cycles filling
   the gap before mature — was out of scope and is untouched.

---

## 10. Independent verification

The measurement above was reproduced independently, and the two runs agree.

**What was done, and by whom.** The re-measurement was carried out by Claude
**separately from the agent run that produced this report**, with a **driver
written from scratch against the public API** — `process_vorticity` /
`get_periods` — rather than by re-executing `item20c_measure.py`. Nothing was
shared between the two: not the driver, not the block-attribution logic, not the
anchor code. It was run under **numpy 2.4.4 / scipy 1.17.1**, against the
**numpy 2.5.3 / scipy 1.18.0** of this report (§8) — the version pair with known
behavioural divergence in this codebase, which is the reason a second
environment is worth the trouble.

**What it reproduced.**

| | agreed |
|---|---|
| the set of series emitting more than one mature block | the same **7** |
| `20205386` — every block boundary, every D1, every ratio | identical |
| the cost-free window | `(0.5333, 0.6667]` |
| `20203947` — detected duration ratio | **1.000** |

It also confirmed, on the branch, the `params-12` sha256 and that
`git diff develop-v2.1 -- cyclophaser/` is empty.

**Scope of the claim, stated exactly.** The independent run is reported here as
received; **this agent did not execute it** and cannot re-run it, because no
numpy 2.4.4 / scipy 1.17.1 environment exists on this machine (the fixed rule
confines runs to the dedicated `cyclophaser` env, which carries 2.5.3 / 1.18.0).
What *is* verified from here is that the four quantities listed above match the
values in §2–§4 of this report exactly. The environment and the independence of
the driver rest on that report, not on a measurement made in this session, and
are recorded on that basis rather than asserted as this front's own result.

The practical consequence: the seven-series finding and the `20205386` numbers —
the two facts the FAIL verdict rests on — are **not** artefacts of one numpy /
scipy pair.

---

## 11. Files

| file | what |
|---|---|
| `item20c_measure.py` | the measurement; replays the detector, attributes blocks to valleys, verifies the replay against `get_periods`, recomputes both defect conditions |
| `item20c_anchors.py` | anchor tables, divergence, floor bands and the criterion-by-criterion gate; reads the JSON only |
| `item20c_facts.json` | every measured fact, per series and per block |
| `item20c_tables.md` | the generated tables |
| `REPORT.md` | this file |
