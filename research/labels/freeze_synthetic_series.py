#!/usr/bin/env python
"""Materialize the 12 synthetic lifecycle series to versioned CSV files.

    python research/labels/freeze_synthetic_series.py            # writes tests/synthetic/data/*.csv, refuses to clobber
    python research/labels/freeze_synthetic_series.py --force    # overwrite

Run ONCE. Freezes the CURRENT output of tests/synthetic/cases.py's generator to
file, exactly as-is -- this front does not change a single synthetic value, only
where they live. See docs/future_work.md item 10: synthetic series were
regenerated in memory on every load while the 51 real tracks were read from
file, and the 12 labels with no file backing them were exactly the ones that
went silently stale between sessions. After this script runs,
labels_core.load_synthetic_series() reads these files and never calls the
generator again, so the values a label is written against can no longer drift
from the values a later session re-hashes.

REFUSING TO OVERWRITE IS THE POINT: once the 12 are labelled against a frozen
file, silently re-freezing would repeat exactly the failure mode this front
exists to close. --force is for the one-time initial freeze only.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labels_core import (  # noqa: E402
    SYNTHETIC_DATA_DIR, SYNTHETIC_DIR, opaque_synthetic_id,
)


def _load_cases_module(synthetic_dir: Path):
    """Exec tests/synthetic/cases.py once, to read its CURRENT generator output.

    This is the one place left that still runs the generator -- deliberately: a
    one-time, human-invoked freeze, not a load-path side effect.
    """
    cases_py = synthetic_dir / "cases.py"
    pkg_name = "_cyclophaser_labels_synthetic_freeze"
    pkg = types.ModuleType(pkg_name)
    pkg.__path__ = [str(synthetic_dir)]
    sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(f"{pkg_name}.cases", cases_py)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=SYNTHETIC_DATA_DIR)
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing frozen CSVs (re-opens the class of "
                         "bug this front closes)")
    args = ap.parse_args(argv)

    mod = _load_cases_module(SYNTHETIC_DIR)

    if not args.force:
        clashes = [
            args.out_dir / f"{opaque_synthetic_id(name)}.csv"
            for name in mod.CASES
            if (args.out_dir / f"{opaque_synthetic_id(name)}.csv").exists()
        ]
        if clashes:
            print("refusing to overwrite existing frozen series:", file=sys.stderr)
            for p in clashes:
                print(f"  {p}", file=sys.stderr)
            print("  Pass --force only for the one-time initial freeze.",
                  file=sys.stderr)
            return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for case_name, case in mod.CASES.items():
        oid = opaque_synthetic_id(case_name)
        out_path = args.out_dir / f"{oid}.csv"
        series = case["series"].astype("float64")
        df = series.rename("min_max_zeta_850").to_frame()
        df.index.name = "time"
        # float_format matters: pandas' default to_csv formatting is LOSSY for
        # float64 (rounds to ~16 significant digits), which would silently
        # perturb every value on the read-back that series_sha256 hashes.
        # "%.17g" is the number of significant digits IEEE-754 double precision
        # guarantees is enough to round-trip any float64 exactly.
        df.to_csv(out_path, sep=";", float_format="%.17g")
        written.append((oid, len(series)))

    print(f"wrote {len(written)} frozen series to {args.out_dir}")
    for oid, n in sorted(written):
        print(f"  {oid}  n={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
