#!/usr/bin/env python
"""Stage 1, step 3 — classify each of the 6 refusals by cause.

The four categories and the precedence order M1 > M2 > M3 were declared in the
commissioning brief BEFORE any of these numbers was read, and are applied here
verbatim:

  M1 edge artefact   the filtered signal at t0 has the opposite sign to the raw
                     one, OR the series is in the defect-I set
                     (docs/future_work.md item 8(d)).
  M2 near miss       relative margin |stat - tau| / |tau| <= 0.20.
  M3 genuine         the filtered series already intensifies from t0, margin > 0.20.
  M4 other.

Two readings of "the filtered signal at t0" are both reported rather than one
being chosen after the fact: the filtered first difference `filt[1]-filt[0]`
(which is how item 8(d) itself defines defect I, so the defect-I test and the
sign test are the same test under this reading) and `dz[0]`, the first sample of
the smoothed-derivative array `find_stages` actually consumes. M1 fires if
EITHER disagrees with the raw first difference — the more permissive reading, so
that M1's precedence is not narrowed by the choice.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
ROWS = json.loads((OUT / "refusal.json").read_text())["rows"]
TAU = 0.2
SIX = ["20160587", "20160735", "20171179", "20180628", "20181046", "20202023"]


def sgn(x: float) -> int:
    return (x > 0) - (x < 0)


def main() -> int:
    by_id = {r["id"]: r for r in ROWS}

    # --- defect I over the whole real TRAIN split ---
    di = sorted(r["id"] for r in ROWS if r["defect_I"] is True)
    print("=" * 78)
    print("DEFECT I (item 8(d)) — sign(z[1]-z[0]) disagrees between raw and filtered")
    print("=" * 78)
    print(f"  over the 35 real TRAIN series: {len(di)} members")
    for sid in di:
        r = by_id[sid]
        print(f"    {sid}  d_raw={r['d_raw_t0']:+.6e}  d_filt={r['d_filt_t0']:+.6e}  "
              f"cell={r['cell']}")
    print(f"\n  the published figure is 7 of 51. The other {7 - len(di)} lie in the "
          f"TEST split,\n  which this stage does not load, so the full list of 7 is "
          f"NOT produced here.\n  That does not weaken the intersection below: all 6 "
          f"refusals are TRAIN series\n  and defect I was evaluated on every one of "
          f"the 35 real TRAIN series, so the\n  intersection is complete as computed.")
    inter = sorted(set(di) & set(SIX))
    print(f"\n  intersection with the 6 refusals: {len(inter)} {inter if inter else '(empty)'}")

    print("\n" + "=" * 78)
    print("SIGNS AT t0 — the 6 refusals")
    print("=" * 78)
    print(f"  {'id':<11} {'d_raw[t0]':>14} {'d_filt[t0]':>14} {'dz[t0]':>14} "
          f"{'filt vs raw':>12} {'dz vs raw':>10} {'defI':>5}")
    for sid in SIX:
        r = by_id[sid]
        a, b, c = r["d_raw_t0"], r["d_filt_t0"], r["dz_t0"]
        print(f"  {sid:<11} {a:>+14.6e} {b:>+14.6e} {c:>+14.6e} "
              f"{('OPPOSITE' if sgn(a) != sgn(b) else 'same'):>12} "
              f"{('OPPOSITE' if sgn(a) != sgn(c) else 'same'):>10} "
              f"{str(r['defect_I']):>5}")

    print("\n" + "=" * 78)
    print("CLASSIFICATION — categories and precedence declared before the data")
    print("=" * 78)
    hdr = (f"  {'id':<11} {'R':>3} {'head_min':>9} {'margin':>8} {'N_lab':>6} "
           f"{'n':>5} {'p_in[0]':<16} {'M1':>4} {'M2':>4} {'M3':>4} {'-> cause':>9}")
    print(hdr)
    out = {}
    for sid in SIX:
        r = by_id[sid]
        margin = abs(r["head_min"] - TAU) / abs(TAU)
        m1 = (sgn(r["d_raw_t0"]) != sgn(r["d_filt_t0"])
              or sgn(r["d_raw_t0"]) != sgn(r["dz_t0"])
              or r["defect_I"] is True)
        m2 = margin <= 0.20
        # "already intensifies from t0" — the detector's own pre-fillna label at
        # t0, which is the pipeline's statement about the filtered curve
        m3 = (r["periods_in_0"] == "intensification") and margin > 0.20
        cause = "M1" if m1 else ("M2" if m2 else ("M3" if m3 else "M4"))
        out[sid] = {"margin": margin, "M1": m1, "M2": m2, "M3": m3, "cause": cause}
        print(f"  {sid:<11} {r['R']:>3} {r['head_min']:>9.6f} {margin:>8.4f} "
              f"{r['N_lab']:>6} {r['n_steps']:>5} {str(r['periods_in_0']):<16} "
              f"{str(m1):>4} {str(m2):>4} {str(m3):>4} {cause:>9}")

    counts = {}
    for v in out.values():
        counts[v["cause"]] = counts.get(v["cause"], 0) + 1
    print(f"\n  counts by precedence (M1 > M2 > M3): {counts}")
    top = max(counts.values())
    verdict = "COMUM" if top >= 4 else ("PARCIAL" if top == 3 else "HETEROGENEO")
    biggest = [c for c, n in counts.items() if n == top]
    print(f"  largest group = {top}/6 ({', '.join(biggest)})  ->  VERDICT: {verdict}")

    json.dump({"defect_I_train": di, "intersection_with_six": inter,
               "per_series": out, "counts": counts, "verdict": verdict},
              open(OUT / "classification.json", "w"), indent=2)
    # repo-relative: a committed .txt must not embed an absolute local path
    print(f"\nwrote {(OUT / 'classification.json').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
