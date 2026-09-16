# Front v3.0 — premise measurement: RESULT

**VERDICT: FAIL**, on all three declared criteria. The premise does not hold as
stated.

A first write-up of this front offered the cycle skeleton as the surviving half
of the premise. The complementary round below computed the constant baselines
that claim needed, and **withdraws it**: against its own baselines the topology
proxy is not measurably better than answering the same thing every time, on any
part of the inventory question. The verdict was FAIL before that round and is
unchanged by it; what changed is that the FAIL is no longer partial.

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

Read these against the per-phase constant baselines below before drawing
anything from them: 100.0 % on intensification is a 100.0 % bar, and the 51.1 %
and 63.8 % are both *below* their phases' own bars.

The failure is **entirely** in the two phases defined by *flatness* — incipient
and residual — and **not at all** in the three defined by the direction of
change. That split is not incidental: flatness at the ends is precisely the
property a Lanczos window of `len//2` plus two Savgol passes destroys, and the
package's own `boundary_padding` measurements already record it (normalised
`|dz|` at t0 has a median of 0.42 under `reflect`, when a plateau needs it below
`tau`).

## The FAIL is about the premise, not about Reader T's thresholds

> **POST-HOC / EXPLORATORY.** Everything from here to the end of this document
> was produced *after* the gate above was run and its verdict recorded. None of
> it is part of the gate, none of it can change the verdict, and the threshold
> sweeps below choose their winner on the same 47 cases they are scored on —
> they are upper bounds, not results a held-out set would reproduce.


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

### Incipient presence is close to unreadable from the filtered series  *(POST-HOC / EXPLORATORY — tau swept)*

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

### The information exists — in the raw series  *(POST-HOC / EXPLORATORY)*

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

## The skeleton reduction  *(POST-HOC / EXPLORATORY)*

With incipient and residual stripped from **both** sides, leaving only the
deepening/weakening skeleton the topology speaks to:

| prominence_relative | core sequence | mature count |
|---|---|---|
| None (Reader T as declared) | 33/47 — 70.2 % | 41/47 — 87.2 % |
| 0.02 – 0.20 | 34/47 — 72.3 % | 42/47 — 89.4 % |
| **0.30 – 0.50** (swept) | **37/47 — 78.7 %** | **43/47 — 91.5 %** |

**Correction — these numbers do not mean what the first write-up said they
meant.** That draft called this "the half of the impression measurement
supports". The constant baselines below, computed in the complementary round,
withdraw that claim: 78.7 % and 87.2 % *are* the constant baselines, to the
case.

## Constant baselines  *(POST-HOC / EXPLORATORY, complementary round)*

A rate means nothing until you know what answering the same thing every time
would have scored. `baselines.py`; full output in `run_baselines.txt`.

### Per-phase presence

"always" emits the phase on every case, "never" on none. The bar is the larger
of the two — the phase's own majority class.

| phase | label has | always | never | **bar** | Reader T | six-function detector |
|---|---|---|---|---|---|---|
| intensification | 47 | 100.0 % | 0.0 % | **100.0 %** | 100.0 % *(ties)* | 100.0 % *(ties)* |
| mature | 44 | 93.6 % | 6.4 % | **93.6 %** | 97.9 % *(+2 cases)* | 97.9 % *(+2)* |
| decay | 44 | 93.6 % | 6.4 % | **93.6 %** | 97.9 % *(+2 cases)* | 97.9 % *(+2)* |
| incipient | 28 | 59.6 % | 40.4 % | **59.6 %** | **51.1 % — below bar** | 61.7 % *(+1)* |
| residual | 10 | 21.3 % | 78.7 % | **78.7 %** | **63.8 % — below bar** | 87.2 % *(+4)* |

Reader T clears its own majority bar on **two** of the five phases, by two cases
each. It is **below** the bar on incipient and on residual, and its 100 % on
intensification is a 100 % bar — that column carries no information at all,
because every one of the 47 labels has an intensification.

### Skeleton and mature count

The label population is highly homogeneous, and that is what the skeleton
numbers were measuring:

| label core sequence | n |
|---|---|
| intensification → mature → decay | **37** |
| decay → intensification → mature → decay | 4 |
| intensification | 3 |
| intensification → mature → decay → intensification → mature → decay | 3 |

| reader | core sequence | vs constant |
|---|---|---|
| **constant: always answer the modal core** | **37/47 — 78.7 %** | — |
| proxy, `prominence_relative=None` (as declared) | 33/47 — 70.2 % | **−8.5 pts (−4 cases)** |
| proxy, `prominence_relative=0.30` (POST-HOC swept) | 37/47 — 78.7 % | **+0.0 pts (0 cases)** |
| six-function detector | 42/47 — 89.4 % | **+10.6 pts (+5 cases)** |

Label mature-count distribution: `{0: 3, 1: 41, 2: 3}` — modal count 1.

| reader | mature count | vs constant |
|---|---|---|
| **constant: always answer 1** | **41/47 — 87.2 %** | — |
| proxy, `prominence_relative=None` (as declared) | 41/47 — 87.2 % | **+0.0 pts (0 cases)** |
| proxy, `prominence_relative=0.30` (POST-HOC swept) | 43/47 — 91.5 % | +4.3 pts (+2 cases) |
| six-function detector | 42/47 — 89.4 % | +2.1 pts (+1 case) |

**What this retracts.** The topology proxy's apparent skeleton competence is the
population's homogeneity, not information it extracts. As declared it is *worse*
than a constant on core sequence (−4 cases) and *exactly* a constant on mature
count. Only after post-hoc tuning does it reach the constant on one and beat it
by two cases on the other. The earlier sentence "the filtered series' topology
is genuinely informative — 91.5 % on mature count" does not survive: against its
own baseline that is +2 cases, on a swept setting.

The six-function detector, by contrast, clears the constant on both (+5 and +1
cases) and on four of the five per-phase bars.

### The detector's own topology baseline

Asked for explicitly, for the record — exact full-sequence agreement:

| | exact sequence | vs constant |
|---|---|---|
| **constant: modal full sequence** (`incipient → intensification → mature → decay`) | **16/47 — 34.0 %** | — |
| six-function detector | **22/47 — 46.8 %** | **+12.8 pts (+6 cases)** |
| Reader T (proxy) | 15/47 — 31.9 % | **−2.1 pts (−1 case)** |

The detector carries real information over a constant answer. The proxy does
not — it is one case worse than answering the same four phases every time.

## The two incipient-presence numbers, reconciled

51.1 % and 68.1 % both appear above and are **the same probe on the same signal
— the filtered `dz` — at two different taus**. Neither is a raw-series number.

| | tau_head | says yes | agreement | misses | false |
|---|---|---|---|---|---|
| **Reader T as declared** — the package's shipped default, and **the configuration the gate scored** | 0.20 | 5 | **24/47 — 51.1 %** | 23 | 0 |
| **POST-HOC**, the sweep's oracle best, chosen on these same 47 cases | 0.70 | 39 | **32/47 — 68.1 %** | 2 | 13 |

The 68.1 % appears only in the filtered-vs-raw table, where each signal is given
its own best tau so that neither is handicapped in the comparison. It is an
oracle-tuned upper bound for the filtered signal, not a configuration anyone
ran, and not the gate's number. For scale, the constant "always incipient" is
28/47 = 59.6 % — so even the oracle-tuned filtered probe carries 8.5 points over
a constant, and the as-declared one is 8.5 points *below* it.

## Consequence for the architecture

The premise as stated — "the filtered series tells you which phases exist" — is
refuted. The corrected statement the measurement supports is narrower:

> The heavily filtered series is **not** a proxy for the presence of
> `incipient` or `residual`, and no threshold makes it one. On the cycle
> skeleton it is **not measurably better than a constant answer** either: as
> declared it is 4 cases worse than always answering
> `intensification → mature → decay`, and only post-hoc tuning brings it level.
> Across the whole inventory question it sits one case below the modal constant.

The first write-up claimed the skeleton as the surviving half of the premise.
With the baselines in hand that claim is withdrawn — nothing in this
measurement shows the filtered series' topology carrying inventory information
that a constant answer does not already carry.

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
python research/v3_topology_proxy/ceiling_diagnostic.py       # POST-HOC only
python research/v3_topology_proxy/baselines.py               # POST-HOC only
```

Full console output in `run_gate.txt`, `run_ceiling.txt` and `run_baselines.txt`.
