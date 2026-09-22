#!/usr/bin/env python
"""Front B - the default-behaviour SHA256, the integrity reference for part 2.

    python research/labels/diagnostics/front_b/default_behaviour_hash.py

WHAT IS HASHED - exact definition
---------------------------------
1. SERIES. The 47 ids listed under `train:` in `research/labels/split.yaml`
   (35 real + 12 synthetic), sorted ascending as Python strings. Real series are
   read by `labels_core.load_real_series()` from `tests/calibration_data/*.csv`
   (column `min_max_zeta_850`, `;` separator, pandas' DEFAULT float parser -
   see that function's docstring for why not round_trip). Synthetic series are
   read by `labels_core.load_synthetic_series()` from the FROZEN CSVs in
   `tests/synthetic/data/`, never regenerated from `cases.py`.
   The 16 TEST ids are not read at all.

2. CONFIG. `get_periods(process_vorticity(df))` with NO arguments beyond the
   frame - i.e. cyclophaser PACKAGE DEFAULTS, not `cyclophaser_params-9.yaml`.
   Defaults are used deliberately: the hash must detect an unintended change to
   the shipped behaviour, so it must not be pinned to one calibration export.

3. FORMAT. For each id, in sorted order, one line:

       "<id>:<p0>|<p1>|...|<pN-1>"

   where each `p` is `str()` of that timestep's entry in the returned `periods`
   column (phase names carry the detector's own numbering, e.g.
   "intensification 2"). Lines are joined with "\n" - no trailing newline.

4. HASH. `hashlib.sha256(blob.encode()).hexdigest()` over the UTF-8 bytes.

`series_sha256` from `labels_core` is verified for every series before hashing,
so a drifted input fails loudly instead of silently changing the digest.

PROVENANCE - why every run records its environment
--------------------------------------------------
The digest is a property of (this code) x (these series) x (the libraries that
computed them). For a long time it was written down as a bare constant, which
invites two opposite errors: reading a match as proof of portability, and
reading a mismatch as proof that the code changed.

So each run appends a RECORD carrying the digest together with the commit and
the python/numpy/scipy/pandas versions that produced it. Records accumulate:
this script never rewrites or removes an earlier one, because the value of the
table is precisely that it shows the digest under several environments.

Measured so far (see the .txt): the digest is STABLE across numpy 2.4.4/scipy
1.17.1/pandas 3.0.2 and numpy 2.5.3/scipy 1.18.0/pandas 3.0.5. A mismatch is
therefore a real signal about the code until some future record shows otherwise
- which is exactly what the table exists to reveal.

WHAT THIS DIGEST IS NOT INTERCHANGEABLE WITH
--------------------------------------------
Any other "hash of the default behaviour" computed with a different blob
layout. The format in section 3 is the definition; a digest built by
concatenating the same phase strings with different separators is a different
number over the same behaviour, and comparing the two measures nothing. If you
need a default-behaviour digest, call THIS script rather than writing a second
one.
"""
from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "research" / "labels"))
sys.path.insert(0, str(REPO))

from labels_core import (load_real_series, load_synthetic_series, read_labels,
                         read_split, series_sha256)
from cyclophaser.determine_periods import get_periods, process_vorticity

OUT = Path(__file__).resolve().parent


def main():
    import cyclophaser
    print(f"cyclophaser.__file__ = {cyclophaser.__file__}")
    if not str(Path(cyclophaser.__file__).resolve()).startswith(str(REPO.resolve())):
        sys.exit("REFUSING: cyclophaser does not resolve to this working tree.")

    split = read_split()
    train = set(split["train"])
    real = {k: v for k, v in load_real_series().items() if k in train}
    syn = {k: v for k, v in load_synthetic_series()[0].items() if k in train}
    series = {**real, **syn}
    assert len(series) == len(train), f"{len(series)} != {len(train)}"

    labels = read_labels()
    stale = [sid for sid, v in series.items()
             if sid in labels and series_sha256(v) != labels[sid]["series_sha256"]]
    if stale:
        sys.exit(f"REFUSING: series_sha256 mismatch on {stale}")
    print(f"series_sha256 verified for all {len(series)} training series.")

    recs = []
    for sid in sorted(series):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = get_periods(process_vorticity(pd.DataFrame({"zeta": series[sid]})))
        recs.append(sid + ":" + "|".join(res["periods"].astype(str)))

    blob = "\n".join(recs)
    digest = hashlib.sha256(blob.encode()).hexdigest()

    prov = provenance()
    print(f"n_series = {len(recs)}")
    print(f"SHA256   = {digest}")
    print("provenance:")
    for k in ("commit", "python", "numpy", "scipy", "pandas"):
        print(f"  {k:8s}: {prov[k]}")

    path = OUT / "default_behaviour_sha256.txt"
    added = append_record(path, digest, len(recs), prov)
    print(f"\n{'appended a new record to' if added else 'record already present in'} {path}")


def provenance() -> dict:
    """The environment this digest was produced in."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
            text=True, check=True).stdout.strip()
    except Exception:
        commit = "unknown"
    return {
        "commit": commit,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
    }


HEADER = (
    "Front B - default-behaviour SHA256 (integrity reference for part 2)\n"
    "Generated by: research/labels/diagnostics/front_b/default_behaviour_hash.py\n"
    "See that script's module docstring for the exact definition.\n\n"
    "series  : 47 TRAIN ids from research/labels/split.yaml, sorted ascending\n"
    "          (35 real from tests/calibration_data, 12 synthetic from the\n"
    "          frozen tests/synthetic/data CSVs). TEST split not read.\n"
    "config  : cyclophaser PACKAGE DEFAULTS - get_periods(process_vorticity(df))\n"
    "          with no further arguments. NOT cyclophaser_params-9.yaml.\n"
    "format  : one line per id, '<id>:<periods joined by |>', lines joined\n"
    "          with newline, no trailing newline; sha256 of the UTF-8 bytes.\n"
    "\n"
    "The digest depends on the code, the series AND the libraries that computed\n"
    "them, so each run is recorded below WITH its environment. Records are\n"
    "append-only: an earlier one is never rewritten or removed, because the\n"
    "table's whole value is showing the digest under several environments.\n"
    "\n"
    "A digest computed with any other blob layout is a different number over the\n"
    "same behaviour and must not be compared against these.\n"
)
SEP = "--- record ---"


def append_record(path: Path, digest: str, n_series: int, prov: dict) -> bool:
    """Append this run's record. Never rewrites or drops an existing one.

    Returns False when an identical record is already present, so re-running
    the script does not grow the file with duplicates.
    """
    existing = ""
    if path.is_file():
        text = path.read_text()
        idx = text.find(SEP)
        existing = text[idx:].rstrip("\n") if idx != -1 else ""

    record = (
        f"{SEP}\n"
        f"sha256  : {digest}\n"
        f"n_series: {n_series}\n"
        f"commit  : {prov['commit']}\n"
        f"date    : {prov['date']}\n"
        f"python  : {prov['python']}\n"
        f"numpy   : {prov['numpy']}\n"
        f"scipy   : {prov['scipy']}\n"
        f"pandas  : {prov['pandas']}\n"
    )
    if record.strip() in existing:
        return False

    body = (existing + "\n" + record) if existing else record
    path.write_text(HEADER + "\n" + body.lstrip("\n"))
    return True


if __name__ == "__main__":
    main()
