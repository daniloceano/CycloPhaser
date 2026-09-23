#!/usr/bin/env python
"""Front A' wrapper: run an original Front A script against a pinned worktree.

Why this exists
---------------
Item 13 suspects the original Front A measurements (2026-09-09) may have run
against the PUBLISHED cyclophaser 1.7.3 wheel rather than the local checkout.
Reproducing A therefore requires proving, in the same process that produces the
numbers, which `cyclophaser` was actually imported.

Two shadowing mechanisms are live on this machine and both are checked here:

1. The dedicated `cyclophaser` conda env carries an EDITABLE install whose
   MAPPING points at the MAIN repo checkout, not at this worktree
   (`__editable___cyclophaser_2_0_0_finder`). It installs itself by APPENDING
   to `sys.meta_path`, i.e. AFTER `PathFinder`, so a `sys.path` entry still
   wins -- but that is a property of setuptools' current codegen, not a
   guarantee. The assert below is what actually establishes it.
2. Current-working-directory shadowing (lesson of item 5 / item 12): a run
   whose CWD is the main repo resolves `cyclophaser` there via `''`.

So: this wrapper puts the worktree at `sys.path[0]`, imports `cyclophaser`
BEFORE the script body runs, and HARD-ASSERTS that the loaded package -- and
the two modules Front A's mechanical claim depends on -- live inside the
worktree. Only then is the script executed, via runpy, under `__main__` with
its original argv. The printed provenance block goes verbatim into REPORT.md.

Run:
    python run_in_worktree.py --worktree <path> --script <path-under-worktree> \
        [-- <original argv ...>]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import runpy
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--script", required=True, type=Path)
    ap.add_argument("script_args", nargs="*")
    args = ap.parse_args()

    worktree = args.worktree.resolve()
    script = args.script.resolve()

    # The worktree must win over BOTH the editable finder and any CWD entry.
    sys.path.insert(0, str(worktree))

    print("=" * 74)
    print("PROVENANCE (same process, before the script body runs)")
    print("=" * 74)
    print(f"  cwd                  : {Path(os.getcwd()).resolve()}")
    print(f"  worktree             : {worktree}")
    print(f"  script               : {script}")
    print(f"  sys.executable       : {sys.executable}")
    print(f"  sys.prefix           : {sys.prefix}")

    import cyclophaser
    import cyclophaser.determine_periods  # noqa: F401
    import cyclophaser.find_stages  # noqa: F401

    # `cyclophaser.determine_periods` as an ATTRIBUTE is the function of that
    # name, which the package __init__ rebinds over the submodule; it has no
    # __file__. The module object itself is only reachable via sys.modules.
    dp = sys.modules["cyclophaser.determine_periods"]
    fs = sys.modules["cyclophaser.find_stages"]

    pkg_file = Path(cyclophaser.__file__).resolve()
    dp_file = Path(dp.__file__).resolve()
    fs_file = Path(fs.__file__).resolve()

    print(f"  cyclophaser.__file__ : {pkg_file}")
    print(f"  cyclophaser.__version__: {getattr(cyclophaser, '__version__', '<none>')}")
    print(f"  determine_periods.py : {dp_file}")
    print(f"    sha256             : {sha256_of(dp_file)}")
    print(f"  find_stages.py       : {fs_file}")
    print(f"    sha256             : {sha256_of(fs_file)}")
    print("  sys.meta_path:")
    for i, f in enumerate(sys.meta_path):
        print(f"    [{i}] {f}")

    for name, p in (("cyclophaser", pkg_file),
                    ("determine_periods", dp_file),
                    ("find_stages", fs_file)):
        if worktree not in p.parents:
            raise SystemExit(
                f"SHADOWED: {name} resolved to {p}, which is NOT inside the "
                f"worktree {worktree}. Refusing to measure.")
    print("  ASSERT OK: package and both modules load from the worktree.")
    print("=" * 74, flush=True)

    sys.argv = [str(script)] + list(args.script_args)
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
