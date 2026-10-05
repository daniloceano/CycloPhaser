#!/usr/bin/env python
"""Passo 6a, commit 21 — the calibration app's help text for the probe smoothing
window cited a test-split series; it now cites the first training series of
passo6/rel_t0_window.json, with that file's numbers (nothing typed).

    python research/cleanup/passo6/edit_21_help_text.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
r = json.loads((Path(__file__).with_name("rel_t0_window.json")).read_text())["ranked_rise_then_fall"][0]
v = r["rel_t0"]
p = ROOT / "tools/calibration_app/app.py"
s = p.read_text()
old = '"window (20170225: 0.44 → 0.66 at w=5 → 0.38 at w=7), so a "'
new = (f'"window (training track {r["id"]}: {v["0"]:.2f} without smoothing → {v["5"]:.2f} at w=5 → '
       f'{v["7"]:.2f} at w=7), so a "')
assert s.count(old) == 1
p.write_text(s.replace(old, new))
print("old:", old); print("new:", new)
