# Read the Docs site: map and proposed structure (clean-up front, Passo 4, part 4b-1)

This is a map only. No page under `docs/` was rewritten. The rewrite (4b-2) waits
for Danilo to approve the structure in section 2 and answer section 3.

Every value quoted as "the code says" comes from `passo4/rtd_facts.json`, which
`passo4/rtd_facts.py` generates from the signatures, the repository and the built
site. The default divergences come from the verifier run after commit 17
(`passo4/after17.json`). Line numbers refer to `docs/*.rst` at `bffa6fe` unless
another file is named.

## 0. Local build (mirrors the new `.readthedocs.yml`)

* Environment: Python 3.12 venv, `pip install -r docs/requirements.txt`, then
  `pip install .`. There were no version conflicts: both steps exit 0 and
  `pip check` reports no broken requirements. The wheel installs as
  `cyclophaser 2.0.0`, because `setup.py` still says `VERSION = '2.0.0'` while
  the code is the unreleased development line. Header of `build_rtd_raw.txt`.
* Autodoc works now. `api.html` renders the signature of `determine_periods`
  with all its parameters (`api_html_renders_signature`), plus its docstring.
  Before the config change, autodoc could not import the package
  (`build_before_raw.json`).
* Build result (`build_rtd_raw.json`): 1 error and 2 warnings, exit 0. Before:
  0 errors and 1 warning. Autodoc now reads the docstring, and all three come
  from the docstring of `determine_periods`:
  * error: `|dz|` at `cyclophaser/determine_periods.py:1522` is read as an rst
    substitution;
  * warnings: bold (`**…**`) that spans an indentation change, at
    `cyclophaser/determine_periods.py:1481-1482` and `:1507-1508`.

  D3 predicted no errors, so **D3 is not met** under the new configuration.
  Fixing these three lines means editing `cyclophaser/`, which this front may
  not do without authorization (question Q9).
* `docs/conf.py` does not load `sphinx.ext.napoleon`. The package docstrings are
  Google style (`name (type, optional): …`), so autodoc renders them as plain
  indented text: no parameter list and no types. This is visible in
  `docs/_build/html/api.html`.

## 1. The pages today (toctree order)

### index
*Purpose.* Landing page. It says what CycloPhaser does and why, cites the
papers, and notes that tracking is out of scope. The references are listed at
the bottom.
*Stale.*
1. The paper is cited as "de Souza et al. (under review)" (lines 9 and 42).
   Its status is for Danilo to confirm (Q1).
2. The landing image `test_custom.png` was last changed in `a6842d9`
   (2024-10-18). The package code was last changed in `129b04d` (2026-09-30).
   The image shows results from the old defaults.
3. `docs/conf.py` sets `release = '2.0.0'`, but the pages describe the
   unreleased defaults. Nothing tells the reader which version the site
   documents (Q4).

*Repetition.* The introduction repeats the aim that `overview` states again.
*Missing.* A line saying which version is documented, and a pointer to what
changed since 2.0.0.

### overview
*Purpose.* Describes the method: filtering, then peak/valley-based phase rules,
with the 2024 paper's methodology figure.
*Stale* (against the defaults in the code, `overview_relevant_defaults`):
1. Line 16 says the Savitzky-Golay filter "is applied". The defaults are now
   `use_smoothing=False` and `use_smoothing_twice=False`.
2. Line 24 defines mature as the stretch "between a derivative valley and its
   following derivative peak". That is `mature_method="derivative"`; the
   default is `"amplitude"`.
3. Line 20 says incipient is "detected from unassigned periods". That is the
   geometric rule; the default is `incipient_method="plateau"`.
4. Line 14 says the endpoint oscillations of the Lanczos filter "are removed".
   `replace_endpoints_with_lowpass` now defaults to `0`, and the edges are
   handled by `boundary_padding` (default `"reflect"`), which the page does not
   mention.
5. The figure `cyclophaser_methodology.jpg` (last changed `107152a`,
   2024-09-27) shows the 2.0.0-era pipeline: panels C–D apply Savitzky-Golay
   twice (Q3).

*Repetition.* The paper citation is repeated from `index`. Northern-Hemisphere
use is repeated in `usage`.
*Missing.* The split between filtering and phase detection. Several rules have
no description at all: the prominence filter, `reclassify_index0`, the depth
floors, the decay tail and `length_scale`.

### installation
*Purpose.* Two recipes, conda and venv, that end in `pip install cyclophaser`.
*Stale.*
1. "Python 3.10 or later" (lines 9, 13 and 78) has no backing: `setup.py`
   declares no `python_requires` (`setup_python_requires` is empty).
2. `pip install cyclophaser` installs the PyPI release. The other pages
   document parameters that release does not have (docs/findings.md S11,
   "Published app against the published package").

*Repetition.* The conda and venv sections repeat the same four steps.
*Missing.* Installing from source to get the version the site documents.

### usage
*Purpose.* Explains the input format, lists the `determine_periods` arguments
with advice, and walks through one example with its outputs.
*Stale.*
1. The data-format example (line 21) shows only `time;Lat;Lon`, with no
   vorticity column. The example reads `min_max_zeta_850`, which
   `example_file` has (`example_file_columns`).
2. The custom-filtering example sets `'use_filter': True` (line 184). The code
   warns and treats this as `'auto'` (`use_filter_true_warns`).
3. The same example calls `determine_periods(series, x=x, …)` (line 190), but
   `x` is never defined.
4. The caption at line 195, "positioning corrected using default parameters",
   sits under the custom-parameter example.
5. The three output figures and the CSV preview are dated 2024
   (`images_last_commit`), before the defaults changed. The CSV preview was
   not regenerated (Q3).
6. The page quotes Portuguese inside English text: "adotada sem validação
   independente" (line 115).
7. It points readers to repository-internal paths
   (`research/labels/defaults_2.0.0.json`, line 117;
   `research/labels/configs/…`), which a PyPI user does not have.

*Repetition.* The argument list duplicates `api.rst` and the docstring, which
autodoc now renders. The Northern-Hemisphere note appears twice on the page,
in the arguments and in "Important Notes".
*Missing.* Only filtering, plotting and I/O arguments are listed. The phase
parameters are missing, and so are `get_periods` and `process_vorticity` as
entry points.

### calibration_tool
*Purpose.* Introduces the Streamlit app: features, a hosted version, a local
run, limits, and a batch script without the app.
*Stale.*
1. The YAML sections are called `filter_options` / `period_options`
   (lines 207–211). The app reads and writes `filter_params` / `phase_params`
   (`app_yaml_sections`).
2. `params.pop("replace_endpoints_with_lowpass", 24)` (line 214) falls back to
   24. The default in the code is `0`.
3. The batch `PARAMS` (lines 146–150) are 2.0.0 values: `use_filter=True`,
   `cutoff_high=48`, `replace_endpoints_with_lowpass=24` and
   `use_smoothing="auto"`. The code defaults are `'auto'`, `18.0`, `0` and
   `False`.
4. "All seven phase-detection thresholds" (line 27): seven `threshold_*`
   parameters do exist, but the sidebar now has many more phase controls.
5. The hosted-version section is a placeholder, `<STREAMLIT_APP_URL>`
   (lines 47 and 51) (Q5).
6. Line 70 says the app pulls `cyclophaser >= 2.0.0` from PyPI (so does
   `tools/calibration_app/requirements.txt`). That release lacks parameters
   the app reads (docs/findings.md S11).

*Repetition.* The batch script repeats the `usage` example.
*Missing.* The Grid, Inspector and Label modes, the Benchmark and Documentation
tabs, and a pointer to `tools/calibration_app/README.md`.

### testing
*Purpose.* One command to run the tests.
*Stale.*
1. `pytest tests/` (line 8) also collects the browser tests, which need
   Chromium. `tests/conftest.py` declares the `browser` marker, and the suite
   is run with `-m "not browser"`.
2. The page describes the tests as `tests/test.csv` "dummy data" only. There
   are 27 `test_*.py` files (`n_test_files`), including a synthetic suite
   scored against manual labels.

*Missing.* Which environment to run in. What the synthetic suite and the
regression baselines check.

### api
*Purpose.* API reference for `determine_periods`: an autodoc block, a
hand-written parameter list, and an example.
*Stale.*
1. Four stated defaults differ from the code (`after17.json`):
   `replace_endpoints_with_lowpass` 24 → `0` (line 22), `use_smoothing_twice`
   `'auto'` → `False` (line 24), `threshold_mature_distance` 0.125 → `0.18`
   (line 29), and `threshold_mature_length` 0.03 → `0.15` (line 30).
2. "Default values are 168 and 48" (line 26): the code has `cutoff_high=18.0`
   (`api_cutoff_sentence`). The verifier's claim forms missed this sentence.
3. The example reads column `min_zeta_850`, which `tests/test.csv` does not
   have (it has `min_max_zeta_850`, `tests_test_csv_columns`). It also passes
   an undefined `x`.
4. The example options are the 2.0.0 values (`api_example_option_values`).
5. The hand-written list covers 19 names. The signature has 38 parameters
   (`signature_n_params`).

*Repetition.* The hand-written list duplicates the autodoc output on the same
page.
*Missing.* Autodoc for `get_periods` and `process_vorticity`, the public entry
points besides `determine_periods`. Napoleon, so the docstrings render as
parameter lists.

### contribute
*Purpose.* Fork, branch, pull-request workflow, plus style tools.
*Stale.*
1. Pull requests are aimed at the **main** branch (line 68). The default branch
   is `master` (`default_branch`).
2. Markdown syntax in an rst file: the links `[…](https://…)` at lines 8 and 82,
   and the heading `### Additional Notes` at line 80. The heading shows up as
   literal text in `contribute.html`.
3. It recommends `flake8` / `black` (lines 84–90), but the repository has no
   configuration for either (`lint_configs_present` is empty).

*Repetition.* The test command repeats `testing`.
*Missing.* The CHANGELOG convention (`[Unreleased]`), the dedicated test
environment, and the browser marker.

### license
*Purpose.* A summary of GPL-3.0. `LICENSE` is the GPL version 3 text. No stale
value was found. `setup.py` declares `GPL-3.0-or-later`, while the page says
"Version 3". Whether "or later" is intended is Danilo's call (Q10).

### Outside the toctree
`docs/findings.md` and `docs/future_work.md` sit in `docs/` but are not pages
of the site (Q6).

### Problems per page

| page | stale | repetition | missing |
|---|---|---|---|
| index | 3 | 1 | 1 |
| overview | 5 | 1 | 1 |
| installation | 2 | 1 | 1 |
| usage | 7 | 1 | 1 |
| calibration_tool | 6 | 1 | 1 |
| testing | 2 | 0 | 1 |
| api | 5 | 1 | 1 |
| contribute | 3 | 1 | 1 |
| license | 0 | 0 | 0 |

(Counts of the numbered "Stale" items and of the "Repetition" and "Missing"
paragraphs above, made by `passo4/rtd_map_counts.py`.)

## 2. Proposed structure

The order below is for a reader who installs the package and wants phases out
of a track. Research internals (item numbers, preset histories, label files)
stay in the repository and are linked, not reproduced.

1. **Home** (`index`). What CycloPhaser does, what input it needs (a vorticity
   series along a track; tracking is out of scope), which version the site
   documents, how to cite it, and one current figure.
2. **How it works** (`overview`). Sections:
   * *Two stages: filtering, then phase detection.* Filtering
     (`process_vorticity`: Lanczos with `boundary_padding`, optional
     Savitzky-Golay) produces the smoothed series and its derivatives. Phase
     detection (`get_periods`) applies the rules to that output.
   * *Phase rules.* One subsection per phase, in detection order, each
     describing the default rule (amplitude mature, plateau incipient, depth
     floors, prominence, decay tail, `reclassify_index0`), with the
     alternatives named as options.
   * *Entry points.* `determine_periods` (filtering + detection + plots) and
     `get_periods` (detection on an already filtered series). The stage
     functions in `find_stages` are internal: they are called by `get_periods`
     with every key set, and their own fallbacks are older values
     (docs/findings.md S11).
   * The updated methodology figure (Q3).
3. **Installation.** PyPI versus source, and which of them matches this site
   (Q4). A single recipe.
4. **Quick start** (from `usage`). The example with `example_file`,
   regenerated outputs (figure and CSV), and the input format with its
   vorticity column.
5. **Defaults and what was calibrated** (new page). Sections:
   * *Current defaults.* Not typed: rendered from the signatures by autodoc, or
     by a small generated table at build time.
   * *What was calibrated.* Only the filtering for TRACK input (hourly 850 hPa
     relative vorticity along South-Atlantic tracks). The phase defaults were
     calibrated against manual labels.
   * *`params-track` versus the defaults.* `params-track` is the measured
     preset. The package defaults equal it except for `boundary_padding`
     (`"reflect"`, where the preset uses `"edge"`), and the defaults have no
     measured scores. How to pass `params-track` explicitly.
   * *The known effect of `boundary_padding`.* What `"reflect"` versus `"edge"`
     moves on the training series, citing `research/cleanup/passo1/`
     (`RELATORIO.md`, `hygiene_train.json`), with no scoring against labels.
   * *Other data.* Other levels, variables, sampling intervals and
     hemispheres: which parameters to revisit, and that this filtering was not
     calibrated.
6. **Calibration app** (`calibration_tool`). What it is for, running it
   locally, the modes and tabs (summary with a link to
   `tools/calibration_app/README.md`), YAML export with the
   `filter_params` / `phase_params` sections, the hosted version if one exists
   (Q5), and batch use.
7. **API reference** (`api`). Autodoc for `determine_periods`, `get_periods`
   and `process_vorticity`, with napoleon enabled. No hand-written parameter
   list. A short "internal functions" note for `find_stages`.
8. **Running the tests** (`testing`). The environment, `pytest -m "not browser"`,
   what the synthetic suite checks (manual labels as ground truth for timing),
   and the regression baselines.
9. **Contributing** (`contribute`). Branch model (default branch `master`),
   CHANGELOG `[Unreleased]`, tests, and style (only what the repository
   actually configures). Valid rst throughout.
10. **Changelog** (optional page including `CHANGELOG.md`) and **License**.

## 3. Questions only Danilo can answer

* **Q1 — article.** The status of "de Souza et al. (under review)" in JOSS:
  still under review, accepted or published? Which citation (and DOI) should
  the site use?
* **Q2 — audience.** Is the site for package users only, or also for
  contributors and for readers of the research record (calibration, labels,
  findings)? This decides how much of section 2.5 is shown and how much is
  linked.
* **Q3 — examples and figures.** Should the example figures and the CSV
  preview be regenerated with the current defaults on `example_file`? Should
  the 2024 methodology figure be kept as the paper's figure (labelled as
  such), redrawn for the current pipeline, or dropped? Is `example_file` the
  right example track?
* **Q4 — version.** Which version should the site document: the PyPI 2.0.0
  release or the development line? Which branch does Read the Docs build? Should
  `release` in `conf.py` change before the next release?
* **Q5 — hosted app.** Is there a public Streamlit instance? If not, is the
  section removed?
* **Q6 — findings and future work.** Should `docs/findings.md` and
  `docs/future_work.md` be on the site, or stay repository-only?
* **Q7 — Portuguese quote.** Keep "adotada sem validação independente"
  verbatim, or English only on the site?
* **Q8 — contributions.** Are pull requests from outside contributors welcome,
  and against which branch? Should any style tool be recommended when none is
  configured?
* **Q9 — docstring markup.** May a docstring-only commit in `cyclophaser/`
  (same gate as 16b: identical syntax tree without docstrings, digest
  unchanged) fix the three rst problems at
  `cyclophaser/determine_periods.py:1481-1482`, `:1507-1508` and `:1522`? May
  `sphinx.ext.napoleon` be added to `docs/conf.py`?
* **Q10 — licence wording.** GPL-3.0 "only" (the page) or "or later"
  (`setup.py`)?
* **Q11 — Python floor.** Which minimum Python version should the site state,
  given that `setup.py` declares none?
