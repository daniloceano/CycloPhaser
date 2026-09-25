# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — calibration app: flexible track reading (item 29)

**One reader for every track, recognised by content; `.txt` accepted; an
opt-in custom format; nothing accepted silently.** `cyclophaser/` is untouched.

* `tools/calibration_app/track_io.py` — `read_track(data, fmt=None)`, now the
  only way the app reads a track (`_run_process_vorticity`, `_gt_boundary_iso`,
  `benchmark_core.parse_cyclone_csv`). A file whose first line is
  `;`-separated with `time` and `min_max_zeta_850` is read by the exact
  `read_csv` call the app always used — bit-identical on all 64 bundled series.
  Every path is then validated: DatetimeIndex, strictly increasing, no
  duplicates, float64 vorticity with no NaN, at least 2 points; any failure is
  an error naming the cause.
* **Dates must be year-first** (`YYYY-MM-DD…`) unless an explicit date format is
  given. `parse_dates=True` reads `05/01/2015` as 1 May without a warning; every
  bundled track is already year-first.
* Both upload fields (Calibration, Benchmark → Exploration) accept `.csv` and
  `.txt`, with `help=` text describing the standard layout.
* **Custom track format** (off by default): separator, header yes/no, date and
  vorticity columns, optional strftime date format. A file read this way is
  normalised to the standard layout, previewed (parsed rows, first/last date,
  points, vorticity min/max; warnings for predominantly positive vorticity —
  the package assumes the southern hemisphere — and for magnitudes above
  1e-2 s⁻¹), and used only after an explicit confirmation. The Benchmark
  Exploration upload uses the same settings.

### Fixed — calibration app: no `use_filter=True` warning per cyclone

The "Apply Lanczos filter" checkbox yields a bool, and `process_vorticity`
warns on `use_filter=True` — so the grid showed one copy of that warning per
cyclone, asking the user to change a value they never typed. The app now passes
`'auto'` for `True` at its three calls into the package
(`package_args.package_use_filter`); `'auto'` and `True` select the same window
(`len(series)//2`), and filtered/smoothed series and phase maps are
bit-identical (128/128: 64 series × params-14 and app defaults). The warning
stays in the package for direct callers. The YAML export and import still carry
a bool, byte-identical to before.

### Changed — default behaviour

**`reclassify_index0` — the type of the extremum at index 0 is now decided
against the next surviving extremum, not against `z[1] - z[0]`. Default `True`.**

`get_periods` and `determine_periods` accept a new `reclassify_index0` bool,
**on by default**. On the final z extremum list — after the prominence filter
and after the boundary exception — let E1 be the extremum immediately after
index 0, **of either type**:

* index 0 typed `valley` and `z[E1] < z[0]` strictly → index 0 becomes `peak`;
* index 0 typed `peak` and `z[E1] > z[0]` strictly → index 0 becomes `valley`;
* a tie, or no E1 → nothing changes.

Only index 0 is touched; no other extremum is created, removed or retyped, and
the rule is applied to `z` alone (no stage function reads index 0's type in
`dz`/`dz2`).

**Why.** Index 0 is always an extremum: `argrelextrema` runs with `mode='clip'`
and non-strict comparators, so it compares `data[0]` against itself and the test
passes whatever the data does. Its *type* then came from the single difference
`z[1] - z[0]` — one finite difference on the sample the smoother had least
information about. Measured over the 51 calibration tracks and the 12 synthetic
series, that typed index 0 as a `valley` on 11 of 63 and opened the life cycle
with a `decay` the vorticity does not support on several of them.

**What moves.** Under the calibration reference (params-13 + the rule =
params-14) the output changes on 5 of those 63 series and is byte-identical on
the other 58, the 12 synthetic series included:

| series | before | after |
|---|---|---|
| 20180170 | `Ic > D > It > M > D` | `Ic > It > M > D` (now matches its manual label) |
| 20190325 | `Ic > D > It > M > D` | `Ic > It > D > It > M > D` |
| 20191014 | `Ic > D > It > D` | `Ic > It > M > D > R` |
| 20190639 | `Ic > It > M > D` | `Ic > D > It > M > D` |
| 20206498 | `Ic > D > It > D` | `Ic > It > D > It > D` |

`20190639` is the `peak->valley` branch and the one case where the rule *adds* a
`decay` block: it moves the `intensification` start from 13 to 26 against a
manual label that says 25 ± 5, at the cost of calling `[13, 26)` decay where the
label says incipient. Reviewed and accepted as a reclassification.

**When it can fire at all — read this before assuming your results moved.**
The rule needs an extremum to have been *removed* between index 0 and E1.
Raw `argrelextrema` output alternates, so the extremum right after a valley at
index 0 is a peak the series rose to and cannot lie below it; symmetrically for
a peak. What breaks that alternation is the prominence filter. **With
`prominence` and `prominence_relative` both None — which is what the package
defaults give you — the rule never fires: measured identical output with and
without it on all 64 series tried** (51 calibration tracks, 12 synthetic series,
the packaged example file;
`research/labels/diagnostics/frontA_idx0_c2/stage2_defaults_check.py`). So this
change affects only configurations that use a prominence filter, and no CI
reference baseline moved.

**Compatibility.** This is a change of default behaviour: a config that does not
carry the key now runs *with* the rule. To reproduce any earlier release — or
any calibration config from params-1 to params-13, all of which predate the rule
— pass `reclassify_index0=False`. `research/labels/configs/cyclophaser_params-14.yaml`
is the first config that states it. `find_peaks_valleys` also accepts the flag
but **defaults to False**, so a direct caller of that function keeps the
historical behaviour: the rule is a statement about the vorticity series a life
cycle is read from, not a property of extremum detection in general.

The calibration app carries a sidebar control for it ("Reclassify the extremum
at index 0", section 3), on by default.

Measured in full — 63-series table, figures, and the gate this change was
required to pass — in
`research/labels/diagnostics/frontA_idx0_c2/REPORT.md` and
`docs/future_work.md` item 28.

### Added

**`intensification_min_depth` — an opt-in depth floor on which candidate
segments may be accepted as intensification.**

`get_periods` and `determine_periods` accept a new `intensification_min_depth`
float in `[0, 1]`. A raw candidate segment (a z-peak and the next z-valley) is
accepted only when its normalised depth

```
D2 = (z[peak] - z[valley]) / (z_max - z_min)
```

measured on the series' own `z`, is at least this value. `D2` is the drop the
segment itself achieves as a fraction of the whole series' z range: `~0` for an
essentially flat stretch, negative for a segment ending shallower than it began,
`1.0` for one running from the series maximum down to its minimum.

**Why it was needed.** Until now a segment was accepted on
`threshold_intensification_length` alone — on *duration*, with no depth
criterion whatsoever — so a long flat stretch was labelled intensification.
`find_residual_period` then converts an intensification block with no mature
phase after it into `residual` to the end of the series. That rule is correct
and is **not** changed here: it implements the project's physical definition of
residual, namely that deepening with no subsequent mature stage lies outside the
cyclone's life cycle (a transient interaction, or TRACK contamination). But fed
a phantom intensification it faithfully wrote a phantom residual, over a stretch
the manual label calls decay. The floor supplies the missing criterion, so the
phantom segment never exists, the residual rule never fires on it, and the
preceding decay extends over the tail.

**Where it acts.** Per *raw segment*, after the duration test and **before** the
gap stitching controlled by `threshold_intensification_gap`. A stitched block's
endpoints are the first segment's peak and the last segment's valley, so its D2
is a property of the merged span and can be far smaller than either component's
— judging after the stitch would measure a different quantity from the one the
parameter is defined on.

**Calibration.** Over the 47 training series, 75 raw segments clear the duration
test. Exactly one falls below 0.15 — 20180733's spurious segment, at
`D2 = 0.0068` — and the smallest legitimate segment sits at `0.1714`. Nothing
lies between them, so every floor in `(0.0068, 0.1714]` selects the same
segments on that split. `research/labels/configs/cyclophaser_params-13.yaml`
records the reference value `0.05`.

A series whose z range is zero or non-finite has no depth scale; the floor is
skipped for it and a `UserWarning` says so, rather than the request being
silently ignored.

**Default `0.0` switches the floor off entirely**, and is a strict no-op: the
phase output over the 47 training series is byte-identical with the parameter
absent and with `0.0` passed explicitly, and identical to `develop-v2.1`'s
output for the same series in the same environment.

See `docs/future_work.md` item 22 ("Recorded while working front C") and
`research/labels/diagnostics/frontC/`.

**`mature_min_depth` — an opt-in depth floor on which valleys may generate a
mature phase.**

`get_periods` and `determine_periods` accept a new `mature_min_depth` float in
`[0, 1]`. A z-valley is allowed to generate a mature block only when its
normalised depth

```
D1 = (z_max - z[valley]) / (z_max - z_min)
```

measured on the series' own `z`, is at least this value — `1.0` at the series
minimum, `0.0` at its maximum. It applies to both `mature_method` values, since
it decides which valleys are *eligible*, not how the window around one is sized.

It is **not** a cap on the number of mature phases. Every valley clearing the
floor still produces its own block; a cyclone can genuinely have more than one
mature stage, and the rule is deliberately built to preserve that.

Why this is not part of the existing prominence filter: `prominence_relative` is
the *smaller of a valley's two climbs*, which is a different quantity from depth,
and it is applied in `find_peaks_valleys`, whose output feeds every phase.
`mature_min_depth` is applied inside `find_mature_stage` alone and so cannot move
an incipient, decay or residual boundary.

A series whose z range is zero or non-finite has no depth scale; the floor is
skipped for that series and a `UserWarning` says so rather than the filter being
silently ignored.

**Default `0.0` is a no-op**: every valley has `D1 >= 0` by construction, so the
filter admits all of them and the phase output is unchanged from prior versions.

### Removed

**`distance` extrema filter removed from the package and the calibration app.**

`get_periods`, `determine_periods`, `find_peaks_valleys` and `_refine_extrema` no
longer accept a `distance` argument, and the calibration app no longer offers the
control or writes the key. `prominence` and `prominence_relative` are unchanged.

`distance` required surviving same-type z extrema to be at least N timesteps
apart, and ran *after* relative prominence — on the set prominence had already
thinned. Measured over the 47 training series at the calibrated configuration
(`prominence_relative=0.30`, `distance=5`) it removed **0 extrema**: nothing is
removed at any value up to 14, one inert extremum at 15–18, and the first phase
change only at 20. It was redundant with `prominence_relative` throughout the
calibrated range.

**No compatibility shim, and none is owed**: `distance` was added after v2.0.0
(commit `969904b`) and never appeared in a release, so no published API carries
it. Passing it now raises the ordinary Python `TypeError`. A calibration YAML
that still carries the key imports cleanly — the key is applied to nothing and
reported as removed rather than as an unknown key.

`length_scale` is **not** removed. Under `mature_method="amplitude"` it no longer
scales the mature window, but it still scales the intensification and decay
thresholds (measured to change the phase output on 3 of the 47 training series),
so the app annotates it rather than disabling it.

Default behaviour is unchanged: the phase output over the 47 training series at
package defaults is byte-identical before and after
(sha256 `b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5`).

That digest is only meaningful together with the blob layout that defines it and
the environment that produced it, so both are now recorded per run in
`research/labels/diagnostics/front_b/default_behaviour_sha256.txt`. The value
above was first written under numpy 2.4.4 / scipy 1.17.1 / pandas 3.0.2 and has
since been reproduced **unchanged** under numpy 2.5.3 / scipy 1.18.0 /
pandas 3.0.5 (python 3.12.14), at both `17dc21f` and `7a87a10`. It is therefore
stable across every environment recorded so far — but that is a measured fact
with two data points, not a guarantee, which is why the table exists.

What the digest is *not* comparable against is a "default behaviour hash"
computed with a different blob layout. Concatenating the same phase strings with
different separators yields a different number over identical behaviour; such a
mismatch says nothing about the code. Use
`research/labels/diagnostics/front_b/default_behaviour_hash.py` rather than
writing a second digest.

See `docs/future_work.md` item 19 and
`research/inert_params/REPORT_inertia_sweep.md`.

### Changed (tests only)

**Synthetic timing test scored against manual labels.** `test_lifecycle_phase_timing`
now compares detected boundaries with `research/labels/manual_labels.yaml` on the
frozen synthetic series (hash-checked), instead of the hand-typed
`expected_starts_idx`. No change to the package. See `docs/future_work.md` item 17.

### Added

**Opt-in `incipient_method="plateau"` — a slope-based incipient boundary (behaviour
unchanged by default)**

`determine_periods(..., incipient_method="plateau")` places the incipient/next-phase
boundary at the end of the initial low-slope *plateau* — the leading stretch over
which the normalised slope `|dz|/max|dz|` stays below `incipient_plateau_tau`
(default 0.20) — instead of at `threshold_incipient_length` (0.4) of the distance to
the next dz extremum. The default remains `"geometric"`, which is byte-identical to
every prior version; verified over all 51 calibration tracks against `develop-v2.1`
and pinned in `tests/baselines/baseline_defaults_multitrack.csv`.

Motivation, measured at 01c4492 (see
`research/incipient_plateau/REPORT_incipient_characterisation.md`): at the point
where the geometric rule ends the incipient phase, `|dz|` has already reached a
median **58 %** (author's calibration) / **77 %** (package defaults) of its own
maximum — the rule is measuring a distance, not a slope. Two further findings scope
it: the `It → D → It` re-cut branch never fires (0/51, and it is structurally
unreachable — a smooth It→D transition must pass through a minimum, which is
detected as `mature`), and the catch-all `fillna` produces no incipient phase at all
on real data.

Unlike the geometric rule the plateau rule is **self-contained**: it scans from t₀
and does not use the case A/B/C dispatch. It declines to create an incipient phase
exactly when the plateau has zero length (`rel(0) >= tau`), which is what replaces
the case gating as the false-positive guard. `threshold_incipient_length` is ignored
under `"plateau"`, as `threshold_mature_length` is under `mature_method="amplitude"`.

Two structural options are exposed for validation: `incipient_plateau_signal`
(`"derivative"`, default, on `dz_dt_smoothed2`; or `"vorticity"`, on `np.gradient`
of the **unfiltered** input, immune to filter edge artifacts) and
`incipient_plateau_crossing` (`"single"`, default; or `"sustained"` requiring
`incipient_plateau_k` consecutive samples, robust to a spike inside the plateau).

Measured effect at `tau=0.20` over the 51 tracks:

| configuration | tracks with `incipient` | boundary Δ (median) | sequences changed |
|---|---|---|---|
| author's §3c calibration | 48/51 → **51/51** | −2 steps | 4/51 |
| package defaults | 49/51 → **7/51** | −5 steps | 43/51 |

**The plateau criterion is only definable once the t₀ boundary artifact is
controlled.** Under package defaults (`r(t₀)` median 0.526) the first sample already
exceeds any usable tau on most tracks, so the rule collapses to "no incipient phase"
on 44 of 51. It is intended for use with a calibration that keeps `r(t₀)` low. `tau`
and the two structural options are **not yet calibrated** — they await the author's
visual validation.

Also added: `SYNTHETIC_VALIDATION_PRESET` in `tests/synthetic/cases.py`, and a
"Load synthetic cases" mode in the calibration app that materialises the synthetic
suite alongside the real tracks and overlays the designed ground-truth incipient
boundary.

### Added

**`incipient_smooth_window` / `incipient_smooth_polyorder` — dedicated denoising
for the incipient probe (opt-in, default off)**

`incipient_plateau_signal="vorticity"` reads the rate on `d(zeta_raw)/dt`, which
is immune to the pipeline's edge artifacts and, for the same reason, exposed to
raw noise: on the 2 %-noise synthetic cases the normalised raw gradient at t₀ is
already 0.25–0.57, above any usable tau, so the criterion trips at the first
sample and yields no incipient phase at all.

A Savitzky-Golay pass is now applied to the raw vorticity **before** the probe
differentiates it, controlled by `incipient_smooth_window` (default `0`,
disabled — previous behaviour byte for byte) and `incipient_smooth_polyorder`
(default 3). It touches the incipient probe **only**: `df['z']` and `df['dz']`
are unchanged, so every other phase is unaffected and `use_smoothing` stays off
as decided in `docs/future_work.md` §4. Both parameters are ignored outside
`incipient_method="plateau"` with `incipient_plateau_signal="vorticity"`.

Savitzky-Golay rather than a moving average: a boxcar attenuates a sinusoid's
amplitude and smears its curvature, and curvature is what the probe reads.

Measured on the synthetic suite (`measure_incipient_smoothing.py`,
`REPORT_incipient_smoothing.md`): a window of 5–9 takes the designed-Ic cases
left with no phase from 1–2 down to 0, and makes `incipient_plateau_crossing=
"sustained"` unnecessary — single-crossing catches up with `k=3` once the rate is
reliable. **Goldilocks caveat, measured:** on real tracks `rel(t₀)` is *not*
monotone in the window (20170225: 0.44 → 0.66 at w=5 → 0.38 at w=7), so a wider
window is not reliably safer. No window is chosen here; it awaits visual
validation.

A curvature-based **knee** candidate (`argmax |d²z|`) was measured alongside and
deliberately **not** added to the package: like the rejected amplitude rule it
cannot decline (2/2 false positives on the linear-onset true negatives at every
window), and smoothing degrades it (worst error 2 → 23 timesteps). It lives in
the measurement script as a recorded negative result.

### Evaluated and rejected

**`incipient_method="amplitude"` — discarded by construction, not by calibration**

A third incipient rule was implemented and then removed: the incipient phase would
last until the cyclone had completed a given fraction of its first deepening,
`|z(t) - z(t0)| >= fraction * |z(first extremum) - z(t0)|` — the level-based
analogue of `mature_method="amplitude"`.

It fails for a structural reason rather than a tunable one. Amplitude measures an
*accumulated* quantity: `|z(t) - z(t0)|` is exactly 0 at t0 and the threshold can
only be met strictly after it, so **some prefix always qualifies as incipient**.
The rule can never return "no incipient phase" — not for a cyclone that is already
intensifying at the first sample, and not for one built with a deliberately steep
onset. Measured before removal, on the 51 calibration tracks it produced a boundary
on **51/51** (declining on none, against 48/51 for the geometric rule), and on the
two synthetic cases designed with a `linear` opening ramp — the shape whose whole
purpose is to have non-zero dz from the first timestep — it still emitted a 3-step
incipient phase.

No choice of `fraction` repairs this, because the defect is in the quantity being
thresholded, not in the threshold. The slope-based `"plateau"` rule keeps its
rejection mechanism (`rel(0) >= tau` is a zero-length plateau) and remains the
opt-in route under evaluation.

### Changed

**`use_smoothing=False` now disables the derivative smoothing too (behaviour change)**

`use_smoothing=False` skipped both Savitzky-Golay passes on the vorticity `z`, but
`process_vorticity` then fell into `if not window_length_savgol:` and picked an
*auto* window for the four Savgol passes applied to the first and second
derivatives — **15-91 timesteps** over the 51-track calibration set, i.e. *larger*
than any window a calibration had ever asked for explicitly. A caller switching
smoothing off still got the derivatives smoothed twice, with a window they never
requested. `use_smoothing=False` now means what its name says: the derivatives
`find_stages` consumes are the unfiltered `d(z)/dt` and `d²(z)/dt²`.

This is the change the derivative-Savgol block had been justifying with "not an
option because they are too noisy". Measured on the 51-track set (TRACK /
Gramcianinov vorticity) under the author's validated calibration
(`use_filter=true`, `cutoff_high=18`, `use_smoothing=false`, `length_scale=local`,
`mature_method=amplitude`):

| | `r(t₀)` | `r(t_final)` | phase sequences changed |
|---|---|---|---|
| before (auto window, 15-91) | 0.545 | 0.403 | — |
| after (derivatives untouched) | **0.068** | **0.060** | **1/51** |

`r(t₀) = |dz_dt_smoothed2[0]| / max|dz_dt_smoothed2|`, median over the set. The
edge artifact drops by ~8x while the phase output barely moves: 1/51 sequences
change, 39/51 tracks see at least one timestep relabelled, 3.5 % of timesteps
relabelled on average, and **no fragmentation** — total phase segments over the set
go 248 → 249. With the Lanczos boundary condition fixed
(`boundary_padding="reflect"`, see below), the derivative Savgol had become the
dominant remaining source of the boundary artifact.

Only the explicit `use_smoothing is False` case changes. `use_smoothing='auto'` and
an explicit integer window are untouched, and so are the two Savgol passes on `z`
itself. Other falsy values (`0`, `''`) keep their previous behaviour. A bare
`determine_periods(series)` call is unaffected — `r(t₀)` under package defaults
stays at its measured 0.526.

> **Scope of validation:** measured and validated on TRACK (Gramcianinov)
> vorticity, which already carries upstream spatial smoothing. **Not validated on
> raw ERA5 vorticity.** See `docs/future_work.md`, item 4.

> **How to reproduce earlier results:** pass an explicit window instead of `False`
> — e.g. `use_smoothing=len(series)//4 | 1` for series longer than 8 days, or
> `len(series)//2 | 1` otherwise, which is the window the old code chose. Note that
> this also re-enables the Savgol passes on `z`, which `use_smoothing=False` still
> skips; the two were never separable through this single parameter.

**Two filtering defaults moved together (behaviour change)**

| parameter | was | now |
|---|---|---|
| `boundary_padding` | `"zero"` | **`"reflect"`** |
| `replace_endpoints_with_lowpass` | `24` | **`0`** (and deprecated) |

They had to move together: with `boundary_padding="reflect"` and a non-zero
`replace_endpoints_with_lowpass`, both the bandpass and the lowpass carry full
amplitude at the edge instead of both being suppressed toward zero, so the
difference in their gains no longer cancels and the 5 % endpoint splice becomes a
visible **step**. Measured over the 51-track calibration set, the number of tracks
whose detected life cycle *opens* with a spurious `decay` phase:

| configuration | `"zero"` | `"reflect"` |
|---|---|---|
| `replace_endpoints_with_lowpass=24` | 4/51 | **28/51** |
| `replace_endpoints_with_lowpass=0` | 0/51 | **0/51** |

A cyclone track essentially never begins by weakening, so 28/51 is an artifact.
With both new defaults in place: **49/51 tracks open with `incipient`, 2/51 with
`intensification`, 0/51 with `decay`** (old defaults: 46 / 1 / 4).

**`boundary_padding` now defaults to `"reflect"`**

The option added below shipped with `"zero"` as its default so that nothing moved
while it was being validated. It is now `"reflect"` in every entry point:
`lanczos_filter`, `lanczos_bandpass_filter`, `process_vorticity`,
`determine_periods`, and the calibration app.

Rationale: `"zero"` is not a neutral choice, it is the artifact. Convolving via
`scipy.signal.convolve(..., mode="same")` zero-pads the input beyond its own ends,
and because vorticity has a non-zero floor those "missing" samples are a jump to
zero rather than a continuation of the signal. With a kernel about half the series
length, the result is a spurious *deepening* ramp worth a median **74 % of the
cyclone's own peak-to-peak amplitude**, contaminating **~48 % of every series**
(~24 % at each end) and accounting for **≥ 80 % of the slope measured at the first
sample in 51/51 tracks** of the calibration set. Leaving that switched on by
default was judged the larger cost.

Measured effect of the new default (normalised `|dz|` at the first/last sample,
median over the 51-track set, with the Lanczos filter active): **0.95/0.98 →
0.42/0.35**. Raw-signal reference: 0.29.

> **How to reproduce earlier results:** pass `boundary_padding="zero"` **and**
> `replace_endpoints_with_lowpass=24` explicitly. Together these restore the
> previous output byte-for-byte. Note that a parameter set calibrated under one
> padding mode must be re-validated under another — the smoothed signal differs in
> the boundary zone, so this is not a drop-in swap in either direction. On the
> 51-track set, 14/51 detected phase sequences differ between `"zero"` and
> `"reflect"`.

### Deprecated

**`replace_endpoints_with_lowpass`**

Kept, not removed; a non-zero value now emits a `DeprecationWarning`.

It was introduced as a palliative for exactly the artifact `boundary_padding` now
fixes at its source — and it never fixed the cause, because the lowpass estimate it
splices in is produced by `lanczos_filter`, i.e. by the *same* zero-padded
convolution. Measured on the 51-track set, it took the normalised `|dz|` at the
first sample only from a median 0.95 to 0.71, at the cost of 14 % of z's amplitude,
whereas `boundary_padding="reflect"` takes it to 0.42 at no amplitude cost.

With `boundary_padding="reflect"` it is worse than redundant, it is harmful — see
the endpoint-splice step documented under "Changed" above.

### Fixed

**`use_filter=True` silently disabled the Lanczos filter (behaviour change)**

`process_vorticity` selected the Lanczos window with
`if use_filter == 'auto': window = len(zeta)//2 else: window = use_filter`.
Because `bool` is a subclass of `int` in Python, `use_filter=True` fell into the
`else` branch and was read as the integer **1**. A 1-tap Lanczos kernel is a
single scalar multiply (0.0714 for `cutoff_low=168` / `cutoff_high=24`), not a
convolution — so a caller asking for filtering received **none**, and the output
differed from `use_filter=False` only by a constant factor that every downstream
(difference-based) criterion cancels out.

`use_filter=True` is now equivalent to `use_filter='auto'` (window
`len(series)//2`) and emits a `UserWarning` naming the resulting window.
`use_filter=False` still disables filtering; an explicit integer is still a
literal window length, and `use_filter=1` is no longer conflated with `True`
(the bool check runs before the int check).

> **Impact — read this before reusing old results.** Any series processed with
> `use_filter=True` on version 2.0.0 or earlier was effectively **unfiltered**.
> This includes the calibration app's "Apply Lanczos filter" checkbox, which
> sends a bool. Parameter sets calibrated under that setting were calibrated on
> an unfiltered signal and **must be re-validated** — the filter now actually
> runs, which changes the smoothed series, its derivatives, and the detected
> phases.

### Added

**`boundary_padding` — opt-in fix for the Lanczos zero-padding edge artifact**

`lanczos_filter` and `lanczos_bandpass_filter` convolve via
`scipy.signal.convolve(..., mode="same")`, which implicitly zero-pads the input
beyond its own ends. Vorticity has a non-zero floor (order -5e-5), so those
"missing" samples are a jump to zero rather than a neutral continuation, and two
properties of this configuration amplify the damage: the kernel is about half the
series length (measured kernel/series ratio median 0.494 over the 51-track
calibration set), and the bandpass kernel does not actually reject DC at these
window lengths (`sum(weights)` median 0.629).

The result is a step between the boundary value and the interior worth a median
**74 % of the cyclone's own peak-to-peak amplitude**, spread as a ramp over ~24 %
of the series at each end and carrying the sign of a spurious *deepening*. On the
calibration set that ramp alone accounts for **≥ 80 % of the slope measured at t0
in 51/51 tracks**.

`boundary_padding` accepts `"reflect"`, `"edge"` and `"zero"` (the latter
byte-for-byte the pre-fix behaviour). Measured on the 51 tracks with
`use_filter='auto'` (normalised `|dz|` at the first/last sample, median):
`"zero"` 0.95/0.98, `"reflect"` 0.42/0.35, `"edge"` 0.50/0.38 — against a
raw-signal reference of 0.29. It shipped with `"zero"` as the default and that
default has since been changed to `"reflect"` (see "Changed" above).

The Lanczos kernels themselves are unchanged; the correction is purely a boundary
condition, and the pad widths reproduce scipy's `"same"` alignment exactly, so no
time shift is introduced. Exposed in the calibration app (selectbox + YAML
import/export; pre-existing YAMLs fall back to the default without warning).

`replace_endpoints_with_lowpass` was introduced as a palliative for this same
artifact and itself calls `lanczos_filter`, i.e. it replaces zero-padded bandpass
endpoints with zero-padded lowpass endpoints. It is unchanged here and is a
candidate for future deprecation.

### Notes

**New validated calibration with the Lanczos filter active.** With the two changes
above in place, the author re-validated the 51-track calibration set and reached
0/51 bad cases with `use_filter=true`, `cutoff_high=18`, `boundary_padding=reflect`
and **Savitzky-Golay smoothing of `z` switched off entirely**
(`use_smoothing=false`, `use_smoothing_twice=false`). See
`docs/future_work.md` § 3c for the full parameter set, the measurements, and the
caveat that `use_smoothing=false` disables Savgol on `z` but leaves the
*derivative* smoothing running with an auto window.

---

## [2.0.0] - 2026-06-14

This release consolidates a comprehensive bug-fix and hardening pass on the core
phase-detection pipeline (`fix/core-bugs` branch), a new synthetic test suite,
an interactive calibration tool, and packaging / documentation cleanup.
No public API defaults were changed; the fixes are behavioural corrections to
previously silent or erroneous logic.

### Fixed

**Phase detection — core bugs**
- `find_intensification_period`: wrong dict key caused `threshold_intensification_gap`
  to be silently ignored (gap-merging was never applied).
- `post_process_periods`: singleton-phase detection used `type(…) == int` which
  never matched a pandas Timedelta; single-timestep phases were therefore never
  absorbed by their neighbour.
- `find_residual_period`: three related bugs corrected —
  correct last-block selection (was always selecting first block),
  working residual fill (fill loop was a no-op),
  and consistent consecutive-block detection.
- `find_residual_period`: guard against `NameError` when neither `decay` nor
  `mature` is present in `unique_phases` (early return instead of crash).
- `periods_to_dict`: suffix counter for 3+ repeated phase names was broken
  (`len()` of a 2-tuple is always 2, so the third block always overwrote
  `"name 2"`); now counts all matching existing keys for a unique suffix.
- `find_mature_stage`: `df.loc[block_start - dt]` and `df.loc[block_end + dt]`
  raised `KeyError` when a mature block touched the series boundary; explicit
  boundary check added, out-of-bounds treated as "required neighbour absent"
  → block cleared to `NaN`.
- `find_peaks_valleys`: plateau runs (consecutive equal extrema) collapsed to a
  single representative midpoint, preventing duplicate / overlapping peak-valley
  labels that caused downstream detection failures.
- `plot_all_periods`, `generate_figures.py`: spurious white gaps between adjacent
  phase bands eliminated by extending each phase's right boundary to the start of
  the following phase (root cause: `periods_to_dict` returns `end` = last timestamp,
  so `axvspan`/`fill_between` stopped one `dt` short of the next phase start).

**Pandas compatibility**
- Removed deprecated `inplace=True` patterns (`find_incipient_period`) replaced
  with direct assignment, compatible with pandas Copy-on-Write (pandas ≥ 2.0).
- `is` / `is not pd.NaT` identity comparisons replaced with `pd.isna()` throughout.

**Savgol smoothing**
- Integer `use_smoothing` / `use_smoothing_twice` values are now coerced to the
  nearest odd integer and clamped to the series length, with a `UserWarning`;
  previously they were passed through silently and could cause Savgol errors.

**Input validation**
- `process_vorticity` now raises a clear `ValueError` when the input is a
  `list` or `ndarray` and `x` (the time index) is `None`, instead of letting
  an obscure downstream error surface.

**Plotting**
- `plot_all_periods` legend moved from `bbox_to_anchor=(1.5, 1)` (far right of
  axes, causing excessive whitespace in exported PNGs) to centred below the axes.

### Changed

- `plot_all_periods` and `plot_didactic` now always return a
  `matplotlib.figure.Figure` object (previously returned `None`). Callers that
  discard the return value are unaffected.
- `plot_didactic`: `output_directory` parameter is now optional (default `None`);
  when `None`, no file is written. Previously `None` caused a crash.
- `find_stages.py` / `find_intensification_period`: stale inline comment hardcoded
  "12.5%" replaced with a generic description referencing the threshold parameter
  (actual configurable default is 7.5%).

### Added

**Tests**
- Synthetic test suite (`tests/synthetic/`) covering 12 life-cycle patterns
  (clean and noisy variants of ItMD, IcItMD, IcDItMD, DItMD, IcItMD×2, ItMD×2,
  IcIt observational, quase_ItD, IcItMD residual); tests check both phase
  sequence and approximate phase timing.
- Regression baselines (`test_baseline_default`, `test_baseline_smoothing`)
  updated to reflect corrected behaviour.
- Unit tests for `find_peaks_valleys` plateau behaviour (4 cases).
- Unit test for `determine_periods` with non-default options.

**Calibration tool** (`tools/calibration_app/` — not distributed in the wheel)
- Interactive Streamlit app for tuning filter, smoothing, and phase-detection
  parameters against one or more cyclone CSV files simultaneously.
- Multi-cyclone grid view (1–6 columns); compact twin-axis figure for dense grids.
- YAML export / import of full parameter configuration.
- Export all results as ZIP (per-cyclone `_periods.csv` + full-resolution
  `_periods.png` + `parameters.yaml`).
- In-app Documentation tab with method overview, parameter reference, and
  methodological notes (detection order, precedence, ~15–18 h detection lag).

**Documentation**
- `get_periods` docstring: phase detection pipeline order, function-call precedence
  (later functions can overwrite earlier labels), and detection-lag note
  (~15–18 h at 3-hourly resolution, most pronounced for `residual`).
- `find_peaks_valleys` docstring: boundary-index artefact documented.
- `docs/future_work.md`: 7 methodological improvement directions for
  post-2.0 releases (adaptive thresholds, `find_peaks` replacement,
  derivative smoothing, low-confidence boundary zone, and more).
- Cross-reference comments in `plots.py` and `generate_figures.py` linking
  the two copies of the gap-fix logic.

### Packaging / Documentation

- **License**: unified to `GPL-3.0-or-later` (SPDX); `setup.py` was incorrectly
  set to `MIT`. `LICENSE` file already contained the full GPLv3 text.
- **Version**: `1.9.4` → `2.0.0`.
- **Dependencies**: `pytest` moved from `install_requires` to
  `extras_require['test']` (test dependency, not runtime).
- **Project URLs**: Documentation and Issue Tracker URLs corrected to
  `cyclophaser.readthedocs.io/en/latest/` and
  `github.com/daniloceano/CycloPhaser/issues`.
- **README**: JOSS citation updated from "(under review)" to published form
  (de Souza et al., 2025, *JOSS*, 10(108), 7363,
  https://doi.org/10.21105/joss.07363); double-parenthesis markdown link bug
  fixed; unclosed code fence closed.
- `process_vorticity` docstring: removed orphaned `filter_derivatives` parameter
  entry (parameter does not exist in the function signature).

---

## [1.9.4] - 2025-01-01

*(Previous release — see git history for details.)*

[2.0.0]: https://github.com/daniloceano/CycloPhaser/compare/v1.9.4...v2.0.0
[1.9.4]: https://github.com/daniloceano/CycloPhaser/releases/tag/v1.9.4
