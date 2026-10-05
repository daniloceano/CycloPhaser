# 6. Wheel contents vs package source — develop-v2.1 `76b7932`

The wheel `cyclophaser-2.0.0-py3-none-any.whl` and the sdist were built by
`run_import_and_wheel.sh` (`python -m build`, clean worktree, new Python 3.12.9 venv).
The full listings are in `06_wheel_files.txt` and `06_sdist_files.txt`.

## Package source (tracked under `cyclophaser/`) vs wheel

| tracked file | in wheel | bytes identical to the git blob |
|---|---|---|
| `cyclophaser/__init__.py` | yes | yes |
| `cyclophaser/determine_periods.py` | yes | yes |
| `cyclophaser/find_stages.py` | yes | yes |
| `cyclophaser/lanczos_filter.py` | yes | yes |
| `cyclophaser/plots.py` | yes | yes |
| `cyclophaser/example_data/example_file.csv` (non-.py, via `package_data`) | yes | yes |

**Nothing in the package source is missing from the wheel.** The wheel holds no file under
`cyclophaser/` that is not tracked. The package code reads only one data file at runtime,
`example_data/example_file.csv` (`cyclophaser/__init__.py:4-5`,
`determine_periods.py:1835`), and that file ships. It imports nothing from `research/`,
`tools/` or `tests/`.

## Present in the repository but not in the wheel (by construction, reported for completeness)

* `LICENSE`: neither the wheel nor the sdist contains it, because `setup.py` sets
  `license_files=[]`. The licence is declared only as the `License: GPL-3.0-or-later`
  METADATA field. There is no `License-Expression` and no `License-File`.
* `tests/`, `docs/`, `research/`, `tools/`: excluded from the wheel. `find_packages` excludes
  `tests`, and the rest are not packages.
* The sdist, with no `MANIFEST.in`, gets setuptools' defaults. It contains:
  * `cyclophaser/` (all 6 files);
  * `README.md`, `setup.py`, `pyproject.toml` and a generated `setup.cfg`/`egg-info`;
  * **the 29 `tests/test_*.py` files**, which setuptools includes by default.

  It does **not** contain `tests/__init__.py`, `tests/conftest.py`, `tests/browser_harness.py`,
  `tests/synthetic/`, `tests/baselines/`, `tests/calibration_data/`, `tests/test.csv`,
  `research/` or `tools/`. The tests shipped in the sdist therefore cannot run from it.
  This is reported only; nothing was tested from the sdist.
* `cyclophaser/__pycache__/` in the local working copy: untracked and not shipped.

## METADATA of the built wheel (as it would be uploaded)

`Version: 2.0.0`, `License: GPL-3.0-or-later`, and only three classifiers
(`Development Status :: 3 - Alpha`, `Intended Audience :: Science/Research`,
`Programming Language :: Python :: 3`). There is **no `Requires-Python`**. `Requires-Dist`
copies `setup.py`'s `install_requires` (21 entries, including `setuptools>=72`,
`wheel>=0.44`, `pluggy>=1.5` and `iniconfig>=2.0` as *runtime* dependencies), plus the
extra `test` → `pytest>=8.3`.
