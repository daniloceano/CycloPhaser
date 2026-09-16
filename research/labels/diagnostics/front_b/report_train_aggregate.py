import json, statistics
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
OUT = REPO/"research/labels/diagnostics/front_b"
rows = json.load(open(OUT/"train_raw.json"))

def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]) + 1)

def pair_mature(det, lab):
    """Pair each labelled mature with the detected mature it overlaps most."""
    out = []
    for (la, lb, lt, lu) in lab:
        best, bo = None, 0
        for (da, db) in det:
            o = overlap((da, db), (la, lb))
            if o > bo:
                best, bo = (da, db), o
        out.append(((la, lb, lt, lu), best, bo))
    return out

lines = []
def P(s=""):
    print(s); lines.append(s)

P("FRONT B - part 1 - train-split aggregate (reference config params-9)")
P("="*90)

n_multi = sum(1 for r in rows if r["cycles"] > 1)
P(f"\n[4a] series with more than one cycle (>1 z-valley bounded by two z-peaks):")
P(f"     {n_multi} of {len(rows)}")
multi_real = sum(1 for r in rows if r["cycles"] > 1 and r["source"]=="real")
multi_syn = n_multi - multi_real
P(f"     real {multi_real}/35, synthetic {multi_syn}/12")
P(f"     cycle-count histogram: "
  f"{dict(sorted(__import__('collections').Counter(r['cycles'] for r in rows).items()))}")

P(f"\n[4b] detected mature windows shorter than 7 steps:")
short_real, short_syn = [], []
for r in rows:
    shorts = [(a,b) for a,b in r["det_mature"] if (b-a+1) < 7]
    if shorts:
        (short_real if r["source"]=="real" else short_syn).append(
            (r["id"], [(a,b,b-a+1) for a,b in shorts], len(r["det_mature"])))
P(f"     real     : {len(short_real)} of 35 series have >=1 mature < 7 steps")
for i, s, tot in short_real:
    P(f"         {i}  {len(s)}/{tot} short  {[(a,b,d) for a,b,d in s]}")
P(f"     synthetic: {len(short_syn)} of 12 series have >=1 mature < 7 steps")
for i, s, tot in short_syn:
    P(f"         {i}  {len(s)}/{tot} short  {[(a,b,d) for a,b,d in s]}")

P(f"\n[4c] mature DURATION deviation (detected - label), overlap-paired:")
devs, dev_start, dev_end = [], [], []
unmatched = []
for r in rows:
    for (lab, det, o) in pair_mature(r["det_mature"], r["lab_mature"]):
        la, lb, lt, lu = lab
        if det is None:
            unmatched.append((r["id"], la, lb))
            continue
        da, db = det
        devs.append((db-da+1) - (lb-la+1))
        dev_start.append(da-la)
        dev_end.append(db-lb)
def stat(name, v):
    P(f"     {name:<22} n={len(v):3d}  median={statistics.median(v):+6.1f}  "
      f"min={min(v):+4d}  max={max(v):+4d}  mean={statistics.mean(v):+6.2f}")
stat("duration (det-label)", devs)
stat("start    (det-label)", dev_start)
stat("end      (det-label)", dev_end)
P(f"     labelled matures with NO overlapping detected mature: {len(unmatched)}")
for i, a, b in unmatched:
    P(f"         {i}  label mature [{a},{b}]")

P(f"\n[4d] series where the `distance` filter removes at least one z extremum:")
hit = [(r['id'], r['n_drop_dist']) for r in rows if r["n_drop_dist"] > 0]
P(f"     {len(hit)} of {len(rows)}")
for i, n in hit:
    P(f"         {i}  {n} removed by distance")
tot_prom = sum(r["n_drop_prom"] for r in rows)
tot_dist = sum(r["n_drop_dist"] for r in rows)
P(f"     total interior extrema removed: prominence={tot_prom}, distance={tot_dist}")

(OUT/"train_aggregate.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT/'train_aggregate.txt'}")
