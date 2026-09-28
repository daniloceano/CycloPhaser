# CycloPhaser — consolidated research findings

This document is the single register of what the research fronts behind
`develop-v2.1` established, refuted, decided and left open. It replaces the
front reports and diagnostic outputs under `research/`, which the clean-up front
removes after this document is approved. `docs/future_work.md` stays as the
chronological record and is not rewritten.

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

- The pre-fix convolution zero-pads the series, which injects a boundary step worth a median 74 % of the cyclone's own peak-to-peak amplitude, with the sign of a spurious deepening. `docs/future_work.md:278@06d8550`
- That ramp alone accounts for at least 80 % of the slope measured at t₀ in 51/51 tracks. `docs/future_work.md:280@06d8550` `docs/future_work.md:281@06d8550`
- The kernel is about half the series (kernel/series ratio median 0.494), so the contaminated zone is about 24 % of the series at each end. `docs/future_work.md:271@06d8550` `docs/future_work.md:272@06d8550`
- Normalised `|dz|` at the first sample, median over 51 tracks: 0.95 with zero padding, 0.42 with reflect, 0.50 with edge; the raw-signal reference is 0.29. `docs/future_work.md:284@06d8550` `docs/future_work.md:285@06d8550`
- With the filter active, reflect padding changes fewer phase sequences than zero padding (9/51 against 15/51). `docs/future_work.md:316@06d8550` `docs/future_work.md:317@06d8550`
- `use_filter=True` was read as the integer 1, a single-tap kernel, so every parameter set calibrated with it had been calibrated on an effectively unfiltered signal. `docs/future_work.md:294@06d8550`
- Once the Lanczos boundary was fixed, the derivative Savitzky-Golay pass became the dominant edge artefact: `r(t₀)` 0.068 without it against 0.545 with its automatic window. `docs/future_work.md:453@06d8550`
- Removing that derivative smoothing changes the phase sequence of 1/51 tracks, in every mode tested. `docs/future_work.md:459@06d8550`

### Decisions

- `use_smoothing=False` also skips the derivative Savitzky-Golay passes (author's decision, 2026-09-04); the fixed-window cap was measured and not adopted. `docs/future_work.md:488@06d8550` `docs/future_work.md:498@06d8550`
- That decision is validated on TRACK vorticity only, not on raw reanalysis vorticity. `docs/future_work.md:513@06d8550`
- The `boundary_padding` default went zero → reflect (the boundary fix) → edge (item 31) → reflect (C1 of the clean-up front). `CHANGELOG.md:99@a132f37` `cyclophaser/determine_periods.py:561@742e685`

### Open

- Defect I: with edge padding the raw and filtered series disagree on `sign(z[1]-z[0])` in 7 of the 51 real tracks; under the current reflect default it is present on 11 of 54 training series (10 under edge). See §S11. `docs/future_work.md:675@06d8550` `research/cleanup/passo1/RELATORIO.md:25@33dc4e1` `research/cleanup/passo1/RELATORIO.md:18@33dc4e1`

## S02 — Incipient phase: plateau rule, probe smoothing, refusal

### Confirmed causes

- Under the pre-plateau package defaults no slope-plateau criterion is definable: on 35–50 of 51 tracks the first sample already exceeds every τ up to 0.30. `research/incipient_plateau/REPORT_incipient_characterisation.md:314@06d8550`
- `r(t₀)` is 0.068 under the author's section-3c calibration against 0.526 under those defaults, and this asymmetry decides whether a plateau is definable at all. `research/incipient_plateau/REPORT_incipient_characterisation.md:311@06d8550`
- The geometric incipient boundary does not sit at a low-slope point: `|dz|` is already at 58 % (a) / 77 % (b) of its maximum there. `research/incipient_plateau/REPORT_incipient_characterisation.md:320@06d8550`
- The catch-all `fillna` produces no incipient phase on real data (case A fires on 0/51). `research/incipient_plateau/REPORT_incipient_characterisation.md:305@06d8550`
- The `vorticity` probe reads the rate of the RAW series; on real tracks light smoothing does not make it usable (τ=0.20 refuses on 6/7 at window 5), while the `derivative` probe sits below any τ without smoothing. `research/incipient_plateau/REPORT_incipient_smoothing.md:17@06d8550` `research/incipient_plateau/REPORT_incipient_smoothing.md:169@06d8550`
- On the synthetic series the knee criterion cannot decline an incipient phase (2/2 false positives at every window). `research/incipient_plateau/REPORT_incipient_smoothing.md:159@06d8550`
- Front D, params-13, 35 real training series: a short detected incipient on 2, no incipient where the label has one on 6, agreed "none" on 14. `research/labels/diagnostics/frontD/REPORT.md:138@06d8550`
- The dominant incipient failure on real training series is refusal: 6 of the 17 series whose label has an incipient phase get none from the detector. `research/labels/diagnostics/frontD/REPORT.md:506@06d8550`
- All 6 refusals and all 14 agreed-none series go through a single path of the plateau rule (R1). `research/labels/diagnostics/frontRefusal/REPORT.md:97@06d8550`
- The refusals are mostly a definitional disagreement between probe and label, not a bug: 4/6 genuine disagreement, 2 near misses, 0 edge artefacts. `research/labels/diagnostics/frontRefusal/REPORT.md:189@06d8550`
- The labels were drawn against a curve, while the probe reads the derivative of the raw series. `research/labels/diagnostics/frontRefusal/REPORT.md:309@06d8550`

### Refuted hypotheses

- "The refusals are an edge artefact": the intersection of defect I with the 6 refusals is empty. `research/labels/diagnostics/frontRefusal/REPORT.md:150@06d8550`
- "A better τ recovers the refusals": a full sweep of τ from 0.20 to 0.80 puts at most 2 of the 6 within tolerance. `research/labels/diagnostics/frontRefusal/REPORT.md:339@06d8550` `research/labels/diagnostics/frontRefusal/REPORT.md:343@06d8550`
- "Front D's second-step test can tell an artefact from a real short phase": it could never return ARTEFACT, because its margin 6 exceeds its "short" floor 4. `research/labels/diagnostics/frontD/REPORT.md:433@06d8550`
- "A heavily filtered series is a proxy for which phases exist" (item 18, unmerged branch): exact-sequence agreement 15/47, below the six-function detector (22/47) and below the constant baseline (16/47). `docs/future_work.md:1450@c508730` `docs/future_work.md:1451@c508730` `docs/future_work.md:1452@c508730`
- Item 18 also found incipient presence readable on the unfiltered input (80.9 %) but not on the filtered one (68.1 %, post-hoc best τ). `docs/future_work.md:1487@c508730` `docs/future_work.md:1488@c508730`

### Decisions

- For the 12 synthetic cases the maintainer's blind manual label is the ground truth for the incipient phase, not the segment-derived `expected_starts_idx`. `docs/future_work.md:1307@06d8550`
- The refusal front closed with no parameter change; reopening needs a new front with a declared premise, never a search over values. `research/labels/diagnostics/frontRefusal/REPORT.md:380@06d8550`

### Geometric against plateau incipient length (the only copy of this table)

- Visual checkpoint, measurement only: incipient length per case under `incipient_method="geometric"` and `"plateau"` (τ 0.20), real tracks under the author's section-3c calibration, synthetic cases under their presets; `designed Ic boundary` is the synthetic generator's designed incipient length. `research/incipient_plateau/gen_geometric_vs_plateau.py:238@06d8550` `research/incipient_plateau/gen_geometric_vs_plateau.py:20@06d8550`
- The table predates the frozen split and the manual labels; its real rows mix future training and test series. `research/labels/split.yaml:2@06d8550`

| set | case | geometric | plateau | designed Ic boundary | source |
|---|---|---|---|---|---|
| real | `20150377` | 3 | 4 | — | `research/incipient_plateau/geometric_vs_plateau.csv:2@06d8550` |
| real | `20190325` | 1 | 7 | — | `research/incipient_plateau/geometric_vs_plateau.csv:3@06d8550` |
| real | `20190639` | 3 | 3 | — | `research/incipient_plateau/geometric_vs_plateau.csv:4@06d8550` |
| real | `20203373` | 8 | 9 | — | `research/incipient_plateau/geometric_vs_plateau.csv:5@06d8550` |
| real | `20203947` | 2 | 14 | — | `research/incipient_plateau/geometric_vs_plateau.csv:6@06d8550` |
| real | `20206498` | 0 | 9 | — | `research/incipient_plateau/geometric_vs_plateau.csv:7@06d8550` |
| synthetic | `ItMD_clean` | 7 | 4 | 3.0 | `research/incipient_plateau/geometric_vs_plateau.csv:8@06d8550` |
| synthetic | `IcItMD_residual_noisy` | 5 | 3 | 3.0 | `research/incipient_plateau/geometric_vs_plateau.csv:9@06d8550` |
| synthetic | `ItMD_noisy` | 5 | 2 | — | `research/incipient_plateau/geometric_vs_plateau.csv:10@06d8550` |
| synthetic | `IcDItMD_noisy` | 4 | 2 | — | `research/incipient_plateau/geometric_vs_plateau.csv:11@06d8550` |
| synthetic | `IcDItMD_residual_noisy` | 3 | 1 | — | `research/incipient_plateau/geometric_vs_plateau.csv:12@06d8550` |
| synthetic | `DItMD_noisy` | 3 | 1 | — | `research/incipient_plateau/geometric_vs_plateau.csv:13@06d8550` |
| synthetic | `DItMD_residual_noisy` | 3 | 1 | — | `research/incipient_plateau/geometric_vs_plateau.csv:14@06d8550` |
| synthetic | `IcItMD_ItMD_noisy` | 4 | 2 | 3.0 | `research/incipient_plateau/geometric_vs_plateau.csv:15@06d8550` |
| synthetic | `ItMD_ItMD_noisy` | 3 | 1 | — | `research/incipient_plateau/geometric_vs_plateau.csv:16@06d8550` |
| synthetic | `IcIt_observational` | 4 | 10 | 6.0 | `research/incipient_plateau/geometric_vs_plateau.csv:17@06d8550` |
| synthetic | `quase_ItD` | 7 | 1 | — | `research/incipient_plateau/geometric_vs_plateau.csv:18@06d8550` |
| synthetic | `IcItMD_residual_clean` | 5 | 3 | 3.0 | `research/incipient_plateau/geometric_vs_plateau.csv:19@06d8550` |

### Open

- Incipient refusal and its reopening rule: §S11.

## S03 — Index 0: extremum type and reclassification

### Confirmed causes

- `argrelextrema` with non-strict comparators and `mode='clip'` marks index 0 as an extremum in 51/51 real tracks, typed only by the sign of the filtered series' first difference. `docs/future_work.md:597@06d8550` `docs/future_work.md:598@06d8550`
- Five real tracks have a valley at index 0 with prominence exactly 0.0 and open with a spurious decay. `research/labels/diagnostics/frontA_reverify/REPORT.md:159@06d8550`
- Front A′ reproduced Front A field by field (990 fields, 0 divergences): Front A measured this repository's code, not a shadowed release. `research/labels/diagnostics/frontA_reverify/REPORT.md:163@06d8550`
- The incipient boundary does not depend on the phase map: it is identical with and without the forced first-extremum type on 63/63 series. `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:337@06d8550`
- The real and synthetic populations differ at index 0: every real valley at index 0 is a raw/filtered sign disagreement (5 against 0), while the synthetic cases split 3 and 3. `docs/future_work.md:705@06d8550` `docs/future_work.md:706@06d8550`

### Refuted hypotheses

- "Remove the extremum at index 0": 40/51 tracks then open with decay. `docs/future_work.md:606@06d8550`
- "Force index 0 to peak": 4 of the 12 synthetic cases that genuinely open with decay regress. `docs/future_work.md:613@06d8550` `docs/future_work.md:616@06d8550`
- "Condition that on raw/filtered sign disagreement": refuted before implementation by the counter-example `IcDItMD_residual_noisy`. `docs/future_work.md:623@06d8550`
- Rule C2 (the next extremum must share index 0's type): reaches 3 of the 5 motivating tracks and gains 0 sequence matches. `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:47@06d8550` `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:48@06d8550` `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:60@06d8550`

### Decisions

- Rule C2′ (`reclassify_index0`, default True) fires on exactly 5/63 series and 0 of 12 synthetics. `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:445@06d8550`
- On the 47 training series the sequence counter reads 31/47 → 31/47; with the maintainer's ruling that 20190639 is scored by its blocks, 32/47. `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:469@06d8550` `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:471@06d8550` `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:473@06d8550`
- C2′ can only fire where a prominence filter has broken the alternation of extrema. `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:498@06d8550`

### Open

- 20180608 cannot be reached by any reclassification: its opening decay comes from defect I, and defect H masks it (boundary 38 against an 11-step block). See §S11. `docs/future_work.md:682@06d8550` `docs/future_work.md:692@06d8550`

## S04 — Mature: prominence and amplitude, depth floor, duration floor

### Confirmed causes

- Under params-10 the detector beats the constant baseline on sequence: 30/47 against 16/47. `research/labels/diagnostics/item19/REPORT.md:85@06d8550`
- `prominence_relative` × `mature_amplitude_fraction` cannot fix 20160735 without destroying other matures: 0 of 45 cells meet all six criteria. `research/labels/diagnostics/item19/REPORT.md:3@06d8550` `research/labels/diagnostics/item19/REPORT.md:7@06d8550`
- The reference cell (params-10) has sequence 30/47, 20160735 with 4 mature blocks, and 2 series with no mature. `research/labels/diagnostics/item19/stage2_grid.md:8@06d8550`
- In that cell, 20160735's only block inside its label comes from the one valley with relative prominence 1.0000 (window 154–166, label 145–177). `research/labels/diagnostics/item19/stage1_prominence.md:29@06d8550` `research/labels/diagnostics/item19/stage1_prominence.md:14@06d8550` `research/labels/diagnostics/item19/stage1_prominence.md:16@06d8550`
- In every informative cell, a lost mature disappears at the prominence filter (stage A). `research/labels/diagnostics/item19/REPORT.md:322@06d8550`
- The duration check (stage C) accounts for 0 of the 402 observed losses, as predicted from the code before measuring. `research/labels/diagnostics/item19/PROVENANCE.md:12@06d8550` `research/labels/diagnostics/item19/stage2_losses.md:14@06d8550`
- 30 of the 32 label-matching matures come from their series' single deepest valley, so `prominence_relative` hardly decides which valley becomes the mature. `research/labels/diagnostics/item19/REPORT.md:430@06d8550`
- 20160735 carries 4 detected mature blocks under params-10 and misses both ends of its label. `research/labels/diagnostics/item19/stage1_per_series.md:20@06d8550`
- Valley depth does not separate true from spurious matures across the 35 real training series (D1: min true 0.8805, max spurious 1.0000). `research/labels/diagnostics/item20b/REPORT.md:311@06d8550` `research/labels/diagnostics/item20b/REPORT.md:315@06d8550`
- Inside 20160735 alone depth separates cleanly (D2 gap +0.3192). `research/labels/diagnostics/item20b/REPORT.md:322@06d8550` `research/labels/diagnostics/item20b/REPORT.md:327@06d8550`
- Three spurious valleys are their series' deepest point (20171179, 20181046, 20205386, all at 1.0000), so no depth rule can reject them. `research/labels/diagnostics/item20b/REPORT.md:454@06d8550`

### Refuted hypotheses

- "A proportional duration floor removes the extra mature blocks" (item 23, unmerged branch): in 20205386 the anchor block is itself spurious, and duration anti-correlates with correctness in 2 of the 5 real multi-block series. `docs/future_work.md:2209@e7792d3` `docs/future_work.md:2226@e7792d3`
- A cost-free floor `r ∈ (0.5333, 0.6667]` exists but does not do the job; the maintainer stopped it (backlog, not implemented). `docs/future_work.md:2270@e7792d3` `docs/future_work.md:2286@e7792d3`

### Decisions

- `mature_amplitude_fraction` 0.95 → 0.90: matures within 6 steps at both ends go from 32/47 to 38/47, with the sequence score unchanged at 30/47. `research/labels/diagnostics/item19/REPORT.md:440@06d8550` `research/labels/diagnostics/item19/REPORT.md:441@06d8550`
- In the per-series table, 20160735's paired mature moves from 154-166 to 150-181 against its label 145-177. `research/labels/diagnostics/item20a/tables.md:15@06d8550`
- `mature_min_depth` 0.80: 20160735 reduces to one 32-step block (150, 181); the sequence goes 30/47 → 31/47; the mature boundary holds at 38/47. `research/labels/diagnostics/item20b/REPORT_stage2.md:8@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:114@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:118@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:139@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:161@06d8550`
- The floor does not fix 20205386 (all three of its valleys clear 0.80), and 20160735 still misses its sequence. `research/labels/diagnostics/item20b/REPORT_stage2.md:174@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:175@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:393@06d8550`
- 0.85 would score one more sequence (32/47) and leave the shallowest true valley a margin of 0.0305 instead of 0.0805; 0.80 was kept. `research/labels/diagnostics/item20b/REPORT_stage2.md:310@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:320@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:321@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:316@06d8550` `research/labels/diagnostics/item20b/REPORT_stage2.md:306@06d8550`
- The 0.80 floor destroyed 20191014's only mature and the boundary-only gate could not see it: any gate over phase detection needs an explicit existence criterion. `docs/future_work.md:2287@06d8550` `docs/future_work.md:2294@06d8550`

### Open

- `_amplitude_mature_bounds` has two latent defects, a loud one at `find_stages.py:152` and a silent wrong window at `find_stages.py:160`; both fired 0 times under params-11 and params-12. `docs/future_work.md:2269@06d8550` `docs/future_work.md:2271@06d8550`
- `mature_amplitude_fraction = 1.0` can raise `IndexError`, depending on the installed numpy/scipy round-off. `research/labels/diagnostics/item19/REPORT.md:407@06d8550`
- The mature window is squeezed from both sides: over 45 overlap-paired windows, start median +2, end −2, duration −5 steps. `docs/future_work.md:1593@06d8550` `docs/future_work.md:1594@06d8550` `docs/future_work.md:1595@06d8550`
- Late mature start (item 17(e)): §S11.

## S05 — Intensification: depth floor

### Confirmed causes

- `find_intensification_period` accepted a segment on duration alone, so a long flat stretch became intensification, which `find_residual_period` then turned into residual to the end of the series. `research/labels/diagnostics/frontC/REPORT.md:15@06d8550`
- Of the 75 raw segments that clear the duration test on the training series, exactly one falls below 0.15 (20180733's spurious segment, D2 0.0068); the smallest legitimate one is 0.1714. `research/labels/diagnostics/frontC/REPORT.md:96@06d8550` `CHANGELOG.md:285@06d8550` `research/labels/diagnostics/frontC/REPORT.md:102@06d8550`
- Residual is topological (a deepening with no later mature), so writing it to the end of the series is the desired behaviour, not a defect. `docs/future_work.md:2297@06d8550`

### Decisions

- `intensification_min_depth` 0.05: one training series changes (20180733, residual removed, decay extended); sequence 31/47 and mature 38/44 unchanged; incipient boundary identical on 47/47. `research/labels/diagnostics/frontC/REPORT.md:35@06d8550` `research/labels/diagnostics/frontC/REPORT.md:51@06d8550` `research/labels/diagnostics/frontC/REPORT.md:47@06d8550` `research/labels/diagnostics/frontC/REPORT.md:48@06d8550` `research/labels/diagnostics/frontC/REPORT.md:50@06d8550`
- Any floor in (0.0068, 0.1714] behaves identically on the training series; 0.05 was chosen after the result was known, and only the D2 distribution test was predictive (0 of 75 in (0.02, 0.15]). `research/labels/diagnostics/frontC/REPORT.md:103@06d8550` `research/labels/diagnostics/frontC/REPORT.md:150@06d8550` `research/labels/diagnostics/frontC/REPORT.md:138@06d8550`

### Refuted hypotheses

- "The default-behaviour digest is environment-dependent": retracted; a second generator with a different blob layout had been compared against the canonical one. `research/labels/diagnostics/frontC/REPORT.md:85@06d8550`

### Open

- Recalibration of `decay_tail_amplitude_fraction`: §S11.

## S06 — `distance` and `length_scale`

### Confirmed causes

- Under the params-9 reference, `distance` removes an extremum on 0 of 47 training series; all 63 removed interior extrema go by prominence. `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:219@06d8550` `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:220@06d8550`
- Swept over the full split, `distance` first removes an extremum at 15 and first changes a phase at 20. `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:9@06d8550` `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:10@06d8550`
- `length_scale` is never read for the mature window under `mature_method="amplitude"`. `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:35@06d8550`

### Refuted hypotheses

- "`distance` makes the matures of 20160735 and 20203947 too short": the filter does nothing at the reference value. `docs/future_work.md:1571@06d8550` `docs/future_work.md:1572@06d8550`
- "11/12 synthetic is not an evaluator number": it is the evaluator at package defaults (all series 22/47), while 12/12 is the params-9 figure. `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:24@06d8550` `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:26@06d8550`

### Decisions

- `distance` was removed from the package and the app without a compatibility shim; it was added after 2.0.0 and never published. `docs/future_work.md:1584@06d8550`

### Open

- `mature_method="derivative"` with `length_scale="global"` yields no mature on both target tracks (local returns 3). `docs/future_work.md:1601@06d8550` `docs/future_work.md:1602@06d8550`
- 20 of the 47 training series carry a detected mature shorter than 7 steps. `docs/future_work.md:1612@06d8550` `docs/future_work.md:1613@06d8550`
- At `distance=25` the phases of five series changed, 20160735 included, and nobody scored those changes. `docs/future_work.md:1619@06d8550` `docs/future_work.md:1620@06d8550`

## S07 — Plateau overwriting intensification; the swell batch

### Confirmed causes

- The signal "plateau boundary after the intensity peak" fires in 8/14 bad and 9/182 good swell tracks. `research/labels/diagnostics/item30/REPORT.md:155@06d8550`
- Defect H is the mechanism: in 8/8 bad tracks with the signal, the intensification present before the incipient step is erased by the overwrite of `[0, boundary)`. `research/labels/diagnostics/item30/REPORT.md:158@06d8550` `docs/future_work.md:3474@06d8550`
- The signal groups two situations: a peak near index 0, where only decay is erased (7/9 good tracks), and an intensification plus mature swallowed whole. `research/labels/diagnostics/item30/REPORT.md:140@06d8550`
- H is a property of the unconditional overwrite, not an isolated defect: with a right boundary it hides a wrong map, with a late boundary it destroys a correct one. `docs/future_work.md:3473@06d8550` `docs/future_work.md:3479@06d8550`

### Refuted hypotheses

- "The symptom persists in all 8 bad tracks": 5/8, because in the others the overwrite erased the whole mature. `research/labels/diagnostics/item30/PREDICTIONS.md:9@06d8550` `research/labels/diagnostics/item30/REPORT.md:163@06d8550`
- "In the 9 good tracks the intensification ending at the global minimum also vanishes": 2/9. `research/labels/diagnostics/item30/PREDICTIONS.md:10@06d8550` `research/labels/diagnostics/item30/REPORT.md:169@06d8550`
- "A pre-incipient quantity separates a late boundary from a right one": none of the three candidates does on the training series (3 late and 2 right cases with a value); the one that clears the partial cases (margin 0.471) only restates the signal. `research/labels/diagnostics/item30/REPORT_part2.md:152@06d8550` `research/labels/diagnostics/item30/REPORT_part2.md:155@06d8550` `research/labels/diagnostics/item30/REPORT_part2.md:104@06d8550`
- The prediction that c3 does not separate the two groups held, with c3 = 1 in all 3 late cases and in 19860380 and 19870927. `research/labels/diagnostics/item30/PREDICTIONS_part2.md:5@06d8550` `research/labels/diagnostics/item30/REPORT_part2.md:94@06d8550`
- "The spare rule changes exactly 10 swell tracks": 15. Where E lies wholly before the boundary does not imply that the boundary is after the global minimum. `research/labels/diagnostics/item30/PREDICTIONS_part3.md:11@06d8550` `research/labels/diagnostics/item30/REPORT_part3.md:138@06d8550`

### Decisions

- `incipient_plateau_spare_intensification` pulls the boundary back to the start of an intensification block that lies wholly before it. `research/labels/diagnostics/item30/REPORT_part3.md:23@06d8550`
- The counterfactual boundary brings the three late cases closer to their labels and 19860380 and 19870927 further from theirs. `research/labels/diagnostics/item30/REPORT_figs_cf.md:18@06d8550` `research/labels/diagnostics/item30/REPORT_figs_cf.md:19@06d8550`
- On the 5 adjudicated cases params-15 scores 5/5 against 0/5 for params-14, circular by construction: their labels are the counterfactual. `research/labels/diagnostics/item30/REPORT_part3.md:63@06d8550` `research/labels/diagnostics/item30/REPORT_part3.md:65@06d8550`
- params-15 was adopted "without independent validation"; the 5 validation tracks were seen under params-15 before they were labelled. `research/labels/diagnostics/item30/REPORT_part3.md:225@06d8550` `research/labels/diagnostics/item30/REPORT_part3.md:208@06d8550`
- A "default unchanged" guard must exercise the branch that changed: the canonical digest ran the geometric incipient method at the time, so it could not guard the plateau rule. `research/labels/diagnostics/item30/REPORT_part3.md:172@06d8550`

### Open

- H and the spare rule's lack of independent validation: §S11.

## S08 — params-15 / params-track and the package defaults

### Confirmed causes

- params-15 against the pre-item-31 defaults: of 31 keys, 20 differ strictly, 19 by value, 17 in behaviour. `research/labels/diagnostics/item31/DESIGN.md:41@06d8550` `research/labels/diagnostics/item31/DESIGN.md:42@06d8550` `research/labels/diagnostics/item31/DESIGN.md:43@06d8550`
- `use_filter: true` in the preset is behaviour-equal to the default `'auto'`, apart from a `UserWarning`. `research/labels/diagnostics/item31/param_table.md:7@06d8550`
- The original split does not test `incipient_plateau_spare_intensification`: it changes nothing on its 47 training series and 5 of the 7 batch training series. `research/labels/diagnostics/item31/DESIGN.md:81@06d8550` `research/labels/diagnostics/item31/DESIGN.md:72@06d8550`
- Relative to the pre-item-31 defaults, item 31 changed the final map of 54/54 training series and the sequence of 32/54; for example 20150069 loses its incipient phase (end 7 → none). `CHANGELOG.md:62@06d8550` `research/labels/diagnostics/item31/train_sequences_2b.md:5@06d8550`
- Since stage 2c the app's sidebar opens with the package signature defaults (for example `cutoff_high` 18 instead of 48). `research/labels/diagnostics/item31/sidebar_table_2c.md:5@06d8550`

### Scores belong to params-track, not to the current default

- **Every measured score of params-track, on the training and on the test split, was measured under its own `boundary_padding="edge"`; none applies to the current default (`"reflect"`).** `CHANGELOG.md:30@a132f37` `CHANGELOG.md:32@a132f37`
- The earlier reference configurations measured by the fronts also carried edge (params-9 in Front B; params-11 and params-14 in item 30). `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:22@06d8550` `research/labels/diagnostics/item30/REPORT.md:33@06d8550`
- params-track is params-15 renamed, byte for byte. `research/cleanup/passo1/RELATORIO.md:10@33dc4e1`
- The current defaults differ from params-track in `boundary_padding` and `use_filter` only (plus the absent `prominence` key, whose default is `None`). `research/cleanup/passo1/RELATORIO.md:37@33dc4e1`

Regenerated at render time from `inspect.signature` and the YAML (working tree at HEAD `2a3080f`; the render aborts if the set of differing keys changes):

| key | params-track | package default |
|---|---|---|
| `filter_params.use_filter` | `True` | `'auto'` |
| `filter_params.boundary_padding` | `'edge'` | `'reflect'` |
| `phase_params.prominence` | (absent) | `None` |

### Stage 1 of item 31 (the single scoring run on the test split)

- Stage 1 passed on 16 test series with params-15, i.e. with `boundary_padding="edge"`: incipient hits 3/9 against 4/9 for the pre-item-31 defaults, refusals agreed 6/6 against 0/6. `docs/future_work.md:3861@06d8550` `docs/future_work.md:3862@06d8550`
- The PASS is weak evidence: the 16 series were part of the visual calibration set, were seen under params-15 when it was adopted, had test blocks displayed in the Benchmark, and are labelled by the same assessor. `docs/future_work.md:3875@06d8550` `research/labels/diagnostics/item31/DESIGN.md:316@06d8550`
- The incipient boundary is worse on the test split than on the training split: hits 3/9 against 8/17, false refusals 4/9 against 6/17. `docs/future_work.md:3883@06d8550` `docs/future_work.md:3884@06d8550` `docs/future_work.md:3885@06d8550`
- The test split is spent: stage 1 is single-shot, and no later choice may be scored on these 16 as if they were held out. `docs/future_work.md:3893@06d8550`
- The exposure of the test series is reconstructed as 23 events, each tied to a source line; E22 records all 16 test series viewed under params-15. `docs/future_work.md:3843@06d8550` `research/labels/diagnostics/item31/DESIGN.md:93@06d8550` `research/labels/diagnostics/item31/exposure_table.md:9@06d8550`
- The label-only census of the 16 test records, itself a declared exposure: 9 boundary, 6 none, 1 ambiguous. `research/labels/diagnostics/item31/test_label_census.txt:11@06d8550` `docs/future_work.md:3846@06d8550` `docs/future_work.md:3847@06d8550`

### Decisions

- `boundary_padding="reflect"` is the default by the maintainer's choice (2026-09-28), made without a detection-quality measurement. `CHANGELOG.md:100@a132f37`
- Against edge, C1 changes the final map of 19 of the 54 training series and the phase sequence of 3. `research/cleanup/passo1/RELATORIO.md:13@33dc4e1`

### Open

- Only the TRACK filtering was calibrated; the spare rule has no independent validation; no independent test split remains: §S11.

## S09 — Inert parameters in the calibration app

### Confirmed causes

- The sweep covered 46 (parameter, base configuration) pairs over all 51 tracks; its self-test flagged all 13 pairs of the 5 known inert cases. `research/inert_params/REPORT_inertia_sweep.md:14@06d8550` `research/inert_params/REPORT_inertia_sweep.md:10@06d8550` `research/inert_params/REPORT_inertia_sweep.md:25@06d8550`
- The prediction of the 5 known inert cases was declared before the sweep ran. `research/inert_params/PREDICTION.md:14@06d8550`
- `savgol_polynomial` is inert whenever `use_smoothing` alone is False (0/51 changed), not only when both passes are off (45/51 changed with only the second pass off). `research/inert_params/REPORT_inertia_sweep.md:65@06d8550` `research/inert_params/REPORT_inertia_sweep.md:68@06d8550`
- Under `incipient_plateau_signal="derivative"` the single and sustained crossings give the same map on all 51 tracks at 37 of the 56 (τ, k) grid points tested; under `"vorticity"` they differ on 42/51. `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md:26@06d8550` `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md:45@06d8550` `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md:20@06d8550`

### Decisions

- Inertia has three categories, not two: by design, data-dependent, unexplained; the unexplained backlog is empty. `research/inert_params/DATA_DEPENDENT_findings.md:27@06d8550` `research/inert_params/BACKLOG_inexplicada.md:10@06d8550`
- Parameters inert by design get a disabled control in the app (for example the three Lanczos parameters when `use_filter` is off). `research/inert_params/REPORT_inertia_sweep.md:49@06d8550`

### Open

- `process_vorticity(use_smoothing=False, use_smoothing_twice="auto")` raises `ValueError`; it was a one-click crash from the app's then-default state, recorded and not fixed, and the raise is still in the package at `06d8550`. `research/inert_params/INCIDENTAL_crash_bug.md:23@06d8550` `cyclophaser/determine_periods.py:709@06d8550`

## S10 — Traceability

- 40 closed-front scripts stopped running when params-1 to params-14 left the configs directory; they are listed, not migrated, and reproduce from commit `33ea489358d9`. `docs/future_work.md:3922@06d8550` `research/labels/diagnostics/item31/stale_scripts.md:1@06d8550`
- Every file below leaves the tree after approval and stays readable with `git show 06d8550:<path>`. The "finding recorded at" column cites where its finding is written; the destination is a section of this document or a line of `docs/future_work.md`, never a file that leaves.
- Files that leave without a finding of their own (scripts, and generated outputs whose front report is consolidated here) are not repeated below; they are listed in `research/cleanup/MANIFEST.md`.

| file that leaves | manifest destination | finding recorded at (source) | destination |
|---|---|---|---|
| `docs/_images/item5/*.png` | remove | `docs/future_work.md:2004@06d8550` | `docs/future_work.md:2004@06d8550` |
| `research/incipient_plateau/REPORT_incipient_characterisation.md` | consolidate | the report itself (`research/incipient_plateau/REPORT_incipient_characterisation.md:1@06d8550`) | §S02 |
| `research/incipient_plateau/REPORT_incipient_smoothing.md` | consolidate | the report itself (`research/incipient_plateau/REPORT_incipient_smoothing.md:1@06d8550`) | §S02 |
| `research/incipient_plateau/gen_geometric_vs_plateau.py` | remove | only in this file: reproduced in §S02 | §S02 |
| `research/incipient_plateau/geometric_vs_plateau.csv` | remove | only in this file: reproduced in §S02 | §S02 |
| `research/incipient_plateau/incipient_measurements.csv` | remove | `research/incipient_plateau/REPORT_incipient_characterisation.md:57@06d8550` | §S02 |
| `research/incipient_plateau/incipient_smoothing_real_rel0.csv` | remove | `research/incipient_plateau/REPORT_incipient_smoothing.md:118@06d8550` | §S02 |
| `research/incipient_plateau/incipient_smoothing_sweep.csv` | remove | `research/incipient_plateau/REPORT_incipient_smoothing.md:96@06d8550` | §S02 |
| `research/incipient_plateau/incipient_smoothing_tables.txt` | remove | `research/incipient_plateau/REPORT_incipient_smoothing.md:157@06d8550` | §S02 |
| `research/incipient_plateau/summary_tables.txt` | remove | `research/incipient_plateau/REPORT_incipient_characterisation.md:302@06d8550` | §S02 |
| `research/inert_params/BACKLOG_inexplicada.md` | consolidate | the report itself (`research/inert_params/BACKLOG_inexplicada.md:1@06d8550`) | §S09 |
| `research/inert_params/DATA_DEPENDENT_findings.md` | consolidate | the report itself (`research/inert_params/DATA_DEPENDENT_findings.md:1@06d8550`) | §S09 |
| `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md` | consolidate | the report itself (`research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md:1@06d8550`) | §S09 |
| `research/inert_params/INCIDENTAL_crash_bug.md` | consolidate | the report itself (`research/inert_params/INCIDENTAL_crash_bug.md:1@06d8550`) | §S09 |
| `research/inert_params/PREDICTION.md` | consolidate | the report itself (`research/inert_params/PREDICTION.md:1@06d8550`) | §S09 |
| `research/inert_params/REPORT_inertia_sweep.md` | consolidate | the report itself (`research/inert_params/REPORT_inertia_sweep.md:1@06d8550`) | §S09 |
| `research/inert_params/inertia_matrix.csv` | remove | `research/inert_params/REPORT_inertia_sweep.md:36@06d8550` | §S09 |
| `research/inert_params/inertia_matrix_full.csv` | remove | `docs/future_work.md:756@06d8550` | §S09; `docs/future_work.md:756@06d8550` |
| `research/inert_params/sweep_derived_summary.txt` | remove | `research/inert_params/REPORT_inertia_sweep.md:87@06d8550` | §S09 |
| `research/inert_params/sweep_summary.txt` | remove | `research/inert_params/REPORT_inertia_sweep.md:26@06d8550` | §S09 |
| `research/labels/diagnostics/frontA_idx0_c2/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/frontA_idx0_c2/REPORT.md:1@06d8550`) | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_blocks.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_boundaries.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fig_20190639_c2.png` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:66@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.json` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_off.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.json` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_cur_on.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.json` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550`; `docs/future_work.md:3108@06d8550` | §S03; `docs/future_work.md:3108@06d8550` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/fp_ref_c714451.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m1_m2_census.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:114@06d8550`; `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:156@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2_c2_table.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:156@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:261@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m2b_peak_to_valley.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:261@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m3_force_peak.png` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:220@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_H.png` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m4_20180608_head.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:278@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:314@06d8550`; `docs/future_work.md:3048@06d8550` | §S03; `docs/future_work.md:3048@06d8550` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/m5_boundary_independence.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:314@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_changed_series.png` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.csv` | remove | `docs/future_work.md:3131@06d8550` | §S03; `docs/future_work.md:3131@06d8550` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_defaults_check.log` | remove | `docs/future_work.md:3131@06d8550` | §S03; `docs/future_work.md:3131@06d8550` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_gate.log` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:429@06d8550`; `docs/future_work.md:3083@06d8550` | §S03; `docs/future_work.md:3083@06d8550` |
| `research/labels/diagnostics/frontA_idx0_c2/outputs/stage2_table.csv` | remove | `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:467@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/frontA_reverify/REPORT.md:1@06d8550`) | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_final_output_check.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_build_idx0_inventory.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_capture_pipeline_state.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_eval_raw.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/1a_gate.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550`; `docs/future_work.md:2799@06d8550` | §S03; `docs/future_work.md:2799@06d8550` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_census.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:179@06d8550`; `docs/future_work.md:2817@06d8550` | §S03; `docs/future_work.md:2817@06d8550` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_diff_vs_A.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:195@06d8550`; `docs/future_work.md:2817@06d8550` | §S03; `docs/future_work.md:2817@06d8550` |
| `research/labels/diagnostics/frontA_reverify/outputs/1b_eval_params9.log` | remove | `docs/future_work.md:2827@06d8550` | §S03; `docs/future_work.md:2827@06d8550` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_attribution.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:239@06d8550`; `docs/future_work.md:2837@06d8550` | §S03; `docs/future_work.md:2837@06d8550` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_census.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:213@06d8550`; `docs/future_work.md:2817@06d8550` | §S03; `docs/future_work.md:2817@06d8550` |
| `research/labels/diagnostics/frontA_reverify/outputs/2_diff_vs_A.log` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:220@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_final_output_check.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_fix_eval_before.txt` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0_final_stage.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0_inventory.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1a_regen_idx0b_prominence.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:135@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_V_table.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:179@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0_final_stage.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:179@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0_inventory.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:179@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step1b_params9_idx0b_prominence.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:179@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_attribution.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:239@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_V_table.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:213@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0_final_stage.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:213@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0_inventory.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:213@06d8550` | §S03 |
| `research/labels/diagnostics/frontA_reverify/outputs/step2_params13_idx0b_prominence.csv` | remove | `research/labels/diagnostics/frontA_reverify/REPORT.md:213@06d8550` | §S03 |
| `research/labels/diagnostics/frontC/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/frontC/REPORT.md:1@06d8550`) | §S05 |
| `research/labels/diagnostics/frontC/d2_segments.csv` | remove | `research/labels/diagnostics/frontC/REPORT.md:41@06d8550`; `docs/future_work.md:2366@06d8550` | §S05; `docs/future_work.md:2366@06d8550` |
| `research/labels/diagnostics/frontC/d2_segments.json` | remove | `docs/future_work.md:2366@06d8550` | §S05; `docs/future_work.md:2366@06d8550` |
| `research/labels/diagnostics/frontC/fig_20180654_before_after.png` | remove | `research/labels/diagnostics/frontC/REPORT.md:41@06d8550` | §S05 |
| `research/labels/diagnostics/frontC/fig_20180733_before_after.png` | remove | `research/labels/diagnostics/frontC/REPORT.md:41@06d8550` | §S05 |
| `research/labels/diagnostics/frontC/measurements.json` | remove | `research/labels/diagnostics/frontC/REPORT.md:41@06d8550`; `docs/future_work.md:2334@06d8550` | §S05; `docs/future_work.md:2334@06d8550` |
| `research/labels/diagnostics/frontD/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/frontD/REPORT.md:1@06d8550`) | §S02 |
| `research/labels/diagnostics/frontD/anchoring.json` | remove | `research/labels/diagnostics/frontD/REPORT.md:158@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/anchoring.txt` | remove | `research/labels/diagnostics/frontD/REPORT.md:158@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/census.json` | remove | `research/labels/diagnostics/frontD/REPORT.md:61@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/census.txt` | remove | `research/labels/diagnostics/frontD/REPORT.md:61@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/constant_baseline.json` | remove | `research/labels/diagnostics/frontD/REPORT.md:308@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/constant_baseline.txt` | remove | `research/labels/diagnostics/frontD/REPORT.md:308@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/evaluate_params13_train.txt` | remove | `research/labels/diagnostics/frontD/REPORT.md:243@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/fig_*_opening.png` | remove | `research/labels/diagnostics/frontD/REPORT.md:361@06d8550` | §S02 |
| `research/labels/diagnostics/frontD/verify_hashes.txt` | remove | `research/labels/diagnostics/frontD/REPORT.md:29@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/frontRefusal/REPORT.md:1@06d8550`) | §S02 |
| `research/labels/diagnostics/frontRefusal/classification.json` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:170@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/classification.txt` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:170@06d8550`; `docs/future_work.md:672@06d8550` | §S02; `docs/future_work.md:672@06d8550` |
| `research/labels/diagnostics/frontRefusal/evaluate_params13_train.txt` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:46@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/fig_*_refusal.png` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:155@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/refusal.json` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:67@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/refusal.txt` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:102@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/separability.json` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:201@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/separability.txt` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:201@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/tau_sweep.json` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:334@06d8550` | §S02 |
| `research/labels/diagnostics/frontRefusal/tau_sweep.txt` | remove | `research/labels/diagnostics/frontRefusal/REPORT.md:334@06d8550` | §S02 |
| `research/labels/diagnostics/front_b/ADDENDUM_part1b.md` | consolidate | the report itself (`research/labels/diagnostics/front_b/ADDENDUM_part1b.md:1@06d8550`) | §S06 |
| `research/labels/diagnostics/front_b/REPORT_front_b_part1.md` | consolidate | the report itself (`research/labels/diagnostics/front_b/REPORT_front_b_part1.md:1@06d8550`) | §S06 |
| `research/labels/diagnostics/front_b/distance_sweep.txt` | remove | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:33@06d8550`; `docs/future_work.md:1564@06d8550` | §S06; `docs/future_work.md:1564@06d8550` |
| `research/labels/diagnostics/front_b/headroom_and_hash.txt` | remove | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:267@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/mature_pairing_audit.txt` | remove | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:86@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/reference_score_attribution.txt` | remove | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:149@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/sensitivity.txt` | remove | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:223@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/sweep_distance.py` | remove | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:68@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/target_tracks.txt` | remove | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:100@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/topology_run_gate_excerpt.txt` | remove | `research/labels/diagnostics/front_b/ADDENDUM_part1b.md:149@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/train_aggregate.txt` | remove | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:193@06d8550` | §S06 |
| `research/labels/diagnostics/front_b/train_raw.json` | remove | `research/labels/diagnostics/front_b/REPORT_front_b_part1.md:193@06d8550` | §S06 |
| `research/labels/diagnostics/item19/PROVENANCE.md` | consolidate | the report itself (`research/labels/diagnostics/item19/PROVENANCE.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item19/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/item19/REPORT.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item19/closeout_measurements.txt` | remove | `research/labels/diagnostics/item19/REPORT.md:405@06d8550` | §S04 |
| `research/labels/diagnostics/item19/evaluate_params10_train.txt` | remove | `research/labels/diagnostics/item19/REPORT.md:45@06d8550` | §S04 |
| `research/labels/diagnostics/item19/fig_20160735_params10.png` | remove | `research/labels/diagnostics/item19/REPORT.md:41@06d8550` | §S04 |
| `research/labels/diagnostics/item19/fig_prominence_distributions.png` | remove | `research/labels/diagnostics/item19/REPORT.md:92@06d8550` | §S04 |
| `research/labels/diagnostics/item19/fig_tradeoff_pr060_maf090.png` | remove | `research/labels/diagnostics/item19/REPORT.md:207@06d8550` | §S04 |
| `research/labels/diagnostics/item19/stage1_baseline.txt` | remove | `research/labels/diagnostics/item19/REPORT.md:76@06d8550` | §S04 |
| `research/labels/diagnostics/item19/stage1_per_series.md` | consolidate | the report itself (`research/labels/diagnostics/item19/stage1_per_series.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item19/stage1_prominence.md` | consolidate | the report itself (`research/labels/diagnostics/item19/stage1_prominence.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item19/stage2_cells.json` | remove | `research/labels/diagnostics/item19/REPORT.md:143@06d8550`; `docs/future_work.md:1731@06d8550` | §S04; `docs/future_work.md:1731@06d8550` |
| `research/labels/diagnostics/item19/stage2_grid.md` | consolidate | the report itself (`research/labels/diagnostics/item19/stage2_grid.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item19/stage2_losses.md` | consolidate | the report itself (`research/labels/diagnostics/item19/stage2_losses.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md` | consolidate | the report itself (`research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item20a/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/item20a/REPORT.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item20a/evaluate_params10_train.txt` | remove | `research/labels/diagnostics/item20a/REPORT.md:38@06d8550` | §S04 |
| `research/labels/diagnostics/item20a/evaluate_params11_train.txt` | remove | `research/labels/diagnostics/item20a/REPORT.md:52@06d8550` | §S04 |
| `research/labels/diagnostics/item20a/measurements.json` | remove | `research/labels/diagnostics/item20a/REPORT.md:107@06d8550` | §S04 |
| `research/labels/diagnostics/item20a/tables.md` | consolidate | the report itself (`research/labels/diagnostics/item20a/tables.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item20b/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/item20b/REPORT.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item20b/REPORT_stage2.md` | consolidate | the report itself (`research/labels/diagnostics/item20b/REPORT_stage2.md:1@06d8550`) | §S04 |
| `research/labels/diagnostics/item20b/analyse_20b.txt` | remove | `research/labels/diagnostics/item20b/REPORT.md:145@06d8550`; `docs/future_work.md:2146@06d8550` | §S04; `docs/future_work.md:2146@06d8550` |
| `research/labels/diagnostics/item20b/defectH_watch.txt` | remove | `research/labels/diagnostics/item20b/REPORT_stage2.md:227@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/denominator_robustness.txt` | remove | `research/labels/diagnostics/item20b/REPORT_stage2.md:250@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/depth_table.csv` | remove | `research/labels/diagnostics/item20b/REPORT.md:145@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/fig_20160735_before_after.png` | remove | `research/labels/diagnostics/item20b/REPORT_stage2.md:114@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/fig_20205386_before_after.png` | remove | `research/labels/diagnostics/item20b/REPORT_stage2.md:112@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/gate_stage2.txt` | remove | `research/labels/diagnostics/item20b/REPORT_stage2.md:191@06d8550`; `docs/future_work.md:2191@06d8550` | §S04; `docs/future_work.md:2191@06d8550` |
| `research/labels/diagnostics/item20b/measurements.json` | remove | `research/labels/diagnostics/item20b/REPORT.md:49@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/stage2_measurements.json` | remove | `research/labels/diagnostics/item20b/REPORT_stage2.md:191@06d8550` | §S04 |
| `research/labels/diagnostics/item20b/supplement_20b.txt` | remove | `research/labels/diagnostics/item20b/REPORT.md:96@06d8550` | §S04 |
| `research/labels/diagnostics/item30/PREDICTIONS.md` | consolidate | the report itself (`research/labels/diagnostics/item30/PREDICTIONS.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/PREDICTIONS_part2.md` | consolidate | the report itself (`research/labels/diagnostics/item30/PREDICTIONS_part2.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/PREDICTIONS_part3.md` | consolidate | the report itself (`research/labels/diagnostics/item30/PREDICTIONS_part3.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/REPORT.md` | consolidate | the report itself (`research/labels/diagnostics/item30/REPORT.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/REPORT_figs_cf.md` | consolidate | the report itself (`research/labels/diagnostics/item30/REPORT_figs_cf.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/REPORT_part2.md` | consolidate | the report itself (`research/labels/diagnostics/item30/REPORT_part2.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/REPORT_part3.md` | consolidate | the report itself (`research/labels/diagnostics/item30/REPORT_part3.md:1@06d8550`) | §S07 |
| `research/labels/diagnostics/item30/census_train_params14.csv` | remove | `research/labels/diagnostics/item30/REPORT.md:184@06d8550` | §S07 |
| `research/labels/diagnostics/item30/evaluate_params14_train_batch.txt` | remove | `research/labels/diagnostics/item30/REPORT.md:118@06d8550` | §S07 |
| `research/labels/diagnostics/item30/figs_cf/*.png` | remove | `research/labels/diagnostics/item30/REPORT_figs_cf.md:3@06d8550`; `docs/future_work.md:3504@06d8550` | §S07; `docs/future_work.md:3504@06d8550` |
| `research/labels/diagnostics/item30/figs_cf_output.txt` | remove | `research/labels/diagnostics/item30/REPORT_figs_cf.md:1@06d8550` | §S07 |
| `research/labels/diagnostics/item30/figs_part3/*.png` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:123@06d8550` | §S07 |
| `research/labels/diagnostics/item30/outside_signal.py` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:45@06d8550` | §S07 |
| `research/labels/diagnostics/item30/outside_signal_output.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:130@06d8550` | §S07 |
| `research/labels/diagnostics/item30/part3_eval_params14.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:57@06d8550` | §S07 |
| `research/labels/diagnostics/item30/part3_eval_params15.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:57@06d8550` | §S07 |
| `research/labels/diagnostics/item30/part3_measure_output.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:29@06d8550` | §S07 |
| `research/labels/diagnostics/item30/post_merge_checks_output.txt` | remove | `docs/future_work.md:3619@06d8550` | §S07; `docs/future_work.md:3619@06d8550` |
| `research/labels/diagnostics/item30/prove_defaults_30c.txt` | remove | `docs/future_work.md:3800@06d8550` | §S07; `docs/future_work.md:3800@06d8550` |
| `research/labels/diagnostics/item30/prove_defaults_part3_checkpoint.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:191@06d8550` | §S07 |
| `research/labels/diagnostics/item30/prove_defaults_part3_step2.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:125@06d8550` | §S07 |
| `research/labels/diagnostics/item30/prove_defaults_part3_step3.txt` | remove | `research/labels/diagnostics/item30/REPORT_part3.md:42@06d8550` | §S07 |
| `research/labels/diagnostics/item30/separability_criterion.json` | remove | `research/labels/diagnostics/item30/REPORT_part2.md:15@06d8550` | §S07 |
| `research/labels/diagnostics/item30/separability_train_output.txt` | remove | `research/labels/diagnostics/item30/REPORT_part2.md:77@06d8550` | §S07 |
| `research/labels/diagnostics/item30/separability_train_params14.csv` | remove | `research/labels/diagnostics/item30/REPORT_part2.md:77@06d8550` | §S07 |
| `research/labels/diagnostics/item31/DESIGN.md` | consolidate | the report itself (`research/labels/diagnostics/item31/DESIGN.md:1@06d8550`) | §S08 |
| `research/labels/diagnostics/item31/benchmark_swap_mutation.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:756@06d8550` | §S08 |
| `research/labels/diagnostics/item31/benchmark_swap_mutation_2c.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:923@06d8550` | §S08 |
| `research/labels/diagnostics/item31/constant_train.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:170@06d8550` | §S08 |
| `research/labels/diagnostics/item31/constant_train.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:170@06d8550` | §S08 |
| `research/labels/diagnostics/item31/exposure_table.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:88@06d8550` | §S08 |
| `research/labels/diagnostics/item31/exposure_table.md` | consolidate | the report itself (`research/labels/diagnostics/item31/exposure_table.md:1@06d8550`) | §S08 |
| `research/labels/diagnostics/item31/fix_use_filter_false_after.json` | remove | `CHANGELOG.md:107@06d8550` | §S08 |
| `research/labels/diagnostics/item31/fix_use_filter_false_before.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:865@06d8550` | §S08 |
| `research/labels/diagnostics/item31/fix_use_filter_false_equivalence.py` | remove | `CHANGELOG.md:107@06d8550` | §S08 |
| `research/labels/diagnostics/item31/fix_use_filter_false_equivalence.txt` | remove | `CHANGELOG.md:118@06d8550` | §S08 |
| `research/labels/diagnostics/item31/footprint_train.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:442@06d8550` | §S08 |
| `research/labels/diagnostics/item31/footprint_train.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:442@06d8550` | §S08 |
| `research/labels/diagnostics/item31/future_work_numbers.json` | remove | `docs/future_work.md:3823@06d8550` | §S08; `docs/future_work.md:3823@06d8550` |
| `research/labels/diagnostics/item31/gate_2a.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:595@06d8550` | §S08 |
| `research/labels/diagnostics/item31/gate_2b.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:756@06d8550` | §S08 |
| `research/labels/diagnostics/item31/gate_2b.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:756@06d8550` | §S08 |
| `research/labels/diagnostics/item31/p15_expected_digest.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:375@06d8550` | §S08 |
| `research/labels/diagnostics/item31/param_table.md` | consolidate | the report itself (`research/labels/diagnostics/item31/param_table.md:1@06d8550`) | §S08 |
| `research/labels/diagnostics/item31/reachability_train.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:62@06d8550` | §S08 |
| `research/labels/diagnostics/item31/reachability_train.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:62@06d8550` | §S08 |
| `research/labels/diagnostics/item31/sidebar_table_2c.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:923@06d8550` | §S08 |
| `research/labels/diagnostics/item31/sidebar_table_2c.md` | consolidate | the report itself (`research/labels/diagnostics/item31/sidebar_table_2c.md:1@06d8550`) | §S08 |
| `research/labels/diagnostics/item31/stage1_output.json` | remove | `docs/future_work.md:3854@06d8550` | §S08; `docs/future_work.md:3854@06d8550` |
| `research/labels/diagnostics/item31/stage1_output.txt` | remove | `docs/future_work.md:3854@06d8550` | §S08; `docs/future_work.md:3854@06d8550` |
| `research/labels/diagnostics/item31/stage1_smoke_train.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:547@06d8550` | §S08 |
| `research/labels/diagnostics/item31/stale_scripts.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:595@06d8550` | §S08 |
| `research/labels/diagnostics/item31/stale_scripts.md` | consolidate | the report itself (`research/labels/diagnostics/item31/stale_scripts.md:1@06d8550`) | §S10 |
| `research/labels/diagnostics/item31/suite_2a.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:595@06d8550` | §S08 |
| `research/labels/diagnostics/item31/suite_2b_final.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:756@06d8550` | §S08 |
| `research/labels/diagnostics/item31/suite_2b_measure.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:815@06d8550` | §S08 |
| `research/labels/diagnostics/item31/suite_2b_prefix.txt` | remove | `research/labels/diagnostics/item31/DESIGN.md:756@06d8550` | §S08 |
| `research/labels/diagnostics/item31/suite_2c.txt` | remove | `docs/future_work.md:3983@06d8550` | §S08; `docs/future_work.md:3983@06d8550` |
| `research/labels/diagnostics/item31/test_label_census.json` | remove | `research/labels/diagnostics/item31/DESIGN.md:124@06d8550` | §S08 |
| `research/labels/diagnostics/item31/test_label_census.txt` | consolidate | the report itself (`research/labels/diagnostics/item31/test_label_census.txt:1@06d8550`) | §S08 |
| `research/labels/diagnostics/item31/train_sequences_2b.md` | consolidate | the report itself (`research/labels/diagnostics/item31/train_sequences_2b.md:1@06d8550`) | §S08 |

## S11 — Open items (recorded, not resolved)

- **Defect H.** The incipient overwrite of `[0, boundary)` is unconditional; redescribed as a property of the overwrite, so the open question is the boundary, not the overwrite. `docs/future_work.md:3474@06d8550` `docs/future_work.md:3483@06d8550`
- **Late mature start (item 17(e)).** All 13 labelled synthetic mature boundaries start after the label, by +1 to +6 steps. `docs/future_work.md:1459@06d8550` `docs/future_work.md:1460@06d8550`
- **Spare rule without independent validation.** `incipient_plateau_spare_intensification=True`, which pulls the incipient boundary back, is a default "adopted without independent validation"; the validation batch and the test split are spent. `docs/future_work.md:4006@06d8550` `docs/future_work.md:4008@06d8550`
- **Only the TRACK filtering was calibrated** (hourly 850 hPa vorticity along tracks); other inputs may need another filtering. `docs/future_work.md:4009@06d8550`
- **`decay_tail_amplitude_fraction` needs recalibration.** Its documented calibration was made on a pre-correction configuration and does not reproduce; it is inert on the two series tested under params-12. `docs/future_work.md:2310@06d8550` `docs/future_work.md:2318@06d8550`
- **Stopped window of item 20(c).** A cost-free duration floor `r ∈ (0.5333, 0.6667]` is on hold; reopening needs a new front with its premise redeclared. `docs/future_work.md:2286@e7792d3` `docs/future_work.md:2307@e7792d3`
- **Incipient refusal.** Reopening requires a new front with a declared premise for why a parameter would separate the four genuine-disagreement series from the agreed-none ones; never a search over values. `research/labels/diagnostics/frontRefusal/REPORT.md:380@06d8550`
- **Synthetic generator non-determinism.** Its root cause across environments is unknown; labels are protected only because the series are frozen to files. `docs/future_work.md:1259@06d8550`
- **Frozen series in CSV.** The exact round-trip depends on a load-bearing float-format pairing; a binary format would remove that hazard. `docs/future_work.md:1272@06d8550`
- **CI coverage gap.** CI exercises none of the streamlit/plotly code paths of the calibration app, by design. `docs/future_work.md:1283@06d8550`
- **Label exposure.** The test series were exposed in 23 recorded events before stage 1 scored them. `docs/future_work.md:3843@06d8550`
- **No independent test split.** The test split is spent; any later choice needs newly labelled series. `docs/future_work.md:3892@06d8550`
- **Training re-labels outside develop.** Three re-labels made on `feat/label-tab-toplevel` never reached develop: 20150656 residual 91 → 100, 20170409 decay 74 → 71, 20170154 boundary (incipient end 6) → ambiguous (regenerated by `research/cleanup/passo0/relabel_diff.py` against `0c63145`). `research/cleanup/MANIFEST.md:1820@d8a19cc` `research/cleanup/MANIFEST.md:1822@d8a19cc` `research/cleanup/MANIFEST.md:1821@d8a19cc`
- **Published app against the published package.** The calibration app installs cyclophaser from PyPI (`>=2.0.0`), whose latest release predates the parameters the app reads; this is an input to the release front. `tools/calibration_app/requirements.txt:20@06d8550` `research/cleanup/MANIFEST.md:1763@f17d802` `research/cleanup/MANIFEST.md:1765@f17d802` `research/cleanup/MANIFEST.md:1760@d8a19cc`
- **The canonical digest generator reads test CSVs from disk.** Its docstring says the 16 test ids are not read, but it loads all real CSVs and filters to training afterwards (debt for a later clean-up step). `research/labels/diagnostics/front_b/default_behaviour_hash.py:15@06d8550` `research/labels/diagnostics/front_b/default_behaviour_hash.py:94@06d8550` `research/labels/labels_core.py:189@06d8550`

## S12 — Record corrections

- **C1's premise against what was measured.** When C1 was decided two consequences were expected, no incipient refusals under reflect and defect I leaving the default path; the prediction declared before measuring was 0 refusals on the training series. `CHANGELOG.md:101@a132f37` `research/cleanup/passo1/PREVISOES.md:12@d8a19cc`
- Measured: 28/54 refusals under reflect and 28/54 under edge, the same series; defect I on 11 of 54 under reflect against 10 under edge, so it stays on the default path. `research/cleanup/passo1/RELATORIO.md:12@33dc4e1` `research/cleanup/passo1/RELATORIO.md:25@33dc4e1`
- Mechanism: the default `incipient_plateau_signal="vorticity"` measures the plateau on the unfiltered input, which the padding never touches; under `"derivative"` the padding decides (2/54 refusals under reflect against 32/54 under edge, post-hoc). `cyclophaser/find_stages.py:961@06d8550` `research/cleanup/passo1/RELATORIO.md:31@33dc4e1`
- The app's help text states the contrast (0/51 refusals under reflect, 33/51 under edge) without naming the incipient signal; the post-hoc check reproduces a contrast of that kind only under `"derivative"`. `tools/calibration_app/app.py:1604@06d8550`
- **The "2.0.0" label.** `research/labels/defaults_2.0.0.json`, the `*_2_0_0` baselines and the "2.0.0" columns of item 31 describe develop before item 31, not the published release: the release has no `boundary_padding` (it always zero-pads) and uses `replace_endpoints_with_lowpass=24`. `research/labels/defaults_2.0.0.json:4@06d8550` `CHANGELOG.md:42@a132f37` `CHANGELOG.md:46@a132f37`
- For example, the stage-1 row labelled "defaults 2.0.0" is the pre-item-31 table passed explicitly. `docs/future_work.md:3862@06d8550`
- **C2′'s "no change under package defaults" (0 of 64 series).** That was measured when `prominence` and `prominence_relative` were both None; since item 31 the default `prominence_relative` is 0.3, so the scope no longer holds. `research/labels/diagnostics/frontA_idx0_c2/REPORT.md:512@06d8550` `CHANGELOG.md:59@a132f37`
- **Two instruments for "correct mature".** `evaluate_against_labels.py` (`labels_core.score_phase_sequences`) scores a series only on an exact whole-sequence match, compares phase starts only, and uses each label's own tolerance, so on 47 series its ceiling for mature was 30 when a gate asked for 38/47. `research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md:51@06d8550` `research/labels/diagnostics/item20a/BLOCKER_pairing_rule.md:48@06d8550`
- `item19_core.pair_by_overlap` scores every series: it pairs the first labelled mature with the detected block of largest overlap and requires both ends within a fixed margin of 6. `research/labels/diagnostics/item19/item19_core.py:44@06d8550` `research/labels/diagnostics/item20a/REPORT.md:92@06d8550`
- Which governs what: phase-sequence claims use the evaluator; mature-window gates (items 20, 20(a), 20(b) and Front C) used `pair_by_overlap`; the Benchmark reports both, named. The three local copies of `pair_by_overlap` leave with their diagnostics. `research/labels/diagnostics/item20a/REPORT.md:15@06d8550` `research/labels/diagnostics/frontC/REPORT.md:125@06d8550` `tools/calibration_app/benchmark_core.py:95@06d8550`
- **A summary that its own table contradicts.** The inert-parameter finding says every (τ, k) point with k ≤ 10 shows zero divergence between the two crossings, but its table has 1 diverging track at τ 0.50, k 10; the count of 37 zero-divergence points out of 56 is right. `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md:45@06d8550` `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md:36@06d8550`
- **Item 18 and item 23 exist only on unmerged branches.** `docs/future_work.md` on develop goes from item 17 to item 19 and from item 22 to item 24; their findings are in §S02 (item 18) and §S04 (item 23), cited at `c508730` and `e7792d3`. `docs/future_work.md:1347@06d8550` `docs/future_work.md:1564@06d8550` `docs/future_work.md:2140@06d8550` `docs/future_work.md:2334@06d8550`
