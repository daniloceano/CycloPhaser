# Front D, stage 0 — incipient census on the TRAIN split

**Status: front D CLOSED with no mechanism and no parameter change, 2026-09-23.**
Nothing in the package changed; no PR was opened. Stage 0's measurements stand
exactly as emitted — see **§10** for the later reading and the corrections to
the step-2 criterion's *design*, which sit alongside the originals, not over them.

Branch `research/frontD-stage0-census`, from `develop-v2.1` @ `f901b76`.
Config `research/labels/configs/cyclophaser_params-13.yaml`. Run in the dedicated
`cyclophaser` conda environment
(`/Users/danilocoutodesouza/miniconda3/envs/cyclophaser/bin/python`), with
`cyclophaser` resolving to the **working tree**
(`.../CycloPhaser/cyclophaser/__init__.py`), not the 2.0.0 wheel in
`site-packages` — verified by printing `cyclophaser.__file__` before measuring.

**The test split was never read.** `census.py:_assert_train_only` raises before
any detection runs if a single id from `split.yaml`'s `test` list reaches the
detector, and `anchoring.py` asserts the same for its C1 subset. No label, no
series and no figure for any test id was produced by this stage. The one
exposure that did occur is recorded in `docs/future_work.md` (see
"Exposure on the record", below) and it is not a measurement.

The question this stage answers is exactly one: **does the short-incipient
symptom exist in the training set?** It proposes no mechanism and no parameter
change, for any result, by instruction.

---

## 1. Hash verification — both PASS, measured before anything else ran

Driver: `verify_hashes.py`; full output `verify_hashes.txt`.

| what | declared / recorded | measured | |
|---|---|---|---|
| `cyclophaser_params-13.yaml`, file sha256 | `c1ab8ce0…6e483973` | `c1ab8ce0…6e483973` | **MATCH** |
| 12 frozen synthetic series, value sha256 vs `manual_labels.yaml` | — | — | **12/12 MATCH** |
| 51 real calibration tracks, value sha256 vs `manual_labels.yaml` | — | — | **51/51 MATCH** |

The registry checked against is `research/labels/manual_labels.yaml`'s
per-record `series_sha256`, which is the repo's own record of what each label was
written against. It hashes the **parsed float64 values**
(`labels_core.series_sha256`), not the CSV bytes, so it is the value hash that
decides; that is the same check `evaluate_against_labels.py` uses to void a stale
label. The real tracks are included because the census reads them too.

---

## 2. The "short" floor, declared before the cases were listed

```
short  =  0 < N_det < min(N_lab)  over the TRAIN REAL series whose label has N_lab > 0
```

**min(N_lab) over the 17 such real train series = 4.** So a detected incipient
phase is "short" iff `0 < N_det < 4`, i.e. `N_det ∈ {1, 2, 3}`. The same floor is
applied to the synthetic series, since the definition names the real series as
its source.

---

## 3. Census — TRAIN, 35 real + 12 synthetic, under params-13

Driver: `census.py`; full output `census.txt`; machine-readable `census.json`.

`N_det` = leading `incipient` steps in the detected `periods` (0 = no incipient
phase), read exactly as `evaluate_against_labels.detected_incipient_end` reads
it. `N_lab` = where the manual label ends the incipient phase; `0` = the label
says the series has none; **`amb`** = the labeller declined to place the boundary
— a third state, deliberately *not* folded into 0. `defI` = does
`sign(z[1]−z[0])` differ between the raw and the filtered series
(`docs/future_work.md` item 8(d), defect I)?

### 3.1 Real (35)

| id | n | N_det | N_lab | kind | tol | \|Δ\| | defI | class |
|---|---:|---:|---:|---|---:|---:|---|---|
| 20150069 | 66 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20150436 | 112 | 20 | 16 | boundary | 4 | 4 | no | — |
| 20150528 | 51 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20150532 | 107 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20150656 | 160 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20160587 | 79 | 0 | 26 | boundary | 1 | 26 | no | **C2** |
| 20160735 | 259 | 0 | 19 | boundary | 5 | 19 | no | **C2** |
| 20170154 | 124 | 6 | 6 | boundary | 2 | 0 | no | — |
| 20170342 | 146 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20170409 | 169 | 6 | 6 | boundary | 2 | 0 | no | — |
| 20170520 | 58 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20170760 | 59 | 0 | amb | ambiguous | 0 | — | no | — |
| 20170794 | 224 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20171179 | 62 | 0 | 11 | boundary | 1 | 11 | no | **C2** |
| 20180170 | 69 | 8 | amb | ambiguous | 1 | — | **yes** | — |
| 20180263 | 57 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20180300 | 59 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20180608 | 117 | 38 | 37 | boundary | 1 | 1 | **yes** | — |
| 20180628 | 94 | 0 | 9 | boundary | 1 | 9 | no | **C2** |
| 20180733 | 257 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20180759 | 88 | 4 | 4 | boundary | 1 | 0 | **yes** | — |
| 20181046 | 30 | 0 | 9 | boundary | 1 | 9 | no | **C2** |
| 20190325 | 167 | 9 | 10 | boundary | 1 | 1 | **yes** | — |
| **20190397** | 56 | **2** | 8 | boundary | 1 | 6 | **yes** | **C1** |
| 20190639 | 180 | 13 | 25 | boundary | 5 | 12 | no | — |
| 20190870 | 129 | 10 | 12 | boundary | 2 | 2 | no | — |
| 20190879 | 79 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20191014 | 206 | 9 | 0 | none | 0 | 9 | **yes** | — |
| 20191104 | 118 | 0 | 0 | none | 0 | 0 | no | C3 |
| **20191155** | 93 | **1** | 0 | none | 0 | 1 | no | **C1** |
| 20201245 | 98 | 0 | 0 | none | 0 | 0 | no | C3 |
| 20202023 | 78 | 0 | 11 | boundary | 1 | 11 | no | **C2** |
| 20203947 | 242 | 12 | 38 | boundary | 5 | 26 | no | — |
| 20205386 | 100 | 4 | 5 | boundary | 1 | 1 | no | — |
| 20207822 | 162 | 0 | 0 | none | 0 | 0 | no | C3 |

### 3.2 Synthetic (12)

| id | n | N_det | N_lab | kind | tol | \|Δ\| | defI | class |
|---|---:|---:|---:|---|---:|---:|---|---|
| s0596ea57 | 66 | 10 | 14 | boundary | 3 | 4 | n/a | — |
| **s46657891** | 66 | **3** | 3 | boundary | 1 | 0 | no | **C1** |
| s4e7ff65c | 66 | 5 | 5 | boundary | 1 | 0 | n/a | — |
| s5b8aa46f | 66 | 0 | 0 | none | 0 | 0 | no | C3 |
| s5dcc0f79 | 66 | 5 | 4 | boundary | 1 | 1 | n/a | — |
| **s6b1e8245** | 66 | **2** | 3 | boundary | 1 | 1 | no | **C1** |
| **s6b542eee** | 66 | **2** | 2 | boundary | 1 | 0 | no | **C1** |
| s8001f17b | 66 | 0 | 0 | none | 0 | 0 | no | C3 |
| s9ddbc53c | 66 | 4 | 3 | boundary | 1 | 1 | no | — |
| **sbceec644** | 66 | **2** | 3 | boundary | 1 | 1 | no | **C1** |
| sbd6c6920 | 66 | 4 | 5 | boundary | 1 | 1 | no | — |
| **scfcf1387** | 66 | **2** | 3 | boundary | 1 | 1 | **yes** | **C1** |

`defI = n/a` on three synthetic cases means `z[1]−z[0]` is exactly 0 in the raw
or the filtered series, so there is no sign to disagree about. It is recorded as
its own state rather than being allowed to read as agreement.

### 3.3 Counts

| | C1 (short) | C2 (N_det=0, N_lab>0) | C3 (N_det=0, N_lab=0) | neither |
|---|---:|---:|---:|---:|
| **real (35)** | **2** | **6** | **14** | 13 |
| **synthetic (12)** | **5** | **0** | **2** | 5 |

* **C1 real:** `20190397` (N_det=2), `20191155` (N_det=1).
* **C2 real:** `20160587`, `20160735`, `20171179`, `20180628`, `20181046`,
  `20202023`. *Counted and listed only, per instruction — not investigated, and
  nothing is proposed about them here.*
* **C3 real:** `20150069`, `20150528`, `20150532`, `20150656`, `20170342`,
  `20170520`, `20170794`, `20180263`, `20180300`, `20180733`, `20190879`,
  `20191104`, `20201245`, `20207822`.
* **C1 synthetic:** `s46657891`, `s6b1e8245`, `s6b542eee`, `sbceec644`,
  `scfcf1387`. **C3 synthetic:** `s5b8aa46f`, `s8001f17b`.

**Answer to the stage-0 question: yes, the symptom exists in TRAIN** — 2 real
series and 5 synthetic ones carry a detected incipient phase shorter than the
shortest labelled one. It is, however, much rarer among the reals (2/35) than the
refusal it sits next to (6/35).

---

## 4. Step 2 — artefact vs real short phase, C1 only

Driver: `anchoring.py`; full output `anchoring.txt`; `anchoring.json`. Verdict
rule exactly as frozen in the brief; margin fixed at 6; each label's
`tolerance_idx` printed beside it as information only.

| id | L=N_det | N_lab | tol | (a) \|Δ\|≤6 | (b) reading | **verdict** |
|---|---:|---:|---:|---|---|---|
| 20190397 | 2 | 8 | 1 | PASS (Δ=6) | indistinguishable | **INCONCLUSIVE** |
| 20191155 | 1 | 0 | 0 | PASS (Δ=1) | n/a (L=1) | **INCONCLUSIVE** |
| s46657891 | 3 | 3 | 1 | PASS (Δ=0) | **time-anchored** | **REAL SHORT PHASE** |
| s6b1e8245 | 2 | 3 | 1 | PASS (Δ=1) | indistinguishable | **INCONCLUSIVE** |
| s6b542eee | 2 | 2 | 1 | PASS (Δ=0) | indistinguishable | **INCONCLUSIVE** |
| sbceec644 | 2 | 3 | 1 | PASS (Δ=1) | indistinguishable | **INCONCLUSIVE** |
| scfcf1387 | 2 | 3 | 1 | PASS (Δ=1) | indistinguishable | **INCONCLUSIVE** |

**Verdicts: ARTEFACT 0, REAL SHORT PHASE 1, INCONCLUSIVE 6** (real: 0 / 0 / 2;
synthetic: 0 / 1 / 4).

### 4.1 Per-cut detail

`abs_end` = the detected incipient end re-expressed in the ORIGINAL index
(`k + N_det_cut`). "time?" = `|abs_end − L| ≤ 1`; "edge?" = incipient vanished
or `|N_det_cut − L| ≤ 1`.

| id | k | N_det_cut | abs_end | time? | edge? | removed chunk holds |
|---|---:|---:|---:|---|---|---|
| 20190397 | 1 | 1 | 2 | True | True | global max (filtered) |
| s46657891 | 1 | 2 | 3 | True | True | global max |
| s46657891 | 2 | 1 | 3 | True | **False** | global max |
| s6b1e8245 | 1 | 1 | 2 | True | True | neither extremum |
| s6b542eee | 1 | 1 | 2 | True | True | neither extremum |
| sbceec644 | 1 | 1 | 2 | True | True | global max |
| scfcf1387 | 1 | 1 | 2 | True | True | neither extremum |

Known limitation, as declared: a cut that removes the global min or max of the
filtered series changes the normalisation every relative threshold is measured
against. It happened on 3 of the 7 series (`20190397`, `s46657891`, `sbceec644`,
all at the global **max**, which sits at index 0 in each) and is flagged per cut
above rather than corrected.

### 4.2 The step-2 instrument has no discriminating power at L = 2

This is a property of the test as specified, not of the data, and it drives 5 of
the 7 verdicts — so it is reported rather than worked around.

At `L = 2` the only valid cut is `k = 1`. If the detector then returns
`N_det_cut = 1`, both readings are satisfied **simultaneously and by
arithmetic**: `abs_end = 1 + 1 = 2 = L` (time-anchored, within ±1) *and*
`|N_det_cut − L| = 1 ≤ 1` (edge-anchored, duration ≈ L). The two criteria the
decision rule is built to separate collapse onto the same observation. That is
exactly what happened on all five `L = 2` series. `s46657891` is the only case
that discriminated, and only because `L = 3` admits a second cut: at `k = 2` the
end stayed at absolute index 3 while the duration fell to 1, which is
time-anchoring and not edge-anchoring.

I did not classify these five as "mixed" — they are not a mixture across `k`,
they are a single observation both labels fit — so the frozen rule routes them
to INCONCLUSIVE, which is where they belong.

### 4.3 ARTEFACT was unreachable on this set

> **Corrected in §10.1:** this is too weak. ARTEFACT was unreachable **by
> construction, in any split, for any series** — the margin 6 exceeds the
> "short" floor 4, so criterion (a) cannot fail on a short detection whose
> label says "no incipient". The paragraph below stands as originally written.

`ARTEFACT` requires **(a) to fail**. All 7 C1 series **passed** (a). So no C1
series in TRAIN could have been classified as an artefact under the frozen rule,
whatever (b) had shown. The stage returns zero artefacts because none of the
short detections is far from its label, not because the anchoring test cleared
them.

### 4.4 One case where (a) passes but the agreement is not what it looks like

`20191155` has `N_lab = 0`: the label says the series has **no incipient phase at
all**, and the detector produced one of length 1. The frozen rule reads `N_lab`
as the number 0, so `|1 − 0| = 1 ≤ 6` and (a) PASSES. Arithmetically correct;
but this is a refusal-type disagreement (phase exists / does not exist) being
scored as a 1-step timing error. `evaluate_against_labels.py` keeps those two
accountings separate for exactly this reason. Recorded, not adjusted —
the rule was frozen before measurement and I am not moving it afterwards.

---

## 5. Evaluator output, verbatim — and the constant baseline that is not in it

`evaluate_against_labels.py --config …/cyclophaser_params-13.yaml` (train only),
full output in **`evaluate_params13_train.txt`**, reproduced here:

```
==========================================================================
Incipient boundary vs manual labels   (63 usable label(s))
config: research/labels/configs/cyclophaser_params-13.yaml
against: current
==========================================================================

  TRAIN · real   (35 labelled)
   ── incipient boundary ──
    boundary labels    17   hit within margin   8  ( 47.1%)
    raw distance      MAE   4.82   worst     26   (over 11 comparable)
    refusal           detector found no incipient phase on 6 of those 17
                      label says none:  16, detector agreed on 14 ( 87.5%)
                      label ambiguous:   2, detector found none on 1
   ── whole phase sequence ──
    sequence          19 of 35 match ( 54.3%); 16 differ in phases or order
    boundaries        34 of 45 within their own margin ( 75.6%)
    not sure          3 boundary/ies the labeller declined to place, excluded from the rate above
      phase              n   hit    MAE  worst
      intensification    8   75.0%   3.12     12
      mature            18   66.7%   2.22      7
      decay             18   88.9%   2.17      7
      residual           1    0.0%   3.00      3

  TRAIN · synthetic   (12 labelled)
   ── incipient boundary ──
    boundary labels    10   hit within margin   9  ( 90.0%)
    raw distance      MAE   1.00   worst      4   (over 10 comparable)
    refusal           detector found no incipient phase on 0 of those 10
                      label says none:   2, detector agreed on 2 (100.0%)
                      label ambiguous:   0, detector found none on 0
   ── whole phase sequence ──
    sequence          12 of 12 match (100.0%); 0 differ in phases or order
    boundaries        43 of 46 within their own margin ( 93.5%)
      phase              n   hit    MAE  worst
      intensification   14   92.9%   0.93      4
      mature            13   84.6%   1.00      2
      decay             15  100.0%   0.67      2
      residual           4  100.0%   1.25      2

  TRAIN · ALL   (47 labelled)
   ── incipient boundary ──
    boundary labels    27   hit within margin  17  ( 63.0%)
    raw distance      MAE   3.00   worst     26   (over 21 comparable)
    refusal           detector found no incipient phase on 6 of those 27
                      label says none:  18, detector agreed on 16 ( 88.9%)
                      label ambiguous:   2, detector found none on 1
   ── whole phase sequence ──
    sequence          31 of 47 match ( 66.0%); 16 differ in phases or order
    boundaries        77 of 91 within their own margin ( 84.6%)
    not sure          3 boundary/ies the labeller declined to place, excluded from the rate above
      phase              n   hit    MAE  worst
      intensification   22   86.4%   1.73     12
      mature            31   74.2%   1.71      7
      decay             33   93.9%   1.48      7
      residual           5   80.0%   1.60      3

  TEST split held out (16 series). Pass --test to score it, once.
```

### 5.1 Divergence from the brief: there is no constant-baseline line to attach

The brief asks for this output "including the constant baseline line".
**`evaluate_against_labels.py` computes no baseline of any kind** — verified by
reading it in full and by `grep -i baseline` over the file at `f901b76`; the word
does not occur. The "constant modal-sequence baseline scores 16/47" quoted in
`docs/future_work.md` item 19 is (i) a different quantity — about the whole phase
**sequence**, not the incipient boundary — and (ii) produced by that front's own
diagnostics, not by this script. I did not modify the evaluator ("rode, sem
alterar"), and I did not invent a line for it.

Instead, the baseline is computed separately, in **`constant_baseline.py`**
(full output `constant_baseline.txt`, `constant_baseline.json`), and is
attributed to that file and nowhere else. It scores "ignore the series, always
answer N" — including N = *no incipient phase* — against the same train labels
through `labels_core.score_labels`, so baseline and detector are measured with
one ruler:

| TRAIN | best constant | baseline hit | baseline MAE | **detector** hit | detector MAE |
|---|---|---:|---:|---:|---:|
| real | 10 | 6/17 (35.3%) | 7.53 | **8/17 (47.1%)** | **4.82** |
| synthetic | 4 | 8/10 (80.0%) | 1.90 | **9/10 (90.0%)** | **1.00** |
| all | 4 | 12/27 (44.4%) | 7.52 | **17/27 (63.0%)** | **3.00** |

The detector beats the best constant on all three, by 2 series on the reals.
Note the constant "always answer *no incipient phase*" scores 0/17 on the
boundary labels while agreeing on 16/16 of the `none` labels — which is why the
refusal accounting is kept separate from the hit rate, and why a single headline
number would be misleading here.

### 5.2 Replay check

`constant_baseline.py` feeds the census's own `N_det` values back through
`score_labels` and reproduces the evaluator exactly — 8/17 real (47.1%, MAE
4.82, worst 26), 9/10 synthetic, 17/27 all. The census is therefore a verified
replay of the evaluator's detection, not an independent re-derivation that might
be reading `periods` differently.

---

## 6. Declared predictions, scored

Both were declared before any measurement.

| | prediction | measured | |
|---|---|---|---|
| **P1** | C1 ≥ 2 among the real train series (~55%) | C1 = **2** | **CORRECT** |
| **P2** | C2 ≥ 2 among the real train series (~50%) | C2 = **6** | **CORRECT** |

P1 landed exactly on its boundary: one series fewer and it would have failed.

---

## 7. Figures

One per C1 series — raw and filtered vorticity over the opening 30 steps, with
`N_det`, `N_lab` (or a note that the label says none) and the incipient end at
each cut `k` in absolute index, with the removed chunk shaded:

`fig_20190397_opening.png`, `fig_20191155_opening.png`,
`fig_s46657891_opening.png`, `fig_s6b1e8245_opening.png`,
`fig_s6b542eee_opening.png`, `fig_sbceec644_opening.png`,
`fig_scfcf1387_opening.png`.

---

## 8. What this stage does NOT say

By instruction, no mechanism and no parameter change is proposed, for any
result. In particular: the 6 C2 refusals are counted and listed only; nothing
here explains defect I's role, even though 1 of the 2 real C1 series and 1 of the
5 synthetic ones carry the flag; and the 5 INCONCLUSIVE verdicts at `L = 2` are
inconclusive because the test cannot separate the two hypotheses at that length,
which is a fact about the instrument that a later stage would have to fix before
the question can be answered on those series.

## 9. Open for Danilo

1. **Step 2 cannot discriminate at `L = 2`** (§4.2), and 5 of 7 C1 series have
   `L = 2`. If front D continues on this route, the anchoring test needs a
   criterion that separates the two hypotheses at short `L` — or the ±1
   tolerances need to be tightened — before it can return anything but
   INCONCLUSIVE there.
2. **`ARTEFACT` was unreachable on TRAIN** (§4.3), since it requires (a) to fail
   and no C1 series failed (a). The rule is fine; the training set simply
   contains no short detection that is also far from its label. `20150646`, the
   case that motivated front D, is in TEST and was not looked at.
   **Corrected in §10.1:** the rule is *not* fine and the training set is not
   the reason — ARTEFACT was unreachable by construction, in any split.
3. **`N_lab = 0` scored as a 1-step error on `20191155`** (§4.4) — decide whether
   a future gate should route "label says no incipient" to the refusal
   accounting instead of the distance.
4. **The constant baseline is not in the evaluator** (§5.1). If it should be a
   standing line of `evaluate_against_labels.py`, that is a change to commission;
   it was not made here.

---

## 10. Leitura posterior e correções (front D closing, 2026-09-23)

Stage 0's execution was verified independently by the technical lead: the
evaluator and constant-baseline outputs reproduced identically, and `census.json`
differed only by floating-point noise in the 15th–16th digit of `d_filt_t0`, with
no change of sign or of any count. **The execution is correct.** The defect is in
the **design of the step-2 criterion**, which came from the commissioning brief.

Nothing measured is restated here. Every number, table and verdict in §1–§9
stands exactly as emitted by the frozen rule; this section is a **later reading
placed alongside them**, not a revision of them.

### 10.1 ARTEFACT was unreachable BY CONSTRUCTION, not merely "on TRAIN"

§4.3 and §9.2 say ARTEFACT was unreachable *on the training set*. That is too
weak. **It was unreachable in any split, for any series, by arithmetic** —
`params-13` and the data never enter the argument:

* "short" is defined as `0 < N_det < 4`, so `N_det ∈ {1, 2, 3}`;
* hypothesis D is that the label has **no** incipient phase, i.e. `N_lab = 0`;
* then `|N_det − N_lab| = N_det ≤ 3 < 6`, so criterion **(a) always passes**;
* ARTEFACT required (a) to **fail**, i.e. `|N_det − N_lab| ≥ 7`. With
  `N_det ≤ 3` and `N_lab ≥ 0` that can only happen when `N_lab ≥ N_det + 7` —
  the label carrying an incipient phase at least 7 steps **longer** than the
  detected one. **That is the opposite of the hypothesis the test was built to
  confirm.**

The margin (6) is larger than the "short" floor (4), so the two criteria are
mutually exclusive on the very population the test selects.

**Consequence, recorded:** had `20150646` been spent directly on this test, it
would have returned INCONCLUSIVE or REAL SHORT PHASE **regardless of the truth
of the matter**. The test set would have been burned for a verdict that carried
no information. It was not spent.

### 10.2 The anchoring test (b) discriminates only at L = 3

§4.2's `L = 2` analysis stands and generalises. With cuts restricted to `k < L`
and a ±1 tolerance on both readings, and with `L ≤ 3` for any series that can be
C1 at all:

| L | valid k | outcome |
|---|---|---|
| 1 | none | (b) does not apply |
| 2 | k = 1 | the two hypotheses **collapse**: `N_det_cut = 1` satisfies time-anchored (`abs_end = 2 = L`) and edge-anchored (`\|N_det_cut − L\| = 1 ≤ 1`) simultaneously |
| 3 | k = 1, 2 | **the only discriminating case**, via `k = 2` |

So across the whole "short" population, only `L = 3` can produce a discriminating
(b) reading at all.

**And the one discriminating verdict is weak.** `s46657891` (the sole REAL SHORT
PHASE) has the global maximum of its filtered series at **index 0**, so **both**
its cuts (`k = 1` and `k = 2`) removed it, changing the normalisation that every
relative threshold is measured against. Its verdict rests on the one series whose
cuts also perturbed the quantity the detector normalises by.

### 10.3 Attribution of the defect

Recorded explicitly, because a later reader should not have to infer it:

* **The step-2 defect is in the brief's design, written by the technical lead** —
  specifically the fixed margin 6 being larger than the "short" floor 4 (§10.1),
  and `k < L` with ±1 tolerances (§10.2). The execution followed the frozen rule
  correctly and is not at fault.
* **The premise that `evaluate_against_labels.py` already carried a constant
  baseline was likewise an error of the brief** (§5.1). The script computes no
  baseline of any kind.

### 10.4 `20191155` is a CATEGORICAL disagreement, not a 1-step timing error

The original row stands: `N_det = 1`, `N_lab = 0`, `|Δ| = 1`, class **C1**,
verdict **INCONCLUSIVE**.

Later reading: this is a **categorical** disagreement — the detector produced an
incipient phase, the label says the series has none. It is not a timing error of
one step. `evaluate_against_labels.py` already accounts for it that way (it falls
under "label says none", where the detector did **not** agree — the 14 of 16 in
§5). The error was confined to the brief's criterion (a), which subtracts the two
numbers as though a phase's existence and a phase's end were the same quantity.

### 10.5 The 2×2 of the real TRAIN series

The 2 ambiguous labels (`20170760`, `20180170`) are excluded — the labeller
declined to place the boundary, so neither column applies. 33 series remain.
**Counts verified against `census.json` before being written.**

| | label HAS incipient | label has NO incipient |
|---|---:|---:|
| **detector HAS incipient** | 11 | **2** — `20191155` (L=1), `20191014` (L=9) |
| **detector has NO incipient** | **6** (refusal) | 14 |

Reading:

* **Symptom D proper** (a *short* incipient where the label has none): **1 real
  series**, `20191155`.
* **`20191014`**: an incipient where the label has none, but **not short**
  (`L = 9`). Already a known bad case of front A.
* **`20190397`** (the other C1): a **different** symptom — the label's incipient
  runs to 8 and the detector closes it at 2. An incipient that **ends too early**,
  not one that should not exist.
* **The dominant incipient failure in TRAIN is refusal**: **6 of the 17** real
  series whose label carries an incipient phase get none from the detector.

### 10.6 Predictions — unchanged, with one note

* **P1 — stays CORRECT.** `C1 = 2` under the frozen definition. Note: C1 **mixed
  two different symptoms** (§10.5); symptom D proper has **1** real series.
* **P2 — stays CORRECT.** `C2 = 6`.
* **"`20150646` will give ARTEFACT"** — recorded as **DECLARED, NO VALID TEST**.
  The criterion could not produce ARTEFACT for any input (§10.1). It counts
  neither as a hit nor as a miss.

### 10.7 Closing state of front D

* **Closed with no mechanism and no parameter change.**
* **`20150646` was not measured and not spent.** The test split still holds 16
  series, of which only `20180654` has been spent (front C).
* **The artefact-vs-real-phase criterion was not redesigned.** The training
  population does not justify it: symptom D proper is **one real series, at
  `L = 1`**, where the anchoring test has no valid cut at all.

### 10.8 Proposed to orchestration — proposals only, no work opened

* **(a) A new front on incipient refusal.** 6 of 17 real train series:
  `20160587`, `20160735`, `20171179`, `20180628`, `20181046`, `20202023`. The
  training population suffices; the test split need not be touched. `20160030`
  (test) stays out.
* **(b) Make the constant baseline a standing output of
  `evaluate_against_labels.py`.** It exists today only in
  `research/labels/diagnostics/frontD/constant_baseline.py`.
* **(c) Repository hygiene:** the committed `.txt` outputs embed absolute local
  paths (`/Users/…`) in a public repository.
