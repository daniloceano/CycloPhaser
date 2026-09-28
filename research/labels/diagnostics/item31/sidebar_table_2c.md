| widget key | package parameter | today (2.0.0) | declared (signature) | changes? |
|---|---|---|---|---|
| `use_filter` | `use_filter` | `True` | `True` | no |
| `cutoff_low` | `cutoff_low` | `168` | `168` | no |
| `cutoff_high` | `cutoff_high` | `48` | `18` | **yes** |
| `replace_endpoints` | `replace_endpoints_with_lowpass` | `0` | `0` | no |
| `savgol_poly` | `savgol_polynomial` | `3` | `3` | no |
| `boundary_padding` | `boundary_padding` | `'reflect'` | `'edge'` | **yes** |
| `thr_int_len` | `threshold_intensification_length` | `0.075` | `0.075` | no |
| `thr_int_gap` | `threshold_intensification_gap` | `0.075` | `0.075` | no |
| `intensification_min_depth` | `intensification_min_depth` | `0.0` | `0.05` | **yes** |
| `thr_mat_dist` | `threshold_mature_distance` | `0.125` | `0.18` | **yes** |
| `thr_mat_len` | `threshold_mature_length` | `0.03` | `0.15` | **yes** |
| `thr_dec_len` | `threshold_decay_length` | `0.075` | `0.075` | no |
| `thr_dec_gap` | `threshold_decay_gap` | `0.075` | `0.075` | no |
| `thr_inc_len` | `threshold_incipient_length` | `0.4` | `0.4` | no |
| `length_scale` | `length_scale` | `'global'` | `'local'` | **yes** |
| `mature_method` | `mature_method` | `'derivative'` | `'amplitude'` | **yes** |
| `mature_amplitude_fraction` | `mature_amplitude_fraction` | `0.9` | `0.9` | no |
| `mature_min_depth` | `mature_min_depth` | `0.0` | `0.8` | **yes** |
| `reclassify_index0` | `reclassify_index0` | `True` | `True` | no |
| `incipient_method` | `incipient_method` | `'geometric'` | `'plateau'` | **yes** |
| `incipient_plateau_tau` | `incipient_plateau_tau` | `0.2` | `0.2` | no |
| `incipient_plateau_signal` | `incipient_plateau_signal` | `'derivative'` | `'vorticity'` | **yes** |
| `incipient_plateau_crossing` | `incipient_plateau_crossing` | `'single'` | `'sustained'` | **yes** |
| `incipient_plateau_k` | `incipient_plateau_k` | `3` | `5` | **yes** |
| `incipient_smooth_window` | `incipient_smooth_window` | `0` | `5` | **yes** |
| `incipient_smooth_polyorder` | `incipient_smooth_polyorder` | `3` | `3` | no |
| `incipient_plateau_spare_intensification` | `incipient_plateau_spare_intensification` | `False` | `True` | **yes** |
| `sm_mode` | `(group)` | `'auto'` | `'off'` | **yes** |
| `sm_val` | `(group)` | `17` | `17` | no |
| `sm2_mode` | `(group)` | `'auto'` | `'off'` | **yes** |
| `sm2_val` | `(group)` | `17` | `17` | no |
| `extrema_prominence_enabled` | `(group)` | `False` | `True` | **yes** |
| `extrema_prominence_mode` | `(group)` | `'relative'` | `'relative'` | no |
| `extrema_prominence_rel_val` | `(group)` | `0.1` | `0.3` | **yes** |
| `extrema_prominence_val` | `(group)` | `1e-06` | `1e-06` | no |
| `decay_tail_enabled` | `(group)` | `False` | `True` | **yes** |
| `decay_tail_fraction_val` | `(group)` | `0.05` | `0.3` | **yes** |

App-own keys, not package parameters (unchanged): `n_cols`, `view_mode`, `inspector_track`, `inspector_ribbon`, `inspector_ledger`, `inspector_mature`, `inspector_incipient`, `inspector_normalize`
