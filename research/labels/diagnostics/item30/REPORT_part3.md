# Item 30, part 3 — opt-in rule, params-15 candidate, adjudicated labels (checkpoint)

**Status: CHECKPOINT. Awaiting Danilo's approval. Not merged.**

Predictions were committed in `84f7c89`, before any implementation:
`PREDICTIONS_part3.md`. They are answered below and not rewritten. Environment:
the dedicated `cyclophaser` env. `cyclophaser.__file__` and
`layer_inspector.__file__` both resolve to this checkout, which the scripts
assert. Versions: python 3.12.14, numpy 2.5.3, scipy 1.18.0, pandas 3.0.5.

## The rule

`incipient_plateau_spare_intensification` is a bool, default `False`, in
`get_periods` and `determine_periods`. It is applied in
`find_stages.find_incipient_period`, in the `plateau` branch, immediately before
the overwrite `df.iloc[:boundary] = 'incipient'`, through
`_spare_enclosed_intensification(periods, boundary)`:

- `periods` is the map the stage receives, captured before the `fillna`, which
  is step 5 of the ribbon.
- E is the first contiguous block whose label starts with `intensification`
  and whose start lies before the boundary.
- If E also ends before the boundary, the boundary becomes E's start. A
  boundary of 0 writes no incipient at all.
- Otherwise nothing changes.

The `geometric` method never reads the key.

## Predictions

| | prediction | result |
|---|---|---|
| **R1** | TRAIN (42 real + 12 synthetic): the rule changes exactly the 5; in them, final == counterfactual of `1a3ad76` | **CONFIRMED.** The rule changes 5 of 54, and the changed set equals the predicted 5. The final map equals the counterfactual in 5/5. |
| **R2** | off by default: byte-identical output (canonical `default_behaviour_hash.py`, same session) | **CONFIRMED.** The hash is `b500d2e0…` both before (`84f7c89`, no rule) and after (rule present, off). See the caveat below. |
| **R3** | swell 196: exactly 10 tracks change (8 bad-with-signal + 19810854 + 19861089); counts only | **REFUTED.** 15 change. All 10 predicted change; 5 more change outside the prediction. |
| **R4** | the 49 non-adjudicated TRAIN series score identically under params-14 and params-15 | **CONFIRMED.** Every block is textually identical (below). |
| **V** | validation, measured later | Not measured: the 5 validation tracks have no labels yet. |

**R2 caveat.** The canonical generator runs the package defaults, where
`incipient_method = "geometric"`, so it never reaches the `plateau` branch
where the rule lives. The plateau path has its own proof:
`prove_defaults_part3_step3.txt`. The evaluator under params-14 (plateau, key
absent) gives identical output with the rule in the package and at `1a3ad76`.

**R3, the 5 unpredicted tracks.** Counts only; none of them is a validation
track or in a labelled batch.

- **0 of 5** carry the item-30 signal (plateau boundary > peak). The rule
  fires on them because E lies wholly before the boundary, even though the
  plateau does not end after the peak.
- **3 of 5** are among Danilo's bad marks, and 2 are not.

In TRAIN this never happens: every P case has c3 < 1, so its E always crosses
the boundary. The rule is therefore **broader than the signal it was designed
for**, and what it does on those 5 has not been looked at.

## Score, params-14 → params-15 (evaluator, `--batch-train swell_item30`)

| block | sequence match | incipient boundary within margin |
|---|---|---|
| 47 of the split (35 real + 12 synthetic) | 31/47 → 31/47 | 17/27 → 17/27 |
| 2 of the batch, not adjudicated (19790612, 20050893) | 1/2 → 1/2 | 1/2 → 1/2 |
| 5 adjudicated | 0/5 → **5/5** | 0/1 → 1/1; label "none" agreed 0/4 → 4/4 |

**The adjudicated block is circular by construction.** Its labels are the
counterfactual, and params-15 reproduces the counterfactual exactly (R1). So
5/5 says the rule does what it was built to do. It is **not** evidence that
the rule is right. The only independent evidence available is V. The full
outputs are in `part3_eval_params14.txt` and `part3_eval_params15.txt`.

## Adjudicated labels (step 1)

- **Snapshot.** The 7 TRAIN labels of the batch are in
  `swell_item30/labels_v1_snapshot.yaml`: blocks byte for byte, sha256 each.
- **Provenance.** Carried in the existing optional field `notes`
  (`labels_core.ADJUDICATED_NOTE`). No new field, no validator change, no
  schema change. The original also stays in each record's `superseded`,
  because `upsert_label` keeps it.
- **Other records.** The other 68 blocks are byte-identical.
- **Tolerance.** The top-level tolerance is the original's. Per phase, the k-th
  phase of a given name takes the tolerance of the original's k-th phase of
  that name. A phase the original never had takes the original's top-level
  value; this affects the intensification and mature phases of the K cases.
- **`overlays_shown`.** Set to the original's value plus
  `item30_counterfactual`: the label is detector output, so it must not read
  as blind. Under `--against first-blind`, the evaluator scores the blind
  original where one exists (19940445, 19810854) and excludes the other 3.
  Adjudicated records are still reported only in their own block.

## Validation batch (step 2) and blindness

`batches.swell_item30_val` has the role `validation`, with `train` and `test`
empty. Its 5 files are copied byte for byte from `standard/`. The selection was
checked against part 2's per-track table; the table was read, and only a count
was printed. The previous text of `split.yaml` is an exact prefix of the new
file.

The label tab shows the 5 as VALIDATION: each can be saved once while
unlabelled and is locked after that. They are not in the benchmark (even with
the swell batch on), the evaluator never reaches them, and the default loaders
do not see them (tests).

**Blindness in this part.**

- **Kept out:** no validation id appears per case in any table, figure, log or
  benchmark output. They enter only R3's aggregate counts.
- **Where the ids do appear:** in the freeze records (split.yaml,
  `provenance_val.yaml`) and in the test code, as identifiers only.

**Caveat on V's independence.** The 5 are among the 200 swell tracks Danilo
saw with detection in the Grid on 2026-09-24. Their validation labels are
therefore not blind in that sense. This is recorded in the batch's
`labelling_note`.

## Suite

`-m "not browser"`, dedicated env: **1419 passed, 0 failed**. `git diff develop-v2.1 -- cyclophaser/` is the rule only (2 files, +62/−2).

## Files

- `part3_measure.py` and `part3_measure_output.txt`: R1, R3, R4, the scores
  and the figures.
- `figs_part3/`: before and after for the 5 (original label | adjudicated
  label | params-14 | params-15), plus a board.
- `prove_defaults_part3.py`, with outputs `_step2.txt` and `_step3.txt`: the
  default loaders and the evaluator, against `1a3ad76`.

---

## Checkpoint addendum (2026-09-27): the 5 outside the signal, the narrow variant, the benchmark

This section only adds to the report; nothing above is rewritten. The script is
`outside_signal.py` and its output is `outside_signal_output.txt`. The
per-track table and the figures are OUTSIDE the repo, in
`cyclophaser_swell_tracks_test/diag_item30/`
(`outside_signal_5_params14_15.csv` and `figs_outside_signal/`).

### R3 refuted: 15, not 10 — and the hypothesis that was wrong

The 5 tracks outside the prediction are **19850338, 19890443, 20011085,
20040726 and 20110785**. None of them is TEST or VALIDATION, and none is in a
labelled batch. 3 were marked bad and 2 good.

Claude's wrong hypothesis was that "E lies wholly before the boundary" implies
"boundary > global minimum" (the signal). It does not. In all 5, E is a first,
shallower deepening:

- E ends at a secondary z valley before the boundary.
- At E's end, z is 54–88% of the global minimum.
- The global minimum comes at or after the boundary.
- In 19890443 the boundary equals the minimum. The signal is a strict `>`, so
  that track fails it by a tie.

The rule's condition is about where E lies, not about where the minimum lies.

### Narrow variant (measured, not adopted)

The variant acts only when E ends before the boundary **and** the boundary lies
after the argmin of the filtered z. It is a replica built from the
pre-incipient map, outside `cyclophaser/`. Its fidelity was checked first: the
same replica without the extra condition reproduces params-15 on 54/54 TRAIN
and 196/196 swell tracks.

- **TRAIN:** it changes the same 5 as the rule (R1): True.
- **Swell:** it changes 10 tracks, exactly the 10 predicted, and 0 of the 5
  outside the signal.

### R2: the guard that did not exercise the changed branch

The canonical generator, `front_b/default_behaviour_hash.py`, runs the package
defaults. Their incipient method is geometric, so the generator never enters
the plateau branch where the rule lives. Its identical digest therefore proves
nothing about that branch. The effective proof of "default unchanged" on the
plateau branch is the evaluator's output under params-14: it is identical to
`1a3ad76`. **Lesson:** a "default unchanged" guard must exercise the branch
that changed.

### Deviation

The rule was committed (`f85e1b8`) before the checkpoint was approved. The
history is not rewritten; the deviation is recorded here.

### Benchmark

Labels that carry the adjudication note get their own "Adjudicated (item 30)"
block in the benchmark's scoring and are never added into train or test
(`benchmark_core.metrics_by_split`). An AppTest with the swell batch on shows
the batch's 7 TRAIN cases split into 2 in train and 5 adjudicated. A positive
control strips the note and gets all 7 back in train. The default loaders and
the evaluator are unchanged against `1a3ad76`
(`prove_defaults_part3_checkpoint.txt`).

### Cleanup debts (not done here)

- The configs table in `research/labels/README.md` stops at params-11.
- Importing a config older than params-14 into the app warns "missing key" for
  the incipient keys and `reclassify_index0`.

---

## Closing record (2026-09-27)

- **Rule kept in its BROAD form**, by the declared decision rule. In Danilo's
  evaluation under params-15 (27 Sept 2026, 20:43Z, 249 tracks), none of the 5
  tracks outside the signal (19850338, 19890443, 20011085, 20040726, 20110785)
  was marked bad. 19890443, 20011085 and 20040726 had been marked bad under
  params-14. Visual marks are judgement, not a score.
- **V: spent.** The 5 validation tracks were seen under params-15 before they
  were labelled. `batches.swell_item30_val` stays frozen as a record, role
  "spent before labelling", with no labels. The block in `split.yaml` was not
  edited and still reads `role: validation`; updating it is a separate
  decision.
- **Test exposure.** 19 test series were evaluated in the Grid under params-15:
  the 16 of the split, the 3 of the batch and 20203389. Danilo marked 20150377
  and 20206498 bad. The marks were used in no decision.
- **Danilo's note.** Other cases may be bad because their series are genuinely
  ambiguous. They are outside the scope of this front.
- **Adoption NOT recorded.** The ADOÇÃO line of the closing brief came back
  unfilled, so params-15 remains a CANDIDATE and is not the reference
  configuration. The package default stays False.
- **Merge NOT done.** The AUTORIZAÇÃO DE MERGE line came back unfilled.

## Closing decisions (2026-09-27, supersede the "NOT recorded / NOT done" lines above)

- **Adoption (Danilo): "adotado sem validação independente".** params-15 is
  now the calibration reference, and params-11 becomes historical. The package
  default of `incipient_plateau_spare_intensification` stays False. The configs
  table in `research/labels/README.md` now runs to params-15, which also clears
  that cleanup debt.
- **Validation batch (Danilo's authorisation).** In `batches.swell_item30_val`,
  only `role` and `labelling_note` were edited: the role is now "spent before
  labelling", and the note carries the edit record. The series hashes are
  unchanged. The label tab locks the 5 outright, which an AppTest proves.
  Commit `916ecfc`.
- **Merge authorised by Danilo.** The merge result is recorded on
  develop-v2.1.
