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

## Note

All items above were identified during the code review and testing phase that preceded
the **2.0.0 release**. None of them are implemented in this version. The 2.0.0 release
consolidates fixes and calibration tooling from the `fix/core-bugs` branch; any
methodological changes will be introduced in a subsequent release following proper
validation against the synthetic test suite and real-cyclone benchmarks.
