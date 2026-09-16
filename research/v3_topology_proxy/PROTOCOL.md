# Front v3.0 — premise measurement: is the filtered series a proxy for *which* phases exist?

**Declared in full before a single number was produced.** Committed as its own
commit, ahead of the commit that adds the measurement's output. `git log` is the
evidence that nothing here was adjusted to fit a result.

## The premise under test

A heavily filtered series (Lanczos + double Savgol, all `'auto'`) is *bad at
timing* — it displaces short matures and compresses or stretches the incipient —
but is claimed to be *good at inventory*: at saying WHICH phases a cyclone has.
If that holds, a v3.0 architecture can take the inventory from the filtered
series and leave timing to a later stage, replacing the present six sequential
phase functions (each overwriting the last).

This front measures the premise only. It implements no architecture.

## What is compared

The **phase-name sequence** — order and multiplicity, no indices at all — of a
topology-only reader against the manual label's own phase sequence, over the
**47 training cases** of the frozen `research/labels/split.yaml` (35 real + 12
synthetic). The 16 test cases are not touched.

Every series' raw values are hashed and checked against the label's recorded
`series_sha256` before anything is compared. A single mismatch aborts the run.

## Reader T — the topology-only proxy (frozen)

Input series: `process_vorticity(zeta_df)` at package defaults —
`use_filter='auto'` (Lanczos, window `len//2`), `use_smoothing='auto'`,
`use_smoothing_twice='auto'` (the double Savgol), `boundary_padding='reflect'`,
`replace_endpoints_with_lowpass=0`. This is exactly the series the front names.
Reader T reads `z = vorticity_smoothed2` and `dz = dz_dt_smoothed2` and nothing
else. It calls **none** of the six phase functions.

**1 — skeleton, from z's topology alone.**
Extrema from the package's own `find_peaks_valleys(z)` with `prominence`,
`prominence_relative` and `distance` all `None` — no knob of mine. Index 0 and
index N-1 are always extrema (documented boundary-clip behaviour), so the
extremum walk covers the whole series by construction. Consecutive extrema of
the same type are reduced to the most extreme member of the run (lowest z for a
valley, highest for a peak; ties take the first), making the sequence strictly
alternating.

Walking consecutive extrema:

| transition | emits |
|---|---|
| peak → valley (descending) | `intensification` |
| valley → peak (ascending)  | `decay` |
| a valley with an extremum on **both** sides | `mature`, between them |

A valley that is the first or the last extremum emits no `mature`. That is not a
convenience: it is the package's existing physical invariant — a plateau is only
confirmed as the storm's peak if an intensification is seen to reach it and a
decay is seen to leave it (see the neighbour-confirmation comment in
`find_mature_stage`).

**2 — the two flat ends.**
`rel = |dz| / max|dz|` — the package's own `_incipient_plateau_rel` with
`signal="derivative"`, its shipped default. Then the package's own
`_incipient_plateau_boundary` at its shipped defaults (`tau=0.20`,
`crossing="single"`, `k=3`):

* **head** — applied to `rel`. A non-zero boundary prepends `incipient`.
* **tail** — the same call on `rel[::-1]`. A non-zero boundary appends `residual`.

Symmetric by construction, and every threshold in Reader T is a value the
package already ships as a default. No number here was chosen by the person
running the measurement.

**Expressiveness check (stated before running).** Reader T can produce all 11
phase-name sequences that occur in the 47 labels, including the two-cycle ones,
the `decay → …` openings and the truncated `incipient → intensification`. A
disagreement is therefore evidence about the premise, not an artefact of a
reader that was unable to say the right thing.

## The gate

Primary metric: **exact phase-name-sequence agreement**, Reader T vs label, over
the 47 training cases.

**PASS requires all three:**

1. exact-sequence agreement **≥ 70 % (≥ 33/47)**;
2. it beats the **majority-class baseline** — always emitting the modal label
   sequence, which is 16/47 = 34.0 % — by **≥ 10 percentage points** (≥ 44.0 %);
3. it is **≥ the current six-function detector's** exact-sequence agreement on
   the same 47 cases at package defaults, read the same way (sequence only,
   every boundary ignored).

Anything else is **FAIL**.

Why 70 %: under the proposed architecture the downstream does not re-derive the
inventory, it places boundaries inside the one it is handed. Front A is the
precedent for what a wrong skeleton does — forcing index 0 to `peak` made
`find_mature_stage` invent a spurious mature block on 20190325 and 20191014. An
inventory wrong in more than three cases in ten is not something a later stage
can be built on; it would have to second-guess its own input, which is the
six-function architecture over again. 70 % also sits well clear of the 34 %
constant baseline, so the test discriminates.

Criterion 3 exists because "replace the architecture" needs the replacement to
be better *at the thing it is being replaced for*. If today's detector already
recovers the inventory at least as well, then inventory is not where the current
architecture fails — timing is — and the premise does not justify the rebuild.

Reported alongside, not gating, so that a FAIL is diagnosable: per-phase
presence/absence agreement, phase-count agreement, the confusion between
sequences, and the split by source (real / synthetic).

## Prediction (declared before running; never to be adjusted)

**FAIL.** Exact-sequence agreement in the **30–55 %** band.

Dominant error: **incipient presence**, predicted to agree on **fewer than 75 %**
of the 47. Incipient is the main discriminator in this population — present in
28/47, absent in 19 — and it is read here from `|dz|` of the heavily filtered
series, which is precisely the quantity the front says the filtering distorts.
The package's own boundary_padding measurements put normalised `|dz|` at t0 at a
median of 0.42 under `reflect`, above `tau = 0.20`, so I expect incipient to be
**under**-detected rather than over-detected.

Secondary error: **residual over-firing**. `residual` occurs in only 10/47
labels, while a flat tail at `tau = 0.20` should be common.

I expect the skeleton itself (intensification / mature / decay and their
repeats) to be the *strong* part — that is the part topology actually speaks to.
