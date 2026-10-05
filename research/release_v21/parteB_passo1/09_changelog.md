# 9. CHANGELOG — `[Unreleased]` and the gaps (develop-v2.1 `76b7932`)

`[Unreleased]` spans `CHANGELOG.md:10-821` (~810 lines). Below it come `[2.0.0] - 2026-06-14`
(`:822`) and `[1.9.4]` (`:941`). The compare links at `:945-946` cover `[2.0.0]` and
`[1.9.4]` only. There is **no `[Unreleased]` link**.

## What `[Unreleased]` holds

Newer blocks are at the top. From `:283` down, the headings carry no date or front name;
they are the blocks of earlier fronts, kept as they were written. The "introduced by"
column is the first first-parent commit in `v2.0.0..develop-v2.1` whose CHANGELOG diff adds
the block's opening text (`git log -S`). Headings `:12`–`:271` name their own front.

| line | heading → bold entries | introduced by |
|---|---|---|
| 12 | Changed — default behaviour: defaults are `params-track` except `boundary_padding="reflect"`. Includes the parameter tables vs 2.0.0 at `:40`/`:54`. | item 31 `0a469eb`, then C1 in clean-up `0d75db3` |
| 151 | Changed — documentation site rewritten for package users | `0d75db3` |
| 166 | Fixed — calibration app: switched-off checks exported as null | `0d75db3` |
| 175 | Changed — repository clean-up: research diagnostics archived (`runtime.txt`/`.python-version` removal at `:186`) | `0d75db3` |
| 188 | Changed — calibration app: the sidebar opens with the package defaults | item 31 (stage 2c) |
| 216 | Fixed — `process_vorticity(use_filter=False)` on an unnamed index | item 31 (`a1784b5`) |
| 229 | Changed — research tooling: incomplete configs and the configs directory | item 31 (`eed8e77`) |
| 245 | Added — calibration app: flexible track reading | item 29 `84b63ec` |
| 271 | Fixed — calibration app: no `use_filter=True` warning per cyclone | item 29 `84b63ec` |
| 283 | Changed — default behaviour → `reclassify_index0` (`:285`) | item 28 `e1dc17f` |
| 357 | Added → `intensification_min_depth` (`:359`) and `mature_min_depth` (`:417`) | front C `7a87a10` (the parameter `mature_min_depth` itself came with 20(b) `17dc21f`) |
| 451 | Removed — `distance` (with the note that `length_scale` stays) | front B `5120856` |
| 501 | Changed (tests only) — synthetic timing test scored against manual labels | front G `ff82f85` |
| 508 | Added → `incipient_method="plateau"` (`:510`), which covers `incipient_plateau_tau/_signal/_crossing/_k`, plus "Load synthetic cases" in the app | `1d7a9a0` |
| 564 | Added → `incipient_smooth_window` / `incipient_smooth_polyorder` (`:566`) | `1d7a9a0` |
| 603 | Evaluated and rejected → `incipient_method="amplitude"` (`:605`) | `1d7a9a0` |
| 628 | Changed → `use_smoothing=False` also disables the derivative smoothing (`:630`); two filtering defaults moved together (`:676`); `boundary_padding` defaults to `"reflect"` (`:699`) | `01c4492` (block); `4e70d17` (`:676`, `:699`) |
| 728 | Deprecated → `replace_endpoints_with_lowpass` (`:730`) | `4e70d17` |
| 744 | Fixed → `use_filter=True` silently disabled the Lanczos filter (`:746`) | `4a1ebdb` |
| 771 | Added → `boundary_padding` opt-in (`:773`) | `4a1ebdb` |
| 809 | Notes → new validated calibration with the Lanczos filter active (`:811`) | (with `b5441aa`) |

## Gaps — changes merged in develop-v2.1 since the last release with no entry

Method:
* Classified all 61 first-parent commits `v2.0.0..develop-v2.1` by the surfaces their diff
  touches.
* Compared the signatures of the three public functions between `v2.0.0` and
  `develop-v2.1` with `ast`. This found 18 new parameters, all in `determine_periods`;
  `get_periods` has 17 of them and `process_vorticity` has `boundary_padding`. No parameter
  was removed relative to 2.0.0, because `distance` was added and removed after it.
* For each new parameter and each user-facing change, looked for the CHANGELOG heading and
  bold entry that govern its mentions.

**Package: new public parameters with no entry of their own.** These appear only in the
defaults table of `:12` or in passing inside other entries.

| parameter | mentions in `[Unreleased]` | introduced by |
|---|---|---|
| `prominence`, `prominence_relative` | table (`:58-59`) plus mentions inside the `:166`, `:283`, `:357` and `:451` blocks | `9e44c48` (`feat/extrema-prominence-distance`) |
| `length_scale`, `mature_method`, `mature_amplitude_fraction`, `decay_tail_amplitude_fraction` | table (`:61-63`) plus mentions inside other blocks; `mature_amplitude_fraction` appears only in the table | `7d489ab` (`research/adaptive-thresholds`) |
| `incipient_plateau_spare_intensification` | table only (`:74`) | item 30 `5434d87` |

**Calibration app (`tools/calibration_app/`): user-visible changes with no entry**

* **Layer Inspector**, `fba17e5`: 0 mentions.
* **Label tab / manual labelling**, `887c628`; navigation and overlays in `8102334` (item 16).
  Only incidental mentions of "manual label".
* **Benchmark tab**, item 5, `e579518`. It is mentioned in passing (`:95`, `:208`, `:212`, `:261`, `:268`),
  but there is no "Added" entry.
* **Inspector depth parameters**, item 30a, `ad8daca`: 0 mentions.
* **Inspector crossing layer and legend fix**, `1f38611`: no entry. The 4 hits for
  "crossing" are `incipient_plateau_crossing`.
* **Inert-parameter signalling**, `f837052` and `402d3f7`: no entry. The 2 hits for "inert"
  are about extremum inertia.

**Build, CI, distribution**

* **After the tag `v2.0.0` (`5d99ae3`).**
  * Commits: `f0c0661` (CircleCI modernised), `153111d` (CI workspace/JUnit), `b7a1c04`
    (`pyproject.toml` added), `f423476` (`license_files=[]`, so no License-File in the
    wheel; `twine>=6.0`), `3d25bd5` (`--skip-existing` on the PyPI upload; Streamlit
    Python), `0df0ef5` (`.python-version`, relaxed app pins).
  * None of them is in CHANGELOG, under `[2.0.0]` or `[Unreleased]`.
  * The published 2.0.0 wheel, downloaded and compared, has package files byte-identical to
    the tag. Its upload, 2026-06-15 10:17Z = 07:17 −03:00, came 3 min after `f423476`, and
    its METADATA has no License-File. Together these suggest it was built from `f423476`.
    That is an inference, not a record.
* **`build_test` installs `pyyaml`**, `887c628`: no entry.
* **`environment.yml` / dedicated conda env**, `77ee919`: no entry.
* **Removed from the tree**: `Pipfile` and `.pypirc` (clean-up `0d75db3`): no entry.
  `runtime.txt` and `.python-version` are mentioned (`:186`).

**Not in CHANGELOG, probably by nature (reported, not judged)**

* The part-A re-labels (`4b3b86e`, merge `76b7932`) touch `research/labels/manual_labels.yaml`
  and research scores, not the package. The register commits (`docs/future_work.md`) are
  likewise absent.
