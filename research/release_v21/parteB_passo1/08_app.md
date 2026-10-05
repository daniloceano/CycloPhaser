# 8. App: requirement used by Streamlit Cloud, how it imports the package, and the tests CI skips

## Requirement on Streamlit Community Cloud

* **`tools/calibration_app/requirements.txt:21` — `cyclophaser>=2.0.0`.** The file header
  (`:1-11`) says it is the Streamlit Community Cloud dependency file and that the package
  comes from PyPI. Community Cloud reads the dependency file in the entrypoint's directory
  before the repository root, and the entrypoint is `tools/calibration_app/app.py`. The root
  `requirements.txt` is the docs toolchain and does not mention cyclophaser.
* `tools/calibration_app/requirements-app.txt:11` reads `-e ../..`. That is the local
  editable install, not Cloud.
* **Not visible from the repository:** the Cloud app's deployment settings (branch,
  entrypoint, Python version). `docs/future_work.md:4114` records that the app deploys from
  `master`, and `:4115` that its Python version must be checked in the Cloud settings. Both
  are cited as recorded, not verified here. The hosted URL is
  https://cyclophaser.streamlit.app (`docs/calibration_tool.rst:9`).
* PyPI's latest is 2.0.0 (`01_pypi_versions.txt`). It predates the parameters the app reads
  (`docs/future_work.md:4113`, §S11 of `docs/findings.md`).

## How the app imports the package

* By name, with no path manipulation that targets it:
  * `app.py:26-28` (`from cyclophaser.determine_periods import …`,
    `cyclophaser.find_stages`, `cyclophaser.plots`) and the lazy imports at `:196`, `:268`,
    `:975`;
  * `layer_inspector.py:63-64`;
  * `benchmark_core.py:74`.

  Whichever `cyclophaser` comes first on `sys.path` wins.
* `benchmark_core.py:66-72` **appends** `research/labels`,
  `research/labels/diagnostics/item19` and **the repo root** to `sys.path`. Because it
  appends, an installed copy in site-packages comes first. When no copy is installed, the
  checkout's `cyclophaser/` would be imported silently. That is not a failure.
  `app.py:30-34`, `benchmark_core.py:88-89`, `benchmark_tab.py:62-63` and
  `label_tab.py:121-122` add only the app's own folders or `research/labels`.
* **The version the app displays is not the installed one.** `app.py:43-49` sets
  `_CP_VERSION` by parsing `VERSION` from the checkout's **`setup.py`**, not from
  `importlib.metadata`. On Cloud the label shows the deployed branch's `setup.py`, which can
  differ from the PyPI version actually installed.
* The app also reads repository data by `__file__`: `tests/calibration_data`
  (`app.py:54`), `tests/synthetic` (`:57`), the example CSV in the checkout's
  `cyclophaser/example_data` (`:2513`), and `research/labels` (labels, split, configs).
  Cloud therefore needs the full checkout, not only the package.

## App tests skipped by the CI recipe

From the R0 run (`05_import_summary.json`, junit of the CI recipe: 35 skipped). Counts of
modules skipped whole come from `--collect-only` in the conda env `cyclophaser`, which has
streamlit 1.63.0 and plotly 7.0.0; nothing was run there.

| module | what skips under CI | tests | reason / mechanism |
|---|---|---|---|
| `tests/test_app_distance_removed.py` | whole module | 16 | `importorskip("streamlit")` at `:36` |
| `tests/test_benchmark_apptest.py` | whole module | 55 | streamlit, `:42` |
| `tests/test_inspector_apptest.py` | whole module | 4 | streamlit, `:28` |
| `tests/test_label_apptest.py` | whole module | 13 | streamlit, `:36` |
| `tests/test_sidebar_coverage.py` | whole module | 41 | streamlit, `:38` |
| `tests/test_sidebar_defaults.py` | whole module | 7 | streamlit, `:33` |
| `tests/test_track_upload_apptest.py` | whole module | 10 | streamlit, `:38` |
| `tests/test_label_browser.py` | whole module | 29 (count from `CLAUDE.md`; not collected here) | playwright, `:40`. Browser tests are run by hand and **must not be run by an agent**. |
| `tests/test_app_passo5_fixes.py` | 7 of 22 | 7 | `importorskip("streamlit")` in `_app()` (`:57`) |
| `tests/test_layer_inspector.py` | 4 of 282 | 4 | `importorskip("plotly")` (`:617`, `:658`, `:696`, `:803`) |
| `tests/test_manual_labels.py` | 15 of 82 | 15 | `requires_streamlit` (`:78`) / `importorskip("streamlit")` (`:914`), "the labelling tab is calibration-app code" |

Not an app test: 1 skip in `tests/synthetic/test_synthetic_lifecycles.py` ("Timing not
checked for observational cases").

## How to run them against an installed PyPI version (described, not run)

1. Create a new venv outside the repository with the Python the Cloud app uses (3.12 is
   recorded, not verified). Install exactly what Cloud resolves, plus pytest:
   `pip install -r tools/calibration_app/requirements.txt pytest`. That brings in
   `cyclophaser>=2.0.0` from PyPI. For a fixed candidate, add
   `"cyclophaser==<version>"`. For a TestPyPI candidate, add
   `--index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/`.
2. Do **not** install playwright. Without it, `test_label_browser.py` stays skipped at
   collection. Also pass `-m "not browser"`.
3. From the repo root, run **bare `pytest`, not `python -m pytest`**, with
   `--import-mode=append`. That is alternative A2 of `05_import_mode.md`, which measurably
   imports the installed copy. Add `-p cp_import_probe` with
   `research/release_v21/parteB_passo1/` on `PYTHONPATH` to record
   `cyclophaser.__file__` inside the session. Then assert it is under `site-packages`.
   Target the modules above:
   `pytest --import-mode=append -m "not browser" tests/test_app_distance_removed.py tests/test_benchmark_apptest.py tests/test_inspector_apptest.py tests/test_label_apptest.py tests/test_sidebar_coverage.py tests/test_sidebar_defaults.py tests/test_track_upload_apptest.py tests/test_app_passo5_fixes.py tests/test_layer_inspector.py tests/test_manual_labels.py`
4. Caveats for reading the result:
   * The app code under test is the checkout's (`tools/calibration_app`), combined with
     the PyPI package. That is the same combination Cloud runs.
   * Against today's PyPI **2.0.0**, failures are expected, because the app reads
     parameters 2.0.0 does not have. The run is informative only against the release
     candidate.
   * Any test that imports `research/labels/diagnostics/item30/item30_core.py` fails by
     design under an installed copy (`05_import_mode.md`). A grep of the 10 modules listed
     above finds no `item30_core`/`figs_cf` import and no `cyclophaser.__file__` assertion.
     The same grep over `tests/*.py`, `research/labels/*.py` and
     `tools/calibration_app/*.py` finds no `cyclophaser.__file__` either.
