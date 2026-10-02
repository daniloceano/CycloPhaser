#!/usr/bin/env python
"""Passo 4, part 4b-1 — facts the site map (passo4/rtd_map.md) cites, each read
from the code, the repository or the built site (docs/_build/html); nothing typed.

    <cyclophaser env python> -P research/cleanup/passo4/rtd_facts.py

Read-only. Writes rtd_facts.json next to it.
"""
import ast
import inspect
import json
import re
import subprocess
from pathlib import Path

import cyclophaser
from cyclophaser.determine_periods import determine_periods, get_periods, process_vorticity

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
HTML = ROOT / "docs/_build/html"


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()


def sig(fn):
    return {k: v.default for k, v in inspect.signature(fn).parameters.items()
            if v.default is not inspect.Parameter.empty}


def rst(name):
    return (ROOT / "docs" / name).read_text()


def lines_matching(name, pattern):
    return [i for i, l in enumerate(rst(name).splitlines(), 1) if re.search(pattern, l)]


D = sig(determine_periods)
F = {}

# --- defaults ---------------------------------------------------------------
F["signature_n_params"] = {"determine_periods": len(inspect.signature(determine_periods).parameters),
                           "get_periods": len(inspect.signature(get_periods).parameters),
                           "process_vorticity": len(inspect.signature(process_vorticity).parameters)}
F["defaults"] = {k: repr(v) for k, v in D.items()}
F["threshold_params"] = sorted(k for k in D if k.startswith("threshold_"))
after = json.loads((HERE / "after17.json").read_text())
F["default_divergences_in_docs"] = [dict(file=r["file"], line=r["line"], param=r["param"], stated=r["value"],
                                         code=r["code"]) for r in after["divergence_rows"]]
# claims the verifier's forms do not catch, checked here one by one
api = rst("api.rst")
F["api_cutoff_sentence"] = dict(line=lines_matching("api.rst", r"Default values are 168 and 48")[:1],
                                code_cutoff_low=D["cutoff_low"], code_cutoff_high=D["cutoff_high"])
F["api_documented_params"] = sorted(set(re.findall(r"^- \*\*(\w+)\*\*", api, re.M)))
F["api_autofunctions"] = re.findall(r"autofunction:: ([\w.]+)", api)
F["api_example_column"] = re.findall(r"track\['(\w+)'\]", api)
F["tests_test_csv_columns"] = (ROOT / "tests/test.csv").read_text().splitlines()[0].split(";")
F["example_file_columns"] = Path(cyclophaser.example_file).read_text().splitlines()[0].split(";")
F["api_example_uses_undefined_x"] = {"x=x": "x=x" in api,
                                     "x assigned": bool(re.search(r"^\s*x\s*=", api, re.M))}
F["api_example_option_values"] = {k: v for k, v in re.findall(r'"(\w+)": ([^,\n]+)', api)}
# app YAML sections, from the app's own reader
app = (ROOT / "tools/calibration_app/app.py").read_text()
F["app_yaml_sections"] = sorted(set(re.findall(r'"(filter_params|phase_params|filter_options|period_options)"', app)))
F["calibration_tool_yaml_sections"] = sorted(set(re.findall(r'"(filter_\w+|period_\w+|phase_\w+)"',
                                                             rst("calibration_tool.rst"))))
F["calibration_tool_lines"] = {
    "seven thresholds": lines_matching("calibration_tool.rst", r"seven phase-detection thresholds"),
    "STREAMLIT_APP_URL placeholder": lines_matching("calibration_tool.rst", r"<STREAMLIT_APP_URL>"),
    "use_filter=True in PARAMS": lines_matching("calibration_tool.rst", r"use_filter=True"),
    "pop(..., 24)": lines_matching("calibration_tool.rst", r'"replace_endpoints_with_lowpass", 24\)'),
    "cutoff_high=48 in PARAMS": lines_matching("calibration_tool.rst", r"cutoff_high=48"),
    "cyclophaser >= 2.0.0 from PyPI": lines_matching("calibration_tool.rst", r"cyclophaser >= 2.0.0"),
}
F["app_requirements_cyclophaser"] = [l for l in (ROOT / "tools/calibration_app/requirements.txt").read_text().splitlines()
                                     if l.startswith("cyclophaser")]
# use_filter=True handling, from the code
pv_src = inspect.getsource(process_vorticity)
F["use_filter_true_warns"] = "UserWarning" in pv_src or "warnings.warn" in pv_src
# overview claims against the defaults
F["overview_lines"] = {
    "Savitzky-Golay applied": lines_matching("overview.rst", r"Savitzky-Golay filter\*\* is applied"),
    "mature = derivative valley..peak": lines_matching("overview.rst", r"between a derivative valley and its following derivative peak"),
    "incipient from unassigned periods": lines_matching("overview.rst", r"Detected from unassigned periods"),
    "Lanczos endpoint oscillations removed": lines_matching("overview.rst", r"spurious oscillations, which are removed"),
}
F["overview_relevant_defaults"] = {k: repr(D[k]) for k in ("use_smoothing", "use_smoothing_twice", "mature_method",
                                                           "incipient_method", "replace_endpoints_with_lowpass",
                                                           "boundary_padding")}
# usage
F["usage_lines"] = {
    "data format shows only time;Lat;Lon": lines_matching("usage.rst", r"^\s+time;Lat;Lon$"),
    "x=x in custom example": lines_matching("usage.rst", r"x=x"),
    "use_filter True in custom example": lines_matching("usage.rst", r"'use_filter': True"),
    "caption 'corrected using default parameters'": lines_matching("usage.rst", r"corrected using default parameters"),
    "defaults_2.0.0.json cited": lines_matching("usage.rst", r"defaults_2\.0\.0\.json"),
    "adotada sem validacao (Portuguese quote)": lines_matching("usage.rst", r"adotada sem"),
}
F["images_last_commit"] = {p.name: git("log", "-1", "--format=%h %ad", "--date=short", "--", str(p.relative_to(ROOT)))
                           for p in sorted((ROOT / "docs/_images").iterdir())}
F["package_code_last_commit"] = git("log", "-1", "--format=%h %ad", "--date=short", "--", "cyclophaser/")
# installation / testing / contribute / index / conf
setup_src = (ROOT / "setup.py").read_text()
F["setup_version"] = re.search(r"VERSION = '([^']+)'", setup_src).group(1)
F["setup_python_requires"] = re.findall(r"python_requires\s*=\s*['\"]([^'\"]+)", setup_src)
F["installation_python_claim_lines"] = lines_matching("installation.rst", r"3\.10")
F["conf_release"] = re.search(r"release = '([^']+)'", (ROOT / "docs/conf.py").read_text()).group(1)
F["pytest_browser_marker"] = "browser" in (ROOT / "tests/conftest.py").read_text()
F["testing_command_lines"] = lines_matching("testing.rst", r"pytest tests/")
F["n_test_files"] = len([p for p in (ROOT / "tests").glob("test_*.py")])
F["default_branch"] = git("symbolic-ref", "refs/remotes/origin/HEAD").rsplit("/", 1)[-1]
F["contribute_lines"] = {
    "PR to main": lines_matching("contribute.rst", r"\*\*main\*\* branch"),
    "markdown link syntax": lines_matching("contribute.rst", r"\]\(https?://"),
    "markdown heading": lines_matching("contribute.rst", r"^### "),
    "flake8/black": lines_matching("contribute.rst", r"flake8|black"),
}
F["lint_configs_present"] = [n for n in (".flake8", "setup.cfg", "tox.ini") if (ROOT / n).exists()] + \
    (["pyproject.toml [tool.black/ruff/flake8]"] if re.search(r"\[tool\.(black|ruff|flake8)",
                                                              (ROOT / "pyproject.toml").read_text()) else [])
F["contribute_html_raw_markdown"] = {"'### Additional Notes' shown raw": "### Additional Notes" in (HTML / "contribute.html").read_text(),
                                     "'](https://' shown raw": "](https://" in (HTML / "contribute.html").read_text()}
F["index_lines"] = {"under review": lines_matching("index.rst", r"under review"),
                    "toctree pages": re.findall(r"^   (\w+)$", rst("index.rst"), re.M)}
F["docs_not_in_toctree"] = sorted(p.name for p in (ROOT / "docs").glob("*.md"))
F["api_html_renders_signature"] = all(
    re.search(r'<span class="pre">' + p + '<', (HTML / "api.html").read_text())
    for p in inspect.signature(determine_periods).parameters)
F["stage_functions_public_in_init"] = sorted(n for n in dir(cyclophaser) if not n.startswith("_"))
(HERE / "rtd_facts.json").write_text(json.dumps(F, indent=1, ensure_ascii=False, default=str))
print(json.dumps({k: F[k] for k in ("default_divergences_in_docs", "api_cutoff_sentence", "app_yaml_sections",
                                     "calibration_tool_yaml_sections", "api_example_column", "setup_python_requires",
                                     "default_branch", "contribute_html_raw_markdown", "images_last_commit",
                                     "package_code_last_commit", "lint_configs_present", "use_filter_true_warns",
                                     "stage_functions_public_in_init", "api_html_renders_signature")},
                 indent=1, default=str))
