# Front 20(b), stage 1 — depth of the valleys that generate mature blocks

**Measurement only. No rule proposed, no rule implemented, no package code
changed.** The question this stage answers is narrow: *is there a separation
between the depth of the valleys that generate a correct mature block and the
depth of the ones that generate a spurious block?* If there is none, the front
dies here without code.

**Verdict: FAIL on global separability, for D1 and for D2 alike.** The
distributions do not merely overlap at the margin — the single deepest point of
three different series generates a **spurious** block, so the spurious
population reaches the maximum possible depth (D1 = D2 = 1.0000) and no
threshold on depth can sit above it. Details in §7.

---

## 1. Provenance

| | |
|---|---|
| branch | `research/item20b-depth-rule`, from `develop-v2.1` |
| environment | conda env `cyclophaser`, `/Users/danilocoutodesouza/miniconda3/envs/cyclophaser/bin/python` |
| numpy | **2.5.3** |
| scipy | **1.18.0** |
| pandas | 3.0.5 |
| python | 3.12.14 |
| config | `research/labels/configs/cyclophaser_params-11.yaml` |
| config sha256 | `24dd7f22b76d98cf0cab0b18ff040e010209604a8485007551095e9622abe420` — **confirmed before measuring**, matches the `24dd7f22…abe420` in the brief |
| `mature_amplitude_fraction` | 0.90 |
| scope | the **35 real series of the TRAIN split**. `read_split()["test"]` is never read, loaded or inspected by any file in this directory. |
| synthetics | excluded from the depth table (measurement A) as instructed; read **only** for measurement C, whose published denominator (38) is a 47-series number. |

`cyclophaser` resolves to the working tree via the editable install, verified
from **outside** the repository (`cd /tmp; python -c "import cyclophaser"` →
`…/CycloPhaser/cyclophaser/__init__.py`), so the working tree is not being
shadowed by the installed 2.0.0 wheel.

Note on numpy/scipy: earlier fronts saw a result divergence between
numpy 2.4.4 / scipy 1.17.1 and 2.5.3 / 1.18.0. Everything here was produced on
**2.5.3 / 1.18.0**. Recorded for traceability only; no claim is made about the
other pair.

Files in this directory:

* `measure_20b.py` — the driver. Runs the detector, builds the table.
* `analyse_20b.py` — reduces the table to the numbers in this report.
* `supplement_20b.py` — the two supplementary measurements (§4, §7.3).
* `depth_table.csv` — measurement A, one row per generating valley.
* `measurements.json` — the full per-series dump.

`research/labels/diagnostics/item19/item19_core.py` is **not** imported and
**not** edited. It is pinned to params-10 on purpose, and repointing or reusing
it would silently redefine the baseline of later fronts. The handful of helpers
it also contains (extremum prominence, phase runs, `pair_by_overlap`) are
re-derived in `measure_20b.py` directly from `determine_periods`, so this
driver stands alone.

---

## 2. Sanity check — the front's premise

Required before anything else: reproduce 20160735's four mature blocks with
durations 5, 12, 32, 12 under params-11.

```
blocks     [(7, 11), (53, 64), (150, 181), (224, 235)]
durations  [5, 12, 32, 12]                     <-- exact match
labelled   [(145, 177, 33)]                    <-- one block of 33
series_sha256 verified against the manual label: True
```

**REPRODUCED.** The premise holds: four detected blocks against a single
labelled one, and the best of the four (150–181) is the one that overlaps the
label. Measurement continued.

---

## 3. Which series feeds mature detection — declared explicitly

**The FILTERED series.** `determine_periods.py:1012–1017` sets

```python
z  = vorticity.vorticity_smoothed2
df = z.to_dataframe().rename(columns={'vorticity_smoothed2': 'z'})
```

and `find_stages._amplitude_mature_bounds` reads `df.at[…, 'z']` and nothing
else. `find_peaks_valleys` is also called on `df['z']`, so the valleys
themselves are the filtered series' valleys. The raw series is carried along as
`df['z_unfil']` and is never consulted by the mature path.

Under params-11 (`use_filter=True`, `cutoff_low=168`, `cutoff_high=18`,
`use_smoothing=False`), `vorticity_smoothed2` **is** the Lanczos band-pass
output with no Savitzky–Golay pass on top.

### Its mean — and why the brief's inference does not follow

The brief's concern was: if the filter is a band-pass it removes the mean, so a
≈ 0 mean would make D2's "zero" a filter artefact rather than the physical zero
of vorticity, which would remove D2's conceptual advantage over D1.

**Measured, over the 35 real train series:**

| quantity | min | median / mean | max |
|---|---|---|---|
| mean of the FILTERED `z` (s⁻¹) | −6.518e−05 | −3.829e−05 (mean) | −1.695e−05 |
| mean of the RAW `zeta` (s⁻¹) | −9.374e−05 | −6.311e−05 (mean) | −3.852e−05 |
| effective DC gain, mean(z)/mean(ζ) | 0.2408 | **0.6542** (median) | 0.8343 |
| \|mean(z)\| / (z_max − z_min) | 0.36 | **0.93** (median) | 2.81 |

**The mean is not ≈ 0.** The filtered series keeps a median **65 %** of the raw
mean, and that offset is a median **0.93×** the series' own peak-to-peak range —
on one series 2.81×. `z` does not oscillate about zero; it oscillates about a
large negative offset.

This is not a surprise to the package, which documents the mechanism in
`cyclophaser/lanczos_filter.py`: at `window_length_lanczo = len(series)//2`
the band-pass kernel *does not reject DC* — `sum(weights)` has a documented
median of 0.629. The measured 0.6542 matches that.

So the specific inference in the brief does not go through: D2's zero is **not**
the artefact of a mean-removing filter, because the mean is not removed.

It is, however, **not the physical zero either**. It is the physical zero times
a DC gain that depends on `len(series)//2` and therefore **varies per series**,
measured range **0.2408 – 0.8343** (spread 0.5935). D2 is a ratio taken on one
series, so a pure scalar gain would cancel — but the gain is not the same
number from one series to the next, so D2 is not measured against a common
baseline across the 35. This weakens D2's claim to be "the physical one" of the
two without rescuing D1. Both are reported throughout, and §7.3 additionally
recomputes D2 against physical zero on the raw series.

---

## 4. Sign guard

* series with `z_min ≥ 0`: **0** (none).
* generating valleys with `z_valley > 0`: **0** (none).

D2 = |z_valley| / |z_min| is well defined on every row of the table. Nothing was
worked around and no absolute value was used to repair a sign.

---

## 5. Measurement A — the generating-valley table

`depth_table.csv`, one row per valley that generates a mature block in the final
`periods` column, over the 35 real train series. All blocks are judged, not just
each series' best one: classification is **simple overlap** with any labelled
mature of that series (≥ 1 step), never `pair_by_overlap`.

Attribution of a block to a valley: each surviving z-valley with both bounding
z-peaks is passed through `_amplitude_mature_bounds` (the package function
itself, read-only) to get its candidate window; the valley is credited with the
final mature block its window overlaps most. Valleys whose window was cleared
downstream — by the neighbour-confirmation rule, or by `post_process_periods` —
generate no block and do not appear.

| | count |
|---|---|
| generating valleys measured | **46** |
| → **TRUE** (block overlaps a labelled mature) | **32** |
| → **SPURIOUS** (block overlaps none) | **14** |
| series emitting more than one block | 7 — `20150656` (2), `20160735` (4), `20170794` (2), `20180628` (2), `20180733` (2), `20203947` (4), `20205386` (3) |
| series with no labelled mature at all | 2 — `20171179`, `20181046` |
| series with no detected block at all | 1 — `20170760` |

Columns: `series, valley_idx, z_valley, z_min, z_max, D1, D2,
prominence_relative, prominence_abs, drop_left, drop_right, drop_asymmetry,
amp_prev_peak, amp_next_peak, window_start, window_end, block_start, block_end,
block_len, label_overlap, classification, n_blocks_in_series,
n_labelled_matures`.

`drop_left` / `drop_right` are scipy's own two climbs out of the valley, in z
units, reported **separately**; `peak_prominences` keeps only their minimum, so
`drop_asymmetry = drop_left − drop_right` is the quantity the detector currently
discards. `amp_prev_peak` / `amp_next_peak` are the peak-to-valley amplitudes
against the *surviving* bounding peaks — the two numbers
`_amplitude_mature_bounds` actually uses to size the window, which are not in
general the same as scipy's bases.

### All 14 SPURIOUS valleys, deepest first

| series | valley | D1 | D2 | rel. prom. | left drop | right drop | asymmetry | block | len |
|---|---|---|---|---|---|---|---|---|---|
| 20171179 | 45 | **1.0000** | **1.0000** | 1.0000 | 3.729e−05 | 3.813e−06 | +3.348e−05 | 36–48 | 13 |
| 20181046 | 26 | **1.0000** | **1.0000** | 1.0000 | 2.275e−05 | 2.353e−07 | +2.251e−05 | 19–26 | 8 |
| 20205386 | 82 | **1.0000** | **1.0000** | 1.0000 | 2.984e−05 | 1.530e−05 | +1.455e−05 | 80–85 | 6 |
| 20180628 | 72 | 0.9980 | 0.9984 | 0.3373 | 1.385e−05 | 4.093e−05 | −2.708e−05 | 70–75 | 6 |
| 20180733 | 37 | 0.9303 | 0.9108 | 0.7432 | 4.647e−05 | 2.586e−05 | +2.062e−05 | 31–43 | 13 |
| 20205386 | 41 | 0.8687 | 0.9201 | 0.3115 | 2.593e−05 | 4.765e−06 | +2.116e−05 | 36–42 | 7 |
| 20150656 | 143 | 0.8351 | 0.8390 | 0.6304 | 2.005e−05 | 1.789e−05 | +2.161e−06 | 140–147 | 8 |
| 20160735 | 59 | 0.7077 | 0.6808 | 0.5709 | 2.584e−05 | 2.191e−05 | +3.934e−06 | 53–64 | 12 |
| 20191014 | 137 | 0.6421 | 0.6347 | 0.4178 | 1.983e−05 | 3.217e−05 | −1.234e−05 | 134–140 | 7 |
| 20170794 | 163 | 0.6065 | 0.6134 | 0.6234 | 3.024e−05 | 3.164e−05 | −1.399e−06 | 159–167 | 9 |
| 20160735 | 228 | 0.5133 | 0.4685 | 0.4902 | 2.201e−05 | 1.881e−05 | +3.200e−06 | 224–235 | 12 |
| 20203947 | 90 | 0.4860 | 0.5400 | 0.3193 | 1.570e−05 | 9.212e−06 | +6.483e−06 | 87–93 | 7 |
| 20203947 | 61 | 0.4016 | 0.4646 | 0.3597 | 1.297e−05 | 1.038e−05 | +2.593e−06 | 58–63 | 6 |
| 20160735 | 9 | 0.3833 | 0.3265 | 0.3037 | 1.193e−05 | 1.166e−05 | +2.765e−07 | 7–11 | 5 |

### The TRUE population is degenerate

**30 of the 32** TRUE valleys sit at D1 = D2 = **1.0000 exactly** — they *are*
their series' minimum. Only two are not:

| series | valley | D1 | D2 | rel. prom. | block | len |
|---|---|---|---|---|---|---|
| 20205386 | 61 | 0.8805 | 0.9272 | 0.3074 | 60–63 | 4 |
| 20203947 | 185 | 0.9422 | 0.9483 | 0.6892 | 181–188 | 8 |

This is the same degeneracy item 19 found in the prominence distribution, and it
has the same consequence: the TRUE side of any depth threshold is decided
entirely by these two points, and the threshold's fate rests on where the
spurious ones fall relative to them.

---

## 6. Measurement B — baseline for the multi-mature cases

**The list in the brief needed the correction it anticipated.** Checked against
`split.yaml`:

| series | where it actually is |
|---|---|
| `20203947` | real, train ✔ |
| `s6b542eee` | **synthetic**, train — not one of the 35 real |
| `sbd6c6920` | **synthetic**, train — not one of the 35 real |

So among the **35 real train series there is exactly one** with more than one
labelled mature, not three. The other two are synthetic (the `s`-prefix is
`opaque_synthetic_id`), and synthetics are out of scope for this stage.

**Baseline for `20203947` under params-11, before any rule:**

```
detected blocks        (58,63)  (87,93)  (129,136)  (181,188)
labelled mature #1     122–144  (23 steps)            -> DETECTED by (129,136)
labelled mature #2     178–188  (11 steps) [UNSURE]   -> DETECTED by (181,188)
```

**Both labelled matures are detected today.** Two of the four blocks are
spurious (58–63 and 87–93, at D1 0.4016 and 0.4860) and two are true.

This is the number criterion (b) of the stage-2 gate would have been measured
against: any rule that suppresses blocks must keep **2 of 2** here, and the
second one is a genuine second mature at D1 = 0.9422 / D2 = 0.9483 — i.e. a
*true* valley that is not its series' deepest, only ~0.06 in D1 above the
deepest **spurious** valleys of other series and *below* three of them.

---

## 7. Measurement C — is the generating valley the deepest valley?

### 7.1 The recount

The prior claim was "30 of the 32 cases where the mature matches the label, the
generating valley is the deepest valley of the series", from params-10. Recount
under params-11, with `matches_label` defined exactly as item 19 defines it
(`pair_by_overlap` against the first labelled mature, |Δstart| ≤ 6 and
|Δend| ≤ 6, margin fixed at 6):

| | all 47 train series | 35 real train only |
|---|---|---|
| cases whose mature matches the label | **38** | 27 |
| generating valley is the deepest of **all** valley candidates | **36** | 26 |
| … the deepest of the **surviving** valleys | 36 | 26 |
| … at relative prominence exactly 1.0000 (item 19's proxy) | 36 | 26 |
| could not be attributed to a generating valley | 0 | 0 |

The 38 reproduces front 20a's gate (a) figure exactly, which corroborates that
this new driver is counting the same cases as the frozen instrument.

**36 of 38.** The two exceptions, named:

| series | valley | D1 | D2 | rel. prom. | deepest valley is |
|---|---|---|---|---|---|
| `20205386` | 61 | **0.8805** | **0.9272** | 0.3074 | 82 |
| `s6b542eee` (synthetic) | 16 | 0.9999 | 0.9999 | 0.9761 | 48 |

Restricted to the 35 real series there is **one** exception, `20205386`.

### 7.2 A caveat on the "30 of 32" this replaces

Item 19 measured that claim using **relative prominence == 1.0000** as the
stand-in for "deepest valley". Those are not the same quantity — prominence is
the *smaller of the two climbs* out of a valley, not the valley's depth — so
both columns are given above. On this data they happen to agree (36 either way),
but the agreement is a fact about this set, not an identity.

### 7.3 The six entries new since front 20a

All six were unverified. Checked individually — **all six generate their mature
from their series' deepest valley**, so none of them is an exception:

```
20150436  matches, Δ=(−2,−5)   valley  66 = deepest    DEEPEST
20160735  matches, Δ=(+5,+4)   valley 159 = deepest    DEEPEST
20170342  matches, Δ=(+1,−2)   valley  46 = deepest    DEEPEST
20180628  matches, Δ=(−1,−6)   valley  37 = deepest    DEEPEST
20180733  matches, Δ=(+6,−4)   valley 140 = deepest    DEEPEST
20207822  matches, Δ=(+2,−2)   valley  51 = deepest    DEEPEST
```

---

## 8. Separability test — the output

For D1 and D2 separately: the minimum over TRUE valleys against the maximum
over SPURIOUS ones. Separation exists iff min(TRUE) > max(SPURIOUS).

### Globally, over the 35 real train series (46 valleys, 32 true / 14 spurious)

| | min(TRUE) | max(SPURIOUS) | gap | separates? |
|---|---|---|---|---|
| **D1** | 0.8805 | **1.0000** | −0.1195 | **NO** |
| **D2** | 0.9272 | **1.0000** | −0.0728 | **NO** |

Full ranges: TRUE D1 0.8805–1.0000, SPURIOUS D1 0.3833–1.0000; TRUE D2
0.9272–1.0000, SPURIOUS D2 0.3265–1.0000. The spurious population **spans the
true one entirely**.

### Restricted to 20160735 alone (4 valleys, 1 true / 3 spurious)

| | min(TRUE) | max(SPURIOUS) | gap | separates? |
|---|---|---|---|---|
| **D1** | 1.0000 | 0.7077 | +0.2923 | **YES** |
| **D2** | 1.0000 | 0.6808 | +0.3192 | **YES** |

These are different questions and the answers are different. **Within
20160735 the separation is clean and wide** — its three spurious valleys sit at
D2 0.3265, 0.4685 and 0.6808, well clear of the true one at 1.0000. The front's
motivating case is, on its own, exactly as favourable as hoped. It is the other
34 series that refuse.

### The valleys that cause the overlap, named

Five spurious valleys sit at or above the lowest TRUE D1 (0.8805, `20205386`
v61); four sit at or above the lowest TRUE D2 (0.9272, same valley):

| series | valley | D1 | D2 | above lowest TRUE in | rel. prom. |
|---|---|---|---|---|---|
| `20171179` | 45 | 1.0000 | 1.0000 | D1 and D2 | 1.0000 |
| `20181046` | 26 | 1.0000 | 1.0000 | D1 and D2 | 1.0000 |
| `20205386` | 82 | 1.0000 | 1.0000 | D1 and D2 | 1.0000 |
| `20180628` | 72 | 0.9980 | 0.9984 | D1 and D2 | 0.3373 |
| `20180733` | 37 | 0.9303 | 0.9108 | D1 only | 0.7432 |

Two mechanisms, and they need separating:

**(i) `20171179` and `20181046` have no labelled mature at all.** The human
marked zero mature phases on these two series, so *every* block they emit is
SPURIOUS by the brief's classification rule — including the one anchored on the
series minimum. This is a real detector failure, but it is a *different* one
from the fragmentation 20(b) targets, and no depth rule can address it: the
offending valley is at the maximum depth by definition.

**(ii) `20205386` is the one that kills the rule outright.** Its three valleys:

| valley | D1 | D2 | class |
|---|---|---|---|
| 41 | 0.8687 | 0.9201 | SPURIOUS |
| **61** | **0.8805** | **0.9272** | **TRUE** |
| 82 | 1.0000 | 1.0000 | SPURIOUS |

The true valley is **sandwiched**: 0.0118 in D1 above one spurious valley and
0.1195 below another, within a single series. The series' deepest point produces
a spurious block while a shallower point produces the correct one. No threshold
on depth — global or per-series, on D1 or on D2 — can separate these three,
because depth orders them *wrongly*.

### Supplementary cuts (not a sweep — the same two statistics, two other cuts)

Excluding the two series with no labelled mature, so that only mechanism (ii)
remains:

| | min(TRUE) | max(SPURIOUS) | separates? | worst spurious |
|---|---|---|---|---|
| D1 | 0.8805 | 1.0000 | **NO** | `20205386` v82 |
| D2 | 0.9272 | 1.0000 | **NO** | `20205386` v82 |

And D2 recomputed against **physical zero** on the raw series `df['z_unfil']`,
at the same valley positions, to close out §3's caveat:

| | min(TRUE) | max(SPURIOUS) | separates? | worst spurious |
|---|---|---|---|---|
| D2_raw | 0.9533 | 0.9999 | **NO** | `20181046` v26 |

Neither cut produces a separation. The FAIL is not an artefact of the choice of
series, nor of the two no-label cases.

---

## 9. The two latent defects of `_amplitude_mature_bounds`

Neither was fixed; the prohibition was respected and `cyclophaser/` is
untouched. Both were checked **actively**, by recomputing the condition that
triggers them for every valley `find_mature_stage` evaluates — not by observing
that no exception was raised, which would be worthless for the second one.

* **`find_stages.py:152`** — `seg_prev.index[violations_prev[-1] + 1]` overruns
  the index when the last element of `seg_prev` violates, i.e. when the valley
  itself is above `level_prev`, i.e. when `amp_prev < 0`. Raises `IndexError`
  (loud).
  **Fired: 0 times.**
* **`find_stages.py:159–160`** — `seg_next.index[violations_next[0] - 1]`
  evaluates `index[-1]` when the *first* element violates, i.e. when
  `amp_next < 0`, returning `next_z_peak` — a maximally wrong window — **with no
  error**. This is the silent one.
  **Fired: 0 times.**

Checked over all 47 train series (real and synthetic), every valley with both
bounding peaks, not only the 46 generating ones. Neither condition arises under
params-11, so no number in this report is contaminated by either defect. They
remain latent and remain unfixed.

---

## 10. Prohibitions — verified, not assumed

| | |
|---|---|
| `git diff develop-v2.1 -- cyclophaser/` | **empty** |
| `git diff develop-v2.1 -- research/labels/diagnostics/item19/item19_core.py` | **empty** — not edited, and not imported either |
| threshold sweep | none. No grid, no optimisation, no search. Every figure here is a min or a max over a fixed table. |
| rule proposed or implemented | none |
| test split | never read. `read_split()["test"]` appears in no file in this directory. |

---

## 11. The declared prediction, against the result

Declared in the brief **before** measuring, and reported here without
reinterpretation:

> FAIL on global separability, confidence ~60%.

**The prediction was correct.** FAIL, on both D1 and D2.

Two parts of the stated *reasoning* also held: the true valleys that are their
series' deepest sit at D = 1.00 by construction (30 of 32 do), so they do not
decide the threshold; and the decision falls to the rare points.

One part of the reasoning did not hold, and the discrepancy is the most useful
thing this stage found. The brief expected 20160735's own spurious valleys to be
the ones that refuse to fall below the threshold. **They are not**: 20160735
separates cleanly and widely, and its spurious valleys land at D2 ≤ 0.6808 —
comfortably inside the brief's own "clearly PASS" bound of D2 ≤ 0.85. The
genuine second mature among the real series (`20203947` #2) sits at D2 = 0.9483,
within rounding of the brief's PASS bound of ≥ 0.95.

**So both conditions the brief named as the clearly-PASS scenario were very
nearly met — and the front fails anyway**, on a population the PASS scenario did
not anticipate: spurious valleys that are *themselves* their series' deepest
point (`20171179` v45, `20181046` v26, `20205386` v82, all at exactly 1.0000).
Depth cannot reject a valley that is the minimum. In `20205386` depth orders the
true and spurious valleys backwards outright.

This is a fact about the *premise* of a depth rule, not about the choice of
threshold, which is why no sweep was run and why running one would not change
the answer.

---

## 12. Status

Stage 1 complete. The separability test is **FAIL** globally and **PASS** for
20160735 in isolation.

Committed and pushed on `research/item20b-depth-rule`. **Not merged, no PR.**
Whether the front proceeds to stage 2, is narrowed, or is closed is Danilo's
decision.
