# Front v3.0 — premise measurement: RESULT

**VERDICT: FAIL**, on all three declared criteria. The premise does not hold as
stated — but it fails in a specific, decomposable way that says what a v3.0
architecture could still take from the filtered series and what it must get
elsewhere.

The gate, the reader and the prediction were committed in `PROTOCOL.md`
(`2d95e25`) and the reader in `measure_topology_proxy.py` (`18ead09`) before the
measurement was run. `series_sha256` verified for all 47 training cases. The 16
test cases were not read.

## The gate

Exact phase-name-sequence agreement (order and multiplicity, **no index ever
compared**), 47 training cases:

| reader | exact-sequence agreement |
|---|---|
| **Reader T — the topology proxy** | **15 / 47 — 31.9 %** |
| the current six-function detector | 22 / 47 — 46.8 % |
| majority-class baseline (always emit the modal sequence) | 16 / 47 — 34.0 % |

| declared criterion | required | got | |
|---|---|---|---|
| 1 — absolute | ≥ 70 % (≥ 33/47) | 31.9 % | **FAIL** |
| 2 — beats the constant baseline by ≥ 10 pts | ≥ 44.0 % | 31.9 % | **FAIL** |
| 3 — ≥ the six-function detector | ≥ 46.8 % | 31.9 % | **FAIL** |

Reader T does not merely miss the bar; it scores **below the constant baseline
of always answering `incipient → intensification → mature → decay`**.

## The prediction, as declared, against the result

Declared before running, in `PROTOCOL.md`, and not adjusted:

| predicted | measured | |
|---|---|---|
| FAIL | FAIL | ✓ |
| exact-sequence agreement in the 30–55 % band | 31.9 % | ✓ |
| dominant error is incipient presence, agreeing on < 75 % | 51.1 % | ✓ |
| incipient **under**-detected, not over-detected | 23 misses, **0** false positives | ✓ |
| residual over-fires | 11 false positives vs 6 misses | ✓ |
| the skeleton is the strong part | core sequence 70.2 %, mature count 87.2 % | ✓ |

## Why it fails — the decomposition

Presence/absence agreement per phase, over the 47:

| phase | label has | proxy has | agree | rate | missed | false |
|---|---|---|---|---|---|---|
| intensification | 47 | 47 | 47 | **100.0 %** | 0 | 0 |
| mature | 44 | 45 | 46 | **97.9 %** | 0 | 1 |
| decay | 44 | 45 | 46 | **97.9 %** | 0 | 1 |
| incipient | 28 | 5 | 24 | **51.1 %** | 23 | 0 |
| residual | 10 | 15 | 30 | **63.8 %** | 6 | 11 |

The failure is **entirely** in the two phases defined by *flatness* — incipient
and residual — and **not at all** in the three defined by the direction of
change. That split is not incidental: flatness at the ends is precisely the
property a Lanczos window of `len//2` plus two Savgol passes destroys, and the
package's own `boundary_padding` measurements already record it (normalised
`|dz|` at t0 has a median of 0.42 under `reflect`, when a plateau needs it below
`tau`).

## The FAIL is about the premise, not about Reader T's thresholds

Reader T inherited two thresholds from the package's defaults (`tau = 0.20` at
each end, `prominence_relative = None`). A post-hoc sweep
(`ceiling_diagnostic.py`, run after the verdict was recorded) asks what the best
*any* setting could do. The best setting is chosen on the same 47 cases it is
scored on, so it is an **optimistically biased upper bound** — no held-out
calibration could beat it:

```
CEILING  22/47 = 46.8 %   (prominence_relative=0.30, tau_head=0.40, tau_tail=0.0)
declared gate threshold   70.0 %   NOT reached
```

**46.8 % is the ceiling.** No combination of the two thresholds reaches even
50 %, let alone 70 %. The FAIL survives the most generous possible tuning, and
it lands exactly on the six-function detector's own 46.8 % rather than above it.

Note also that the sweep's optimum for the tail is `tau_tail = 0.0` — that is,
**the best available policy for `residual` is to never emit it at all.**

### Incipient presence is close to unreadable from the filtered series

Sweeping `tau_head` alone, against the 28/47 that carry an incipient:

| tau | proxy says yes | agreement | missed | false |
|---|---|---|---|---|
| 0.20 (shipped default) | 5 | 51.1 % | 23 | 0 |
| 0.40 | 18 | 61.7 % | 14 | 4 |
| 0.60 | 32 | 66.0 % | 6 | 10 |
| **0.70 (best)** | 39 | **68.1 %** | 2 | 13 |
| 0.90 | 45 | 63.8 % | 0 | 17 |

The probe never separates the two populations — it only trades misses for false
positives. Its best, 68.1 %, sits **8.5 points above simply answering "yes"
every time** (28/47 = 59.6 %). On this question the heavily filtered series
carries almost no information.

### The information exists — in the raw series

The same probe on the **unfiltered** input (the package's own
`incipient_plateau_signal="vorticity"`), each at its own best tau:

| signal | best agreement |
|---|---|
| filtered `dz` — *the premise* | 32/47 — 68.1 % |
| **raw zeta** | **38/47 — 80.9 %** |
| raw zeta, savgol 11 | 37/47 — 78.7 % |
| raw zeta, savgol 21 | 38/47 — 80.9 % |
| constant "always incipient" | 28/47 — 59.6 % |

So incipient presence is not intrinsically unreadable — **the filtering is what
destroys it.** 12.8 points of the question survive in the raw series and are
gone from the filtered one.

## What the premise gets right

With incipient and residual stripped from **both** sides, leaving only the
deepening/weakening skeleton the topology actually speaks to:

| prominence_relative | core sequence | mature count |
|---|---|---|
| None (Reader T as declared) | 33/47 — 70.2 % | 41/47 — 87.2 % |
| 0.02 – 0.20 | 34/47 — 72.3 % | 42/47 — 89.4 % |
| **0.30 – 0.50** | **37/47 — 78.7 %** | **43/47 — 91.5 %** |

This is the half of Danilo's impression that measurement supports: for *how many
cycles and where the matures are*, the filtered series' topology is genuinely
informative — 91.5 % on mature count, from extrema alone, with no phase function
involved.

## Consequence for the architecture

The premise as stated — "the filtered series tells you which phases exist" — is
refuted. The corrected statement the measurement supports is narrower:

> The heavily filtered series is a usable proxy for the **cycle skeleton**
> (intensification / mature / decay and their repeats, ~79 % sequence, ~92 %
> mature count). It is **not** a proxy for the presence of `incipient` or
> `residual`, and no threshold makes it one.

A v3.0 built on a single filtered series would therefore inherit a wrong phase
inventory on roughly half its cases — and Front A is the precedent for what a
wrong skeleton does downstream (forcing index 0 to `peak` made
`find_mature_stage` invent a spurious mature block on 20190325 and 20191014). A
proxy architecture is not ruled out, but it cannot be single-series: the
skeleton and the two flat-end phases have to be read off **different** signals,
the latter at a filtering level that still has the flatness in it.

That is a different architecture from the one this front set out to test, so it
needs its own front and its own declared gate before any implementation.

## Reproducing

```bash
conda activate cyclophaser    # never base -- see CLAUDE.md
python research/v3_topology_proxy/measure_topology_proxy.py   # the gate
python research/v3_topology_proxy/ceiling_diagnostic.py       # post-hoc only
```

Full console output of both runs is in `run_gate.txt` and `run_ceiling.txt`.
