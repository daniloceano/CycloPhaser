#!/usr/bin/env python
"""Closing check — sweep tau over its whole usable range, not one value per series.

Why this exists. The tolerance table in step 4 of REPORT.md evaluated each of
the six refusals at ITS OWN minimum recovering tau. That is the weakest possible
form of the claim: it says nothing about whether some OTHER tau would have put a
different series inside its tolerance. This sweeps the whole range and answers
the stronger question — is there ANY tau at which >= 3 of the six land within
their label's tolerance, even with conditions (ii) and (iii) abandoned entirely?

Legitimate without the detector for the reason established in stage 1 and
re-asserted here: `rel` does not depend on tau (tau only thresholds it), a
single path R1 decides, and the leading-NaN fill-in is inert on real TRAIN, so
the plateau boundary IS the detector's leading-incipient count. `separability.py`
already re-derives the stored boundary at tau=0.20 on 35/35; this script repeats
that assertion before sweeping.

Range: tau in [0.20, 0.80] step 0.0005. Below 0.20 every refusal stays refused
(tau must EXCEED head_min, and the smallest head_min among the six is 0.2077);
0.80 is past the largest head_min of any series in the split (0.7168).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
ROWS = json.loads((OUT / "refusal.json").read_text())["rows"]
K = 5
TAU0 = 0.20
LO, HI, STEP = 0.20, 0.80, 0.0005
SIX = ["20160587", "20160735", "20171179", "20180628", "20181046", "20202023"]


def boundary_at(rel: np.ndarray, tau: float, k: int = K) -> int:
    a = rel >= tau
    if a.size < k:
        return 0
    run = np.convolve(a.astype(int), np.ones(k, dtype=int), mode="valid")
    hits = np.flatnonzero(run == k)
    return int(hits[0]) if hits.size else 0


def main() -> int:
    by_id = {r["id"]: r for r in ROWS}
    for r in ROWS:
        assert boundary_at(np.asarray(r["rel"]), TAU0) == r["boundary"], r["id"]
    print(f"re-derivation check at tau={TAU0}: {len(ROWS)}/{len(ROWS)} boundaries "
          f"reproduced\n")

    taus = np.arange(LO, HI + STEP / 2, STEP)
    print(f"sweep: tau in [{LO}, {HI}], step {STEP}  ->  {len(taus)} values\n")

    rel6 = {s: np.asarray(by_id[s]["rel"], dtype=float) for s in SIX}
    hit_tau = {s: [] for s in SIX}
    n_in_tol = np.zeros(len(taus), dtype=int)

    for i, tau in enumerate(taus):
        c = 0
        for s in SIX:
            r = by_id[s]
            nd = boundary_at(rel6[s], float(tau))
            if nd > 0 and abs(nd - r["N_lab"]) <= r["tolerance_idx"]:
                hit_tau[s].append(float(tau))
                c += 1
        n_in_tol[i] = c

    print("=" * 78)
    print("Per series — the FULL set of tau at which it lands within tolerance")
    print("=" * 78)
    print(f"  {'id':<11} {'N_lab':>6} {'tol':>4} {'head_min':>9}   tau interval(s) that hit")
    for s in SIX:
        r = by_id[s]
        ts = hit_tau[s]
        if not ts:
            span = "NEVER — no tau in the swept range"
        else:
            # contiguous runs on the grid
            arr = np.asarray(ts)
            brk = np.flatnonzero(np.diff(arr) > STEP * 1.5)
            starts = np.concatenate(([0], brk + 1))
            ends = np.concatenate((brk, [len(arr) - 1]))
            span = ", ".join(f"[{arr[a]:.4f}, {arr[b]:.4f}]" for a, b in zip(starts, ends))
        print(f"  {s:<11} {r['N_lab']:>6} {r['tolerance_idx']:>4} "
              f"{r['head_min']:>9.6f}   {span}")

    best = int(n_in_tol.max())
    where = taus[n_in_tol == best]
    print("\n" + "=" * 78)
    print("The strong form of the claim")
    print("=" * 78)
    print(f"  max simultaneously within tolerance, over ALL {len(taus)} tau: "
          f"{best} of 6")
    print(f"  attained on tau in [{where.min():.4f}, {where.max():.4f}] "
          f"({len(where)} grid points)")
    print(f"  tau values reaching >= 3 of 6: "
          f"{int((n_in_tol >= 3).sum())}  ->  "
          f"{'G1 REACHABLE' if (n_in_tol >= 3).any() else 'G1 UNREACHABLE by tau'}")
    print("\n  This holds with conditions (ii) [spare the 14] and (iii) [spare the\n"
          "  11] ABANDONED. G1 therefore fails on its own terms, independently of\n"
          "  G3 — no trade-off against the negatives can rescue it.")

    json.dump({"lo": LO, "hi": HI, "step": STEP, "n_tau": int(len(taus)),
               "max_within_tolerance": best,
               "tau_reaching_3_or_more": int((n_in_tol >= 3).sum()),
               "per_series_hit_intervals": {
                   s: ([] if not hit_tau[s]
                       else [float(min(hit_tau[s])), float(max(hit_tau[s]))])
                   for s in SIX}},
              open(OUT / "tau_sweep.json", "w"), indent=2)
    print(f"\nwrote {(OUT / 'tau_sweep.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
