#!/usr/bin/env python
"""POST-HOC / EXPLORATORY — constant baselines for the numbers already reported.

    python research/v3_topology_proxy/baselines.py

**This changes no verdict.** The gate declared in `PROTOCOL.md` was run once and
recorded as FAIL in `RESULTS.md`; nothing here reopens it. This script only
supplies the constant baselines that make the already-reported presence,
skeleton and mature-count figures interpretable — a rate means nothing until you
know what answering the same thing every time would have scored.

Three blocks:

1. **Per-phase presence baselines.** For each of the five phases, what "always
   emit it" and "never emit it" score on presence agreement, beside Reader T
   (as declared) and the six-function detector.

2. **Skeleton and mature-count baselines.** The modal core sequence and the
   modal mature count, as constant answers, beside the proxy's 70.2 % / 78.7 %
   and 87.2 % / 91.5 %.

3. **The two incipient numbers, reconciled** — 51.1 % and 68.1 % come from the
   same signal at two different taus; this prints both explicitly.

Train split only; the 16 test cases are not read.
"""

from __future__ import annotations

import collections
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
    load_real_series, load_synthetic_series, normalize_phase, read_labels,
    read_split, series_sha256,
)
from cyclophaser.determine_periods import find_peaks_valleys, process_vorticity  # noqa: E402
from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel,
)
from measure_topology_proxy import reader_detector, reader_t  # noqa: E402
from ceiling_diagnostic import skeleton  # noqa: E402

PHASES = ("incipient", "intensification", "mature", "decay", "residual")
CORE = ("intensification", "mature", "decay")


def core(seq):
    return tuple(p for p in seq if p in CORE)


def main() -> int:
    split = read_split()
    train = list(split["train"])
    by_id = read_labels()
    series = {**load_real_series(), **load_synthetic_series()[0]}

    for sid in train:
        assert series_sha256(series[sid].values) == by_id[sid]["series_sha256"], sid
    n = len(train)
    print(f"series_sha256 verified for all {n} training cases.")
    print("POST-HOC / EXPLORATORY — baselines only. The gate verdict (FAIL) is untouched.\n")

    labels = {s: [normalize_phase(p["phase"]) for p in by_id[s]["phases"]] for s in train}
    proxy, det, rels = {}, {}, {}
    for sid in train:
        proxy[sid] = reader_t(series[sid])[0]
        det[sid] = reader_detector(series[sid])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            v = process_vorticity(pd.DataFrame({"zeta": series[sid]}))
        rels[sid] = _incipient_plateau_rel(
            pd.DataFrame({"z": np.asarray(v.vorticity_smoothed2.values, dtype=float),
                          "dz": np.asarray(v.dz_dt_smoothed2.values, dtype=float)}),
            "derivative")

    # ----------------------------------------------------------------- 1 ----
    print("=" * 86)
    print("1. PER-PHASE PRESENCE AGREEMENT vs the two constant answers")
    print("=" * 86)
    print("   'always' = emit the phase on every case.  'never' = emit it on none.")
    print("   The bar a reader must clear is the LARGER of the two (the per-phase")
    print("   majority class), printed in the last column.\n")
    hdr = (f"   {'phase':<17}{'label has':>10}{'always':>9}{'never':>9}"
           f"{'Reader T':>10}{'detector':>10}   {'bar (majority)':>15}")
    print(hdr)
    print("   " + "-" * (len(hdr) - 3))
    summary = {}
    for ph in PHASES:
        has = sum(1 for s in train if ph in labels[s])
        always = has
        never = n - has
        pr = sum(1 for s in train if (ph in labels[s]) == (ph in proxy[s]))
        dt = sum(1 for s in train if (ph in labels[s]) == (ph in det[s]))
        bar = max(always, never)
        summary[ph] = (has, always, never, pr, dt, bar)
        print(f"   {ph:<17}{has:>10}{100*always/n:>8.1f}%{100*never/n:>8.1f}%"
              f"{100*pr/n:>9.1f}%{100*dt/n:>9.1f}%   {100*bar/n:>14.1f}%")

    print("\n   clears its own majority bar?")
    for ph in PHASES:
        has, always, never, pr, dt, bar = summary[ph]
        p_ok = "yes" if pr > bar else ("ties" if pr == bar else "NO")
        d_ok = "yes" if dt > bar else ("ties" if dt == bar else "NO")
        print(f"     {ph:<17} Reader T {pr:>2}/{n} vs bar {bar:>2}/{n}  -> {p_ok:<4}"
              f"   |  detector {dt:>2}/{n} vs bar {bar:>2}/{n}  -> {d_ok}")

    # ----------------------------------------------------------------- 2 ----
    print("\n" + "=" * 86)
    print("2. SKELETON and MATURE-COUNT vs their modal constant answers")
    print("=" * 86)

    core_lab = {s: core(labels[s]) for s in train}
    c_counts = collections.Counter(core_lab.values())
    modal_core, modal_core_n = c_counts.most_common(1)[0]
    print(f"\n   label core-sequence distribution ({len(c_counts)} distinct):")
    for seq, k in c_counts.most_common():
        print(f"     {k:>3}  {' -> '.join(seq) if seq else '(empty)'}")
    print(f"\n   modal core sequence: {' -> '.join(modal_core)}")
    print(f"   CONSTANT BASELINE (always answer the modal core):"
          f"  {modal_core_n}/{n} = {100*modal_core_n/n:.1f}%")

    # proxy core at the as-declared setting and at the post-hoc swept setting
    skel = {}
    for pr_val in (None, 0.30):
        for sid in train:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                v = process_vorticity(pd.DataFrame({"zeta": series[sid]}))
            z = np.asarray(v.vorticity_smoothed2.values, dtype=float)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                zpv = find_peaks_valleys(pd.Series(z), prominence_relative=pr_val)
            skel[(pr_val, sid)] = skeleton(z, zpv)

    print(f"\n   {'reader':<46}{'core seq':>12}{'vs baseline':>14}")
    print("   " + "-" * 69)
    rows = [
        ("proxy, prominence_relative=None  (as declared)", None),
        ("proxy, prominence_relative=0.30  (POST-HOC swept)", 0.30),
    ]
    for name, pv in rows:
        hit = sum(1 for s in train if core(skel[(pv, s)]) == core_lab[s])
        print(f"   {name:<46}{hit:>4}/{n} {100*hit/n:>5.1f}%"
              f"{100*(hit-modal_core_n)/n:>+13.1f} pts")
    det_core = sum(1 for s in train if core(det[s]) == core_lab[s])
    print(f"   {'six-function detector':<46}{det_core:>4}/{n} {100*det_core/n:>5.1f}%"
          f"{100*(det_core-modal_core_n)/n:>+13.1f} pts")
    print(f"   {'CONSTANT modal-core baseline':<46}{modal_core_n:>4}/{n} "
          f"{100*modal_core_n/n:>5.1f}%{'--':>13}")

    m_counts = collections.Counter(labels[s].count("mature") for s in train)
    modal_m, modal_m_n = m_counts.most_common(1)[0]
    print(f"\n   label mature-count distribution: {dict(sorted(m_counts.items()))}")
    print(f"   modal mature count: {modal_m}")
    print(f"   CONSTANT BASELINE (always answer {modal_m}):"
          f"  {modal_m_n}/{n} = {100*modal_m_n/n:.1f}%")
    print(f"\n   {'reader':<46}{'mature n':>12}{'vs baseline':>14}")
    print("   " + "-" * 69)
    for name, pv in rows:
        hit = sum(1 for s in train
                  if skel[(pv, s)].count("mature") == labels[s].count("mature"))
        print(f"   {name:<46}{hit:>4}/{n} {100*hit/n:>5.1f}%"
              f"{100*(hit-modal_m_n)/n:>+13.1f} pts")
    det_m = sum(1 for s in train if det[s].count("mature") == labels[s].count("mature"))
    print(f"   {'six-function detector':<46}{det_m:>4}/{n} {100*det_m/n:>5.1f}%"
          f"{100*(det_m-modal_m_n)/n:>+13.1f} pts")
    print(f"   {'CONSTANT modal-count baseline':<46}{modal_m_n:>4}/{n} "
          f"{100*modal_m_n/n:>5.1f}%{'--':>13}")

    # ----------------------------------------------------------------- 3 ----
    print("\n" + "=" * 86)
    print("3. THE TWO INCIPIENT-PRESENCE NUMBERS, RECONCILED")
    print("=" * 86)
    print("   Same series, same probe, same signal. Only tau differs.\n")
    for tau, what in ((0.20, "as declared -- the package's shipped default; THIS is the"),
                      (0.70, "POST-HOC -- the sweep's oracle best, chosen on these 47")):
        yes = agree = miss = false = 0
        for s in train:
            has = _incipient_plateau_boundary(rels[s], tau, "single", 3) > 0
            lab = "incipient" in labels[s]
            yes += has
            agree += (has == lab)
            miss += (lab and not has)
            false += (has and not lab)
        print(f"   tau_head = {tau:.2f}   {agree:>2}/{n} = {100*agree/n:5.1f}%   "
              f"(says yes on {yes:>2}, misses {miss:>2}, false {false:>2})")
        print(f"                 {what}")
        print(f"                 {'one scored by the gate.' if tau == 0.20 else 'cases it is scored on.'}\n")
    always_inc = sum(1 for s in train if "incipient" in labels[s])
    print(f"   for scale: constant 'always incipient' = {always_inc}/{n} = "
          f"{100*always_inc/n:.1f}%;  'never' = {n-always_inc}/{n} = {100*(n-always_inc)/n:.1f}%")
    print("\n   Both rows read the SAME filtered dz. The 51.1 % is Reader T exactly as")
    print("   PROTOCOL.md froze it. The 68.1 % appears only in the post-hoc table that")
    print("   compares filtered dz against the RAW series, where each signal is given")
    print("   its own best tau so neither is handicapped -- it is an oracle-tuned")
    print("   upper bound for the filtered signal, not a configuration anyone ran.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
