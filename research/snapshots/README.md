# Published-version snapshots

Frozen phase detections produced by **published** cyclophaser releases over the
same 63 series the calibration uses (51 real tracks + the 12 frozen synthetic
cases). They are the Benchmark tab's reference columns: what the detector did
before the calibration started.

| file | release | series | failures | sha256 |
|---|---|---|---|---|
| `v1.9.4.json` | 1.9.4 (PyPI, 2024-11-08) | 63 | 0 | `c22eebe72d026a5c6419a4ca417e2dac13ed64ee34d037a471a1c84d37c2d62a` |
| `v2.0.0.json` | 2.0.0 (PyPI, 2026-06-15) | 63 | 0 | `944b51d89d4efc495a0502e3eb8a5092d39022ec4ebb1f27635eabcbabad8ab0` |

`SHA256SUMS` carries the same two hashes in `shasum -a 256 -c` format.

## Why a file and not a live run

Version 1 is **not expressible as a YAML** in the current detector. Both
releases have an identical public signature — 19 parameters on
`determine_periods`, defaults `use_filter='auto'`,
`replace_endpoints_with_lowpass=24`, `cutoff_high=48.0`,
`threshold_mature_distance=0.125`, `threshold_mature_length=0.03` — and
**neither has** `prominence_relative`, `distance`, `length_scale`,
`mature_method`, `mature_amplitude_fraction`, `boundary_padding` or any
`incipient_*`. The behaviour difference is in the CODE, not in the arguments:
2.0.0 added `_collapse_plateaux` to `determine_periods.py` and changed
`find_stages.py` and `plots.py` (verified here: `_collapse_plateaux` is present
in the 2.0.0 wheel and absent from the 1.9.4 one). So the snapshot has to be
produced by *running those releases*, and it is generated once and read from
disk afterwards — the app never runs a published version live.

## How they were generated

```bash
python -m venv /tmp/venv_1_9_4
/tmp/venv_1_9_4/bin/pip install cyclophaser==1.9.4
cd /                                   # NOT the repo root
/tmp/venv_1_9_4/bin/python -P \
    <repo>/research/snapshots/make_published_snapshot.py \
    --repo <repo> --out <repo>/research/snapshots/v1.9.4.json
```

Each release goes in its **own virtual environment**, and no published
cyclophaser is ever installed into the `cyclophaser` conda environment the app
and the test suite use — that is the shadowing that produced backlog item 13
(an installed 1.7.3 hiding the working tree).

**`-P`, and running from outside the repository, are load-bearing.** Without
them the CWD is on `sys.path` and `import cyclophaser` resolves to the working
tree's package instead of the installed wheel. This was not hypothetical: during
this front both venvs initially reported the working tree's
`determine_periods.py` as the module they had imported. The generator now
refuses to run unless `cyclophaser` resolved inside the running interpreter's
own environment, so the mistake cannot silently produce a file again.

The generator puts only `<repo>/research/labels` on `sys.path` — for
`labels_core`, which imports nothing but pandas — and never `<repo>` itself, for
the same reason.

## Contents

Per series: `n_steps`, `series_sha256` of the raw values, and `phases` as
`[[phase, start_idx, end_idx_inclusive], ...]` over normalised phase names. A
series whose detection raised carries its traceback under `error` and
`phases: null`; it is never omitted, because a snapshot missing a track would
understate the divergence it exists to measure. Both files currently record
zero failures.

The `snapshot` block records the release, the resolved module path, the Python
version, the full public signature as it was at that release, and the fact that
**no argument at all** is passed to `process_vorticity` or `get_periods` — the
snapshot is that release's package defaults.

## Measured divergence from the current reference

Against `params-11`, over the 51 real tracks (computed with
`research/labels/configs/cyclophaser_params-11.yaml` on the current working tree):

| snapshot | series whose phase SEQUENCE differs |
|---|---|
| v1.9.4 | 41 / 51 (80.4 %) |
| v2.0.0 | 40 / 51 (78.4 %) |

Disagreement by decile of position along the series (v1.9.4; v2.0.0 is within
one point everywhere):

| decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| % of timesteps disagreeing | **60** | 36 | 32 | 36 | 29 | 21 | 26 | 28 | 21 | **20** |

The divergence is concentrated at the **leading** edge only. The trailing decile
is the *quietest* region of the series, not a second peak — so "concentrated at
the edges", plural, is not what the data show.

**What this does not establish.** The snapshot column differs from params-11 in
roughly fifteen parameters at once (`boundary_padding`, `replace_endpoints_with_lowpass`,
`cutoff_high`, smoothing, `prominence_relative`, `mature_method`,
`incipient_method`, …), so these numbers measure the SIZE of the gap between
"published defaults" and "current reference". They do not attribute it to any
one mechanism — in particular they are not evidence that the leading-edge
concentration is caused by the filter's zero padding, which remains a plausible
but unmeasured explanation. Attributing it would need a one-parameter-at-a-time
run, which this front did not do.
