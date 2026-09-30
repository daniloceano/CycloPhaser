#!/usr/bin/env python
"""Passo 4, commit 16b — the ONLY docstring edit in cyclophaser/ outside C1.

    <cyclophaser env python> -P research/cleanup/passo4/edit_16b_docstring.py

Replaces, in the `decay_tail_amplitude_fraction` note of `get_periods`
(cyclophaser/determine_periods.py), the false "(opt-in; default None reproduces
prior behaviour exactly)" by a sentence whose default is READ from the
signature of get_periods (asserted equal in determine_periods). What None does
is stated from the code: find_stages.find_residual_period runs the tail check
only when the value is not None (`if decay_tail_amplitude_fraction is not None:`),
so None leaves the tail to the catch-all residual rule, as before the option
existed. Aborts unless the old text occurs exactly once and the None guard is
found in find_stages.py.
"""
import importlib
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
dp = importlib.import_module("cyclophaser.determine_periods")
d_gp = inspect.signature(dp.get_periods).parameters["decay_tail_amplitude_fraction"].default
d_dp = inspect.signature(dp.determine_periods).parameters["decay_tail_amplitude_fraction"].default
assert d_gp == d_dp, (d_gp, d_dp)
fs = (ROOT / "cyclophaser/find_stages.py").read_text()
assert "if decay_tail_amplitude_fraction is not None:" in fs

f = ROOT / "cyclophaser/determine_periods.py"
s = f.read_text()
old = ("    cyclone has actually dissipated. With ``decay_tail_amplitude_fraction`` set\n"
       "    (opt-in; default None reproduces prior behaviour exactly),\n")
new = ("    cyclone has actually dissipated. With ``decay_tail_amplitude_fraction`` set\n"
       f"    (default {d_gp}; ``None`` switches the check off and leaves the tail to the\n"
       "    catch-all, the behaviour before this option existed),\n")
assert s.count(old) == 1, s.count(old)
f.write_text(s.replace(old, new))
print("old:", old.splitlines()[1].strip())
print("new:", " ".join(l.strip() for l in new.splitlines()[1:]))
print(f"default read from the signature: {d_gp!r} (get_periods == determine_periods)")
