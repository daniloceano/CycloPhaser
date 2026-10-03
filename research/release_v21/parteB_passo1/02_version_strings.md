# 2. Where the version string lives — develop-v2.1 `76b7932`

Searched across every tracked file outside `research/`. That covers declarations
(`VERSION =`, `version =`, `release =`, `__version__`, `version:`), the metadata-file
names (`CITATION*`, `codemeta*`, `.zenodo*`, `setup.cfg`, `MANIFEST.in`, `paper.*`)
and pins of `cyclophaser` itself.

## Declarations of the package's own version (both say 2.0.0)

| file:line | value | role |
|---|---|---|
| `setup.py:6` | `VERSION = '2.0.0'` | **The only source of the distribution version.** `setup(version=VERSION)` is at `setup.py:12`. `pyproject.toml` holds only `[build-system]` and has no `[project] version`. |
| `docs/conf.py:12` | `release = '2.0.0'` | Sphinx/ReadTheDocs. This is a separate literal, not read from `setup.py`. There is no `version =` in `conf.py`. |

## Places with no version at all (by design or absence)

* `cyclophaser/__init__.py` defines no `__version__`. `README.md:94` and
  `docs/future_work.md:1039` document this and point to
  `importlib.metadata.version('cyclophaser')`. No package or app code reads the version
  at runtime: `importlib.metadata` appears only in `README.md:91,95` and in
  `docs/future_work.md`.
* No `CITATION.cff`, `codemeta.json`, `.zenodo.json`, `setup.cfg` or `MANIFEST.in` is
  tracked.
* The local branch `joss-submission` (`ff5540c`, upstream gone, 27 commits not in
  develop) has `paper/paper.md`, which holds `date: "2024-09-18"` and no version.

## Strings that mention a version without declaring the package's own

| file:line | value | note |
|---|---|---|
| `tools/calibration_app/requirements.txt:21` | `cyclophaser>=2.0.0` | Floor of the app on Streamlit Cloud (see item 8). Also stated in prose at `:3`. |
| `CHANGELOG.md:10` | `## [Unreleased]` | |
| `CHANGELOG.md:822` | `## [2.0.0] - 2026-06-14` | |
| `CHANGELOG.md:941` | `## [1.9.4] - 2025-01-01` | |
| `CHANGELOG.md:945-946` | compare/tag links for `[2.0.0]` and `[1.9.4]` | There is no `[Unreleased]` link. |
| `.circleci/config.yml:1` | `version: 2.1` | CircleCI schema version, not the package's. |
| `.readthedocs.yml:5` | `version: 2` | RTD schema version, not the package's. |
| `research/labels/defaults_2.0.0.json` (file name) | `2.0.0` | Frozen pre-item-31 defaults table. Its own docs say it is **not** the 2.0.0 release (`CHANGELOG.md:77`). |
| `cyclophaser/determine_periods.py` (many docstrings, e.g. `:427`, `:472`, `:492`) and `tests/test_config_defaults.py:2` | "2.0.0" / "up to 2.0.0" | Historical references to the 2.0.0 release in prose. These are not declarations. |

## Git tags

`v1.9.4` and `v2.0.0` (annotated, `2c99a6c` → `5d99ae3`) exist locally and on the remote.
There is no `v2.1*` tag.
