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
