# Front B — Part 1: read-only diagnosis of `distance` and `length_scale`

> **⚠️ Two claims in this document were corrected in Part 1b**
> (`ADDENDUM_part1b.md`). The conclusion — `distance` is inert at the reference
> value — is unchanged.
>
> 1. **§3 / §4, the `distance` sweep.** The `None`→20 sweep was run on the two
>    target tracks only, not on all 47 series. Their own minimum gaps are 21 and
>    29. Over the full split the first value with any effect is **15** (one
>    extremum, no phase change); the first value that changes a phase is **20**.
>    At the reference value 5 the counts are still zero everywhere.
> 2. **§5, the "11/12".** Calling it "not an `evaluate_against_labels.py`
>    number" was wrong. That script at **package defaults** reports synthetic
>    sequence 11/12 and ALL 22/47. The distinction is the **config**, not the
>    script: 11/12 and 22/47 are the defaults figures, 12/12 is the params-9
>    figure.

**Branch** `fix/b-distance-length-scale` (from `develop-v2.1` @ `ab7f244`), no commit.
**Environment** conda `cyclophaser`; `cyclophaser.__file__` =
`/Users/danilocoutodesouza/Documents/Programs_and_scripts/CycloPhaser/cyclophaser/__init__.py`
— the working tree, **not** the published 1.7.3.
**Reference config** `research/labels/configs/cyclophaser_params-9.yaml` (`boundary_padding: edge`).
**Split** `research/labels/split.yaml`, TRAIN only. The 16 test series were never
loaded, scored or inspected. `series_sha256` verified for all 47 train series.

---

## Headline

**The front's premise is false.** Under the reference configuration the
`distance` filter removes **zero** extrema — on the two target tracks and on all
47 training series. It cannot be the cause of anything, because it does nothing.

Separately, and just as decisive for the proposed fix: under the reference
config `mature_method: amplitude`, and in that branch **`length_scale` is never
read for the mature window at all**. Letting `length_scale` govern `distance`
would therefore couple two parameters that are *both* currently inert on the
mature phase.

---

## 1. Target tracks are in TRAIN

| track | split |
|---|---|
| `20160735` | **train** |
| `20203947` | **train** |

Neither is in the test split. Nothing was run on the test split.

---

## 2. Where `distance` and `length_scale` live

### `distance`

| role | location |
|---|---|
| declared (public API, default `None`) | [determine_periods.py:743](cyclophaser/determine_periods.py#L743) in `get_periods`; mirrored at [determine_periods.py:1149](cyclophaser/determine_periods.py#L1149) in `determine_periods` |
| **applied — the only call site** | [determine_periods.py:1041-1044](cyclophaser/determine_periods.py#L1041-L1044) |
| implemented | [determine_periods.py:212-221](cyclophaser/determine_periods.py#L212-L221) in `_refine_extrema` |

**Effective value under the reference config: `distance = 5`.**

Two properties of the call site matter:

1. It is passed **only to `df['z_peaks_valleys']`**. `dz` and `dz2` are computed
   with a bare `find_peaks_valleys(...)` — no prominence, no distance
   ([determine_periods.py:1045-1046](cyclophaser/determine_periods.py#L1045-L1046)).
2. Inside `_refine_extrema`, the order is fixed: absolute prominence → **relative
   prominence** → distance. Relative prominence runs *first* and prunes the
   candidate set that distance then sees.

### `length_scale`

| role | location |
|---|---|
| declared (default `"global"`) | [determine_periods.py:744](cyclophaser/determine_periods.py#L744) |
| validated | [determine_periods.py:995-996](cyclophaser/determine_periods.py#L995-L996) |
| forwarded into `args_periods` | [determine_periods.py:1060](cyclophaser/determine_periods.py#L1060) |
| read — mature | [find_stages.py:236](cyclophaser/find_stages.py#L236), **used only at** [find_stages.py:309](cyclophaser/find_stages.py#L309) |
| read — intensification | [find_stages.py:387](cyclophaser/find_stages.py#L387), used at [406](cyclophaser/find_stages.py#L406), [423](cyclophaser/find_stages.py#L423) |
| read — decay | [find_stages.py:458](cyclophaser/find_stages.py#L458), used at [480](cyclophaser/find_stages.py#L480), [497](cyclophaser/find_stages.py#L497) |

**Effective value under the reference config: `length_scale = local`.**

[find_stages.py:309](cyclophaser/find_stages.py#L309) sits inside the
`else:` branch of `if mature_method == 'amplitude'`. The reference config sets
`mature_method: amplitude`, so for the mature phase `length_scale` is read into
a local variable and then **never used**. The module says so explicitly
([find_stages.py:113-122](cyclophaser/find_stages.py#L113-L122)):
*"Interaction with length_scale / threshold_mature_length: NONE."*

`length_scale` still acts on mature **indirectly**, through the
intensification/decay duration thresholds it does scale: a mature window is only
confirmed if it is bounded by a literal `intensification` and a literal `decay`.

---

## 3. The two target tracks

### Mature windows

`20160735` — n = 259 steps. Labelled sequence
`incipient → intensification → mature → decay`; detected sequence is that core
repeated **four** times (12 phases).

| | start | end | duration |
|---|---|---|---|
| label (tolerance_idx = 5, unsure = false) | 145 | 177 | **33** |
| detected, window overlapping the label | 154 | 166 | **13** |
| Δ | **+9 (late start)** | **−11 (early end)** | **−20** |

Other detected matures: (8,10,3), (55,62,8), (225,232,8) — spurious cycles, no
labelled counterpart.

`20203947` — n = 242 steps. Labelled
`incipient → intensification → mature → decay → intensification → mature → decay → residual`
(2 cycles); detected has **four** cycles (14 phases).

| | start | end | duration |
|---|---|---|---|
| label #1 (tol 5, unsure false) | 122 | 144 | **23** |
| detected overlapping | 130 | 135 | **6** |
| Δ | **+8** | **−9** | **−17** |
| label #2 (tol 3, **unsure true**) | 178 | 188 | **11** |
| detected overlapping | 182 | 187 | **6** |
| Δ | **+4** | **−1** | **−5** |

Other detected matures: (59,62,4), (88,92,5) — spurious.

### Extrema before and after the filter

`20160735` (7 raw peaks, 6 raw valleys):

| | raw | kept | removed by prominence | removed by distance |
|---|---|---|---|---|
| peaks | `[0,21,85,121,172,210,258]` | `[0,21,121,210,258]` | `85, 172` | **none** |
| valleys | `[9,59,97,159,178,228]` | `[9,59,159,228]` | `97, 178` | **none** |

`20203947` (8 raw peaks, 7 raw valleys):

| | raw | kept | removed by prominence | removed by distance |
|---|---|---|---|---|
| peaks | `[0,13,40,74,106,159,202,241]` | `[0,74,106,159,202,241]` | `13, 40` | **none** |
| valleys | `[8,24,61,90,132,185,229]` | `[61,90,132,185]` | `8, 24, 229` | **none** |

Disabling `distance` entirely (`distance=None`) reproduces the kept sets
**byte-for-byte** on both tracks.

Note `20203947`: valleys 8 and 229 are *boundary-adjacent* but not indices 0 or
N−1, so the boundary-preservation rule does not protect them and prominence
removes them. This is adjacent to Front A / defect I territory, not to `distance`.

### Conclusion for item 3 — **(b) another mechanism**

Not (a): `distance` removes nothing. Not (c) alone: the start *is* late, but the
end is early by a comparable or larger amount, so a pure late-start account does
not explain the duration.

Sweeping `distance` from `None` to `20` produces **identical output** on both
tracks. Only at `distance = 30` does anything change — and what changes is that a
whole spurious *cycle* disappears; no mature window changes width. Meanwhile
`mature_amplitude_fraction` moves the width monotonically and strongly
(`20160735`'s labelled-overlapping mature: 13 steps at 0.95 → 32 at 0.90 → 45 at
0.70). `prominence_relative` controls how many cycles exist, not how wide each
mature is.

So two distinct mechanisms, neither of them `distance`:

**(i) Width, symmetric, both ends — `mature_amplitude_fraction = 0.95`.**
`_amplitude_mature_bounds` ([find_stages.py:137-160](cyclophaser/find_stages.py#L137-L160))
walks outward from the z-valley while `z` stays below
`z_peak − fraction × (z_peak − z_valley)`. At 0.95 that level sits 5 % of the
amplitude above the valley — a very tight collar — so the window is narrow on
**both** sides. This is the dominant term.

**(ii) Inventory, not width — `prominence_relative = 0.3`.**
Enough z extrema survive that one labelled cycle is cut into four detected ones.
This is what breaks the *sequence* on both tracks, and it is why the naive
first-to-first pairing looked like a −137-step start error on `20160735`. It does
not shorten any individual mature window.

**Start vs end, separated.** Across all 45 overlap-paired labelled matures in
train: start Δ median **+2** (range −3…+9), end Δ median **−2** (range −34…+3),
duration Δ median **−5** (range −40…+3). The late start reported in
`docs/future_work.md` item 17(e) is reproduced here on real tracks and is real —
but it is roughly half the story. The end is early by a similar median and a far
worse tail, so the mature is squeezed from both sides.

---

## 4. Train split, 35 real + 12 synthetic

**Series with more than one cycle** (z-valleys bounded on both sides by a
surviving z-peak): **9 of 47** — 7 real, 2 synthetic.
Histogram of cycles per series: `{0: 2, 1: 36, 2: 6, 3: 1, 4: 2}`.

**Detected matures shorter than 7 steps** — **20 of 47 series** carry at least one:

*real (14 of 35)*: `20150528`, `20150656`, `20160735`, `20170154`, `20170409`,
`20170520`, `20170794`, `20180263`, `20180628`, `20181046`, `20190325`,
`20191014`, `20203947` (4 of 4 windows short), `20205386` (3 of 3 short).

*synthetic (6 of 12)*: `s9ddbc53c`, `scfcf1387`, `s5b8aa46f`, `sbd6c6920`
(2 of 2), `s6b542eee` (2 of 2), `s5dcc0f79`.

**Mature duration deviation (detected − label)**, overlap-paired, n = 45:

| quantity | median | min | max | mean |
|---|---|---|---|---|
| duration | **−5** | −40 | +3 | −6.58 |
| start | **+2** | −3 | +9 | +2.64 |
| end | **−2** | −34 | +3 | −3.93 |

Two labelled matures have **no** overlapping detected mature at all:
`20170760` [26,39] and `20191014` [43,68].

**Series where `distance` removes any extremum: 0 of 47.**
Total interior extrema removed across the train split: **63 by prominence, 0 by
distance.**

### Why `distance` is inert, quantified

The smallest separation between two *surviving* same-type z extrema, over all 47
train series, is **14** (`20170760`). The next smallest are 19, 19, 20, 21.
`distance = 5` is therefore below the observed floor by a factor of ~3: relative
prominence has already spaced the survivors far wider than the threshold, so the
greedy distance pass never rejects a candidate.

**`distance` would only begin to act above 14**, and the first thing it would do
is delete legitimate extrema in the most densely-structured track in the split.

---

## 5. Reference scores reconfirmed

`python research/labels/evaluate_against_labels.py --config research/labels/configs/cyclophaser_params-9.yaml`
(TRAIN, 63 usable labels):

| quantity | expected | measured | |
|---|---|---|---|
| real, incipient boundary | 8/17 | **8/17** (47.1 %) | ✅ |
| real, refusal | 14/16 | **14/16** (87.5 %) | ✅ |
| real, sequence | 18/35 | **18/35** (51.4 %) | ✅ |
| synthetic, incipient boundary | 9/10 | **9/10** (90.0 %) | ✅ |
| synthetic, sequence | *(brief says 11/12)* | **12/12** (100 %) | ⚠️ see below |
| topology baseline, exact sequence | 22/47 | **22/47** (46.8 %) | ✅ |

**The 11/12 is an attribution error in the brief, not a divergence.** It is not
an `evaluate_against_labels.py` number. It comes from
`research/v3_topology_proxy/measure_topology_proxy.py`, whose detector column runs
at **package defaults**, not at `params-9`:

```
real       n=35   Reader T 14/35 ( 40.0%)   detector 11/35 ( 31.4%)
synthetic  n=12   Reader T  1/12 (  8.3%)   detector 11/12 ( 91.7%)
```

Re-run in this session, that script reproduces `22/47`, `15/47`, `16/47` and
`11/12` exactly, and reports `series_sha256 verified for all 47 training cases`.
So both numbers are correct against their own source; `params-9` scores 12/12 on
synthetic sequence and the default parameters score 11/12. Nothing is stale.

---

## 6. Default-behaviour SHA256

No default-behaviour hash artefact existed in the repository, so one is defined
here explicitly (`default_behaviour_sha256.txt`):

> cyclophaser at **package defaults** (no config passed), over the **47 TRAIN**
> series of `split.yaml` sorted by id; per series the detected `periods` column
> joined with `|` and prefixed `"<id>:"`; lines joined with `\n`; `sha256` of the
> UTF-8 bytes. The 16 test series are not read.

```
n_series : 47
SHA256   : b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5
```

---

## Blockers and divergences

1. **The front's premise does not survive measurement.** `distance` is inert at
   the reference value — 0 removals in 47 series, with the binding threshold at
   14 rather than 5. Making `distance` a function of `length_scale` would be
   tuning a parameter that currently has no effect on any output in the split.
2. **`length_scale` does not reach the mature window** under
   `mature_method: amplitude` ([find_stages.py:309](cyclophaser/find_stages.py#L309)
   is in the `derivative` branch only). The proposed coupling joins two inert
   controls.
3. **The measured cause is elsewhere**, and it is two things:
   `mature_amplitude_fraction = 0.95` (width, both ends) and
   `prominence_relative = 0.3` (cycle inventory). Neither is in this front's
   declared scope.
4. **Part 2 as declared would measure nothing.** A gate on `distance` behaviour
   cannot move any of the reference scores. Recommend re-scoping before
   implementing — the decision is Danilo's.
5. `mature_method='derivative'` with `length_scale='global'` yields **no mature
   phase at all** on both target tracks. Recorded as an observation only.

## Files

| file | contents |
|---|---|
| `train_raw.json` | per-series raw record, 47 series (phases, extrema, attributions) |
| `train_aggregate.txt` | item-4 aggregate tables |
| `sensitivity.txt` | causal sweep on the two targets |
| `headroom_and_hash.txt` | `distance` headroom + hash definition |
| `default_behaviour_sha256.txt` | the integrity reference |

Nothing committed. No detector code modified. `split.yaml` untouched; test split
unread.
