# Choosing the incipient probe's smoothing window and boundary criterion

**Status: measurement only. No window chosen, no criterion locked in, no default
changed.** `determine_periods(series)` remains byte-identical to `develop-v2.1`.

| | |
|---|---|
| Branch | `research/incipient-plateau` |
| Script | `research/incipient_plateau/measure_incipient_smoothing.py` |
| Raw output | `incipient_smoothing_sweep.csv` (540 rows), `incipient_smoothing_real_rel0.csv`, `incipient_smoothing_tables.txt` |
| Figures | `research/incipient_plateau/figures/incipient_smoothing/` (gitignored) |
| Environment | python 3.13.5, scipy 1.17.1, numpy 2.4.0, pandas 2.3.3 |
| Sibling | `measure_incipient.py` and its three artefacts are untouched |

## The question

`incipient_plateau_signal="vorticity"` reads the rate on `d(zeta_raw)/dt`. That
is what makes it immune to the pipeline's edge artifacts, and also what exposes
it to raw noise — measured previously, on the 2 %-noise synthetic cases the
normalised raw gradient at t₀ is already 0.25–0.57, above any usable τ, so the
criterion trips at the first sample and returns *no incipient phase at all*.

`incipient_smooth_window` gives the probe its own light Savitzky-Golay denoising,
applied to the raw vorticity before differentiating it and **nowhere else** —
`df['z']` and `df['dz']` are untouched, so no other phase sees it and
`use_smoothing` stays off as decided in `docs/future_work.md` §4.

Two choices follow, settled here by number rather than by eye: how wide the
window should be, and which criterion to read off the denoised curve.

## Candidates

- **τ-slope, single crossing** — first `t` with `rel(t) ≥ τ`.
- **τ-slope, sustained k=3** — first `t` starting a run of 3 samples at or above τ.
- **Knee (measurement only, deliberately NOT in the package)** — `argmax |d²z|`
  over the first half, restricted to before the slope peak. Threshold-free: it
  asks where the curve actually turns rather than when the rate crosses a level.

Scored against the 5 synthetic cases that open with a literal `Ic` segment
(the only ones with a checkable boundary), tolerance 6 timesteps.

---

# 1. The knee is disqualified — twice over

| candidate | w=0 | w=3 | w=5 | w=7 | w=9 |
|---|---|---|---|---|---|
| knee — mean \|error\| | 1.6 | 1.6 | **6.6** | **4.4** | **8.6** |
| knee — worst \|error\| | 2.0 | 2.0 | **14** | **13** | **23** |
| knee — false positives (of 2) | **2** | **2** | **2** | **2** | **2** |

**It cannot refuse.** The knee fires on *both* linear-onset true negatives at
every window — 2/2 false positives throughout. This is the same structural
defect that disqualified `incipient_method="amplitude"`: `argmax` always returns
an index, so the criterion has no way to say "there is no incipient phase here".
A threshold-free criterion is attractive precisely because it has no threshold,
and that is exactly what removes its ability to decline.

**And smoothing makes it worse, not better.** Mean error goes 1.6 → 8.6 as the
window widens, worst error 2 → 23. On `IcItMD_residual_noisy` the knee moves
3 → 16 → 26 across w = 0/5/9. This is the Goldilocks caveat made concrete: a
wider window flattens the turn and displaces it later in the series, and
curvature is the quantity most sensitive to that.

Every τ candidate, by contrast, scores **0 false positives at every window** —
the `rel(0) ≥ τ` rejection mechanism survives the smoothing intact.

---

# 2. Smoothing removes the need for `sustained k` as a crutch

Designed-Ic cases left with **no incipient phase at all** (a qualitative failure,
counted separately from a boundary error):

| candidate | w=0 | w=3 | w=5 | w=7 | w=9 |
|---|---|---|---|---|---|
| τ=0.10 single | 2 | 2 | 1 | 1 | **0** |
| τ=0.10 sustained k=3 | 1 | 1 | **0** | **0** | **0** |
| τ=0.15 single | 2 | 2 | 1 | **0** | **0** |
| τ=0.15 sustained k=3 | **0** | **0** | **0** | **0** | **0** |
| τ=0.20 single | 2 | 2 | **0** | **0** | **0** |
| τ=0.20 sustained k=3 | **0** | **0** | **0** | **0** | **0** |

Without smoothing, single-crossing misses 1–2 of the 5 cases: the noisy rate
trips at t₀ and the plateau has zero length. `sustained k=3` masks that by
demanding the rate *stay* tripped — it compensates for an unreliable rate rather
than measuring it better, and it delays the boundary to do so.

With `w ≥ 5–7` the single-crossing rule catches up and reaches 0 misses on its
own. **This is the hypothesis the smoothing was added to test, and it holds**:
denoising the probe restores the rate's reliability, so `k` is no longer doing
load-bearing work.

---

# 3. Ranking by number

Ranked by (false positives, misses, mean |error|, worst |error|) — a criterion
must score 0 on the first two before its error matters:

| candidate | window | mean \|err\| | worst | misses | false pos |
|---|---|---|---|---|---|
| τ=0.10 single | 9 | **0.8** | 2.0 | 0 | 0 |
| τ=0.10 sustained k=3 | 9 | **0.8** | 2.0 | 0 | 0 |
| τ=0.10 sustained k=3 | 5 | 1.0 | 2.0 | 0 | 0 |
| τ=0.10 sustained k=3 | 7 | 1.0 | 2.0 | 0 | 0 |
| τ=0.15 single | 9 | 1.2 | 3.0 | 0 | 0 |
| τ=0.15 sustained k=3 | 9 | 1.2 | 3.0 | 0 | 0 |
| τ=0.15 single | 7 | 1.4 | 3.0 | 0 | 0 |
| τ=0.15 sustained k=3 | 5 | 1.4 | 3.0 | 0 | 0 |

On the synthetic ground truth the numbers point at **τ ≈ 0.10–0.15 with a window
of 5–9**, and at that point single and sustained are indistinguishable — which is
finding 2 restated.

---

# 4. The real tracks say something different, and it matters more

`rel(0)` under the author's §3c calibration. τ can only fire if it *exceeds*
`rel(0)`, so a `rel(0)` above every usable τ means the criterion refuses outright.

**`signal="vorticity"`** — the path the smoothing acts on:

| track | w=0 | w=3 | w=5 | w=7 | w=9 | w=15 | w=21 |
|---|---|---|---|---|---|---|---|
| 20190325 | 0.283 | 0.283 | 0.246 | 0.214 | 0.184 | 0.128 | 0.102 |
| 20206498 | 0.677 | 0.677 | 0.517 | 0.459 | 0.413 | 0.297 | 0.057 |
| 20150377 | 0.534 | 0.534 | 0.430 | 0.372 | 0.340 | 0.185 | 0.232 |
| 20190639 | 0.255 | 0.255 | 0.243 | 0.164 | 0.108 | 0.186 | 0.226 |
| 20203373 | 0.210 | 0.210 | 0.201 | 0.247 | 0.214 | 0.097 | 0.106 |
| 20170225 | 0.436 | 0.436 | **0.656** | 0.382 | 0.467 | 0.509 | 0.478 |
| 20204655 | 0.177 | 0.177 | 0.093 | 0.015 | 0.132 | 0.174 | 0.189 |

**`signal="derivative"`** — the pipeline-filtered curve, for reference:
0.005, 0.017, 0.031, 0.050, 0.008, 0.091, 0.047.

Two things follow.

**The smoothing does not rescue `vorticity` on real tracks.** `rel(0)` stays at
0.18–0.68 and comes down only slowly. At w=5, τ=0.20 refuses on 6 of the 7
tracks. The synthetic noisy cases are genuinely unfiltered series where the
denoising is doing necessary work; real TRACK vorticity already carries upstream
spatial smoothing, and under §3c the Lanczos handles the rest.

**And the window is not monotone on real data.** `20170225` goes 0.436 → 0.656
at w=5 → 0.382 at w=7 → 0.467 at w=9; `20204655` goes 0.177 → 0.093 → 0.015 →
0.132 → 0.174. A wider window is not reliably better, so the window cannot be
picked by "more is safer" — it has to be looked at.

**`signal="derivative"` is the one that works on real tracks**, at 0.005–0.091,
an order of magnitude below any usable τ — and it needs no smoothing at all,
because the Lanczos already did that job.

---

# 5. Summary

1. **The knee is out.** It cannot decline (2/2 false positives at every window),
   and smoothing degrades it (worst error 2 → 23). Recommended not to carry it
   into the package; it stays in this script as a measured negative result.
2. **τ keeps its rejection mechanism** under every window tested — 0 false
   positives throughout.
3. **Smoothing removes `sustained k` as a crutch**: single-crossing goes from
   1–2 misses at w=0 to 0 at w ≥ 7, matching sustained k=3.
4. **On synthetic ground truth**, τ ≈ 0.10–0.15 with window 5–9 is best by
   number (mean error 0.8–1.4 steps, 0 misses, 0 false positives).
5. **On real tracks the conclusion inverts**: smoothing does not make
   `vorticity` usable (τ=0.20 refuses on 6/7 at w=5) and the window is
   non-monotone; `derivative` is comfortably below any τ without smoothing.

# 6. Open questions for the author

- **Which signal is the target?** The smoothing was built for `vorticity`, and
  it does its job on synthetic noisy series — but on real tracks `derivative`
  already sits at 0.005–0.091 and needs none of it. If validation is on real
  tracks under §3c, the smoothing may be solving a problem that only the
  synthetic suite has.
- **Window**: 5–9 by the synthetic numbers, but §4 shows it is non-monotone on
  real data — this one genuinely needs the visual check.
- **τ and crossing**: 0.10–0.15, and with smoothing the single/sustained choice
  stops mattering. Is `sustained` worth keeping as an option once the rate is
  reliable?
- **Knee**: confirm it stays out of the package.
