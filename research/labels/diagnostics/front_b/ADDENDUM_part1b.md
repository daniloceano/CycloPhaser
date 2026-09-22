# Front B — Part 1b: clarifications and two corrections to Part 1

Read-only. No detector code touched. TRAIN split only; the 16 test series were
never loaded. Environment: conda `cyclophaser`, `cyclophaser.__file__` resolves
to this working tree.

---

## Corrections to Part 1

**Correction 1 — the `distance` sweep was run on two series, not on all 47.**
Part 1 reported a sweep of `distance` from `None` to 20 showing no change, and
in the same section reported a *global* minimum surviving gap of 14 measured on
`20170760`. Those are two different populations, and presenting them together
implied the sweep covered the series that sets the 14. It did not — the sweep
covered only `20160735` and `20203947`, whose own minimum gaps are **21** and
**29**. The full sweep is in §1 below and it does change the claim: the first
value with any effect is **15**, not "above 14 in principle".

**Correction 2 — `11/12` *is* an `evaluate_against_labels.py` number.**
Part 1 said "the 11/12 is an attribution error in the brief… it is not an
`evaluate_against_labels.py` number." That was wrong. `evaluate_against_labels.py`
run with **no `--config`** (package defaults) reports synthetic sequence
**11/12** and ALL sequence **22/47** — identical to the topology script. The
real distinction is the **config**, not the script: `11/12` and `22/47` are the
package-defaults figures, `12/12` is the `params-9` figure. Full table in §3.

Neither correction changes the front's conclusion: `distance` is inert at the
reference value.

---

## 1. The `distance` sweep over all 47 train series

`sweep_distance.py` → `distance_sweep.txt`.

| `distance` | extrema removed | series with a removal | series with a **phase** change |
|---:|---:|---:|---:|
| None | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 |
| **5 (reference)** | **0** | **0** | **0** |
| 8 | 0 | 0 | 0 |
| 10 | 0 | 0 | 0 |
| 12 | 0 | 0 | 0 |
| **14** | **0** | **0** | **0** |
| **15** | **1** | **1** | **0** |
| 16 | 1 | 1 | 0 |
| 18 | 1 | 1 | 0 |
| **20** | 3 | 3 | **1** |
| 25 | 8 | 7 | 5 |
| 30 | 17 | 14 | 11 |
| 40 | 32 | 21 | 17 |

Series whose phases change:

- `distance=20` → `20205386`
- `distance=25` → `20160587`, `20160735`, `20180759`, `20205386`, `20207822`
- `distance=30` → 11 series
- `distance=40` → 17 series

### Why 15–18 "changes nothing" — the two senses separated

The question conflates two different things, and the sweep separates them:

- **Extrema.** `distance=15` *does* remove one extremum. The prediction from the
  gap analysis is confirmed exactly: the binding gap is 14 (`20170760`), so 14
  removes nothing and 15 removes exactly one — the one extremum in the split
  that sits 14 steps from its same-type neighbour.
- **Phases.** That removal does **not** propagate to the `periods` column.
  `20170760` has **no detected mature window at all** under the reference config
  (see §2), and the extremum removed is not one the surviving phase logic
  depends on. The first `distance` value that changes any phase assignment
  anywhere in the split is **20**, and it changes exactly one series.

So Part 1's sweep result ("None→20 identical") was correct *for the two target
tracks* and remains correct for them. Across the whole split the accurate
statement is: **`distance` removes nothing up to and including 14, removes one
inert extremum at 15–18, and first alters a phase at 20.**

At the reference value of **5** all three counts are zero. The conclusion stands.

---

## 2. What `n=45` counts

`mature_pairing_audit.py` → `mature_pairing_audit.txt`.

The unit is **one labelled mature window** — not a series, not a boundary.

| | count |
|---|---|
| train series | 47 |
| series with ≥1 labelled mature | 44 |
| series with **no** labelled mature | 3 — `20171179`, `20181046`, `s0596ea57` |
| **total labelled mature windows** | **47** |
| total *detected* mature windows | 59 |
| paired with an overlapping detected mature | **45** ← the `n=45` |
| excluded (zero overlap with any detected mature) | 2 |

47 = 45 + 2. The two exclusions:

| series | labelled mature | detected matures | why excluded |
|---|---|---|---|
| `20170760` | [26, 39], len 14 | **none at all** | no detected mature to pair with |
| `20191014` | [43, 68], len 26 | [135, 139] | detected window is 67 steps away — zero overlap |

47 labelled windows across 44 series because three series carry two labelled
matures each.

**Deliberately *not* excluded**, for the record:
- Labelled matures flagged `unsure` by the labeller **are included** — 3 of the
  45: `20170154` [31,76], `20180170` [34,42], `20203947` [178,188].
- Series whose detected *sequence* differs from the label **are included**.
  Pairing is by overlap rather than by position precisely so that a sequence
  mismatch does not manufacture a deviation. Position-pairing is what produced
  Part 1's spurious −137 on `20160735`.

Statistics recomputed from this audit reproduce Part 1 exactly: duration median
−5 (−40…+3), start +2 (−3…+9), end −2 (−34…+3).

---

## 3. The gap of 14 — measured after prominence

**After.** The 14 is the smallest same-type separation among the **survivors of
the relative-prominence filter**, i.e. post-prominence and pre-distance — which
is exactly the set the distance criterion is handed.

This is forced by the filter order in
[`_refine_extrema`](../../../../cyclophaser/determine_periods.py#L186-L221):
absolute prominence → **relative prominence** → distance. Measuring the gap on
the raw candidate set would answer a question the code never asks.

Two details of that set: boundary indices `0` and `N−1` are unconditionally kept
and **do** count toward the exclusion radius, so they are included in the gap
measurement; and peaks and valleys are filtered independently, so gaps are
computed within each type, never between a peak and a valley.

In Part 1 the figure was read off the post-prominence **and** post-distance
survivors. Since `distance=5` removes nothing, the two sets are identical and
the number is the same 14. `sweep_distance.py` recomputes it explicitly
post-prominence/pre-distance and reproduces the same ordered list: 14, 19, 19,
20, 21, 23, 24, 25, 26, 26.

---

## 4. Provenance of every reference number

`reference_score_attribution.py` → `reference_score_attribution.txt`. Both
configs re-run live; every figure verified.

| metric | source | **package defaults** | **params-9** |
|---|---|---:|---:|
| incipient boundary | real | 5/17 | **8/17** |
| refusal | real | 1/16 | **14/16** |
| sequence | real | 11/35 | **18/35** |
| incipient boundary | synthetic | 6/10 | **9/10** |
| refusal | synthetic | 2/2 | 2/2 |
| sequence | synthetic | **11/12** | **12/12** |
| sequence | ALL | **22/47** | 30/47 |

| number | script | config | verified |
|---|---|---|---|
| 8/17 | `evaluate_against_labels.py` | `params-9` | ✅ |
| 14/16 | `evaluate_against_labels.py` | `params-9` | ✅ |
| 18/35 | `evaluate_against_labels.py` | `params-9` | ✅ |
| 9/10 | `evaluate_against_labels.py` | `params-9` | ✅ |
| 12/12 | `evaluate_against_labels.py` | `params-9` | ✅ |
| 11/12 | `evaluate_against_labels.py` **or** `measure_topology_proxy.py` | **package defaults** | ✅ |
| 22/47 | `evaluate_against_labels.py` **or** `measure_topology_proxy.py` | **package defaults** | ✅ |

`measure_topology_proxy.py` lives on branch `research/v3-topology-proxy` and
runs the detector at package defaults; its verified output is in
`topology_run_gate_excerpt.txt`. The two scripts agree exactly at defaults, so
`11/12` and `22/47` are **not** topology-front-specific — they are simply the
default-parameter figures.

Consistency check, both configs:

```
defaults : real 11/35 + synthetic 11/12 = 22/47   (reported ALL: 22/47)
params-9 : real 18/35 + synthetic 12/12 = 30/47   (reported ALL: 30/47)
```

**The practical rule:** quoting a train score without naming its config is
ambiguous by 12 percentage points on ALL-sequence. Always state the config.

---

## 5. The default-behaviour SHA256

Generator: `default_behaviour_hash.py`; output: `default_behaviour_sha256.txt`.
The script's module docstring carries the full definition; in short —

- **series**: the 47 `train:` ids of `split.yaml`, sorted ascending; real from
  `tests/calibration_data/*.csv` (`min_max_zeta_850`, `;`, pandas' default float
  parser), synthetic from the frozen `tests/synthetic/data/` CSVs. Test split
  never read.
- **config**: `get_periods(process_vorticity(df))` at **package defaults** —
  deliberately not `params-9`, so the hash tracks shipped behaviour rather than
  one calibration export.
- **format**: one line per id, `"<id>:<periods joined by |>"`, lines joined with
  `\n`, no trailing newline; `sha256` of the UTF-8 bytes.
- **guards**: refuses to run if `cyclophaser` does not resolve to this working
  tree, and verifies every series' `series_sha256` against `manual_labels.yaml`
  before hashing.

```
n_series : 47
SHA256   : b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5
```

Reproduced twice in this session, including once from the standalone generator.

> **Added 2026-09-22, after the fact — not part of the front B record above.**
> This digest is now recorded per run together with its environment (commit,
> python, numpy, scipy, pandas) in `default_behaviour_sha256.txt`. The value
> above stands: it was reproduced **unchanged** under numpy 2.5.3 / scipy 1.18.0
> / pandas 3.0.5 at both `17dc21f` and `7a87a10`. Note also that a digest built
> with a different blob layout is a different number over the same behaviour and
> must not be compared against this one. Nothing in the front B record was
> rewritten.

---

## Files

| file | role |
|---|---|
| `REPORT_front_b_part1.md` | part 1 report (carries a correction banner) |
| `ADDENDUM_part1b.md` | this document |
| `collect_train_diagnostics.py` → `train_raw.json` | per-series record for all 47 |
| `report_targets.py` → `target_tracks.txt` | the two target tracks in detail |
| `report_train_aggregate.py` → `train_aggregate.txt` | item-4 aggregates |
| `sensitivity_probe.py` → `sensitivity.txt` | causal sweep on the two targets |
| `report_headroom.py` → `headroom_and_hash.txt` | gap headroom |
| `sweep_distance.py` → `distance_sweep.txt` | **1b** — sweep over all 47 |
| `mature_pairing_audit.py` → `mature_pairing_audit.txt` | **1b** — the `n=45` audit |
| `reference_score_attribution.py` → `reference_score_attribution.txt` | **1b** — provenance |
| `default_behaviour_hash.py` → `default_behaviour_sha256.txt` | **1b** — integrity reference |
| `topology_run_gate_excerpt.txt` | verified excerpt from the v3 topology run |

No test-split track data is contained in any of these files. `train_raw.json`
holds train series only.
