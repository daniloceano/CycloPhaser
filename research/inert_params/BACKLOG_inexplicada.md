# FRENTE F(iii) — INEXPLICADA backlog (measured inert, no code-skip line, no data-level explanation)

Per gate (b), now with three categories (see `DATA_DEPENDENT_findings.md`
for the full operational definitions): POR DESENHO / DEPENDENTE DOS DADOS /
INEXPLICADA. Only INEXPLICADA belongs here — an inertia where the parameter
is read unconditionally, the branch is real, **and** no dataset-level
explanation has been traced. This is the genuine "might be a bug" bucket.
**None of these get a UI caption.**

## Current entries: none

Both entries originally filed here during the first pass —
`threshold_intensification_gap` and `incipient_plateau_crossing` under
`signal="derivative"` — were reclassified during the F(iii) closeout audit
(PASSO 3): both are read unconditionally on a real branch, and both now have
a traced, data-level explanation (which 51-track-specific property makes the
branch a no-op at the tested values). Filing them as INEXPLICADA would have
put them in a bug-hunt queue for a defect that isn't there. See
`DATA_DEPENDENT_findings.md` for the full writeup, line citations, and —
for `incipient_plateau_crossing` — the (τ, k) quantification showing the
"agreement" is a property of a specific region of parameter space, not a
blanket one.

If a future sweep pass finds a parameter that is inert, whose reading line
is unconditional, and for which no dataset-level story can be traced, it
goes here.
