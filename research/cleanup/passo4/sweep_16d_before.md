# sweep_16d_before — default/opt-in sentences in cyclophaser/ (working tree)

199 lines; by file {'cyclophaser/determine_periods.py': 140, 'cyclophaser/find_stages.py': 49, 'cyclophaser/lanczos_filter.py': 10}

| file:line | kind | function | text |
|---|---|---|---|
| `cyclophaser/determine_periods.py:139` | docstring | `find_peaks_valleys` | NOTE (#14 — pending fix): argrelextrema uses mode='clip' by default, which |
| `cyclophaser/determine_periods.py:172` | docstring | `find_peaks_valleys` | Default None disables absolute filtering (no-op). |
| `cyclophaser/determine_periods.py:176` | docstring | `find_peaks_valleys` | below 10 % of the most prominent one.  Default None |
| `cyclophaser/determine_periods.py:179` | docstring | `find_peaks_valleys` | see ``_reclassify_index0``. **Default False here, |
| `cyclophaser/determine_periods.py:181` | docstring | `find_peaks_valleys` | default it to True.** The asymmetry is deliberate: |
| `cyclophaser/determine_periods.py:427` | docstring | `process_vorticity` | Defaults (item 31, then C1 — a change of default behaviour relative to 2.0.0) |
| `cyclophaser/determine_periods.py:429` | docstring | `process_vorticity` | The defaults are the calibration preset ``params-track`` |
| `cyclophaser/determine_periods.py:431` | docstring | `process_vorticity` | ``boundary_padding`` defaults to ``"reflect"``, while params-track sets |
| `cyclophaser/determine_periods.py:434` | docstring | `process_vorticity` | params-track, not these defaults. Callers working with TRACK input who want |
| `cyclophaser/determine_periods.py:435` | docstring | `process_vorticity` | the measured behaviour must pass params-track explicitly. The defaults fall |
| `cyclophaser/determine_periods.py:438` | docstring | `process_vorticity` | * **Phase defaults** (``get_periods``: thresholds, ``length_scale``, |
| `cyclophaser/determine_periods.py:442` | docstring | `process_vorticity` | * **Filtering defaults** (``process_vorticity``: ``cutoff_high=18.0``, |
| `cyclophaser/determine_periods.py:447` | docstring | `process_vorticity` | South-Atlantic cyclone tracks. The default ``boundary_padding="reflect"`` |
| `cyclophaser/determine_periods.py:455` | docstring | `process_vorticity` | The defaults before item 31 are frozen in research/labels/defaults_2.0.0.json; |
| `cyclophaser/determine_periods.py:466` | docstring | `process_vorticity` | (or `True`, which is equivalent — see the "use_filter=True note" below) for the default window |
| `cyclophaser/determine_periods.py:468` | docstring | `process_vorticity` | window length explicitly in time steps. **Units**: Time steps. Default is `'auto'`. |
| `cyclophaser/determine_periods.py:472` | docstring | `process_vorticity` | Default is 0 (disabled) — it was 24 in versions up to and including 2.0.0. Passing a non-zero |
| `cyclophaser/determine_periods.py:477` | docstring | `process_vorticity` | default window length or specify an integer value as the desired window length. Must be greater than or equal |
| `cyclophaser/determine_periods.py:478` | docstring | `process_vorticity` | to `savgol_polynomial`. **Units**: Time steps. Default is `False` (`'auto'` up to 2.0.0). **To deactivate**, set `use_smoothing` |
| `cyclophaser/determine_periods.py:483` | docstring | `process_vorticity` | Same requirements as `use_smoothing`. Default is `False` (`'auto'` up to 2.0.0). |
| `cyclophaser/determine_periods.py:486` | docstring | `process_vorticity` | window length (`use_smoothing` or `use_smoothing_twice` if specified). Default is 3. |
| `cyclophaser/determine_periods.py:489` | docstring | `process_vorticity` | noise. Suitable for time series data with hourly resolution. **Units**: Time steps. Default is 168. |
| `cyclophaser/determine_periods.py:492` | docstring | `process_vorticity` | Suitable for time series data with hourly resolution. **Units**: Time steps. Default is 18.0 (48.0 up to 2.0.0). |
| `cyclophaser/determine_periods.py:495` | docstring | `process_vorticity` | ends before the Lanczos convolution. ``"reflect"`` (the default) and ``"edge"`` |
| `cyclophaser/determine_periods.py:499` | docstring | `process_vorticity` | meaningful when ``use_filter`` is truthy. Default is ``"reflect"`` |
| `cyclophaser/determine_periods.py:559` | docstring | `process_vorticity` | ``"reflect"`` became the DEFAULT here (behaviour change): leaving a |
| `cyclophaser/determine_periods.py:560` | docstring | `process_vorticity` | quantified artefact switched on by default was judged the larger cost. |
| `cyclophaser/determine_periods.py:561` | docstring | `process_vorticity` | Item 31 moved the default to ``"edge"``, the padding of the calibration |
| `cyclophaser/determine_periods.py:566` | docstring | `process_vorticity` | results from a version before the default changed, pass |
| `cyclophaser/determine_periods.py:578` | docstring | `process_vorticity` | ``replace_endpoints_with_lowpass`` is **DEPRECATED** and its default changed |
| `cyclophaser/determine_periods.py:579` | docstring | `process_vorticity` | from 24 to **0** together with the ``boundary_padding`` default above. Passing |
| `cyclophaser/determine_periods.py:595` | docstring | `process_vorticity` | visible STEP. Measured over the 51 tracks with the package defaults, the |
| `cyclophaser/determine_periods.py:602` | docstring | `process_vorticity` | defaults with replace_endpoints_with_lowpass=24   4/51      28/51 |
| `cyclophaser/determine_periods.py:603` | docstring | `process_vorticity` | defaults with replace_endpoints_with_lowpass=0    0/51       0/51 |
| `cyclophaser/determine_periods.py:607` | docstring | `process_vorticity` | artefact, not a finding. Hence the two defaults had to move together: a |
| `cyclophaser/determine_periods.py:741` | comment | `process_vorticity` | # differentiate('time'). Item 31 made use_smoothing=False the default, |
| `cyclophaser/determine_periods.py:810` | comment | `process_vorticity` | # test: other falsy values (0, '') keep their previous behaviour, which the |
| `cyclophaser/determine_periods.py:885` | docstring | `get_periods` | Defaults (item 31, then C1 — a change of default behaviour relative to 2.0.0) |
| `cyclophaser/determine_periods.py:887` | docstring | `get_periods` | The defaults are the calibration preset ``params-track`` |
| `cyclophaser/determine_periods.py:889` | docstring | `get_periods` | ``boundary_padding`` defaults to ``"reflect"``, while params-track sets |
| `cyclophaser/determine_periods.py:892` | docstring | `get_periods` | params-track, not these defaults. Callers working with TRACK input who want |
| `cyclophaser/determine_periods.py:893` | docstring | `get_periods` | the measured behaviour must pass params-track explicitly. The defaults fall |
| `cyclophaser/determine_periods.py:896` | docstring | `get_periods` | * **Phase defaults** (``get_periods``: thresholds, ``length_scale``, |
| `cyclophaser/determine_periods.py:900` | docstring | `get_periods` | * **Filtering defaults** (``process_vorticity``: ``cutoff_high=18.0``, |
| `cyclophaser/determine_periods.py:905` | docstring | `get_periods` | South-Atlantic cyclone tracks. The default ``boundary_padding="reflect"`` |
| `cyclophaser/determine_periods.py:913` | docstring | `get_periods` | The defaults before item 31 are frozen in research/labels/defaults_2.0.0.json; |
| `cyclophaser/determine_periods.py:948` | docstring | `get_periods` | (default 0.3; ``None`` switches the check off and leaves the tail to the |
| `cyclophaser/determine_periods.py:975` | docstring | `get_periods` | ``threshold_decay_gap`` are all fractions of a *length*.  With the default |
| `cyclophaser/determine_periods.py:992` | docstring | `get_periods` | With ``mature_method="derivative"`` (the default before item 31; not a parameter of the 2.0.0 release) the mature window around |
| `cyclophaser/determine_periods.py:1048` | docstring | `get_periods` | plot (Union[str, bool], optional): Path to save plots or False to disable plotting. Default is False. |
| `cyclophaser/determine_periods.py:1049` | docstring | `get_periods` | plot_steps (Union[str, bool], optional): Path to save step-by-step plots or False to disable. Default is False. |
| `cyclophaser/determine_periods.py:1050` | docstring | `get_periods` | export_dict (Union[str, bool], optional): Path to export periods to CSV or False to disable. Default is False. |
| `cyclophaser/determine_periods.py:1051` | docstring | `get_periods` | threshold_intensification_length (float, optional): Minimum intensification length. Default is 0.075. |
| `cyclophaser/determine_periods.py:1052` | docstring | `get_periods` | threshold_intensification_gap (float, optional): Maximum gap in intensification periods. Default is 0.075. |
| `cyclophaser/determine_periods.py:1053` | docstring | `get_periods` | threshold_mature_distance (float, optional): Distance threshold for mature stage detection. Default is 0.18 (0.125 up to 2.0.0). |
| `cyclophaser/determine_periods.py:1054` | docstring | `get_periods` | threshold_mature_length (float, optional): Minimum mature stage length. Default is 0.15 (0.03 up to 2.0.0). |
| `cyclophaser/determine_periods.py:1055` | docstring | `get_periods` | threshold_decay_length (float, optional): Minimum decay stage length. Default is 0.075. |
| `cyclophaser/determine_periods.py:1056` | docstring | `get_periods` | threshold_decay_gap (float, optional): Maximum gap in decay periods. Default is 0.075. |
| `cyclophaser/determine_periods.py:1057` | docstring | `get_periods` | threshold_incipient_length (float, optional): Minimum incipient length. Default is 0.4. |
| `cyclophaser/determine_periods.py:1059` | docstring | `get_periods` | ``"geometric"`` (the default before item 31; not a parameter of the 2.0.0 release) is the historical rule: the incipient phase runs |
| `cyclophaser/determine_periods.py:1062` | docstring | `get_periods` | case A/B/C dispatch. ``"plateau"`` (the default since item 31) instead marks the leading stretch over |
| `cyclophaser/determine_periods.py:1068` | docstring | `get_periods` | artifact at t0 has been controlled. Under the 2.0.0 package defaults the first |
| `cyclophaser/determine_periods.py:1072` | docstring | `get_periods` | ``boundary_padding="reflect"`` and ``use_smoothing=False``) — as the current defaults are. Default is ``"plateau"``. |
| `cyclophaser/determine_periods.py:1076` | docstring | `get_periods` | Only used when ``incipient_method="plateau"``. Default is 0.20. |
| `cyclophaser/determine_periods.py:1079` | docstring | `get_periods` | on. ``"derivative"`` (the default before item 31; not a parameter of the 2.0.0 release) uses ``\|dz_dt_smoothed2\|`` normalised by its |
| `cyclophaser/determine_periods.py:1081` | docstring | `get_periods` | ``"vorticity"`` (the default since item 31) uses ``\|d(zeta)/dt\|`` computed with ``np.gradient`` on the |
| `cyclophaser/determine_periods.py:1086` | docstring | `get_periods` | detected. ``"single"`` (the default before item 31; not a parameter of the 2.0.0 release) ends it at the first sample with |
| `cyclophaser/determine_periods.py:1087` | docstring | `get_periods` | ``rel >= tau``. ``"sustained"`` (the default since item 31) requires ``incipient_plateau_k`` |
| `cyclophaser/determine_periods.py:1094` | docstring | `get_periods` | ``incipient_plateau_crossing="sustained"``. Default is 5 (3 before item 31; not a parameter of the 2.0.0 release). Ignored for |
| `cyclophaser/determine_periods.py:1100` | docstring | `get_periods` | therefore every other phase, are untouched. 0 disables it (the default before item 31; not a parameter of the 2.0.0 release). Default is 5. Only used when |
| `cyclophaser/determine_periods.py:1108` | docstring | `get_periods` | Savitzky-Golay pass. Default is 3. A window at or below this order cannot |
| `cyclophaser/determine_periods.py:1116` | docstring | `get_periods` | writes no incipient at all). Otherwise nothing changes. Default True since item 31 — **adotada sem validação independente** (item 30); False reproduces the behaviour before item 31 (not a parameter of the 2.0.0 release). Only used when |
| `cyclophaser/determine_periods.py:1119` | docstring | `get_periods` | z-extrema filtering. Default None (no-op). See ``find_peaks_valleys`` |
| `cyclophaser/determine_periods.py:1126` | docstring | `get_periods` | prominence. Default 0.3 since item 31 (None, a no-op, before item 31; not a parameter of the 2.0.0 release). |
| `cyclophaser/determine_periods.py:1141` | docstring | `get_periods` | ``prominence_relative`` both None — the defaults before item 31; neither is a parameter of the 2.0.0 release — the rule |
| `cyclophaser/determine_periods.py:1147` | docstring | `get_periods` | **Default True — this is a change of default behaviour.** Index 0 is |
| `cyclophaser/determine_periods.py:1158` | docstring | `get_periods` | length_scale (str, optional): "local" (default since item 31) or "global" (the default before item 31; not a parameter of the 2.0.0 release). See the |
| `cyclophaser/determine_periods.py:1160` | docstring | `get_periods` | mature_method (str, optional): "amplitude" (default since item 31) or "derivative" (the default before item 31; not a parameter of the 2.0.0 release). |
| `cyclophaser/determine_periods.py:1164` | docstring | `get_periods` | (opt-in) instead defines the mature window as the contiguous |
| `cyclophaser/determine_periods.py:1176` | docstring | `get_periods` | Default 0.90. |
| `cyclophaser/determine_periods.py:1191` | docstring | `get_periods` | ``find_stages.find_mature_stage``. Default 0.8 since item 31; 0.0 (the default before item 31; not a parameter of the 2.0.0 release) admits every valley and |
| `cyclophaser/determine_periods.py:1225` | docstring | `get_periods` | ``find_stages.find_intensification_period``. Default 0.05 since item 31; 0.0 (the default before item 31; not a parameter of the 2.0.0 release) switches the |
| `cyclophaser/determine_periods.py:1231` | docstring | `get_periods` | mechanism. Default 0.3 since item 31; None (the default before item 31; not a parameter of the 2.0.0 release) disables this check, reproducing the exact |
| `cyclophaser/determine_periods.py:1425` | docstring | `determine_periods` | Defaults (item 31, then C1 — a change of default behaviour relative to 2.0.0) |
| `cyclophaser/determine_periods.py:1427` | docstring | `determine_periods` | The defaults are the calibration preset ``params-track`` |
| `cyclophaser/determine_periods.py:1429` | docstring | `determine_periods` | ``boundary_padding`` defaults to ``"reflect"``, while params-track sets |
| `cyclophaser/determine_periods.py:1432` | docstring | `determine_periods` | params-track, not these defaults. Callers working with TRACK input who want |
| `cyclophaser/determine_periods.py:1433` | docstring | `determine_periods` | the measured behaviour must pass params-track explicitly. The defaults fall |
| `cyclophaser/determine_periods.py:1436` | docstring | `determine_periods` | * **Phase defaults** (``get_periods``: thresholds, ``length_scale``, |
| `cyclophaser/determine_periods.py:1440` | docstring | `determine_periods` | * **Filtering defaults** (``process_vorticity``: ``cutoff_high=18.0``, |
| `cyclophaser/determine_periods.py:1445` | docstring | `determine_periods` | South-Atlantic cyclone tracks. The default ``boundary_padding="reflect"`` |
| `cyclophaser/determine_periods.py:1453` | docstring | `determine_periods` | The defaults before item 31 are frozen in research/labels/defaults_2.0.0.json; |
| `cyclophaser/determine_periods.py:1470` | docstring | `determine_periods` | plot (Union[str, bool], optional): Path to save generated plots. Set to `False` to skip plotting. Default is `False`. |
| `cyclophaser/determine_periods.py:1473` | docstring | `determine_periods` | phase of the algorithm. Set to `False` to disable. Default is `False`. |
| `cyclophaser/determine_periods.py:1476` | docstring | `determine_periods` | exporting. Default is `False`. |
| `cyclophaser/determine_periods.py:1478` | docstring | `determine_periods` | hemisphere (str, optional): Hemisphere of the data. Set to `"southern"` (default) to apply southern hemisphere |
| `cyclophaser/determine_periods.py:1482` | docstring | `determine_periods` | pressure (SLP) data**, set to `"southern"` as the default convention. |
| `cyclophaser/determine_periods.py:1490` | docstring | `determine_periods` | Default is `'auto'`. |
| `cyclophaser/determine_periods.py:1493` | docstring | `determine_periods` | filtered series with a lowpass estimate. **Units:** Time steps. Default is 0 (disabled) — it was 24 |
| `cyclophaser/determine_periods.py:1501` | docstring | `determine_periods` | `True` to use a default window, specify an integer window length, or use `'auto'` to adapt the length based |
| `cyclophaser/determine_periods.py:1502` | docstring | `determine_periods` | on data. **Must be greater than or equal to `savgol_polynomial`** to avoid errors. Default is `False` (`'auto'` up to 2.0.0). |
| `cyclophaser/determine_periods.py:1505` | docstring | `determine_periods` | noise reduction. Choose `True`, `False`, or specify an integer. Default is `False` (`'auto'` up to 2.0.0). |
| `cyclophaser/determine_periods.py:1508` | docstring | `determine_periods` | to the window length specified in `use_smoothing` and `use_smoothing_twice`.** Default is 3. |
| `cyclophaser/determine_periods.py:1511` | docstring | `determine_periods` | for hourly data. **Units:** Time steps. Default is 168. |
| `cyclophaser/determine_periods.py:1514` | docstring | `determine_periods` | for hourly data. **Units:** Time steps. Default is 18.0 (48.0 up to 2.0.0). |
| `cyclophaser/determine_periods.py:1517` | docstring | `determine_periods` | before the Lanczos convolution: `"reflect"` (default; `"edge"` from item 31 until the cleanup front's change C1, and still the |
| `cyclophaser/determine_periods.py:1524` | docstring | `determine_periods` | reproduce results from a version before this default changed — see the |
| `cyclophaser/determine_periods.py:1529` | docstring | `determine_periods` | of the dataset. Default is 0.075. |
| `cyclophaser/determine_periods.py:1531` | docstring | `determine_periods` | threshold_intensification_gap (float, optional): Maximum allowed gap in intensification phase. Default is 0.075. |
| `cyclophaser/determine_periods.py:1534` | docstring | `determine_periods` | of the mature stage. Default is 0.18 (0.125 up to 2.0.0). |
| `cyclophaser/determine_periods.py:1537` | docstring | `determine_periods` | Default is 0.15 (0.03 up to 2.0.0). |
| `cyclophaser/determine_periods.py:1540` | docstring | `determine_periods` | Default is 0.075. |
| `cyclophaser/determine_periods.py:1542` | docstring | `determine_periods` | threshold_decay_gap (float, optional): Maximum allowed gap in decay phase. Default is 0.075. |
| `cyclophaser/determine_periods.py:1545` | docstring | `determine_periods` | dataset. Default is 0.4. |
| `cyclophaser/determine_periods.py:1548` | docstring | `determine_periods` | ``"geometric"`` (the default before item 31; not a parameter of the 2.0.0 release) is the historical rule: the incipient phase runs |
| `cyclophaser/determine_periods.py:1551` | docstring | `determine_periods` | case A/B/C dispatch. ``"plateau"`` (the default since item 31) instead marks the leading stretch over |
| `cyclophaser/determine_periods.py:1557` | docstring | `determine_periods` | artifact at t0 has been controlled. Under the 2.0.0 package defaults the first |
| `cyclophaser/determine_periods.py:1561` | docstring | `determine_periods` | ``boundary_padding="reflect"`` and ``use_smoothing=False``) — as the current defaults are. Default is ``"plateau"``. |
| `cyclophaser/determine_periods.py:1565` | docstring | `determine_periods` | Only used when ``incipient_method="plateau"``. Default is 0.20. |
| `cyclophaser/determine_periods.py:1568` | docstring | `determine_periods` | on. ``"derivative"`` (the default before item 31; not a parameter of the 2.0.0 release) uses ``\|dz_dt_smoothed2\|`` normalised by its |
| `cyclophaser/determine_periods.py:1570` | docstring | `determine_periods` | ``"vorticity"`` (the default since item 31) uses ``\|d(zeta)/dt\|`` computed with ``np.gradient`` on the |
| `cyclophaser/determine_periods.py:1575` | docstring | `determine_periods` | detected. ``"single"`` (the default before item 31; not a parameter of the 2.0.0 release) ends it at the first sample with |
| `cyclophaser/determine_periods.py:1576` | docstring | `determine_periods` | ``rel >= tau``. ``"sustained"`` (the default since item 31) requires ``incipient_plateau_k`` |
| `cyclophaser/determine_periods.py:1583` | docstring | `determine_periods` | ``incipient_plateau_crossing="sustained"``. Default is 5 (3 before item 31; not a parameter of the 2.0.0 release). Ignored for |
| `cyclophaser/determine_periods.py:1589` | docstring | `determine_periods` | therefore every other phase, are untouched. 0 disables it (the default before item 31; not a parameter of the 2.0.0 release). Default is 5. Only used when |
| `cyclophaser/determine_periods.py:1597` | docstring | `determine_periods` | Savitzky-Golay pass. Default is 3. A window at or below this order cannot |
| `cyclophaser/determine_periods.py:1605` | docstring | `determine_periods` | writes no incipient at all). Otherwise nothing changes. Default True since item 31 — **adotada sem validação independente** (item 30); False reproduces the behaviour before item 31 (not a parameter of the 2.0.0 release). Only used when |
| `cyclophaser/determine_periods.py:1621` | docstring | `determine_periods` | ``prominence_relative`` both None — the defaults before item 31; neither is a parameter of the 2.0.0 release — the rule |
| `cyclophaser/determine_periods.py:1627` | docstring | `determine_periods` | **Default True — this is a change of default behaviour.** Index 0 is |
| `cyclophaser/determine_periods.py:1638` | docstring | `determine_periods` | length_scale (str, optional): "local" (default since item 31) or "global" (the default before item 31; not a parameter of the 2.0.0 release). Controls what |
| `cyclophaser/determine_periods.py:1641` | docstring | `determine_periods` | ``threshold_decay_gap`` are fractions *of*. "global" (the default before item 31; not a parameter of the 2.0.0 release) uses the |
| `cyclophaser/determine_periods.py:1649` | docstring | `determine_periods` | mature_method (str, optional): "amplitude" (default since item 31) or "derivative" (the default before item 31; not a parameter of the 2.0.0 release). |
| `cyclophaser/determine_periods.py:1657` | docstring | `determine_periods` | Default 0.90. |
| `cyclophaser/determine_periods.py:1672` | docstring | `determine_periods` | ``find_stages.find_mature_stage``. Default 0.8 since item 31; 0.0 (the default before item 31; not a parameter of the 2.0.0 release) admits every valley and |
| `cyclophaser/determine_periods.py:1707` | docstring | `determine_periods` | ``find_stages.find_intensification_period``. Default 0.05 since item 31; 0.0 (the default before item 31; not a parameter of the 2.0.0 release) switches the |
| `cyclophaser/determine_periods.py:1718` | docstring | `determine_periods` | Default 0.3 since item 31; None (the default before item 31; not a parameter of the 2.0.0 release) disables this check, reproducing the exact behaviour |
| `cyclophaser/determine_periods.py:1729` | docstring | `determine_periods` | - **Data Frequency**: The default values for `cutoff_low`, `cutoff_high`, `replace_endpoints_with_lowpass`, |
| `cyclophaser/determine_periods.py:1845` | comment | `main` | # Test with default parameters |
| `cyclophaser/determine_periods.py:1850` | comment | `main` | # Test with default parameters but without filtering |
| `cyclophaser/determine_periods.py:1855` | comment | `main` | # Test with default parameters but without smoothing |
| `cyclophaser/find_stages.py:8` | comment | `<module>` | # length_scale: "global" (default) vs "local" |
| `cyclophaser/find_stages.py:28` | comment | `<module>` | # `length_scale="local"` (opt-in; default remains "global" for exact backward |
| `cyclophaser/find_stages.py:79` | docstring | `_amplitude_mature_bounds` | distance to the neighbouring z_peak (that's the "derivative"/default method, |
| `cyclophaser/find_stages.py:89` | docstring | `_amplitude_mature_bounds` | exactly like the previous/next z_peak pair the default method already uses |
| `cyclophaser/find_stages.py:173` | docstring | `find_mature_stage` | - "derivative" (default, unchanged behaviour): the mature window is a fixed |
| `cyclophaser/find_stages.py:176` | docstring | `find_mature_stage` | - "amplitude" (opt-in): the mature window is the contiguous stretch of z |
| `cyclophaser/find_stages.py:189` | docstring | `find_mature_stage` | - 'mature_method' (str, optional): "derivative" (default) or |
| `cyclophaser/find_stages.py:197` | docstring | `find_mature_stage` | reach to count as mature. Default 0.90. Only used when |
| `cyclophaser/find_stages.py:206` | docstring | `find_mature_stage` | window around one is sized. Default 0.0 admits every valley and |
| `cyclophaser/find_stages.py:207` | docstring | `find_mature_stage` | reproduces the previous behaviour exactly. A series whose z range |
| `cyclophaser/find_stages.py:217` | docstring | `find_mature_stage` | mature_method="derivative" (see note below). 'global' (default) |
| `cyclophaser/find_stages.py:295` | comment | `find_mature_stage` | # Default 0.0 disables the rule: every valley has D1 >= 0 by construction, |
| `cyclophaser/find_stages.py:452` | docstring | `find_intensification_period` | than it started. Default 0.0 admits every segment whose drop is |
| `cyclophaser/find_stages.py:453` | docstring | `find_intensification_period` | non-negative-or-larger, i.e. reproduces the previous behaviour |
| `cyclophaser/find_stages.py:458` | docstring | `find_intensification_period` | - 'length_scale' (str, optional): 'global' (default) measures both |
| `cyclophaser/find_stages.py:517` | comment | `find_intensification_period` | # Default 0.0 disables the rule outright: the guard below runs the floor |
| `cyclophaser/find_stages.py:518` | comment | `find_intensification_period` | # ONLY when it is > 0, so on the default path no depth is computed and no |
| `cyclophaser/find_stages.py:519` | comment | `find_intensification_period` | # segment can be rejected — the function reproduces its previous behaviour |
| `cyclophaser/find_stages.py:521` | comment | `find_intensification_period` | # segment that ends shallower than it starts is still admitted by default, |
| `cyclophaser/find_stages.py:523` | comment | `find_intensification_period` | # default value.) |
| `cyclophaser/find_stages.py:596` | docstring | `find_decay_period` | - 'length_scale' (str, optional): 'global' (default) measures both |
| `cyclophaser/find_stages.py:666` | docstring | `find_residual_period` | 'decay_tail_amplitude_fraction' note (opt-in, default None: no effect) |
| `cyclophaser/find_stages.py:730` | docstring | `find_residual_period` | Default None disables this check entirely, reproducing the exact |
| `cyclophaser/find_stages.py:819` | comment | `find_residual_period` | # decay_tail_amplitude_fraction (opt-in, see docstring above): if the NaN |
| `cyclophaser/find_stages.py:840` | comment | `<module>` | # incipient_method: "geometric" (default) vs "plateau" |
| `cyclophaser/find_stages.py:844` | comment | `<module>` | # (default 0.4) of the span between the start of the series and the next dz |
| `cyclophaser/find_stages.py:851` | comment | `<module>` | # a median 58 % (author's calibration) / 77 % (package defaults) of its own |
| `cyclophaser/find_stages.py:854` | comment | `<module>` | # `incipient_method="plateau"` (opt-in; default remains "geometric", which is |
| `cyclophaser/find_stages.py:855` | comment | `<module>` | # byte-identical to every prior version) replaces that with a direct slope |
| `cyclophaser/find_stages.py:861` | comment | `<module>` | # artifact at t0 has been dealt with. Under bare package defaults the very |
| `cyclophaser/find_stages.py:866` | comment | `<module>` | # report. This is why the method is opt-in and why tau is exposed rather than |
| `cyclophaser/find_stages.py:899` | comment | `<module>` | # before, and `incipient_smooth_window=0` (the default) reproduces the previous |
| `cyclophaser/find_stages.py:932` | docstring | `_smooth_incipient_probe` | * ``window <= 0`` disables it (the default); |
| `cyclophaser/find_stages.py:964` | docstring | `_incipient_plateau_rel` | BEFORE differentiating it. 0 (default) disables it, reproducing the |
| `cyclophaser/find_stages.py:965` | docstring | `_incipient_plateau_rel` | previous behaviour exactly. **Only used when |
| `cyclophaser/find_stages.py:970` | docstring | `_incipient_plateau_rel` | Default 3. |
| `cyclophaser/find_stages.py:1039` | docstring | `_spare_enclosed_intensification` | """Item 30 (opt-in): the plateau boundary, pulled back so as not to erase an |
| `cyclophaser/find_stages.py:1077` | docstring | `find_incipient_period` | ``"geometric"`` (default, unchanged from every prior version) |
| `cyclophaser/find_stages.py:1083` | docstring | `find_incipient_period` | ``"plateau"`` (opt-in) |
| `cyclophaser/find_stages.py:1102` | docstring | `find_incipient_period` | - 'incipient_method' (str): "geometric" (default) or "plateau". |
| `cyclophaser/find_stages.py:1104` | docstring | `find_incipient_period` | normalised slope. Default 0.20. Only used when method="plateau". |
| `cyclophaser/find_stages.py:1105` | docstring | `find_incipient_period` | - 'incipient_plateau_signal' (str): "derivative" (default) or |
| `cyclophaser/find_stages.py:1107` | docstring | `find_incipient_period` | - 'incipient_plateau_crossing' (str): "single" (default) or |
| `cyclophaser/find_stages.py:1110` | docstring | `find_incipient_period` | "sustained". Default 3. Only used when crossing="sustained". |
| `cyclophaser/find_stages.py:1113` | docstring | `find_incipient_period` | Default 0 (disabled). Only used when method="plateau" AND |
| `cyclophaser/find_stages.py:1116` | docstring | `find_incipient_period` | pass. Default 3. |
| `cyclophaser/find_stages.py:1120` | docstring | `find_incipient_period` | plateau branch). Default False. Only used when method="plateau". |
| `cyclophaser/find_stages.py:1127` | comment | `find_incipient_period` | # .get() with defaults: keeps the function callable with the partial |
| `cyclophaser/find_stages.py:1235` | comment | `<module>` | # Modify the array_vorticity_args if provided, otherwise use defaults |
| `cyclophaser/lanczos_filter.py:6` | comment | `<module>` | # boundary_padding: "reflect" (default) vs "zero" / "edge" |
| `cyclophaser/lanczos_filter.py:41` | comment | `<module>` | #   "reflect" -- DEFAULT since the boundary-artifact fix.  Pads with the |
| `cyclophaser/lanczos_filter.py:48` | comment | `<module>` | #                the default changed. |
| `cyclophaser/lanczos_filter.py:54` | comment | `<module>` | # The DEFAULT IS NOW "reflect".  This is a deliberate behaviour change: leaving |
| `cyclophaser/lanczos_filter.py:55` | comment | `<module>` | # a documented, quantified artefact on by default was the larger cost.  Anyone |
| `cyclophaser/lanczos_filter.py:83` | docstring | `_convolve_same` | With "reflect" (the default) or "edge" the input is padded explicitly with |
| `cyclophaser/lanczos_filter.py:168` | docstring | `lanczos_filter` | own ends before convolution. ``"reflect"`` (default) and ``"edge"`` |
| `cyclophaser/lanczos_filter.py:170` | docstring | `lanczos_filter` | reproduces the behaviour of versions before this default changed. |
| `cyclophaser/lanczos_filter.py:226` | docstring | `lanczos_bandpass_filter` | own ends before convolution. ``"reflect"`` (default) and ``"edge"`` |
| `cyclophaser/lanczos_filter.py:228` | docstring | `lanczos_bandpass_filter` | reproduces the behaviour of versions before this default changed. |
