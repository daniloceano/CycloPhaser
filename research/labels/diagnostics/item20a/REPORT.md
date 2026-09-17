# Front 20a — `mature_amplitude_fraction` 0.95 → 0.90

**Verdict: PASS.** All seven gate criteria confirmed, each measured against the
value declared before measurement.

Configuration only. No package line is touched, and the measuring instrument
(`item19_core.pair_by_overlap`) is imported unmodified.

---

## Instruments, per the maintainer's step-3 ruling

| gate | instrument |
|---|---|
| (a), (e) | `pair_by_overlap`, `research/labels/diagnostics/item19/item19_core.py:130` — largest-overlap pairing, **both ends**, fixed margin 6 |
| (b) | `evaluate_against_labels.py` → `labels_core.score_phase_sequences` |
| (c), (d), (f), (g) | unchanged |

The step-3 halt is recorded in `BLOCKER_pairing_rule.md`: the front originally
named `evaluate_against_labels.py` for gate (a), which cannot produce 38/47 —
it drops sequence-mismatched series (ceiling 30), compares phase *starts* only,
and uses each label's own `tolerance_idx` rather than a fixed 6.

---

## P1 — instrument is versioned

`research/labels/diagnostics/item19/item19_core.py`

* **tracked** in `develop-v2.1` (`d4014036`) — confirmed via `git ls-tree`
* sha256 `778831d1481305a3a06854276bf1a73747189715b0bd12485690512d63ff51d2`
* git blob `13b3df7b75bf1ff4f5dcd641191592ec638c2a6e`
* introduced by **`0541a54`** — *"diag(item20): stage 1 + stage 2 measured — gate
  FAIL, 0/45 cells, trade-off confirmed"* (2026-09-17)
* `git diff d4014036 -- <the file>` is **empty** at the end of this front: the
  instrument was read, never written.

## P2 / T9 — baseline reproduced in this environment

Re-measured `params-10` with `pair_by_overlap` on the 47 train series under
numpy 2.5.3 / scipy 1.18.0:

**32/47 — exact match to the item-20 baseline.** The version sensitivity that
produced an `IndexError` at `maf=1.00` does not touch this cell; `maf=0.90` and
`0.95` are both in the legal range and 47 of 47 series ran without an exception
in either configuration.

M95, nominally, is in T2 below.

---

## Gate verdict — criterion by criterion

| | predicted | measured | |
|---|---|---|---|
| **(a)** matures within ±6 both ends at 0.90 | 38/47, M95 ⊆ M90 | **38/47**, `M95 − M90` = **∅** | **PASS** |
| **(b)** sequence at 0.90 | 30/47, S90 = S95 | **30/47**, both differences **∅** | **PASS** |
| **(c)** synthetics | 12/12 unchanged | **12/12 → 12/12** | **PASS** |
| **(d)** incipient boundaries | identical case by case | **0 of 47 differ** | **PASS** |
| **(e)** `20205386` | boundary stays within ±6 | **±6 YES in both**; sequence still missed in both | **PASS** |
| **(f)** suite / package diff | 1130 passed, 0 failed; empty diff | **1130 passed, 0 failed**; `git diff develop-v2.1 -- cyclophaser/` **empty** | **PASS** |
| **(g)** clean run, T6 empty | no exception, both columns empty | **47/47 ran**, T6 **0 and 0** | **PASS** |

Two independent confirmations of (b), (c) and (d): `evaluate_against_labels.py`
run side by side on both configs differs **only** in the mature and decay
boundary lines. Its incipient block is byte-identical, its sequence counts are
identical (30/47 all, 18/35 real, 12/12 synthetic), and `item19_core`'s own
`seq_match` flag agrees with `score_phase_sequences` on both configs.

### Not in the gate, but measured by the official script

| | 0.95 | 0.90 |
|---|---|---|
| mature start, own margin | 56.7% (MAE 2.23, worst 9) | **73.3%** (MAE 1.73, worst 7) |
| decay start, own margin | 65.6% (MAE 2.62, worst 11) | **93.8%** (MAE 1.41, worst 7) |
| all boundaries | 61 of 89 | **75 of 89** |

The decay gain is the mechanical consequence of the mature window extending
forward: the mature→decay boundary lands closer to the label. Recorded, not
claimed as a front result.

### `20191014`

Still wrong, as the front anticipated: label 43–68, detected 135–139 at 0.95 and
134–140 at 0.90 — ~92 steps off at the start in both. The window moved one step
at each end; the failure is unchanged in kind. Not a regression of this front.

---

## Known limitation of the instrument, accepted by ruling

`pair_by_overlap` scores **only the first labelled mature** (`first_lab =
lab_mat[0]`, `item19_core.py:187`). Three train labels carry a second mature
that is not paired or scored, in **either** configuration:

| id | labelled matures | scored | unscored |
|---|--:|---|---|
| `20203947` | 2 | 122–144 | the second |
| `s6b542eee` | 2 | 12–18 | the second |
| `sbd6c6920` | 2 | 13–21 | the second |

Both counts (32/47 and 38/47) are therefore out of 47 **series**, not 47
matures. The second-mature question belongs to fronts 20b/20c.

---

See `tables.md` for T1–T8 in full, `measurements.json` for the raw record, and
`evaluate_params10_train.txt` / `evaluate_params11_train.txt` for the official
script's output on each config.

## T7 — environment

conda env `cyclophaser`, `cyclophaser` imported from the working tree (not a
shadowed release): **python 3.12.14, numpy 2.5.3, scipy 1.18.0**.
