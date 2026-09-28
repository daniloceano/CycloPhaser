"""Item 30 — post-merge checks on develop-v2.1, against the pre-merge tip f92569a.

1. The default evaluator (no options beyond `--config`): under params-14 and
   under package defaults, the population hash and the full printed output are
   identical to f92569a's evaluator (`prove_evaluator_default._run`: TRAIN labels
   of the 47/16 split only, test labels never read).
2. `labels_core.load_real_series()` returns 51 series.
3. R1 rerun: params-15 changes the final map of exactly the 5 adjudicated TRAIN
   series (of 54), and in each of them the final map is the counterfactual of
   1a3ad76.

Run: python research/labels/diagnostics/item30/post_merge_checks.py
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = HERE.parent.parent
REPO = LABELS.parent.parent
BEFORE = "f92569a"
sys.path.insert(0, str(HERE))
import prove_evaluator_default as ped  # noqa: E402
import item30_core as core  # noqa: E402
import part3_measure as pm  # noqa: E402

lc = core.lc


def main() -> None:
    print("HEAD:", subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                                  capture_output=True, text=True).stdout.strip(),
          "| compared against:", BEFORE)
    ok = True

    old = LABELS / "_evaluate_against_labels_before.py"
    old.write_text(subprocess.run(
        ["git", "show", f"{BEFORE}:research/labels/evaluate_against_labels.py"],
        cwd=REPO, capture_output=True, text=True, check=True).stdout)
    new = LABELS / "evaluate_against_labels.py"
    p14 = str(LABELS / "configs" / "cyclophaser_params-14.yaml")
    try:
        for argv in (["--config", p14], []):
            (ho, oo), (hn, on) = ped._run(old, argv), ped._run(new, argv)
            name = "params-14" if argv else "package defaults"
            ok &= (ho == hn) and (oo == on)
            print(f"evaluator {name}: population hash {BEFORE} {ho[:16]} merge {hn[:16]} "
                  f"identical={ho == hn} | output identical={oo == on} ({len(on)} chars)")
    finally:
        old.unlink()

    n = len(lc.load_real_series())
    ok &= n == 51
    print(f"load_real_series: {n} series (== 51: {n == 51})")

    sets = core.split_sets()
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    batch = lc.load_batch_series()
    train = {k: v for k, v in {**real, **synth}.items() if k in sets["train"]}
    train |= {k: v for k, v in batch.items() if k in sets["batch_train"]}
    assert len(train) == 54
    pm.r1(train, core.load_config("params-14"), core.load_config("params-15"))
    print(f"ALL CHECKS (evaluator + 51) OK={ok}")


if __name__ == "__main__":
    main()
