#!/usr/bin/env python
"""Passo 4, D5 — versioned configurations that reach the app's literal
fallbacks, and whether their results change (definition: passo4/PREVISOES.md).

    <cyclophaser env python> -P research/cleanup/passo4/d5_app_fallbacks.py

Literal fallbacks are read from the code BEFORE commit 17 (b9991c4), by AST:
every `.get(key, <literal>)` in tools/calibration_app/app.py:_preset_to_widgets
and tools/calibration_app/layer_inspector.py:mature_ledger.

* _preset_to_widgets has one caller in the app, fed with the two synthetic
  presets of tests/synthetic/cases.py (SYNTHETIC_CLEAN_PRESET,
  SYNTHETIC_NOISY_PRESET). A preset reaches a fallback when it lacks the key.
  Results: the old function (b9991c4) and the new one (HEAD) are both executed
  on each preset and their widget dicts compared. The new one is given a
  `_DEFAULTS` that raises on access, so it is on record whether it was read.
* mature_ledger is called by the app with the output of
  layer_inspector.build_args_periods; a key is reachable only if
  build_args_periods can leave it out, i.e. if it is absent from
  _ARGS_PERIODS_DEFAULTS.

Writes d5_app_fallbacks.json next to it.
"""
import ast
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path

import cyclophaser
from cyclophaser.determine_periods import get_periods, process_vorticity

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
OLD = "b9991c4"


def src(rev, path):
    if rev is None:
        return (ROOT / path).read_text()
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=ROOT, text=True)


def func_node(code, name):
    return next(n for n in ast.walk(ast.parse(code)) if isinstance(n, ast.FunctionDef) and n.name == name)


def literal_gets(fn):
    out = {}
    for n in ast.walk(fn):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get"
                and len(n.args) == 2 and isinstance(n.args[0], ast.Constant) and isinstance(n.args[1], ast.Constant)):
            out[n.args[0].value] = n.args[1].value
    return out


def loop_gets(fn):
    """`for src, ... in ((key, ...), ...): x.get(src, <literal>)` → {key: literal}."""
    out = {}
    for n in ast.walk(fn):
        if not (isinstance(n, ast.For) and isinstance(n.iter, ast.Tuple) and isinstance(n.target, ast.Tuple)):
            continue
        var = n.target.elts[0].id
        for m in ast.walk(n):
            if (isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) and m.func.attr == "get"
                    and len(m.args) == 2 and isinstance(m.args[0], ast.Name) and m.args[0].id == var
                    and isinstance(m.args[1], ast.Constant)):
                for t in n.iter.elts:
                    out[t.elts[0].value] = m.args[1].value
    return out


def load_fn(code, name, ns):
    fn = func_node(code, name)
    exec(compile(ast.Module([fn], []), f"<{name}>", "exec"), ns)
    return ns[name]


class NoRead(dict):
    reads = []

    def __getitem__(self, k):
        NoRead.reads.append(k)
        raise KeyError(f"_DEFAULTS[{k!r}] read")


def pkg_default(name):
    for fn in (process_vorticity, get_periods):
        p = inspect.signature(fn).parameters.get(name)
        if p is not None and p.default is not inspect.Parameter.empty:
            return p.default
    raise KeyError(name)


APP, LI = "tools/calibration_app/app.py", "tools/calibration_app/layer_inspector.py"
old_app, new_app = src(OLD, APP), src(None, APP)
ptw_literals = {**literal_gets(func_node(old_app, "_preset_to_widgets")),
                **loop_gets(func_node(old_app, "_preset_to_widgets"))}
ml_literals = literal_gets(func_node(src(OLD, LI), "mature_ledger"))
ptw_literals_head = {**literal_gets(func_node(new_app, "_preset_to_widgets")),
                     **loop_gets(func_node(new_app, "_preset_to_widgets"))}
ml_literals_head = literal_gets(func_node(src(None, LI), "mature_ledger"))

# the same private-package trick the app uses (app.py, synthetic loader), so that
# cases.py's relative import resolves
import types  # noqa: E402
_pkg = types.ModuleType("_d5_synthetic")
_pkg.__path__ = [str(ROOT / "tests/synthetic")]
sys.modules["_d5_synthetic"] = _pkg
spec = importlib.util.spec_from_file_location("_d5_synthetic.cases", ROOT / "tests/synthetic/cases.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
presets = {"SYNTHETIC_CLEAN_PRESET": dict(mod.SYNTHETIC_CLEAN_PRESET),
           "SYNTHETIC_NOISY_PRESET": dict(mod.SYNTHETIC_NOISY_PRESET)}

old_fn = load_fn(old_app, "_preset_to_widgets", {})
new_fn = load_fn(new_app, "_preset_to_widgets", {"_DEFAULTS": NoRead(), "_pkg_default": pkg_default})
rows = {}
for name, pre in presets.items():
    missing = sorted(k for k in ptw_literals if k not in pre)
    NoRead.reads = []
    a, b = old_fn(pre), new_fn(pre)
    rows[name] = dict(missing_keys=missing, reaches_fallback=bool(missing),
                      widgets_old=a, widgets_new=b, identical=a == b, defaults_read=list(NoRead.reads))

sys.path.insert(0, str(ROOT / "tools/calibration_app"))
import layer_inspector as li  # noqa: E402
assert Path(li.__file__).resolve().is_relative_to(ROOT)
ml_unreachable = {k: k in li._ARGS_PERIODS_DEFAULTS for k in ml_literals}
args = li.build_args_periods()
ml_in_built = {k: k in args for k in ml_literals}

n_reaching = sum(r["reaches_fallback"] for r in rows.values()) + (0 if all(ml_in_built.values()) else 1)
out = dict(
    old_rev=OLD,
    preset_to_widgets_literal_fallbacks_old=ptw_literals,
    preset_to_widgets_literal_fallbacks_head=ptw_literals_head,
    mature_ledger_literal_fallbacks_old=ml_literals,
    mature_ledger_literal_fallbacks_head=ml_literals_head,
    presets=rows,
    mature_ledger_keys_in_ARGS_PERIODS_DEFAULTS=ml_unreachable,
    mature_ledger_keys_in_build_args_periods=ml_in_built,
    configurations_reaching_a_fallback=n_reaching,
    results_changed=[n for n, r in rows.items() if not r["identical"]],
)
(HERE / "d5_app_fallbacks.json").write_text(json.dumps(out, indent=1, default=str))
print(f"literal fallbacks (old): _preset_to_widgets {len(ptw_literals)}, mature_ledger {len(ml_literals)}; "
      f"at HEAD: {len(ptw_literals_head)}, {len(ml_literals_head)}")
for n, r in rows.items():
    print(f"  {n}: missing {r['missing_keys']}; identical old/new {r['identical']}; _DEFAULTS read {r['defaults_read']}")
print(f"  mature_ledger keys always passed by build_args_periods: {ml_in_built}")
print(f"D5: configurations reaching a fallback = {n_reaching}; results changed = {out['results_changed']}")
