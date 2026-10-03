# 5. Which cyclophaser does the suite import? — measured, nothing applied

Run by `run_import_and_wheel.sh 76b7932`. Each variant used the same clean, detached worktree
of develop-v2.1 `76b7932` and the same new Python 3.12.9 venv, provisioned with the CI's own
steps: `pip install --upgrade pip build`, `python -m build`, `pip install <wheel>`,
`pip install pytest pyyaml`. playwright is absent, so `tests/test_label_browser.py` skips
whole at collection, as in CI. `.github/` and all tracked files were left untouched. The
built artefacts went to a scratch directory, and the worktree was clean while the suite ran.

`cyclophaser.__file__` was read **inside** each pytest session by the plugin
`cp_import_probe.py` (`-p cp_import_probe`). The plugin reads `sys.modules`, meaning the
modules the tests actually imported, at collection end and at session end. Every
`cyclophaser.*` submodule came from the same directory as `cyclophaser/__init__.py` in every
run. Counts are from junit. Raw output: `05_06_run_raw.txt`. Summary:
`05_import_summary.json` (with `failed_ids`).

| id | cwd | invocation | `cyclophaser.__file__` (in-session) | passed | failed | skipped |
|---|---|---|---|---|---|---|
| R0 (CI today) | repo root | `python -m pytest` | `<wt>/cyclophaser/__init__.py` — **source** | 1279 | 0 | 35 |
| A1 | repo root | `pytest --import-mode=importlib` (no `python -m`) | `<venv>/…/site-packages/cyclophaser/__init__.py` — **wheel** | 1278 | 1 | 35 |
| A2 | repo root | `pytest --import-mode=append` (no `python -m`) | `<venv>/…/site-packages/cyclophaser/__init__.py` — **wheel** | 1278 | 1 | 35 |
| A3 | outside the repo | `python -m pytest <wt>` | `<wt>/cyclophaser/__init__.py` — **source** | 1260 | 19 | 35 |
| A4 | outside the repo | `python -P -m pytest --import-mode=importlib <wt>` | `<venv>/…/site-packages/cyclophaser/__init__.py` — **wheel** | 1259 | 20 | 35 |

## What each result is due to

* **Why R0 imports the source.** There are two independent reasons.
  1. `python -m` puts the CWD (the repo root) first on `sys.path`.
  2. `tests/__init__.py` exists, so pytest's default `--import-mode=prepend` inserts the
     *parent of the top-level test package* (again the repo root) at `sys.path[0]` during
     collection.

  Removing only one of the two is not enough. A3 shows this: run from outside the root,
  `python -m pytest` still imports the source because of reason 2.
* **A1 and A2 import the wheel and still find the data.** Every test locates its data and
  helper modules through `REPO_ROOT = Path(__file__)…`, and that works from the root.
  A2 keeps `from tests.synthetic…` working because it puts the root *last* on `sys.path`.
* **A1/A2's single failure is a guard, not the wheel.** The failing test is
  `tests/test_item30_spare_intensification.py::test_params_track_reproduces_the_counterfactual_in_the_five`,
  and it fails at import of the research module
  `research/labels/diagnostics/item30/item30_core.py:66`. That line asserts
  `Path(cyclophaser.__file__).resolve().is_relative_to(REPO)`, an anti-shadowing guard
  that refuses by design to run against any installed copy. The `AssertionError` message is
  the site-packages path. It will fail under any invocation that imports the wheel.
* **A3 and A4 add 19 failures because of CWD-relative paths.** Three test files open data by
  a path relative to the CWD, not to `__file__`:
  * `tests/test_determine_periods.py:14`: `'tests/test.csv'` (1 test)
  * `tests/test_regression_baseline.py:23`: `BASELINES_DIR = "tests/baselines"` (4 tests)
  * `tests/test_use_filter_bool.py:55`: `"tests/calibration_data/20160735.csv"` (14 tests,
    errors in a fixture)

  All 19 are `FileNotFoundError`. A4 also has the guard failure above (20 in total).
* Apart from that guard, the suite passes the same way against the wheel (A1/A2) as against
  the source (R0): 1278 of R0's 1279 pass, and the one that does not is the guard.

## Not applied

None of these was applied to CI, tests or configuration.
