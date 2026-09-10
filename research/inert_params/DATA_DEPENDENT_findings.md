# FRENTE F(iii) closeout, PASSO 3 — DEPENDENTE DOS DADOS (not a defect backlog)

Original gate (b) recognised two buckets (POR DESENHO / INEXPLICADA). That was
incomplete: an inertia can be neither "a code line skips the parameter" nor
"unexplained" — it can be a true, well-understood property of *this specific
51-track calibration set* at the *tested* parameter values, with the code
path fully traced and doing exactly what it says. Filing that as INEXPLICADA
put it in a defect backlog, which invites someone to chase a bug that isn't
there. Filing it as POR DESENHO and captioning it in the UI would be worse —
the parameter IS read on every affected track; a "does nothing in this mode"
caption would be false.

**Operational definitions** (used to (re)classify every inert (parameter,
base_config) pair going forward, in `inertia_matrix.csv` / `sweep_summary.txt`
/ `REPORT_inertia_sweep.md`):

- **POR DESENHO** — a concrete, citable line exists that does not read the
  parameter on the branch taken. Gets a `disabled=` UI guard.
- **DEPENDENTE DOS DADOS** — the parameter *is* read unconditionally on the
  cited line, and the branch taken does not depend on the config axis
  swept; the flat result is a property of the 51-track set at the tested
  values, not of the code. **No UI caption** — the parameter is live and a
  different dataset could exercise it.
- **INEXPLICADA** — neither of the above: the parameter is read, the branch
  is real, and no dataset-level explanation has been traced yet. Backlog
  item, no UI caption either. After this pass, `BACKLOG_inexplicada.md` has
  **zero** entries — both former candidates below have a traced,
  data-level explanation and move here instead.

## 1. `threshold_intensification_gap` — DEPENDENTE DOS DADOS (moved from INEXPLICADA)

- Measured: 0/51 tracks changed across the full UI range (0.01–0.30, step
  0.005), under the default `threshold_intensification_length` (0.075).
- Read unconditionally at `find_stages.py:386`
  (`threshold_intensification_gap = args_periods['threshold_intensification_gap']`)
  and used at `find_stages.py:424` inside `for i in range(len(blocks) - 1):`
  — a loop that only runs a gap comparison when a track has **more than
  one** contiguous intensification block under the default
  `threshold_intensification_length`.
- Data-level explanation: under the *default* configuration, none of these
  51 tracks' intensification detection produces more than one block whose
  gap falls inside the swept range — so the comparison at line 424 either
  never runs (single block) or never changes the outcome. Not a reopening
  of the historical wrong-key bug (confirmed fixed; the key read at line
  386 is its own).
- Scope of this finding: only measured under `threshold_intensification_length`
  at its default (0.075). Untested: a different length threshold (or
  `length_scale='local'`) may produce multi-block tracks where the gap
  parameter bites — that combination was not swept and is not claimed
  inert.

## 2. `incipient_plateau_crossing` under `signal="derivative"` — DEPENDENTE DOS DADOS, narrower than first reported (moved from INEXPLICADA)

- Original gate (b) measurement: 0/51 tracks changed between `"single"` and
  `"sustained"` **at the one tested point** `incipient_plateau_tau=0.20,
  incipient_plateau_k=3` (the `plateau_single_derivative` base config's
  defaults). That specific pair is confirmed correct — re-measured
  independently below, still 0/51 at that exact point.
- **Correction to the original writeup**: describing this as "single and
  sustained coincide under signal=derivative" full stop overstated the
  finding — it was only ever measured at one (τ, k) point. Quantifying
  across the grid (below) shows the two modes **do** diverge, growing from
  0 tracks at low k to 15/51 tracks at `k=25, τ=0.60`. The correct
  statement is: **they coincide in the region of (τ, k) space this
  calibration set's default and nearby values happen to sit in, not in
  general.**
- Both branches are real, distinct code in `_incipient_plateau_boundary`
  (`cyclophaser/find_stages.py`, ~line 840): `"single"` returns the first
  index where `rel >= tau`; `"sustained"` returns the start of the first
  run of `k` consecutive such indices.
- **Quantified** (51 tracks, `signal="derivative"`, 7×8 grid of τ ∈ {0.05,
  0.10, 0.20, 0.30, 0.40, 0.50, 0.60} × k ∈ {1, 2, 3, 5, 10, 15, 20, 25} —
  see `research/inert_params/FINDING_signal_derivative_crossing_for_G_E.md`
  for the full table and the document written for fronts G/E):
  - 0/51 tracks differ for every τ at k ≤ 10 (37/56 grid points, including
    the tested default k=3).
  - Divergence appears only at k ≥ 15, growing with both τ and k, up to
    15/51 tracks at τ=0.60, k=25 — the corner of the UI's own range
    farthest from the calibration defaults.
- Working hypothesis for the low-k region only (not verified beyond this
  dataset): under `signal="derivative"`, `rel(t)` is the pipeline's own
  smoothed `|dz|`, which tends to rise past τ and then keep rising rather
  than dip back below it for several samples — so for small k, the first
  sample at or above τ is already the start of a run of at least k
  consecutive samples above τ on most tracks. Larger k demands a longer
  uninterrupted run, which starts failing on some tracks (hence the
  divergence at k ≥ 15). `signal="vorticity"` is noisier and does not share
  even the low-k property (per the k-sweep result already in
  `inertia_matrix.csv`, `plateau_sustained_vorticity` base, not inert).

## Confirmation (PASSO 3, item 4)

`grep -n "threshold_intensification_gap\|incipient_plateau_crossing"
tools/calibration_app/app.py` — neither parameter has a `disabled=` kwarg or
an inline "inactive"/"only used when" note anywhere in the app. Both remain
fully live, un-captioned controls, as they must — DEPENDENTE DOS DADOS gets
no UI signaling, since the parameter genuinely IS read and a different
dataset or a different corner of its own range (as just measured for case 2)
would exercise it.
