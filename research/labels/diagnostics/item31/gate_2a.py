"""Item 31, stage 2a — the gate: removal + decision (a), with NO package behaviour change.

Checks (predictions in DESIGN.md §10.5, written before this ran):

G1  `git diff develop-v2.1 -- cyclophaser/` is empty.
G2  front_b default digest over the 47 TRAIN ids = b500d2e0… — computed with
    `p15_expected_digest.digest`, whose layout was proven equal to front_b's
    generator at stage 0 (positive control). front_b's own script is not run
    here because it appends a record to a tracked file; stage 2b appends one.
G3  params-1..14 are absent from the tree and each is recoverable: `git show
    <recovery commit>:<path>` hashes to the sha256 in recovery_table.json.
    params-15 is present with its recorded hash.
G4  The frozen table equals the live signature defaults (make_defaults_2_0_0.py's
    own assertion, re-run): in 2a, filling is exactly what omission did.
G5  The evaluator's stdout is byte-identical to 33ea489's evaluator, under
    params-15 and under package defaults (TRAIN only, test never read). The old
    evaluator is run from a worktree at 33ea489 with THIS checkout's package
    forced first on sys.path, so only the evaluator differs — asserted by
    printing cyclophaser.__file__ from both runs.

The suite is run separately (`-m "not browser"`); its prediction is in §10.5.

Output: gate_2a.txt (via tee).
Run: python -P research/labels/diagnostics/item31/gate_2a.py --old-worktree <path at 33ea489>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402
import p15_expected_digest as ped  # noqa: E402

REPO = core.REPO
FRONT_B_DEFAULT = "b500d2e0b0112e5250073385639a030155e06fc21c15509fdcda88254226c4a5"


def git(*a, binary=False):
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode().strip()


def evaluator_stdout(evaluator: Path, argv: list[str]) -> tuple[str, str]:
    """Run an evaluator file with THIS checkout's package first on sys.path."""
    code = ("import sys, runpy; sys.path.insert(0, %r); import cyclophaser; "
            "print('PKG', cyclophaser.__file__, file=sys.stderr); "
            "sys.argv = [%r] + %r; runpy.run_path(%r, run_name='__main__')"
            % (str(REPO), str(evaluator), argv, str(evaluator)))
    r = subprocess.run([sys.executable, "-P", "-c", code], cwd="/tmp",
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout, r.stderr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-worktree", type=Path, required=True)
    a = ap.parse_args()
    env = core.assert_environment()
    print("environment:", json.dumps(env), "| HEAD", git("rev-parse", "--short", "HEAD"))
    ok = {}

    d = git("diff", "develop-v2.1", "--", "cyclophaser")
    ok["G1 cyclophaser/ diff empty"] = d == ""

    g = core.train_series()
    train47 = {**g["original_real"], **g["synthetic"]}
    dig = ped.digest(train47, {}, {})
    ok["G2 front_b default digest == b500d2e0…"] = dig == FRONT_B_DEFAULT
    print(f"G2 digest {dig}")

    rec = json.loads((HERE / "recovery_table.json").read_text())
    g3 = True
    for r in rec["rows"]:
        absent = not (REPO / r["file"]).exists()
        shown = hashlib.sha256(git("show", f"{rec['head']}:{r['file']}", binary=True)).hexdigest()
        g3 &= absent and shown == r["sha256"]
    p15 = REPO / "research/labels/configs/cyclophaser_params-15.yaml"
    g3 &= hashlib.sha256(p15.read_bytes()).hexdigest() == \
        "5aa61f2dec710029b46a47668812d14e6d552517b7bca8912a8e00fd130ccf04"
    g3 &= sorted(p.name for p in (REPO / "research/labels/configs").glob("*.yaml")) == \
        ["cyclophaser_params-15.yaml"]
    ok["G3 14 removed + recoverable (git show hash), params-15 intact"] = g3

    r = subprocess.run([sys.executable, "-P", str(HERE / "make_defaults_2_0_0.py")],
                       cwd="/tmp", capture_output=True, text=True)
    table_now = (REPO / "research/labels/defaults_2.0.0.json").read_bytes()
    ok["G4 frozen table == live signature defaults (regenerated, unchanged)"] = (
        r.returncode == 0 and git("diff", "--", "research/labels/defaults_2.0.0.json") == ""
        and len(table_now) > 0)

    old = a.old_worktree / "research/labels/evaluate_against_labels.py"
    new = REPO / "research/labels/evaluate_against_labels.py"
    old_p15 = str(a.old_worktree / "research/labels/configs/cyclophaser_params-15.yaml")
    new_p15 = str(p15)
    g5 = True
    for name, argv_old, argv_new in (("params-15", ["--config", old_p15], ["--config", new_p15]),
                                     ("package defaults", [], [])):
        so, eo = evaluator_stdout(old, argv_old)
        sn, en = evaluator_stdout(new, argv_new)
        pkg = {ln for ln in (eo + en).splitlines() if ln.startswith("PKG ")}
        so_n = so.replace(old_p15, "<P15>")
        sn_n = sn.replace(new_p15, "<P15>")
        same = so_n == sn_n and pkg == {f"PKG {REPO}/cyclophaser/__init__.py"}
        g5 &= same
        print(f"G5 evaluator {name}: stdout identical to 33ea489 = {so_n == sn_n} "
              f"({len(sn)} chars); package = {sorted(pkg)}; fill note on stderr: "
              f"{[ln for ln in en.splitlines() if ln.startswith('NOTE')] or 'none'}")
    ok["G5 evaluator stdout identical to 33ea489 (params-15, defaults)"] = g5

    print()
    for k, v in ok.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"GATE 2a (scripted part): {'PASS' if all(ok.values()) else 'FAIL'}")


if __name__ == "__main__":
    main()
