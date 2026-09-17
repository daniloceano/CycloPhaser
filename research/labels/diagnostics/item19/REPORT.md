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
loss is invisible here. Stage 2 finds it. See §2.3 and §3.

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

### 2.3 The trade-off, exactly

Criterion (b) — `20160735` reduced to exactly one mature within ±6 of 145 and 178
— is satisfied in **2 cells out of 45**, both at the top of the
`prominence_relative` range:

| cell | (b) | Δstart | Δend | what it costs |
|---|---|---|---|---|
| `pr=0.60, maf=0.85` | PASS | +3 | +6 | (a′) `20191014` and `scfcf1387` lose their mature; (c) `scfcf1387` stops matching its sequence; (d) `20191014` goes from sum\|Δ\|=163 to no mature at all; (f) synthetic sequence 12 → 11 |
| `pr=0.60, maf=0.90` | PASS | +5 | +4 | identical costs |

Criterion (e) is the only one these cells keep.

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

### 2.4 Before/after figures (step 3.4)

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
2. **A ≥ 7-step floor does not, on its own, fix `20160735` under `params-10` — and
   at `params-10` it would do real damage.** `20160735`'s four blocks are 3, 8, 13
   and 8 steps long, so a floor of 7 removes only the 3-step block and leaves
   three matures where the label has one; clearing the 8-step blocks needs a floor
   of 9. Meanwhile the detector's own correct matures are short at this config:
   of the 32 label-matching matures, **11 are shorter than 7 steps and 17 shorter
   than 9**. A ≥ 7-step floor at `params-10` would delete 11 correct matures to
   remove one spurious block.

   That is a statement about `params-10`, not about the mechanism. Widening the
   window first changes it completely:

   | `maf` (at `pr=0.30`) | matures matching the label | windows < 7 steps | < 9 steps | median length |
   |---|---|---|---|---|
   | 0.95 (`params-10`) | 32 | **11** | 17 | 8 |
   | 0.90 | **38** | 2 | 8 | 13 |
   | 0.85 | 36 | 1 | 3 | 15 |
   | 0.80 | 32 | 1 | 1 | 18 |

   **So the duration floor should be measured at `mature_amplitude_fraction ≈ 0.90`,
   not at 0.95**, where it costs 2 correct matures rather than 11. The floor's
   value still has to be measured on the train split against a gate declared
   first, exactly as this one was — but it should not be measured at `params-10`'s
   amplitude fraction.

---

## 4. Findings recorded in passing (not part of the gate)

**(a) `mature_amplitude_fraction = 1.0` raises `IndexError`.** Documented as a
legal value (`0 < maf ≤ 1`, validated `find_stages.py:242-245`) and reachable from
the calibration app. Two of 47 training series hit it; whether a given series does
depends on floating-point round-off in `z_peak − 1.0 × (z_peak − z_valley)`
against `z_valley`. The forward side of the same function has the mirror defect
and is **worse because it is silent**: `mature_end = seg_next.index[violations_next[0] - 1]`
(`find_stages.py:160`) wraps to `index[-1]` when the first element violates, which
returns `next_z_peak` — a maximally wrong window — instead of raising. Not fixed
here; this front changes no package code.

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
| test split | not read, not scored, not plotted |

The premise of the front is **confirmed**: `prominence_relative` and
`mature_amplitude_fraction` cannot separate "reject the spurious troughs in
`20160735`" from "keep the true extrema in the rest of the split". A different
mechanism is required, and the gate already declared which one to try.
