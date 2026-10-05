#!/usr/bin/env python
"""Passo 4, 4c — the colours of the 2024 methodology figure, sampled from its
legend swatches (docs/_images/cyclophaser_methodology.jpg, read from git at
8dc2159 because the file leaves the tree with the new site), so the new figure
keeps them (Danilo, 2026-10-01) without typing them by eye.

    python research/cleanup/passo4/sample_old_figure_colors.py   # writes old_figure_colors.json next to it

Each swatch is the median RGB of a 7x3 pixel patch at the given legend position.
"""
import io
import json
import statistics
import subprocess
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REV, IMG = "8dc2159", "docs/_images/cyclophaser_methodology.jpg"
SWATCHES = {"incipient": (1270, 953), "intensification": (1270, 1000), "mature": (1270, 1043),
            "decay": (1270, 1085), "residual": (1270, 1131),
            "zeta_850": (1625, 953), "zeta_f": (1625, 998), "zeta_s": (1625, 1042), "zeta_s2": (1625, 1086)}
im = Image.open(io.BytesIO(subprocess.check_output(["git", "show", f"{REV}:{IMG}"], cwd=ROOT))).convert("RGB")
out = {}
for k, (x, y) in SWATCHES.items():
    px = [im.getpixel((x + dx, y + dy)) for dx in range(-3, 4) for dy in range(-1, 2)]
    out[k] = "#%02x%02x%02x" % tuple(int(statistics.median(p[i] for p in px)) for i in range(3))
(HERE / "old_figure_colors.json").write_text(json.dumps(dict(image=f"{REV}:{IMG}", size=im.size,
                                                            colors=out), indent=1))
print(out)
