# Front 20a — halted at step 3, before any measurement

Step 3 of the front is a blocking precondition: read
`research/labels/evaluate_against_labels.py`, report the rule it uses to pair a
detector mature with a labelled mature when there is more than one block, and
**stop before measuring** if that rule is ambiguous or not explicitly present.

It is not present. Stopping as instructed. No detector run was performed at
either configuration.

## What `evaluate_against_labels.py` actually does

It does not pair matures as matures. Pairing lives in
`labels_core.score_phase_sequences` (`research/labels/labels_core.py:728`), and
the whole rule is these four lines (`:763-773`):

```python
if [p for p, _ in lab] != [p for p, _ in det]:
    n_mismatch += 1
    continue
n_match += 1
for k in range(1, len(lab)):
    ...
    phase, lidx = lab[k]
    didx = det[k][1]
    tol = int(rec["phases"][k]["tolerance_idx"])
```

That is: **compare the entire phase-name sequence first; if it differs in any
way, count a mismatch and score nothing at all for that series. Only on an exact
whole-sequence match, pair positionally by index `k`.**

The docstring states the reasoning (`:734-739`):

> **Sequence mismatch** — the detector found a different set of phases in a
> different order (an extra residual, a missing mature). No boundary-by-boundary
> distance is meaningful across a mismatch: pairing the 3rd labelled boundary
> with the 3rd detected one when the sequences differ compares two different
> transitions and manufactures a number. These series are counted and set aside.

So the case the front asks about — `20160735`'s 4 detected blocks against 1
labelled mature — is never paired by this script. It is dropped before pairing
is reached. The rule is deliberate and explicit, but it is a rule for *declining*
to pair, not a rule for pairing.

## Why this blocks gate (a) specifically

Gate (a) asks for "matures within ±6 at both ends: exactly 38/47". This script
cannot produce that number, for three independent reasons:

1. **Ceiling of 30, not 47.** Only sequence-matching series contribute a mature
   boundary. Gate (b) fixes the sequence score at 30/47, so at most 30 series can
   have a mature scored here. 38 is unreachable in principle.
2. **Starts only, never ends.** `score_phase_sequences` compares `det[k][1]`
   against each phase's `start_idx`. There is no end-of-phase comparison
   anywhere in the script, so "within ±6 at *both ends*" is not expressible.
3. **Per-label tolerance, not a fixed 6.** The margin is
   `rec["phases"][k]["tolerance_idx"]`, the labeller's own uncertainty — the
   quantity the repo's `CLAUDE.md` deliberately keeps distinct from the
   detector's fixed margin of 6.

## Where 38/47 actually came from

`research/labels/diagnostics/item19/item19_core.py:130`, `pair_by_overlap` — a
different instrument, written for item 19/20 part 1:

```python
def pair_by_overlap(det_matures, lab_mature):
    """Pick the detected mature block with the largest overlap with the label.

    Overlap pairing (not order pairing): across a sequence mismatch, pairing the
    k-th detected mature with the k-th labelled one compares two different
    transitions. Falls back to the nearest block by midpoint when nothing
    overlaps, so a Delta is still reported rather than silently dropped.
    """
```

with the hit defined at `item19_core.py:209` as
`abs(d_start) <= 6 and abs(d_end) <= 6`, both ends, fixed margin 6, and scored
across sequence mismatches rather than dropping them.

`REPORT.md:441` confirms the provenance of the number:

> moving 0.95 → 0.90 raises the count of matures within ±6 of their label at both
> ends from **32/47 to 38/47**, leaves the sequence score at 30/47 and the
> synthetic score at 12/12

## Two properties of that instrument the maintainer should rule on

Both are explicit in the code, neither is wrong, but both matter for a gate
stated as "exactly 38/47":

* **Only the first labelled mature is ever scored** (`item19_core.py:187`,
  `first_lab = lab_mat[0]`). Three train labels carry two matures —
  `20203947`, `s6b542eee`, `sbd6c6920` — and their second mature is not scored
  in either configuration. The count is out of 47 *series*, not 47 matures.
* **Ties go to the earliest block.** `best_ov` starts at `-1` and the test is
  `ov > best_ov` (strictly greater), so when two detected blocks overlap the
  label equally, the earlier one wins. Deterministic, but undocumented.

## What is needed to resume

A ruling on which instrument scores gate (a). The front's numbers (38/47, both
ends, fixed 6) are `item19_core.pair_by_overlap` numbers throughout, so the
consistent reading is that 20a should be measured with that function — but the
front names `evaluate_against_labels.py`, and substituting the scoring
instrument is not a call to make unilaterally mid-front.

Gates (b) sequence 30/47, (c) synthetics 12/12 and (d) incipient boundaries are
unaffected by the ruling: all three are well defined in both scripts.

## Already done, independent of the ruling

* branch `research/item20a-maf-090` off `develop-v2.1` at `d4014036`
* `research/labels/configs/cyclophaser_params-11.yaml`, the three specified
  changes and nothing else
  sha256 `24dd7f22b76d98cf0cab0b18ff040e010209604a8485007551095e9622abe420`
* environment: python 3.12.14, numpy 2.5.3, scipy 1.18.0, conda env
  `cyclophaser`, `cyclophaser` importing from the working tree
