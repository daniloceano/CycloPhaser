#!/usr/bin/env python
"""Front v3.0 premise measurement — is the filtered series a proxy for the phase INVENTORY?

    python research/v3_topology_proxy/measure_topology_proxy.py

Everything this script does, the metric it reports, the gate it is judged
against and the prediction made before it was first run are declared in
`research/v3_topology_proxy/PROTOCOL.md`, committed ahead of any output.

Reader T (see the protocol) reads only the filtered/smoothed vorticity `z` and
its derivative `dz` from `process_vorticity` at package defaults, and calls NONE
of the six phase functions. It emits a phase-name sequence. That sequence is
compared with the manual label's own phase sequence on names, order and
multiplicity only — no index is ever compared, because this front is about
inventory, not timing.

Train split only. The 16 test cases are frozen and are not read here.
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

from labels_core import (  # noqa: E402
    is_legacy_record, load_real_series, load_synthetic_series, normalize_phase,
    read_labels, read_split, series_sha256,
)
from cyclophaser.determine_periods import (  # noqa: E402
    find_peaks_valleys, get_periods, process_vorticity,
)
from cyclophaser.find_stages import (  # noqa: E402
    _incipient_plateau_boundary, _incipient_plateau_rel,
)

PHASES = ("incipient", "intensification", "mature", "decay", "residual")


# --------------------------------------------------------------------------- #
# Reader T
# --------------------------------------------------------------------------- #
def _alternating_extrema(pv: pd.Series, z: np.ndarray) -> list[tuple[int, str]]:
    """[(index, 'peak'|'valley'), ...], strictly alternating.

    `find_peaks_valleys` can mark two same-type extrema with no opposite-type
    extremum between them (it also writes a literal 0 where the data is zero,
    which is not an extremum marking at all and is ignored here). Each run of
    one type is reduced to its most extreme member — lowest z for a valley,
    highest for a peak, first on a tie.
    """
    raw = [(i, v) for i, v in enumerate(pv.tolist()) if v in ("peak", "valley")]
    out: list[tuple[int, str]] = []
    for idx, kind in raw:
        if out and out[-1][1] == kind:
            prev = out[-1][0]
            better = z[idx] < z[prev] if kind == "valley" else z[idx] > z[prev]
            if better:
                out[-1] = (idx, kind)
        else:
            out.append((idx, kind))
    return out


def reader_t(values: pd.Series) -> tuple[list[str], dict]:
    """The topology-only proxy. Returns (phase-name sequence, diagnostics)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = process_vorticity(pd.DataFrame({"zeta": values}))

    z = np.asarray(vort.vorticity_smoothed2.values, dtype=float)
    df = pd.DataFrame({"z": z, "dz": np.asarray(vort.dz_dt_smoothed2.values, dtype=float)})

    # --- 1. skeleton, from z's topology alone ---
    ext = _alternating_extrema(find_peaks_valleys(df["z"]), z)
    seq: list[str] = []
    for k in range(len(ext) - 1):
        (_, a), (_, b) = ext[k], ext[k + 1]
        if a == "peak" and b == "valley":
            seq.append("intensification")
        elif a == "valley" and b == "peak":
            # the valley opening this ascent is mature only if an intensification
            # was seen to reach it (k > 0) -- the package's own neighbour
            # confirmation, see find_mature_stage.
            if k > 0:
                seq.append("mature")
            seq.append("decay")

    # --- 2. the two flat ends, at the package's own shipped defaults ---
    rel = _incipient_plateau_rel(df, "derivative")
    head = _incipient_plateau_boundary(rel, 0.20, "single", 3)
    tail = _incipient_plateau_boundary(rel[::-1], 0.20, "single", 3)
    if head > 0:
        seq.insert(0, "incipient")
    if tail > 0:
        seq.append("residual")

    return seq, {"n_extrema": len(ext), "head": int(head), "tail": int(tail),
                 "n_valleys": sum(1 for _, k in ext if k == "valley")}


# --------------------------------------------------------------------------- #
# The current six-function detector, read as an inventory reader (criterion 3)
# --------------------------------------------------------------------------- #
def reader_detector(values: pd.Series) -> list[str]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = get_periods(process_vorticity(pd.DataFrame({"zeta": values})))
    out, prev = [], None
    for lab in res["periods"].astype(str):
        name = normalize_phase(lab)
        if name != prev:
            out.append(name)
            prev = name
    return out


# --------------------------------------------------------------------------- #
def main() -> int:
    split = read_split()
    train = list(split["train"])
    by_id = read_labels()

    real = load_real_series()
    synth, _names = load_synthetic_series()
    series = {**real, **synth}

    # --- integrity gate: every label must still describe the series on disk ---
    stale, missing, legacy = [], [], []
    for sid in train:
        rec = by_id.get(sid)
        if rec is None:
            missing.append(sid)
            continue
        if is_legacy_record(rec):
            legacy.append(sid)
            continue
        if sid not in series:
            missing.append(sid)
            continue
        if series_sha256(series[sid].values) != rec["series_sha256"]:
            stale.append(sid)
    if missing or legacy or stale:
        print("ABORT — the labels do not describe the series on disk.")
        print(f"  missing: {missing}\n  legacy: {legacy}\n  stale sha256: {stale}")
        return 1
    print(f"series_sha256 verified for all {len(train)} training cases.\n")

    rows = []
    for sid in train:
        rec = by_id[sid]
        label = [normalize_phase(p["phase"]) for p in rec["phases"]]
        try:
            proxy, diag = reader_t(series[sid])
        except Exception as exc:
            print(f"  !! {sid}: Reader T failed ({type(exc).__name__}: {exc})", file=sys.stderr)
            proxy, diag = None, {}
        try:
            det = reader_detector(series[sid])
        except Exception as exc:
            print(f"  !! {sid}: detector failed ({type(exc).__name__}: {exc})", file=sys.stderr)
            det = None
        rows.append({"id": sid, "source": rec.get("source"), "label": label,
                     "proxy": proxy, "det": det, **diag})

    n = len(rows)
    proxy_hit = sum(1 for r in rows if r["proxy"] == r["label"])
    det_hit = sum(1 for r in rows if r["det"] == r["label"])

    lab_counts = collections.Counter(tuple(r["label"]) for r in rows)
    modal_seq, modal_n = lab_counts.most_common(1)[0]

    print("=" * 78)
    print("PRIMARY METRIC — exact phase-name-sequence agreement, 47 training cases")
    print("=" * 78)
    print(f"  Reader T (topology proxy)     {proxy_hit:>3} / {n}   {100*proxy_hit/n:5.1f}%")
    print(f"  six-function detector         {det_hit:>3} / {n}   {100*det_hit/n:5.1f}%")
    print(f"  majority-class baseline       {modal_n:>3} / {n}   {100*modal_n/n:5.1f}%"
          f"   ({' -> '.join(modal_seq)})")

    print("\n  gate:")
    c1 = proxy_hit / n >= 0.70
    c2 = proxy_hit / n >= modal_n / n + 0.10
    c3 = proxy_hit >= det_hit
    print(f"    1  >= 70% (>= 33/47)                      {'PASS' if c1 else 'FAIL'}")
    print(f"    2  >= majority baseline + 10 pts          {'PASS' if c2 else 'FAIL'}"
          f"   (need >= {100*(modal_n/n + 0.10):.1f}%)")
    print(f"    3  >= six-function detector               {'PASS' if c3 else 'FAIL'}")
    print(f"\n  VERDICT: {'PASS' if (c1 and c2 and c3) else 'FAIL'}")

    # ---- by source ----
    print("\n" + "-" * 78)
    print("by source")
    print("-" * 78)
    for src in ("real", "synthetic"):
        sub = [r for r in rows if r["source"] == src]
        if not sub:
            continue
        ph = sum(1 for r in sub if r["proxy"] == r["label"])
        dh = sum(1 for r in sub if r["det"] == r["label"])
        print(f"  {src:<10} n={len(sub):<3}  Reader T {ph:>2}/{len(sub)} "
              f"({100*ph/len(sub):5.1f}%)   detector {dh:>2}/{len(sub)} ({100*dh/len(sub):5.1f}%)")

    # ---- per-phase presence/absence (the front's "presença/ausência") ----
    print("\n" + "-" * 78)
    print("per-phase PRESENCE agreement — does the proxy agree the phase exists at all?")
    print("-" * 78)
    print(f"  {'phase':<17} {'label has':>9} {'proxy has':>9} {'agree':>7} {'rate':>7}"
          f"   {'miss':>5} {'false':>6}")
    for ph in PHASES:
        lab_has = sum(1 for r in rows if ph in r["label"])
        pr_has = sum(1 for r in rows if r["proxy"] and ph in r["proxy"])
        agree = sum(1 for r in rows if r["proxy"] is not None
                    and (ph in r["label"]) == (ph in r["proxy"]))
        miss = sum(1 for r in rows if r["proxy"] is not None
                   and ph in r["label"] and ph not in r["proxy"])
        false = sum(1 for r in rows if r["proxy"] is not None
                    and ph not in r["label"] and ph in r["proxy"])
        print(f"  {ph:<17} {lab_has:>9} {pr_has:>9} {agree:>7} {100*agree/n:6.1f}%"
              f"   {miss:>5} {false:>6}")

    # ---- phase count ----
    print("\n" + "-" * 78)
    print("phase COUNT agreement (len of the sequence)")
    print("-" * 78)
    cnt = sum(1 for r in rows if r["proxy"] is not None and len(r["proxy"]) == len(r["label"]))
    print(f"  exact count match           {cnt:>3} / {n}   {100*cnt/n:5.1f}%")
    delta = collections.Counter(len(r["proxy"]) - len(r["label"])
                                for r in rows if r["proxy"] is not None)
    print("  proxy_len - label_len:", dict(sorted(delta.items())))

    # ---- cycle count: the part topology should actually be good at ----
    print("\n" + "-" * 78)
    print("SKELETON only — sequence with incipient/residual stripped from BOTH sides")
    print("-" * 78)
    def core(s):
        return [p for p in s if p in ("intensification", "mature", "decay")]
    core_hit = sum(1 for r in rows if r["proxy"] is not None and core(r["proxy"]) == core(r["label"]))
    print(f"  core-sequence match         {core_hit:>3} / {n}   {100*core_hit/n:5.1f}%")
    mat = sum(1 for r in rows if r["proxy"] is not None
              and r["proxy"].count("mature") == r["label"].count("mature"))
    print(f"  mature-count match          {mat:>3} / {n}   {100*mat/n:5.1f}%")

    # ---- the disagreements, in full ----
    print("\n" + "-" * 78)
    print("every disagreeing case")
    print("-" * 78)
    for r in rows:
        if r["proxy"] == r["label"]:
            continue
        print(f"  {r['id']:<12} [{r['source']}]")
        print(f"      label : {' -> '.join(r['label'])}")
        print(f"      proxy : {' -> '.join(r['proxy']) if r['proxy'] else 'FAILED'}")
        print(f"      det   : {' -> '.join(r['det']) if r['det'] else 'FAILED'}")
        if r.get("n_extrema") is not None:
            print(f"      (extrema={r.get('n_extrema')}, valleys={r.get('n_valleys')}, "
                  f"head_plateau={r.get('head')}, tail_plateau={r.get('tail')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
