# FRENTE F(iii) — INEXPLICADA backlog (measured inert, no code-skip line found)

Per the front's gate (b): every inertia found by the sweep is either POR
DESENHO (a concrete line exists that does not read the parameter on that
branch) or INEXPLICADA. These three are INEXPLICADA — the parameter IS read
unconditionally on the cited line, and the branch taken does not depend on the
config axis the sweep varied; the flat result is a property of *this specific
51-track calibration set* at the tested threshold values, not of the code.
**None of these get a UI caption.** Fixing them (if they turn out to hide a
real defect) is a new front with its own measurement — out of scope here.

## 1. `threshold_intensification_gap` — INERT under default config

- Measured: 0/51 tracks changed across the full UI range (0.01–0.30, step
  0.005).
- Read unconditionally at `find_stages.py:386` (`threshold_intensification_gap
  = args_periods['threshold_intensification_gap']`) and used at
  `find_stages.py:424` inside `for i in range(len(blocks) - 1):` — a loop that
  only runs a gap comparison when a track has **more than one** contiguous
  intensification block under the default `threshold_intensification_length`.
- Not a reopening of the historical wrong-key bug (F(iii) brief, "NÃO
  reabrir") — that bug is confirmed fixed: the key read at line 386 is its
  own, not `threshold_decay_length`'s. This is a separate, new observation:
  under the DEFAULT configuration, this calibration set's tracks apparently
  never produce multiple intensification blocks whose gap straddles the swept
  range. Untested: whether a different `threshold_intensification_length` (or
  `length_scale='local'`) would expose tracks where the gap parameter bites.

## 2. `incipient_plateau_crossing` — INERT under (`incipient_method="plateau"`, `incipient_plateau_signal="derivative"`)

- Measured: 0/51 tracks changed between `"single"` and `"sustained"` (k=3,
  tau=0.20).
- Both branches are real, distinct code in `_incipient_plateau_boundary`
  (`cyclophaser/find_stages.py`, ~line 840): `"single"` returns the first
  index where `rel >= tau`; `"sustained"` returns the start of the first run
  of `k` consecutive such indices. They are NOT algebraically equivalent in
  general (that is the whole point of "sustained" existing — see
  `research/inert_params/inertia_matrix.csv`, this SAME parameter is clearly
  NOT inert under `plateau_sustained_vorticity`, changing 42/51 tracks).
- Working hypothesis (not verified beyond this dataset): under
  `signal="derivative"`, `rel(t)` is the pipeline's own smoothed `|dz|`, which
  tends to rise past tau and then KEEP rising rather than dip back below it —
  so the first sample at or above tau is, on this calibration set, already
  the start of a run of at least `k=3` consecutive samples above tau, making
  "single" and "sustained" agree by coincidence. `signal="vorticity"` is
  noisier and does not share this property (per the k-sweep result above).
  Untested: whether a noisier `signal="derivative"` track (if one exists
  outside this 51-track set) or a larger `k` would separate them.

## 3. (resolved during measurement, listed for completeness — NOT inert)

`decay_tail_amplitude_fraction` first measured INERT under `decay_tail_on`
(prominence filtering off), but that base config never creates the orphan-peak
precondition the feature's own docstring says it compensates for
(`find_stages.py:514+`, "compensates for an artifact of the prominence
filter"). Retested with `prominence_relative=0.10` also enabled: NOT INERT
(1/51 tracks changed). Not a backlog item — the original "inert" reading was a
sweep base-config gap (fixed in
`research/inert_params/followup_checks.py`), not a property of the parameter.
