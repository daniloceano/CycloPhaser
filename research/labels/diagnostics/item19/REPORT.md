# Item 19/20, part 1 — mature detection: `prominence_relative` × `mature_amplitude_fraction`

**Verdict: the gate FAILS. 0 of 45 cells satisfy all six criteria. The declared
prediction was FAIL.**

The trade-off the front was commissioned to test is confirmed with numbers, not
refuted: the only two cells in the whole grid that fix `20160735` are the two
that also destroy the mature phase of two other training series outright, and
they are the same cells for every reason — one scalar cannot separate the two
effects.

---

## 0. Provenance

| | |
|---|---|
| branch | `research/item19-mature-prominence`, from `develop-v2.1` @ `5120856` |
| gate declared at | `cc46b47`, **before** any measurement (`docs/future_work.md`, item 20(a)) |
| code provenance commit | `79bb7b3` |
| config versioned at | `8f8a67f` |
| package code changed | **none** — `git diff develop-v2.1 -- cyclophaser/ tests/` is empty |
| environment | conda `cyclophaser`, `/Users/danilocoutodesouza/miniconda3/envs/cyclophaser/bin/python` |
| cyclophaser imported from | `/Users/danilocoutodesouza/Documents/Programs_and_scripts/CycloPhaser/cyclophaser/__init__.py` — the working tree, **not** the published 1.7.3 |
| config | `research/labels/configs/cyclophaser_params-10.yaml` |
| config sha256 | `c14755e3ac1c2dcb2da8e652e7eba61ce20b8c45235b18cd7183abac047902d7` — **matches** the value declared in the brief |
| split | TRAIN only: 35 real + 12 synthetic = 47. The test split was never read, scored or plotted. |
| label sha256 | all 47 training series match their label's `series_sha256`; 0 mismatches |

Every table below was produced under `params-10`, or under a grid cell that
differs from `params-10` only in `prominence_relative` and
`mature_amplitude_fraction`. Scripts: `item19_core.py` (shared detector harness),
`stage1_describe.py`, `stage2_grid.py`, `stage2_tradeoff_figure.py`.

`evaluate_against_labels.py --config …params-10.yaml` was run first and its
verbatim output is in `evaluate_params10_train.txt`; the per-series tables below
reproduce its totals exactly (sequence 30/47, real 18/35, synthetic 12/12).

---

## 1. Stage 1 — descriptive, `params-10`, train only

Full tables: `stage1_per_series.md`, `stage1_baseline.txt`, `stage1_prominence.md`.

### 1.1 Scoring (step 2.1)

| set | n | sequence match | mature within ±6 at both ends | no mature at all | more than one mature block |
|---|---|---|---|---|---|
| real | 35 | 18/35 | 21/35 | 1 (`20170760`) | 7 |
| synthetic | 12 | 12/12 | 11/12 | 1 (`s0596ea57`) | 2 |
| **ALL** | **47** | **30/47** | **32/47** | **2** | **9** |

Incipient boundary, from `evaluate_against_labels.py`: 27 boundary labels, 17
hit within each label's own margin (63.0%), MAE 3.00, worst 26; the detector
found no incipient phase on 6 of those 27.

`Δstart`/`Δend` are detected minus labelled, in steps, for the detected mature
block with the largest **overlap** with the labelled one. Overlap pairing, not
order pairing: across a sequence mismatch, pairing the k-th detected mature with
the k-th labelled one compares two different transitions. Note that `Δend` is the
same number whether both sides use inclusive or exclusive ends, so the brief's
"label 178" and the tables' "label 177" give identical deviations.

The three series the gate names:

| series | seq | n mature blocks | detected mature | label | Δstart | Δend |
|---|---|---|---|---|---|---|
| `20160735` | NO | **4** | `(8,10) (55,62) (154,166) (225,232)` | 145–178 | +9 | −11 |
| `20191014` | NO | 1 | `(135,137)` | 43–69 | +92 | +71 |
| `20203947` | NO | 4 | — | 122–145 | +8 | −9 |

`20160735` reproduces the brief exactly: short troughs at indices 9, 59 and 228
each become a mature block of 3–8 steps, and the one block that does overlap the
label covers 13 of the label's 33 steps. `fig_20160735_params10.png`.

### 1.2 Constant baseline (step 2.2)

The modal labelled phase sequence over the 47 training labels is
`incipient → intensification → mature → decay`, held by 16 of them. A constant
predictor emitting that sequence for every series scores, on the same
whole-sequence metric:

| | constant baseline | detector under `params-10` |
|---|---|---|
| ALL | **16/47** (34.0%) | **30/47** (63.8%) |
| real | 13/35 | 18/35 |
| synthetic | 3/12 | 12/12 |

The detector beats the constant baseline on this label set, by 14 series. Worth
stating because item 18's topology front was caught the other way round.

### 1.3 Relative prominence (step 2.3)

**The quantity.** `scipy.signal.peak_prominences(signed_data, interior)[0]`,
computed at `cyclophaser/determine_periods.py:188` on the **filtered** vorticity
(`vorticity_smoothed2` — `determine_periods.py:1012`, `:1017`), and compared at
`determine_periods.py:203-208` against
`prominence_relative × max(prom_vals over the surviving interior set)`.
The denominator is **per series and per extremum type** — peaks are refined on
`data`, valleys on `-data` (`determine_periods.py:135-136`) — so each number is a
fraction of its own series' own valley maximum, never a vorticity unit. Indices
0 and N−1 are exempt (`determine_periods.py:180-181`).

**(i) `20160735`.** Four surviving z valleys generate a mature candidate; all
four survive to the output.

| valley | rel prominence | window | len | inside label 145–178? |
|---|---|---|---|---|
| 9 | 0.3037 | 8–10 | 3 | no |
| 59 | 0.5709 | 55–62 | 8 | no |
| 159 | **1.0000** | 154–166 | 13 | **yes** |
| 228 | 0.4902 | 225–232 | 8 | no |

**(ii) the train split.** 32 series have a detected mature within ±6 of the label
at both ends. Of the 32 generating valleys, **30 sit at relative prominence
1.0000** — they are their series' deepest valley — one is at 0.9761
(`s6b542eee`) and one at **0.3074** (`20205386`).

**(iii) the two distributions OVERLAP.**

| | n | range |
|---|---|---|
| spurious — `20160735` candidates outside the label | 3 | **0.3037 – 0.5709** |
| true — valleys generating a label-matching mature, whole train split | 32 | **0.3074 – 1.0000** |

The overlapping band 0.3074–0.5709 holds 2 of the 3 spurious values and 1 of the
32 true ones. A threshold placed just above the worst spurious value (0.5709)
therefore also rejects 1 of the 32 true mature-generating valleys.
`fig_prominence_distributions.png`.

**This is the mechanical statement of the trade-off, before any grid was run:
the separation is not clean, but it looks nearly clean — this table puts the cost
of fixing `20160735` by prominence alone at one valley, and stage 2 measures
whether "one" is small enough.** It is not, and the table understates the cost:
table (ii) lists only series whose mature already *matches* its label, so a series
like `20191014` — which has a mature, badly placed — contributes no row and its
loss is invisible here. Stage 2 finds it. The one valley this table *does* name,
`20205386`'s at relative prominence 0.3074, turns out not to be lost at all but
displaced, in a way the gate itself cannot see: §2.4. See also §2.3 and §3.

---

## 2. Stage 2 — the 45-cell grid, train only

`prominence_relative` {0.20 … 0.60 step 0.05} × `mature_amplitude_fraction`
{0.80 … 1.00 step 0.05}, every other parameter at `params-10`. Full tables:
`stage2_grid.md`, `stage2_losses.md`, raw results `stage2_cells.json`.

### 2.1 Criteria met, out of 6

| prom_rel \ maf | 0.80 | 0.85 | 0.90 | 0.95 | 1.00 |
|---|---|---|---|---|---|
| **0.20** | 5 | 5 | 5 | 5 | 0 |
| **0.25** | 4 | 4 | 5 | 5 | 0 |
| **0.30** | 4 | 4 | 5 | **5** ← `params-10` | 0 |
| **0.35** | 4 | 4 | 5 | 5 | 0 |
| **0.40** | 4 | 4 | 5 | 5 | 0 |
| **0.45** | 3 | 3 | 3 | 3 | 0 |
| **0.50** | 3 | 3 | 3 | 3 | 0 |
| **0.55** | 1 | 1 | 1 | 1 | 0 |
| **0.60** | 1 | **2** | **2** | 1 | 0 |

**Cells meeting all six criteria: none.** `params-10` itself scores 5/6 — it fails
only (b), by construction, since the other five criteria are defined relative to
it.

How often each criterion fails over the 45 cells:

| criterion | cells failing |
|---|---|
| (a′) no series loses its mature | 25/45 |
| (b) `20160735` has exactly one mature within ±6 | **43/45** |
| (c) no series stops matching its sequence | 17/45 |
| (d) `20191014` / `20203947` do not worsen | 33/45 |
| (e) incipient boundary unchanged everywhere | 9/45 |
| (f) synthetic sequence score does not drop | 17/45 |

### 2.2 The `mature_amplitude_fraction = 1.00` column is degenerate — and it crashes

At `maf = 1.00`, `level_prev = z_peak − 1.0 × (z_peak − z_valley) = z_valley`
(`find_stages.py:144-145`), so the amplitude window collapses to the valley alone.
The column scores 0/6 everywhere: sequence drops to 2/47 and 46 of 47 series lose
their mature.

**It also raises.** On `20150532` and `s5b8aa46f`, floating-point round-off puts
`z[z_valley]` above `level_prev` by ~1e-20, so the valley itself counts as a
violation, `violations_prev[-1] + 1` runs one past the end of the segment, and
`find_stages.py:152` raises `IndexError: index 41 is out of bounds for axis 0
with size 41`. `mature_amplitude_fraction = 1.0` is explicitly validated as legal
at `find_stages.py:242-245`. Recorded, not fixed: this front does not change
package code. See §4(a).

The harness records such a cell as a total failure and names the series rather
than swallowing the exception; a cell that cannot be computed on all 47 series
cannot satisfy a gate defined over all 47.

**The crash is environment-dependent; the defect is not.** It was observed here
on **numpy 2.5.3 / scipy 1.18.0 / pandas 3.0.5, Python 3.12.14**. An independent
run on **numpy 2.4.4 / scipy 1.17.1** did **not** reproduce it — `s5b8aa46f` ran
without error there. That is exactly what a round-off-triggered out-of-range index
looks like: the guard at `find_stages.py:152` is missing in every environment, and
whether the last element of the segment lands a part in 1e20 above or below the
level depends on the arithmetic of the installed builds. **The verdict does not
move**: the `maf = 1.00` column is degenerate on its own terms — the window
collapses to a single step — in every environment, crash or no crash.

### 2.3 The trade-off, exactly

Criterion (b) — `20160735` reduced to exactly one mature within ±6 of 145 and 178
— is satisfied in **2 cells out of 45**, both at the top of the
`prominence_relative` range:

| cell | (b) | Δstart | Δend | what it costs |
|---|---|---|---|---|
| `pr=0.60, maf=0.85` | PASS | +3 | +6 | (a′) `20191014` and `scfcf1387` lose their mature; (c) `scfcf1387` stops matching its sequence; (d) `20191014` goes from sum\|Δ\|=163 to no mature at all; (f) synthetic sequence 12 → 11 |
| `pr=0.60, maf=0.90` | PASS | +5 | +4 | identical costs |

Criterion (e) is the only one these cells keep.

**How much weight those costs carry — stated plainly.** `20191014`'s mature under
`params-10` sits at 135–137 against a label of 43–69: it is wrong by 92 steps.
Losing it is not clearly a regression, and criterion (d) flags it only because the
gate was written to compare `sum|Δ|` against "no mature at all". Strip that case
out and **the FAIL rests on `scfcf1387` alone** — a synthetic series that loses a
correctly-placed mature, breaks its phase sequence, and takes the synthetic score
from 12/12 to 11/12, failing (a′), (c) and (f) on its own. One series is enough to
fail the gate as declared, and `scfcf1387` is the cleanest possible case (a
synthetic with an unambiguous label), but the honest statement is that the cost of
`prominence_relative = 0.60` is **one clearly-correct mature destroyed plus one
badly-placed one**, not two equally damning losses.

No cell fixes `20160735` below `prominence_relative = 0.60`, and no cell at
`0.60` leaves the rest of the split intact. The curves are in
`fig_tradeoff_pr060_maf090.png`: `20160735` goes from four mature blocks to one
well-placed one, while `20191014` and `scfcf1387` lose the flanking z peak their
mature needed and end with none.

`mature_amplitude_fraction` cannot rescue this, and the `pr = 0.60` column shows
precisely why. All four of its `maf < 1.00` cells give `20160735` exactly **one**
mature block — that is prominence's doing — and `maf` only sets how wide it is:

| `maf` at `pr=0.60` | Δstart | Δend | (b) |
|---|---|---|---|
| 0.80 | +1 | +7 | fail — end 7 steps late |
| 0.85 | +3 | +6 | **pass** |
| 0.90 | +5 | +4 | **pass** |
| 0.95 | +9 | −11 | fail — window 11 steps short |

and all four lose the same two series, `20191014` and `scfcf1387`, with the same
sequence and synthetic-score damage. The amplitude fraction sizes a window; it
does not decide whether a candidate exists. Against this failure the two knobs
are not two degrees of freedom — they are one, and the second only trims the
result of the first.

### 2.4 The gate's blind spot — `20205386`

§1.3 predicted that a threshold above the worst spurious value (0.5709) would also
reject one true mature-generating valley: `20205386`'s valley at 61, relative
prominence 0.3074. §2.3 lists only `20191014` and `scfcf1387` as losses. Both are
correct, and the gap between them is a hole in the gate.

Measured (`closeout_measurements.txt`), `maf` held at 0.95:

| `prom_rel` | surviving valleys | mature blocks | paired | Δstart | Δend | within ±6 | sequence match |
|---|---|---|---|---|---|---|---|
| 0.30 (`params-10`) | 41 (0.3115), 61 (0.3074), 82 (1.0000) | (38,42) (60,62) (81,84) | (60,62) from valley **61** | +4 | −2 | **YES** | NO |
| 0.45 → 0.60 | **82 (1.0000) only** | (81,84) | (81,84) from valley **82** | **+25** | **+20** | **no** | NO |

So `20205386` **keeps a mature** — the deepest valley at 82 survives any threshold —
but it is a different mature, 25 steps late, and the series stops agreeing with its
label. Three criteria let it through:

* **(a′)** exempts it: it still has a mature, so "no series loses its mature" is
  satisfied.
* **(c)** exempts it: `20205386` does **not** match its sequence under `params-10`
  either, and (c) only protects series that already match.
* **(d)** does not watch it — the gate names only `20191014` and `20203947`.

**The gate as declared cannot see a series whose mature moves to the wrong place
without disappearing, unless that series' sequence was already correct.** On this
split that is not a small exemption: 17 of 47 series fail the sequence under
`params-10`, and all 17 are outside (c)'s protection.

It is genuinely mixed rather than simply bad, which is why it deserves reporting
rather than folding into the loss count. At `pr=0.60` the detected sequence becomes
`incipient → intensification → mature → decay` against a label of
`incipient → intensification → mature → decay → residual` — four phases of five,
where `params-10` produced a ten-phase sequence. The sequence gets tidier while the
mature boundary collapses from (+4, −2) to (+25, +20). Raising prominence trades
boundary accuracy for sequence tidiness on this series, and the gate scores neither
trade.

**This strengthens the FAIL rather than weakening it**: a third training series is
damaged at `pr = 0.60` beyond the two the gate counted, and it was damaged
invisibly.

### 2.5 Before/after figures (step 3.4)

Conditional on a PASS cell existing. None does, so the step is empty as
specified. `fig_tradeoff_pr060_maf090.png` is supplied in its place: the two
cells that come closest, with the series whose sequences change.

---

## 3. Where the lost matures disappear — A / B / C / D (step 3.3)

| code | mechanism | file:line |
|---|---|---|
| **A** | the generating z valley, or a flanking z peak, is cut by the relative-prominence filter, so no candidate is formed | `determine_periods.py:203-208` → `find_stages.py:261-262` |
| **B** | a candidate forms, but the amplitude window collapses to the valley alone (≤ 1 step) and is cleared one step later | `find_stages.py:135-160` |
| **C** | the `threshold_mature_length` duration check discards the window | `find_stages.py:304-312` |
| **D** | a real window forms and the intensification/decay neighbour check clears it | `find_stages.py:340-352` |

402 (cell, series) losses over 42 distinct series, of which 378 are the
degenerate `maf = 1.00` column. Split accordingly:

| region | (cell, series) losses | distinct series | A | B | C | D |
|---|---|---|---|---|---|---|
| `maf < 1.00` — the informative cells | 24 | **2** | **2** | 0 | **0** | 0 |
| `maf = 1.00` — degenerate column | 378 | 42 | 2 | 40 | **0** | 2 |

**Answer: in every informative cell, the lost matures disappear at stage A — the
prominence filter.**

| series | src | code | cells | `prominence_relative` range |
|---|---|---|---|---|
| `20191014` | real | **A** | 16 | ≥ 0.45 |
| `scfcf1387` | syn | **A** | 8 | ≥ 0.55 |

In both, no surviving z valley retains a flanking z peak on each side, so
`find_stages.py:261-262` skips the valley and no window is ever sized.

**C is 0 everywhere, and structurally so**, as recorded in `PROVENANCE.md` before
any measurement: `find_stages.py:304-312` is the `else` arm of
`if mature_method == 'amplitude'` at `:287`, and the `amplitude` arm assigns the
window unconditionally at `:303`. Under `params-10` the duration check does not
exist. The measurement confirms what the code structure already implied.

**B is 0 in the informative region** and is the whole story of the degenerate
column. Note that B can never appear as the guard it looks like: `find_stages.py:284-285`
(`len(mature_indexes) == 0`) can never fire, because `_amplitude_mature_bounds`
always returns a window containing `z_valley` itself. A collapsed window is not
rejected — it is emitted as a one-step mature and cleared a few lines later.

### What this means for the declared next step

The gate declared, before measuring: *replace the height filter with a duration
filter (a mature candidate accepted only if it sustains the window for ≥ 7 steps)
**if** stage 1 shows that the lost matures disappear in the prominence filter; if
they disappear in the amplitude window, a window rule will be declared first.*

They disappear in the **prominence filter** (A, 2 of 2 series). The declared
condition is met and the declared next step — the ≥ 7-step duration floor — is the
one that applies. No new rule needs declaring.

Two things that next front should carry:

1. A duration floor is a **new mechanism in the `amplitude` arm**, not a re-tuning
   of `threshold_mature_length`, which is unreachable there (§3, C). The comment
   at `find_stages.py:288-302` is a deliberate decision against exactly such a
   floor, made on a different case (`20160030`) under thresholds calibrated for
   `derivative`; it will have to be revisited explicitly, not worked around.
2. **A ≥ 7-step floor does not, on its own, fix `20160735` under `params-10`, and
   widening the window does not rescue the idea — the spurious blocks widen too.**

   `20160735`'s four blocks at `maf=0.95` are 3, 8, 13 and 8 steps, of which the
   13-step block is the one overlapping the label. A floor of 7 removes only the
   3-step block and leaves three matures where the label has one. The earlier
   draft of this report recommended measuring the floor at `maf ≈ 0.90` because
   the *correct* matures are longer there. That recommendation was not supported,
   and measuring it shows why:

   | `maf` | `20160735` all blocks (len) | overlapping the label | **spurious** | correct matures in split | < 7 | < 9 | median |
   |---|---|---|---|---|---|---|---|
   | 0.95 | 3, 8, 13, 8 | 13 | **3, 8, 8** | 32 | 11 | 17 | 8 |
   | 0.90 | 5, 12, 32, 12 | 32 | **5, 12, 12** | 38 | 2 | 8 | 13 |
   | 0.85 | 5, 15, 36, 21 | 36 | **5, 15, 21** | 36 | 1 | 3 | 15 |
   | 0.80 | 7, 19, 39, 24 | 39 | **7, 19, 24** | 32 | 1 | 1 | 18 |

   Lowering `mature_amplitude_fraction` widens everything roughly together, so the
   floor has to rise with it, and the cost rises faster than the benefit:

   | `maf` | floor needed to remove **all** spurious blocks | correct matures (min/med/max) | correct matures that floor destroys |
   |---|---|---|---|
   | 0.95 | ≥ 9 | 3 / 8 / 16 | **17 of 32** |
   | 0.90 | ≥ 13 | 4 / 13 / 32 | **19 of 38** |
   | 0.85 | ≥ 22 | 5 / 15 / 36 | **31 of 36** |
   | 0.80 | ≥ 25 | 5 / 18 / 28 | **30 of 32** |

   The best ratio anywhere in the column is `maf = 0.90`, and it still destroys
   **half** the correct matures. **A pure duration floor therefore looks no more
   separable than the height filter it was meant to replace**, at any amplitude
   fraction measured here. The declared next step is still the declared next step
   — the condition that triggers it was met (§3, code A) — but it should be
   measured knowing that the un-measured version of it, "≥ 7 steps at
   `params-10`", removes one of `20160735`'s three spurious blocks and 11 correct
   matures, and that no floor in this table separates the two populations.

   This is a measured prediction about a mechanism, not a result about it. A floor
   combined with something else — the candidates now registered as item 20(e) —
   is a different proposition and is not scored here.

---

## 4. Findings recorded in passing (not part of the gate)

**(a) `mature_amplitude_fraction = 1.0` can raise `IndexError`, and the missing
guard is unconditional.** Documented as a legal value (`0 < maf ≤ 1`, validated
`find_stages.py:242-245`) and reachable from the calibration app. `find_stages.py:152`
computes `seg_prev.index[violations_prev[-1] + 1]` with no check that the result is
in range, so when the last element of the segment — the valley itself — counts as a
violation, the index runs one past the end.

**Whether it fires depends on the environment.** Here, on **numpy 2.5.3 / scipy
1.18.0 / pandas 3.0.5, Python 3.12.14**, two of 47 training series hit it
(`20150532`, `s5b8aa46f`), because round-off puts `z[z_valley]` ~1e-20 above
`level_prev = z_peak − 1.0 × (z_peak − z_valley)`. An **independent run on numpy
2.4.4 / scipy 1.17.1 did not reproduce it** — `s5b8aa46f` completed there. The
absent bounds check is the same in both; only the last bit of the subtraction
differs. A defect that appears and disappears with a dependency bump is worse to
own than one that always fires, not better.

The forward side of the same function has the mirror defect and is **worse because
it is silent in every environment**: `mature_end = seg_next.index[violations_next[0] - 1]`
(`find_stages.py:160`) wraps to `index[-1]` when the first element violates, which
returns `next_z_peak` — a maximally wrong window — instead of raising.

Not fixed here; this front changes no package code.

**(b) The "true" prominence distribution is nearly degenerate.** 30 of the 32
label-matching matures are generated by their series' single deepest valley
(relative prominence exactly 1.0000). `prominence_relative` is therefore doing
almost no work in selecting *which* valley becomes the mature — it decides only
how many *additional* spurious matures appear alongside it. That is a stronger
statement than "the distributions overlap" and it is the reason a scalar height
threshold is the wrong instrument here.

**(c) `mature_amplitude_fraction = 0.90` is better than `params-10`'s 0.95 on
mature boundaries, at no cost to the sequence.** Holding everything else at
`params-10`, moving 0.95 → 0.90 raises the count of matures within ±6 of their
label at both ends from **32/47 to 38/47**, leaves the sequence score at 30/47 and
the synthetic score at 12/12, and moves no incipient boundary — that cell scores
5/6 on this front's gate, failing only (b), exactly as `params-10` does. It was
not pursued here because this front's gate is about `20160735`, which 0.90 does
not fix. It is the cheapest unclaimed improvement the grid turned up and it bears
directly on item 19(a) (the mature window is squeezed from both sides).

Read it as an improvement to the *window*, not as help for a duration floor: §3
measures that `20160735`'s spurious blocks widen along with the correct ones at
0.90, from 3/8/8 steps to 5/12/12.

**(d) Criterion (e) is the most robust of the six** — the incipient boundary moves
in only 9 of 45 cells, all of them at `maf = 1.00` (where the detector fails
wholesale). Neither parameter reaches the incipient boundary in the informative
region. That is a useful negative for any future front tempted to tune these two
knobs against incipient behaviour.

---

## 5. Gate verdict

| | |
|---|---|
| declared prediction | **FAIL** |
| measured | **FAIL** — 0 of 45 cells meet all six criteria |
| criterion (b) alone | met in 2 of 45 cells, both at `prominence_relative = 0.60` |
| those 2 cells | fail (a′), (c), (d) and (f) |
| where the matures are lost | **A** (prominence filter) in 2 of 2 informative series; B 0, C 0 (structurally), D 0 |
| cost of the (b)-passing cells | 1 clearly-correct mature destroyed (`scfcf1387`), 1 badly-placed one lost (`20191014`), 1 moved 25 steps off its label unseen by the gate (`20205386`) |
| test split | not read, not scored, not plotted |

The premise of the front is **confirmed**: `prominence_relative` and
`mature_amplitude_fraction` cannot separate "reject the spurious troughs in
`20160735`" from "keep the true extrema in the rest of the split". A different
mechanism is required.

The gate declared one — a ≥ 7-step duration floor — and the condition that
triggers it was met. But §3 now measures that a floor high enough to clear
`20160735`'s spurious blocks destroys between half and all of the correct matures
at every amplitude fraction tested, so the floor should not be expected to work
alone. Candidate mechanisms that have **not** been measured are registered in
`docs/future_work.md`, item 20(e).
