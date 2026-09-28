"""Item 30, step 3a — `evaluate_against_labels.py`'s DEFAULT path is unchanged by --batch-train.

The evaluator as it was before the option (commit f01ca88) and as it is now
are both run on the same inputs, without the option:

* with `--config params-14`;
* with no config (package defaults).

Two things are compared: the population handed to the detector (a hash over
{id: series_sha256}) and the full printed output, scores included.

TEST labels are never read. In both runs `read_labels` is replaced by a version
that keeps only the records of the split's TRAIN ids, dropped by id and nothing
else. The default path scores TRAIN only, so its scores depend on nothing else.

Run: python research/labels/diagnostics/item30/prove_evaluator_default.py
"""

import contextlib
import hashlib
import importlib.util
import io
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = HERE.parent.parent
REPO = LABELS.parent.parent
BEFORE = "f01ca88"
sys.path.insert(0, str(LABELS))
import labels_core as lc  # noqa: E402

TRAIN = set(lc.read_split()["train"])


def _train_only(path=None):
    return {sid: r for sid, r in lc.read_labels(path).items() if sid in TRAIN}


def _run(mod_path: Path, argv: list[str]) -> tuple[str, str]:
    spec = importlib.util.spec_from_file_location(mod_path.stem, mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.read_labels = _train_only
    pop = {}
    orig = mod.run_detector

    def run_detector(series, pv, gp):
        pop.update({k: lc.series_sha256(v) for k, v in series.items()})
        return orig(series, pv, gp)

    mod.run_detector = run_detector
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert mod.main(argv) == 0
    h = hashlib.sha256(repr(sorted(pop.items())).encode()).hexdigest()
    return h, buf.getvalue()


def main() -> None:
    old = LABELS / "_evaluate_against_labels_before.py"
    old.write_text(subprocess.run(
        ["git", "show", f"{BEFORE}:research/labels/evaluate_against_labels.py"],
        cwd=REPO, capture_output=True, text=True, check=True).stdout)
    new = LABELS / "evaluate_against_labels.py"
    p14 = str(LABELS / "configs" / "cyclophaser_params-14.yaml")
    try:
        for argv in (["--config", p14], []):
            (ho, oo), (hn, on) = _run(old, argv), _run(new, argv)
            name = "params-14" if argv else "package defaults"
            print(f"{name}: population hash before {ho[:16]} after {hn[:16]} "
                  f"identical={ho == hn} | output identical={oo == on} ({len(on)} chars)")
            if argv:
                print(on)
    finally:
        old.unlink()


if __name__ == "__main__":
    main()
