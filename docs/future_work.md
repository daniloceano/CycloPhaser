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

## 3. Locally-adaptive thresholds

All seven detection thresholds are currently expressed as fractions of total series
length. This scales poorly for:
- Long series with a brief intensification that exceeds the fractional threshold but
  represents a physically real episode.
- Multi-cycle series where the second cycle is detected out of phase because the
  denominator (total series length) inflates all fractions.

A locally-adaptive approach — e.g., fractions of the local cycle length, or absolute
timestep counts derived from an estimated lifecycle duration — would generalise better
across the climatological range of cyclone lifetimes.

**Expected benefit:** highest-impact change for cross-cyclone threshold generalization;
likely to reduce the need for per-dataset manual calibration.

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
