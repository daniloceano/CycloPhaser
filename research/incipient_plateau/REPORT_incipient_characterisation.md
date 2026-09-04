# Characterisation of the incipient phase under the current pipeline

**Status: measurement only. No threshold chosen, no redefinition implemented,
`cyclophaser/` untouched.**

| | |
|---|---|
| Branch | `research/incipient-plateau` |
| Base commit | `01c44923cc6d9e9ae70c48c0fc717fd126546390` (`develop-v2.1`) |
| Script | `research/incipient_plateau/measure_incipient.py` |
| Raw output | `incipient_measurements.csv` (126 rows), `summary_tables.txt` |
| Figures | `research/incipient_plateau/figures/` (gitignored; regenerate by running the script) |
| Environment | python 3.13.5, scipy 1.17.1, numpy 2.1.2, pandas 2.3.3 |
| Data | 51 tracks in `tests/calibration_data/` (hourly, n = 30–259, median 98) + the 12 `tests/synthetic/` cases (3 h/step, n = 66) |

The previous incipient investigation ran on a pipeline contaminated by Lanczos
zero-padding, an inert `use_filter=True`, and an unrequested Savitzky-Golay pass
on the derivatives. All of it is re-measured here from scratch.

## Pinned metrics

Following the definition fixed in `docs/future_work.md` §4 (the earlier note did
not pin its script and produced the 0.571 vs 0.545 discrepancy):

```
r(t0)      = |dz_dt_smoothed2[0]|  / max|dz_dt_smoothed2|
r(t_final) = |dz_dt_smoothed2[-1]| / max|dz_dt_smoothed2|
rel(t)     = |dz_dt_smoothed2(t)| / max|dz_dt_smoothed2|
```

`dz_dt_smoothed2` is the array `find_stages` consumes. Medians are over the 51
real tracks. Both configurations are measured with the same script in the same
process, so the (a)/(b) contrast is free of metric-definition drift.

## Configurations

**(a) `author` — the validated §3c calibration (PRIMARY).** `use_filter=True`,
`cutoff_low=168`, `cutoff_high=18`, `boundary_padding=reflect`,
`replace_endpoints_with_lowpass=0`, `use_smoothing=False`,
`use_smoothing_twice=False`, `savgol_polynomial=3`, `prominence_relative=0.3`,
`distance=3`, `mature_method=amplitude`, `mature_amplitude_fraction=0.95`,
`decay_tail_amplitude_fraction=0.05`, `length_scale=local`,
`threshold_mature_distance=0.18`. Other thresholds at package defaults.

**(b) `defaults` — bare `determine_periods(series)`.**

## Instrumentation

`find_incipient_period` is monkeypatched *in the script only* with a tracing
wrapper that (i) diagnoses which code path fires on a deep copy, then
(ii) delegates to the untouched original for the actual result. A per-call
self-check reproduces the boundary the genuine function produced from the
replica's prediction; it passed on **126/126 rows**.

---

# 1. The four paths of `find_incipient_period` (51 real tracks)

| path | (a) author | (b) defaults |
|---|---|---|
| (i) catch-all `fillna` only — `len(phases_order) <= 2` | 2 (0 fired) | 1 (0 fired) |
| (ii) case A re-cut, `It → D → It` | **0** | **0** |
| (iii) case B, starts `It`, `dz_valley` before `mature` | **44 fired** | **49 fired**, 1 not fired |
| (iv) case C, starts `D`, `dz_peak` before `mature` | 4 fired, 1 not fired | 0 |
| tracks that end up with an `incipient` phase | 48/51 | 49/51 |

**Two results that change the scope of the redefinition:**

**Case A never fires.** 0/51 under both configurations. The `It → D → It`
re-cut branch is unexercised by this track set entirely.

**The catch-all `fillna` produces no incipient phase at all on real data.** By
the time `find_incipient_period` runs, `post_process_periods` has already filled
every gap: the leading run of NaN in the `periods` column is **0 on 51/51 tracks
under (a)**, and under (b) exactly one track (`20190639`) has any NaN at all —
a leading run of 3, entirely subsumed by the case-B boundary at index 23 that
fires on the same track. Every one of the 48/49 incipient phases on the real set
is therefore written by a *via* — none by the catch-all. On the three (a) / two
(b) tracks where no via fires, the result is simply **no incipient phase**, not
a spurious one.

The single exception in the whole study is synthetic: `IcIt_observational`
under (a), where no via fires, a leading run of 4 NaN survives
`post_process_periods`, and the catch-all alone writes the incipient phase
(§5). It is the truncated Ic→It series — the one case with no mature stage for
the vias' `next_mature` comparison to resolve against.

So the redefinition target on real data is **case B (44/51 under (a), 49/51
under (b)) plus case C (4/51 under (a), 0 under (b))** — not the catch-all, and
not case A. The catch-all only manufactures a spurious incipient on synthetic
series (§5).

The five tracks where no via fired:

| track | config | via | `phases_order` | resulting sequence |
|---|---|---|---|---|
| `20170760` | a | catch-all only | `intensification > decay` | `intensification > decay` |
| `20181046` | a, b | catch-all only | `intensification` | `intensification` |
| `20206498` | a | case C, not fired | `decay > intensification > decay` | `decay > intensification` |
| `20180733` | b | case B, not fired | 6 entries (two cycles) | `intensification > mature > decay` |

`20170760`, `20181046` and `20206498` are the three sub-three-phase tracks
already recorded in §3c; `20181046` (n=30) is the shortest series in the set.

**The via itself is config-dependent.** **Six** tracks change path between (a)
and (b): `20180170`, `20180608`, `20190325`, `20203947` and `20206498` sit on
case C under (a) but on case B under (b), and `20170760` falls through to the
catch-all under (a) while taking case B under (b). Separately, three tracks
differ in whether the via *fires* at all (`20170760`, `20180733`, `20206498`).
The leading phase the pipeline assigns is not stable across the two
calibrations, so any redefinition keyed on "which via" inherits that
instability.

---

# 2. Pinned edge metrics — the (a) vs (b) asymmetry

| config | `r(t0)` median [q25–q75] | `r(t_final)` median [q25–q75] |
|---|---|---|
| (a) author | **0.068** [0.044–0.108] | **0.060** [0.034–0.095] |
| (b) defaults | **0.526** [0.260–0.678] | **0.319** [0.165–0.415] |

This reproduces §4 exactly (0.068 / 0.526), which confirms the pinned metric
definition transfers cleanly. Range under (a): 0.003–0.172. Under (b):
0.012–**1.000** — on at least one track the *global maximum* of `|dz|` falls on
the very first sample.

**This asymmetry is the central finding of this measurement**, and §4 already
explains its mechanism: under (b), `use_smoothing='auto'` leaves the two
Savitzky-Golay passes on the derivative active with an unbounded auto window,
and that is what puts ~0.53 of the peak slope at `t0`. Its consequence for the
incipient question is developed in §4 below.

---

# 3. Current incipient boundary

The boundary is geometric: `start + 0.4 × (first dz extremum − start)`. It is a
fraction of a *distance*, so it carries no information about the slope at the
point where it lands.

| config | tracks with incipient | boundary idx q25/med/q75 | as fraction of series | in hours | `rel` at the boundary q25/med/q75 |
|---|---|---|---|---|---|
| (a) author | 48 | 3 / **4** / 6 | 0.027 / **0.043** / 0.059 | 3 / **4** / 6 | 0.349 / **0.584** / 0.665 |
| (b) defaults | 49 | 7 / **8** / 11 | 0.068 / **0.089** / 0.134 | 7 / **8** / 11 | 0.562 / **0.772** / 0.852 |

The incipient phase is short in both configurations — a median of 4 h (a) /
8 h (b), i.e. 4 % / 9 % of the series — and it is **twice as long under (b)**.

**The current boundary does not land on a low-slope region.** At the moment the
incipient phase ends, `|dz|` has already reached a median **58 % of its maximum
under (a) and 77 % under (b)**; it is above half the maximum on 29/48 (a) and
41/49 (b) tracks. Whatever the geometric rule is selecting, it is not the end of
a flat start.

---

# 4. Slope profile and the τ sweep (diagnostic — no τ recommended)

For each τ, the first step where `rel(t) ≥ τ`. That index is by construction the
length `L` of the leading run with `rel < τ` — the "initial plateau".

## Does an initial plateau exist at all?

| config | τ | `L = 0` (no plateau) | `L ≥ 1` | `L ≥ 3` | `L ≥ 6` | `L` med | `L` q75 |
|---|---|---|---|---|---|---|---|
| (a) author | 0.05 | 32/51 | 19 | 4 | 1 | 0 | 1 |
| | 0.10 | 15/51 | 36 | 8 | 5 | 1 | 2 |
| | 0.15 | 1/51 | 50 | 11 | 7 | 2 | 2 |
| | 0.20 | 0/51 | 51 | 19 | 8 | 2 | 3 |
| | 0.30 | 0/51 | 51 | 29 | 10 | 3 | 4 |
| (b) defaults | 0.05 | **50/51** | 1 | 1 | 1 | 0 | 0 |
| | 0.10 | **48/51** | 3 | 2 | 2 | 0 | 0 |
| | 0.15 | **44/51** | 7 | 7 | 5 | 0 | 0 |
| | 0.20 | **44/51** | 7 | 7 | 7 | 0 | 0 |
| | 0.30 | **35/51** | 16 | 12 | 8 | 0 | 2 |

**Under (b) a plateau criterion is not merely inaccurate — it is undefined.**
On 35–50 of 51 tracks the *first sample already exceeds τ*, for every τ in the
sweep including 0.30. There is no low-slope start to find, because the residual
edge artifact (`r(t0)` median 0.526) is itself larger than any plateau threshold
one would want to set. A τ rule under (b) collapses to "boundary at index 0",
i.e. no incipient phase at all.

**Under (a) a plateau exists but is short.** Every track has `L ≥ 1` for
τ ≥ 0.15, and `L` grows smoothly with τ (median 0 → 1 → 2 → 2 → 3). But it is
short in absolute terms: even at τ = 0.30, the median plateau is **3 h** and
only 10/51 tracks have one lasting ≥ 6 h. The slope rises quickly from the
start; there is no extended quiescent phase to detect.

## Candidate boundary per τ against the current one

| config | τ | idx med | frac med | hours med | Δ vs current, med [q25–q75] | tracks where τ is *later* than current |
|---|---|---|---|---|---|---|
| (a) author | 0.05 | 0 | 0.000 | 0 | −4 [−5.2 … −3.0] | 3/51 |
| | 0.10 | 1 | 0.012 | 1 | −3 [−4.0 … −2.8] | 3/51 |
| | 0.15 | 2 | 0.017 | 2 | −2 [−3.0 … −1.8] | 5/51 |
| | 0.20 | 2 | 0.022 | 2 | −2 [−3.0 … −1.0] | 8/51 |
| | 0.30 | 3 | 0.033 | 3 | −1 [−2.0 … 0.0] | 11/51 |
| (b) defaults | 0.05 | 0 | 0.000 | 0 | −8 [−11 … −7] | 0/51 |
| | 0.10 | 0 | 0.000 | 0 | −8 [−11 … −7] | 0/51 |
| | 0.15 | 0 | 0.000 | 0 | −8 [−10 … −7] | 1/51 |
| | 0.20 | 0 | 0.000 | 0 | −8 [−10 … −7] | 1/51 |
| | 0.30 | 0 | 0.000 | 0 | −8 [−9 … −6] | 3/51 |

Every τ in the sweep places the boundary **earlier** than the current geometric
rule, in both configurations. Under (a) the gap closes as τ rises (−4 h at
τ=0.05 down to −1 h at τ=0.30, with 11/51 tracks moving later at τ=0.30);
under (b) the gap is a flat −8 h for every τ, which is just the statement that
the τ boundary is pinned at index 0.

Reading the two tables together: on the real set, a slope-plateau criterion
would produce a **shorter** incipient phase than today's, not a longer one — the
opposite of what a "the incipient phase is being cut off too early" framing
would predict.

**No τ is recommended here.** τ = 0.15–0.20 is the smallest value that yields a
defined plateau on all 51 tracks under (a), and τ = 0.20 happens to have zero
median error on the synthetic set (§5), but a two-criterion coincidence on five
synthetic cases is not a basis for a choice.

---

# 5. Synthetic suite — the only ground truth for the incipient boundary

Classification of the 12 cases:

- **`designed_Ic` (5)** — the segment list opens with a literal `Ic` segment;
  the ground-truth boundary is its length: `ItMD_clean` (3),
  `IcItMD_residual_noisy` (3), `IcItMD_residual_clean` (3),
  `IcItMD_ItMD_noisy` (3), `IcIt_observational` (6).
- **`expected_Ic` (5)** — the case asserts an `incipient` phase but has no `Ic`
  segment (it is derived from a leading `D`, or tolerated at the start of an
  `It`). Its designed boundary is degenerate — `incipient` and the next phase
  share start index 0 — so **no boundary target is checkable**:
  `ItMD_noisy`, `IcDItMD_noisy`, `IcDItMD_residual_noisy`, `ItMD_ItMD_noisy`,
  `quase_ItD`.
- **`no_Ic` (2)** — the case asserts no incipient at all: `DItMD_noisy`,
  `DItMD_residual_noisy`.

## Accuracy against the known `Ic` boundary (`designed_Ic`, n=5)

| config | criterion | scored | MAE (steps) | signed median | misses |
|---|---|---|---|---|---|
| (a) author | current 0.4× | 5 | **2.00** | +2 | 0 |
| | τ = 0.05 | 5 | 2.00 | −2 | 0 |
| | τ = 0.10 | 5 | **1.40** | −1 | 0 |
| | τ = 0.15 | 5 | **1.40** | −1 | 0 |
| | τ = 0.20 | 5 | **1.40** | **0** | 0 |
| | τ = 0.30 | 5 | 2.20 | +1 | 0 |
| (b) defaults | current 0.4× | 4 | 2.00 | +2 | **1** |
| | τ = 0.05 | 5 | 3.40 | −3 | 0 |
| | τ = 0.10 | 5 | 2.60 | −3 | 0 |
| | τ = 0.15 | 5 | 2.60 | −3 | 0 |
| | τ = 0.20 | 5 | 2.80 | −3 | 0 |
| | τ = 0.30 | 5 | 3.40 | −3 | 0 |

1 step = 3 h on these series; the suite's own tolerance is 6 steps, so **every
criterion in this table is inside tolerance**. The differences are real but
small against the suite's declared precision.

- Under **(a)**, the current geometric rule is systematically **late** (+2) and
  every τ ≤ 0.20 is systematically **early** (−1 to −2); τ = 0.20 is the only
  criterion with zero median error. Best MAE is 1.40 (τ = 0.10–0.20) vs 2.00 for
  the current rule — a modest improvement on five cases.
- Under **(b)**, every τ is stuck at a flat −3, which is the index-0 collapse of
  §4 measured against a ground truth of 3. The τ criterion carries no
  information under (b).
- The one **miss** is `IcIt_observational` under (b): the truncated
  Ic→It series that never reaches peak intensity gets **no incipient phase at
  all** (detected sequence: `intensification`), whereas (a) detects
  `incipient > intensification` with a boundary of 4 vs a ground truth of 6.
  Note that under (a) this phase comes from the **catch-all `fillna`**, not from
  a via — the only such instance in the study (§1). The case has no mature
  stage, so both vias' `next_mature` comparison fails and neither fires; the
  incipient phase survives only because `post_process_periods` happens to leave
  4 leading NaN. Any redefinition that touches the catch-all changes the
  behaviour of exactly this class of truncated track.

## Spurious incipient on the `no_Ic` cases

| case | config | incipient? | boundary | via | detected sequence |
|---|---|---|---|---|---|
| `DItMD_noisy` | a | **yes (spurious)** | 3 | case C fired | `incipient > decay > intensification > mature` |
| `DItMD_noisy` | b | no | — | case C not fired | `decay > intensification > mature` |
| `DItMD_residual_noisy` | a | **yes (spurious)** | 3 | case C fired | `incipient > decay > intensification > mature > residual` |
| `DItMD_residual_noisy` | b | no | — | case C not fired | `decay > intensification > mature > residual` |

**On the two cases designed without an incipient, configuration (a) invents one
and (b) does not** — the reverse of the accuracy ranking above, and via case C
in both instances, not the catch-all. This is a second point where case C, not
case B, is the path that misbehaves.

Note also that on the real set the catch-all produces nothing (§1), while here
the `expected_Ic` cases `ItMD_noisy` and `ItMD_ItMD_noisy` — which have no `Ic`
segment — do receive an incipient phase (boundary 3–6), written by case B. So
even the "spurious incipient on an `ItMD` series" that the suite tolerates comes
from a via, not from `fillna`.

---

# 6. Summary of findings

1. **The redefinition scope is case B, plus case C.** Case A never fires
   (0/51), and the catch-all `fillna` produces zero incipient phases on real
   data because `post_process_periods` leaves no leading NaN. 48/51 (a) and
   49/51 (b) incipient phases come from vias B and C. The catch-all is the sole
   mechanism on exactly one series in the study — the truncated, mature-less
   synthetic `IcIt_observational` — which is the only evidence available on what
   changing it would affect.
2. **`r(t0)` is 0.068 (a) vs 0.526 (b)** — reproducing §4 exactly — and this
   asymmetry decides whether a plateau criterion is definable at all.
3. **Under package defaults, no slope-plateau criterion is definable.** On
   35–50 of 51 tracks the first sample already exceeds every τ up to 0.30. Any
   τ rule degenerates to "boundary at index 0". A plateau-based redefinition is
   conditional on configuration (a)'s filtering, not portable to (b).
4. **Under (a) a plateau exists but is short** — median 1–3 h depending on τ,
   with ≥ 6 h on only 10/51 tracks even at τ = 0.30.
5. **The current geometric boundary does not sit at a low-slope point.** `|dz|`
   is already at 58 % (a) / 77 % (b) of its maximum there. The rule is
   measuring a distance, not a slope.
6. **Every τ in the sweep shortens the incipient phase** relative to today's
   boundary (median −1 to −4 h under (a), −8 h under (b)).
7. **On synthetic ground truth all criteria are within the suite's 6-step
   tolerance.** Under (a) the current rule is late by +2 and τ = 0.10–0.20 is
   more accurate (MAE 1.40 vs 2.00); under (b) τ carries no information.
8. **(a) and (b) fail in opposite directions on the synthetics**: (a) is more
   accurate on the five designed-`Ic` cases but invents an incipient on both
   `no_Ic` cases; (b) invents none but misses `IcIt_observational` entirely.

# 7. Open questions for the author

- Is configuration (a) confirmed as the primary target, given that a plateau
  criterion is undefined under package defaults (finding 3)? If the redefinition
  is to work under both, the defaults' derivative smoothing has to be revisited
  first — that is the §4 `use_smoothing='auto'` path, explicitly left unchanged.
- Case C is the path that misbehaves on both `no_Ic` synthetic cases and the
  path that is unstable between configurations (§1). Should it be in scope
  alongside case B?
- Case A is dead code on this track set. Keep, or investigate whether any real
  track exercises it?
- No τ is proposed here. τ = 0.15–0.20 is the smallest value with a defined
  plateau on all 51 tracks under (a), and τ = 0.20 has zero median error on
  five synthetic cases — that is the whole of the evidence, and it is thin.
