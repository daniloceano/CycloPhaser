#!/usr/bin/env python
"""Stage 1, step 4 — is the REFUSAL part of the plateau rule separable by tau?

Pure arithmetic on `refusal.json`: no detector run, no new config. This is
legitimate only because stage 1 established two things about params-13 on the
real train split, both asserted in `diagnose.py`:

  1. Every refusal goes through ONE path, R1 — the sustained run of length k
     starts at index 0, i.e. `min(rel[0:k]) >= tau`. So a series is refused iff
     `head_min >= tau`, and `tau` is the only knob in that inequality.
  2. `leading_nan_in == 0` on all 35 real train series, so the plateau
     boundary IS the detector's leading-incipient count (the `fillna` path never
     contributes). Verified per series by the replay assertion in `diagnose.py`.

Together those let `N_det(tau)` be recomputed from the stored `rel` profile
without the detector: `rel` does not depend on tau at all — tau only thresholds
it. Nothing else about the detection is claimed to be tau-invariant; downstream
phases are NOT recomputed here and no claim is made about them.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "refusal.json").read_text())
ROWS = DATA["rows"]
K = 5
TAU0 = 0.2


def boundary_at(rel: list[float], tau: float, k: int = K) -> int:
    """The package rule, re-expressed: first index of the first run of k >= tau."""
    a = np.asarray(rel, dtype=float) >= tau
    if a.size < k:
        return 0
    run = np.convolve(a.astype(int), np.ones(k, dtype=int), mode="valid")
    hits = np.flatnonzero(run == k)
    return int(hits[0]) if hits.size else 0


def main() -> int:
    by = {c: [r for r in ROWS if r["cell"] == c]
          for c in ("TP", "FP", "REFUSAL", "TN", "AMB")}

    # self-check: the stored head_min and rel must reproduce the stored boundary
    for r in ROWS:
        assert boundary_at(r["rel"], TAU0) == r["boundary"], r["id"]
        assert abs(min(r["rel"][:K]) - r["head_min"]) < 1e-12, r["id"]
    print(f"re-derivation check: boundary_at(tau={TAU0}) reproduces the stored "
          f"boundary on {len(ROWS)}/{len(ROWS)} series\n")

    print("=" * 78)
    print("The decisive statistic per group — head_min = min(rel[0:k]), k=5")
    print(f"refused  <=>  head_min >= tau   (tau = {TAU0} in params-13)")
    print("=" * 78)
    for c in ("REFUSAL", "TN", "TP", "FP", "AMB"):
        vals = sorted((r["head_min"], r["id"]) for r in by[c])
        print(f"\n  {c} ({len(vals)}):")
        for v, sid in vals:
            print(f"    {sid}  head_min = {v:.6f}   "
                  f"rel(tau) margin = {(v - TAU0) / TAU0:+.4f}")

    ref = sorted(r["head_min"] for r in by["REFUSAL"])
    tn = sorted(r["head_min"] for r in by["TN"])
    tp = sorted(r["head_min"] for r in by["TP"])

    print("\n" + "=" * 78)
    print("SEPARABILITY — the three conditions, as inequalities on tau")
    print("=" * 78)
    print("  raising tau shortens the 'above' mask, breaks the run at 0 and so\n"
          "  CREATES an incipient phase; lowering tau removes one.\n")
    need_i = ref[2]
    print(f"  (i)  >=3 of the 6 recovered  needs tau >  {need_i:.6f}  "
          f"(3rd smallest refusal head_min)")
    keep_tn = tn[0]
    tn_id = [r["id"] for r in by["TN"] if r["head_min"] == keep_tn][0]
    print(f"  (ii) all 14 TN still refused needs tau <= {keep_tn:.6f}  "
          f"(smallest TN head_min, {tn_id})")
    keep_tp = tp[-1]
    tp_id = [r["id"] for r in by["TP"] if r["head_min"] == keep_tp][0]
    print(f"  (iii) no TP becomes refused  needs tau >  {keep_tp:.6f}  "
          f"(largest TP head_min, {tp_id})")

    lo = max(need_i, keep_tp)
    hi = keep_tn
    ok = lo < hi
    print(f"\n  (i) AND (iii):  tau > {lo:.6f}")
    print(f"  (ii):           tau <= {hi:.6f}")
    print(f"\n  VERDICT: {'range = (%.6f, %.6f]' % (lo, hi) if ok else 'NO RANGE EXISTS'}")
    if not ok:
        blockers = [(r["id"], r["head_min"]) for r in by["TN"]
                    if r["head_min"] <= need_i]
        print(f"  blocked by these TN series, whose head_min sits BELOW the "
              f"tau needed for (i) ({need_i:.6f}):")
        for sid, v in sorted(blockers, key=lambda x: x[1]):
            print(f"    {sid}  head_min = {v:.6f}")

    print("\n" + "=" * 78)
    print("How far a tau move gets before it costs a TN — the interleaving")
    print("=" * 78)
    marks = sorted([(v, "REFUSAL", r["id"]) for r in by["REFUSAL"] for v in [r["head_min"]]]
                   + [(r["head_min"], "TN", r["id"]) for r in by["TN"]])
    print(f"  {'head_min':>10}  {'group':<9} id      (ascending: tau must EXCEED "
          f"this to flip the series)")
    for v, g, sid in marks:
        print(f"  {v:>10.6f}  {g:<9} {sid}")
    n_before = sum(1 for v, g, _ in marks if g == "REFUSAL" and v < tn[0])
    print(f"\n  refusals recoverable before the first TN flips: {n_before} of 6")

    print("\n" + "=" * 78)
    print("IF a tau existed — would the recovered series land within tolerance?")
    print("This IS calculable without the detector, for the reason in the "
          "module docstring.")
    print("=" * 78)
    print(f"  {'id':<11} {'N_lab':>6} {'tol':>4} {'min tau to recover':>19} "
          f"{'N_det at that tau':>18} {'|err|':>6} {'within tol':>11}")
    recovered_in_tol = 0
    for r in sorted(by["REFUSAL"], key=lambda x: x["head_min"]):
        hm = r["head_min"]
        # the smallest representable tau strictly above head_min
        tau = np.nextafter(hm, np.inf)
        nd = boundary_at(r["rel"], float(tau))
        err = abs(nd - r["N_lab"])
        hit = err <= r["tolerance_idx"]
        recovered_in_tol += bool(hit)
        print(f"  {r['id']:<11} {r['N_lab']:>6} {r['tolerance_idx']:>4} "
              f"{hm:>19.6f} {nd:>18} {err:>6} {'yes' if hit else 'no':>11}")
    print(f"\n  even ignoring (ii) and (iii) entirely — i.e. recovering ALL SIX "
          f"at its own\n  minimum tau — {recovered_in_tol} of 6 would land within "
          f"its label's tolerance.")

    json.dump({
        "need_i_tau_gt": need_i, "keep_tn_tau_le": keep_tn,
        "keep_tp_tau_gt": keep_tp, "range_exists": bool(ok),
        "refusals_recoverable_before_first_TN_flips": int(n_before),
        "recovered_within_tolerance_if_all_recovered": int(recovered_in_tol),
    }, open(OUT / "separability.json", "w"), indent=2)
    # repo-relative: a committed .txt must not embed an absolute local path
    print(f"\nwrote {(OUT / 'separability.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
