#!/usr/bin/env python
"""Passo 4, commit 17 — stale "2.0.0" wording outside cyclophaser/: the frozen
table research/labels/defaults_2.0.0.json holds the pre-item-31 defaults, not
the 2.0.0 release (research/labels/README.md). Exact replacements, each asserted
to match once; the log lists them. Test comments that use "2.0.0" as the name of
that table (the convention declared in tests/legacy_defaults.py) are left; the
ones stating a value "up to 2.0.0" for a parameter the release does not have
are corrected.

    python research/cleanup/passo4/fix_stale_200_texts.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EDITS = [
    ("tools/calibration_app/benchmark_tab.py", '"**4 · keys absent, filled with the frozen 2.0.0 default** "',
     '"**4 · keys absent, filled with the frozen pre-item-31 default** "'),
    ("tools/calibration_app/benchmark_tab.py", '"**4 · keys absent, filled with the frozen 2.0.0 default** — none"',
     '"**4 · keys absent, filled with the frozen pre-item-31 default** — none"'),
    ("tools/calibration_app/app.py", "# does not carry is FILLED with the frozen cyclophaser 2.0.0 default",
     "# does not carry is FILLED with the frozen pre-item-31 default"),
    ("tools/calibration_app/app.py", "# 2.0.0 default is None (OFF) as well,",
     "# pre-item-31 default is None (OFF) as well,"),
    ("tools/calibration_app/app.py", "    frozen cyclophaser 2.0.0 default and listed",
     "    frozen pre-item-31 default and listed"),
    ("tools/calibration_app/app.py", '"the cyclophaser 2.0.0 defaults (frozen table, item 31): "',
     '"the frozen pre-item-31 defaults (research/labels/defaults_2.0.0.json, item 31): "'),
    ("tools/calibration_app/app.py", "decay_tail_amplitude_fraction are None when their sidebar check is OFF; up to\n# 2.0.0 omitting them",
     "decay_tail_amplitude_fraction are None when their sidebar check is OFF; before\n# item 31 omitting them"),
    ("tools/calibration_app/layer_inspector.py", "The 2.0.0 values are the frozen",
     "The pre-item-31 values are the frozen"),
    ("tools/calibration_app/benchmark_core.py", "filled with the frozen 2.0.0 defaults (`config_defaults.fill_missing`",
     "filled with the frozen pre-item-31 defaults (`config_defaults.fill_missing`"),
    ("tools/calibration_app/benchmark_core.py", "be used: the FROZEN 2.0.0 default (`config_defaults`",
     "be used: the FROZEN pre-item-31 default (`config_defaults`"),
    ("research/labels/config_defaults.py", '"""Filling incomplete calibration configs with the FROZEN 2.0.0 defaults.',
     '"""Filling incomplete calibration configs with the FROZEN pre-item-31 defaults.'),
    ("research/labels/config_defaults.py", "**cyclophaser 2.0.0 default**, and the keys filled are always listed.",
     "**pre-item-31 default** (the file name says 2.0.0; it is not the 2.0.0\nrelease, see research/labels/README.md), and the keys filled are always listed."),
    ("research/labels/config_defaults.py", 'f"cyclophaser 2.0.0 defaults (frozen table {DEFAULTS_PATH.name}): {items}")',
     'f"pre-item-31 defaults (frozen table {DEFAULTS_PATH.name}): {items}")'),
    ("research/labels/evaluate_against_labels.py", "filled with the frozen cyclophaser 2.0.0",
     "filled with the frozen pre-item-31"),
    ("tests/test_decay_tail_amplitude_fraction.py", "moved (None up to 2.0.0).", "moved (None before item 31)."),
    ("tests/test_intensification_min_depth.py", "moved (0.0 up to 2.0.0).", "moved (0.0 before item 31)."),
    ("tests/test_item30_spare_intensification.py", "(item 31; False up to 2.0.0)", "(item 31; False before it)"),
]
log = []
for f, old, new in EDITS:
    p = ROOT / f
    s = p.read_text()
    assert s.count(old) == 1, (f, old)
    p.write_text(s.replace(old, new))
    log.append(dict(file=f, old=old, new=new))
(ROOT / "research/cleanup/passo4/fix_stale_200_texts_log.json").write_text(json.dumps(log, indent=1, ensure_ascii=False))
print(f"{len(log)} edits in {len({e['file'] for e in log})} files")
