# Finding for FRENTES G and E — `crossing="sustained"` under `signal="derivative"` is barely exercised by the calibration set

Surfaced as a side effect of FRENTE F(iii)'s inertia sweep (measuring whether
`incipient_plateau_crossing` is inert), not something either front asked for
— filed here so it reaches whoever owns G (presumably the k/sustained-run
detection logic) and E (presumably the visualization layer built in
F(i)(ii) for the same mechanism), rather than getting buried in F(iii)'s own
report.

## The finding

`incipient_plateau_crossing` has two modes under `incipient_method="plateau"`:
- `"single"` — the incipient-phase boundary is the first index where
  `rel(t) >= tau`.
- `"sustained"` — the boundary is the start of the first *run* of `k`
  consecutive indices where `rel(t) >= tau` (code:
  `_incipient_plateau_boundary`, `cyclophaser/find_stages.py`, ~line 840).

Under `incipient_plateau_signal="vorticity"`, these two modes clearly
produce different results on this calibration set (42/51 tracks changed
across the `k` sweep — see `inertia_matrix.csv`,
`plateau_sustained_vorticity` base). That's the mechanism working as
designed.

Under `incipient_plateau_signal="derivative"`, **the two modes agree on
every one of the 51 calibration tracks for nearly the entire UI-reachable
(τ, k) space**, and only start to diverge at the extreme end of `k`:

| τ \\ k | 1 | 2 | 3 | 5 | 10 | 15 | 20 | 25 |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 2 |
| 0.10 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 2 |
| 0.20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| 0.30 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 4 |
| 0.40 | 0 | 0 | 0 | 0 | 0 | 1 | 3 | 6 |
| 0.50 | 0 | 0 | 0 | 0 | 1 | 2 | 5 | 8 |
| 0.60 | 0 | 0 | 0 | 0 | 0 | 2 | 3 | 15 |

(cell = number of tracks, out of 51, where `single` and `sustained` produce
a different `periods` array; τ = `incipient_plateau_tau`, k =
`incipient_plateau_k`; grid: τ ∈ {0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60},
k ∈ {1, 2, 3, 5, 10, 15, 20, 25}; measured directly with
`get_periods`/`process_vorticity`, not inferred from the app.)

**37 of the 56 grid points — every one with k ≤ 10, i.e. the app's default
`k=3` and everything up to more than 3× that — show zero divergence on any
track.** The calibration set's own default point (`τ=0.20, k=3`) sits deep
inside this flat region. Divergence only appears at `k ≥ 15`, and even then
stays small (1–15 tracks) except at the single farthest corner tested
(`τ=0.60, k=25`).

## Why this matters for G and E, not just F(iii)

- **The `k`/sustained-run *machinery itself* — the code path that makes
  `"sustained"` different from `"single"` — is, for practical purposes, not
  exercised by this calibration set under `signal="derivative"` at any k a
  user is likely to pick** (the UI default is 3; nothing suggests users
  reach for k > 10). If front G is meant to validate or tune that
  mechanism, doing so against `signal="derivative"` tracks in this
  calibration set will show near-zero signal regardless of whether the
  mechanism is implemented correctly — the calibration set cannot
  distinguish a correct "sustained" implementation from a buggy one in this
  region.
- **The F(i)(ii) `rel ≥ tau` / "run rejected" visualization layer in the
  layer inspector** — built specifically to show *why* a plateau crossing
  was accepted or refused, including the crossing/k evidence — has, under
  `signal="derivative"`, essentially nothing to show for `k ≤ 10`: single
  and sustained agree, so there is no rejected-then-accepted run to
  visualize on this dataset. If front E extends or audits that
  visualization, `signal="derivative"` tracks at low k are not a
  representative test case for the "sustained run was rejected, then later
  accepted" code path — `signal="vorticity"` tracks are, since that's where
  the two modes actually disagree already (42/51).

## Not claimed

This is a property of these 51 tracks at these (τ, k) values, not a
statement that `signal="derivative"` + `"sustained"` is redundant or wrong
in general — the working hypothesis in `DATA_DEPENDENT_findings.md` (item 2)
is untested beyond this dataset. No action is taken on this in F(iii) — it
is explicitly out of scope (front boundary: no changes to
`find_stages.py`/detection logic, no re-opening of front A/E/G's own scope).
