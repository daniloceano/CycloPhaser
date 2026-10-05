#!/usr/bin/env python
"""Run a PUBLISHED cyclophaser release over the frozen series set and record its phases.

This is the generator behind the Benchmark tab's reference columns. It must be run
with the interpreter of an ISOLATED virtual environment that has the published
release installed — never in the `cyclophaser` conda environment, which carries the
working tree in editable mode:

    python -m venv /tmp/venv_1_9_4
    /tmp/venv_1_9_4/bin/pip install cyclophaser==1.9.4
    cd /   # anywhere that is NOT the repo root
    /tmp/venv_1_9_4/bin/python -P <repo>/research/snapshots/make_published_snapshot.py \
        --repo <repo> --out <repo>/research/snapshots/v1.9.4.json

Two things about that invocation are load-bearing, not style:

* `-P` (and running from outside the repo) keeps the CWD off `sys.path`. Without it,
  a run started from the repo root imports the WORKING TREE's `cyclophaser/` package
  instead of the installed release and silently snapshots the wrong code — measured
  during this front: both venvs reported the working tree's `determine_periods.py`
  until the CWD was moved. This is the same shadowing class as backlog item 13.
* only `<repo>/research/labels` goes on `sys.path` (for `labels_core`, which imports
  nothing but pandas), never `<repo>` itself — that directory contains the
  `cyclophaser` package and would reintroduce the shadowing this script exists to
  avoid.

The script refuses to run if `cyclophaser` did not resolve inside the running
interpreter's own site-packages, so the mistake above cannot produce a file.

A series whose detection raises is recorded with its traceback under `"error"` and
`"phases": null`. It is never dropped: a snapshot missing a track would understate
the divergence it exists to measure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import traceback
import warnings
from datetime import datetime, timezone
from pathlib import Path


def _published_module():
    """Import the published detector, proving it is NOT the working tree."""
    import importlib

    import cyclophaser
    mod = importlib.import_module("cyclophaser.determine_periods")
    here = Path(mod.__file__).resolve()
    # Must live under this interpreter's own environment, not under a checkout.
    prefix = Path(sys.prefix).resolve()
    if prefix not in here.parents:
        raise SystemExit(
            f"REFUSING TO RUN: cyclophaser resolved to {here}, which is not inside "
            f"this interpreter's environment ({prefix}). The working tree is "
            "shadowing the published release — re-run with `-P` from a directory "
            "outside the repository."
        )
    return cyclophaser, mod, here


def _signature_report(mod) -> dict:
    import inspect
    out = {}
    for fn in ("determine_periods", "process_vorticity", "get_periods"):
        if not hasattr(mod, fn):
            out[fn] = None
            continue
        sig = inspect.signature(getattr(mod, fn))
        out[fn] = {
            k: (None if p.default is inspect.Parameter.empty else repr(p.default))
            for k, p in sig.parameters.items()
        }
    return out


def _runs(periods, normalize) -> list[list]:
    """[[phase, start_idx, end_idx_inclusive], ...] over NORMALISED phase names."""
    names = [normalize(str(x)) for x in periods]
    out, prev, start = [], None, 0
    for i, n in enumerate(names):
        if n != prev:
            if prev is not None:
                out.append([prev, start, i - 1])
            prev, start = n, i
    if prev is not None:
        out.append([prev, start, len(names) - 1])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True,
                    help="repository root (only <repo>/research/labels is imported)")
    ap.add_argument("--out", type=Path, required=True, help="output .json path")
    ap.add_argument("--label", default=None,
                    help="human label for this snapshot (default: the installed version)")
    args = ap.parse_args(argv)

    repo = args.repo.resolve()
    # ONLY the labels helper directory. See the module docstring.
    sys.path.insert(0, str(repo / "research" / "labels"))
    from labels_core import (load_real_series, load_synthetic_series,  # noqa: E402
                             normalize_phase, series_sha256)

    cyclophaser, mod, modfile = _published_module()
    try:
        from importlib.metadata import version as _ver
        installed = _ver("cyclophaser")
    except Exception:
        installed = "unknown"

    real = load_real_series(repo / "tests" / "calibration_data")
    synth, synth_names = load_synthetic_series(repo / "tests" / "synthetic",
                                               repo / "tests" / "synthetic" / "data")

    import pandas as pd
    process_vorticity = mod.process_vorticity
    get_periods = mod.get_periods

    records: dict[str, dict] = {}
    n_failed = 0
    for source, population in (("real", real), ("synthetic", synth)):
        for sid, values in sorted(population.items()):
            rec = {
                "id": sid,
                "source": source,
                "n_steps": int(len(values)),
                "series_sha256": series_sha256(values),
                "phases": None,
                "error": None,
            }
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    vort = process_vorticity(pd.DataFrame({"zeta": values}))
                    res = get_periods(vort)
                rec["phases"] = _runs(res["periods"], normalize_phase)
            except Exception:
                rec["error"] = traceback.format_exc(limit=6).strip()
                n_failed += 1
            records[sid] = rec

    doc = {
        "snapshot": {
            "label": args.label or f"cyclophaser {installed} (published, package defaults)",
            "cyclophaser_version": installed,
            "module_file": str(modfile),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "generated": datetime.now(timezone.utc).isoformat(),
            "generator": "research/snapshots/make_published_snapshot.py",
            "parameters": "package defaults — no argument is passed to "
                          "process_vorticity or get_periods",
            "public_signature": _signature_report(mod),
            "has_collapse_plateaux": hasattr(mod, "_collapse_plateaux"),
        },
        "counts": {
            "real": len(real),
            "synthetic": len(synth),
            "total": len(records),
            "failed": n_failed,
        },
        "records": records,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, indent=2, sort_keys=False) + "\n"
    args.out.write_text(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"wrote {args.out}")
    print(f"  version  {installed}   module {modfile}")
    print(f"  series   {len(records)} ({len(real)} real + {len(synth)} synthetic), "
          f"{n_failed} failed")
    print(f"  sha256   {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
