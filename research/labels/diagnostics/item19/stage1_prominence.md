# Stage 1 step 3 - relative prominence (TRAIN only, `params-10`)

**The quantity.** `scipy.signal.peak_prominences(signed_data, interior)[0]`,
computed at `cyclophaser/determine_periods.py:188` on the FILTERED vorticity
(`vorticity_smoothed2`, `determine_periods.py:1012`/`:1017`), and compared at
`determine_periods.py:203-208` against
`prominence_relative x max(prom_vals of the surviving interior set)`.
The denominator is per series **and per extremum type** - peaks are refined on
`data`, valleys on `-data` (`determine_periods.py:135-136`) - so every number
below is a fraction of its own series' own valley maximum, never a vorticity
unit. Indices 0 and N-1 are exempt from the filter
(`determine_periods.py:180-181`) and are shown as `bnd`.

## (i) `20160735` - every z valley that generates a mature candidate

Label: mature 145 -> 177. Detected mature blocks under params-10: [(8, 10), (55, 62), (154, 166), (225, 232)].

A candidate needs a surviving valley plus a surviving z peak on each side
(`find_stages.py:247-265`); the window is `_amplitude_mature_bounds`
(`find_stages.py:135-160`) called directly. `in label?` asks whether the valley
position falls inside 145-178. `survived?` asks whether the window is still
`mature` in the output, i.e. whether the neighbour check
(`find_stages.py:340-352`) kept it.

| valley idx | rel prominence | prev/next peak | amplitude window | len | in label? | survived? |
|---|---|---|---|---|---|---|
| 9 | 0.3037 | 0/21 | 8-10 | 3 | no | yes |
| 59 | 0.5709 | 21/121 | 55-62 | 8 | no | yes |
| 159 | 1.0000 | 121/210 | 154-166 | 13 | YES | yes |
| 228 | 0.4902 | 210/258 | 225-232 | 8 | no | yes |

## (ii) every train series whose detected mature matches its label

Matching = |Dstart| <= 6 and |Dend| <= 6 against the labelled
mature. The prominence shown is that of the surviving z valley inside the
matching block (the deepest one, when a merged block holds more than one).

| series | src | detected mature | label | Dstart | Dend | valley idx | rel prominence |
|---|---|---|---|---|---|---|---|
| `20150069` | real | 32-42 | 29-45 | 3 | -3 | 37 | 1.0000 |
| `20150528` | real | 30-35 | 29-37 | 1 | -2 | 33 | 1.0000 |
| `20150532` | real | 35-41 | 35-41 | 0 | 0 | 40 | 1.0000 |
| `20150656` | real | 37-46 | 34-52 | 3 | -6 | 42 | 1.0000 |
| `20160587` | real | 52-62 | 51-63 | 1 | -1 | 56 | 1.0000 |
| `20170520` | real | 28-33 | 27-35 | 1 | -2 | 31 | 1.0000 |
| `20170794` | real | 39-46 | 36-52 | 3 | -6 | 42 | 1.0000 |
| `20180170` | real | 37-45 | 34-42 | 3 | 3 | 39 | 1.0000 |
| `20180263` | real | 27-32 | 25-35 | 2 | -3 | 30 | 1.0000 |
| `20180300` | real | 16-24 | 13-25 | 3 | -1 | 20 | 1.0000 |
| `20180608` | real | 63-69 | 61-73 | 2 | -4 | 66 | 1.0000 |
| `20180759` | real | 30-45 | 31-45 | -1 | 0 | 34 | 1.0000 |
| `20190325` | real | 101-104 | 95-109 | 6 | -5 | 103 | 1.0000 |
| `20190397` | real | 31-41 | 34-41 | -3 | 0 | 38 | 1.0000 |
| `20190870` | real | 37-47 | 37-53 | 0 | -6 | 41 | 1.0000 |
| `20190879` | real | 30-36 | 30-39 | 0 | -3 | 34 | 1.0000 |
| `20191104` | real | 30-39 | 26-43 | 4 | -4 | 35 | 1.0000 |
| `20191155` | real | 33-45 | 33-46 | 0 | -1 | 40 | 1.0000 |
| `20201245` | real | 40-50 | 40-51 | 0 | -1 | 46 | 1.0000 |
| `20202023` | real | 56-63 | 56-64 | 0 | -1 | 60 | 1.0000 |
| `20205386` | real | 60-62 | 56-64 | 4 | -2 | 61 | 0.3074 |
| `s46657891` | syn | 28-37 | 25-40 | 3 | -3 | 32 | 1.0000 |
| `s4e7ff65c` | syn | 22-32 | 20-35 | 2 | -3 | 27 | 1.0000 |
| `s5b8aa46f` | syn | 25-30 | 22-31 | 3 | -1 | 27 | 1.0000 |
| `s5dcc0f79` | syn | 19-24 | 16-26 | 3 | -2 | 21 | 1.0000 |
| `s6b1e8245` | syn | 36-43 | 34-45 | 2 | -2 | 40 | 1.0000 |
| `s6b542eee` | syn | 13-18 | 12-18 | 1 | 0 | 16 | 0.9761 |
| `s8001f17b` | syn | 28-37 | 26-39 | 2 | -2 | 32 | 1.0000 |
| `s9ddbc53c` | syn | 19-24 | 18-25 | 1 | -1 | 21 | 1.0000 |
| `sbceec644` | syn | 22-33 | 21-33 | 1 | 0 | 27 | 1.0000 |
| `sbd6c6920` | syn | 15-19 | 13-21 | 2 | -2 | 17 | 1.0000 |
| `scfcf1387` | syn | 31-36 | 29-38 | 2 | -2 | 33 | 1.0000 |

## (iii) do the two distributions overlap?

* spurious - `20160735` candidate valleys OUTSIDE the labelled mature: n=3, range **0.3037 - 0.5709**
* true - valleys generating a label-matching mature across the train split: n=32, range **0.3074 - 1.0000**

**The two distributions OVERLAP.**

Overlapping band **0.3074 - 0.5709**: it contains 2 of the 3 spurious values and 1 of the 32 true ones.

A single threshold placed above the worst spurious value (0.5709) would also reject 1 of the 32 true mature-generating valleys.

See `fig_prominence_distributions.png`.
