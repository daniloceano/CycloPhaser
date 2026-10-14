"""Pytest plugin (loaded with ``-p ci_probe``) that records WHERE things came from.

Copied into each venv's site-packages by make_venv.sh, so loading it adds no
repository path to ``sys.path``. At session end it writes, to the JSON file
named by $CIPROBE_OUT:

* the interpreter, ``sys.prefix`` and the final ``sys.path`` (in order);
* the origin of every loaded ``cyclophaser*`` module, and whether it lies in
  this venv's site-packages;
* the origin of every loaded module whose file lies in the checkout (the app
  modules under tools/calibration_app, the research/labels helpers, tests);
* versions of the app dependencies actually imported.

It reads ``sys.modules`` only; it imports nothing of the code under test.
"""

import json
import os
import sys
from pathlib import Path


def _version(name):
    mod = sys.modules.get(name)
    return getattr(mod, "__version__", None) if mod else None


def pytest_sessionfinish(session, exitstatus):
    out = os.environ.get("CIPROBE_OUT")
    if not out:
        return
    root = Path(str(session.config.rootpath)).resolve()
    prefix = Path(sys.prefix).resolve()

    def origin(mod):
        f = getattr(mod, "__file__", None)
        return str(Path(f).resolve()) if f else None

    cyclo, in_checkout = {}, {}
    for name, mod in sorted(sys.modules.items()):
        f = origin(mod)
        if name == "cyclophaser" or name.startswith("cyclophaser."):
            cyclo[name] = {"file": f,
                           "in_venv": bool(f) and Path(f).is_relative_to(prefix)}
        elif f and Path(f).is_relative_to(root):
            in_checkout[name] = str(Path(f).relative_to(root))

    data = {
        "executable": sys.executable,
        "prefix": str(prefix),
        "rootpath": str(root),
        "exitstatus": int(exitstatus),
        "sys_path": list(sys.path),
        "cyclophaser_modules": cyclo,
        "all_cyclophaser_in_venv": all(v["in_venv"] for v in cyclo.values()),
        "checkout_modules": in_checkout,
        "versions": {n: _version(n) for n in
                     ("streamlit", "pandas", "plotly", "numpy", "scipy",
                      "matplotlib", "xarray", "yaml", "pytest", "cyclophaser")},
    }
    Path(out).write_text(json.dumps(data, indent=2))
