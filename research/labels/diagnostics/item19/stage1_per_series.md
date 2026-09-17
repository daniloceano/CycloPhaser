# Stage 1 - per-series scoring under `params-10` (TRAIN only)

Config: `research/labels/configs/cyclophaser_params-10.yaml` (`prominence_relative=0.3`, `mature_amplitude_fraction=0.95`).

`seq` = detected phase sequence equals the labelled one. `incip` = number of
leading `incipient` steps the detector produced (`-` = step 0 is not incipient),
next to the label's own incipient end. `n_mat` = contiguous detected mature
blocks. `Dstart`/`Dend` = detected minus labelled mature boundary, in steps,
for the detected block with the largest overlap with the labelled mature.
`hit` = both within the fixed margin of 6 (item 17(d)).

| series | src | n | seq | incip det/lab | n_mat | Dstart | Dend | hit |
|---|---|---|---|---|---|---|---|---|
| `20150069` | real | 66 | yes | - / - | 1 | 3 | -3 | yes |
| `20150436` | real | 112 | yes | 20 / 16 | 1 | 1 | -7 | no |
| `20150528` | real | 51 | yes | - / - | 1 | 1 | -2 | yes |
| `20150532` | real | 107 | yes | - / - | 1 | 0 | 0 | yes |
| `20150656` | real | 160 | NO | - / - | 2 | 3 | -6 | yes |
| `20160587` | real | 79 | NO | - / 26 | 1 | 1 | -1 | yes |
| `20160735` | real | 259 | NO | - / 19 | 4 | 9 | -11 | no |
| `20170154` | real | 124 | yes | 6 / 6 | 1 | 6 | -34 | no |
| `20170342` | real | 146 | NO | - / - | 1 | 3 | -8 | no |
| `20170409` | real | 169 | yes | 6 / 6 | 1 | 6 | -8 | no |
| `20170520` | real | 58 | yes | - / - | 1 | 1 | -2 | yes |
| `20170760` | real | 59 | NO | - / - | 0 | - | - | no |
| `20170794` | real | 224 | NO | - / - | 2 | 3 | -6 | yes |
| `20171179` | real | 62 | NO | - / 11 | 1 | - | - | no |
| `20180170` | real | 69 | NO | 8 / 20 | 1 | 3 | 3 | yes |
| `20180263` | real | 57 | yes | - / - | 1 | 2 | -3 | yes |
| `20180300` | real | 59 | yes | - / - | 1 | 3 | -1 | yes |
| `20180608` | real | 117 | yes | 38 / 37 | 1 | 2 | -4 | yes |
| `20180628` | real | 94 | NO | - / 9 | 2 | 2 | -7 | no |
| `20180733` | real | 257 | NO | - / - | 2 | 8 | -6 | no |
| `20180759` | real | 88 | yes | 4 / 4 | 1 | -1 | 0 | yes |
| `20181046` | real | 30 | NO | - / 9 | 1 | - | - | no |
| `20190325` | real | 167 | NO | 9 / 10 | 1 | 6 | -5 | yes |
| `20190397` | real | 56 | yes | 2 / 8 | 1 | -3 | 0 | yes |
| `20190639` | real | 180 | yes | 13 / 25 | 1 | 9 | -6 | no |
| `20190870` | real | 129 | yes | 10 / 12 | 1 | 0 | -6 | yes |
| `20190879` | real | 79 | yes | - / - | 1 | 0 | -3 | yes |
| `20191014` | real | 206 | NO | 9 / - | 1 | 92 | 71 | no |
| `20191104` | real | 118 | yes | - / - | 1 | 4 | -4 | yes |
| `20191155` | real | 93 | NO | 1 / - | 1 | 0 | -1 | yes |
| `20201245` | real | 98 | yes | - / - | 1 | 0 | -1 | yes |
| `20202023` | real | 78 | NO | - / 11 | 1 | 0 | -1 | yes |
| `20203947` | real | 242 | NO | 12 / 38 | 4 | 8 | -9 | no |
| `20205386` | real | 100 | NO | 4 / 5 | 3 | 4 | -2 | yes |
| `20207822` | real | 162 | yes | - / - | 1 | 4 | -11 | no |
| `s0596ea57` | syn | 66 | yes | 10 / 14 | 0 | - | - | no |
| `s46657891` | syn | 66 | yes | 3 / 3 | 1 | 3 | -3 | yes |
| `s4e7ff65c` | syn | 66 | yes | 5 / 5 | 1 | 2 | -3 | yes |
| `s5b8aa46f` | syn | 66 | yes | - / - | 1 | 3 | -1 | yes |
| `s5dcc0f79` | syn | 66 | yes | 5 / 4 | 1 | 3 | -2 | yes |
| `s6b1e8245` | syn | 66 | yes | 2 / 3 | 1 | 2 | -2 | yes |
| `s6b542eee` | syn | 66 | yes | 2 / 2 | 2 | 1 | 0 | yes |
| `s8001f17b` | syn | 66 | yes | - / - | 1 | 2 | -2 | yes |
| `s9ddbc53c` | syn | 66 | yes | 4 / 3 | 1 | 1 | -1 | yes |
| `sbceec644` | syn | 66 | yes | 2 / 3 | 1 | 1 | 0 | yes |
| `sbd6c6920` | syn | 66 | yes | 4 / 5 | 2 | 2 | -2 | yes |
| `scfcf1387` | syn | 66 | yes | 2 / 3 | 1 | 2 | -2 | yes |

## Totals by source

| set | n | sequence match | mature within +-6 both ends | no mature at all | >1 mature block |
|---|---|---|---|---|---|
| real | 35 | 18/35 | 21/35 | 1 | 7 |
| synthetic | 12 | 12/12 | 11/12 | 1 | 2 |
| ALL | 47 | 30/47 | 32/47 | 2 | 9 |
