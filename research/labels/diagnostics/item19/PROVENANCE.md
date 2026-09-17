# Item 19/20, part 1 — code provenance (no measurement)

This file holds **only the config-independent half** of the front's stage 1 and
stage 2 deliverables: where in the package the quantities named by the gate are
computed, and which code path each way of losing a mature goes through. It
contains no scores and no figures by design.

It was written and committed (`79bb7b3`) **before** `params-10` was supplied and
before anything was measured, so its claims are predictions from the code
structure alone. Stages 1 and 2 have since been run; the measured results are in
`REPORT.md`, and they confirm the one prediction this file makes — stage **C**
accounts for 0 of the 402 observed mature losses.

The directory is named `item19` because Danilo's brief named it so; the
`future_work.md` item is numbered 20 (19 was already Front B).

## Environment

Confirmed before anything else was read, per `CLAUDE.md`:

```
$ conda activate cyclophaser && which python
/Users/danilocoutodesouza/miniconda3/envs/cyclophaser/bin/python
$ python -c "import cyclophaser; print(cyclophaser.__file__)"
/Users/danilocoutodesouza/Documents/Programs_and_scripts/CycloPhaser/cyclophaser/__init__.py
```

The working tree, not the published 1.7.3. (Item 13's open risk does not apply
to this front.)

## The quantity compared with `prominence_relative`

Not a property of the mature window at all — a property of the **z extrema**
that the mature search iterates over.

| step | where |
|---|---|
| z extrema are the only ones prominence-filtered (dz and dz2 are not) | `cyclophaser/determine_periods.py:1022-1031` |
| the series it runs on is the **filtered/smoothed** vorticity `vorticity_smoothed2`, column `z` | `determine_periods.py:1012`, `:1017` |
| peaks and valleys are refined in two separate calls, on `data` and `-data` | `determine_periods.py:135-136` |
| the raw quantity: `scipy.signal.peak_prominences(signed_data, interior)[0]` | `determine_periods.py:188` |
| the normalisation: threshold = `prominence_relative × prom_vals.max()` over the **surviving interior set of that same extremum type** | `determine_periods.py:203-208` |
| indices 0 and N−1 are exempt — never filtered, whatever their prominence | `determine_periods.py:180-181` |

Two consequences the stage-1 tables have to respect:

1. The denominator is **per series and per extremum type**. A "relative
   prominence of 0.34" for a valley in `20160735` and the same number for a
   valley in `20191014` are fractions of two different maxima, so the two
   distributions asked for in step 2.3(iii) are only comparable as *fractions*,
   never as vorticity units.
2. Peaks and valleys are normalised against **different** maxima in the same
   series (`determine_periods.py:769-770` already records this as a known
   asymmetry). A mature candidate needs a z valley **and** a flanking z peak on
   each side (`find_stages.py:247-265`), so raising `prominence_relative` can
   destroy a mature by removing either one.

## Where a mature can be lost — the A/B/C/D map for step 3.3

Under `params-10`, which sets `mature_method="amplitude"`:

| label | mechanism | where |
|---|---|---|
| **A** | the z valley, or one of its two flanking z peaks, is cut by the relative-prominence filter — after which the valley is not iterated at all, or is skipped for want of a flanking peak | filter: `determine_periods.py:203-208`; skip: `find_stages.py:261-262` |
| **B** | the amplitude window collapses: `z` leaves the `mature_amplitude_fraction` level immediately on one side, so the window is empty | bounds: `find_stages.py:135-160`; empty-window `continue`: `find_stages.py:284-285` |
| **C** | the `threshold_mature_length` duration check discards the window | `find_stages.py:304-312` |
| **D** | the window survives but the neighbour check clears it — a mature block is erased unless it is immediately preceded by `intensification` and followed by `decay` | `find_stages.py:340-352` (and `find_residual_period`'s separate copy of the same assumption) |

**C is unreachable under `params-10` and cannot account for a single lost
mature.** `find_stages.py:304-312` is the `else` arm of `if mature_method ==
'amplitude'` at `:287`; the `amplitude` arm assigns the window unconditionally
at `:303`, with the comment at `:288-302` recording that as a deliberate
decision. This is the same structural fact Front B hit from the other side
(item 19: `length_scale` never reaches the mature window under `amplitude`).

That is decided before any measurement, and it bears on the gate's declared next
step: a ≥ 7-step duration floor for mature candidates would be a **new**
mechanism in the `amplitude` arm, not a re-tuning of `threshold_mature_length`.

## Labels for the three series the gate names (train split)

Read from `research/labels/manual_labels.yaml` (schema 4, 63 labels).

| series | n_steps | labelled phases (`start_idx`) | mature window |
|---|---|---|---|
| `20160735` | 259 | incipient 0, intensification 19, mature 145, decay 178 | 145 → 178, **33 steps** |
| `20191014` | 206 | intensification 0, mature 43, decay 69 | 43 → 69, 26 steps |
| `20203947` | 242 | incipient 0, intensification 38, mature 122, decay 145, then intensification 165 / mature 178 / decay 189 / residual 205, all four `unsure` | 122 → 145, 23 steps (first) |

`20160735` matches the brief exactly (mature 145 → 178, 33 steps).

## Not touched

No series in `research/labels/split.yaml`'s **test** list was read, scored or
plotted. Nothing in this file was produced by running the detector.
