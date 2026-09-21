# Front 20(c) stage 1 - anchor tables

config sha256: 39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3
numpy 2.5.3  scipy 1.18.0  pandas 3.0.5
duration convention: end - start + 1

## Series with more than one mature block under params-12: 7

### real (5 of 35 in train)

| series | block | start | end | dur | valley | D1 | label matched | d_start | d_end | ratio/A | ratio/B | ratio/C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20150656 | 0 [ABC] | 34 | 48 | 15 | v42 | 1.0000 | L0 | 0 | -4 | 1.000 | 1.000 | 1.000 |
| 20150656 | 1 | 140 | 147 | 8 | v143 | 0.8351 | - | - | - | 0.533 | 0.533 | 0.533 |
| 20150656 | *labels* | [[34, 52]] unsure=[False] | | | | | | | | | | |
| 20180628 | 0 [ABC] | 29 | 40 | 12 | v37 | 1.0000 | L0 | -1 | -6 | 1.000 | 1.000 | 1.000 |
| 20180628 | 1 | 70 | 75 | 6 | v72 | 0.9980 | - | - | - | 0.500 | 0.500 | 0.500 |
| 20180628 | *labels* | [[30, 46]] unsure=[False] | | | | | | | | | | |
| 20180733 | 0 [B] | 31 | 43 | 13 | v37 | 0.9303 | - | - | - | 1.083 | 1.000 | 1.083 |
| 20180733 | 1 [AC] | 135 | 146 | 12 | v140 | 1.0000 | L0 | 6 | -4 | 1.000 | 0.923 | 1.000 |
| 20180733 | *labels* | [[129, 150]] unsure=[False] | | | | | | | | | | |
| 20203947 | 0 [AB] | 129 | 136 | 8 | v132 | 1.0000 | - | - | - | 1.000 | 1.000 | 1.000 |
| 20203947 | 1 [C] | 181 | 188 | 8 | v185 | 0.9422 | L1 | 3 | 0 | 1.000 | 1.000 | 1.000 |
| 20203947 | *labels* | [[122, 144], [178, 188]] unsure=[False, True] | | | | | | | | | | |
| 20205386 | 0 [B] | 36 | 42 | 7 | v41 | 0.8687 | - | - | - | 1.167 | 1.000 | 1.750 |
| 20205386 | 1 [C] | 60 | 63 | 4 | v61 | 0.8805 | L0 | 4 | -1 | 0.667 | 0.571 | 1.000 |
| 20205386 | 2 [A] | 80 | 85 | 6 | v82 | 1.0000 | - | - | - | 1.000 | 0.857 | 1.500 |
| 20205386 | *labels* | [[56, 64]] unsure=[False] | | | | | | | | | | |

### synthetic (2 of 12 in train)

| series | block | start | end | dur | valley | D1 | label matched | d_start | d_end | ratio/A | ratio/B | ratio/C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s6b542eee | 0 [BC] | 12 | 19 | 8 | v16 | 0.9999 | L0 | 0 | 1 | 1.000 | 1.000 | 1.000 |
| s6b542eee | 1 [A] | 44 | 51 | 8 | v48 | 1.0000 | L1 | 1 | 0 | 1.000 | 1.000 | 1.000 |
| s6b542eee | *labels* | [[12, 18], [43, 51]] unsure=[False, False] | | | | | | | | | | |
| sbd6c6920 | 0 [ABC] | 14 | 20 | 7 | v17 | 1.0000 | L0 | 1 | -1 | 1.000 | 1.000 | 1.000 |
| sbd6c6920 | 1 | 45 | 51 | 7 | v48 | 0.9922 | L1 | 2 | -1 | 1.000 | 1.000 | 1.000 |
| sbd6c6920 | *labels* | [[13, 21], [43, 52]] unsure=[False, False] | | | | | | | | | | |

## Anchor divergence

| series | A (max D1) | B (max duration) | C (label-matched) | A==B | A==C | B==C |
|---|---|---|---|---|---|---|
| 20150656 | block 0 (34,48) | block 0 (34,48) | block 0 (34,48) | yes | yes | yes |
| 20180628 | block 0 (29,40) | block 0 (29,40) | block 0 (29,40) | yes | yes | yes |
| 20180733 | block 1 (135,146) | block 0 (31,43) | block 1 (135,146) | NO | yes | NO |
| 20203947 | block 0 (129,136) | block 0 (129,136) | block 1 (181,188) | yes | NO | NO |
| 20205386 | block 2 (80,85) | block 0 (36,42) | block 1 (60,63) | NO | NO | NO |
| s6b542eee | block 1 (44,51) | block 0 (12,19) | block 0 (12,19) | NO | NO | yes |
| sbd6c6920 | block 0 (14,20) | block 0 (14,20) | block 0 (14,20) | yes | yes | yes |

Series where the anchors do not all agree: ['20180733', '20203947', '20205386', 's6b542eee']

## Usable band for a proportional floor r

A floor r rejects a non-anchor block when ratio < r. For each anchor
definition, the constraints are:
  - r must EXCEED the ratio of every spurious (label-unmatched) block that
    must be removed;
  - r must NOT exceed the ratio of any label-matched block.

### Anchor A
- spurious non-anchor blocks (ratio): 20205386#0=1.167, 20180733#0=1.083, 20150656#1=0.533, 20180628#1=0.500
  -> to remove ALL of them, r > 1.1667
- label-matched non-anchor blocks (ratio): 20205386#1=0.667, 20203947#1=1.000, s6b542eee#0=1.000, sbd6c6920#1=1.000
  -> to preserve ALL of them, r <= 0.6667
- BAND: (1.1667, 0.6667] -> EMPTY
- UNREACHABLE: 20203947: block 0 is spurious AND is the anchor -> can never be removed
- UNREACHABLE: 20205386: block 2 is spurious AND is the anchor -> can never be removed

### Anchor B
- spurious non-anchor blocks (ratio): 20205386#2=0.857, 20150656#1=0.533, 20180628#1=0.500
  -> to remove ALL of them, r > 0.8571
- label-matched non-anchor blocks (ratio): 20205386#1=0.571, 20180733#1=0.923, 20203947#1=1.000, s6b542eee#1=1.000, sbd6c6920#1=1.000
  -> to preserve ALL of them, r <= 0.5714
- BAND: (0.8571, 0.5714] -> EMPTY
- UNREACHABLE: 20180733: block 0 is spurious AND is the anchor -> can never be removed
- UNREACHABLE: 20203947: block 0 is spurious AND is the anchor -> can never be removed
- UNREACHABLE: 20205386: block 0 is spurious AND is the anchor -> can never be removed

### Anchor C
- spurious non-anchor blocks (ratio): 20205386#0=1.750, 20205386#2=1.500, 20180733#0=1.083, 20203947#0=1.000, 20150656#1=0.533, 20180628#1=0.500
  -> to remove ALL of them, r > 1.7500
- label-matched non-anchor blocks (ratio): s6b542eee#1=1.000, sbd6c6920#1=1.000
  -> to preserve ALL of them, r <= 1.0000
- BAND: (1.7500, 1.0000] -> EMPTY


## Stage-1 gate, criterion by criterion

### Anchor A (max D1)

- **(a)** remove both spurious blocks of 20205386: anchor is block 2 (SPURIOUS - can never be removed); spurious blocks = [0, 2]. -> **FAIL**
- **(b)/(c)/(d)** cost-free floors exist: r in (0.5333, 0.6667]
  - at the widest such floor, blocks removed: [('20150656', 1, None), ('20180628', 1, None)]
  - series improved: ['20150656', '20180628']
  - **(e)** generalises beyond 20205386: **PASS** (other series helped: ['20150656', '20180628'])

### Anchor B (max duration)

- **(a)** remove both spurious blocks of 20205386: anchor is block 0 (SPURIOUS - can never be removed); spurious blocks = [0, 2]. -> **FAIL**
- **(b)/(c)/(d)** cost-free floors exist: r in (0.5333, 0.5714]
  - at the widest such floor, blocks removed: [('20150656', 1, None), ('20180628', 1, None)]
  - series improved: ['20150656', '20180628']
  - **(e)** generalises beyond 20205386: **PASS** (other series helped: ['20150656', '20180628'])

### Verdict

The gate requires (a)-(e) to hold together for at least one of anchors A or B.
(a) fails under both, so the stage-1 verdict is **FAIL** regardless of the rest.
