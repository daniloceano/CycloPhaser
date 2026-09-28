"""Item 30c — the DEFAULT loader and the DEFAULT evaluator are unchanged.

30c adds an opt-in batch loader to the benchmark (`benchmark_core.load_batch`,
behind "Include swell_item30 batch"). This proves the default paths did not
move, the way `prove_evaluator_default.py` did for part 1, against the commit
before 30c (99f5a9a):

1. **Benchmark loader.** `benchmark_core.load_all_series` and `split_membership`
   of 99f5a9a and of the working tree, run side by side: the population hash
   (sha256 over sorted {id: series_sha256}), the source map and the split
   membership must be identical.
2. **`load_real_series` and the evaluator.** `labels_core.py` and
   `evaluate_against_labels.py` must be byte-identical to 99f5a9a, and the
   evaluator's default path is run old vs new (`--config params-14`, and
   package defaults) with `prove_evaluator_default._run`: population hash and
   the full printed output must be identical.

TEST labels are never read: the evaluator runs keep `_run`'s train-only
`read_labels`, and step 1 reads series, not labels.

Run: python research/labels/diagnostics/item30/prove_defaults_30c.py
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
BEFORE = "99f5a9a"
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


def _population(bc) -> tuple[str, dict, dict]:
    series, source = bc.load_all_series()
    h = hashlib.sha256(repr(sorted(
        (k, lc.series_sha256(v)) for k, v in series.items())).encode()).hexdigest()
    return h, dict(sorted(source.items())), dict(sorted(bc.split_membership().items()))


def main() -> None:
    ok = True

    # 1 — benchmark loader, old vs new
    old_path = APP / "_benchmark_core_before.py"
    old_path.write_text(_git_show("tools/calibration_app/benchmark_core.py"))
    try:
        (ho, so, mo) = _population(_load(old_path, "_benchmark_core_before"))
        (hn, sn, mn) = _population(_load(APP / "benchmark_core.py", "_benchmark_core_now"))
    finally:
        old_path.unlink()
    n_src = {s: sum(1 for v in sn.values() if v == s) for s in sorted(set(sn.values()))}
    n_mem = {m: sum(1 for v in mn.values() if v == m) for m in sorted(set(mn.values()))}
    same = (ho == hn, so == sn, mo == mn)
    ok &= all(same)
    print(f"benchmark load_all_series: population hash before {ho[:16]} after "
          f"{hn[:16]} identical={same[0]} | sources identical={same[1]} {n_src} "
          f"| split_membership identical={same[2]} {n_mem}")

    # 2 — the files behind load_real_series and the evaluator, then the evaluator
    for rel in ("research/labels/labels_core.py",
                "research/labels/evaluate_against_labels.py"):
        same = _git_show(rel) == (REPO / rel).read_text()
        ok &= same
        print(f"{rel}: byte-identical to {BEFORE}={same}")

    old = LABELS / "_evaluate_against_labels_before.py"
    old.write_text(_git_show("research/labels/evaluate_against_labels.py"))
    new = LABELS / "evaluate_against_labels.py"
    p14 = str(LABELS / "configs" / "cyclophaser_params-14.yaml")
    try:
        for argv in (["--config", p14], []):
            (ho, oo), (hn, on) = ped._run(old, argv), ped._run(new, argv)
            name = "params-14" if argv else "package defaults"
            ok &= (ho == hn) and (oo == on)
            print(f"evaluator {name}: population hash before {ho[:16]} after "
                  f"{hn[:16]} identical={ho == hn} | output identical={oo == on} "
                  f"({len(on)} chars)")
    finally:
        old.unlink()

    print(f"ALL IDENTICAL={ok}")


if __name__ == "__main__":
    main()
