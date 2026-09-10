# Incidental finding — NOT part of FRENTE F(iii), NOT fixed here

**Elevated after live confirmation: this is a ONE-CLICK crash from the app's
own default state**, not a rare combination. Found while precisely pinning
down `savgol_poly`'s gating condition, then reproduced live in the running
app while taking the screenshot for this front's own verification (see
`verify_smoothing_off.png`): with every other widget still at its default,
changing ONLY `use_smoothing` from `"auto"` to `"off"` (`use_smoothing_twice`
stays at its default `"auto"`) crashes vorticity processing for every loaded
track, with the app surfacing "Vorticity processing failed: Second Savgol
window length (use_smoothing_twice) must be ≥ savgol_polynomial." in place of
every figure. Out of scope for this front ("Qualquer mudança em
find_stages.py, determine_periods.py ou lógica de detecção" is explicitly
excluded) — reported so it isn't lost, not touched, and not mitigated at the
UI level either (that would be a crash-prevention fix, a different kind of
change from "signal an inert parameter").

## Reproduction

Python:
```python
from cyclophaser.determine_periods import process_vorticity
process_vorticity(zeta_df, use_smoothing=False, use_smoothing_twice="auto")
# ValueError: Second Savgol window length (use_smoothing_twice) must be >= savgol_polynomial.
```

App: open the calibration app, in "Savgol Smoothing" change `use_smoothing`
from `auto` to `off` and leave everything else untouched. `use_smoothing_twice`
mode and `use_smoothing` mode are two independent selectboxes (`sm_mode`,
`sm2_mode`), and `sm2_mode` defaults to `"auto"` — so this is a single
dropdown change away from the app's own defaults.

## Cause (`cyclophaser/determine_periods.py`)

When `use_smoothing=False`, line 566's `else` branch sets
`window_length_savgol = use_smoothing`, i.e. the Python **bool** `False`
(the `'auto'` branch at line 561 is skipped since `False != 'auto'`). When
`use_smoothing_twice == 'auto'` (line 582), `window_length_savgol_2nd` is
then derived from that bool: `window_length_savgol * 2 | 1` or
`window_length_savgol | 1` — and `False` behaves as `0` in both, so
`window_length_savgol_2nd` comes out as `1` regardless of series length. The
guard at line 607 (`if use_smoothing_twice and window_length_savgol_2nd <
savgol_polynomial:`) then raises for any `savgol_polynomial >= 2` — i.e.
always, since the UI's own minimum is 2.

Every OTHER combination sidesteps this: `use_smoothing_twice` as an explicit
manual int does not go through the `'auto'` derivation, so it computes a
real window and does not crash (confirmed:
`use_smoothing=False, use_smoothing_twice=17` runs fine).

## Independent re-confirmation (FRENTE F(iii) closeout, PASSO 2)

Re-derived from a fresh traceback, not copied from the orchestration brief
(whose own line numbers — 568/585/607 — were approximate; the actual lines
on this checkout are 567/582–586/608):

```
Traceback (most recent call last):
  File "<string>", line 7, in <module>
    process_vorticity(zeta_df, use_smoothing=False, use_smoothing_twice='auto')
  File ".../cyclophaser/determine_periods.py", line 608, in process_vorticity
    raise ValueError("Second Savgol window length (use_smoothing_twice) must be >= savgol_polynomial.")
ValueError: Second Savgol window length (use_smoothing_twice) must be >= savgol_polynomial.
```

Chain, confirmed line-by-line on this checkout:
- `determine_periods.py:567` — `use_smoothing=False` takes the `else` branch
  (not `'auto'`); `window_length_savgol = use_smoothing` is the Python
  **bool** `False`. Line 568's `isinstance(use_smoothing, int) and not
  isinstance(use_smoothing, bool)` guard is specifically there to skip int
  coercion for bools — but it does nothing to stop `False` reaching the
  arithmetic below, since `bool` still behaves as `int` in `*`/`|`.
- `determine_periods.py:582-586` — `use_smoothing_twice == 'auto'` derives
  `window_length_savgol_2nd` from `window_length_savgol`: `False * 2 | 1` or
  `False | 1`, both `== 1` (Python evaluates `False` as `0` in arithmetic).
- `determine_periods.py:608` — `if use_smoothing_twice and
  window_length_savgol_2nd < savgol_polynomial:` — `'auto'` is truthy,
  `1 < savgol_polynomial` is `True` for every value the UI's own slider
  allows (`savgol_poly` ∈ [2, 5]) — always raises.

### Blast-radius table (measured, not just reasoned about)

Brute-forced `process_vorticity(use_smoothing=sm, use_smoothing_twice=sm2,
savgol_polynomial=poly)` over `sm, sm2 ∈ {False, "auto", 3, 5, 17, 61}` (the
full shape of UI-reachable values: off / auto / manual-int) × `poly ∈ {2, 3,
4, 5}` (the UI's own range), on the shortest (1d05h, `<8D` branch) and
longest (10d18h, `>8D` branch) calibration tracks — **288 combinations
total, identical verdict on both tracks (0 track-dependence)**.

88/288 raised, but the crash message and root cause split into two
unrelated groups:

1. **This bug** (the `False`→`0` coercion) — raises *regardless of any
   inconsistency the user introduced*, purely because `use_smoothing=False`
   degrades the derivation instead of being excluded from it:
   - `use_smoothing=False, use_smoothing_twice="auto"`, **any**
     `savgol_polynomial` (2, 3, 4, or 5) — **4/4 combinations raise**. This
     is exactly the app's own defaults for `sm2_mode` — a **one-click**
     crash, confirmed live in the running app (see below), not a rare or
     contrived combination.
2. **Ordinary window-too-small-for-polyorder validation** — legitimate,
   symmetric checks that would fire for any reasonable library when a user
   picks an explicit window smaller than the polynomial degree (e.g.
   `use_smoothing=3, savgol_polynomial=5`; `use_smoothing=False,
   use_smoothing_twice=3, savgol_polynomial=5`, where `use_smoothing_twice`
   is a **manual** int and bypasses the `'auto'` derivation entirely — the
   window is the user's own literal choice, not a coerced `False`). These
   are the other 84/288 raises and are **not** this bug.

No `use_smoothing_twice=False` combination raises at line 608, for any
`use_smoothing`/`savgol_polynomial` — the guard's own `if use_smoothing_twice
and ...` short-circuits on the falsy value before the window comparison.

### Existing test coverage

`grep -rn "use_smoothing" tests/*.py` — every existing test that sets
`use_smoothing=False` (`test_use_smoothing_false_derivatives.py`,
`test_layer_inspector.py`, `test_regression_baseline.py`,
`test_decay_tail_amplitude_fraction.py`, `test_boundary_padding.py`,
`tests/synthetic/cases.py`) **also explicitly sets
`use_smoothing_twice=False`** in the same call — none exercises
`use_smoothing_twice`'s own default. `process_vorticity`'s signature default
for `use_smoothing_twice` (`determine_periods.py:344`) is itself `'auto'` —
so **any library caller** who passes `use_smoothing=False` alone, relying on
the function's own default for the second pass, hits this exact crash; it is
not an app-UI-specific footgun. **No test covers this combination at all.**

Still not fixed here — out of scope for this front by the same reasoning as
above (package logic change, sha256 gate, needs its own behavior-declared
front). This section only strengthens the existing report with independent
verification, a full blast-radius table, and the test-coverage gap; it
changes no conclusion.
