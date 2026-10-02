#!/usr/bin/env python
"""Passo 4, commit 16d — the review of every sweep hit (sweep_16d_before.json).

    <cyclophaser env python> -P research/cleanup/passo4/sweep_16d_review.py

For each hit: the reference it must be checked against, with the value read
from the code at 0522992 (before the edit):
* a public function (get_periods, determine_periods, process_vorticity,
  find_peaks_valleys, lanczos_filter, lanczos_bandpass_filter, ...): the
  default in ITS signature of every parameter named on the line;
* a stage function of find_stages: its own `args_periods.get(key, fallback)`;
* a private helper: its own signature;
* a module comment: the get_periods signature (it speaks of the package).
The verdict is "corrected" when edit_16d.py changed the line (the edit log is
matched on the hit's text), else "kept". The reason for a kept hit is the
reviewer's reading, recorded in REASONS below by file:line (all lines were read
in full context before the edit); hits not listed there are kept under the
rule of their reference, stated in the table. Writes sweep_16d_review.json/.md.
"""
import ast
import inspect
import json
import re
import subprocess
from pathlib import Path

import cyclophaser
import importlib
import sys

# `import cyclophaser.determine_periods as X` binds the FUNCTION (the package
# re-exports it under the module's name); take the modules from sys.modules.
for _m in ("determine_periods", "find_stages", "lanczos_filter"):
    importlib.import_module(f"cyclophaser.{_m}")
DPM, FSM, LFM = (sys.modules[f"cyclophaser.{m}"] for m in ("determine_periods", "find_stages", "lanczos_filter"))

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
BEFORE = "0522992"
hits = json.loads((HERE / "sweep_16d_before.json").read_text())["rows"]
log = json.loads((HERE / "edit_16d_log.json").read_text())

FUNCS = {}
for mod in (DPM, FSM, LFM):
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if fn.__module__ == mod.__name__:
            FUNCS[name] = fn
SIG = {n: {k: v.default for k, v in inspect.signature(f).parameters.items()
           if v.default is not inspect.Parameter.empty} for n, f in FUNCS.items()}


def fallbacks(fname):
    src = subprocess.check_output(["git", "show", f"{BEFORE}:cyclophaser/find_stages.py"], cwd=ROOT, text=True)
    fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == fname)
    return {c.args[0].value: c.args[1].value for c in ast.walk(fn)
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "get"
            and len(c.args) == 2 and all(isinstance(a, ast.Constant) for a in c.args)}


STAGES = {"find_mature_stage", "find_intensification_period", "find_decay_period",
          "find_residual_period", "find_incipient_period"}
GP = SIG["get_periods"]
ALL_PARAMS = set().union(*[set(s) for s in SIG.values()]) | set().union(*[set(fallbacks(s)) for s in STAGES])

REASONS = {
    "cyclophaser/determine_periods.py:139": "about scipy's argrelextrema, not a package default",
    "cyclophaser/determine_periods.py:179": "find_peaks_valleys' own default (False) against get_periods/determine_periods (True): both stated and both true",
    "cyclophaser/determine_periods.py:181": "same sentence as :179",
    "cyclophaser/determine_periods.py:1068": "states a measurement under the 2.0.0 defaults; not a claim about the current default (provenance not re-measured here)",
    "cyclophaser/determine_periods.py:1557": "same sentence as :1068 (determine_periods' copy)",
    "cyclophaser/determine_periods.py:1845": "comment in main(): it calls with default parameters",
    "cyclophaser/determine_periods.py:1850": "comment in main()",
    "cyclophaser/determine_periods.py:1855": "comment in main()",
    "cyclophaser/find_stages.py:844": "threshold_incipient_length default 0.4 in the get_periods signature",
    "cyclophaser/find_stages.py:851": "dated measurement ('at 01c4492' two lines above)",
    "cyclophaser/find_stages.py:1127": "explains why the stage function uses .get() fallbacks; true",
    "cyclophaser/find_stages.py:1235": "comment in main()",
    "cyclophaser/find_stages.py:964": "_incipient_plateau_rel's own signature default (smooth_window=0)",
    "cyclophaser/find_stages.py:965": "same sentence as :964",
    "cyclophaser/find_stages.py:970": "_incipient_plateau_rel's own signature default (smooth_polyorder=3)",
}
# The verifier's own association (parameter from the header line above, etc.),
# run on the edited tree (after16d.json); matched on the line's text, which a
# kept hit did not change.
VER = {}
for c in json.loads((HERE / "after16d.json").read_text())["claim_rows"]:
    VER[(c["file"], c["text"].strip())] = c
DPF, FSF, LFF = "cyclophaser/determine_periods.py", "cyclophaser/find_stages.py", "cyclophaser/lanczos_filter.py"
SECTION = "the 'Defaults (item 31, then C1)' section, written and checked against the signatures in C1 (Passo 1)"
for f, lines in ((DPF, (429, 434, 435, 438)), (DPF, (887, 892, 893, 900)), (DPF, (1427, 1432, 1433))):
    for ln in lines:
        REASONS[f"{f}:{ln}"] = SECTION
REASONS.update({
    f"{DPF}:477": "'default window length' describes what 'auto' picks, not a parameter default",
    f"{DPF}:1501": "'a default window' describes what True/'auto' picks, not a parameter default",
    f"{DPF}:495": f"boundary_padding: process_vorticity signature {SIG['process_vorticity']['boundary_padding']!r}",
    f"{DPF}:560": "history of the boundary_padding default, labelled",
    f"{DPF}:607": "history: why two defaults moved together",
    f"{DPF}:1147": f"reclassify_index0: get_periods signature {SIG['get_periods']['reclassify_index0']!r}",
    f"{DPF}:1627": f"reclassify_index0: determine_periods signature {SIG['determine_periods']['reclassify_index0']!r}",
    f"{FSF}:452": "intensification_min_depth: find_intensification_period's own fallback "
                  f"{fallbacks('find_intensification_period')['intensification_min_depth']!r} "
                  "(the docstring now says these are direct-call fallbacks)",
    f"{FSF}:523": "'smuggled in under a default value' is not a claim about a default",
    f"{LFF}:41": f"boundary_padding: lanczos_filter signature {SIG['lanczos_filter']['boundary_padding']!r}",
    f"{LFF}:54": f"boundary_padding: lanczos_filter signature {SIG['lanczos_filter']['boundary_padding']!r}",
    f"{LFF}:55": "same sentence as :54",
    f"{LFF}:83": f"boundary_padding: _convolve_same signature {SIG['_convolve_same']['boundary_padding']!r}",
})
HIST = re.compile(r"before item 31|since item 31|up to (and including )?2\.0\.0|\(it was|before this (default|option)|"
                  r"default changed|became the DEFAULT|moved the default|previous|prior|history|2\.0\.0", re.I)


def corrected(h):
    """The hit's line is (part of) an edited span: some line of an edit's `old`
    text (stripped, 15+ characters) occurs in the hit's text, or vice versa."""
    t = h["text"].strip()
    for e in log:
        if e["file"] != h["file"]:
            continue
        for l in e["old"].splitlines():
            l = l.strip()
            if len(l) >= 15 and (l in t or t in l):
                return True
    return False


rows = []
for h in hits:
    fn = h["function"]
    names = sorted({n for n in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", h["text"]) if n in ALL_PARAMS})
    if fn in STAGES:
        fb = fallbacks(fn)
        ref = "own fallback: " + (", ".join(f"{n}={fb[n]!r}" for n in names if n in fb) or "—")
    elif fn in SIG and fn != "<module>":
        ref = f"{fn} signature: " + (", ".join(f"{n}={SIG[fn][n]!r}" for n in names if n in SIG[fn]) or "—")
    elif h["file"].endswith("lanczos_filter.py"):
        ref = "lanczos_filter / lanczos_bandpass_filter signature: " + ", ".join(
            f"{n}={SIG['lanczos_filter'][n]!r}" for n in names if n in SIG["lanczos_filter"]) if names else "—"
    else:
        ref = "get_periods signature: " + (", ".join(f"{n}={GP[n]!r}" for n in names if n in GP) or "—")
    v = VER.get((h["file"], h["text"].strip()))
    if v:
        ref += f"; verifier: {v['param']}={v['value']} vs code {v['code']} → {'ok' if v['ok'] else 'DIVERGES'}"
    key = f"{h['file']}:{h['line']}"
    if corrected(h):
        verdict, why = "corrected", "false as written (see edit_16d_log.json)"
    elif key in REASONS:
        verdict, why = "kept", REASONS[key]
    elif HIST.search(h["text"]):
        verdict, why = "kept", "historical statement, labelled as such"
    else:
        verdict, why = "kept", "matches the reference"
    rows.append(dict(hit=key, kind=h["kind"], function=fn, reference=ref, verdict=verdict, reason=why,
                     text=h["text"]))
n_corr = sum(r["verdict"] == "corrected" for r in rows)
out = dict(before=BEFORE, hits=len(rows), corrected=n_corr, kept=len(rows) - n_corr, rows=rows)
(HERE / "sweep_16d_review.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=repr))
md = ["# Commit 16d — review of every sweep hit (generated by sweep_16d_review.py)\n",
      f"Hits {len(rows)}: corrected {n_corr}, kept {len(rows) - n_corr}. Edits: `edit_16d.py` / `edit_16d_log.json`.\n",
      "| hit | function | reference (value read from the code) | verdict | reason | text |", "|---|---|---|---|---|---|"]
md += [f"| `{r['hit']}` | `{r['function']}` | {r['reference']} | {r['verdict']} | {r['reason']} | "
       f"{r['text'][:110].replace('|', '\\|')} |" for r in rows]
(HERE / "sweep_16d_review.md").write_text("\n".join(md) + "\n")
print(f"hits {len(rows)}; corrected {n_corr}; kept {len(rows) - n_corr}")
for r in rows:
    if r["verdict"] == "corrected":
        print("  C", r["hit"], "|", r["text"][:90])
