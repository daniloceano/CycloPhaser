# Stage 2 - where a lost mature disappears (A/B/C/D)

Every (cell, series) pair in which a series that HAS a mature under params-10
ends up with none. Attribution is recomputed from the package's own
`_amplitude_mature_bounds` and the same extrema filter the detector runs.

| code | mechanism | file:line |
|---|---|---|
| A | generating z valley or a flanking z peak cut by the relative prominence filter, so no candidate forms | `determine_periods.py:203-208`, `find_stages.py:261-262` |
| B | a candidate forms but the amplitude window collapses to the valley alone (<= 1 step), and is cleared one step later | `find_stages.py:135-160` |
| C | `threshold_mature_length` duration check | `find_stages.py:304-312` - **unreachable under `mature_method='amplitude'`** |
| D | window formed, neighbour check cleared it | `find_stages.py:340-352` |

**402 (cell, series) losses over 42 distinct series.**

378 of them are the degenerate `mature_amplitude_fraction=1.00`
column, where the level equals `z` at the valley and every window
collapses to a single step. That column is reported separately: it says
nothing about the trade-off under investigation.

### `mature_amplitude_fraction` < 1.00 - the informative cells

24 (cell, series) losses over 2 distinct series. Distinct series by code: **A** 2, **B** 0, **C** 0, **D** 0

| series | src | code | cells | prom_rel range | maf range | detail |
|---|---|---|---|---|---|---|
| `20191014` | real | A | 16 | 0.45-0.60 | 0.80-0.95 | no surviving z valley with a flanking z peak on each side |
| `scfcf1387` | syn | A | 8 | 0.55-0.60 | 0.80-0.95 | no surviving z valley with a flanking z peak on each side |

### `mature_amplitude_fraction` = 1.00 - the degenerate column

378 (cell, series) losses over 42 distinct series. Distinct series by code: **A** 2, **B** 40, **C** 0, **D** 2

| series | src | code | cells | prom_rel range | maf range | detail |
|---|---|---|---|---|---|---|
| `20150069` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20150436` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20150528` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20150656` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 2 candidate(s), every amplitude window collapsed to the valley alone (lengths [1, 1]) |
| `20160587` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20160735` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20170154` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20170342` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20170409` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20170520` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20170794` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 2 candidate(s), every amplitude window collapsed to the valley alone (lengths [1, 1]) |
| `20171179` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180170` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180263` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180300` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180608` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180628` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180733` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20180759` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20181046` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20190325` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20190397` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20190639` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20190870` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20190879` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20191014` | real | A/B | 9 | 0.20-0.60 | 1.00-1.00 | no surviving z valley with a flanking z peak on each side |
| `20191104` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20191155` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20201245` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20202023` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20203947` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 2 candidate(s), every amplitude window collapsed to the valley alone (lengths [1, 1]) |
| `20205386` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `20207822` | real | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `s46657891` | syn | D | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate window(s) formed (lengths [34]), all cleared by the intensification/decay neighbour check |
| `s4e7ff65c` | syn | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `s6b1e8245` | syn | D | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate window(s) formed (lengths [26]), all cleared by the intensification/decay neighbour check |
| `s6b542eee` | syn | B | 9 | 0.20-0.60 | 1.00-1.00 | 2 candidate(s), every amplitude window collapsed to the valley alone (lengths [1, 1]) |
| `s8001f17b` | syn | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `s9ddbc53c` | syn | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `sbceec644` | syn | B | 9 | 0.20-0.60 | 1.00-1.00 | 1 candidate(s), every amplitude window collapsed to the valley alone (lengths [1]) |
| `sbd6c6920` | syn | B | 9 | 0.20-0.60 | 1.00-1.00 | 2 candidate(s), every amplitude window collapsed to the valley alone (lengths [1, 1]) |
| `scfcf1387` | syn | A/B | 9 | 0.20-0.60 | 1.00-1.00 | no surviving z valley with a flanking z peak on each side |

