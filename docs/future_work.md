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

**Not yet done:** wiring `length_scale` into `tools/calibration_app/app.py` (defaults
dict, YAML import/export map, UI control, `determine_periods` call) — left for a
separate pass since it touches several non-trivial locations in that app.

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
