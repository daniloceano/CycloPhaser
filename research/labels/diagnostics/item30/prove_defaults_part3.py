"""Item 30, part 3 — the DEFAULT loaders and the DEFAULT evaluator are unchanged.

Part 3 edits `labels_core.py` (the adjudication note, the validation role) and
`evaluate_against_labels.py` (the ADJUDICATED block), so byte identity is no
longer the claim. The claim is behaviour: against 1a3ad76, the commit before
part 3, run side by side,

1. `labels_core.load_real_series` and `load_synthetic_series`: same ids, same
   series (population hash over sorted {id: series_sha256});
2. `benchmark_core.load_all_series` and `split_membership`: same population
   hash, sources and membership;
3. the evaluator's default path (`--config params-14`, and package defaults):
   same population hash and the same full printed output, via
   `prove_evaluator_default._run` (TRAIN labels only; test labels never read).

Run: python research/labels/diagnostics/item30/prove_defaults_part3.py
"""

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = HERE.parent.parent
REPO = LABELS.parent.parent
APP = REPO / "tools" / "calibration_app"
BEFORE = "1a3ad76"
sys.path.insert(0, str(HERE))
import prove_evaluator_default as ped  # noqa: E402
import labels_core as lc  # noqa: E402


def _git_show(rel: str) -> str:
    return subprocess.run(["git", "show", f"{BEFORE}:{rel}"], cwd=REPO,
                          capture_output=True, text=True, check=True).stdout


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # @dataclass resolves its module by name
    spec.loader.exec_module(mod)
    return mod


def _h(series: dict) -> str:
    return hashlib.sha256(repr(sorted(
        (k, lc.series_sha256(v)) for k, v in series.items())).encode()).hexdigest()


def main() -> None:
    ok = True
    tmp = []
    try:
        # 1 — labels_core loaders
        p = LABELS / "_labels_core_before.py"
        p.write_text(_git_show("research/labels/labels_core.py"))
        tmp.append(p)
        old = _load(p, "_labels_core_before")
        for fn in ("load_real_series", "load_synthetic_series"):
            a = getattr(old, fn)()
            b = getattr(lc, fn)()
            a, b = (a[0], b[0]) if isinstance(a, tuple) else (a, b)
            same = _h(a) == _h(b)
            ok &= same
            print(f"labels_core.{fn}: {len(b)} series, population hash before "
                  f"{_h(a)[:16]} after {_h(b)[:16]} identical={same}")

        # 2 — benchmark loader
        p = APP / "_benchmark_core_before.py"
        p.write_text(_git_show("tools/calibration_app/benchmark_core.py"))
        tmp.append(p)
        ob = _load(p, "_benchmark_core_before")
        nb = _load(APP / "benchmark_core.py", "_benchmark_core_now")
        (so, xo), (sn, xn) = ob.load_all_series(), nb.load_all_series()
        same = (_h(so) == _h(sn), xo == xn, ob.split_membership() == nb.split_membership())
        ok &= all(same)
        print(f"benchmark load_all_series: population hash before {_h(so)[:16]} after "
              f"{_h(sn)[:16]} identical={same[0]} | sources identical={same[1]} | "
              f"split_membership identical={same[2]}")

        # 3 — evaluator default path
        p = LABELS / "_evaluate_against_labels_before.py"
        p.write_text(_git_show("research/labels/evaluate_against_labels.py"))
        tmp.append(p)
        new = LABELS / "evaluate_against_labels.py"
        p14 = str(LABELS / "configs" / "cyclophaser_params-14.yaml")
        for argv in (["--config", p14], []):
            (ho, oo), (hn, on) = ped._run(p, argv), ped._run(new, argv)
            name = "params-14" if argv else "package defaults"
            ok &= (ho == hn) and (oo == on)
            print(f"evaluator {name}: population hash before {ho[:16]} after "
                  f"{hn[:16]} identical={ho == hn} | output identical={oo == on} "
                  f"({len(on)} chars)")
    finally:
        for p in tmp:
            p.unlink()
    print(f"ALL IDENTICAL={ok}")


if __name__ == "__main__":
    main()
