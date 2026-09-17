import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
rows = json.load(open(REPO/"research/labels/diagnostics/front_b/train_raw.json"))
by = {r["id"]: r for r in rows}

for tid in ("20160735", "20203947"):
    r = by[tid]
    print("="*78)
    print(f"{tid}   ({r['source']}, n={r['n']} steps, sha256 OK={r['sha_ok']})")
    print("="*78)
    print(f"  detected sequence : {' -> '.join(r['det_seq'])}")
    print(f"  labelled sequence : {' -> '.join(r['lab_seq'])}")
    print()
    print("  MATURE window")
    for a, b in r["det_mature"]:
        print(f"    detected : start={a:4d}  end={b:4d}  duration={b-a+1:3d} steps")
    if not r["det_mature"]:
        print("    detected : NONE")
    for a, b, t, u in r["lab_mature"]:
        print(f"    label    : start={a:4d}  end={b:4d}  duration={b-a+1:3d} steps"
              f"   (tolerance_idx={t}, unsure={u})")
    if r["det_mature"] and r["lab_mature"]:
        da, db = r["det_mature"][0]
        la, lb, lt, _ = r["lab_mature"][0]
        print(f"    delta    : start {da-la:+d}   end {db-lb:+d}   "
              f"duration {(db-da+1)-(lb-la+1):+d}  (margin +/-{lt})")
    print()
    ex = r["ex"]
    print("  z EXTREMA  (raw -> kept), interior drops attributed")
    print(f"    raw peaks   ({len(ex['raw_peaks']):3d}): {ex['raw_peaks']}")
    print(f"    kept peaks  ({len(ex['kept_peaks']):3d}): {ex['kept_peaks']}")
    print(f"    raw valleys ({len(ex['raw_valleys']):3d}): {ex['raw_valleys']}")
    print(f"    kept valleys({len(ex['kept_valleys']):3d}): {ex['kept_valleys']}")
    print()
    dp = {int(k): v for k, v in ex["dropped_peaks"].items()}
    dv = {int(k): v for k, v in ex["dropped_valleys"].items()}
    print(f"    dropped peaks   by prominence: {sorted(k for k,v in dp.items() if v=='prominence')}")
    print(f"    dropped peaks   by distance  : {sorted(k for k,v in dp.items() if v=='distance')}")
    print(f"    dropped valleys by prominence: {sorted(k for k,v in dv.items() if v=='prominence')}")
    print(f"    dropped valleys by distance  : {sorted(k for k,v in dv.items() if v=='distance')}")
    print()
    print(f"    kept peaks  if distance DISABLED: {ex['kept_peaks_no_distance']}")
    print(f"    kept valleys if distance DISABLED: {ex['kept_valleys_no_distance']}")
    same = (ex['kept_peaks']==ex['kept_peaks_no_distance'] and
            ex['kept_valleys']==ex['kept_valleys_no_distance'])
    print(f"    => distance filter changes the extremum set? {'NO' if same else 'YES'}")
    print()
