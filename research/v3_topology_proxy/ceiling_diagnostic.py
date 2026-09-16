#!/usr/bin/env python
"""POST-HOC DIAGNOSTIC — not part of the gate, run after the verdict was recorded.

The gate in PROTOCOL.md was declared, run once and recorded as FAIL before this
file existed. Nothing here can change that verdict, and nothing here is a
re-run of it.

It answers one follow-up question the FAIL raises: is Reader T's 31.9 % a
property of the PREMISE ("the filtered series carries the phase inventory") or
of the two thresholds Reader T happened to inherit from the package's defaults
(the plateau `tau = 0.20` at each end, and `prominence_relative = None` on the
z extrema)?

Method: sweep both thresholds and report the BEST exact-sequence agreement any
setting reaches. The best setting is chosen on the same 47 cases it is scored
on, so the number is an optimistically biased **upper bound** — no honest
calibration could do better, and a held-out one would do worse. That bias is
the point: if even the ceiling is far below the declared 70 %, the premise is
refuted robustly rather than by one unlucky threshold.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "research" / "v3_topology_proxy"))

from labels_core import (  # noqa: E402
    load_real_series, load_synthetic_series, normalize_phase, read_labels, read_split,
)
from cyclophaser.determine_periods import find_peaks_valleys, process_vorticity  # noqa: E402
from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel,
)
from measure_topology_proxy import _alternating_extrema  # noqa: E402


def skeleton(z: np.ndarray, zpv: pd.Series) -> list[str]:
    ext = _alternating_extrema(zpv, z)
    seq: list[str] = []
    for k in range(len(ext) - 1):
        (_, a), (_, b) = ext[k], ext[k + 1]
        if a == "peak" and b == "valley":
            seq.append("intensification")
        elif a == "valley" and b == "peak":
            if k > 0:
                seq.append("mature")
            seq.append("decay")
    return seq


def main() -> int:
    split = read_split()
    train = list(split["train"])
    by_id = read_labels()
    series = {**load_real_series(), **load_synthetic_series()[0]}

    labels = {sid: [normalize_phase(p["phase"]) for p in by_id[sid]["phases"]] for sid in train}

    # process_vorticity once per series; the sweep only re-reads z / dz.
    cache = {}
    for sid in train:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v = process_vorticity(pd.DataFrame({"zeta": series[sid]}))
        z = np.asarray(v.vorticity_smoothed2.values, dtype=float)
        dz = np.asarray(v.dz_dt_smoothed2.values, dtype=float)
        rel = _incipient_plateau_rel(pd.DataFrame({"z": z, "dz": dz}), "derivative")
        cache[sid] = (z, pd.Series(z), rel)

    proms = [None, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
    taus = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.01]

    # skeletons depend only on prominence_relative
    skels = {}
    for pr in proms:
        for sid in train:
            z, zs, _ = cache[sid]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                zpv = find_peaks_valleys(zs, prominence_relative=pr)
            skels[(pr, sid)] = skeleton(z, zpv)

    print("=" * 78)
    print("POST-HOC CEILING — best exact-sequence agreement over all threshold settings")
    print("(oracle-selected on the same 47 cases it is scored on: an UPPER BOUND)")
    print("=" * 78)

    best = (-1, None)
    per_prom = {}
    for pr in proms:
        best_pr = (-1, None)
        for th in taus:
            for tt in taus:
                hit = 0
                for sid in train:
                    seq = list(skels[(pr, sid)])
                    rel = cache[sid][2]
                    if th > 0 and _incipient_plateau_boundary(rel, th, "single", 3) > 0:
                        seq.insert(0, "incipient")
                    if tt > 0 and _incipient_plateau_boundary(rel[::-1], tt, "single", 3) > 0:
                        seq.append("residual")
                    if seq == labels[sid]:
                        hit += 1
                if hit > best_pr[0]:
                    best_pr = (hit, (pr, th, tt))
                if hit > best[0]:
                    best = (hit, (pr, th, tt))
        per_prom[pr] = best_pr
        pr_s = "None" if pr is None else f"{pr:.2f}"
        print(f"  prominence_relative={pr_s:>5}   best {best_pr[0]:>3}/47 "
              f"({100*best_pr[0]/47:5.1f}%)  at tau_head={best_pr[1][1]}, tau_tail={best_pr[1][2]}")

    n = len(train)
    hit, (pr, th, tt) = best
    print(f"\n  CEILING  {hit}/{n}  = {100*hit/n:5.1f}%   "
          f"(prominence_relative={pr}, tau_head={th}, tau_tail={tt})")
    print(f"  declared gate threshold                70.0%  ({'reached' if hit/n >= 0.70 else 'NOT reached'})")
    print(f"  Reader T as declared                    31.9%")
    print(f"  six-function detector                   46.8%")
    print(f"  majority-class baseline                 34.0%")

    # --- how much of the ceiling is the skeleton alone? ---
    print("\n" + "-" * 78)
    print("core skeleton alone (incipient/residual stripped from BOTH sides)")
    print("-" * 78)
    def core(s):
        return [p for p in s if p in ("intensification", "mature", "decay")]
    for pr in proms:
        hit = sum(1 for sid in train if core(skels[(pr, sid)]) == core(labels[sid]))
        mat = sum(1 for sid in train
                  if skels[(pr, sid)].count("mature") == labels[sid].count("mature"))
        pr_s = "None" if pr is None else f"{pr:.2f}"
        print(f"  prominence_relative={pr_s:>5}   core {hit:>3}/47 ({100*hit/47:5.1f}%)"
              f"   mature-count {mat:>3}/47 ({100*mat/47:5.1f}%)")

    # --- the incipient question in isolation: is ANY tau good at it? ---
    print("\n" + "-" * 78)
    print("incipient PRESENCE alone, as a function of tau_head (28 of 47 labels have one)")
    print("-" * 78)
    print(f"  {'tau':>5} {'proxy says yes':>15} {'agree':>7} {'rate':>7} {'miss':>6} {'false':>6}")
    for th in taus:
        yes = agree = miss = false = 0
        for sid in train:
            has = th > 0 and _incipient_plateau_boundary(cache[sid][2], th, "single", 3) > 0
            lab = "incipient" in labels[sid]
            yes += has
            agree += (has == lab)
            miss += (lab and not has)
            false += (has and not lab)
        print(f"  {th:>5} {yes:>15} {agree:>7} {100*agree/47:6.1f}% {miss:>6} {false:>6}")

    # --- where does the incipient information actually live? ---
    # The same probe, read off the RAW input instead of the filtered series
    # (the package's own incipient_plateau_signal="vorticity" option). This is
    # no longer a test of the premise -- the premise is about the FILTERED
    # series -- but of where the signal survives, which is what the FAIL branch
    # needs in order to rethink the architecture.
    print("\n" + "-" * 78)
    print("incipient PRESENCE: filtered dz vs the RAW series, each at its own best tau")
    print("-" * 78)
    frames = {}
    for sid in train:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v = process_vorticity(pd.DataFrame({"zeta": series[sid]}))
        frames[sid] = pd.DataFrame({
            "z": np.asarray(v.vorticity_smoothed2.values, dtype=float),
            "dz": np.asarray(v.dz_dt_smoothed2.values, dtype=float),
            "z_unfil": np.asarray(v.zeta.values, dtype=float)})
    for sig, sw, name in [("derivative", 0, "filtered dz (the premise)"),
                          ("vorticity", 0, "raw zeta"),
                          ("vorticity", 11, "raw zeta, savgol 11"),
                          ("vorticity", 21, "raw zeta, savgol 21")]:
        rels = {sid: _incipient_plateau_rel(frames[sid], sig, sw, 3) for sid in train}
        best_a, best_t = -1, None
        for th in taus:
            if th <= 0:
                continue
            a = sum(1 for sid in train
                    if (_incipient_plateau_boundary(rels[sid], th, "single", 3) > 0)
                    == ("incipient" in labels[sid]))
            if a > best_a:
                best_a, best_t = a, th
        print(f"  {name:<28} best {best_a:>3}/47 ({100*best_a/47:5.1f}%) at tau={best_t}")
    print(f"  {'constant always-incipient':<28}      28/47 ( 59.6%)")
    print(f"  {'constant never-incipient':<28}      19/47 ( 40.4%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
