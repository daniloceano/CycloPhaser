# series_sha256 diagnostic report

Diagnosis only — no label, no split.yaml, and no recorded series_sha256
was modified to produce this report.

## Routes found (`git grep -n series_sha256`)

| file:line | what it computes, over what object, when |
|---|---|
| `research/labels/labels_core.py:105` (`series_sha256`) | The only hash function in the repo: `hashlib.sha256(np.asarray(values, dtype="float64").tobytes()).hexdigest()`. Values only — no index, no dtype name, no metadata. |
| `research/labels/labels_core.py:376` (`make_label_record`) | **WRITE.** Calls `series_sha256(values)` at the moment a label is saved, where `values` is whatever the caller passed in untouched. |
| `tools/calibration_app/label_tab.py:830,845,966` | The labelling UI's copy of WRITE. `values = series[sid]` (830) comes from `_load_population()` (698-709) = `lc.load_real_series()` / `lc.load_synthetic_series()`, merged, with **no further transformation**. Hashed again at 845 (the in-session "stale" banner) and passed to `make_label_record` at 966 (actual save). Verified by reading the source: this is the same two loader calls as VERIFY below, not a separate implementation. |
| `research/labels/evaluate_against_labels.py:221-229` | **VERIFY.** `series = {**load_real_series(), **load_synthetic_series()}`, then `series_sha256(series[sid])` compared against the recorded value; mismatches collected into `stale` and excluded with a warning. |
| `tests/test_manual_labels.py:1129-1140` | **VERIFY (pytest).** Same two loader calls, same comparison, as a hard `assert` per training label — this is what fails under `pytest` for 12/47 train labels. |
| `research/labels/labels_core.py:138-180` (`load_real_series`, `load_synthetic_series`) | The loaders both WRITE and VERIFY call. Real: `pd.read_csv(sep=";", index_col="time", parse_dates=True)` per CSV in `tests/calibration_data/`. Synthetic: dynamic `importlib` exec of `tests/synthetic/cases.py` by file path, reading `CASES[name]["series"]`, `.astype("float64")`. |
| `tools/calibration_app/app.py:62` (`_load_synthetic_cases`) | **Unrelated third route** — materialises the same 12 synthetic cases as CSV bytes for the main Calibration tab's detector preview. `git grep -n series_sha256` confirms this function is never on the hash read/write path. Included below only as a control (`app_csv_roundtrip`). |

WRITE and VERIFY are, by construction, the same two function calls (`load_real_series` + `load_synthetic_series`) — there is only one live loading route per population in the code that exists today, not two.

## Conclusion

**(a) Are the values numerically identical between the two routes today?** Yes, trivially — WRITE and VERIFY are the same function calls, and this script confirms `max|Δ| == 0`, `n_diff == 0` between them for all 15 sampled ids, real and synthetic alike. There is no live divergence between two loading code paths in the current codebase.

**(b) If so, what field differs?** Nothing does, between WRITE and VERIFY today — see (a). The actual discrepancy is between *either* route computed today and the hash recorded in `manual_labels.yaml` on 2026-09-08. That comparison cannot identify a differing *field* in the sense of dtype/index/contiguity/serialisation: none of the 11 alternative byte encodings tried (float32, big-endian, index-inclusive, rounded, CSV text via the app.py route, repr/str text, Fortran order, plain `.tobytes()`) reproduces the recorded hash for any of the 12 synthetic ids (see the table above). `git diff` confirms `tests/synthetic/cases.py` and `generators.py` are byte-identical between the commit that predates labelling (`f80c2f6`, 2026-09-04) and HEAD, and the recorded hash is also stable across four numpy versions tested on this machine (1.26.4, 2.1.2, 2.4.0, 2.5.3 — spanning the pre-/post-2.0 BLAS-backend split). So this script cannot attribute the difference to any of dtype, index, contiguity, serialisation, numpy version, or a code change on this branch.

**(c) Is the recorded hash reproduced by either route, and which?** No. For all 12 synthetic ids, `recorded_eq_write` and `recorded_eq_verify` are both False, and no alternative encoding matches either (`any_encoding_matches_recorded` is False for all 12). For all 3 real controls, recorded == write == verify == canonical, exactly as expected.

**Scenario: P3** — no route or encoding examined reproduces the recorded hash for the 12 synthetic labels. This is not evidence of two silently-diverging loading routes (P1 is refuted: WRITE and VERIFY agree perfectly with each other today), and it cannot be reduced to genuinely-different numeric values either (P2), since a sha256 mismatch alone cannot distinguish "different values" from "same values, an encoding this script did not try" — the original 2026-09-08 array is not recoverable from a hash. What the measurement rules out: the current code (single loader per population, unchanged since before labelling), the numpy version, and the 11 encodings tried are all NOT the explanation. That leaves something about the environment or process that produced the 2026-09-08 labelling session's synthetic data that is not reproducible from this repository's current state — for instance, a long-lived `st.cache_data` cache in a Streamlit session serving a synthetic snapshot pre-dating a local edit that was never committed. That process no longer exists to inspect, so this cannot be confirmed further; it is the open question left for Danilo's decision (see the orchestration summary).

## Summary

- synthetic ids sampled: 12
- of those, WRITE route == VERIFY route today (max|Δ| == 0, byte-identical): 12 / 12
- of those, recorded hash reproduced by WRITE or VERIFY route today: 0 / 12
- of those, recorded hash reproduced by ANY of the 11 alternative byte encodings tried: 0 / 12

## Per-id table

| id | source | case_name | len | dtype | C-contig | recorded (12) | write (12) | verify (12) | canonical (12) | max\|Δ\| write vs verify | n_diff | any encoding matches recorded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0596ea57 | synthetic | IcIt_observational | 66 | float64 | True | 78ae091842bc | 15cce43e9556 | 15cce43e9556 | 15cce43e9556 | 0.000e+00 | 0 | False |
| s46657891 | synthetic | quase_ItD | 66 | float64 | True | e0fe1e0a8598 | 7da0c5496516 | 7da0c5496516 | 7da0c5496516 | 0.000e+00 | 0 | False |
| s4e7ff65c | synthetic | ItMD_clean | 66 | float64 | True | 8ef970c54d89 | 821f1e7a56a0 | 821f1e7a56a0 | 821f1e7a56a0 | 0.000e+00 | 0 | False |
| s5b8aa46f | synthetic | DItMD_residual_noisy | 66 | float64 | True | 4dbf8e04ab28 | 90ce58dba437 | 90ce58dba437 | 90ce58dba437 | 0.000e+00 | 0 | False |
| s5dcc0f79 | synthetic | IcItMD_residual_clean | 66 | float64 | True | 9454fe8e2b34 | 8434ba71b30a | 8434ba71b30a | 8434ba71b30a | 0.000e+00 | 0 | False |
| s6b1e8245 | synthetic | IcDItMD_noisy | 66 | float64 | True | c3f0600e92b6 | 72c2a1d8ca8e | 72c2a1d8ca8e | 72c2a1d8ca8e | 0.000e+00 | 0 | False |
| s6b542eee | synthetic | ItMD_ItMD_noisy | 66 | float64 | True | 6ad904a1a64d | 0e67659759cc | 0e67659759cc | 0e67659759cc | 0.000e+00 | 0 | False |
| s8001f17b | synthetic | DItMD_noisy | 66 | float64 | True | 284cd8141059 | 69843d633318 | 69843d633318 | 69843d633318 | 0.000e+00 | 0 | False |
| s9ddbc53c | synthetic | IcItMD_residual_noisy | 66 | float64 | True | af5e3fb08414 | 7d17e21a46ed | 7d17e21a46ed | 7d17e21a46ed | 0.000e+00 | 0 | False |
| sbceec644 | synthetic | ItMD_noisy | 66 | float64 | True | 0443afab2618 | 5fdeefa9c329 | 5fdeefa9c329 | 5fdeefa9c329 | 0.000e+00 | 0 | False |
| sbd6c6920 | synthetic | IcItMD_ItMD_noisy | 66 | float64 | True | eb4f2989b871 | 7c439c8b28fa | 7c439c8b28fa | 7c439c8b28fa | 0.000e+00 | 0 | False |
| scfcf1387 | synthetic | IcDItMD_residual_noisy | 66 | float64 | True | f315cb99c453 | 37d0012719b7 | 37d0012719b7 | 37d0012719b7 | 0.000e+00 | 0 | False |
| 20150069 | real |  | 66 | float64 | True | 7231f13dd908 | 7231f13dd908 | 7231f13dd908 | 7231f13dd908 | 0.000e+00 | 0 | True |
| 20150377 | real |  | 113 | float64 | True | 50b48d08248d | 50b48d08248d | 50b48d08248d | 50b48d08248d | 0.000e+00 | 0 | True |
| 20150436 | real |  | 112 | float64 | True | cd5783d0e292 | cd5783d0e292 | cd5783d0e292 | cd5783d0e292 | 0.000e+00 | 0 | True |

## First / last 3 values (full precision)

### s0596ea57 (synthetic, IcIt_observational)
- first3: ['-0.0001', '-0.0001', '-0.0001']
- last3:  ['-0.0006983004400630411', '-0.0006995748087030286', '-0.0007']

### s46657891 (synthetic, quase_ItD)
- first3: ['-0.0001', '-0.00010192610933112124', '-0.00010768588783870784']
- last3:  ['-0.00010768588783870788', '-0.00010192610933112132', '-0.00010000000000000005']

### s4e7ff65c (synthetic, ItMD_clean)
- first3: ['-0.0001', '-0.0001', '-0.0001']
- last3:  ['-0.00010607689879511676', '-0.00010152212076330186', '-0.00010000000000000005']

### s5b8aa46f (synthetic, DItMD_residual_noisy)
- first3: ['-0.0008969751458913034', '-0.000819475086174803', '-0.0007288312389164925']
- last3:  ['-0.0004908476047947674', '-0.00048687434623917653', '-0.0005170614337946386']

### s5dcc0f79 (synthetic, IcItMD_residual_clean)
- first3: ['-0.0001', '-0.0001', '-0.0001']
- last3:  ['-0.0004931851652578137', '-0.0004982889722747622', '-0.0005']

### s6b1e8245 (synthetic, IcDItMD_noisy)
- first3: ['-0.0008944706529269634', '-0.0008800433495775421', '-0.0008677018985428081']
- last3:  ['-0.00013255105381552337', '-0.00010053226905991452', '-0.00010746799387007687']

### s6b542eee (synthetic, ItMD_ItMD_noisy)
- first3: ['-0.00011042865844178704', '-0.00011441874970679163', '-0.0001191980058764569']
- last3:  ['-0.00013181065188004967', '-0.00010905477336046988', '-9.493634337152644e-05']

### s8001f17b (synthetic, DItMD_noisy)
- first3: ['-0.0008944706529269634', '-0.0007979652208150925', '-0.000716935229003288']
- last3:  ['-0.00012590599225364537', '-9.885891811768872e-05', '-0.00010746799387007687']

### s9ddbc53c (synthetic, IcItMD_residual_noisy)
- first3: ['-9.51245267239291e-05', '-0.00011663974569984793', '-8.799278086709669e-05']
- last3:  ['-0.00048380560795606523', '-0.0004869093469980765', '-0.0004873064442368012']

### sbceec644 (synthetic, ItMD_noisy)
- first3: ['-9.798831646250571e-05', '-0.00010553573326313668', '-0.00010338290707728016']
- last3:  ['-0.00011401147045019119', '-9.625860669193863e-05', '-0.00010413716072758282']

### sbd6c6920 (synthetic, IcItMD_ItMD_noisy)
- first3: ['-6.73452940578371e-05', '-0.0001408906405010269', '-9.331041845238754e-05']
- last3:  ['-0.00012246628022682932', '-0.00014128763608157262', '-0.00011463191260791347']

### scfcf1387 (synthetic, IcDItMD_residual_noisy)
- first3: ['-0.0008969751458913034', '-0.0008996230153572142', '-0.0008720271997513106']
- last3:  ['-0.0004787753615852825', '-0.0004837904490438426', '-0.0005170614337946386']

### 20150069 (real, )
- first3: ['-2.3848300000000003e-05', '-2.589e-05', '-2.7730700000000005e-05']
- last3:  ['-5.00256e-05', '-4.85482e-05', '-4.69912e-05']
- matching encodings: ['fortran_order_f8', 'float64_native_no_ascontig', 'values_attr_tobytes']

### 20150377 (real, )
- first3: ['-1.3653900000000002e-05', '-1.58713e-05', '-1.78842e-05']
- last3:  ['-4.05875e-05', '-4.00798e-05', '-4.07661e-05']
- matching encodings: ['fortran_order_f8', 'float64_native_no_ascontig', 'values_attr_tobytes']

### 20150436 (real, )
- first3: ['-2.07021e-05', '-2.14878e-05', '-2.19352e-05']
- last3:  ['-5.9550500000000005e-05', '-5.89032e-05', '-5.85136e-05']
- matching encodings: ['fortran_order_f8', 'float64_native_no_ascontig', 'values_attr_tobytes']

