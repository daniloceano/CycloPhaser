# FRENTE F(iii) — Predicted sweep results (written BEFORE running the sweep)

Declared per the front's rule: "Previsão declarada antes da medição, nunca
ajustada depois de ver o resultado." Nothing below is touched after the sweep
runs — deltas from actual results are recorded in the final report, not fixed
retroactively here.

Method: for each (parameter, base_config), sweep the parameter's full UI range
over the 51 calibration tracks, comparing `df_result["periods"]` (the per-step
phase label array) across every swept value. INERT = identical for all 51
tracks across the whole range. NOT INERT = at least one track shows a
different `periods` array for at least one swept value.

## Gate (a) — the 5 known cases the sweep must self-rediscover

| # | Parameter(s) | Base config | Predicted |
|---|---|---|---|
| 1 | incipient_plateau_tau, incipient_plateau_signal, incipient_plateau_crossing, incipient_plateau_k, incipient_smooth_window, incipient_smooth_polyorder | incipient_method="geometric" | INERT (all six) |
| 2 | incipient_plateau_k | incipient_method="plateau", crossing="single" | INERT |
| 3 | incipient_smooth_window, incipient_smooth_polyorder | incipient_method="plateau", signal="derivative" | INERT (both) |
| 4 | threshold_incipient_length | incipient_method="plateau" | INERT |
| 5 | threshold_mature_length, threshold_mature_distance | mature_method="amplitude" | INERT (both) |

If any of these comes back NOT INERT, the sweep itself is wrong per the
front's gate (a) — stop, do not implement anything on top of it.

## Confirmed-by-code-reading cases (not part of gate (a), expected to be
## independently rediscovered and classified POR DESENHO)

| Parameter | Base config | Predicted | Design line (already known) |
|---|---|---|---|
| cutoff_low | use_filter=False | INERT | only Lanczos convolution reads it |
| cutoff_high | use_filter=False | INERT | only Lanczos convolution reads it |
| boundary_padding | use_filter=False | INERT | only Lanczos convolution reads it |
| savgol_poly | use_smoothing=False AND use_smoothing_twice=False | INERT | only the Savgol pass(es) read it |

## Control cases (expected NOT INERT — confirms the sweep isn't just saying
## "inert" for everything, and that the historical threshold_intensification_gap
## fix — NOT re-investigated here — still behaves like a normal parameter)

| Parameter | Base config | Predicted |
|---|---|---|
| cutoff_low, cutoff_high, boundary_padding | use_filter=True (default) | NOT INERT |
| savgol_poly | use_smoothing="auto" (default) | NOT INERT |
| threshold_mature_length, threshold_mature_distance | mature_method="derivative" (default) | NOT INERT |
| threshold_incipient_length | incipient_method="geometric" (default) | NOT INERT |
| incipient_plateau_tau, signal, crossing | incipient_method="plateau" | NOT INERT |
| incipient_plateau_k | plateau, crossing="sustained" | NOT INERT |
| incipient_smooth_window, incipient_smooth_polyorder | plateau, signal="vorticity" | NOT INERT |
| threshold_intensification_length, threshold_decay_length, threshold_intensification_gap, threshold_decay_gap | default | NOT INERT |
| mature_amplitude_fraction | mature_method="amplitude" | NOT INERT |
| length_scale, mature_method, use_filter | default | NOT INERT |
| extrema_prominence_relative, extrema_distance | their own feature enabled | NOT INERT |
| decay_tail_amplitude_fraction | decay_tail_enabled=True | NOT INERT |
| replace_endpoints_with_lowpass | default (boundary_padding="reflect") | UNCERTAIN — no prior claim either way; genuinely measuring |

## Gate (c)

`determine_periods()` on the 51-track calibration set + the package's
`example_file`, all-default config, must hash byte-identical before and after
any UI change this front makes — this front only touches app.py widget
guards/captions, never cyclophaser/.
