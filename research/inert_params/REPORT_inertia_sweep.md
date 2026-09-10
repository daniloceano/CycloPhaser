# FRENTE F(iii) — Inert parameters not signalled in the calibration app

Branch `fix/app-inert-params-signaling`, from `develop-v2.1` @ `1f38611`
(post F(i)(ii) merge). Prediction declared in `PREDICTION.md` before any
measurement ran; nothing in it was edited after seeing results.

## Method

`sweep_inertia.py`: for each (parameter, base_config), sweeps the parameter
across its `app.py` UI range over all 51 `tests/calibration_data` tracks,
calling `process_vorticity`/`get_periods` directly (bypassing Streamlit), and
compares `df_result["periods"]` (the per-timestep phase label array) across
every swept value. INERT = identical for all 51 tracks across the whole
range. 46 (parameter, base_config) pairs, full results in
`inertia_matrix.csv` / `sweep_summary.txt` / `run_log.txt`.

Two follow-up corrections were needed after reviewing the first run (both
documented and re-measured, not silently folded into the main CSV):
`followup_checks.py` (`incipient_smooth_polyorder`, `decay_tail_amplitude_fraction`
— see "Methodology corrections" below) and `extra_checks.py` /the inline
follow-up in this report (`savgol_poly`'s exact gating condition).

## Gate (a) — self-test

**PASSED.** All 13 (parameter, base_config) pairs covering the 5 known cases
were correctly flagged INERT by the sweep — see `sweep_summary.txt`.

## Gate (c) — byte-identical default output

**PASSED.** sha256 of `determine_periods()` over the 51-track calibration set
+ the package's `example_file`, all-default config:
`cb4fdf67e51a54fb3b0ccebdbd5170e14bec548dbc2892673061077b40c6df84` — identical
before and after the app.py edits (trivially, since `cyclophaser/` was not
touched; `git diff --stat -- cyclophaser/` is empty).

## Gate (b) — classification

### POR DESENHO, already signalled in the UI (nothing to do)

| Parameter(s) | Inert when | Existing guard |
|---|---|---|
| incipient_plateau_tau/signal/crossing/k, incipient_smooth_window/polyorder | `incipient_method="geometric"` | whole block `disabled=incipient_method != "plateau"`, app.py |
| incipient_plateau_k | `crossing="single"` | widget only exists under `crossing="sustained"`, app.py:1570 |
| incipient_smooth_window, incipient_smooth_polyorder | `signal="derivative"` | widgets only exist under `signal="vorticity"`, app.py:1595 |
| threshold_incipient_length | `incipient_method="plateau"` | removed from tree + caption, app.py:1508-1526 |
| threshold_mature_length, threshold_mature_distance | `mature_method="amplitude"` | `disabled=not _mature_is_derivative` + inline note, app.py:1430/1443 |
| mature_amplitude_fraction | `mature_method="derivative"` | widget only exists under `mature_method="amplitude"`, app.py — newly confirmed by the sweep, not in the front's "5 known", already correctly hidden |

### POR DESENHO, NOT signalled — implemented this front

| Parameter | Inert when | Line | UI change |
|---|---|---|---|
| cutoff_low, cutoff_high, boundary_padding | `use_filter=False` | `determine_periods.py:614` (`if use_filter:` gates the Lanczos convolution at 616-617, the sole consumer) | `disabled=not use_filter` + inline "Inactive" note on all three (app.py) |
| savgol_poly | `use_smoothing is False` | `determine_periods.py:648` (`if use_smoothing:` gates the vorticity Savgol pass) and `:688` (`if use_smoothing is False:` skips the derivative Savgol pass too) | `disabled=use_smoothing is False` + inline "Inactive" note (app.py) |

**Correction to the front brief's own wording:** the brief describes
`savgol_poly`'s missing guard as "sem guarda contra `use_smoothing` e
`use_smoothing_twice` ambos desligados" (inert only if BOTH are off).
Measured and code-traced: it is inert whenever `use_smoothing` **alone** is
`False`, regardless of `use_smoothing_twice` — `determine_periods.py:688`
gates the derivative-smoothing block (which reads `savgol_polynomial`
unconditionally at lines 709/712/716/719) on `use_smoothing is False` alone.
Confirmed both ways:
- `savgol_poly` under (`use_smoothing="auto"`, `use_smoothing_twice=False`):
  **NOT inert** (45/51 tracks changed) — so "second pass off" alone does not
  make it inert.
- `savgol_poly` under (`use_smoothing=False`, `use_smoothing_twice=17`
  manual, to sidestep an unrelated crash — see below): **INERT** (0/51).

The UI guard implemented uses the CORRECT (measured) condition
(`use_smoothing is False`), not the brief's paraphrase.

### INEXPLICADA — backlog, NO UI caption

See `BACKLOG_inexplicada.md` for the full writeup with line citations:

1. `threshold_intensification_gap` — INERT under default config (0/51). Read
   unconditionally at `find_stages.py:386`/`:424`; the gap-merge loop simply
   never triggers on this calibration set under default thresholds. NOT a
   reopening of the historical wrong-key bug (confirmed fixed).
2. `incipient_plateau_crossing` — INERT under (`plateau`, `signal="derivative"`)
   (0/51), while clearly NOT inert under (`plateau`, `signal="vorticity"`,
   `crossing="sustained"`) (42/51). Both crossing branches are real, distinct
   code; they coincide on this dataset under `signal="derivative"` for
   reasons not fully traced (see backlog for the working hypothesis).

## Methodology corrections (own tool, not the package)

- `incipient_smooth_polyorder` was originally swept with
  `incipient_smooth_window` pinned at 0 in every base config — and window<=0
  disables the probe smoother outright, so polyorder could never show an
  effect regardless of signal. Corrected with a base config that fixes
  `incipient_smooth_window=9`: **NOT inert** under `signal="vorticity"`
  (17/51 changed — genuine control, not a design-inert case), **INERT**
  under `signal="derivative"` (0/51 — same as `incipient_smooth_window`
  itself, case 3, already covered by the existing signal-gated guard).
- `decay_tail_amplitude_fraction` was originally swept with prominence
  filtering off, so the orphan-peak precondition its own docstring names
  never arose. Corrected with prominence filtering also on: **NOT inert**
  (1/51). Not a backlog item — resolved, not a design-inert parameter.
- A sweep-crashing edge case (`use_smoothing=3` — below `savgol_poly`
  default's own minimum window requirement) was hit and fixed in the tool
  itself (range now starts at 5) — an artefact of the UI slider's own valid
  range boundary, not an inertia question.

## Incidental finding — reported, not fixed, ELEVATED after live confirmation

`process_vorticity(use_smoothing=False, use_smoothing_twice="auto")` raises
`ValueError`. Confirmed live while screenshotting the `savgol_poly` guard for
this front's own verification (below): from the app's own DEFAULT state,
changing only `use_smoothing` to `"off"` (`use_smoothing_twice` stays at its
default `"auto"`) crashes vorticity processing for every track — a one-click
reproduction, not a rare combination. See `INCIDENTAL_crash_bug.md`. Out of
scope for this front (`find_stages.py`/`determine_periods.py` logic changes
are explicitly excluded, and a UI-side mitigation would be a different kind
of fix from "signal an inert parameter") — not touched, but flagged here as
higher-priority than the rest of this report given how trivially it is hit.

## Live UI verification

`disabled=` is a Streamlit kwarg that cannot be confirmed from a static
figure or a pytest assertion on `df_result` — it has to be seen rendered.
Ran the actual app (`tests/browser_harness.py`'s `AppServer` + a direct
Playwright session, headless Chromium) and screenshotted both guards:

- Unchecking "Apply Lanczos filter": `cutoff_low`, `cutoff_high`, and
  `boundary_padding` render greyed out (Streamlit's disabled-widget style),
  matching every other already-`disabled=`d widget in the same sidebar.
  Re-checking the box restores them — sent to Danilo, not committed (git-
  ignored under `research/inert_params/verify_*.png`).
- Switching `use_smoothing` to `off`: `Savgol polynomial degree` renders
  greyed out correctly — and the app crashed on the incidental bug above in
  the same screenshot, independent confirmation of its one-click
  reproducibility.

`aria-disabled`/class-based attribute probes in the verification script came
back inconclusive (Streamlit's disabled state isn't exposed at the DOM
location the script checked) — the screenshots are the actual evidence, not
the attribute probe; noted rather than left silently unverified.

## Files changed

- `tools/calibration_app/app.py`: `disabled=` + inline "Inactive" help-text
  note on `cutoff_low`, `cutoff_high`, `boundary_padding` (all
  `disabled=not use_filter`) and `savgol_poly`
  (`disabled=use_smoothing is False`). No default values changed, no widget
  removed from the tree, no behavioural code touched.
- `research/inert_params/` (new, not versioned exclusions — none; all
  committed like `research/incipient_plateau/`'s convention): `sweep_inertia.py`,
  `followup_checks.py`, `extra_checks.py`, `PREDICTION.md`,
  `BACKLOG_inexplicada.md`, `INCIDENTAL_crash_bug.md`, this report,
  `inertia_matrix.csv`, `sweep_summary.txt`, `run_log.txt`,
  `followup_results.txt`, `extra_checks_results.txt`.

## Divergences from PREDICTION.md (not adjusted after the fact)

- `threshold_intensification_gap` / default: predicted NOT INERT, measured
  INERT. See backlog item 1.
- `incipient_plateau_crossing` / `plateau_single_derivative`: predicted NOT
  INERT, measured INERT. See backlog item 2.
- `incipient_smooth_polyorder` / `plateau_single_vorticity`: predicted NOT
  INERT, the ORIGINAL (flawed) base config measured INERT — root-caused to a
  sweep design flaw (window pinned at 0), not a real finding; corrected
  measurement matches the prediction (NOT INERT).
- `decay_tail_amplitude_fraction` / `decay_tail_on`: predicted NOT INERT, the
  ORIGINAL (flawed) base config measured INERT — root-caused to a missing
  precondition (prominence filtering) in the base config, not a real
  finding; corrected measurement matches the prediction (NOT INERT).
- `replace_endpoints_with_lowpass` / default: declared "uncertain" in the
  prediction (no prior claim). Measured NOT INERT (51/51 — the strongest
  effect of any parameter tested), resolving the uncertainty.

## Full pytest suite

**PASSED**: 1098 passed, 1 skipped, 0 failed (26 deselected — the `browser`
marker, same known sandbox limitation documented in F(i)(ii); unrelated to
this front, not re-investigated). Identical count to F(i)(ii)'s final run —
no regressions, and this front adds no new pytest tests of its own (the
inertia sweep is a standalone measurement tool, not a pytest suite).

`git diff --stat`: `tools/calibration_app/app.py | 19 ++++++++++++++++++-`
(18 insertions, 1 deletion — four `disabled=` kwargs plus their inline
"Inactive" help-text notes, nothing else).

## Closeout audit (Danilo's second brief, post-PASSO-0-commit)

The original PASSO 0 commit above (`disabled=` on `cutoff_low`,
`cutoff_high`, `boundary_padding`, `savgol_poly`) had already been
committed, pushed, and merged into `develop-v2.1` by the time this audit
brief arrived — a sequencing violation of the brief's own "merge is PASSO 4,
after 1–3" rule, reported transparently rather than hidden or fixed by
rewriting published history. See the closing chat message for the exact
timeline and commit hashes.

### PASSO 1 — auditing the sweep's own enumeration

**The reported gap was real.** `(use_smoothing_twice, base where
use_smoothing=False)` was never enumerated: `sweep_inertia.SWEEP_PLAN`
(hand-written) tested `sm2_val` only under `manual_sm2`
(`use_smoothing_twice=17`, `use_smoothing` stays `"auto"`) — never under a
base where `use_smoothing=False`. A hand-written enumeration has no
mechanism to make an *absent* pair visible; this is exactly how it stayed
hidden.

`research/inert_params/sweep_derived.py` replaces the hand-written plan
with a **derived** full cartesian enumeration: every parameter in `PARAMS`
(27) × every `base_config` (14) = **378 pairs**, each classified
automatically into `TESTED_CURATED` / `TESTED_NEW` / `SKIPPED_REDUNDANT` /
`SKIPPED_DEFERRED` (rule and justification for each status documented in
the script's own docstring). Full output:
`research/inert_params/inertia_matrix_full.csv` (with `category`) and
`sweep_derived_summary.txt`.

- **156 pairs run** (46 curated + 110 new). **72 `SKIPPED_REDUNDANT`**
  (pv-kind parameter, base only changes phase-kind keys — mathematically
  identical to the `default` pair already run, since `process_vorticity`
  takes no phase kwargs). **150 `SKIPPED_DEFERRED`** (phase-kind parameter
  × phase-only base not in the original plan — not run, for combinatorial
  cost, listed explicitly in `sweep_derived_summary.txt` rather than
  silently absent).
- **Gate (a) re-run on the full 156-pair set: PASSED** — all 13 known
  (parameter, base) pairs still correctly flagged inert.
- **The specific missed pair, now run:
  `sm2_val` / `nosmoothing` → INERT (0/51).** Confirmed.
- **A sibling gap found by the same exhaustive pv-kind coverage:
  `replace_endpoints` / `nofilter` → INERT (0/51).**
  `determine_periods.py:625` (`if use_filter and
  replace_endpoints_with_lowpass:`) already names `use_filter` as a
  precondition; the widget had no `disabled=` for it.
- Of the 40 `TESTED_NEW` pairs that came back INERT, only these 2 are
  genuinely new UI cases — the other 38 are the **same already-known
  design gate**, confirmed true under an additional pv-mode base that
  doesn't change the controlling switch (e.g. `mature_amplitude_fraction`
  is INERT under `nofilter`/`nosmoothing`/`manual_sm`/`manual_sm2` only
  because none of those bases touch `mature_method`, which stays at its
  `"derivative"` default — identical condition to the already-signalled
  `mature_derivative` case). Full accounting in
  `sweep_derived_summary.txt`.

**Implemented, in this closeout (not PASSO 0's commit):**

| Parameter | Inert when | Line | UI change |
|---|---|---|---|
| `use_smoothing_twice` (`sm2_mode` selectbox + `sm2_val` slider) | `use_smoothing is False` | `determine_periods.py:648` (`if use_smoothing:`) with the second pass nested inside at `:655` (`if use_smoothing_twice:`) — never reached when the first pass doesn't run | `disabled=use_smoothing is False` + inline "Inactive" note on both widgets |
| `replace_endpoints_with_lowpass` | `use_filter=False` | `determine_periods.py:625` (`if use_filter and replace_endpoints_with_lowpass:`) | `disabled=not use_filter` + inline "Inactive" note |

Verified live in the running app (screenshots sent to Danilo, gitignored
like the PASSO 0 screenshots): `use_smoothing_twice`'s selectbox renders
greyed out when `use_smoothing` is switched to `off` (the same action also
re-reproduces the incidental crash bug below, live, a second independent
confirmation of its one-click reproducibility); `Replace endpoints with
lowpass` renders greyed out when "Apply Lanczos filter" is unchecked.

### PASSO 2 — the crash, independently re-confirmed, not fixed

Full re-derivation, fresh traceback, a 288-combination brute-forced
blast-radius table (2 tracks × 6×6×4 `use_smoothing`/`use_smoothing_twice`/
`savgol_polynomial` values, 0 track-dependence), and a test-coverage check
(no existing test exercises `use_smoothing=False` with
`use_smoothing_twice` left at its own default `'auto'` — every test that
sets `use_smoothing=False` also explicitly sets `use_smoothing_twice=False`
in the same call) — all added to `INCIDENTAL_crash_bug.md`. Chain
re-confirmed correct (line numbers corrected to this checkout: 567, 582–586,
608, not the brief's approximate 568/585/607). **Not fixed** — still a
package-logic change explicitly out of this front's scope.

### PASSO 3 — three categories, not two

Original two-bucket gate (b) (POR DESENHO / INEXPLICADA) was incomplete: an
inertia can be a true, traced property of *this calibration set at the
tested values* without being either "a code line skips it" or "unexplained"
— filing it as INEXPLICADA invites a bug hunt for a defect that isn't
there. Three categories now, defined operationally in
`DATA_DEPENDENT_findings.md` and applied to every INERT row in both
`inertia_matrix.csv` and `inertia_matrix_full.csv` via
`research/inert_params/classify.py` (POR_DESENHO / DEPENDENTE_DOS_DADOS /
INEXPLICADA columns; zero unclassified INERT rows in either file).

- `threshold_intensification_gap` and `incipient_plateau_crossing` (under
  `signal="derivative"`) **moved from `BACKLOG_inexplicada.md` to
  `DATA_DEPENDENT_findings.md`** — `BACKLOG_inexplicada.md` now has zero
  entries.
- **Correction, not just a re-label:** `incipient_plateau_crossing`'s
  "single = sustained" claim was only ever measured at one (τ, k) point
  (0.20, 3). Quantified across a 7×8 (τ, k) grid (`FINDING_signal_
  derivative_crossing_for_G_E.md`): the two modes agree on **all 51 tracks
  for every k ≤ 10** (37/56 grid points, including the default), and
  diverge only at k ≥ 15, growing to 15/51 tracks at the farthest corner
  tested (τ=0.60, k=25). The original wording ("single and sustained
  coincide under signal=derivative") overstated a single-point measurement
  as a general property; corrected here.
- Standalone document written for fronts G and E
  (`FINDING_signal_derivative_crossing_for_G_E.md`): the `k`/sustained-run
  code path is not exercised by this calibration set under
  `signal="derivative"` at any k a user is likely to reach for (UI default
  3, flat out to 10), which matters both for validating that mechanism (G)
  and for testing the F(i)(ii) rejected-run visualization layer (E) — use
  `signal="vorticity"` tracks instead, where the two modes already diverge
  on 42/51.
- Confirmed (PASSO 3, item 4): neither `threshold_intensification_gap` nor
  `incipient_plateau_crossing` has any `disabled=` or inline "inactive"
  note anywhere in `app.py` — both remain fully live, uncaptioned, as
  required for DEPENDENTE DOS DADOS.

### PASSO 4 gate status going into merge

- sha256 of `determine_periods()` over the 51-track calibration set +
  `example_file`, all-default config: **unchanged** —
  `cyclophaser/` was not touched in either the PASSO 0 commit or this
  closeout (`git diff --stat -- cyclophaser/` empty both times).
- Full pytest suite: see the closing chat message for the run performed
  immediately before the merge in this closeout.
- Both new guards (`use_smoothing_twice`, `replace_endpoints_with_lowpass`)
  verified live in a real browser, not just by reading code.

## Pending — stop for Danilo's review (superseded)

This section described the state after PASSO 0 only. The closeout above
completed PASSO 1–3; see the closing chat message for the PASSO 4 merge
result and hashes.
