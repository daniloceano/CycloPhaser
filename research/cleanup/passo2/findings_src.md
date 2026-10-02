# CycloPhaser — consolidated research findings

This document is the single register of what the research fronts behind
`develop-v2.1` established, refuted, decided and left open. It replaces the
front reports and diagnostic outputs under `research/`, which the clean-up front
removes after this document is approved. `docs/future_work.md` stays as the
chronological record and is not rewritten.

Maintained by hand from 2026-09-28. It was last built by
`research/cleanup/passo2/make_findings.py`, with its citation checks, in the
commit that added this paragraph; that generator and its source
`findings_src.md` are no longer edited.

How to read it:

- One line per finding: the claim, its number, its source.
- Every source is `path:line@commit`. Unless stated otherwise the commit is
  `06d8550`, the tip of `develop-v2.1` before the clean-up. Files that leave the
  tree stay readable with `git show 06d8550:<path>`.
- Sources on unmerged branches are cited at the branch commit. Records made by
  the clean-up front itself are cited at their commit on `chore/repo-cleanup`.
- Every number on a line appears on one of the lines it cites. The document is
  rendered by `research/cleanup/passo2/make_findings.py`, which enforces that
  rule, and `research/cleanup/passo2/verify_citations.py` re-checks it.
- "Open" entries point to §S11, which lists every pending item once.

## S01 — Lanczos filter and boundary padding

### Confirmed causes

- The pre-fix convolution zero-pads the series, which injects a boundary step worth a median 74 % of the cyclone's own peak-to-peak amplitude, with the sign of a spurious deepening. {{FW|Result: a step between the boundary value and the interior worth a median **74 % of}}
- That ramp alone accounts for at least 80 % of the slope measured at t₀ in 51/51 tracks. {{FW|carrying the sign of a spurious *deepening*. That ramp alone accounts for}} {{FW|of the slope measured at t₀ in 51/51 tracks**.}}
- The kernel is about half the series (kernel/series ratio median 0.494), so the contaminated zone is about 24 % of the series at each end. {{FW|len(zeta)//2`; measured kernel/series ratio median **0.494** over the 51-track}} {{FW|set), so the contaminated zone is **~24 % of the series at each end}}
- Normalised `|dz|` at the first sample, median over 51 tracks: 0.95 with zero padding, 0.42 with reflect, 0.50 with edge; the raw-signal reference is 0.29. {{FW|over 51 tracks): `"zero"` **0.95/0.98**}} {{FW|**0.50/0.38**. Raw-signal reference: **0.29**.}}
- With the filter active, reflect padding changes fewer phase sequences than zero padding (9/51 against 15/51). {{FW|| filter active, `zero` | **0.949** | **0.981** | **15/51** |}} {{FW|| filter active, `reflect` | **0.415** | **0.346** | **9/51** |}}
- `use_filter=True` was read as the integer 1, a single-tap kernel, so every parameter set calibrated with it had been calibrated on an effectively unfiltered signal. {{FW|`window_length_lanczo = use_filter` read `True` as the integer **1**. A 1-tap}}
- Once the Lanczos boundary was fixed, the derivative Savitzky-Golay pass became the dominant edge artefact: `r(t₀)` 0.068 without it against 0.545 with its automatic window. {{FW|(0.068 → 0.545) and `r(t_final)` by ~7. Under package defaults the factor is smaller}}
- Removing that derivative smoothing changes the phase sequence of 1/51 tracks, in every mode tested. {{FW|3. **The phase output is nearly insensitive to this.** 1/51 sequences change in every}}

### Decisions

- `use_smoothing=False` also skips the derivative Savitzky-Golay passes (author's decision, 2026-09-04); the fixed-window cap was measured and not adopted. {{FW|### Author's decision, 2026-09-04 — `use_smoothing=False` now disables the derivative smoothing}} {{FW|**Explicitly NOT adopted:** the fixed cap (a window of 5–15) and the}}
- That decision is validated on TRACK vorticity only, not on raw reanalysis vorticity. {{FW|**It has NOT been validated on raw ERA5 vorticity**, which reaches}}
- The `boundary_padding` default went zero → reflect (the boundary fix) → edge (item 31) → reflect (C1 of the clean-up front). {{CL@a132f37|**Why `"reflect"`.** `boundary_padding="reflect"` is the default by the}} {{cyclophaser/determine_periods.py@742e685|Item 31 moved the default to ``"edge"``, the padding of the calibration}}

### Open

- Defect I: with edge padding the raw and filtered series disagree on `sign(z[1]-z[0])` in 7 of the 51 real tracks; under the current reflect default it is present on 11 of 54 training series (10 under edge). See §S11. {{FW|`sign(z[1]-z[0])` in **7 of the 51** real calibration tracks (5 of which are}} {{P1/RELATORIO.md@33dc4e1|| defect_I | 11 | 10 |}} {{P1/RELATORIO.md@33dc4e1|Séries: 54 (}}

## S02 — Incipient phase: plateau rule, probe smoothing, refusal

### Confirmed causes

- Under the pre-plateau package defaults no slope-plateau criterion is definable: on 35–50 of 51 tracks the first sample already exceeds every τ up to 0.30. {{IP/REPORT_incipient_characterisation.md|35–50 of 51 tracks the first sample already exceeds every τ up to 0.30. Any}}
- `r(t₀)` is 0.068 under the author's section-3c calibration against 0.526 under those defaults, and this asymmetry decides whether a plateau is definable at all. {{IP/REPORT_incipient_characterisation.md|2. **`r(t0)` is 0.068 (a) vs 0.526 (b)**}}
- The geometric incipient boundary does not sit at a low-slope point: `|dz|` is already at 58 % (a) / 77 % (b) of its maximum there. {{IP/REPORT_incipient_characterisation.md|is already at 58 % (a) / 77 % (b) of its maximum there. The rule is}}
- The catch-all `fillna` produces no incipient phase on real data (case A fires on 0/51). {{IP/REPORT_incipient_characterisation.md|(0/51), and the catch-all `fillna` produces zero incipient phases on real}}
- The `vorticity` probe reads the rate of the RAW series; on real tracks light smoothing does not make it usable (τ=0.20 refuses on 6/7 at window 5), while the `derivative` probe sits below any τ without smoothing. {{IP/REPORT_incipient_smoothing.md|`incipient_plateau_signal="vorticity"` reads the rate on `d(zeta_raw)/dt`. That}} {{IP/REPORT_incipient_smoothing.md|`vorticity` usable (τ=0.20 refuses on 6/7 at w=5) and the window is}}
- On the synthetic series the knee criterion cannot decline an incipient phase (2/2 false positives at every window). {{IP/REPORT_incipient_smoothing.md|1. **The knee is out.** It cannot decline (2/2 false positives at every window),}}
- Front D, params-13, 35 real training series: a short detected incipient on 2, no incipient where the label has one on 6, agreed "none" on 14. {{D/frontD/REPORT.md|| **real (35)** | **2** | **6** | **14** | 13 |}}
- The dominant incipient failure on real training series is refusal: 6 of the 17 series whose label has an incipient phase get none from the detector. {{D/frontD/REPORT.md|* **The dominant incipient failure in TRAIN is refusal**: **6 of the 17** real}}
- All 6 refusals and all 14 agreed-none series go through a single path of the plateau rule (R1). {{D/frontRefusal/REPORT.md|**A single path fires.** All 6 refusals are **R1**, as are all 14 agreed-none.}}
- The refusals are mostly a definitional disagreement between probe and label, not a bug: 4/6 genuine disagreement, 2 near misses, 0 edge artefacts. {{D/frontRefusal/REPORT.md|Counts: **M1 = 0, M2 = 2, M3 = 4, M4 = 0.** Largest group 4/6.}}
- The labels were drawn against a curve, while the probe reads the derivative of the raw series. {{D/frontRefusal/REPORT.md|against a curve, the probe reads the *raw* series' derivative — rather than}}

### Refuted hypotheses

- "The refusals are an edge artefact": the intersection of defect I with the 6 refusals is empty. {{D/frontRefusal/REPORT.md|> **Intersection of defect I with the 6 refusals: empty (0 of 6).**}}
- "A better τ recovers the refusals": a full sweep of τ from 0.20 to 0.80 puts at most 2 of the 6 within tolerance. {{D/frontRefusal/REPORT.md|strong form is now settled by a full sweep — τ ∈ [0.20, 0.80], step 0.0005, 1201}} {{D/frontRefusal/REPORT.md|> **Maximum 2 of 6 within tolerance at ANY τ. No τ reaches 3.**}}
- "Front D's second-step test can tell an artefact from a real short phase": it could never return ARTEFACT, because its margin 6 exceeds its "short" floor 4. {{D/frontD/REPORT.md|The margin (6) is larger than the "short" floor (4), so the two criteria are}}
- "A heavily filtered series is a proxy for which phases exist" (item 18, unmerged branch): exact-sequence agreement 15/47, below the six-function detector (22/47) and below the constant baseline (16/47). {{FW@c508730|| Reader T (the proxy) | **15/47 — 31.9 %** |}} {{FW@c508730|| the six-function detector | 22/47 — 46.8 % |}} {{FW@c508730|| majority-class baseline | 16/47 — 34.0 % |}}
- Item 18 also found incipient presence readable on the unfiltered input (80.9 %) but not on the filtered one (68.1 %, post-hoc best τ). {{FW@c508730|(`incipient_plateau_signal="vorticity"`) reaches **80.9 %** on incipient}} {{FW@c508730|presence against the filtered series' 68.1 %.}}

### Decisions

- For the 12 synthetic cases the maintainer's blind manual label is the ground truth for the incipient phase, not the segment-derived `expected_starts_idx`. {{FW|For the 12 synthetic cases, his blind manual label in}}
- The refusal front closed with no parameter change; reopening needs a new front with a declared premise, never a search over values. {{D/frontRefusal/REPORT.md|**Re-opening requires a NEW front with a declared premise**: an argument for}}

### Geometric against plateau incipient length (the only copy of this table)

- Visual checkpoint, measurement only: incipient length per case under `incipient_method="geometric"` and `"plateau"` (τ 0.20), real tracks under the author's section-3c calibration, synthetic cases under their presets; `designed Ic boundary` is the synthetic generator's designed incipient length. {{IP/gen_geometric_vs_plateau.py|ap.add_argument("--tau", type=float, default=0.20)}} {{IP/gen_geometric_vs_plateau.py|real tracks : the author's validated section-3c calibration, which is the}}
- The table predates the frozen split and the manual labels; its real rows mix future training and test series. {{research/labels/split.yaml|created: '2026-09-06T00:26:54+00:00'}}

{{!csv_table}}

### Open

- Incipient refusal and its reopening rule: §S11.

## S03 — Index 0: extremum type and reclassification

### Confirmed causes

- `argrelextrema` with non-strict comparators and `mode='clip'` marks index 0 as an extremum in 51/51 real tracks, typed only by the sign of the filtered series' first difference. {{FW|passes under a non-strict comparator — index 0 is marked as an extremum in}} {{FW|51/51 real tracks, and its TYPE is decided only by the sign of}}
- Five real tracks have a valley at index 0 with prominence exactly 0.0 and open with a spurious decay. {{D/frontA_reverify/REPORT.md|| index-0 prominence, 5 tracks | exactly `0.0` | met (all 5) |}}
- Front A′ reproduced Front A field by field (990 fields, 0 divergences): Front A measured this repository's code, not a shadowed release. {{D/frontA_reverify/REPORT.md|**990 fields compared, 0 divergences** (`compare_1a.py`; log in}}
- The incipient boundary does not depend on the phase map: it is identical with and without the forced first-extremum type on 63/63 series. {{D/frontA_idx0_c2/REPORT.md|**identical on 63/63**. Table: `outputs/m5_boundary_independence.csv`.}}
- The real and synthetic populations differ at index 0: every real valley at index 0 is a raw/filtered sign disagreement (5 against 0), while the synthetic cases split 3 and 3. {{FW|| 51 real tracks | 5 | 0 |}} {{FW|| 12 synthetic cases | 3 | 3 |}}

### Refuted hypotheses

- "Remove the extremum at index 0": 40/51 tracks then open with decay. {{FW|1. **Remove the index-0 extremum entirely** → 40/51 tracks then open with}}
- "Force index 0 to peak": 4 of the 12 synthetic cases that genuinely open with decay regress. {{FW|3. **Force index 0 to `'peak'` unconditionally** → mechanically clean on the}} {{FW|tracks' first non-incipient phase), **but** 4 of the 12 synthetic cases}}
- "Condition that on raw/filtered sign disagreement": refuted before implementation by the counter-example `IcDItMD_residual_noisy`. {{FW|counter-example `IcDItMD_residual_noisy`: it opens with genuine decay AND}}
- Rule C2 (the next extremum must share index 0's type): reaches 3 of the 5 motivating tracks and gains 0 sequence matches. {{D/frontA_idx0_c2/REPORT.md|- Of the 5 tracks whose index 0 is typed `valley` and that motivated the front,}} {{D/frontA_idx0_c2/REPORT.md|C2 reaches **3**; the two it misses (`20180170`, `20180608`) are missed}} {{D/frontA_idx0_c2/REPORT.md|Net effect of C2 at params-13 on the train split, after that ruling: **0 gained}}

### Decisions

- Rule C2′ (`reclassify_index0`, default True) fires on exactly 5/63 series and 0 of 12 synthetics. {{D/frontA_idx0_c2/REPORT.md|| **Q2** | fires on exactly 5/63; the other 58 byte-identical | fires on exactly those 5; 58 byte-identical; **0 of 12 synthetics** | **CONFIRMED** |}}
- On the 47 training series the sequence counter reads 31/47 → 31/47; with the maintainer's ruling that 20190639 is scored by its blocks, 32/47. {{D/frontA_idx0_c2/REPORT.md|**TRAIN only — 47 series: 31/47 → 31/47.**}} {{D/frontA_idx0_c2/REPORT.md|`20190639` is scored by its blocks (Q6) and not by `score_phase_sequences`,}} {{D/frontA_idx0_c2/REPORT.md|**32/47 — +1 sequence match and one accepted reclassification.**}}
- C2′ can only fire where a prominence filter has broken the alternation of extrema. {{D/frontA_idx0_c2/REPORT.md|**Rule C2' can only fire where something has already removed the extremum}}

### Open

- 20180608 cannot be reached by any reclassification: its opening decay comes from defect I, and defect H masks it (boundary 38 against an 11-step block). See §S11. {{FW|**Backlog addition, 2026-09-24 — `20180608` is handed to this item by item 28.**}} {{FW|`boundary = 38` against an 11-step block, so it is invisible in the output and}}

## S04 — Mature: prominence and amplitude, depth floor, duration floor

### Confirmed causes

- Under params-10 the detector beats the constant baseline on sequence: 30/47 against 16/47. {{D/item19/REPORT.md|| ALL | **16/47** (34.0%) | **30/47** (63.8%) |}}
- `prominence_relative` × `mature_amplitude_fraction` cannot fix 20160735 without destroying other matures: 0 of 45 cells meet all six criteria. {{D/item19/REPORT.md|**Verdict: the gate FAILS. 0 of 45 cells satisfy all six criteria. The declared}} {{D/item19/REPORT.md|refuted: the only two cells in the whole grid that fix `20160735` are the two}}
- The reference cell (params-10) has sequence 30/47, 20160735 with 4 mature blocks, and 2 series with no mature. {{D/item19/stage2_grid.md|Reference: sequence 30/47, `20160735` has 4 mature blocks, 2 series with no mature.}}
- In that cell, 20160735's only block inside its label comes from the one valley with relative prominence 1.0000 (window 154–166, label 145–177). {{D/item19/stage1_prominence.md|| 159 | 1.0000 | 121/210 | 154-166 | 13 | YES | yes |}} {{D/item19/stage1_prominence.md|## (i) `20160735` - every z valley}} {{D/item19/stage1_prominence.md|Label: mature 145 -> 177. Detected mature blocks under params-10: [(8, 10), (55, 62), (154, 166), (225, 232)].}}
- In every informative cell, a lost mature disappears at the prominence filter (stage A). {{D/item19/REPORT.md|**Answer: in every informative cell, the lost matures disappear at stage A — the}}
- The duration check (stage C) accounts for 0 of the 402 observed losses, as predicted from the code before measuring. {{D/item19/PROVENANCE.md|accounts for 0 of the 402 observed mature losses.}} {{D/item19/stage2_losses.md|**402 (cell, series) losses over 42 distinct series.**}}
- 30 of the 32 label-matching matures come from their series' single deepest valley, so `prominence_relative` hardly decides which valley becomes the mature. {{D/item19/REPORT.md|**(b) The "true" prominence distribution is nearly degenerate.** 30 of the 32}}
- 20160735 carries 4 detected mature blocks under params-10 and misses both ends of its label. {{D/item19/stage1_per_series.md|| `20160735` | real | 259 | NO | - / 19 | 4 | 9 | -11 | no |}}
- Valley depth does not separate true from spurious matures across the 35 real training series (D1: min true 0.8805, max spurious 1.0000). {{D/item20b/REPORT.md|### Globally, over the 35 real train series (46 valleys, 32 true / 14 spurious)}} {{D/item20b/REPORT.md|| **D1** | 0.8805 | **1.0000** | −0.1195 | **NO** |}}
- Inside 20160735 alone depth separates cleanly (D2 gap +0.3192). {{D/item20b/REPORT.md|### Restricted to 20160735 alone (4 valleys, 1 true / 3 spurious)}} {{D/item20b/REPORT.md|| **D2** | 1.0000 | 0.6808 | +0.3192 | **YES** |}}
- Three spurious valleys are their series' deepest point (20171179, 20181046, 20205386, all at 1.0000), so no depth rule can reject them. {{D/item20b/REPORT.md|point (`20171179` v45, `20181046` v26, `20205386` v82, all at exactly 1.0000).}}

### Refuted hypotheses

- "A proportional duration floor removes the extra mature blocks" (item 23, unmerged branch): in 20205386 the anchor block is itself spurious, and duration anti-correlates with correctness in 2 of the 5 real multi-block series. {{FW@e7792d3|**In `20205386` the anchor is itself a spurious block, under both implementable}} {{FW@e7792d3|label 129–150. So in **2 of the 5 real multi-block series** — `20205386`, where}}
- A cost-free floor `r ∈ (0.5333, 0.6667]` exists but does not do the job; the maintainer stopped it (backlog, not implemented). {{FW@e7792d3|proposed for: `r ∈ (0.5333, 0.6667]` under anchor A (`(0.5333, 0.5714]` under}} {{FW@e7792d3|### Ruling on the window `(0.5333, 0.6667]` — stopped, not implemented}}

### Decisions

- `mature_amplitude_fraction` 0.95 → 0.90: matures within 6 steps at both ends go from 32/47 to 38/47, with the sequence score unchanged at 30/47. {{D/item19/REPORT.md|`params-10`, moving 0.95 → 0.90 raises the count of matures within ±6 of their}} {{D/item19/REPORT.md|label at both ends from **32/47 to 38/47**, leaves the sequence score at 30/47 and}}
- In the per-series table, 20160735's paired mature moves from 154-166 to 150-181 against its label 145-177. {{D/item20a/tables.md|| `20160735` | real | 145-177 | 154-166 | +9 | -11 | no | 4 | 150-181 | +5 | +4 | YES | 4 |}}
- `mature_min_depth` 0.80: 20160735 reduces to one 32-step block (150, 181); the sequence goes 30/47 → 31/47; the mature boundary holds at 38/47. {{D/item20b/REPORT_stage2.md|**Gate verdict at 0.80: PASS on (a)–(f).**}} {{D/item20b/REPORT_stage2.md|### (a) `20160735` reduces to one block — **PASS**}} {{D/item20b/REPORT_stage2.md|after   [(150, 181)]                                  duration  32}} {{D/item20b/REPORT_stage2.md|**31/47**, against a base of 30/47 and a floor of 30.}} {{D/item20b/REPORT_stage2.md|* mature boundary **38/47** (base 38/47, floor 38). Gained: none. Lost: none.}}
- The floor does not fix 20205386 (all three of its valleys clear 0.80), and 20160735 still misses its sequence. {{D/item20b/REPORT_stage2.md|Note what this also means: **`20205386` is completely unchanged by the floor.**}} {{D/item20b/REPORT_stage2.md|All three of its valleys (D1 0.8687, 0.8805, 1.0000) clear 0.80, so both of its}} {{D/item20b/REPORT_stage2.md|`20160735`. `20160735` still fails its sequence after the fix: its four blocks}}
- 0.85 would score one more sequence (32/47) and leave the shallowest true valley a margin of 0.0305 instead of 0.0805; 0.80 was kept. {{D/item20b/REPORT_stage2.md|| (c) sequence | **31**/47 (gained `20170794`) — PASS | **32**/47 (gained `20150656`, `20170794`) — PASS |}} {{D/item20b/REPORT_stage2.md|leaves the shallowest true valley (`20205386` v61 at 0.8805) a margin of 0.0305}} {{D/item20b/REPORT_stage2.md|instead of 0.0805. Under the adverse denominator of §6 that valley is cut at}} {{D/item20b/REPORT_stage2.md|Both pass. 0.85 additionally removes `20150656` v143 (D1 = 0.8351), which buys}} {{D/item20b/REPORT_stage2.md|| criterion | **0.80** (params-12) | **0.85** (diagnostic) |}}
- The 0.80 floor destroyed 20191014's only mature and the boundary-only gate could not see it: any gate over phase detection needs an explicit existence criterion. {{FW|* **The 0.80 floor destroyed `20191014`'s only mature phase, and 20(b)'s gate}} {{FW|gate over phase detection needs an explicit existence criterion alongside the}}

### Open

- `_amplitude_mature_bounds` has two latent defects, a loud one at `find_stages.py:152` and a silent wrong window at `find_stages.py:160`; both fired 0 times under params-11 and params-12. {{FW|* The two latent defects of `_amplitude_mature_bounds` — `find_stages.py:152`}} {{FW|unfixed. Both fired **0** times here, checked by recomputing `amp_prev < 0` /}}
- `mature_amplitude_fraction = 1.0` can raise `IndexError`, depending on the installed numpy/scipy round-off. {{D/item19/REPORT.md|**(a) `mature_amplitude_fraction = 1.0` can raise `IndexError`, and the missing}}
- The mature window is squeezed from both sides: over 45 overlap-paired windows, start median +2, end −2, duration −5 steps. {{FW|synthetic), over 45 overlap-paired labelled mature windows, the end is early by}} {{FW|a comparable median and a far worse tail: start deviation median **+2**}} {{FW|(−3…+9), end **−2** (−34…+3), duration **−5** (−40…+3). The mature window is}}
- Late mature start (item 17(e)): §S11.

## S05 — Intensification: depth floor

### Confirmed causes

- `find_intensification_period` accepted a segment on duration alone, so a long flat stretch became intensification, which `find_residual_period` then turned into residual to the end of the series. {{D/frontC/REPORT.md|`find_intensification_period` accepted a candidate segment on **duration alone**}}
- Of the 75 raw segments that clear the duration test on the training series, exactly one falls below 0.15 (20180733's spurious segment, D2 0.0068); the smallest legitimate one is 0.1714. {{D/frontC/REPORT.md|2. **75 raw segments, not 68.** Both numbers are real and they count different}} {{CL|test. Exactly one falls below 0.15 — 20180733's spurious segment, at}} {{D/frontC/REPORT.md|`D2 = 0.0068`; smallest legitimate `D2 = 0.1714`; nothing between, so any}}
- Residual is topological (a deepening with no later mature), so writing it to the end of the series is the desired behaviour, not a defect. {{FW|* **The project's definition of `residual` is topological, not amplitude-based.**}}

### Decisions

- `intensification_min_depth` 0.05: one training series changes (20180733, residual removed, decay extended); sequence 31/47 and mature 38/44 unchanged; incipient boundary identical on 47/47. {{D/frontC/REPORT.md|| `research/labels/configs/cyclophaser_params-13.yaml` | params-12 + `intensification_min_depth: 0.05` (params-12 untouched) |}} {{D/frontC/REPORT.md|| series changed | — | **1** (`20180733`) | see below |}} {{D/frontC/REPORT.md|| sequence | 31/47 | **31/47** | 31/47 ✓ |}} {{D/frontC/REPORT.md|| mature within ±6 | 38/44 | **38/44** | 38/44 ✓ |}} {{D/frontC/REPORT.md|| incipient boundary identical | — | **47/47** | identical ✓ |}}
- Any floor in (0.0068, 0.1714] behaves identically on the training series; 0.05 was chosen after the result was known, and only the D2 distribution test was predictive (0 of 75 in (0.02, 0.15]). {{D/frontC/REPORT.md|floor in `(0.0068, 0.1714]` behaves identically on train.}} {{D/frontC/REPORT.md|5. **`0.05` was chosen after the result was known.** Nothing predictive backs}} {{D/frontC/REPORT.md|`(0.02, 0.15]`", declared before the measurement; result **0 of 75**.}}

### Refuted hypotheses

- "The default-behaviour digest is environment-dependent": retracted; a second generator with a different blob layout had been compared against the canonical one. {{D/frontC/REPORT.md|the CHANGELOG value is environment-dependent.~~ **RETRACTED 2026-09-22 —}}

### Open

- Recalibration of `decay_tail_amplitude_fraction`: §S11.

## S06 — `distance` and `length_scale`

### Confirmed causes

- Under the params-9 reference, `distance` removes an extremum on 0 of 47 training series; all 63 removed interior extrema go by prominence. {{D/front_b/REPORT_front_b_part1.md|**Series where `distance` removes any extremum: 0 of 47.**}} {{D/front_b/REPORT_front_b_part1.md|Total interior extrema removed across the train split: **63 by prominence, 0 by}}
- Swept over the full split, `distance` first removes an extremum at 15 and first changes a phase at 20. {{D/front_b/REPORT_front_b_part1.md|29. Over the full split the first value with any effect is **15** (one}} {{D/front_b/REPORT_front_b_part1.md|extremum, no phase change); the first value that changes a phase is **20**.}}
- `length_scale` is never read for the mature window under `mature_method="amplitude"`. {{D/front_b/REPORT_front_b_part1.md|config `mature_method: amplitude`, and in that branch **`length_scale` is never}}

### Refuted hypotheses

- "`distance` makes the matures of 20160735 and 20203947 too short": the filter does nothing at the reference value. {{FW|`distance` extrema filter was producing mature phases that were too short on}} {{FW|`20160735` and `20203947`, with a view to letting `length_scale` govern it. The}}
- "11/12 synthetic is not an evaluator number": it is the evaluator at package defaults (all series 22/47), while 12/12 is the params-9 figure. {{D/front_b/ADDENDUM_part1b.md|**11/12** and ALL sequence **22/47** — identical to the topology script. The}} {{D/front_b/ADDENDUM_part1b.md|package-defaults figures, `12/12` is the `params-9` figure. Full table in §3.}}

### Decisions

- `distance` was removed from the package and the app without a compatibility shim; it was added after 2.0.0 and never published. {{FW|`distance` was added after v2.0.0 (`969904b`) and never published, Danilo's}}

### Open

- `mature_method="derivative"` with `length_scale="global"` yields no mature on both target tracks (local returns 3). {{FW|`length_scale="global"` returns **no mature phase whatsoever** (`local` returns}} {{FW|3). Observed during the causal sweep and not pursued; it may be the same}}
- 20 of the 47 training series carry a detected mature shorter than 7 steps. {{FW|four detected ones). **20 of the 47 training series carry at least one detected}} {{FW|mature shorter than 7 steps** (14 of 35 real, 6 of 12 synthetic). Front B}}
- At `distance=25` the phases of five series changed, 20160735 included, and nobody scored those changes. {{FW|The sweep recorded that at `distance=25` the phase output changes on five}} {{FW|series including `20160735`, and at 30 on eleven. **Whether any of those changes}}

## S07 — Plateau overwriting intensification; the swell batch

### Confirmed causes

- The signal "plateau boundary after the intensity peak" fires in 8/14 bad and 9/182 good swell tracks. {{D/item30/REPORT.md|**P2 — CONFIRMED.** The signal fires in **8/14 bad and 9/182 good** tracks,}}
- Defect H is the mechanism: in 8/8 bad tracks with the signal, the intensification present before the incipient step is erased by the overwrite of `[0, boundary)`. {{D/item30/REPORT.md|**P3 — CONFIRMED, 8/8.** In every one of the 8 bad tracks with the pattern,}} {{FW|isolated defect.** Line 1134 writes `incipient` over `[0, boundary)` whatever the}}
- The signal groups two situations: a peak near index 0, where only decay is erased (7/9 good tracks), and an intensification plus mature swallowed whole. {{D/item30/REPORT.md|- **In 7/9 the peak is at index 0 or 1.** The series opens at its most intense}}
- H is a property of the unconditional overwrite, not an isolated defect: with a right boundary it hides a wrong map, with a late boundary it destroys a correct one. {{FW|**H redescribed (2026-09-26): a property of the unconditional overwrite, not an}} {{FW|- **Boundary late:** it destroys a correct map (20120297, 19940445, 19810854).}}

### Refuted hypotheses

- "The symptom persists in all 8 bad tracks": 5/8, because in the others the overwrite erased the whole mature. {{D/item30/PREDICTIONS.md|P4 sintoma (mature sem intensificação antes, mapa final) persiste 8/8.}} {{D/item30/REPORT.md|**P4 — REFUTED: 5/8, not 8/8.** The symptom persists in 19860380, 19870927,}}
- "In the 9 good tracks the intensification ending at the global minimum also vanishes": 2/9. {{D/item30/PREDICTIONS.md|P5 nos 9 bons com sinal: a intensificação que termina no mínimo global}} {{D/item30/REPORT.md|**P5 — REFUTED: 2/9, not 9/9.** Per the prediction's own dichotomy, H is not}}
- "A pre-incipient quantity separates a late boundary from a right one": none of the three candidates does on the training series (3 late and 2 right cases with a value); the one that clears the partial cases (margin 0.471) only restates the signal. {{D/item30/REPORT_part2.md|late boundary from a right one. c1 and c2 put L on both sides of K. c3 ties them.}} {{D/item30/REPORT_part2.md|With 3 L cases and 2 K cases carrying a value, this is a small sample. The}} {{D/item30/REPORT_part2.md|c3 separates **{L ∪ K}** from **P**, by a margin of 0.471: c3 = 1 in all 5 with}}
- The prediction that c3 does not separate the two groups held, with c3 = 1 in all 3 late cases and in 19860380 and 19870927. {{D/item30/PREDICTIONS_part2.md|Q1 c3 não separa L de K: c3 = 1 nos 3 de L e em 19860380 e 19870927.}} {{D/item30/REPORT_part2.md|**Q1 — CONFIRMED.** c3 does not separate L from K: c3 = 1 in all 3 of L and in}}
- "The spare rule changes exactly 10 swell tracks": 15. Where E lies wholly before the boundary does not imply that the boundary is after the global minimum. {{D/item30/PREDICTIONS_part3.md|R3 swell 196: a regra muda exatamente 10 tracks (8 ruins com padrão +}} {{D/item30/REPORT_part3.md|### R3 refuted: 15, not 10 — and the hypothesis that was wrong}}

### Decisions

- `incipient_plateau_spare_intensification` pulls the boundary back to the start of an intensification block that lies wholly before it. {{D/item30/REPORT_part3.md|- If E also ends before the boundary, the boundary becomes E's start. A}}
- The counterfactual boundary brings the three late cases closer to their labels and 19860380 and 19870927 further from theirs. {{D/item30/REPORT_figs_cf.md|| 19860380 | K | 1 | incipient > decay |}} {{D/item30/REPORT_figs_cf.md|| 19870927 | K | 1 | incipient > decay |}}
- On the 5 adjudicated cases params-15 scores 5/5 against 0/5 for params-14, circular by construction: their labels are the counterfactual. {{D/item30/REPORT_part3.md|| 5 adjudicated | 0/5 → **5/5** | 0/1 → 1/1; label "none" agreed 0/4 → 4/4 |}} {{D/item30/REPORT_part3.md|**The adjudicated block is circular by construction.** Its labels are the}}
- params-15 was adopted "without independent validation"; the 5 validation tracks were seen under params-15 before they were labelled. {{D/item30/REPORT_part3.md|- **Adoption (Danilo): "adotado sem validação independente".** params-15 is}} {{D/item30/REPORT_part3.md|- **V: spent.** The 5 validation tracks were seen under params-15 before they}}
- A "default unchanged" guard must exercise the branch that changed: the canonical digest ran the geometric incipient method at the time, so it could not guard the plateau rule. {{D/item30/REPORT_part3.md|the plateau branch where the rule lives. Its identical digest therefore proves}}

### Open

- H and the spare rule's lack of independent validation: §S11.

## S08 — params-15 / params-track and the package defaults

### Confirmed causes

- params-15 against the pre-item-31 defaults: of 31 keys, 20 differ strictly, 19 by value, 17 in behaviour. {{D/item31/DESIGN.md|* strict (value and type): **20 / 31**;}} {{D/item31/DESIGN.md|* value (`==`): **19 / 31**;}} {{D/item31/DESIGN.md|* behaviour: **17 / 31** (filtering 4/8, phase 13/23).}}
- `use_filter: true` in the preset is behaviour-equal to the default `'auto'`, apart from a `UserWarning`. {{D/item31/param_table.md|| `use_filter` | `'auto'` (str) | `True` (bool) | filtragem |}}
- The original split does not test `incipient_plateau_spare_intensification`: it changes nothing on its 47 training series and 5 of the 7 batch training series. {{D/item31/DESIGN.md|**The original split does NOT test the `spare_intensification` rule.** On its 47}} {{D/item31/DESIGN.md|| batch train | 7 | **5** | 5 | 5 |}}
- Relative to the pre-item-31 defaults, item 31 changed the final map of 54/54 training series and the sequence of 32/54; for example 20150069 loses its incipient phase (end 7 → none). {{CL|* TRAIN: the final map of 54/54 series changes, the phase sequence of 32/54}} {{D/item31/train_sequences_2b.md|| original_real | 20150069 |}}
- Since stage 2c the app's sidebar opens with the package signature defaults (for example `cutoff_high` 18 instead of 48). {{D/item31/sidebar_table_2c.md|| `cutoff_high` | `cutoff_high` | `48` | `18` | `18` | yes |}}

### Scores belong to params-track, not to the current default

- **Every measured score of params-track, on the training and on the test split, was measured under its own `boundary_padding="edge"`; none applies to the current default (`"reflect"`).** {{CL@a132f37|params-track is the only configuration with measured scores, on the training}} {{CL@a132f37|`boundary_padding="edge"`, so they describe params-track. If you work with}} {{research/labels/configs/cyclophaser_params-15.yaml@06d8550:64|boundary_padding: edge}} {{D/item31/stage1_output.txt|config params-15: research/labels/configs/cyclophaser_params-15.yaml sha256}}
- The earlier reference configurations measured by the fronts also carried edge (params-9 in Front B; params-11 and params-14 in item 30). {{D/front_b/REPORT_front_b_part1.md|**Reference config** `research/labels/configs/cyclophaser_params-9.yaml` (`boundary_padding: edge`).}} {{D/item30/REPORT.md|Yes. `filter_params` (including `boundary_padding: edge`) and every}}
- params-track is params-15 renamed, byte for byte. {{P1/RELATORIO.md@33dc4e1|| P2 | sha256(params-track) = sha256(params-15 antes) |}}
- The current defaults differ from params-track in `boundary_padding` and `use_filter` only (plus the absent `prominence` key, whose default is `None`). {{P1/RELATORIO.md@33dc4e1|* params-track × defaults: diferem só em}}

{{!params_track_diff}}

### Stage 1 of item 31 (the single scoring run on the test split)

- Stage 1 passed on 16 test series with params-15, i.e. with `boundary_padding="edge"`: incipient hits 3/9 against 4/9 for the pre-item-31 defaults, refusals agreed 6/6 against 0/6. {{FW|| params-15 | 3/9 | 6/6 | 9/15 | 10/16 | 11/15 | 4 |}} {{FW|| defaults 2.0.0 | 4/9 | 0/6 | 4/15 | 8/16 | 10/15 | 0 |}}
- The PASS is weak evidence: the 16 series were part of the visual calibration set, were seen under params-15 when it was adopted, had test blocks displayed in the Benchmark, and are labelled by the same assessor. {{FW|* the 16 series were part of the visual calibration set (E01);}} {{D/item31/DESIGN.md|> "A etapa 1 NÃO é validação fora da amostra. As 16 séries foram conjunto}}
- The incipient boundary is worse on the test split than on the training split: hits 3/9 against 8/17, false refusals 4/9 against 6/17. {{FW|* Hits for params-15: 3/9 (33 %) on TEST against}} {{FW|8/17 (47 %) on the 35 real TRAIN series.}} {{FW|* False refusals: 4/9 on TEST against 6/17.}}
- The test split is spent: stage 1 is single-shot, and no later choice may be scored on these 16 as if they were held out. {{FW|act as a lock), and no later choice may be scored on these 16 as if they were}}
- The exposure of the test series is reconstructed as 23 events, each tied to a source line; E22 records all 16 test series viewed under params-15. {{FW|* **Exposure of the TEST series.** 23 events, each tied to}} {{D/item31/DESIGN.md|* **E22.** On 2026-09-27, all 16 TEST series of the split, plus the 3 batch}} {{D/item31/exposure_table.md|| E01 | P,D | ALL16 |}}
- The label-only census of the 16 test records, itself a declared exposure: 9 boundary, 6 none, 1 ambiguous. {{D/item31/test_label_census.txt|"records_present": 16,}} {{FW|exposure: n 16; boundary 9, none 6,}} {{FW|ambiguous 1; 15 with a mature;}}

### Decisions

- `boundary_padding="reflect"` is the default by the maintainer's choice (2026-09-28), made without a detection-quality measurement. {{CL@a132f37|maintainer's choice (2026-09-28), made without a detection-quality measurement.}}
- Against edge, C1 changes the final map of 19 of the 54 training series and the phase sequence of 3. {{P1/RELATORIO.md@33dc4e1|| P5 | mapas que mudam entre default e edge > 0 | 19/54 (sequências: 3) | sim |}}

### Open

- Only the TRACK filtering was calibrated; the spare rule has no independent validation; no independent test split remains: §S11.

## S09 — Inert parameters in the calibration app

### Confirmed causes

- The sweep covered 46 (parameter, base configuration) pairs over all 51 tracks; its self-test flagged all 13 pairs of the 5 known inert cases. {{IN/REPORT_inertia_sweep.md|range. 46 (parameter, base_config) pairs, full results in}} {{IN/REPORT_inertia_sweep.md|across its `app.py` UI range over all 51 `tests/calibration_data` tracks,}} {{IN/REPORT_inertia_sweep.md|**PASSED.** All 13 (parameter, base_config) pairs covering the 5 known cases}}
- The prediction of the 5 known inert cases was declared before the sweep ran. {{IN/PREDICTION.md|## Gate (a) — the 5 known cases the sweep must self-rediscover}}
- `savgol_polynomial` is inert whenever `use_smoothing` alone is False (0/51 changed), not only when both passes are off (45/51 changed with only the second pass off). {{IN/REPORT_inertia_sweep.md|**NOT inert** (45/51 tracks changed) — so "second pass off" alone does not}} {{IN/REPORT_inertia_sweep.md|manual, to sidestep an unrelated crash — see below): **INERT** (0/51).}}
- Under `incipient_plateau_signal="derivative"` the single and sustained crossings give the same map on all 51 tracks at 37 of the 56 (τ, k) grid points tested; under `"vorticity"` they differ on 42/51. {{IN/FINDING_signal_derivative_crossing_for_G_E.md|every one of the 51 calibration tracks for nearly the entire UI-reachable}} {{IN/FINDING_signal_derivative_crossing_for_G_E.md|**37 of the 56 grid points — every one with k ≤ 10, i.e. the app's default}} {{IN/FINDING_signal_derivative_crossing_for_G_E.md|produce different results on this calibration set (42/51 tracks changed}}

### Decisions

- Inertia has three categories, not two: by design, data-dependent, unexplained; the unexplained backlog is empty. {{IN/DATA_DEPENDENT_findings.md|**zero** entries — both former candidates below have a traced,}} {{IN/BACKLOG_inexplicada.md|## Current entries: none}}
- Parameters inert by design get a disabled control in the app (for example the three Lanczos parameters when `use_filter` is off). {{IN/REPORT_inertia_sweep.md|### POR DESENHO, NOT signalled — implemented this front}}

### Open

- `process_vorticity(use_smoothing=False, use_smoothing_twice="auto")` raises `ValueError`; it was a one-click crash from the app's then-default state, recorded and not fixed, and the raise is still in the package at `06d8550`. {{IN/INCIDENTAL_crash_bug.md|process_vorticity(zeta_df, use_smoothing=False, use_smoothing_twice="auto")}} {{cyclophaser/determine_periods.py|raise ValueError("Second Savgol window length (use_smoothing_twice) must be >= savgol_polynomial.")}}

## S10 — Traceability

- 40 closed-front scripts stopped running when params-1 to params-14 left the configs directory; they are listed, not migrated, and reproduce from commit `33ea489358d9`. {{FW|* **40 closed-front scripts stop running.** They are listed,}} {{D/item31/stale_scripts.md|Generated by `stale_scripts.py`. 40 tracked script(s) stop running once params-1..14 leave}}
- Every file below leaves the tree after approval and stays readable with `git show 06d8550:<path>`. The "finding recorded at" column cites where its finding is written; the destination is a section of this document or a line of `docs/future_work.md`, never a file that leaves.
- Files that leave without a finding of their own (scripts, and generated outputs whose front report is consolidated here) are not repeated below; they are listed in `research/cleanup/MANIFEST.md`.

{{!traceability}}

## S11 — Open items (recorded, not resolved)

- **Defect H.** The incipient overwrite of `[0, boundary)` is unconditional; redescribed as a property of the overwrite, so the open question is the boundary, not the overwrite. {{FW|isolated defect.** Line 1134 writes `incipient` over `[0, boundary)` whatever the}} {{FW|The question is therefore the boundary, not the overwrite.}}
- **Late mature start (item 17(e)).** All 13 labelled synthetic mature boundaries start after the label, by +1 to +6 steps. {{FW|All **13** labelled mature boundaries have a positive deviation: the detector}} {{FW|places the start of mature **after** the label, by **+1 to +6** steps (12 of}}
- **Spare rule without independent validation.** `incipient_plateau_spare_intensification=True`, which pulls the incipient boundary back, is a default "adopted without independent validation"; the validation batch and the test split are spent. {{FW|* **`incipient_plateau_spare_intensification=True` is "adotada sem validação}} {{FW|it, the validation batch is spent, and the TEST split is spent.}}
- **Only the TRACK filtering was calibrated** (hourly 850 hPa vorticity along tracks); other inputs may need another filtering. {{FW|* **Only the TRACK filtering was calibrated** (hourly 850 hPa vorticity along}}
- **`decay_tail_amplitude_fraction` needs recalibration.** Its documented calibration was made on a pre-correction configuration and does not reproduce; it is inert on the two series tested under params-12. {{FW|`decay_tail_amplitude_fraction`'s documented calibration is not reproducible}} {{FW|Recalibrating it and rewriting those docstrings is **a front of its own, still}}
- **Stopped window of item 20(c).** A cost-free duration floor `r ∈ (0.5333, 0.6667]` is on hold; reopening needs a new front with its premise redeclared. {{FW@e7792d3|### Ruling on the window `(0.5333, 0.6667]` — stopped, not implemented}} {{FW@e7792d3|**Reopening requires a NEW front with its premise redeclared.** Loosening this}}
- **Incipient refusal.** Reopening requires a new front with a declared premise for why a parameter would separate the four genuine-disagreement series from the agreed-none ones; never a search over values. {{D/frontRefusal/REPORT.md|**Re-opening requires a NEW front with a declared premise**: an argument for}}
- **Synthetic generator non-determinism.** Its root cause across environments is unknown; labels are protected only because the series are frozen to files. {{FW|**OPEN — root cause of the synthetic generator's non-determinism across}}
- **Frozen series in CSV.** The exact round-trip depends on a load-bearing float-format pairing; a binary format would remove that hazard. {{FW|**DEBT — the freeze uses CSV, a text format.** `tests/synthetic/data/*.csv`}}
- **CI coverage gap.** CI exercises none of the streamlit/plotly code paths of the calibration app, by design. {{FW|**COVERAGE GAP — CI exercises none of the streamlit/plotly code paths.**}}
- **Label exposure.** The test series were exposed in 23 recorded events before stage 1 scored them. {{FW|* **Exposure of the TEST series.** 23 events, each tied to}}
- **No independent test split.** The test split is spent; any later choice needs newly labelled series. {{FW|* **The TEST split is SPENT.** `stage1_run.py` is single-shot (its output files}}
- **Training re-labels outside develop.** Three re-labels made on `feat/label-tab-toplevel` never reached develop: 20150656 residual 91 → 100, 20170409 decay 74 → 71, 20170154 boundary (incipient end 6) → ambiguous (regenerated by `research/cleanup/passo0/relabel_diff.py`). {{research/labels/manual_labels.yaml@06d8550:629|- id: '20150656'}} {{research/labels/manual_labels.yaml@06d8550:648|start_idx: 91}} {{research/labels/manual_labels.yaml@0c63145:190|start_idx: 100}} {{research/labels/manual_labels.yaml@06d8550:826|- id: '20170409'}} {{research/labels/manual_labels.yaml@06d8550:845|start_idx: 74}} {{research/labels/manual_labels.yaml@0c63145:446|start_idx: 71}} {{research/labels/manual_labels.yaml@06d8550:753|- id: '20170154'}} {{research/labels/manual_labels.yaml@06d8550:777|incipient_end_idx: 6}} {{research/labels/manual_labels.yaml@0c63145:348|kind: ambiguous}}
- **Published app against the published package.** The calibration app installs cyclophaser from PyPI (`>=2.0.0`), whose latest release predates the parameters the app reads; this is an input to the release front. {{tools/calibration_app/requirements.txt|cyclophaser>=2.0.0}} {{research/cleanup/MANIFEST.md@f17d802|do PyPI, e a versão mais nova no PyPI é 2.0.0}} {{research/cleanup/MANIFEST.md@f17d802|leitura estática: o app de develop quebraria na inicialização contra}} {{research/cleanup/MANIFEST.md@d8a19cc|**App publicado × PyPI**: fora de escopo; registrado como insumo da frente de release.}}
- **The canonical digest generator reads test CSVs from disk.** Its docstring says the 16 test ids are not read, but it loads all real CSVs and filters to training afterwards (debt for a later clean-up step). {{D/front_b/default_behaviour_hash.py|The 16 TEST ids are not read at all.}} {{D/front_b/default_behaviour_hash.py|load_real_series().items() if k in train}} {{research/labels/labels_core.py|for p in sorted(d.glob("*.csv")):}}

## S12 — Record corrections

- **C1's premise against what was measured.** When C1 was decided two consequences were expected, no incipient refusals under reflect and defect I leaving the default path; the prediction declared before measuring was 0 refusals on the training series. {{CL@a132f37|The two consequences expected when the change was decided did not hold on the}} {{P1/PREVISOES.md@d8a19cc|| P4 | séries de treino que recusam incipient: 0 sob o novo default (`reflect`) |}}
- Measured: 28/54 refusals under reflect and 28/54 under edge, the same series; defect I on 11 of 54 under reflect against 10 under edge, so it stays on the default path. {{P1/RELATORIO.md@33dc4e1|| P4 | recusas de incipient sob reflect = 0 | **28/54** (edge: 28/54, as mesmas séries) | **NÃO** |}} {{P1/RELATORIO.md@33dc4e1|| defect_I | 11 | 10 |}}
- Mechanism: the default `incipient_plateau_signal="vorticity"` measures the plateau on the unfiltered input, which the padding never touches; under `"derivative"` the padding decides (2/54 refusals under reflect against 32/54 under edge, post-hoc). {{cyclophaser/find_stages.py|``|d(zeta_raw)/dt|`` via ``np.gradient`` on the UNFILTERED input,}} {{P1/RELATORIO.md@33dc4e1|Recusas por sinal × padding: vorticity/reflect: 28/54; vorticity/edge: 28/54; derivative/reflect: 2/54; derivative/edge: 32/54.}}
- The app's help text states the contrast (0/51 refusals under reflect, 33/51 under edge) without naming the incipient signal; the post-hoc check reproduces a contrast of that kind only under `"derivative"`. {{tools/calibration_app/app.py|incipient phase (0/51); under `edge`, 33/51 refuse. Changing it}}
- **The "2.0.0" label.** `research/labels/defaults_2.0.0.json`, the `*_2_0_0` baselines and the "2.0.0" columns of item 31 describe develop before item 31, not the published release: the release has no `boundary_padding` (it always zero-pads) and uses `replace_endpoints_with_lowpass=24`. {{research/labels/defaults_2.0.0.json|"source": "research/labels/diagnostics/item31/param_table.json @ e42da8b (column 'default')",}} {{CL@a132f37|| `replace_endpoints_with_lowpass` | `24` | `0` |}} {{CL@a132f37|| `boundary_padding` | — (no such parameter) | `"reflect"` |}}
- For example, the stage-1 row labelled "defaults 2.0.0" is the pre-item-31 table passed explicitly. {{FW|| defaults 2.0.0 | 4/9 | 0/6 | 4/15 | 8/16 | 10/15 | 0 |}}
- **C2′'s "no change under package defaults" (0 of 64 series).** That was measured when `prominence` and `prominence_relative` were both None; since item 31 the default `prominence_relative` is 0.3, so the scope no longer holds. {{D/frontA_idx0_c2/REPORT.md|Measured on this corpus (0 of 64 under no filtering) and argued from the}} {{CL@a132f37|| `prominence_relative` | — (no such parameter) | `0.3` |}}
- **Two instruments for "correct mature".** `evaluate_against_labels.py` (`labels_core.score_phase_sequences`) scores a series only on an exact whole-sequence match, compares phase starts only, and uses each label's own tolerance, so on 47 series its ceiling for mature was 30 when a gate asked for 38/47. {{D/item20a/BLOCKER_pairing_rule.md|1. **Ceiling of 30, not 47.** Only sequence-matching series contribute a mature}} {{D/item20a/BLOCKER_pairing_rule.md|Gate (a) asks for "matures within ±6 at both ends: exactly 38/47". This script}}
- `item19_core.pair_by_overlap` scores every series: it pairs the first labelled mature with the detected block of largest overlap and requires both ends within a fixed margin of 6. {{D/item19/item19_core.py|MARGIN = 6            # item 17(d): the asserted boundary margin is a fixed 6}} {{D/item20a/REPORT.md|`pair_by_overlap` scores **only the first labelled mature** (`first_lab =}}
- Which governs what: phase-sequence claims use the evaluator; mature-window gates (items 20, 20(a), 20(b) and Front C) used `pair_by_overlap`; the Benchmark reports both, named. The three local copies of `pair_by_overlap` leave with their diagnostics. {{D/item20a/REPORT.md|| (a), (e) | `pair_by_overlap`, `research/labels/diagnostics/item19/item19_core.py:130` — largest-overlap pairing, **both ends**, fixed margin 6 |}} {{D/frontC/REPORT.md|* The mature metric is the same instrument as front 20(b) stage 2}} {{tools/calibration_app/benchmark_core.py|SEQUENCE_INSTRUMENT = "evaluate_against_labels.py / score_phase_sequences"}}
- **A summary that its own table contradicts.** The inert-parameter records state that the single and sustained crossings agree on all 51 tracks for every τ at k ≤ 10 and diverge only at k ≥ 15, but the table they rest on has 1 diverging track at τ 0.50, k 10. The count of 37 zero-divergence points out of 56 is right, but those points are not the k ≤ 10 points. The inertia report and `docs/future_work.md` repeat the claim. {{IN/FINDING_signal_derivative_crossing_for_G_E.md|**37 of the 56 grid points — every one with k ≤ 10, i.e. the app's default}} {{IN/DATA_DEPENDENT_findings.md|- 0/51 tracks differ for every τ at k ≤ 10 (37/56 grid points, including}} {{IN/FINDING_signal_derivative_crossing_for_G_E.md|| 0.50 | 0 | 0 | 0 | 0 | 1 | 2 | 5 | 8 |}} {{IN/FINDING_signal_derivative_crossing_for_G_E.md|Divergence only appears at `k ≥ 15`, and even then}} {{IN/REPORT_inertia_sweep.md|for every k ≤ 10** (37/56 grid points, including the default), and}} {{FW|on all 51 tracks for `k ≤ 10`, across the whole τ range tested — not in}}
- **Item 18 and item 23 exist only on unmerged branches.** `docs/future_work.md` on develop goes from item 17 to item 19 and from item 22 to item 24; their findings are in §S02 (item 18) and §S04 (item 23), cited at `c508730` and `e7792d3`. {{FW|## 17. Front G — synthetic timing test reads the manual labels}} {{FW|## 19. Front B — `distance` removed; premise refuted}} {{FW|## 22. Front 20(b) — `mature_min_depth`}} {{FW|## 24. Front C — `intensification_min_depth`}}
