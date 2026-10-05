# Passo 1 — higiene do novo default (treino)

Gerado por `passo1/hygiene_train.py` (definições em `passo1/PREVISOES.md`). Sem pontuação contra rótulos. `cyclophaser.__file__` = `cyclophaser/__init__.py` (relativo à raiz; assert no processo).

| medida | default (reflect) | edge |
|---|---|---|
| exceptions | 0 | 0 |
| invalid_sequences | 0 | 0 |
| refusals | 28 | 28 |
| defect_I | 11 | 10 |
| dz_t0_rel_zero | 0 | 0 |
| dz_t0_rel_median | 0.065 | 0.295 |
| dz_t0_rel_max | 0.172 | 0.802 |

Séries de treino: **54** (batch swell_item30: 7, top-level real: 35, top-level synthetic: 12). Mapas de fase que mudam entre default e edge: **19**; sequências que mudam: **3**.
Recusas de incipient — default: ['19810854', '19860380', '19940445', '20050893', '20120297', '20150069', '20150528', '20150532', '20150656', '20160587', '20160735', '20170342', '20170520', '20170760', '20170794', '20171179', '20180263', '20180300', '20180628', '20180733', '20181046', '20190879', '20191104', '20201245', '20202023', '20207822', 's5b8aa46f', 's8001f17b']; edge: ['19810854', '19860380', '19940445', '20050893', '20120297', '20150069', '20150528', '20150532', '20150656', '20160587', '20160735', '20170342', '20170520', '20170760', '20170794', '20171179', '20180263', '20180300', '20180628', '20180733', '20181046', '20190879', '20191104', '20201245', '20202023', '20207822', 's5b8aa46f', 's8001f17b'].
Defeito I — default: ['19790612', '19810854', '19870927', '19940445', '20180170', '20180608', '20180759', '20190325', '20190397', '20203947', 'scfcf1387']; edge: ['19790612', '19810854', '19870927', '20180170', '20180608', '20180759', '20190325', '20190397', '20191014', 'scfcf1387'].

| id | grupo | n | exceção (d/e) | válida (d/e) | recusa (d/e) | mapa muda | defeito I (d/e) | |dz|t0 rel (d/e) | sequência default | sequência edge |
|---|---|---|---|---|---|---|---|---|---|---|
| `19790612` | batch swell_item30 | 48 | não/não | sim/sim | não/não | não | sim/sim | 0.006/0.040 | incipient > decay | incipient > decay |
| `19810854` | batch swell_item30 | 72 | não/não | sim/sim | sim/sim | não | sim/sim | 0.080/0.370 | intensification > mature > decay | intensification > mature > decay |
| `19860380` | batch swell_item30 | 45 | não/não | sim/sim | sim/sim | sim | não/não | 0.015/0.460 | intensification > mature > decay | intensification > mature > decay |
| `19870927` | batch swell_item30 | 92 | não/não | sim/sim | não/não | sim | sim/sim | 0.061/0.250 | incipient > intensification > mature > decay > intensification > mature > decay | incipient > intensification > mature > decay > intensification > mature > decay |
| `19940445` | batch swell_item30 | 47 | não/não | sim/sim | sim/sim | não | sim/não | 0.012/0.009 | intensification > mature > decay | intensification > mature > decay |
| `20050893` | batch swell_item30 | 56 | não/não | sim/sim | sim/sim | sim | não/não | 0.137/0.633 | intensification > mature > decay | intensification > mature > decay |
| `20120297` | batch swell_item30 | 40 | não/não | sim/sim | sim/sim | não | não/não | 0.063/0.296 | intensification > mature > decay > residual | intensification > mature > decay > residual |
| `20150069` | top-level real | 66 | não/não | sim/sim | sim/sim | não | não/não | 0.114/0.476 | intensification > mature > decay | intensification > mature > decay |
| `20150436` | top-level real | 112 | não/não | sim/sim | não/não | não | não/não | 0.018/0.041 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20150528` | top-level real | 51 | não/não | sim/sim | sim/sim | não | não/não | 0.067/0.335 | intensification > mature > decay | intensification > mature > decay |
| `20150532` | top-level real | 107 | não/não | sim/sim | sim/sim | não | não/não | 0.080/0.550 | intensification > mature > decay | intensification > mature > decay |
| `20150656` | top-level real | 160 | não/não | sim/sim | sim/sim | sim | não/não | 0.046/0.078 | intensification > mature > decay > intensification > mature > decay | intensification > mature > decay > intensification > mature > decay |
| `20160587` | top-level real | 79 | não/não | sim/sim | sim/sim | sim | não/não | 0.060/0.182 | intensification > mature > decay | intensification > mature > decay |
| `20160735` | top-level real | 259 | não/não | sim/sim | sim/sim | sim | não/não | 0.114/0.774 | intensification > decay > intensification > mature > decay > residual | intensification > decay > intensification > decay > intensification > mature > decay > residual |
| `20170154` | top-level real | 124 | não/não | sim/sim | não/não | sim | não/não | 0.063/0.150 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20170342` | top-level real | 146 | não/não | sim/sim | sim/sim | não | não/não | 0.105/0.635 | intensification > mature > decay > residual | intensification > mature > decay > residual |
| `20170409` | top-level real | 169 | não/não | sim/sim | não/não | sim | não/não | 0.029/0.012 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20170520` | top-level real | 58 | não/não | sim/sim | sim/sim | não | não/não | 0.114/0.456 | intensification > mature > decay | intensification > mature > decay |
| `20170760` | top-level real | 59 | não/não | sim/sim | sim/sim | não | não/não | 0.172/0.802 | intensification > decay | intensification > decay |
| `20170794` | top-level real | 224 | não/não | sim/sim | sim/sim | não | não/não | 0.041/0.066 | intensification > mature > decay > residual | intensification > mature > decay > residual |
| `20171179` | top-level real | 62 | não/não | sim/sim | sim/sim | não | não/não | 0.064/0.344 | intensification > mature > decay | intensification > mature > decay |
| `20180170` | top-level real | 69 | não/não | sim/sim | não/não | sim | sim/sim | 0.011/0.003 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20180263` | top-level real | 57 | não/não | sim/sim | sim/sim | sim | não/não | 0.074/0.457 | intensification > mature > decay > residual | intensification > mature > decay > residual |
| `20180300` | top-level real | 59 | não/não | sim/sim | sim/sim | não | não/não | 0.129/0.667 | intensification > mature > decay | intensification > mature > decay |
| `20180608` | top-level real | 117 | não/não | sim/sim | não/não | não | sim/sim | 0.026/0.121 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20180628` | top-level real | 94 | não/não | sim/sim | sim/sim | não | não/não | 0.068/0.240 | intensification > mature > decay > intensification > mature > decay | intensification > mature > decay > intensification > mature > decay |
| `20180733` | top-level real | 257 | não/não | sim/sim | sim/sim | não | não/não | 0.112/0.408 | intensification > mature > decay > intensification > mature > decay | intensification > mature > decay > intensification > mature > decay |
| `20180759` | top-level real | 88 | não/não | sim/sim | não/não | não | sim/sim | 0.049/0.078 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20181046` | top-level real | 30 | não/não | sim/sim | sim/sim | sim | não/não | 0.082/0.459 | intensification | intensification > mature > decay |
| `20190325` | top-level real | 167 | não/não | sim/sim | não/não | não | sim/sim | 0.005/0.155 | incipient > intensification > decay > intensification > mature > decay | incipient > intensification > decay > intensification > mature > decay |
| `20190397` | top-level real | 56 | não/não | sim/sim | não/não | não | sim/sim | 0.051/0.136 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20190639` | top-level real | 180 | não/não | sim/sim | não/não | sim | não/não | 0.050/0.294 | incipient > decay > intensification > mature > decay | incipient > decay > intensification > mature > decay |
| `20190870` | top-level real | 129 | não/não | sim/sim | não/não | sim | não/não | 0.049/0.048 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20190879` | top-level real | 79 | não/não | sim/sim | sim/sim | não | não/não | 0.131/0.630 | intensification > mature > decay | intensification > mature > decay |
| `20191014` | top-level real | 206 | não/não | sim/sim | não/não | sim | não/sim | 0.039/0.057 | incipient > intensification > mature > decay > residual | incipient > intensification > mature > decay > residual |
| `20191104` | top-level real | 118 | não/não | sim/sim | sim/sim | não | não/não | 0.100/0.587 | intensification > mature > decay | intensification > mature > decay |
| `20191155` | top-level real | 93 | não/não | sim/sim | não/não | sim | não/não | 0.079/0.281 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `20201245` | top-level real | 98 | não/não | sim/sim | sim/sim | não | não/não | 0.094/0.668 | intensification > mature > decay | intensification > mature > decay |
| `20202023` | top-level real | 78 | não/não | sim/sim | sim/sim | não | não/não | 0.050/0.378 | intensification > mature > decay | intensification > mature > decay |
| `20203947` | top-level real | 242 | não/não | sim/sim | não/não | não | sim/não | 0.003/0.407 | incipient > intensification > decay > intensification > decay > intensification > mature > decay > intensification > mature > decay > residual | incipient > intensification > decay > intensification > decay > intensification > mature > decay > intensification > mature > decay > residual |
| `20205386` | top-level real | 100 | não/não | sim/sim | não/não | sim | não/não | 0.128/0.359 | incipient > intensification > mature > decay > intensification > mature > decay | incipient > intensification > mature > decay > intensification > mature > decay > intensification > mature > decay |
| `20207822` | top-level real | 162 | não/não | sim/sim | sim/sim | sim | não/não | 0.111/0.498 | intensification > mature > decay | intensification > mature > decay |
| `s0596ea57` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | —/— | 0.002/0.025 | incipient > intensification | incipient > intensification |
| `s46657891` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | não/não | 0.049/0.098 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `s4e7ff65c` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | —/— | 0.030/0.006 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `s5b8aa46f` | top-level synthetic | 66 | não/não | sim/sim | sim/sim | não | não/não | 0.150/0.677 | decay > intensification > mature > decay > residual | decay > intensification > mature > decay > residual |
| `s5dcc0f79` | top-level synthetic | 66 | não/não | sim/sim | não/não | sim | —/— | 0.047/0.018 | incipient > intensification > mature > decay > residual | incipient > intensification > mature > decay > residual |
| `s6b1e8245` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | não/não | 0.095/0.247 | incipient > decay > intensification > mature > decay | incipient > decay > intensification > mature > decay |
| `s6b542eee` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | não/não | 0.125/0.369 | incipient > intensification > mature > decay > intensification > mature > decay | incipient > intensification > mature > decay > intensification > mature > decay |
| `s8001f17b` | top-level synthetic | 66 | não/não | sim/sim | sim/sim | não | não/não | 0.147/0.680 | decay > intensification > mature > decay | decay > intensification > mature > decay |
| `s9ddbc53c` | top-level synthetic | 66 | não/não | sim/sim | não/não | sim | não/não | 0.047/0.039 | incipient > intensification > mature > decay > residual | incipient > intensification > mature > decay > residual |
| `sbceec644` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | não/não | 0.068/0.138 | incipient > intensification > mature > decay | incipient > intensification > mature > decay |
| `sbd6c6920` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | não/não | 0.071/0.130 | incipient > intensification > mature > decay > intensification > mature > decay | incipient > intensification > mature > decay > intensification > mature > decay |
| `scfcf1387` | top-level synthetic | 66 | não/não | sim/sim | não/não | não | sim/sim | 0.108/0.304 | incipient > decay > intensification > mature > decay > residual | incipient > decay > intensification > mature > decay > residual |
