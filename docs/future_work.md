# Future Work — Methodological Improvements

These are research directions identified for improving phase-detection robustness,
especially the sensitivity of fixed global parameters to heterogeneous cyclone signals.
Each can be evaluated against the synthetic test suite (`tests/synthetic/`) and the
calibration app (`tools/calibration_app/`) before adoption. Several are candidate
material for a future methodological note.

Items are ordered by estimated impact-to-risk ratio (higher return / lower disruption
to existing behaviour first).

---

## 1. Replace `argrelextrema` with `scipy.signal.find_peaks`

The current extrema detection uses `scipy.signal.argrelextrema` with `>=`/`<=`
comparisons, which can be sensitive to noise and plateau regions. Replacing it with
`scipy.signal.find_peaks` (which supports `prominence` and `distance` parameters)
would yield more robust peak/valley identification and more physically interpretable
thresholds that are less dependent on the specific smoothing applied upstream.

**Expected benefit:** fewer spurious extrema; more stable detection across cyclones
with different intensity profiles.

---

## 2. Explicit low-confidence boundary zone

The current approach uses `replace_endpoints_with_lowpass` to mask Lanczos filter
edge artifacts implicitly. A cleaner alternative is to mark the first and last *N%*
of the series (or a fixed number of timesteps) as "uncertain" in the output
`periods` column, propagating uncertainty information to downstream analyses instead
of silently replacing values.

**Expected benefit:** users receive explicit uncertainty flags rather than silently
corrected boundaries; avoids false-confidence in phase attribution near track start/end.

---

## 3. Locally-adaptive thresholds — **implemented (opt-in), 2026-07**

**Status: done as an opt-in on `research/adaptive-thresholds`.** Five of the seven
detection thresholds (`threshold_intensification_length`,
`threshold_intensification_gap`, `threshold_mature_length`,
`threshold_decay_length`, `threshold_decay_gap`) were fractions of the *total series
length*. `determine_periods(..., length_scale="local")` (default remains `"global"`,
byte-identical to all prior versions) checks each candidate segment against
`_local_cycle_scale` (`cyclophaser/find_stages.py`) — the span of the local
oscillation it belongs to (nearest z-extremum before and after it, falling back to
the series boundary) — instead of the whole track. `threshold_mature_distance` and
`threshold_incipient_length` were already local and are unaffected.

**Central finding — a real, load-bearing limit of this approach, not a bug:**
local-scale normalization only resolves heterogeneity **between** life cycles in a
multi-cycle track (a small second cycle no longer has its phases rejected by
thresholds sized for a much larger first cycle). It does **not**, and *cannot by
construction*, correct a disproportion **within** a single, isolated cycle (e.g. an
unusually short decay right after an unusually long intensification): with only one
cycle in the series there is no extremum beyond the ones already bounding it, so
`_local_cycle_scale`'s neighbour-lookup falls back to the series boundary on both
sides and numerically **equals** the global series length. Local and global are
mathematically forced to agree whenever a series contains a single life cycle — the
"local" mode only has something to correct once a series has more structure than the
one segment being evaluated.

This was checked against the real cyclone track database (TRACK/Gramcianinov): decays
as abrupt as the synthetic stress case used to establish this limit (a intensification
~20x longer than the following decay) do not occur in real tracks — real declines are
always at least moderately gradual, and real asymmetric cyclones (decay shorter than
intensification, or the reverse, within physically plausible ratios) are already
detected correctly by the existing pipeline, in both modes. So this is a documented
boundary of what threshold-rescaling alone can do, not an open problem to chase
further — a genuinely disproportionate single-cycle decay would need a different kind
of fix entirely (e.g. item 6 below, changepoint-based segmentation, which does not
rely on a length threshold at all).

Locked in as permanent regression tests in
`tests/synthetic/test_length_scale_regression.py`: the multi-cycle case (local
recovers the second cycle's phases; global still collapses them into `residual`) and
the single-cycle sentinel case (global and local agree exactly; not a target for a
future fix — see the test's docstring for the reasoning above in full, and the
mature/decay neighbour-confirmation comment in `find_mature_stage`,
`cyclophaser/find_stages.py`, for the related physical-confirmation invariant this
interacts with).

**Update 2026-09:** `length_scale` (and `mature_method`, see item 3b below) are now
wired into `tools/calibration_app/app.py` (defaults dict, YAML import/export map, UI
controls, `determine_periods` call).

---

## 3b. Amplitude-based mature-stage detection — **implemented (opt-in), 2026-09**

**Status: done as an opt-in on `research/adaptive-thresholds`.** The mature stage was
previously located only one way (now `mature_method="derivative"`, still the
default): a fixed proportion (`threshold_mature_distance`) of the *time* distance
from the vorticity minimum (z_valley) to each neighbouring z_peak. This locates the
window using extrema of the smoothed *derivative*, which can lag the true z minimum
by a few timesteps and displace the mature window forward of where the cyclone was
actually most intense — observed concretely on case 20160030, where "derivative"
placed the mature window's centre ~3h after the smoothed-z minimum.

`mature_method="amplitude"` (new, opt-in; `find_stages._amplitude_mature_bounds`)
instead defines the mature window as the contiguous stretch of z around the z_valley
that stays within `mature_amplitude_fraction` (default 0.90) of the cycle's own
peak-to-valley amplitude, evaluated independently on the intensification side and the
decay side. Amplitude is always measured as a peak-to-valley *drop*
(`z[side_peak] - z[z_valley]`), never the extremum's absolute value — vorticity has a
non-zero floor, so an absolute fraction would not be physically meaningful (same
reasoning as `prominence_relative` in `find_peaks_valleys`). Anchoring on z's own
value rather than on the derivative removes the phase lag: on 20160030, with the
author's calibrated thresholds, this took the mature window's centre offset from the
smoothed z minimum from +3h ("derivative") down to +30min ("amplitude").

`threshold_mature_length` and `threshold_mature_distance` are **mutually exclusive**
with `mature_method="amplitude"` and have no effect in that mode. Both are
minimum-duration/window-sizing rules calibrated for "derivative"'s
fixed-time-proportion window; reusing `threshold_mature_length` as a floor on the
amplitude window was tried first and found to discard well-centred amplitude windows
for being narrow (20160030's ~19h window fell ~1h15 short of a `threshold_mature_length`
value tuned for "derivative", and was discarded entirely rather than kept). Narrowness
there is a physically meaningful outcome of `mature_amplitude_fraction`, not a defect.
No replacement minimum-duration safeguard has been introduced for "amplitude" —
deliberately, to evaluate the method unconstrained first (see below). The mature/decay
neighbour-confirmation invariant (`find_mature_stage` / `find_residual_period`,
see item 3 above) is unrelated to `threshold_mature_length` and still applies
identically in both modes.

### Empirical calibration on the 51-track set (`tests/calibration_data/`)

Best configuration found by the author so far:

```
mature_method: amplitude
mature_amplitude_fraction: 0.95
prominence_relative: 0.3
distance: 3
length_scale: local
use_smoothing: 31
cutoff_high: 24
replace_endpoints_with_lowpass: 0
```

Result: **7.8% bad cases (4/51)**, down from **17.6% (9/51)** with the previous
`mature_method="derivative"` calibration (`length_scale=local`,
`threshold_mature_distance=0.18`, `threshold_mature_length=0.15`, no prominence
filtering — see the YAML exported 2026-07-16 for that baseline).

**Finding — signal-significance criteria outperform duration thresholds here:**
raising `prominence_relative` from 0.2 to 0.3 alone resolved 5 of the 9 bad cases.
Separately adjusting `threshold_intensification_length` (a *duration* threshold) was
tried and produced no improvement. This suggests that, at least for this track set,
criteria based on how significant a feature is (prominence, amplitude) generalize
better than criteria based on how long it lasts (duration fractions) — consistent
with why `mature_method="amplitude"` itself outperforms `"derivative"` on the
displacement problem it was built to fix.

**Remaining bad cases (4/51) and diagnoses:**

- **20206498** — a second mature phase (in a two-cycle track) is not detected.
- **20170409**, **20191014** — small spurious "intensification" bumps during an
  otherwise-continuous decay cause much of that decay to be reclassified as
  `residual` instead.
- **20150561** — a plateau during decay is misread as a renewed intensification
  (same failure family as 20170409/20191014 above).

**Note on ceiling, not failure:** part of these remaining cases appears to originate
upstream, at the TRACK stage (spurious merging of two distinct cyclones into one
track), not in CycloPhaser's phase detection itself. Those are a ceiling on what
threshold/method tuning inside CycloPhaser can fix, not a defect of the method — worth
keeping in mind before chasing further threshold changes on this specific subset.

### Update 2026-09-02 — `decay_tail_amplitude_fraction` closes the gap to 0/51

Root cause of the 20170409 / 20150561 failure family above: on a single-cycle
series, `find_peaks_valleys`' prominence filter scores peaks and valleys as
*separate* populations, so the largest interior z_peak always survives
`prominence_relative` filtering by construction (it is the max of its own
population), even when its prominence is negligible in absolute terms — while
the valley of that same ripple is correctly rejected against the population
containing the cycle's genuine main valley. The result is an "orphan" z_peak
with no surviving valley after it, which makes `find_decay_period` truncate
decay early; the remaining flat tail is then labelled `residual` by
`find_residual_period`'s catch-all rule, even though nothing in the vorticity
indicates a genuine re-intensification (20170409 was declared `residual` with
89.5% of its peak intensity still present).

`decay_tail_amplitude_fraction` (new, opt-in; `find_stages.find_residual_period`)
fixes this **without touching `z_peaks_valleys` or any extrema detection** —
unlike the discarded alternative of dropping the orphan peak from the extrema
themselves, which was found to shift `_amplitude_mature_bounds`'s decay-side
amplitude reference and inflate the mature window's duration in every case it
fixed. Instead, immediately before the catch-all rule, and only when the NaN
tail directly follows an existing `decay` block, it checks whether that tail
contains a genuine re-deepening — a drop below the tail's running-maximum z
larger than this fraction of the cycle's own peak-to-valley amplitude — and
extends `decay` over the tail if not. See the function's docstring for the
full mechanism and `tests/test_decay_tail_amplitude_fraction.py` for the
locked-in regression cases.

**Author's validated calibration on the 51-track set: 0% bad cases (0/51)**,
down from 17.6% (9/51) at the start of this line of investigation:

```
mature_method: amplitude
mature_amplitude_fraction: 0.95
prominence_relative: 0.3
distance: 3
decay_tail_amplitude_fraction: 0.05
length_scale: local
use_smoothing: 31
cutoff_high: 24
cutoff_low: 168
replace_endpoints_with_lowpass: 0
savgol_polynomial: 3
```

Duration thresholds (`threshold_intensification_length`,
`threshold_intensification_gap`, `threshold_decay_length`,
`threshold_decay_gap`, `threshold_incipient_length`) are left at package
defaults, except `threshold_mature_distance=0.18` and
`threshold_mature_length=0.15` — the latter has no effect under
`mature_method="amplitude"` (see above) and is carried over from the prior
`"derivative"` calibration mainly for continuity/documentation, not because it
does anything here.

**NOTE — this calibration is specific to TRACK (Gramcianinov et al.)
vorticity, not a general-purpose default.** TRACK output already carries
built-in spatial smoothing; raw ERA5 vorticity series (no upstream smoothing)
will very likely need a different calibration — most immediately different
`cutoff_high`/`use_smoothing` values, and possibly different
`prominence_relative`/`decay_tail_amplitude_fraction` since both are measured
relative to the *smoothed* signal's own amplitude, which depends on how much
noise reaches `find_peaks_valleys` in the first place.

**Plan — named presets instead of changed defaults:** once the improvement
fronts opened by this investigation (item 3 above, this item, and the two
remaining known cases below) are closed, turn validated calibrations like this
one into named presets (e.g. `"track_gramcianinov"`, `"era5_raw"`) exposed
alongside the existing keyword arguments, rather than changing
`determine_periods`'s own default values. This keeps a bare
`determine_periods(series)` call byte-identical to v2.0.0 while giving users a
one-line way to opt into a validated, dataset-appropriate parameter set. Not
implemented yet — noted here for when this line of work is ready to close.

**Known remaining cases (not counted as bad, but not fully understood
either):**

- **20206498** — a second mature phase, in a two-cycle track, is still not
  detected. Unrelated to the orphan-peak mechanism above; not yet diagnosed.
- **Incipient phase** — the current `find_incipient_period` heuristic (see
  `cyclophaser/find_stages.py`) needs a redefinition pass; flagged here as a
  future front, not addressed by this update.

---

## 3c. Lanczos boundary artifact + `use_filter=True` bug — **implemented, 2026-09-03**

Two changes, on the `research/boundary-artifacts` branch, that together alter what
the filtering stage actually does.

### `boundary_padding` (opt-in, default `"zero"`)

`lanczos_filter` / `lanczos_bandpass_filter` convolve via
`scipy.signal.convolve(..., mode="same")`, which implicitly **zero-pads** the input
beyond its own ends. Vorticity has a non-zero floor (order −5e-5), so those
"missing" samples are a jump to zero, not a neutral continuation — and two
properties of this configuration amplify the damage:

- the kernel is about **half the series length** (`window_length_lanczo =
  len(zeta)//2`; measured kernel/series ratio median **0.494** over the 51-track
  set), so the contaminated zone is **~24 % of the series at each end (~48 % in
  total)**;
- the "bandpass" kernel **does not reject DC** at these window lengths
  (`sum(weights)` median **0.629**, `|H(DC)|/|H|max` median **0.79**), so most of
  the large mean vorticity passes through and is what gets removed at the edges.

Result: a step between the boundary value and the interior worth a median **74 % of
the cyclone's own peak-to-peak amplitude** (q25 0.40, q75 1.29), spread as a ramp
carrying the sign of a spurious *deepening*. That ramp alone accounts for **≥ 80 %
of the slope measured at t₀ in 51/51 tracks**.

Measured with the filter active, normalised `|dz|` at the first/last sample (median
over 51 tracks): `"zero"` **0.95/0.98** → `"reflect"` **0.42/0.35** → `"edge"`
**0.50/0.38**. Raw-signal reference: **0.29**.

The kernels are untouched — the fix is purely a boundary condition, and the pad
widths (`M//2`, `M-1-M//2`) reproduce scipy's own `"same"` alignment exactly, so no
time shift is introduced.

### `use_filter=True` was silently disabling the filter (bug fix, behaviour change)

`bool` is a subclass of `int` in Python, so the previous
`window_length_lanczo = use_filter` read `True` as the integer **1**. A 1-tap
Lanczos kernel is a scalar multiply (0.0714 for `cutoff_low=168`/`cutoff_high=24`),
not a convolution.

**Every parameter set previously calibrated with `use_filter=True` — including the
0/51 calibration recorded in section 3b above — was calibrated on an effectively
UNFILTERED signal.** That is what the calibration app's "Apply Lanczos filter"
checkbox sent. `use_filter=True` now means `'auto'` and warns; `use_filter=1` still
means a literal 1-tap window and reproduces the old behaviour byte-identically
(pinned in `tests/test_decay_tail_amplitude_fraction.py` as a historical record).

The section-3b calibration does **not** survive activating the filter: 5 of its 7
`decay_tail_amplitude_fraction` CONVERT cases stop converting, and the set of
changed tracks becomes a *different* set, not a smaller one.

**Interaction between the two changes.** Activating the filter with
`boundary_padding="reflect"` is *less* disruptive than with `"zero"` — measured
against the section-3b calibration as baseline:

| configuration | `r(t₀)` | `r(t_final)` | phase sequences changed |
|---|---|---|---|
| filter inert (window 1), `zero` — baseline | 0.581 | 0.428 | — |
| filter active, `zero` | **0.949** | **0.981** | **15/51** |
| filter active, `reflect` | **0.415** | **0.346** | **9/51** |

With `"zero"`, switching the filter on makes the boundary *worse*; with `"reflect"`
it improves on the baseline. The two corrections are complementary, not independent.

### Author's validated calibration with the Lanczos filter ACTIVE — 0/51 bad cases

```
use_filter: true                      # == 'auto'; window = len(series)//2
cutoff_low: 168
cutoff_high: 18
replace_endpoints_with_lowpass: 0
use_smoothing: false
use_smoothing_twice: false
savgol_polynomial: 3
boundary_padding: reflect
prominence_relative: 0.3
distance: 3
mature_method: amplitude
mature_amplitude_fraction: 0.95
decay_tail_amplitude_fraction: 0.05
length_scale: local
threshold_mature_distance: 0.18
threshold_mature_length: 0.15         # no effect under mature_method="amplitude"
```

All other thresholds at package defaults. **0 % bad cases (0/51)** by the author's
visual evaluation in the calibration app.

**Finding — with the Lanczos filter finally doing its job, the Savitzky-Golay
smoothing of `z` could be switched off entirely** (`use_smoothing=false`,
`use_smoothing_twice=false`) while keeping 0/51. This is consistent with the
attribution measured under the old (unfiltered) configuration, where **100 % of the
edge-artifact excess came from the Savgol passes on the derivative** — `r(t₀)` went
0.465 (raw) → 0.372 (after Savgol on z) → 0.524 (+Savgol #1 on dz) → 0.581
(+Savgol #2 on dz). Two smoothing stages were doing the same job, and the one that
was actually hurting the boundary was the redundant one. `cutoff_high` moved
18 h (from 24 h), which is the high-frequency rejection the Savgol was standing in
for.

**Caveat on "Savgol off" — it is off for `z`, not for the derivatives.**
`use_smoothing=false` skips both Savgol passes on `z` (verified:
`vorticity_smoothed2 == filtered_vorticity`), but `process_vorticity` then hits
`if not window_length_savgol: window_length_savgol_derivatives = len//4|1` (or
`len//2|1`), so the **derivatives are still smoothed twice, with an *auto* window**
— 29–67 timesteps on this track set, i.e. *larger* than the explicit 31 used
before. This is why `r(t₀)` under the new calibration measures **0.571**, close to
the old 0.581, rather than dropping toward the 0.42 that `"reflect"` reaches with
Savgol on `z` active. Worth knowing before concluding that derivative smoothing is
out of the picture; it connects directly to item 4 below.

**Structural notes on the new calibration (measured, for the record — not a
contradiction of the 0/51 visual evaluation, which is the author's own criterion):**
47/51 tracks get an `incipient` phase, 14/51 a `residual`, 0 unclassified
timesteps, median mature duration 9 h, median `|mature centre − argmin(z)|` 1.0 h
(unchanged). Three tracks resolve to fewer than three distinct phases —
`20170760` (n=59) → `intensification → decay`, `20206498` (n=133) →
`decay → intensification`, `20181046` (n=30) → `intensification` only. `20181046`
is the shortest series in the set and the least resolvable by a
`len(series)//2`-tap kernel; `20206498` is the two-cycle track already listed as a
known open case in section 3b.

**Presets.** This calibration and the section-3b one are the two concrete
candidates for the named-preset plan described in section 3b — with the caveat
that the section-3b set is only reproducible via `use_filter=1`.

---

## 4. Replace / improve derivative smoothing

The Savitzky-Golay filter has documented boundary artifacts that are most pronounced
when computing derivatives (`deriv=1`). Alternatives to evaluate:

- **Whittaker-Henderson smoother** — penalised least-squares, no boundary artifacts.
- **Gaussian smoothing** — well-behaved boundaries, tunable bandwidth.
- **Better edge padding** — AR(p) extrapolation or reflective padding before applying
  Savgol, to reduce the amplitude of endpoint distortions without discarding data.

**Expected benefit:** cleaner derivative signal near series edges; less dependence on
`replace_endpoints_with_lowpass` as a compensatory measure.

### Measurement 2026-09-03 — derivative smoothing is the dominant remaining edge artifact, and removing it barely moves the phases

**Commit measured: `50a624480b02817dac6f2987ff260616435312a8`** (`develop-v2.1`, i.e.
with `boundary_padding="reflect"` as default and the `use_filter=True` bug fixed).
Branch of the investigation: `research/smooth-derivatives`.
Environment: scipy 1.17.1, numpy 2.1.2, pandas 2.3.3.
Track set: the 51 tracks in `tests/calibration_data/`.

**What was varied.** Only the four `savgol_filter` calls applied to the derivatives in
`process_vorticity` (`cyclophaser/determine_periods.py`, the block after
`dzfilt_dt = vorticity_smoothed2.differentiate(...)`). The two Savgol passes on `z`
were left exactly as the configuration specifies. `current` is the unmodified code;
`off` and `w5/w9/w15` required a temporary monkeypatch of `savgol_filter` in the module
namespace **for measurement only** — no package code was changed on this branch.

- `current` — untouched. With `use_smoothing=false` the code falls into
  `if not window_length_savgol:` and picks the *auto* window
  `len//4|1` or `len//2|1`; measured range over the set **15–91 timesteps**.
- `off` — derivative Savgol calls replaced by identity (no smoothing of `dz`, `dz2`).
- `w5` / `w9` / `w15` — window forced to 5 / 9 / 15, `savgol_polynomial=3` unchanged.

**Metrics.** `r(t₀) = |dz_dt_smoothed2[0]| / max|dz_dt_smoothed2|`, `r(t_final)` the
same at the last sample; median over the 51 tracks. `dz_dt_smoothed2` is the array
`find_stages` actually consumes. "seq" counts tracks whose *phase sequence* changes;
"labels" counts tracks where **any** timestep is relabelled; "relabelled" is the mean
fraction of timesteps that change label. All comparisons are against `current` **of the
same parameter set**.

#### (a) Author's validated calibration (section 3c: `use_filter=true`, `cutoff_low=168`, `cutoff_high=18`, `use_smoothing=false`, `length_scale=local`, `mature_method=amplitude`, …)

| derivative smoothing | `r(t₀)` (q25–q75) | `r(t_final)` | seq changed | labels changed | relabelled |
|---|---|---|---|---|---|
| `current` (auto, 15–91) | **0.545** (0.29–0.70) | 0.403 | — | — | — |
| off | **0.068** (0.04–0.11) | 0.060 | 1/51 | 39/51 | 3.5 % |
| window 5 | 0.082 (0.05–0.13) | 0.072 | 1/51 | 39/51 | 3.5 % |
| window 9 | 0.122 (0.08–0.20) | 0.108 | 1/51 | 40/51 | 3.3 % |
| window 15 | 0.192 (0.12–0.31) | 0.179 | 1/51 | 41/51 | 3.2 % |

#### (b) Package defaults (bare `determine_periods(series)`: `use_filter='auto'`, `cutoff_high=48`, `use_smoothing='auto'`, `length_scale=global`, `mature_method=derivative`)

| derivative smoothing | `r(t₀)` (q25–q75) | `r(t_final)` | seq changed | labels changed | relabelled |
|---|---|---|---|---|---|
| `current` (auto, 15–91) | **0.526** (0.26–0.68) | 0.319 | — | — | — |
| off | **0.282** (0.16–0.37) | 0.182 | 1/51 | 27/51 | 0.7 % |
| window 5 | 0.285 (0.16–0.37) | 0.186 | 1/51 | 27/51 | 0.7 % |
| window 9 | 0.301 (0.18–0.38) | 0.196 | 1/51 | 27/51 | 0.7 % |
| window 15 | 0.334 (0.21–0.40) | 0.208 | 1/51 | 27/51 | 0.7 % |

The single track whose sequence changes is `20180170` under the author's calibration and
`20180733` under the defaults — the same track in every mode, in both cases.

**Findings.**

1. **With the Lanczos boundary fixed, the derivative Savgol is now the dominant source
   of the edge artifact.** Under the author's calibration it multiplies `r(t₀)` by ~8
   (0.068 → 0.545) and `r(t_final)` by ~7. Under package defaults the factor is smaller
   (~1.9) because the wider `cutoff_high=48` leaves more genuine high-frequency slope in
   the signal for the Savgol to preserve.
2. **The auto window is the problem, not smoothing per se.** `r(t₀)` scales smoothly
   with window length — 0.068 (off) → 0.082 (5) → 0.122 (9) → 0.192 (15) → 0.545
   (auto, 15–91). Any fixed short window recovers most of the benefit.
3. **The phase output is nearly insensitive to this.** 1/51 sequences change in every
   mode and both parameter sets; per-timestep relabelling is 3.5 % (author) / 0.7 %
   (defaults); no fragmentation appears — total phase segments over the set go 248 → 249
   (author) and 218 → 219 (defaults), tracks with fewer than three distinct phases stay
   at 3 and 1, `residual` counts are unchanged, and `incipient` gains one track. The
   label at `t₀` changes in 1/51 and at `t_final` in 0/51; the median shift of the first
   phase boundary is −2 h (author) / 0 h (defaults), with a worst case of 31 h / 44 h on
   a single track.
4. **`use_smoothing=false` does not mean "no Savgol".** Confirmed again here: with
   `use_smoothing=false` the derivatives are still smoothed twice with a window of
   15–91 timesteps — *larger* than the explicit windows used by any calibration. This is
   the caveat recorded in section 3c, now quantified.

**Reconciliation with the earlier note.** Section 3c records `r(t₀) = 0.571` for this
calibration; re-measured here at `50a6244` it is **0.545**. The earlier note did not pin
the measurement script, so the small gap is a metric-definition difference, not a
behaviour change — `cyclophaser/` is byte-identical between `b5441aa` and `50a6244`
apart from the two default values. The definition used above (`dz_dt_smoothed2`,
normalised by its own maximum, median over tracks) is the one to reuse from now on.
For reference, the same quantity on `dz_dt_filt` (one Savgol pass instead of two) is
0.353 (author) / 0.438 (defaults).

**Implication for the item below.** The cheapest correction is not a new smoother: it is
to stop deriving the derivative window from `window_length_savgol` and to cap it (a fixed
5–15, or a physically-motivated fraction of the cycle length), plus a `use_smoothing=false`
that actually disables the derivative passes too. Both are behaviour changes and need the
author's visual re-validation on the 51 tracks before adoption — the numbers above say the
re-validation should be nearly a no-op, but 0/51 is the author's criterion, not a metric.

### Author's decision, 2026-09-04 — `use_smoothing=False` now disables the derivative smoothing

**Decided and implemented** (branch `research/smooth-derivatives`): of the two
corrections proposed just above, only the second was adopted. `use_smoothing=False`
now skips the four derivative Savgol passes as well, so `find_stages` consumes the
unfiltered `d(z)/dt` and `d²(z)/dt²`. This is exactly the `off` variant measured in
the tables above, re-confirmed against the package code after the change:
`r(t₀) = 0.068` (q25–q75 0.04–0.11), `r(t_final) = 0.060` under the author's
calibration; 1/51 phase sequences change; no fragmentation.

**Explicitly NOT adopted:** the fixed cap (a window of 5–15) and the
cycle-length-fraction window. Both were measured (windows 5/9/15 in the tables
above) and both remain unimplemented — the parameter-name honesty fix was judged to
cover the case that mattered, without introducing a new tuning knob.

**Scope of the decision — and what it does not cover.** The check is `use_smoothing
is False` by identity, so `use_smoothing='auto'` and explicit integer windows are
untouched, as are the two Savgol passes on `z`. Note that the `off` row under
*package defaults* in table (b) above (`r(t₀) = 0.282`) is **not** reachable through
this change: those defaults use `use_smoothing='auto'`, and that path is unchanged
(`r(t₀) = 0.526`, as measured). That row remains a measurement-only variant.

**This is validated on TRACK (Gramcianinov) vorticity only.** That data already
carries built-in spatial smoothing from the upstream tracking, which is very
plausibly why removing a second, redundant smoothing stage costs so little here.
**It has NOT been validated on raw ERA5 vorticity**, which reaches
`process_vorticity` with no upstream smoothing at all and therefore carries
high-frequency content the TRACK series never had.

**When raw ERA5 is taken up, the order of investigation is:** first establish
whether the now-corrected Lanczos stage (`boundary_padding="reflect"` plus the
`use_filter=True` fix, item 3c) handles that noise on its own — with an appropriate
`cutoff_high`, which is the knob the derivative Savgol was standing in for on TRACK
data. Only if it does not should re-enabling derivative smoothing be reconsidered,
and in that case the capped-window variants above become live options again rather
than the unbounded `auto` window this change removed.


---

## 5. Review the bandpass low-frequency cutoff

The current low cutoff (168 h, 7 days) removes variability slower than one week.
For long-lived cyclones (> 10 days), this may remove part of the life-cycle envelope
itself. A pure low-pass filter, or a more permissive cutoff (~14 days), should be
evaluated for such cases.

**Expected benefit:** improved handling of long-lived and recurving systems; reduced
risk of artificially shortening the incipient or decay phases.

---

## 6. (Exploratory) Slope-based segmentation / changepoint detection

Reformulate phase detection as a segmentation problem on the smoothed trend:

1. Detect changepoints in the derivative using a penalised algorithm
   (e.g., `ruptures` with PELT or binary segmentation).
2. Classify each resulting segment by the sign and magnitude of its derivative
   (negative slope → intensification in SH; near-zero → mature; positive → decay).

This is a paradigm change, not a drop-in replacement. It would require side-by-side
validation against the current method on the full test suite and on a representative
sample of real cyclones before any replacement.

**Expected benefit:** principled changepoint detection; removes the dependency on
manually tuned extrema thresholds; potentially more robust for multi-cycle events.

---

## 7. (Exploratory) Data-driven threshold calibration

Learn detection thresholds — or per-cyclone-type clusters of thresholds — from a
manually labelled set of named validation storms (analogous to a "ground truth" set),
instead of relying on manual calibration via the calibration app.

Possible approaches:
- Bayesian optimisation over the threshold space, minimising deviation from expert
  labels on a held-out validation set.
- Clustering cyclones by intensity profile or geographic origin, then learning separate
  threshold sets per cluster.

**Expected benefit:** removes subjectivity from calibration; provides quantitative
uncertainty bounds on detected phase boundaries.

---

## 8. Front A — index-0 boundary extremum type (investigation closed, unresolved)

**Status: closed without a fix.** Related to item 1 above (`argrelextrema`'s
`>=`/`<=` comparators). Full investigation, all measurements, and the refuted
code change live on branch `fix/idx0-boundary-extremum-type` (pushed, **not
merged** — the change is refuted and the branch exists only as a
self-contained record) in `research/labels/diagnostics/` (`REPORT.md`,
`FIX_REPORT.md`, `FIX_REPORT_v2.md`, `idx0_inventory.csv`,
`synthetic_sign_table.csv`, and the scripts/figures alongside them). All
numbers below are sourced from there; nothing here is a new measurement.

### (a) Symptom, mechanical cause, four discarded routes

**Symptom:** in 5 of the 51 real calibration tracks (`20180170`, `20180608`,
`20190325`, `20191014` — training; `20206498` — held-out test split), the
detected life cycle opens with a spurious `decay` phase instead of
`intensification`.

**Mechanical cause:** `find_peaks_valleys` (`cyclophaser/determine_periods.py:122-123`)
calls `argrelextrema` with non-strict comparators (`np.greater_equal` /
`np.less_equal`) and the default `mode='clip'`. Under `mode='clip'`, index 0
is compared against itself as its own "missing" left neighbour, which always
passes under a non-strict comparator — index 0 is marked as an extremum in
51/51 real tracks, and its TYPE is decided only by the sign of
`data[1]-data[0]` on the filtered series. This extremum has calculated
prominence exactly `0.0` in the 5 affected cases and survives the
prominence/distance filter only via an explicit boundary exemption
(`cyclophaser/determine_periods.py:181-223`).

**Four routes discarded, each with the number that killed it:**

1. **Remove the index-0 extremum entirely** → 40/51 tracks then open with
   decay instead (worse, not fixed).
2. **Guard `find_decay_period` against a decay run starting at index 0** →
   no part of the pipeline has any handling for an unassigned gap at the
   START of the series (`cyclophaser/determine_periods.py:259`,
   `cyclophaser/find_stages.py:621-628`); a guard here would leave up to 52%
   of a series with no assigned phase at all.
3. **Force index 0 to `'peak'` unconditionally** → mechanically clean on the
   51 real tracks (46/46 no-op on the already-correct ones, incipient
   boundary identical field-for-field, 3/3 correct on the affected training
   tracks' first non-incipient phase), **but** 4 of the 12 synthetic cases
   that open with genuine decay by construction (`DItMD_noisy`,
   `DItMD_residual_noisy`, `IcDItMD_noisy`, `IcDItMD_residual_noisy`)
   regressed from a perfect sequence match to a mismatch.
4. **Condition route 3 on raw/filtered sign disagreement** (the raw and
   filtered series disagree on `sign(z[1]-z[0])` in exactly the 5 affected
   real tracks, 5/5) → refuted at a gate, before implementation, by the
   counter-example `IcDItMD_residual_noisy`: it opens with genuine decay AND
   has disagreeing raw/filtered signs — the same signature the rule would
   use to (wrongly) call it a boundary artefact.

**Front A does not block the v2.1 release.** The incipient-phase boundary —
the metric v2.1 is actually closing on — is IDENTICAL, field for field, with
and without route 3's fix applied (`TRAIN · real`: 17 boundary labels, 8
within margin, MAE 4.82, worst 26; refusal 16/14 — all unchanged). This is
not incidental: `boundary` is computed from `dz`/`z_unfil` and config alone
(`cyclophaser/find_stages.py:969-978`), never from the phase map, so it is
mathematically invariant to how index 0 is classified in `z_peaks_valleys`.
The index-0 problem affects the opening decay/intensification phase in 5/51
real tracks — not the incipient boundary v2.1 depends on.

### (b) Not pursued: magnitude instead of sign

The counter-example that refuted route 4, `IcDItMD_residual_noisy`, has
`|z[1]-z[0]|` = 2.6×10⁻⁶ raw vs. 1.9×10⁻⁵ filtered — the filter AMPLIFIES the
difference by ~7×. The three genuine-decay-opening synthetic cases that
passed the gate have large raw magnitude, and the filter ATTENUATES it
instead of amplifying it. A rule keyed on amplification-vs-attenuation of
`|z[1]-z[0]|` was **not pursued**, because it would require a numeric
amplification/attenuation threshold — i.e. a new parameter, which this
investigation was explicitly constrained not to introduce. Left here as a
lead for whoever reopens Front A.

### (c) Defect H (open): unconditional incipient overwrite can mask a wrong phase map

`find_incipient_period` overwrites `df.iloc[:boundary]` unconditionally,
regardless of what was already assigned there:

```
cyclophaser/find_stages.py:982:        df.iloc[:boundary, df.columns.get_loc('periods')] = 'incipient'
```

Observed case: `20180608` — the incipient boundary happens to consume the
entire spurious decay block produced by the index-0 artefact, so the final
output looks correct (opens with `intensification`) even though the
underlying extremum classification at index 0 was wrong underneath it.
Correct-looking final output here is not evidence that the phase map
beneath it is correct.

### (d) Defect I (open): Lanczos boundary padding flips the sign at t0 in 7/51 real tracks

With `boundary_padding='edge'`, the raw and filtered series disagree on
`sign(z[1]-z[0])` in **7 of the 51** real calibration tracks (5 of which are
the `valley`-at-index-0 cases in (a); the other 2 keep the correct `'peak'`
classification, since the classification depends only on the filtered
series' sign and that one happens to still read the same way despite the
disagreement). This is the underlying mechanism behind both routes 3 and 4
above, and behind item 3c's `r(t₀)` measurements for `boundary_padding`.

### (e) ⚠️ The synthetic suite does not represent the real tracks at the t0 boundary

**The 12 synthetic cases (`tests/synthetic/cases.py`) are not evidence about
real-track behaviour at the t0 boundary, and real-track measurements are not
evidence about the synthetic suite there — the two populations have a
measurably different sign structure at index 0.** Measured 2×2 table,
`idx0_tipo` (peak/valley) × whether the raw and filtered signs agree:

| population | `valley` & signs disagree | `valley` & signs agree |
|---|---|---|
| 51 real tracks | 5 | 0 |
| 12 synthetic cases | 3 | 3 |

The real tracks separate cleanly (every `valley`-at-index-0 case is a sign
disagreement, no exceptions); the synthetic suite does not (split evenly).
**Any future front that touches the index-0 boundary and validates only
against the synthetic suite, or only against the real tracks, is not
validating against the other population** — they do not agree well enough
here to stand in for each other.

---

## 9. Calibration app — layer inspector fidelity and inert-parameter UI signaling (F(i)(ii) and F(iii), implemented 2026-09-10)

**Status: implemented, merged into `develop-v2.1`.** Two related fronts on
`tools/calibration_app/`, both UI-only — no `cyclophaser/` file was touched
by either, verified by a byte-identical sha256 of `determine_periods()`
default output before/after each.

### (a) F(i)(ii) — rel-panel fidelity and a boundary-selection bug (commit `7133570`, merge `1f38611`)

The layer inspector's "rel" panel hardcoded `"rel = |dz| / max|dz|"` as its
label everywhere, even under `incipient_plateau_signal="vorticity"` where
the curve actually plotted is `|d(zeta_raw)/dt|` — misleading whenever the
signal choice didn't match the label. It also never showed the crossing/k
evidence that decides whether a plateau incipient phase exists, so a
refused plateau just said "no crossing" with no reason.

**Bug fixed:** the panel picked which crossing to draw with
`boundary_smoothed or boundary_raw or 0`, which silently fell back to the
unsmoothed probe's boundary whenever the active configuration *legitimately
refused* a crossing — `0` is both a valid falsy Python value and this
codebase's refusal sentinel, so the `or`-chain could not tell "there is no
crossing" from "the crossing is at index 0." Affected **5 of the 51 real
calibration tracks**: `20150561`, `20150656`, `20170225`, `20171179`,
`20180263` (diagnostic before/after renders in
`research/labels/diagnostics/04_item3_*`, reviewed visually before commit).

`rel_signal_label()` now derives the label from the actual
`signal`/`smooth_window` at the same site `rel` is computed, and the
crossing/k evidence (rejected runs, accepted run, active requirement,
refusal reason) is read back from the same package helpers the detector
itself uses, not recomputed. Fidelity locked in by
`tests/test_layer_inspector.py`: label/anti-hardcode tests, and
crossing/k-evidence fidelity checked across all 51 tracks × 2 configs.

Series colours were also made role-based (grey/thickest = raw, yellow =
post-filter, red = post-smoothing) with per-panel legends, at Danilo's
request — a separate, purely cosmetic follow-up commit from the bug fix
above, per this project's "aesthetic changes go in their own commit" rule.

### (b) F(iii) — inert calibration parameters were live controls that silently did nothing (commits `f188bae`, `25a113a`, `20e003d`; merges `f837052`, `402d3f7`)

Several `app.py` widgets were clickable and had a real effect under *some*
configurations but were completely inert (no effect on `determine_periods`'
`periods` output) under others, with no indication to the user. Measured
with an automated "inertia sweep" (`research/inert_params/sweep_inertia.py`,
later replaced by a **derived** cartesian enumeration,
`research/inert_params/sweep_derived.py` — see the methodology note below)
across all 51 calibration tracks, and every inert case classified into
**POR DESENHO** (a citable line skips the parameter) or **DEPENDENTE DOS
DADOS** (the parameter is read unconditionally; the flat result is a
property of this specific 51-track set, not of the code) — never left
uncaptioned-but-unclassified, since captioning a data-dependent coincidence
as "unused" would misrepresent it as documented behaviour.

**3 POR DESENHO conditions, now signalled with `disabled=` + an inline
"Inactive" note:**

1. `use_filter=False` → `cutoff_low`, `cutoff_high`, `boundary_padding`
   (`determine_periods.py:614`, the Lanczos convolution's sole consumer).
2. `use_smoothing is False` → `savgol_polynomial`
   (`determine_periods.py:648`/`:688`, both Savgol passes on `z` and the
   derivative passes gated on this check).
3. Found in a follow-up audit of the sweep's own enumeration (below):
   `use_smoothing is False` → `use_smoothing_twice` (the second pass is
   nested inside the first, `determine_periods.py:648,655`, never reached);
   and `use_filter=False` → `replace_endpoints_with_lowpass`
   (`determine_periods.py:625`).

**Methodology finding, worth keeping in mind for any future sweep-style
audit:** the original sweep's `(parameter, base_config)` pairs were a
hand-written list — and a hand-written list has no way to make an *absent*
pair visible, which is exactly how the `use_smoothing_twice` case above
stayed hidden through the front's own gate (a) self-test. Replaced with a
**derived** enumeration: the full cartesian product of every parameter ×
every base config, with every pair explicitly marked `TESTED` /
`SKIPPED_REDUNDANT` (provably identical to an already-tested pair) /
`SKIPPED_DEFERRED` (not run, cost, but listed rather than silently absent)
— see `research/inert_params/sweep_derived.py` and
`inertia_matrix_full.csv`.

**3 items registered here rather than left only in `research/inert_params/`
(which a future front is not guaranteed to read):**

1. **Real package defect, not fixed (out of scope for a UI-only front):**
   `process_vorticity(use_smoothing=False, use_smoothing_twice="auto")`
   raises `ValueError`. `bool` is a subclass of `int`, so
   `use_smoothing=False` degrades `window_length_savgol` to `0` in the
   `'auto'` derivation of the second pass's window
   (`determine_periods.py:582-586`), which then fails the
   `>= savgol_polynomial` guard at `:608` for any polynomial degree the UI
   allows. **One click from the app's own defaults** (`use_smoothing` to
   `"off"`, `use_smoothing_twice` left at its own default `"auto"`) —
   reproduced live twice, independently. No existing test exercises this
   combination (every test that sets `use_smoothing=False` also explicitly
   sets `use_smoothing_twice=False` in the same call). Full brute-forced
   blast-radius table (288 combinations) and blocked-vs-legitimate-error
   split in `research/inert_params/INCIDENTAL_crash_bug.md`.
2. `threshold_intensification_gap` is inert under the *default*
   configuration across its whole UI range (0/51 tracks change) — read
   unconditionally, but the gap-merge loop it feeds only runs when a track
   has more than one intensification block, which none of the 51 tracks do
   at default thresholds. **Untested:** whether a different
   `threshold_intensification_length`, or `length_scale='local'`, exposes
   tracks where this parameter bites.
3. `incipient_plateau_crossing` (`"single"` vs `"sustained"`) only agrees
   on all 51 tracks for `k ≤ 10`, across the whole τ range tested — not in
   general, as first reported; it diverges (up to 15/51 tracks) at
   `k ≥ 15`. Practical implication for whoever works on the `k`/sustained-
   run mechanism or its F(i)(ii) visualization next: **that machinery is
   barely exercised by this calibration set under
   `signal="derivative"` at any `k` a user is likely to reach for** (UI
   default 3) — validate against `signal="vorticity"` tracks instead,
   where the two modes already diverge on 42/51. Full (τ, k) grid in
   `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md`.

**Also surfaced, unrelated to this front, not investigated:** the full
pytest suite has 4 pre-existing failures in `tests/test_label_browser.py`
(drag-to-resize margin assertions off by a few pixels, e.g. `36 == 40 ± 2`)
— confirmed via `git stash` to fail identically with every file this front
touched removed, so not a regression from F(iii). Likely
viewport/DPI-sensitive in this sandbox; candidate for its own front.

---

## 10. Front G blocker — `series_sha256` void on all 12 synthetic train labels (investigation closed, unresolved)

**Status: closed without a fix — FAIL against the declared gate (root cause
identified).** Blocks Front G (`expected_starts_idx`) until resolved. Full
investigation, all measurements, and the diagnostic script live on branch
`diag/series-sha256-mismatch` (pushed, **not merged** — the branch exists
only as a self-contained record) in `research/labels/diagnostics/`
(`diag_series_sha256.py`, `series_sha256_report.md`, `.csv`; that directory
is gitignored, the three files were force-added). All numbers below are
sourced from there; nothing here is a new measurement.

**Symptom:** 12 of 47 TRAIN labels in `research/labels/manual_labels.yaml`
are marked void by the `series_sha256` guard — the totality of the 12
synthetic cases, 0 of the 35 real tracks. Deterministic, reproduced outside
CircleCI.

**Declared gate:** identify the root cause. **Not identified — FAIL.**

**What was measured:**
- There is exactly one hash function, `labels_core.py:105`
  (`series_sha256`) — `sha256(np.asarray(values, dtype="float64").tobytes())`,
  values only, no index.
- WRITE (`labels_core.py:376`, `label_tab.py:830/845/966`) and VERIFY
  (`evaluate_against_labels.py:221-229`, `test_manual_labels.py:1129-1140`)
  call that same function over the output of the same two loaders
  (`load_real_series`/`load_synthetic_series`).
- **WRITE and VERIFY agree with each other today: 12/12 synthetic ids have
  `max|Δ| == 0` between the two routes.** The two-diverging-routes
  hypothesis is refuted.
- None of 11 alternative byte encodings tried (float32, big-endian,
  index-inclusive, rounded, CSV round-trip, repr/str text, Fortran order)
  reproduces the hash recorded on 2026-09-08, for any of the 12 synthetic
  ids.
- `tests/synthetic/cases.py` and `generators.py` are git-diff-identical
  between the commit predating labelling (`f80c2f6`, 2026-09-04) and HEAD.
- The recorded-vs-current mismatch is stable across four numpy versions
  tested (1.26.4, 2.1.2, 2.4.0, 2.5.3 — spanning the pre-/post-2.0
  BLAS-backend split), so it is not numpy/Accelerate/OpenBLAS drift.

**Conclusion by elimination:** the hash function is correct (the 35 real
labels pass through it and match) and the encoding is correct (11 tried,
none explains it). So the values of the 12 synthetic series on 2026-09-08
were not the values produced by the code today. A sha256 mismatch is not
reversible, so this cannot be directly demonstrated — it is the only
reading compatible with the measurements above.

**Leading theory, not confirmed and not confirmable:** a long-lived
`st.cache_data` Streamlit session serving a stale synthetic snapshot from
before a local edit that was never committed. The original session no
longer exists to inspect.

**Structural cause, this one actionable:** synthetic series are generated
in memory on every load; real series are read from a file on disk. The 12
broken labels are exactly the ones with no file backing them. Addressed by
freezing the synthetic suite to a versioned file, in a following front.

**Not tested:** cross-checking the id → values pairing at write time
itself. Superseded by immediate same-process verification right after
re-labelling, rather than trusting a hash written and checked in separate
sessions.

**Addendum, 2026-09-10 (see item 11):** the structural fix below found, as a
side effect of its own measurements, that a fresh process on this machine
reproduces 12/12 MATCHING hashes against the unmodified in-memory generator
— the opposite of what is recorded above. `manual_labels.yaml` was not
touched between the two sessions (`git log` shows its last change at
`7f1cd04`, 2026-09-08, before this investigation). This is left as-recorded
above rather than revised, since it was not re-investigated; item 11 is the
next measurement in the timeline, not a correction of this one.

**Addendum, 2026-09-11 — main finding, from item 12's work, not a
re-investigation of this one:** CircleCI build `#327` (Linux runner,
`cimg/python:3.12.3`, fresh wheel install), run on `feat/dedicated-conda-env`
before item 11 had merged into it, failed the same `series_sha256` guard on
the same id (`s0596ea57`) with a **third** hash value — distinct from the
value recorded on 2026-09-08, from the diagnostic session's value (commit
`3ae6082`), and from this machine's value (the 2026-09-10 addendum above).
Three separate environments (the original labelling session, the diagnostic
session, and a Linux CI runner) produced three different values for the same
nominal computation. **This is evidence for environment dependence (OS,
numpy/BLAS build, float rounding), not for the "leading theory" above of one
specific lost/stale Streamlit session** — a single stale session could
account for two diverging values, not three independently-diverging ones
across unrelated environments including a CI runner that never had a
Streamlit process running at all. Left here as a correction of the *shape* of
the evidence, not a resolution of the root cause: WHICH environment factor
causes the divergence is still not identified, and is not being
re-investigated. See item 12 for the build `#327` → `#329` (green, after item
11 merged) comparison this is drawn from.

---

## 11. Front G blocker — synthetic series frozen to versioned file — **closed, PASS, 2026-09-10**

**Status: closed with a fix.** Unblocks Front G (`expected_starts_idx`).
Branch `feat/freeze-synthetic-series`, pushed, not merged. Implements the
structural fix item 10 named as actionable: the 12 synthetic series no
longer regenerate in memory on every load.

**What changed:**
- `research/labels/freeze_synthetic_series.py` (new): one-time script,
  execs `tests/synthetic/cases.py` to get its CURRENT generator output and
  writes each of the 12 series to `tests/synthetic/data/<opaque_id>.csv` —
  no value was invented; this only relocates what the generator already
  produced.
- `labels_core.load_synthetic_series()`: reads those 12 CSVs instead of
  exec'ing `cases.py`. Case names (needed to derive the opaque id) are
  still read from `cases.py`, but via static AST parsing of the
  `CASES["name"] = {...}` assignments, not import/exec — so the load path
  performs no computation at all, matching `load_real_series()`.

**Declared gate — PASS on all five parts:**
- (a) the 12 series are read from a versioned file, and synthetic loading
  recomputes nothing — verified structurally (AST-based name parsing, no
  generator call, no RNG) and by the full test suite passing unchanged.
- (b) `series_sha256` of the 12 identical across 3 separate Python
  processes — measured, byte-identical (see below on the precision fix
  this required).
- (c) fresh-process verification, right after freezing, validates the 12
  labels — measured PASS, with a scope change from what was planned:
  Danilo decided (2026-09-10) to accept this as satisfying the gate rather
  than running the blind relabelling protocol, because there turned out to
  be no NEW rotulagem to verify — see next paragraph. (c) as originally
  written assumed today's synthetic values differed from September's; that
  premise was wrong, and the measured hash coincidence is stronger evidence
  than the relabelling protocol it stood in for — without this correction
  (c) would read as not measured, which it is not.
- (d) the real labels' recorded `series_sha256` is unchanged and still
  validates — measured across all 51 (the gate text said 35, the TRAIN
  subset; all 51 real labels, train and test, were checked and PASS, 0
  stale).
- (e) the 12 ids and `split.yaml` are unchanged — measured, `git diff` on
  `split.yaml` is empty; the 12 ids derived from the frozen files match
  `split.yaml`'s synthetic id list exactly.

**The scope change on (c), in full:** a fresh-process check (done to
satisfy (c)) found that the UNMODIFIED in-memory generator's current output
already matches all 12 recorded 2026-09-08 label hashes — 0 stale, direct
contradiction of item 10's "12/12 mismatch, root cause not identified."
`manual_labels.yaml` has not been touched since 2026-09-08 (`git log`).
Once the CSV freeze round-trips losslessly (see below), the frozen files
validate against the EXISTING 12 labels with no new labelling performed.
Presented to Danilo as a three-way choice (accept as satisfying (c) /
relabel anyway as independent confirmation / hold off pending a look at why
item 10 said otherwise); he chose to accept it. This front does not
re-investigate item 10's finding — it is left standing as its own
measurement, unrevised, with this file cross-referencing both directions.

**A fix required within this front, not carried over from item 10:** the
freeze is not a no-op — pandas' default `to_csv`/`read_csv` float
formatting does NOT guarantee recovering the exact float64 a value was
written from (measured: ~16-significant-digit truncation on write by
default, plus a separate low-precision fast parser on read). Either alone
silently perturbs the last 1-2 bits of most values, which `series_sha256`
hashes raw — this would have manufactured a NEW staleness bug distinct
from, and unrelated to, item 10's. Fixed for the synthetic loader with
`float_format="%.17g"` on write and `float_precision="round_trip"` on
read; verified bit-exact (`.tobytes()` equality) for all 12 series.
**Deliberately NOT applied to `load_real_series()`**: measured that
switching its parser to `round_trip` makes all 51 real labels newly void,
because their recorded hashes were written against the default parser's
(imprecise) output — the fix belongs only on the newly-introduced
synthetic round-trip, not on a real-track path that was already correct
under its existing parser.

**Verification method:** `git stash` used throughout to compare
before/after on the same commit rather than trusting either state
asserted; the pandas round-trip precision loss was caught this way, not
assumed. Full `pytest tests/ -k "not label_browser"` — 1098 passed, 1
skipped (`test_synthetic_lifecycles.py:128`, pre-existing, unrelated to
this front — an observational-mode case with no timing assertion), before
and after, no new failures. `test_label_browser.py` itself deselected, not
run — pre-existing sandbox-only Playwright exception, per item 9.

---

## 12. Dedicated conda environment for development — **closed, PASS, 2026-09-11**

**Status: closed with a fix.** Branch `feat/dedicated-conda-env`, merged
into `develop-v2.1`. Fixes the shadowing bug behind `research/labels/
evaluate_against_labels.py` resolving `cyclophaser.determine_periods` to
whichever version happens to be installed in the active environment rather
than to this repository, depending on the launch directory — confirmed
concretely (repo root vs `/tmp`, under the non-editable 1.7.3 install in
conda env "lorenz").

**What changed:**
- `environment.yml` (already existed, commit `e17fe12`, never actually
  built as an env): `python=3.13` → `python=3.12`, to match "lorenz", the
  environment development has actually happened in; added `plotly>=5.24`
  (floor matches `tools/calibration_app/requirements.txt`), which
  `tools/calibration_app/inspector_plotly.py` imports unconditionally and
  which was undeclared in every root dependency file (`environment.yml`,
  `requirements.txt`, `Pipfile`, `setup.py`) — it was already declared in
  the app's own `requirements.txt`/`requirements-app.txt`, just not here.
- `README.md`: new "Development Environment" section documenting the
  shadowing failure mode and the verification command. No `CONTRIBUTING.md`
  exists, so this went into `README.md` per the task's own fallback.
- `cyclophaser.__version__` does not exist anywhere in the package (neither
  the repo copy nor the installed 1.7.3 copy) — measured, `AttributeError`
  in both. Documented verification uses
  `importlib.metadata.version('cyclophaser')` instead.

**Declared gate, three parts, decided explicitly (2026-09-11) because the
two declared texts for it disagreed with each other on authorship — not
resolved by picking whichever text is more literal, resolved by judgement,
recorded here so it is not ambiguous again:**

1. **Import resolves to the repo from any directory** — measured PASS.
   Checked from `/tmp`, `$HOME`, the repo root, and `tests/`: all four
   resolve to `.../CycloPhaser/cyclophaser/__init__.py`, version `2.0.0`
   (via `importlib.metadata`, not `1.7.3`).
2. **Full pytest suite, "mesmo resultado do ambiente atual"** — measured,
   not literally identical: `cyclophaser` (new) = 1098 passed / 2 skipped /
   0 failed (1100 collected); "lorenz" (the environment named as current in
   this front's own problem statement) = 1079 passed / **21 skipped** / 0
   failed (1100 collected) — `lorenz` lacks `streamlit` and `plotly`
   entirely, so it cannot even collect-and-run 19 tests
   (`test_layer_inspector.py` ×4, `test_manual_labels.py` ×15) that the new
   environment runs and passes. **Decided: PASS.** No test passed in one
   environment and failed in the other — the declared FAIL trigger did not
   fire — and the difference is not noise: it is monotonic (strictly more
   tests execute and pass, zero regress), and it is fully and only
   explained by `environment.yml` declaring dependencies `lorenz` was
   missing, which is this front's entire point. A "same result" reading
   that penalizes fixing a coverage gap by calling it FAIL would reward the
   deficient baseline.
3. **CircleCI vs `environment.yml`** — decided: **deliberately kept
   different, not unified**, and documented as a choice rather than left
   implicit (comments added to both `.circleci/config.yml` and
   `environment.yml`). CircleCI builds the sdist/wheel and installs it plus
   bare `pytest`+`pyyaml` — no `streamlit`, no `plotly`, no conda — which is
   *closer to a PyPI user's install than to `environment.yml`*, on purpose:
   that minimal, from-a-wheel install is exactly what caught `plotly` being
   undeclared, and it is what caught the hash instability below. Making CI
   provision from `environment.yml` (conda) would have CI stop validating
   what a `pip install cyclophaser` user actually gets, for a package that
   is published to PyPI — the two environments testing different things is
   the reason to keep them apart, not an oversight to fix.
   **Directly relevant evidence, not a new investigation:** CircleCI build
   `#327`, on this branch, **before** item 11 merged into it, failed the
   same `series_sha256` guard as items 10/11, on the same id (`s0596ea57`)
   — with a **third** hash value distinct from every one already on record
   (the recorded label, the item-10 diagnostic session's, and this front's
   local session's). Build `#329`, immediately after merging item 11 into
   this branch and re-running, was green — 1100 collected, 0 failed,
   matching `lorenz` exactly. The environment-set difference between CI and
   local was a real, active contributor to the instability items 10/11
   chased; item 11's fix (series read from a committed file, never
   regenerated) closes that off regardless of what CI or any future
   environment installs, which is what makes keeping CI thin safe rather
   than reintroducing the original risk.

---

## 13. Open risk — earlier fronts may have run against the shadowed cyclophaser 1.7.3, not this repo (OPEN, not investigated)

**Status: OPEN.** Flagged 2026-09-11, not yet checked. Item 12 established
that, before its fix, `import cyclophaser` in conda env "lorenz" resolved to
the non-editable, installed **1.7.3** package or to this repository depending
on the launch directory (repo root → repo; elsewhere, e.g. `/tmp` → 1.7.3).
Any analysis run from "lorenz" in a directory where that resolved to 1.7.3
was measuring a **different version of the detector than this repository's**,
silently, with no error.

**At risk, named so far:** Front A (item 8, "index-0 boundary extremum
type") — its investigation cites specific line numbers in
`cyclophaser/determine_periods.py` (`find_peaks_valleys`, lines 122-123) and
draws conclusions about `argrelextrema`'s `mode='clip'` behaviour; if it was
launched from a directory where the import shadowed to 1.7.3, those line
numbers and that behaviour may not be this repository's code at all. A
second front, referred to as "Front E," was also named as at risk in the
same message that opened this item, but is **not identified** in this file,
in `docs/`, or in project memory as of this writing — which front "E" refers
to needs to come from Danilo directly before it can be checked.

**Not yet done:** determining, for each at-risk front, which directory/
environment it was actually launched from, and if it cannot be determined,
whether the front's conclusions change under a re-run against this
repository's code as of the commit that front used. This item exists so
that risk is not lost, not as a verdict that either front's findings are
wrong — nothing about their correctness has been checked yet.

---

## 14. Open items and debt carried forward from items 11 and 12

**Status: not closed, not being closed by this entry.** Three items named
alongside item 13, registered together here because they belong to items 11
and 12 respectively, not because they are one investigation.

**OPEN — root cause of the synthetic generator's non-determinism across
environments.** Item 11 worked around this for the 12 labelled cases only:
`load_synthetic_series()` no longer calls the generator at all, so the
non-determinism items 10's addenda measured (three distinct hash values
across three environments, for the same nominal computation) cannot reach a
label anymore, regardless of what causes it. It is **not fixed at the
source** — `tests/synthetic/generators.py`'s `make_lifecycle_series` is
unchanged, and any use of the synthetic suite outside
`load_synthetic_series()` (a script calling the generator directly, or a
future case added to `cases.py`) is exposed to the same non-determinism
item 10 measured and did not explain. Not being investigated here — see
item 10 for what was already ruled out.

**DEBT — the freeze uses CSV, a text format.** `tests/synthetic/data/*.csv`
round-trips exactly today only because of the explicit
`float_format="%.17g"` / `float_precision="round_trip"` pairing item 11 had
to add (pandas' defaults were silently lossy on both the write and the read
side — measured, see item 11). A binary format (`.npz`, NetCDF) would not
depend on a text round-trip being configured correctly to stay exact, and
would remove this as a maintenance hazard for whoever next touches either
side without knowing the precision pairing is load-bearing. Not urgent —
the current pairing is verified bit-exact for all 12 series — noted as the
more robust long-term choice, not an active problem.

**COVERAGE GAP — CI exercises none of the streamlit/plotly code paths.**
Direct, accepted consequence of item 12's decision 3 (CI deliberately does
not provision `streamlit`/`plotly`, to stay close to a PyPI install).
`tools/calibration_app/` — `label_tab.py`, `inspector_plotly.py`, `app.py`
— is untested on every push; the only checks on that code are local
(`tests/test_label_browser.py`, sandbox-only per item 9) or manual. Accepted
as a tradeoff, not accidental — but it means a regression in the
calibration app can land on `develop-v2.1` with a green CI.

---

## 15. Synthetic incipient ground truth — manual label overrules `expected_starts_idx` (decision, 2026-09-14)

**Status: decided, no code change required.** Danilo, after blind-labelling
the 12 synthetic cases through the calibration app's Label tab (see item 9;
the tab itself gained navigation, per-boundary edge uncertainty, selective
phase removal and gated overlays on branch
`feat/label-tab-navigation-overlays`, not merged as of this writing (merged
since, 8102334)):

> nos sintéticos quase sempre há uma fase incipiente que não foi pretendida
> originalmente. Pelo menos para os sintéticos eu confirmo meu label manual
> como fonte da verdade

For the 12 synthetic cases, his blind manual label in
`research/labels/manual_labels.yaml` is the source of truth for the
incipient phase — not `tests/synthetic/cases.py`'s segment-derived
`expected_starts_idx`.

**Why:** this independently confirms, by blind human judgment, what
`cases.py`'s own comments and `research/incipient_plateau/
REPORT_incipient_characterisation.md` already measured algorithmically:
`_ramp_sine` is a half-period cosine with zero derivative at both endpoints,
so any `It`/`D` segment opening in `sine` starts flat and produces a genuine
incipient plateau the segment list never designed for. Only the two
`linear` openings (`DItMD_noisy`, `DItMD_residual_noisy` —
`STEEP_START_CASE_IDS`) are true negatives.

**Practical consequence:** `research/labels/evaluate_against_labels.py`
already scores every case, synthetic included, against `manual_labels.yaml`
— it never reads `expected_starts_idx` at all, so this decision needs **no
code change** there. What it DOES affect: `research/incipient_plateau/
REPORT_incipient_characterisation.md` and `measure_incipient.py`'s
`synthetic_ground_truth()` (`designed_Ic` / `expected_Ic` / `no_Ic`,
built entirely from `expected_starts_idx`) predate the blind-labelling front
and are now **superseded**, for the synthetic set, by the manual labels.
Neither has been updated to reflect this ruling — not done as part of this
entry, pending a separate request.

**Data change, same date:** one synthetic case was re-labelled under this
front's schema 4 — `s5dcc0f79` (`IcItMD_residual_clean`) gained a `residual`
phase. Its previous version is preserved under that record's `superseded`
list (schema 4 never discards an overwritten label), and the new version is
flagged `overlays_shown: [vorticity_smoothed2]` — not blind, since an
overlay was on screen before this specific re-save.

**Extended to every phase, 2026-09-15 (front E).** The ruling recorded above
is scoped to the incipient phase. Front E extended it: for the synthetic set
the manual label is the source of truth for **all** phases, `mature`
included. See item 17, which is where the timing test was switched over to
the labels and where the consequences for `mature` are recorded.

---

## 17. Front G — synthetic timing test reads the manual labels, not `expected_starts_idx` — **gate FAIL (finding); verified and decided, 2026-09-15**

**What changed.** `tests/synthetic/test_synthetic_lifecycles.py::test_lifecycle_phase_timing`
no longer reads `expected_starts_idx` from `tests/synthetic/cases.py`. It now
compares each detected boundary with the boundary in Danilo's manual label
(`research/labels/manual_labels.yaml`), paired by position, only when the
detected phase sequence equals the labelled one. The detector, its parameters,
`expected_phases`, the sequence test, the labels and `split.yaml` are untouched.
`expected_starts_idx` is still in `cases.py`, now unread (own clean-up front).

**Why the series source also changed (timing test only).** A label certifies
one exact array (`series_sha256`). The test now runs on the frozen
`tests/synthetic/data/<id>.csv` and checks that hash first. `case["series"]`
(regenerated at import) did not match any of the 12 hashes in the development
sandbox used for this front (max |Δ| ≤ 1.1e-19 vs the frozen files; item 14's
generator non-determinism). Measured: no phase assignment changed between the
two sources in any of the 12 cases.

**Margin used.** The assertion margin is still the case `tolerance` (6). The
labels' own `tolerance_idx` (1–4 on the synthetic boundaries, mostly 1–2: 40
of 45 boundaries) is reported alongside, not asserted: with it as the margin,
18 of 45 boundaries would fail. See the decision below.

**Result.** Suite passes; no case changed pass/fail (`quase_ItD` went from a
vacuous timing pass — it had no `expected_starts_idx` — to a real one;
`IcIt_observational` is still skipped). Full table, 45 boundaries:
`research/labels/front_g/front_g_synthetic_deviations.md`, regenerated by
`front_g_deviation_table.py` next to it using the test's own comparison.

**Gate: FAIL by its own declared rule (slack ≤ 1 is luck, not a hit).**
- `ItMD_clean` / mature: label 20, detected 26, dev +6, slack **0**.
- `DItMD_noisy` / mature: label 26, detected 31, dev +5, slack **1**.
Both are mature starts detected late. All 13 labelled mature boundaries have a
positive dev (+1..+6, 12 of 13 at +2 or more): the detector's mature starts
later than the labelled one in every case, consistent with the label marking
the start of the visually flat region. Not investigated further (out of scope:
no detector change in this front; front E owns the definition of mature).

**Not comparable.** `IcIt_observational`: label is
incipient→intensification (boundary 14), detector returns only
intensification — no boundary to subtract. Observational, so not asserted.

**Premise corrections from the brief, measured.** Labelled mature length is
7–16 steps (not 8–16: `ItMD_ItMD_noisy` first mature is 7), across 13 mature
phases in 11 cases, not 12 of 12 (`IcIt_observational` has no mature;
`quase_ItD` has one but no designed plateau at all).

### (a) Independent verification in the conda `cyclophaser` environment (2026-09-15)

The patch was authored and first measured in a pip venv (numpy 2.4.0, scipy
1.17.1, pandas 2.3.3). Re-verified on branch `feat/front-g-manual-labels-source`
(commit `727efd2`, branched from `develop-v2.1` at `ff53f1f`) in the dedicated
conda environment of item 12 — python 3.12.14, numpy 2.5.3, scipy 1.18.0,
pandas 3.0.5, `cyclophaser` resolving to this repository (not the shadowed
1.7.3 of item 13):

- **Deviation table identical across all 45 boundary rows.** Regenerating
  `front_g_synthetic_deviations.md` changed only the embedded library-versions
  line. Every `dev`, `slack` and `label_tol` is unchanged across those three
  library upgrades.
- **Suite: 1115 passed, 0 failures** (`pytest -m "not browser"`).
- Both slack ≤ 1 boundaries reproduce exactly (`ItMD_clean` / mature dev +6
  slack 0; `DItMD_noisy` / mature dev +5 slack 1), as does the 18/45 figure.

### (b) The `case["series"]` hash mismatch is environment-specific

Measured in the conda `cyclophaser` environment: `case["series"]` (regenerated
at import) matches the recorded `series_sha256` for **12 of 12** synthetic
cases, with `max |Δ|` against the frozen CSV of **exactly 0.0**. In the pip
venv with numpy 2.4.0 it matched **0 of 12** (≤ 1.1e-19, the observation in
item 14 that motivated the change of series source).

The timing test reads the frozen `tests/synthetic/data/<id>.csv` precisely so
that it does not depend on which of those two environments it runs in. The
hash guard stays regardless. Do not cite the 1.1e-19 figure as a property of
the generators — it is a property of that one sandbox. This is also a third
dated data point in the unreconciled item 10 / item 11 contradiction, agreeing
with item 11; not investigated here.

### (c) Skip counts are environment-dependent — do not gate on them

The front's declared gate predicted `1115 passed / 2 skipped` and got
`1115 passed / 1 skipped / 29 deselected`. No test changed outcome. Cause:
`tests/test_label_browser.py` does a module-level
`pytest.importorskip("playwright.sync_api")`, so the same commit reports two
shapes under `-m "not browser"`:

| playwright | reported |
|---|---|
| absent | 1115 passed, **2 skipped**, 0 deselected — module skips whole at collection, its 29 tests never collected |
| present | 1115 passed, **1 skipped**, 29 deselected — the 29 collect, then the marker filter drops them |

The 29 was confirmed exactly by collection. The only real runtime skip is
`test_synthetic_lifecycles.py:244` (observational case). **The correct
prediction for a gate is "1115 passed, 0 failures"** — predict `passed` and
`failed`, never the skipped/deselected split, which reports on the machine
rather than on the code.

### (d) DECISION (Danilo, 2026-09-15): the asserted margin stays a fixed 6

`max(6, tolerance_idx)` was considered and **rejected**. On today's labels it
would change nothing — the largest `tolerance_idx` on any synthetic boundary
is 4, so the expression yields 6 at **45 of 45** boundaries — but it was
rejected on principle, not on effect: it would mix the detector's error margin
with the labeller's own uncertainty, which are two different quantities. The
labels' `tolerance_idx` stays reported alongside and unasserted.

This closes the open question left in *Margin used* above. `expected_starts_idx`
remains in `cases.py`, unread, for its own clean-up front.

### (e) OPEN backlog — the detector's mature starts late at every labelled boundary

All **13** labelled mature boundaries have a positive deviation: the detector
places the start of mature **after** the label, by **+1 to +6** steps (12 of
13 at +2 or more; devs +1, +2, +2, +3, +3, +3, +4, +4, +4, +4, +4, +5, +6).
This is systematic, not scatter — there is no mature boundary the detector
finds early or on time. The labelled mature phases it is measured against run
7–16 steps across 11 cases, so a +6 offset consumes a large fraction of the
shorter ones.

This is registered against the definition of mature decided in **front E**:
the label marks the start of the visually flat region, and the detector does
not. Not investigated and not to be fixed here — no detector change was in
this front's scope. Whoever picks this up should start from the 13 mature rows
of `research/labels/front_g/front_g_synthetic_deviations.md` and front E's
definition, and decide whether the detector, the definition, or the labelling
convention is the thing that moves.

---

## 16. Calibration app — Label tab navigation, per-boundary uncertainty, overlays, schema 4 — **closed, PASS, 2026-09-14**

**Status: closed with a fix.** Branch `feat/label-tab-navigation-overlays`
(6 commits: `ab17faa`, `d1e23a5`, `2b9d5a1`, `c8d3dbb`, `ddc4522`, `f300420`),
merged into `develop-v2.1` as `8102334` (`--no-ff`). Follows on from item 9's
Label tab.

**What changed, in the Label tab (`tools/calibration_app/label_tab.py`)
only, plus a schema bump in `research/labels/labels_core.py`:**
- Case-navigation dropdown (status/split/frozen indicators) moved into the
  main content area, above the heading — it originally shipped in the
  sidebar, mixed with Grid/Inspector filters, and Danilo could not find it.
- Uncertainty is now settable on both edges (`open`/`close`) of every phase,
  including the two series edges, not one flag per row; reconciled per
  boundary across the two rows that share it.
- Selective multi-phase removal via a per-row checkbox + "Remove selected",
  replacing the old "No incipient" / "Remove last" buttons. Navigation is a
  pure "◂ Previous" / "Next ▸" pair that never saves.
- An opt-in, Inspection-only overlay of the detector's own filtered/smoothed
  series (`cyclophaser.determine_periods.process_vorticity`, computed in
  `app.py`, never reimplemented in the tab), drawn in the SAME chart and
  y-axis as the raw series and the boundary bars — forced off in Labelling
  mode, so blind labelling never sees it.
- `manual_labels.yaml` schema 3 → 4: `open_unsure`, `close_unsure`,
  `overlays_shown` (blindness provenance), `superseded` (label history on
  overwrite). Schema-3 records are read unchanged and do not migrate until a
  deliberate resave; the addition never changes verdict derivation — checked
  by round-tripping all 63 committed records with zero content change.
- Hard blocks before save: TEST-split cases cannot be saved at all; the 12
  frozen synthetic cases require two separate confirmations; overwriting any
  existing label requires an explicit confirmation. An explicit "Cannot save
  yet — <reasons>" caption makes a blocked save diagnosable from the screen.

**Two bugs found and fixed against real usage, both root-caused before being
patched:**
1. A genuine Streamlit lesson, not specific to this tab: a widget rendered
   after another widget that can call `st.rerun()` earlier in the same
   script pass loses its ticked/typed state on the pass it gets skipped,
   even though its key is unchanged — bare widget-key memory does not
   survive being skipped. Hit this on the three save-confirmation checkboxes
   and the Notes field, right after `_mode_switch`'s Confirm button reruns.
   Fixed by backing each with an explicit `st.session_state` entry read as
   `value=`. See [[streamlit_widget_state_after_early_rerun]].
2. **Real, pre-existing bug, not introduced by this front**: dragging a
   phase boundary in the chart could silently move the WRONG boundary
   whenever two adjacent boundaries' tolerance hit-areas overlapped (an
   ordinary condition, not an edge case). Root cause: one `pointerdown`
   listener per boundary's hit-rect, so an overlap was resolved by DOM
   z-order (whichever rect was painted last won), never by geometry.
   Confirmed pre-existing via a throwaway `git worktree` of unmodified
   `develop-v2.1` — reproduces there identically, so the front's own
   initial hypothesis (the new three-curve overlay chart broke boundary
   identification) was investigated and ruled out (reproduces with zero
   overlays active) before any fix was applied. Fixed with one chart-level
   listener that picks the target by distance to boundary geometry.
   `setStart`/`setTol`/`onMove`/`onKey` — the pointer/keyboard code that
   only ever reads `clientX`/step index, never a curve value — are
   untouched by this fix, confirmed by diff. Verified with a new invariance
   test: dragging never changes the number of phases, only `start_idx`.

Also fixed, found only once real Chromium became available for this
front's browser suite: two `tests/browser_harness.py` selectors broken by a
Streamlit version's migration to react-aria components (slider `role`,
combobox value storage in an `input` attribute rather than text) —
confirmed pre-existing on `develop-v2.1` too, not caused by the navigation
move; and a ~3px viewport overflow at 1440x800 fixed by a chart-height
budget bump, re-measured at 1440x800 / 1680x950 / 1920x1080 to confirm no
shrinkage on the two larger sizes.

**Verification:** `tests/test_label_browser.py` (real Chromium, branch tip
`f300420`, pre-merge): 29/29 passed. Full project suite, run on merged
`develop-v2.1` (`8102334`) in the dedicated `cyclophaser` conda env (item
12): **1144 passed, 1 skipped, 95 warnings in 546.53s** — a first attempt at
this same run, from a shell where `python` resolved to the base conda env
(3.13) rather than `cyclophaser` (3.12), produced 2 failures and 1 error, all
three Playwright timeouts specific to that wrong environment (missing/
different browser binaries) — exactly the shadowing failure mode item 13
warned about, not a regression from this merge. Discarded once identified;
not the number recorded above.

**Data change carried in from this branch:** two manual labels Danilo saved
while testing (`20170794`, `s5dcc0f79`), and item 15's
[[synthetic-incipient-ground-truth-decision]] (registered separately, ahead
of this front closing, at Danilo's explicit request).

---

## 19. Front B — `distance` removed; premise refuted — **closed, PREMISE REFUTED, 2026-09-16**

> Item 18 is claimed by the v3.0 topology-proxy front, which lives on the
> unmerged branch `research/v3-topology-proxy`. This item is numbered 19 to
> avoid a collision when that branch merges.

Front B was commissioned on the hypothesis that the fixed-in-timesteps
`distance` extrema filter was producing mature phases that were too short on
`20160735` and `20203947`, with a view to letting `length_scale` govern it. The
read-only diagnosis refuted the premise: under the reference config
(`research/labels/configs/cyclophaser_params-9.yaml`, `distance=5`) the filter
removes **zero** extrema across all 47 training series — every one of the 63
interior extrema removed in the split goes by relative prominence. Swept over
the whole split, `distance` removes nothing up to and including 14, removes one
inert extremum at 15–18, and first changes a phase at 20. `length_scale`, in
turn, never reaches the mature window under `mature_method="amplitude"`
(`find_stages.py:309` is in the `derivative` branch alone), so the proposed
coupling would have joined two controls that are both inert on mature. Because
the redundancy is with `prominence_relative` rather than a mode switch — a UI
guard cannot express "already done by another parameter" — and because
`distance` was added after v2.0.0 (`969904b`) and never published, Danilo's
decision was to **remove it from the package and the app** with no compatibility
shim. Diagnosis: `research/labels/diagnostics/front_b/`; removal rationale and
the sweep table: `research/inert_params/REPORT_inertia_sweep.md`.

### (a) OPEN backlog — the mature phase ends EARLY, not just starts late

Item 17(e) registered that the detector's mature **starts** late at every
labelled synthetic boundary. Measured here on the 47 training series (real and
synthetic), over 45 overlap-paired labelled mature windows, the end is early by
a comparable median and a far worse tail: start deviation median **+2**
(−3…+9), end **−2** (−34…+3), duration **−5** (−40…+3). The mature window is
squeezed from both sides, so 17(e) is half the picture. Not investigated.

### (b) OPEN backlog — `derivative` + `length_scale="global"` yields no mature at all

On both front-B target tracks, `mature_method="derivative"` with
`length_scale="global"` returns **no mature phase whatsoever** (`local` returns
3). Observed during the causal sweep and not pursued; it may be the same
global-denominator inflation already described in `find_stages.py`'s comment on
`threshold_decay_length`. Not investigated.

### (c) OPEN backlog — the real cause of short matures was never addressed

The measured drivers of short mature windows are `mature_amplitude_fraction`
(width, symmetric: `20160735`'s labelled-overlapping window goes 13 → 32 → 45
steps as the fraction goes 0.95 → 0.90 → 0.70) and `prominence_relative`
(cycle inventory: it leaves enough z extrema to cut one labelled cycle into
four detected ones). **20 of the 47 training series carry at least one detected
mature shorter than 7 steps** (14 of 35 real, 6 of 12 synthetic). Front B
changed neither parameter — removing `distance` does not touch this. Whoever
picks it up should start from `research/labels/diagnostics/front_b/sensitivity.txt`.

### (d) OPEN backlog — `distance=25` changed `20160735`'s phases, and nobody scored it

The sweep recorded that at `distance=25` the phase output changes on five
series including `20160735`, and at 30 on eleven. **Whether any of those changes
is an improvement was never measured** — the front scored nothing above the
calibrated value, and the removal did not test that range. This is the one
substantive thing the removal forecloses: if a future front wants a separation
constraint on z extrema, it starts from scratch, and the history is
`research/labels/diagnostics/front_b/distance_sweep.txt` (regenerable only
against `develop-v2.1` @ `ab7f244`).

Observed in passing while guarding the app and recorded here without
investigation: `length_scale` is likewise unscored on these tracks. Switching
`local` → `global` under `params-9`/`amplitude` changes the phase output on
**`20160735`, `20191014` and `20203947`** — not through the mature window
(inert under `amplitude`) but through the intensification and decay duration
thresholds, and from there through the intensification/mature/decay neighbour
check that confirms a mature window. Which setting is *better* on those three
was never measured.


---

## 20. Mature detection — the `prominence_relative` × `mature_amplitude_fraction` trade-off — **part 1 closed, gate FAIL, premise CONFIRMED, 2026-09-17**

> Danilo's brief commissioned this front as "Item 19". Item 19 on this branch is
> already Front B (`distance` removed), and item 18 is claimed by the unmerged
> `research/v3-topology-proxy` branch, so the front is registered here as **item
> 20**. It is the same front; the number is the only thing that changed.

This front picks up item 19(c) — the real cause of short matures was never
addressed. The symptom: the mature phase comes out short or fragmented. Under
`params-10` (`prominence_relative=0.30`, `mature_amplitude_fraction=0.95`),
`20160735` has short troughs detected as mature where the manual label carries a
single mature of 33 steps, 145 → 178. Raising `prominence_relative` cleans that
case up but, by construction, also makes it harder to accept true extrema in
other series — so a single scalar adjustment may not be able to separate the two
effects. Part 1 of the front measures, **on the train split only**, whether any
combination of the two parameters fixes `20160735` without any training series
losing its mature. The trade-off is to be confirmed or refuted with numbers
before any new mechanism is proposed.

Out of scope, already decided: `distance` is gone (item 19) and `length_scale` is
not to be touched; mature follows the human label (item 15 / 17); the asserted
boundary margin is a fixed 6 (item 17(d)). `20150377` and `20206498` are in the
**test** split and stay out of this front.

### (a) Gate — declared before any measurement, config `params-10`

Stage 1 is descriptive, on the train split (35 real + 12 synthetic = 47 series).
Stage 2 is a grid over `prominence_relative` {0.20, 0.25, …, 0.60} ×
`mature_amplitude_fraction` {0.80, 0.85, …, 1.00} — 45 cells — with every other
parameter held at `params-10`.

**PASS** if at least one cell satisfies all of the following simultaneously:

- **(a′)** no training series that has a mature under `params-10` ends up with
  no mature;
- **(b)** `20160735` has exactly one mature, with |Δstart| ≤ 6 (label 145) and
  |Δend| ≤ 6 (label 178);
- **(c)** no training series that gets the full phase sequence right under
  `params-10` stops getting it right (checked series by series);
- **(d)** `20191014` and `20203947`: the sequence does not get worse, and the sum
  of |Δ| over the mature boundaries does not increase;
- **(e)** the incipient boundary is identical to `params-10` in every series;
- **(f)** the sequence score over the 12 synthetics does not drop.

**FAIL** otherwise. **Declared prediction: FAIL.**

**Next step if FAIL, declared now:** replace the height filter with a duration
filter — a mature candidate is accepted only if it sustains the window for ≥ 7
steps, the floor from the item-15 decision — *if* stage 1 shows that the lost
matures disappear in the prominence filter. If they disappear in the amplitude
window instead, a window rule will be declared before any test is run.

**Exposure on the record:** the 16 test cases were inspected visually under
`params-10` in the calibration app (bad cases `20150377` and `20206498`), and the
label for `20150377` was read during the split check. `20150377` will be scored
as a test result after the mechanism is chosen, with no adjustment afterwards.

<details>
<summary>Gate as Danilo wrote it (Portuguese, verbatim)</summary>

```
Portão Item 19 (declarado antes da medição, config params-10):
Etapa 1 descritiva no treino (35 reais + 12 sintéticos).
Etapa 2: grade prominence_relative {0.20,0.25,...,0.60} ×
mature_amplitude_fraction {0.80,0.85,...,1.00} (45 células), demais
parâmetros = params-10.
PASS se existir ao menos uma célula com, simultaneamente:
(a') nenhuma série de treino com mature sob params-10 fica sem mature;
(b) 20160735 com exatamente uma mature, |Δinício| ≤ 6 (rótulo 145) e
    |Δfim| ≤ 6 (rótulo 178);
(c) nenhuma série de treino que acerta a sequência completa sob
    params-10 deixa de acertar (série a série);
(d) 20191014 e 20203947: sequência não piora e soma de |Δ| das
    fronteiras da mature não aumenta;
(e) fronteira do incipient idêntica a params-10 em todas as séries;
(f) pontuação de sequência dos 12 sintéticos não cai.
FAIL caso contrário. Previsão declarada: FAIL.
Próximo passo se FAIL (declarado agora): substituir o filtro por altura
por um filtro por duração (candidato a mature só aceito se sustentar a
janela por ≥ 7 passos, piso da decisão E), SE a etapa 1 mostrar que as
matures perdidas somem no filtro de proeminência; se somem na janela de
amplitude, uma regra de janela será declarada antes de qualquer teste.
Exposição registrada: os 16 casos de teste foram inspecionados
visualmente com params-10 no app (bad cases 20150377 e 20206498), e o
rótulo de 20150377 foi lido durante a checagem do split. 20150377 será
avaliado como resultado de teste depois do mecanismo escolhido, sem
ajuste posterior.
```

</details>

### (b) Result — gate FAIL, 0 of 45 cells; the trade-off is real

Branch `research/item19-mature-prominence`, from `develop-v2.1` @ `5120856`.
`params-10` versioned and verified against the declared sha256
`c14755e3…047902d7`. Measured in the conda `cyclophaser` environment against the
working tree, not the published 1.7.3. No package code changed. The test split
was never read. Full write-up and tables:
`research/labels/diagnostics/item19/REPORT.md`.

**Stage 1, `params-10`, train (47 series).** Sequence 30/47 (real 18/35,
synthetic 12/12); mature within ±6 at both ends 32/47; 2 series with no mature; 9
with more than one mature block. The constant modal-sequence baseline scores
16/47, so the detector beats it by 14 series. `20160735` produces **four** mature
blocks (3, 8, 13 and 8 steps) where the label has one of 33.

The quantity `prominence_relative` compares is
`scipy.signal.peak_prominences` (`determine_periods.py:188`) on the filtered
vorticity, normalised at `:203-208` by the maximum over the surviving interior
set **per series and per extremum type**. The two distributions the front asked
about **overlap**: `20160735`'s three spurious candidates run 0.3037–0.5709,
the 32 valleys that generate a label-matching mature across the split run
0.3074–1.0000, and the shared band holds 2 of 3 spurious and 1 of 32 true values.

**Stage 2, the 45-cell grid.** **No cell meets all six criteria.** Criterion (b) —
`20160735` reduced to one mature within ±6 — is met in exactly **2 cells**,
`prominence_relative=0.60` with `mature_amplitude_fraction` 0.85 or 0.90, and both
fail (a′), (c), (d) and (f): `20191014` and `scfcf1387` lose their mature outright,
`scfcf1387` stops matching its sequence, and the synthetic score drops 12 → 11.
`params-10` itself scores 5/6, failing only (b). **The declared prediction was
FAIL and the measurement is FAIL.**

**Where the matures are lost.** In every informative cell (`maf < 1.00`) the
answer is **A — the prominence filter**: 2 of 2 series (`20191014` at
`prominence_relative ≥ 0.45`, `scfcf1387` at `≥ 0.55`) lose the flanking z peak
their valley needed, so no candidate is formed (`find_stages.py:261-262`). **B 0,
C 0, D 0.** C is 0 structurally, as item 20's pre-measurement provenance note
already established. The `maf = 1.00` column is degenerate (window collapses to
the valley) and is reported apart.

**Consequence for the declared next step.** The declared condition is met — the
lost matures disappear in the prominence filter — so the ≥ 7-step duration floor
is the mechanism to try, with no new rule to declare. But the follow-up
measurement asked for at closeout weakens it: `20160735`'s **spurious** blocks
widen along with the correct ones as `mature_amplitude_fraction` falls (3/8/8 steps
at 0.95, 5/12/12 at 0.90, 5/15/21 at 0.85, 7/19/24 at 0.80), so the floor must rise
with the window, and a floor high enough to remove all three destroys **17 of 32,
19 of 38, 31 of 36 and 30 of 32** correct matures at those four fractions. The best
ratio anywhere is `maf = 0.90`, and it still costs half of them. A duration floor
**alone** should not be expected to work. It is also a **new** mechanism in the
`amplitude` arm — `threshold_mature_length` is unreachable there — so the
deliberate decision against such a floor at `find_stages.py:288-302` has to be
revisited explicitly. Candidates that have not been measured: item 20(e).

**A blind spot in the gate, found at closeout.** `20205386` keeps a mature at
`prominence_relative=0.60` but a *different* one: its valleys at 41 (0.3115) and 61
(0.3074) are cut, the deepest valley at 82 survives, and the detected mature moves
from (60,62) — within ±6 of the label — to (81,84), 25 steps late. No criterion
catches it: (a′) exempts it because a mature still exists, (c) exempts it because
`20205386` did not match its sequence under `params-10` either, and (d) watches
only `20191014` and `20203947`. **The gate cannot see a mature that moves to the
wrong place without disappearing, unless the series' sequence was already
correct** — and 17 of the 47 training series are outside (c)'s protection on that
ground. It strengthens the FAIL (a third series is damaged at `pr = 0.60`) and it
is a lesson for the next gate's wording.

**How much weight the two counted losses carry.** `20191014`'s mature under
`params-10` is at 135–137 [**corrected: 135–139**, see 20(a)] against a label
of 43–69 — wrong by 92 steps — so losing
it is not clearly a regression. Stripped of that case, the FAIL rests on
`scfcf1387` alone, which fails (a′), (c) and (f) on its own. One series is enough
to fail the gate as declared, and `scfcf1387` is the cleanest possible case, but
the honest accounting is one clearly-correct mature destroyed, one badly-placed one
lost, and one displaced unseen.

### (c) OPEN — `mature_amplitude_fraction=1.0` raises `IndexError`

A documented-legal value (`0 < maf ≤ 1`, validated `find_stages.py:242-245`) that
crashes: `find_stages.py:152` indexes one past the end of the segment when
floating-point round-off puts `z[z_valley]` a part in 1e20 above
`level_prev = z_peak − 1.0 × (z_peak − z_valley)`, so the valley counts as a
violation. 2 of 47 training series hit it **on numpy 2.5.3 / scipy 1.18.0 /
pandas 3.0.5, Python 3.12.14**; an independent run on **numpy 2.4.4 / scipy
1.17.1 did not reproduce it**. The missing bounds check is unconditional in both
— only whether it fires is environment-dependent, which makes it harder to own,
not less real. The `maf = 1.00` column is degenerate either way, so the item-20
verdict does not move. The forward side (`find_stages.py:160`) has the mirror defect and
is worse because it is **silent**: it wraps to `index[-1]` and returns
`next_z_peak`, a maximally wrong window, instead of raising. Not fixed — this
front changes no package code.

### (d) ~~OPEN~~ **CLOSED by 20(a) below, 2026-09-17** — `mature_amplitude_fraction=0.90` is free improvement, unclaimed

Holding everything else at `params-10`, 0.95 → 0.90 raises matures within ±6 of
their label from **32/47 to 38/47**, leaves the sequence at 30/47 and the
synthetics at 12/12, and moves no incipient boundary. Not pursued here because it
does not fix `20160735`. It bears directly on item 19(a) — the mature window is
squeezed from both sides — and is the cheapest unclaimed gain the grid turned up.


### 20(a) — `mature_amplitude_fraction` 0.95 → 0.90 — **closed, gate PASS, 2026-09-17**

Closes 20(d) above, which registered this cell as the cheapest unclaimed gain the
item-20 grid turned up. Confirmed in isolation, with its own gate declared before
measurement.

**What changed, and why.** `mature_amplitude_fraction` 0.95 → 0.90, in the
calibration config only. The parameter sets the fraction of each side's
peak-to-valley amplitude a timestep must still cover to count as mature, so 0.95
admitted only the deepest 5% of the cycle and produced a window systematically
too short against the manual label — train medians: start +2, end −2, duration
−5. 0.90 doubles the accepted band and extends the window at both ends.
`prominence_relative` stays at 0.30. No other parameter is touched, and no line
of `cyclophaser/` changes.

**Gate, declared before measurement, measured with the instruments the
step-3 ruling assigns** — (a) and (e) with `pair_by_overlap`
(`research/labels/diagnostics/item19/item19_core.py:130`, both ends, fixed margin
6), (b) with `evaluate_against_labels.py` / `score_phase_sequences`:

| | predicted | measured | |
|---|---|---|---|
| (a) matures within ±6 at both ends | 38/47, M95 ⊆ M90 | **38/47**, `M95 − M90` = **∅** | PASS |
| (b) sequence | 30/47, S90 = S95 | **30/47**, both differences **∅** | PASS |
| (c) synthetics | 12/12 unchanged | **12/12 → 12/12** | PASS |
| (d) incipient boundaries | identical case by case | **0 of 47 differ** | PASS |
| (e) `20205386` | boundary stays within ±6 | **YES both configs** (60–62 → 60–63) | PASS |
| (f) suite, package diff | 1130 passed, 0 failed; empty diff | **1130 passed, 0 failed**; diff **empty** | PASS |
| (g) clean run, no degenerate window | 47/47, no 1-step mature, none ending on the next z peak | **47/47**, **0 and 0** | PASS |

**The six series that join**, nominally: `20150436`, `20160735`, `20170342`,
`20180628`, `20180733`, `20207822`. None leaves — `M95 − M90` is empty, so the
gain is strictly additive over the nominal set, not a net total hiding a swap.

**Caveat, and it is the important line in this subsection: 38/47 is a
best-block metric, not a cleanliness metric.** `pair_by_overlap` pairs the
detected block with the largest overlap against the label, so a series can count
as a hit while remaining fragmented. `20160735` is exactly that case: at 0.90 it
emits four mature blocks — 5, 12, **32** and 12 steps — and enters the 38 because
the 32-step block at 150–181 matches the 33-step label at 145–177 (Δ +5 / +4).
The detector still produces four matures where the label has one. `20203947`
is fragmented the same way, four blocks of 6, 7, 8 and 8 steps, and does *not*
reach the 38. So **38/47 means "the best mature is in the right place", not "the
detection is clean"** — and that is precisely why the sequence score is pinned at
30/47 on both sides of the change. Any reading of 38/47 as a detection-quality
number is wrong.

**Accepted limitation of the instrument.** `pair_by_overlap` scores only
`lab_mat[0]` (`item19_core.py:187`), so the second labelled mature of
`20203947`, `s6b542eee` and `sbd6c6920` is never scored, in **either**
configuration. Both totals — 32/47 and 38/47 — are over 47 **series**, not 47
matures. This belongs to 20b/20c, not to this front.

**Corroboration from outside the gate.** `evaluate_against_labels.py` on both
configs, over the same 30 sequence-matching series on each side: mature start hit
56.7% → **73.3%** (MAE 2.23 → 1.73), decay start 65.6% → **93.8%** (MAE 2.62 →
1.41), all boundaries 61/89 → **75/89**. The decay gain follows mechanically from
the mature window extending forward — the mature→decay boundary lands closer to
the label. The two runs' output differs in the mature and decay lines and nowhere
else; the incipient block is byte-identical, which is an independent confirmation
of (d).

**Side effect that moves the starting point for 20b and 20c.** In `20160735` the
true block grows from 13 to 32 steps while the spurious ones grow too, so the
largest-spurious / true ratio falls to 12/32 = **0.375** — below any genuine
ratio in the labels. A depth rule (20b) or a duration floor (20c) calibrated
against the `params-10` window is calibrated against the wrong window; both must
be re-derived on the 0.90 window.

**`20180733` changed category.** It now hits the mature boundary (two blocks,
paired 135–146 against label 129–150) but its sequence is still wrong. It is one
of the three problem-C cases (a `residual` where the label continues in `decay`).
This does **not** resolve C; it moves C's starting point, and C should be
re-diagnosed on 0.90 rather than on `params-10`.

**`CHANGELOG.md` deliberately not touched.** A recorded decision, not an
omission: the CHANGELOG describes the package, and no package line changed in
this front. **Still correct** — re-checked 2026-09-21, see the third correction
below.

#### Correction added 2026-09-21 by front 20(c) — the package default is 0.90, and there is no deferred API decision

`research/labels/README.md` carried the claim that "`mature_amplitude_fraction`
in `cyclophaser/` remains **0.95**" and that "moving the default is a public-API
decision, deferred until after fronts 20b and 20c". **Both halves are false**,
and the text has been corrected in place.

The package default is **0.90** and has never been anything else. It entered at
that value in `f38082f`, the commit that introduced `mature_method="amplitude"`
(`determine_periods.py:734` and `:1154`, both `= 0.90`).
`git log -S 'mature_amplitude_fraction: float = 0.95' --all -- cyclophaser/`
returns **nothing**: that default never existed. The 0.95 was the value carried
by the calibration configs `params-9` and `params-10`, and was mistaken for the
package's.

Two consequences for the record. First, front 20(a) is better described than it
was: it moved the **config** from 0.95 **to** the package default, rather than
away from it — which is also why it needed no package line and no CHANGELOG
entry. Second, **the deferred public-API decision does not exist and must not be
carried as pending work** by 20(b), 20(c) or any successor. `CHANGELOG.md`
remains correctly untouched.

#### Two corrections to the earlier record

1. **`20191014`'s mature under `params-10` is 135–139, not 135–137.** The
   five-step window is what the detector produces; under `params-11` it is
   134–140. The figure 135–137 appears in the item-20 documents and is wrong.
   The case still misses by ~92 steps against a label starting at 43 in both
   configurations — unchanged in kind, and not a regression of this front — but
   the recorded number was incorrect.
2. **The repository has two measuring instruments with different definitions of
   "a correct mature", and until now no document said which governs what.**
   `score_phase_sequences` scores only series whose whole phase sequence matches
   exactly, compares phase **starts** only, and uses each label's own
   `tolerance_idx`; `pair_by_overlap` scores **all** series, compares **both
   ends**, and uses a fixed margin of 6. They are not interchangeable, and a gate
   stated in one instrument's numbers cannot be checked with the other — front
   20a was halted at its step 3 for exactly this reason before the ruling arrived
   (`research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md`). **Open debt:
   pick the governing instrument per quantity and say so in one place.** To be
   resolved in the repository clean-up front, alongside the `expected_starts_idx`
   removal.

**Reproduced in two environments**, which is worth stating because this code has
shown version sensitivity elsewhere: python 3.12.14 / numpy 2.5.3 / scipy 1.18.0,
and independently on numpy 2.4.4 / scipy 1.17.1 from a clean clone with a
separate driver — 32/47, 38/47, `M95 − M90` empty, S90 = S95, 12/12, 0 of 47
incipient boundaries moved, `20205386` 60–62 → 60–63, zero pairing ties, zero
one-step matures, and the same six series joining. The numbers are robust to that
version difference, unlike `mature_amplitude_fraction = 1.00`, whose `IndexError`
reproduces on one and not the other (20(c) above).

**Artifacts.** Config `research/labels/configs/cyclophaser_params-11.yaml`,
sha256 `24dd7f22b76d98cf0cab0b18ff040e010209604a8485007551095e9622abe420`.
Report, tables T1–T8, raw record and both evaluation outputs in
`research/labels/diagnostics/item20a/`.

### 20(e) — candidate mechanisms not yet measured

Registered, not implemented, not scored. Each is a **separate** candidate, and
none of them has been measured on any split. They exist because part 1 refuted
the mechanism it tested: `prominence_relative` and `mature_amplitude_fraction`
are one degree of freedom against a fragmented mature, and part 1's own follow-up
measurement (`REPORT.md` §3) shows that a duration floor on its own is no more
separable — a floor high enough to clear `20160735`'s spurious blocks destroys
between half and all of the correct matures at every amplitude fraction tested.

**(i) ~~A duration floor on mature candidates, measured over the window actually
chosen — not over `params-10`.~~ — RETIRED 2026-09-21 by front 20(c); see item
23.** The original entry read: this is the next step the item-20 gate declared
in advance, and the condition that triggers it was met (every informative loss is
code A, the prominence filter). Part 1 measured only the un-measured version of
it: "≥ 7 steps at `mature_amplitude_fraction=0.95`" removes one of `20160735`'s
three spurious blocks and 11 of 32 correct matures. Whatever window a future front
settles on, the floor has to be calibrated **on that window**, and the numbers in
`REPORT.md` §3 say a floor alone is unlikely to be enough. It is also a **new**
mechanism in the `amplitude` arm — `threshold_mature_length`
(`find_stages.py:304-312`) is unreachable there — so the deliberate decision
against such a floor at `find_stages.py:288-302` has to be revisited explicitly.

**Why it is retired, and what is withdrawn.** Front 20(c) made exactly the
measurement this entry asked for — a **proportional** floor on the window
actually chosen (`params-12`: `mature_amplitude_fraction = 0.90`,
`mature_min_depth = 0.80`) — and it **failed on premise**. The reading that
survived here, that *a proportional duration floor measured at
`mature_amplitude_fraction = 0.90` is viable and only wants calibrating*, is
**withdrawn**. The failure is structural, not a matter of finding the right
number: in `20205386` the anchor block is itself spurious under both
implementable anchor definitions, and across the five real multi-block series
duration **anti-correlates** with veracity in two of them (`20205386`,
`20180733`). No choice of floor repairs that.

The `~0.45` figure this entry's successor inherited is additionally **orphaned**:
it was derived from `20160735`'s four-block fragmentation under `params-11`, and
front 20(b) reduced that series to a single block `(150,181)`. The evidence
behind the number is gone.

An **absolute** duration floor was already refuted by item 20 (at 0.90 it would
demand ≥ 13 steps and destroy 19 of 38 correct matures). With the proportional
form now refuted too, **duration is closed as a discriminator** on this split,
in both forms. Candidates (ii), (iii) and (iv) below are untouched by this and
remain open.

**(ii) Absolute valley depth, as distinct from prominence.** `peak_prominences`
returns the **smaller** of the two climbs from a valley to its bounding peaks, so
a deep minimum sitting next to an even deeper neighbour scores low, and a shallow
dip between two modest bumps can score high. The proposed alternative is the
valley's depth measured against the **series minimum** (or against the series'
own dynamic range) — a global quantity the current filter never computes. Part 1
gives a reason to expect it to behave differently: 30 of the 32 correct matures
are generated by their series' single deepest valley, which is precisely the
population an absolute-depth criterion selects and a relative-prominence
criterion only approximately recovers.

**(iii) The asymmetry between the two flanks.** Prominence collapses the two
climbs into their minimum and throws the rest away. The ratio (or difference) of
the previous-peak climb to the next-peak climb is information the detector
currently discards, and it is exactly the quantity that distinguishes a genuine
mature — a deep minimum flanked by comparable intensification and decay — from a
pause on one side of a larger cycle. Untested.

**(iv) The leanest variant: one mature per cycle, anchored on the deepest
valley.** Rather than filtering extrema and hoping the survivors produce one
window, select the mature directly: the deepest valley of the series gets the
mature, and a second is admitted only if its **absolute depth is comparable**
(criterion (ii)). Two facts from part 1's train split motivate it: **41 of the 47
labels carry exactly one mature** (3 carry none, 3 carry two), and **30 of the 32
detected matures that match their label are generated by the series' deepest
valley** (relative prominence exactly 1.0000). Under that rule, `20160735`'s three
spurious blocks never form, because they are not anchored on the deepest valley —
without touching any threshold.

Candidates (ii), (iii) and (iv) come from **Danilo's intuition about what
prominence throws away**, recorded here on 2026-09-17 before any measurement, so
that whichever is taken up is scored against a gate declared in advance, as items
19 and 20 were. **None of the four has been measured.** Any front that picks one
up starts by declaring its gate and its prediction, and the frozen test split
(`research/labels/split.yaml`) stays untouched until a mechanism is chosen.

---

## 21. Calibration app — Benchmark tab, published-version snapshots, sidebar in execution order — **closed, PASS, 2026-09-18**

Branch `research/item5-benchmark-tab`. **No change to `cyclophaser/`** (verified:
empty diff against `develop-v2.1`).

### What the front delivered

* **A Benchmark tab** holding N configurations side by side over the same
  cyclones, aligned by cyclone, each column carrying its own provenance: the
  sha256 of its source YAML, the commit of the code actually running, the keys
  the current signature ignores, the keys it fills from defaults, and a warning
  when the file predates the filter fix.
* **Two modes.** `Validation` and `Exploration` filter what is selectable and
  what is emphasised. They never decide whether a number exists: that is decided
  per cyclone by whether it carries a manual label
  (`benchmark_core.scoreable`), which every scoring path routes through. **A row
  without a label produces no scoring number in either mode.**
* **A reference column**, chosen explicitly, defaulting to the manual label.
* **Metrics without ground truth** — in Exploration each column is measured
  against the reference column and the block is labelled `relative to
  reference`: sequences changed; boundary displacement (median, max) where the
  sequence matches; phases appeared/disappeared per type; cyclones refusing an
  incipient phase. Distances, never accuracies.
* **Frozen snapshots of the published releases** (`research/snapshots/`) —
  1.9.4 and 2.0.0, 63 series each, 0 failures, generated by running each
  published wheel in its own isolated virtualenv with that release's package
  defaults. Version 1 is not expressible as a YAML in the current detector: the
  two releases have an identical 19-parameter public signature and the
  difference is in the code, so the reference has to be a recording.
* **The sidebar reorganised by execution order**, read off the source:
  1 Lanczos → 2 Savgol → 3 `find_peaks_valleys` → 4 intensification → 5 decay →
  6 mature → 7 residual → (8 `post_process_periods`, no parameter) →
  9 incipient. Two parameters that cross groups carry a note in their own
  widget: `length_scale` and `boundary_padding`.

### Gate

| item | verdict | measured |
|---|---|---|
| (a) app suite, no regression | **PASS** | 1204 passed / **0 failed** (base 1130) |
| (b) `cyclophaser/` diff empty | **PASS** | empty |
| (c) Benchmark tab under AppTest, public API only | **PASS** | 37 tests, three positive controls |
| (d) sidebar verified by automatic test | **PASS** | 35 tests; 28/28 public parameters, plus step-numbering assertion |
| (e) snapshot isolated + hashed + env confirmed | **PASS** | `c22eebe7…`, `944b51d8…`; app env editable-only |
| (f) Danilo's visual checkpoint | **PASS** | approved |

The three positive controls in (c): swapped columns; an unlabelled row producing
a score; and the mode leak (an uploaded track surviving into a Validation run).
Each was confirmed to fail when the behaviour it guards was removed, as were
(d)'s coverage and step-numbering assertions.

### Declared prediction, scored

> `>= 40 %` of the 51 real series with a different phase sequence between v1 and
> params-11, the divergence concentrated at the edges, because of the
> zero-padded filter convolution.

* **Count: CORRECT** — 41/51 (**80.4 %**) against v1.9.4, 40/51 (78.4 %) against
  v2.0.0, against a declared threshold of 40 %.
* **Localisation: PARTLY WRONG** — the divergence concentrates on the **leading**
  edge alone: 60 % of timesteps disagree in the first decile against 20–36 %
  elsewhere, and the **last** decile is the quietest region at 20 %. "Edges",
  plural, is not what the data show.
* **Mechanism: NOT ESTABLISHED** — the snapshot differs from params-11 in ~15
  parameters at once, so the measurement sizes the gap and attributes nothing.
  Zero padding remains a plausible, unmeasured explanation.

### Findings

**`decay_tail_amplitude_fraction` is read by `find_residual_period`
(`find_stages.py:588`), not by `find_decay_period`.** The name says decay and
the effect is in the residual step: the parameter decides whether a flat tail
after the last decay block is labelled `decay` instead of `residual`. Grouping
the sidebar by phase name would have put the control under Decay, where it does
nothing; it sits under Residual because the execution order was read off the
source rather than assumed. **This is a naming debt of the package, not of the
app** — the app can only describe it accurately. Renaming it is a public-API
change and belongs to a package front, not here.

**An isolated virtualenv does not isolate if the CWD is the repository.** The
current directory precedes site-packages on the search path, so `import
cyclophaser` resolves to the **working tree** and the installed wheel is
shadowed — silently, with no error, producing a snapshot of the wrong code.
Measured here: two freshly built venvs with `cyclophaser==1.9.4` and `==2.0.0`
both reported the working tree's `determine_periods.py` until the CWD was moved.
This is the same class as item 13 and it survives the fix recorded in item 12 —
that one was about the conda environment, this is about the CWD, and a correct
environment does not protect you. `research/snapshots/make_published_snapshot.py`
now **refuses to run** unless `cyclophaser` resolved inside the running
interpreter's own environment, and is invoked with `-P` from outside the repo.

**A file's sha256 is a poor instrument when the file carries a timestamp.**
Re-running the snapshot generator produces a different file hash with identical
content, because `generated` changes. Verifying that a recorded artefact is
sound therefore means comparing **field by field, ignoring the timestamp** — done
for both snapshots, which reproduce exactly in `records`, `counts`,
`public_signature`, `module_file` and `has_collapse_plateaux`. Hash the payload,
not the file, whenever reproducibility is the question being asked.

### Open defect — handed to the clean-up front (item 6)

The cyclone upload block and the three loading checkboxes are rendered **before**
`st.tabs` (`app.py:2037-2205` against `:2305`), so they appear above **every**
tab. On the Benchmark tab they govern nothing: it reads the 63 records from disk
through `benchmark_core.load_all_series()` and never consults those checkboxes.
The caption *"No file uploaded — using `example_file.csv` as default"* is
therefore **false on the Benchmark tab**, where 63 records are in fact available
and selectable. The natural fix is to move the block inside `with tab_cal:`.
**Deliberately not fixed here:** it changes the Calibration tab, whose layout did
not go through the visual checkpoint this front's gate required.

### Debt that remains

**Two instruments with different definitions of a correct mature.**
`evaluate_against_labels.py / score_phase_sequences` refuses to pair boundaries
when the sequence does not match; `item19_core.pair_by_overlap` pairs the
largest-overlap block against a fixed margin of 6. The tab **declares which
number came from which instrument and never sums them**; the general resolution
stays open, as it was before this front.

**Portuguese sections in the app README** (`Instalação`, `Como rodar`, `Formato
do CSV`, `Modos de exibição`), which predate this front. Everything this front
wrote — interface, sidebar, tab, and its own README sections — is in English.
**Permanent rule: the app interface is in English.**

### Also done

`research/labels/configs/` now holds all **eleven** configurations
(`cyclophaser_params-1` … `-11`), each exactly as the app exports it, with
`metadata.cyclones_used`. Only 9, 10 and 11 were there before, which would have
left the tab unable to span the history it exists to show. `params-10` is
`item19_core`'s frozen instrument and was not touched. See
`research/labels/README.md` for the eleven hashes.

---

## 22. Front 20(b) — `mature_min_depth`, a depth floor on mature detection — **stage 1 gate FAIL (premise), stage 2 closed, PASS, merged 2026-09-21**

Branch `research/item20b-depth-rule`. Two stages with opposite results, and both
matter: the separability premise the front was built on is **false**, and the
rule built on it nonetheless passes its gate. Authorised by Danilo at 0.80.

### Stage 1 — does valley depth separate true matures from spurious ones? **FAIL**

Measured over the 46 valleys that generate a mature block across the 35 real
train series under `params-11` (32 true, 14 spurious), with two depth
definitions: `D1 = (z_max - z_valley) / (z_max - z_min)` and
`D2 = |z_valley| / |z_min|`.

| | min(TRUE) | max(SPURIOUS) | separates? |
|---|---|---|---|
| D1 | 0.8805 | **1.0000** | **NO** |
| D2 | 0.9272 | **1.0000** | **NO** |

**It is the premise that fails, not the threshold.** Three spurious valleys are
their own series' deepest point (`20171179` v45, `20181046` v26, `20205386` v82,
all at exactly 1.0000), so the spurious population reaches the ceiling and no
threshold can sit above it. The decisive case is **`20205386`, where depth orders
the valleys backwards inside one series**: the true valley 61 (0.8805) sits
between a spurious 41 (0.8687) and a spurious 82 (1.0000). The FAIL survives
excluding the two series with no labelled mature, and survives recomputing D2
against physical zero on the raw series. **Do not re-run this as a sweep** — a
sweep cannot change it.

Restricted to `20160735` alone, both D1 and D2 **do** separate, cleanly
(+0.2923 / +0.3192). The motivating case is as favourable as hoped; the other 34
refuse.

Three corrections to the record came out of stage 1:

* **The series feeding mature detection is the FILTERED `z`
  (`vorticity_smoothed2`), and its mean is NOT ≈ 0.** It keeps a median **65 %**
  of the raw mean, because the Lanczos band-pass does not reject DC at
  `window = len//2` (`sum(weights)` median 0.629 — documented in
  `lanczos_filter.py`). The offset is a median 0.93× the series' own range. The
  baseline still is not physical zero: the DC gain varies **0.2408–0.8343**
  across series, so `|z|` ratios are not on a common baseline between series.
* **`s6b542eee` and `sbd6c6920` are SYNTHETIC**, not real train series. Among the
  35 real, exactly **one** (`20203947`) has more than one labelled mature, and
  both of its labelled matures are already detected under `params-11`.
* **The "deepest valley" recount is 36 of 38 under `params-11`, not 30 of 32.**
  The old figure was `params-10` **and** used `prominence_relative == 1.0` as a
  *stand-in* for depth — prominence is the smaller of a valley's two climbs, not
  its depth. They agree here (36 either way) but are not the same quantity.
  Exceptions: `20205386` and synthetic `s6b542eee`. All six entries new since
  front 20(a) sit on their series' deepest valley.

### Stage 2 — the rule, implemented anyway at the fixed floor 0.80. **Gate PASS**

`mature_min_depth`, a float in `[0, 1]`: a z-valley may generate a mature block
only if its `D1` reaches the floor. The rule lives entirely in
`find_stages.find_mature_stage`, as a filter on the valley list; it touches
neither the extrema filter nor `prominence_relative`, so no other phase can move.
It applies to both `mature_method` values, and it is **not a cap on the number of
matures** — every valley clearing the floor still emits its own block.

`research/labels/configs/cyclophaser_params-12.yaml` = `params-11` + `0.80`,
sha256 `39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3`.

**Default 0.0 is a proven no-op**: the whole `periods` column of all 47 train
series, hashed against a clean `develop-v2.1` worktree — package defaults
`b01b16b6…` and `params-11` `b65551009b…` byte-identical across both trees, and
an explicit `0.0` equal to an absent key.

| criterion | 0.80 (merged) | 0.85 (diagnostic) |
|---|---|---|
| (a) `20160735` | 4 blocks → **1**, `(150,181)` | same |
| (b) `20203947` | both labelled matures kept | same |
| (c) sequence | **31**/47 (base 30) | 32/47 |
| (d) synthetic sequence | 12/12, min D1 0.9922 | same |
| (e) mature boundary | 38/47, incipient unchanged, no displacement | same |
| (f) suite / latent defects | 1205 passed, 0 failed; `:152`/`:160` 0 | same |

Both floors pass; **0.80 is the merged value, by Danilo's decision.**

### What the rule does NOT fix — read before building on it

* **`20205386` is completely unchanged.** All three of its valleys clear 0.80, so
  both spurious blocks survive. The series stage 1 identified as the one that
  refuses depth still refuses it.
* **`20160735` still fails its sequence.** Its four blocks correctly became one,
  and the sequence still does not match the label. Removing the spurious matures
  was necessary but not sufficient for the case that motivated the front.
* **The margin rests on one sample.** 30 of 32 true valleys are at `D1 = 1.0000`
  *exactly* — they ARE the series minimum, so a spiky `z_max` cannot flip them.
  But `20205386` v61 (0.8805), the only true valley that is not its series'
  minimum, lives in a series whose `z_max` sits **0.4874** of the range above the
  next peak; under an adverse denominator its D1 falls to 0.7669 and it would be
  **cut**, losing a true mature. The 0.08 margin is propped up by a single point.

### Collateral, deliberate

* **`determine_periods.py` carries plumbing only** — signature default,
  `args_periods` entry, docstrings, in `get_periods` and the `determine_periods`
  wrapper. No logic. It was unavoidable: `get_periods` takes no `**kwargs` and
  builds `args_periods` from an explicit literal, and every calibration driver
  filters `phase_params` against its signature, so without a signature entry the
  parameter is dropped before reaching `find_stages` and `params-12` would
  silently behave as `params-11`.
* **`tools/calibration_app/app.py` declares the parameter**, because
  `tests/test_sidebar_coverage.py::test_every_public_parameter_is_declared`
  enforces exact signature coverage in both directions and failed until it did.
  On import the key is applied when present but not reported missing when absent,
  which needed an explicit subtraction from `_REQUIRED_PHASE_YAML_KEYS`:
  membership of `_OPTIONAL_PHASE_YAML_KEYS` only suppresses the "unknown key"
  warning, it does **not** make a key optional — a key must be in
  `_YAML_PHASE_MAP` to be applied at all, and `_REQUIRED` is derived from that
  map. `params-1` … `params-11` all import clean.

### Fill-in and defect H

Seven blocks removed across five series. **No series lost a label match or a
sequence match**; one gained a sequence (`20170794`). Five vacated ranges are
closed over by the neighbouring intensification/decay; two become **residual**
(`20160735` 211–258 and `20170794` 119–223) — a real change in how those tails
are described, even at no cost on either metric.

Defect H (`find_stages.py:982`, unconditional incipient overwrite) was checked
**actively**: the overwrite reaches index 9 and 12 in the two series that have
one, and the earliest removed block starts at 7 in a series whose overwrite is
`None`. **No removed block is touched**, so every fill-in reading is the
detector's own output, not the overwrite masking it.

### Still open

* The two latent defects of `_amplitude_mature_bounds` — `find_stages.py:152`
  (loud `IndexError`) and `:159`/`:160` (**silent** wrong window) — remain
  unfixed. Both fired **0** times here, checked by recomputing `amp_prev < 0` /
  `amp_next < 0` for every valley rather than by absence of an exception.
* Whether `20205386` and `20160735`'s sequence want a different instrument
  altogether. Stage 1 says it will not be depth.

Artefacts: `research/labels/diagnostics/item20b/` — `REPORT.md` (stage 1),
`REPORT_stage2.md`, `depth_table.csv`, the drivers, and before/after figures for
`20160735` and `20205386`. `item19_core.py` and `params-11.yaml` untouched
throughout.

---

## 23. Front 20(c) — proportional duration floor for `mature` — **stage 1 gate FAIL (premise), front closed, 2026-09-21**

Branch `research/item20c-duration-ratio`, commit `83fcd59`, pushed, **not
merged** (stage 1 was measurement only; there is nothing to merge into the
package). **No line of `cyclophaser/` was touched** — `git diff develop-v2.1 --
cyclophaser/` is empty.

### The question

The detector emits more than one `mature` block on series whose manual label has
one, which breaks the phase sequence even when the principal mature is correctly
placed. Proposal: reject a mature block whose **duration**, as a fraction of an
**anchor** block's duration in the same series, falls below a floor — a
plausibility rule per valley, never a cap on the number of matures, since a
cyclone can genuinely have several.

Stage 1 asked only whether such a floor exists. It does not.

### Answer — FAIL, and structurally, not by tuning

Under `params-12` (sha256 `39262f45…7ebec3`; `mature_amplitude_fraction` 0.90
and `mature_min_depth` 0.80 both frozen, neither swept), **7 of the 47 train
series** emit more than one mature block: `20150656`, `20180628`, `20180733`,
`20203947`, `20205386` (three blocks), and the synthetics `s6b542eee`,
`sbd6c6920`.

**In `20205386` the anchor is itself a spurious block, under both implementable
definitions.** Anchor A (block of the deepest valley, D1 = 1.0000 at v82) picks
`(80,85)`; anchor B (longest block) picks `(36,42)`. Neither matches the label.
The label-matched block `(60,63)` is the **shortest** of the three, duration 4.
A proportional floor never rejects its own anchor, so criterion (a) is
unreachable under A and B alike; under A the other spurious block is *longer*
than the anchor (ratio 1.167), so no floor reaches it either. The rule points
the wrong way: the block a duration floor most wants to discard is the one the
label calls correct.

This is the mechanism that was **predicted before measuring** (Danilo and
Claude): "FAIL of premise; in 20205386 anchor A probably lands on a spurious
block". Confirmed, unadjusted.

**And it is not a single awkward series.** `20180733` inverts duration against
veracity just as plainly: its **spurious** block `(31,43)` runs **13** steps
against the **12** of the true block `(135,146)`, which pairs with the mature
label 129–150. So in **2 of the 5 real multi-block series** — `20205386`, where
the true block is the shortest of three, and `20180733`, where the true block is
the shorter of two — duration and veracity point in **opposite** directions.
That is a property of the population, not an outlier, and it belongs to the
verdict rather than to a list of loose ends: a duration-based rule is being
asked to rank blocks on a quantity that anti-correlates with correctness in 40 %
of the cases it exists to fix.

| criterion | anchor A | anchor B |
|---|---|---|
| (a) removes both spurious blocks of `20205386` | **FAIL** | **FAIL** |
| (b) cuts no label-matched block in any of the 47 | PASS, `r ≤ 0.6667` | PASS, `r ≤ 0.5714` |
| (c) preserves both detected blocks of `20203947` | PASS | PASS |
| (d) removes no block of the 12 synthetics | PASS | PASS |
| (e) generalises beyond `20205386` | PASS (`20150656`, `20180628`) | PASS (same two) |

Anchor C (label-matched) was diagnostic only and never counted toward the
verdict; its band is empty too (`r > 1.7500` to clear `20205386` against
`r ≤ 1.0000` to keep the synthetics).

### The anchors disagree — the central measurement

They diverge in **4 of the 7** series: `20180733` (A≠B), `20203947` (C≠A=B),
`20205386` (**all three differ**), `s6b542eee` (A≠B=C).

**Instrument gap, recorded against this front's own measurement.** Anchor B
(longest block) **ties** in **3 of the 7** series — `20203947` (8 and 8),
`s6b542eee` (8 and 8), `sbd6c6920` (7 and 7) — and **no tie-break rule was
declared before measuring**. The driver's `max()` resolves a tie at the **lowest
index**, which is an implicit rule, not a stated one. One reported divergence is
an artefact of it: **`s6b542eee`'s "A≠B" is not a real divergence**, only
`max()` picking block 0 while anchor A picks block 1 on a D1 margin of
0.9999 vs 1.0000. The other two ties resolve to the same block anchor A picks,
so nothing else moves.

**The verdict is unaffected**: all three tied pairs have ratio exactly 1.000, so
no floor `r ≤ 1.0` touches them under either resolution, and criterion (a) fails
on `20205386`, which has no tie. But any future attempt at a duration rule must
**declare its tie-break rule before measuring** — on this split a tie is not
rare, it is 43 % of the multi-block series.

### Numbers worth not re-deriving

* **A cost-free floor does exist**, it simply does not do the job it was
  proposed for: `r ∈ (0.5333, 0.6667]` under anchor A (`(0.5333, 0.5714]` under
  B) removes the spurious second blocks of `20150656` and `20180628` and cuts
  nothing label-matched in any of the 47. It does not touch `20205386`,
  `20180733` or `20203947`. **Danilo's ruling, 2026-09-21: STOPPED backlog —
  recorded, not implemented.** See the ruling below.
* **The 0.48 ceiling in the premise does not apply.** `20203947`'s two
  *labelled* matures have durations 23 and 11 (ratio 0.4783), but its two
  *detected* blocks are both duration 8 — **detected ratio exactly 1.000**.
  Labelled duration ratios do not transfer to detected ones. The real ceiling is
  `20205386`'s own true block at 0.667 (A) / 0.571 (B).
* `20180733`'s spurious block is **longer** than the true one (13 vs 12): no
  duration rule in either direction separates that pair.
* Both synthetics are *correct* — each genuinely has two labelled matures, all
  four blocks match, both already pass the sequence test, and every ratio is
  exactly 1.000.

### Ruling on the window `(0.5333, 0.6667]` — stopped, not implemented

Danilo's decision, 2026-09-21. The window is **backlog, halted**. It is not
implemented by this front and is not handed to a follow-up as ready work. Three
recorded reasons:

1. **Its ceiling is set by the true mature of `20205386`.** The 0.6667 is not a
   comfortable margin discovered in open space — it is exactly the ratio of the
   one block in `20205386` that the label says is **correct**. The rule's safe
   upper bound is pinned by the very block the front was trying not to destroy.
2. **The 0.13 of slack rests on two points.** The floor side comes from
   `20150656` (0.5333) and the ceiling from `20205386` (0.6667). Two series
   define the entire usable interval; there is no third observation anywhere
   inside it.
3. **The sequence gain is unverifiable without implementing.** Removing a block
   rewrites `periods`, which `find_residual_period`, `post_process_periods` and
   `find_incipient_period` then read — the 20(b) fill-in lesson, where vacated
   ranges were closed over by neighbours in five series and turned two tails
   (`20160735` 211–258, `20170794` 119–223) into `residual`. Nothing here
   predicts what `20150656` and `20180628` would become.

**Reopening requires a NEW front with its premise redeclared.** Loosening this
gate after seeing the result is **forbidden** — that is the whole point of
declaring the gate in advance, and a floor rescued by relaxing criterion (a)
after (a) failed would be a floor fitted to the answer.

### The inherited `~0.45` candidate is orphaned — and retires a conclusion of item 20

The proportional-floor figure of `~0.45` carried into this front came from
`20160735` under `params-11`, where that series fragmented into four mature
blocks (5/12/32/12 steps). **That data no longer exists.** Front 20(b)'s
`mature_min_depth = 0.80` reduced `20160735` to a **single** block, `(150,181)`,
32 steps, which pairs with its label 145–177 — measured again here under
`params-12` and confirmed. The series that generated the number is no longer a
member of the population the number was meant to describe.

Consequently **item 20(e)(i) is retired**, not merely superseded: its standing
claim was that a proportional duration floor remained a live candidate once
measured "on the window actually chosen" rather than on `params-10`. That
measurement has now been made, on the chosen window (`params-12`,
`mature_amplitude_fraction = 0.90`, `mature_min_depth = 0.80`), and it **fails**
— for a structural reason (the anchor is itself spurious; duration anti-
correlates with veracity in 2 of 5) that no recalibration of the floor addresses.
The conclusion that "a proportional duration floor measured at
`mature_amplitude_fraction = 0.90` is viable" is **withdrawn**. See the amended
20(e)(i) above.

### Method note — attribution was verified, not assumed

`get_periods` does not report which `z_valley` generated which block, and the
blocks it returns have already passed through `find_residual_period`,
`post_process_periods` and `find_incipient_period`. The pipeline was therefore
replayed step by step with the real package functions, recording each eligible
valley's window from the real `_amplitude_mature_bounds`, and **the replayed
`periods` column was asserted equal to the single-call `get_periods` output on
47/47 series** before any per-block statistic was read. `pair_by_overlap` came
from the frozen `item19_core.py`; that module's `CONFIG` still points at
`params-10` and was not used — `params-12` was loaded independently.

Duration convention, declared before measuring: `end − start + 1`. Depth
`D1 = (z_max − z_valley)/(z_max − z_min)` on `df['z'] = vorticity_smoothed2`,
never the raw series.

### Latent defects `find_stages.py:152` / `:159`-`:160` — 0 firings

Independently re-confirmed by **recomputing the trigger on every valley**, not
by absence of an exception — the same conclusion item 22 reached, by the same
reasoning reached independently. Substituting the level definition gives an
identity, `margin ≡ −(1 − mature_amplitude_fraction) · amplitude` (verified
numerically to a relative error of **3.67e-16**), which collapses the trigger to
a **sign test**: either defect can fire only if the amplitude is `≤ 0`, i.e.
only if a valley's z sits at or above its own bounding peak's z.

Of **81** z-valleys in the 47 series, **59** reach the window code (the other 22
lack a bounding peak and hit the `continue` at `find_stages.py:328`-`329`) and
**52** are eligible after the 0.80 depth floor. All 59 were checked, not just
the 52. **0/59** firings of each defect; `min amplitude_prev = +5.116e-06`,
`min amplitude_next = +2.353e-07`, both strictly positive. Nearest to the sign
flip: `20205386` v61 and `20181046` v26. Both defects remain unfixed.

### Baseline, unmoved

Mature boundary within ±6 **38/47**; sequence **31/47**; synthetics **12/12**;
`series_sha256` **47/47**; suite **1205 passed, 0 failed**. Of the 16 sequence
failures only 5 are multi-mature-block series, so fragmentation of `mature` is a
minority cause of sequence mismatch on this split.

One instrument note, not a divergence: 38/47 is the item 19/20 convention
(`pair_by_overlap` against the **first** labelled mature only). A per-block scan
across *all* labels finds **39** series with a matched block; the one-series
difference is `20203947`, which matches on L1. Both are right for their own
instrument.

### New backlog items opened by this front

Three, addressable as 23(i)–(iii). None is measured; none carries a proposed
mechanism. Each needs a front with its own gate and prediction declared in
advance, as items 19–22 did.

**23(i) — `20205386` resists both instruments the project has built.** Its three
mature blocks are `(36,42)`, `(60,63)` and `(80,85)`; only the middle one matches
the label 56–64. **Depth does not separate them**: all three generating valleys
clear `mature_min_depth = 0.80` (D1 = 0.8687, 0.8805, 1.0000), and the true one
is *not* the deepest — item 22 stage 1 already failed on this series.
**Duration does not separate them either**: the true block is the **shortest** of
the three, so the anchor is spurious under both anchor definitions — item 23,
here. Two independent scalar discriminators have now been refuted on the same
series. A third front should not propose a third scalar without first saying why
this one would differ; composite depth×duration scores, explicitly out of scope
in both fronts, remain entirely unmeasured. This is the sharpest open case in the
mature-detection line.

**23(ii) — `20180733` has a spurious block longer than the true one.** Spurious
`(31,43)`, **13** steps; true `(135,146)`, **12** steps, paired against label
129–150. Any rule that ranks blocks by duration ranks this pair **backwards**,
whichever direction the rule points. Together with `20205386` this makes **2 of
the 5** real multi-block series duration-inverted. Note `20180733` is also one of
the three problem-C cases (a `residual` where the label continues in `decay`,
item 20(a)), so it is carrying two distinct defects and they should not be
conflated.

**23(iii) — `20170409` and `20190639` miss the mature boundary by exactly one
step.** `20170409`: detected `(60,66)` against label 55–73, **Δend = −7** against
the fixed margin **6**. `20190639`: detected `(88,104)` against label 81–105,
**Δstart = +7**, same margin. Both are single-block series, so neither is touched
by anything in this front — they are recorded because two of the nine misses in
the 38/47 baseline sit **one step** outside the instrument's threshold, which is
worth knowing before anyone reads 38/47 as nine qualitatively failed series. This
is a question about the margin's calibration, **not** a licence to widen it: the
margin is fixed at 6 by item 17(d) and moving it after seeing which series it
excludes is exactly the move this project forbids.

### Still open from elsewhere, untouched here

* **Whether removing a block displaces a surviving block's boundary is not
  measured** — it requires an implementation. `find_mature_stage` writes into
  `periods`, which `find_residual_period`, `post_process_periods` and
  `find_incipient_period` then read. This is the 20(b)/`20205386` lesson (watch
  the boundary, not the presence) and would have been stage 2's first check.
* The two latent defects of `_amplitude_mature_bounds` (`find_stages.py:154`,
  `:161`) remain unfixed; confirmed dormant on this split only.
* `20160735`'s remaining defect (two false intensification/decay cycles filling
  the gap before mature) was out of scope and is untouched.

Artefacts: `research/labels/diagnostics/item20c/` — `REPORT.md`,
`item20c_measure.py`, `item20c_anchors.py`, `item20c_facts.json`,
`item20c_tables.md`.

---

## Note

All items above were identified during the code review and testing phase that preceded
the **2.0.0 release**. None of them are implemented in this version. The 2.0.0 release
consolidates fixes and calibration tooling from the `fix/core-bugs` branch; any
methodological changes will be introduced in a subsequent release following proper
validation against the synthetic test suite and real-cyclone benchmarks.
