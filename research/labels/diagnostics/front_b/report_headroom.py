import json, hashlib, sys, warnings, collections
from pathlib import Path
import pandas as pd
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO/"research/labels")); sys.path.insert(0, str(REPO))
from labels_core import load_real_series, load_synthetic_series, read_split
from cyclophaser.determine_periods import get_periods, process_vorticity

OUT = REPO/"research/labels/diagnostics/front_b"
rows = json.load(open(OUT/"train_raw.json"))
lines = []
def P(s=""):
    print(s); lines.append(s)

P("FRONT B - part 1 - `distance` headroom and default-behaviour hash")
P("="*90)
P("\n[5] Minimum separation between SURVIVING same-type z extrema, per series")
P("    (the quantity `distance` compares against; distance=5 is inert because")
P("     prominence_relative=0.3 already leaves nothing closer than this)")
P()
mins = []
for r in rows:
    ex = r["ex"]
    g = []
    for key in ("kept_peaks", "kept_valleys"):
        v = sorted(ex[key])
        g += [b-a for a, b in zip(v, v[1:])]
    m = min(g) if g else None
    if m is not None:
        mins.append((m, r["id"], r["source"]))
mins.sort()
P(f"    smallest surviving same-type gaps across the 47 train series:")
for m, i, s in mins[:12]:
    P(f"        {m:4d}  {i}  ({s})")
P(f"    ...")
P(f"    global minimum gap = {mins[0][0]}  ->  `distance` only starts removing")
P(f"    extrema once it exceeds {mins[0][0]}; at the reference value 5 it is a no-op.")
P(f"    gap histogram (min per series): "
  f"{dict(sorted(collections.Counter(m for m,_,_ in mins).items()))}")

# --- default-behaviour hash -------------------------------------------------
P("\n[6] Default-behaviour SHA256 (integrity reference for part 2)")
P("    No such artefact existed in the repo; this defines one explicitly.")
P("    Definition: cyclophaser at PACKAGE DEFAULTS (no config), over the 47")
P("    TRAIN series in split.yaml, sorted by id. For each series the detected")
P("    `periods` column is joined with '|', prefixed by the id, and the whole")
P("    newline-joined text is sha256'd. The 16 test series are NOT read.")
split = read_split()
train = set(split["train"])
real = {k: v for k, v in load_real_series().items() if k in train}
syn = {k: v for k, v in load_synthetic_series()[0].items() if k in train}
series = {**real, **syn}
recs = []
for sid in sorted(series):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = get_periods(process_vorticity(pd.DataFrame({"zeta": series[sid]})))
    recs.append(sid + ":" + "|".join(res["periods"].astype(str)))
blob = "\n".join(recs)
h = hashlib.sha256(blob.encode()).hexdigest()
P(f"    n_series = {len(recs)}")
P(f"    SHA256   = {h}")
(OUT/"default_behaviour_sha256.txt").write_text(
    "definition: cyclophaser package defaults, 47 train series (split.yaml), "
    "sorted by id,\n'<id>:<periods joined by |>' per line, newline-joined, sha256\n"
    f"n_series: {len(recs)}\nsha256: {h}\n")
(OUT/"headroom_and_hash.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT/'headroom_and_hash.txt'} and default_behaviour_sha256.txt")
