# Item 30, part 2 — separability of a late plateau boundary from a right one

**Measurement only.** No rule and no parameter is proposed, and no threshold is
swept beyond reporting the valid interval. No line under `cyclophaser/` changed:
`git diff develop-v2.1 -- cyclophaser/` is empty.

The question: when the plateau boundary falls after the peak, does any quantity
of the pre-incipient map separate the labelled cases where the boundary is
**late** (L) from those where it is **right** (K), without touching the cases
where the overwrite is correct (P)?

Predictions are in `PREDICTIONS_part2.md`, committed in `2ded3af` before the run
and judged below without rewriting.

## Setup

- **Branch.** `research/item30-plateau-overwrite`, after merging `develop-v2.1`
  (`a860b36`, which brings item 30a).
- **Config and environment.** `params-14`; the dedicated `cyclophaser` env,
  python 3.12.14, numpy 2.5.3, scipy 1.18.0, pandas 3.0.5.
- **Code actually loaded.** `cyclophaser.__file__` and `layer_inspector.__file__`
  are asserted in-process to be this checkout.
- **Pipeline.** The ribbon uses develop's `build_args_periods`. It is asserted
  equal, on every run, to the `args_periods` captured inside `get_periods`, and
  step 6 is asserted equal to `get_periods`.

**Step 0a.** After the merge, the part-1 measurement (`002078b`) was re-run with
develop's inspector and without the args workaround. Every output was identical:

- the swell per-track table and gate JSON, byte for byte;
- the census CSV, byte for byte;
- the evaluator's 47 | 7 output.

Suite: 1371 passed, 0 failed. The code change for this step landed in `ce1b74b`
by mistake; `011216d` records it.

**Exclusions.**

- **TEST series:** the 16 of the split and the 3 of the batch are excluded
  everywhere. Their labels are never read: `train_labels` drops them by id.
- **Swell:** 20203389 is excluded as well, leaving a universe of 196.

### Definitions

The pre-incipient map is step 5 of the ribbon.

- **E:** the first intensification block of step 5 that starts before the
  boundary. If there is none, the series has no value.
- **c1:** (z[start] − z[end]) / (z_max − z_min) over E. This is D2 as
  `intensification_min_depth` computes it, with the z range from
  `layer_inspector._z_range` (the item-30a transcription), on the filtered `z`.
- **c2:** c1 / duration of E. The duration is counted in samples,
  **end + 1 − start**. The brief left the step count open, and this reading
  matches c3's denominator.
- **c3:** (min(end + 1, boundary) − start) / (end + 1 − start).

## Groups, and P

- **L (late boundary):** 20120297, 19940445, 19810854. E is defined in all 3.
- **K (right boundary):** 19790612, 19860380, 19870927. E is defined in 2;
  **19790612 has no value**, because its step-5 map is `decay` only and its peak
  is at index 0.
- **P:** every train series outside the signal in which E exists. That is
  **21 = 13 real series of the split + 8 synthetic**, and none from the batch:
  the batch's C case, 20050893, has boundary 0.

For a train series outside the signal, "E exists" is the same condition as "the
overwrite erases intensification". The 21 are exactly the 13 + 8 of part 1's
census.

**All 21 are partial erasures (c3 < 1)**. Their c3 runs from 0.033 to 0.529;
the largest is 20180608. None is total.

Per-series values are in `separability_train_params14.csv`, and the criterion
detail in `separability_criterion.json`.

## Step 1 — the three candidates on the training series

Values in ascending order, each with its group:

- **c1:** K 0.160 · **L 0.209** · K 0.226 · P 0.396 … P 0.839 · **L 0.852** ·
  P 0.872 … P 0.890 · **L 0.890** · P 0.893 … P 1.000.
- **c2:** P 0.0066 … P 0.0177 · **L 0.0182** · P 0.0186 · P 0.0198 · K 0.0200 ·
  P 0.0214 · K 0.0226 · P 0.0256 … P 0.0339 · **L 0.0348** · P 0.0437 …
  P 0.0499 · **L 0.0568** · P 0.0600 · P 0.0684.
- **c3:** P 0.033 … P 0.345 · P 0.529 · then K 1 · K 1 · **L 1 · L 1 · L 1**.

| candidate | (i)+(ii): L vs K | (iii): P off L's side | passes | valid thresholds | tightest margin |
|---|---|---|---|---|---|
| c1 | **fails**: L straddles K (20120297 at 0.209, between K's 0.160 and 0.226) | fails | **no** | none (empty in both orientations) | −0.731 (L low), −0.791 (L high) |
| c2 | **fails**: L straddles K (19810854 at 0.0182 is below both K; the other two are above) | fails | **no** | none | −0.050 (both orientations) |
| c3 | **fails**: tie, L = K = 1 | **holds** for "L high": every P is below 1 | **no** | none; the interval collapses to [1, 1) | 0 against K; 0.471 against P |

**Q1 — CONFIRMED.** c3 does not separate L from K: c3 = 1 in all 3 of L and in
19860380 and 19870927.

**Q2 (weak) — does not apply.** Its antecedent is false: no candidate separates.
Neither c1 nor c2 satisfies even (i) and (ii) on its own.

**Q3 — no prediction.** No candidate passes the full criterion.

### What c3 does separate

c3 separates **{L ∪ K}** from **P**, by a margin of 0.471: c3 = 1 in all 5 with
a defined value, and at most 0.529 in P. In these data that is the signal
itself, restated. Whenever the boundary falls after the peak, it also falls
after the end of E, because E ends before the peak. So c3 = 1 tells a case
where H erases a whole block from one where it trims the start of one. It does
not tell whether the whole block should have been erased.

### Labels next to the values (train, from `train_labels`)

- **L:** the label's intensification starts at 3, 8 and 2, well before the
  boundary (62, 38 and 10). The label's incipient ends at those same indices.
- **K with a value:** 19860380 and 19870927 are labelled `incipient > decay`,
  with no intensification. Their incipient ends at 14 and 64, against
  boundaries of 12 and 66.
- **P:** the labelled incipient end is close to the boundary in most series
  (see part 1's census).

On the candidates that reach L and K, the two groups look the same.

## Step 2 — external check on the swell (reporting only)

These are the 17 swell tracks with the signal: 8 bad with the pattern and 9 good
with the signal, out of the 196. Per-track values are outside the repo
(`cyclophaser_swell_tracks_test/diag_item30/separability_swell17_params14.csv`).

- **No valid threshold exists** for any candidate, so no track can be placed on
  either side of one. The step reduces to reporting the values.
- **E is defined in 10/17**: all 8 bad, and 2 good (19810854, 19861089).
  It is undefined in the other 7 good tracks, whose peak is at index 0 or 1.
- **c3 = 1 in all 10 with a value**, bad and good alike.
- **c1:** bad 0.055–0.852; the 2 good 0.890 and 0.896.
- **c2:** bad 0.011–0.070; the 2 good 0.018 and 0.032.
- **The marks are not labels.** 19810854 was marked good, but its label has
  the intensification and the mature that the detector's final map lacks. It is
  in L.

**The 11 of the 17 not drawn for the batch** (candidates for a validation set):

- bad (4): 19900808, 19940737, 19960808, 20000821;
- good (7): 19830376, 19840325, 19861089, 19880329, 19910227, 20030213,
  20204384.

Six of those 7 good tracks, all except 19861089, have no E. They could validate
only the "no value" branch.

## What this establishes

On this training set, none of the three pre-incipient quantities separates a
late boundary from a right one. c1 and c2 put L on both sides of K. c3 ties them.
The one quantity that clears P, c3, only restates the signal.

With 3 L cases and 2 K cases carrying a value, this is a small sample. The
result is **no separation found**, not proof that no separation exists.

## Files

- **`separability.py`:** steps 1 and 2. The per-track swell table goes outside
  the repo.
- **`separability_train_params14.csv`**, **`separability_criterion.json`**,
  **`separability_train_output.txt`:** the train outputs.
