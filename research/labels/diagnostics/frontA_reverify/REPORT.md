# Front A′ — re-verification of Front A under the correct detector (item 13)

**Measurement only.** No line of `cyclophaser/` or `tests/` was changed by this
front. Branch `research/frontA-reverify`, cut from `develop-v2.1` at tip
`558eb5d` (confirmed by `git rev-parse`, working tree clean).

Item 13 suspects that Front A's original measurements (2026-09-09, base
`887c628`, config `params-9`) may have run against the **published cyclophaser
1.7.3 wheel** rather than this checkout. If so, A's documented mechanical cause
— index 0 typed `valley` on 5 tracks, prominence 0.0 — and its conclusion that
A does not block v2.1 would both be measuring the wrong code.

This front separates three variables: **environment**, **code drift**, and
**config drift**.

**Verdict: item 13 does not materialise for Front A.** Step 1a reproduced every
one of A's artifacts to the declared criterion; steps 1b and 2 found zero
differences in the mechanical census at the current tip.

---

## Environment

Dedicated conda env `cyclophaser` (per `CLAUDE.md`, never base):

| | |
|---|---|
| `sys.prefix` | `/Users/danilocoutodesouza/miniconda3/envs/cyclophaser` |
| python | 3.12.14 |
| numpy | 2.5.3 |
| scipy | 1.18.0 |
| pandas | 3.0.5 |

Config digests, both confirmed by `shasum -a 256` at run time:

| config | sha256 |
|---|---|
| `research/labels/configs/cyclophaser_params-9.yaml` | `0c3ec55910c45a6dcf9a1787ceca3f3c6796cf25da953be642befa29eaac9f63` |
| `research/labels/configs/cyclophaser_params-13.yaml` | `c1ab8ce02631f1270b3a633cff2ef43fb5caff64dd492642f56cf5a96e483973` |

`~/Downloads/cyclophaser_params-9.yaml` — the path A's scripts hardcode —
**exists and carries exactly the expected digest** `0c3ec559…9f63`, identical to
the versioned `params-9`. The brief's contingency (repoint `CONFIG_PATH` at the
versioned copy and record the diff) was therefore **not exercised**: step 1a ran
the scripts unmodified, against the file they name.

### Two shadowing mechanisms found and handled

This is worth recording because the brief's central worry is shadowing, and the
machine carries two live vectors, neither of which is the one item 13 describes:

1. **The dedicated `cyclophaser` env carries an editable install pointing at the
   MAIN repo checkout** — `__editable___cyclophaser_2_0_0_finder`, `MAPPING =
   {'cyclophaser': '<main repo>/cyclophaser'}`. Its `install()` does
   `sys.meta_path.append(...)`, i.e. it lands *after* `PathFinder` (observed at
   index 4 at run time), so a `sys.path` entry still wins. That is a property of
   setuptools' current codegen, not a guarantee, so the wrapper asserts rather
   than assuming.
2. **CWD shadowing** (the lesson of items 5 and 12). Handled by running step 1a
   with `CWD` = the worktree.

Every step-1a process therefore printed, *before executing any script body*, the
resolved `cyclophaser.__file__` and the sha256 of the two modules actually
loaded, and hard-asserted both live inside the worktree.

---

## Forensic evidence already on the record (cited, not re-investigated)

- `fix_state_before.json` (branch `fix/idx0-boundary-extremum-type`) records
  `config_gp` with **20 keys** filtered through `inspect.signature(get_periods)`,
  including `prominence_relative` and `incipient_method`. The 1.7.3 wheel's
  `get_periods` accepts only `(vorticity, plot, plot_steps, export_dict,
  periods_args)`; under 1.7.3 that filter would have yielded an **empty dict**.
  Step 1a's own run reprints those 20 keys.
- A's scripts do `sys.path.insert(0, REPO_ROOT)`. `REPORT.md:116` records the
  environment as "pointing at this checkout".
- The `6060c6d` edit changed results (3/3 corrected, 4 synthetics regressed) —
  impossible if the local code had been shadowed.
- `config_pv`/`config_gp` as written == `research/labels/configs/cyclophaser_params-9.yaml`,
  key by key.
- params-9 vs params-13: `filter_params` identical; `phase_params` differ only in
  `distance` (5 → removed), `mature_amplitude_fraction` (0.95 → 0.90),
  `mature_min_depth` (— → 0.8) and `intensification_min_depth` (— → 0.05).
- `argrelextrema(np.greater_equal / np.less_equal)` unchanged:
  `determine_periods.py:122-123` at `887c628`, `:116-117` at the tip. `mode='clip'`
  is the function's default, not an explicit argument.

**Not established by that forensics:** that the checkout was clean (no uncommitted
edits) at census time. Step 1a exists to close exactly that gap, and does.

### New forensic evidence found by this front

A's scripts name their interpreter in their own docstrings:
`~/miniconda3/envs/south_atlantic_cyclone_extremes/bin/python`. That env, as it
stands today:

- has **no cyclophaser installed at all** — no package directory, no
  `dist-info`, absent from `pip list`;
- runs python 3.11.15, numpy 2.4.6, scipy 1.17.1, pandas 3.0.5.

So in that env `import cyclophaser` can only resolve through the script's own
`sys.path.insert(0, REPO_ROOT)`: **there is no wheel there to shadow with.** By
contrast the env item 13 actually names, `lorenz`, *does* carry the published
**cyclophaser 1.7.3** non-editably — confirming the vector is real, but that it
is not the env A's scripts name.

This is evidence, not proof: it is the state of that env **today**, not on
2026-09-09. The step 1a gate, not this observation, is what settles the question.

**One confound, stated plainly:** step 1a runs the original code in a *different*
env from the original (python 3.12.14/scipy 1.18.0 vs 3.11.15/scipy 1.17.1). Had
1a failed, env drift and shadowing would not have been separable from that result
alone. It passed, which makes the point moot — and incidentally shows the A
numbers are stable across that scipy/numpy/python step.

---

## Map: which script produces which artifact

All five artifacts under test were added in a single commit, `6060c6d`
("REFUTADO - NAO MERGEAR", branch `fix/idx0-boundary-extremum-type`, 2026-09-09).

| artifact | produced by | invocation |
|---|---|---|
| `idx0_inventory.csv` | `build_idx0_inventory.py` | no args |
| `idx0_final_stage.csv` | `build_idx0_inventory.py` | no args (same run) |
| `idx0b_prominence.csv` | `build_idx0_inventory.py` | no args (same run) |
| `final_output_check.csv` | `build_final_output_check.py` | no args (imports the above) |
| `fix_state_before.json` | `capture_pipeline_state.py` | `before` |
| `fix_eval_before.txt` | `research/labels/evaluate_against_labels.py` | `--config ~/Downloads/cyclophaser_params-9.yaml`, no `--test` |

---

## STEP 1a — environment (GATE) — **PASS**

Method:

- `git worktree add --detach` **outside** the repo directory, at `6060c6d`; then
  `git checkout 887c628 -- cyclophaser/` inside it.
  `git diff 887c628 -- cyclophaser/` in the worktree: **empty**, i.e. the package
  is byte-for-byte `887c628`. Modules as loaded:
  - `determine_periods.py` sha256 `1061fb5560ef1494da4548f60f033c7f2e5563f82fed32db3f48917326588f6a`
  - `find_stages.py` sha256 `bff7ddbb032a537b8fc54bfaed28890be4ed3310c8db858e4fb614cd2301d3f5`
- Each original script run through `run_in_worktree.py`, which in the same
  process imports `cyclophaser`, asserts the package and both modules resolve
  inside the worktree, prints their paths, digests and `sys.meta_path`, then
  executes the script via `runpy` with its original argv. Every run printed
  `ASSERT OK`. CWD = the worktree throughout.
- Comparison is **field-by-field**, never whole-file sha256: a byte comparison
  fails on a float repr change that carries no measurement content, and passes a
  file that is byte-identical for the wrong reason.

Criterion, as declared in the brief before any measurement:

| field class | criterion | result |
|---|---|---|
| categorical and integer | identical | met |
| index-0 prominence, 5 tracks | exactly `0.0` | met (all 5) |
| all other floats | \|rel. error\| ≤ 1e-9 | met |
| `fix_eval` TRAIN·real | 8 of 17, and 14 of 16 | met, both exact |

**990 fields compared, 0 divergences** (`compare_1a.py`; log in
`outputs/1a_gate.log`). Beyond the criterion, `fix_state_before.json` came back
**byte-identical** to the versioned copy, sha256
`a31391cef3d282b8b9bd6b517a132608b091658d3ac336bd7d947809e08c87ed`.

Reproduced headline numbers: `idx0_tipo` 46 peak / 5 valley; leading decay block
at index 0 on those same 5; `get_periods` kwargs = the same 20 keys, including
`distance: 5` and `prominence_relative: 0.3` — keys the 1.7.3 signature would
have dropped.

**Verdict: PASS. Item 13 does not materialise for Front A.** A's measurements
were made against this repository's code, and its documented mechanical cause
stands as recorded.

---

## STEP 1b — code drift (diagnostic, no pass/fail)

Tip `558eb5d` with `params-9`. `distance` is filtered **in memory**: at the tip it
is no longer a `get_periods` parameter (front B removed it), so
`evaluate_against_labels.load_config`'s existing `inspect.signature` filter drops
it. The script prints the dropped set — `['distance']` — and the YAML on disk is
untouched.

Modules measured: `determine_periods.py` sha256 `2c6eaae8…1cb9`,
`find_stages.py` sha256 `a0c65358…c9ea`.

The census is a step-by-step replay of `get_periods`' body, needed to snapshot
`periods` right after `find_decay_period`. A replay is worth only its fidelity,
so every track *also* ran the real `get_periods` and the two final `periods`
columns were compared: **replay == `get_periods` on all 51 tracks.**

### Differences against Front A: **none**

| comparison | tracks × fields | differences |
|---|---|---|
| `idx0_inventory` (idx0 type, dz signs, leading decay block, its fractions) | 51 × 8 | **0** |
| `idx0b_prominence` (index-0 prominence and its context) | 5 × 5 | **0** |
| `idx0_final_stage` (final-output cross-check) | 51 × 3 | **0** |

Incipient boundary on TRAIN via `evaluate_against_labels.py`:
**17 boundary labels, 8 hit within margin (47.1%)**; refusal — **label says none:
16, detector agreed on 14 (87.5%)**. Both identical to A. (The tip's report adds
one cosmetic line, `against: current`, absent at `6060c6d`; it carries no number.)

**Reading: between `887c628` and `558eb5d`, no code change touched the (M)
quantity on any of the 51 real tracks.**

---

## STEP 2 — current state (diagnostic, no pass/fail)

Tip with `params-13`. All 21 phase keys accepted; nothing dropped.

**(M): 5 of 5 unchanged.** 46 peak / 5 valley; the same 5 tracks; prominence
exactly `0.0` on each; the same leading decay-block lengths. Per-track diff
against A across `idx0_inventory`, `idx0b_prominence` and `idx0_final_stage`:
**0 differences**, same as step 1b. `replay == get_periods` on all 51.

**(V): 4 of 5** — identical to Front A.

| track | split | idx0 type | idx0 prominence | final phase sequence (params-13) | first non-incipient | V |
|---|---|---|---|---|---|---|
| `20180170` | train | valley | 0.0 | `incipient>decay>intensification>mature>decay` | decay | **yes** |
| `20180608` | train | valley | 0.0 | `incipient>intensification>mature>decay` | intensification | **no** |
| `20190325` | train | valley | 0.0 | `incipient>decay>intensification>mature>decay` | decay | **yes** |
| `20191014` | train | valley | 0.0 | `incipient>decay>intensification>decay` | decay | **yes** |
| `20206498` | test | valley | 0.0 | `incipient>decay>intensification>decay` | decay | **yes** |

`20180608` remains the sole exception, by the mechanism A documented: its
incipient boundary is 38 while its leading decay block is 11, so the
unconditional overwrite in `find_incipient_period`
(`find_stages.py:1134` at the tip, `:982` at `887c628`) consumes the whole decay
block and the first non-incipient phase becomes `intensification`. The masking is
unchanged, not repaired.

### Attribution

**No track's V changed relative to A**, so the brief's attribution task is
vacuous for V. One *sequence* change did appear and is attributed here anyway,
since it is the only behavioural difference this front found anywhere.

`20191014` loses its `mature` between params-9 and params-13:
`incipient>decay>intensification>mature>decay` → `incipient>decay>intensification>decay`.

One key flipped at a time from the params-9 baseline (only three keys can differ
at the tip; `distance` is inert there and cannot be flipped):

| variant | `20191014` sequence | V |
|---|---|---|
| params-9 baseline | `incipient>decay>intensification>mature>decay` | yes |
| only `mature_amplitude_fraction=0.90` | unchanged | yes |
| **only `mature_min_depth=0.80`** | **`incipient>decay>intensification>decay`** | yes |
| only `intensification_min_depth=0.05` | unchanged | yes |
| all three (== params-13) | `incipient>decay>intensification>decay` | yes |

The all-three variant reproduces the params-13 census on all 5 tracks, which is
what licenses reading the single-key rows as attribution.

**`mature_min_depth=0.80` alone accounts for it** — the known, deliberate
collateral of front 20(b) (item 22), not a new effect. The other four tracks are
invariant under every single-key flip. This is attribution, **not** a proposed
correction.

---

## Predictions vs result

Declared before measuring; not adjusted afterwards.

| prediction | result |
|---|---|
| **Claude** — 1a PASS | **correct** |
| **Claude** — 1b: idx0 type identical 51/51; incipient 8/17 and 14/16 | **correct**, and stronger than claimed: *every* compared field identical, including the full final-stage cross-check, not only idx0 type |
| **Claude** — 2: (M) 5/5 unchanged | **correct** |
| **Claude** — 2: (V) 4/5, `20180608` still masked by the incipient overwrite | **correct**, including the mechanism and the boundary/block numbers (38 vs 11) |
| **Claude** — 2: `20191014` the likeliest to diverge, having lost its only mature in 20(b) | **correct as to the track and the cause**; but it diverges in *sequence* only — its V does not flip, because the phase it loses is `mature`, mid-sequence, while V reads the *first* non-incipient phase, still `decay`. The prediction named the right track for a reason that does not reach V |
| **Danilo** — "tenho o pressentimento de que essa frente já foi resolvida ao longo das frentes anteriores como colateral" | **borne out, with a correction to the mechanism.** The risk is closed, but not because a later front repaired anything: (M) was never broken and never drifted — identical at `887c628`/params-9, at the tip/params-9, and at the tip/params-13. What earlier fronts did supply was the *instrument* that made the check decisive: item 12's dedicated env, and the CWD/`sys.path` discipline from items 5 and 12 that the wrapper's assert is built on. Collateral in the means, not in the result |

---

## Scope discipline

- The frozen test split was respected. The 16 test reals enter **only** the
  mechanical census (M); `20206498` also enters (V), exactly as in A. No test
  label was read or scored: every `evaluate_against_labels.py` run omitted
  `--test`, and its own output confirms "TEST split held out (16 series)".
- No correction to A was attempted, no repository clean-up performed, and fronts
  B, C, D, E, G and the refusal front were not reopened.
- Every number above was regenerated by the scripts in this directory. None was
  copied from the commissioning brief.

## Files

| file | role |
|---|---|
| `run_in_worktree.py` | provenance wrapper — asserts which `cyclophaser` is loaded, then runs an original A script via `runpy` |
| `compare_1a.py` | the step 1a gate — field-by-field, typed, against the declared criterion |
| `census_tip.py` | (M) and (V) census at the tip, with the replay-equals-`get_periods` fidelity check |
| `compare_against_A.py` | per-track diff of a tip census against A's `6060c6d` artifacts |
| `attribute_params.py` | one-key-at-a-time attribution, params-9 → params-13 |
| `outputs/` | all logs and regenerated artifacts |

The `6060c6d` worktree used for step 1a was temporary and is not part of the
deliverable; `run_in_worktree.py` recreates the run from the two commit hashes.
