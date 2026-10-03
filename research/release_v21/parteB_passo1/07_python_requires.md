# 7. Python version: declared vs tested — develop-v2.1 `76b7932`

| source | what it says |
|---|---|
| `setup.py` `python_requires` | **absent**. The built METADATA has no `Requires-Python`, and PyPI's JSON shows `requires_python: None` for the published 2.0.0. |
| `setup.py` classifiers (`setup.py:47-51`) | only `Programming Language :: Python :: 3`. There is no `:: 3.x` classifier and no `:: 3 :: Only`. |
| `pyproject.toml` | `[build-system]` only, with no `[project]` table. |
| CI (`.circleci/config.yml:17,35,57`) | `cimg/python:3.12.3` in all three jobs. **Only 3.12 is tested.** |
| local suite runs on record | Python 3.12.14 in the conda env `cyclophaser` (`environment.yml`: `python=3.12`) and 3.12.9 in the venvs of the CI recipe. |
| Streamlit Cloud | `tools/calibration_app/requirements.txt:10-11` says the Python version is set in the app settings, not read from a file. `runtime.txt` (`python-3.12`) and `.python-version` (`3.12`) still exist on **master** but were removed on develop in `0b21e51`. |

## Floor that `install_requires` implies, independent of declarations

From each floor's own `requires_python` on PyPI:
* `numpy>=2.1`: 2.1.0 needs Python ≥3.10.
* `scipy>=1.14`: 1.14.0 needs ≥3.10.
* `xarray>=2024.9`: 2024.9.0 needs ≥3.10.
* `pandas>=2.2`, `matplotlib>=3.9`: ≥3.9.

So an install resolves only on **Python ≥3.10**, even though the package declares no
limit. That leaves Python 3.10, 3.11 and 3.13+ installable and **untested**. Nothing has
been measured on them.
