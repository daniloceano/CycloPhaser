"""I3 gate (b) and (f): the inventory after the Benchmark page is gone.

    python research/benchmark_review/i3/check_inventory.py --base <checkout of c1617a0> --out <txt>

Four parts, AppTest, public API only, each in its own interpreter (two
checkouts in one process share `sys.modules`):

1. Every P item of the stage-0 inventory on the Compare page of THIS checkout:
   part 1 of research/benchmark_review/i1/check_inventory.py, run unchanged.
   1b. Three of its detectors read the card text in I1's formats ("this →
   reference" lines, `st.warning` boxes), which I2 replaced with the formats
   Danilo approved ("this (reference: …)", the HTML warning block of
   `config_text.warning_html`). They report MISSING for a function that is
   there. Part 1b repeats exactly those three, after the same interactions, in
   the current formats (deviation of instrument, recorded in RELATORIO.md; the
   I1 script is not edited).
2. Every D item on the Validate page of THIS checkout: part 1 of
   research/benchmark_review/i2/check_inventory.py, run unchanged (2 items
   REPLACED by the I2 brief, finding A1, as in I2).
3. The Compare page against c1617a0 (I2 closed): the view of the I2 script
   (`--compare-view`: widgets, texts, tables, stored results, images,
   expanders after the same interactions), compared RAW — no normalisation.
4. The Validate page against c1617a0: the same interactions on both checkouts
   (Defaults, params-track, the v2.0.0 release, the batch on, Run, reference
   params-track, Stacked, the disagreement filter), everything the page shows
   and every stored result, compared raw — and then again after undoing only
   F5 (" tracks differ" → " differ", " tracks with a boundary" → " with a
   boundary") and the running code's commit, which the provenance shows and
   which differs between two checkouts by construction (added after the first
   run showed it; recorded in RELATORIO.md). After that there must be no
   difference: the same numbers on the same sets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
I1 = ROOT / "research" / "benchmark_review" / "i1" / "check_inventory.py"
I2 = ROOT / "research" / "benchmark_review" / "i2" / "check_inventory.py"

LINES: list[str] = []


def log(s: str) -> None:
    LINES.append(s)
    print(s, flush=True)


# ── parts 1 and 2: the earlier scripts' own part 1, unchanged ─────────────────
_RUN_PART = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("inv", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
n = getattr(m, sys.argv[2])()
print("MISSING_COUNT", n)
"""


def run_part(script: Path, func: str) -> int:
    env = dict(os.environ)
    if func == "check_validate":
        env["CYCLOPHASER_APP_DEV"] = "1"
    out = subprocess.run([sys.executable, "-W", "ignore", "-c", _RUN_PART, str(script), func],
                         cwd=str(ROOT), capture_output=True, text=True, env=env)
    keep = [l for l in out.stdout.splitlines()
            if l.startswith("  [") or l.startswith("MISSING_COUNT")]
    for l in keep:
        if not l.startswith("MISSING_COUNT"):
            log(l)
    counts = [int(l.split()[1]) for l in keep if l.startswith("MISSING_COUNT")]
    if out.returncode or not counts:
        log(f"  ERROR (exit {out.returncode}): {out.stderr[-2000:]}")
        return 1
    return counts[0]


# ── part 1b ───────────────────────────────────────────────────────────────────
def check_card_items_current_format() -> int:
    """The interactions of i1/check_inventory.py part 1 up to its three card
    items, then those three in the formats approved in I2."""
    import yaml
    from streamlit.testing.v1 import AppTest
    failures = 0

    def item(name, cond, evidence):
        nonlocal failures
        failures += not cond
        print(f"  [{'OK' if cond else 'MISSING'}] {name} — {evidence}", flush=True)

    def ok(at):
        assert not at.exception, [str(e) for e in at.exception]
        return at

    def plain(v: str) -> str:
        return re.sub(r"<[^>]+>", "", v.replace("<wbr>", ""))

    at = AppTest.from_file(str(ROOT / "tools" / "calibration_app" / "app.py"),
                           default_timeout=1800)
    ok(at.run())
    at.button(key="btn_sample").click()
    ok(at.run())
    next(w for w in at.slider if w.key == "cutoff_high").set_value(48)
    ok(at.run())
    at.switch_page("app_pages/compare.py")
    ok(at.run())
    at.button(key="cmp_add_current").click()
    ok(at.run())
    at.button(key="cmp_add_defaults").click()
    ok(at.run())
    caps = [c.value for c in at.caption]
    md = [plain(m.value) for m in at.markdown]
    item("card: differences from the reference",
         "Differs from **Current settings** in 1 parameter(s):" in caps
         and any("filter_params.cutoff_high: 18 (reference: 48)" in m for m in md),
         "caption + one line per parameter ('section.key: this (reference: …)', I2) "
         "on the Defaults card")
    doc = at.session_state["cmp_columns"][1]["doc"]
    edited = {"filter_params": dict(doc["filter_params"]),
              "phase_params": {**{k: v for k, v in doc["phase_params"].items()
                                  if k != "prominence_relative"}, "distance": 3}}
    next(t for t in at.text_area if t.key == "cmp_edit_2").set_value(yaml.safe_dump(edited))
    ok(at.run())
    at.button(key="cmp_apply_2").click()
    ok(at.run())
    blocks = [plain(m.value) for m in at.markdown if "cp-config-warning" in m.value]
    item("card: ignored keys", any("Ignored keys: phase_params.distance" in b for b in blocks),
         "warning block 'Ignored keys: …' (config_text.warning_html, I2 R1)")
    item("card: filled keys",
         any(b.startswith("1 key(s) absent from this file were filled with the earlier "
                          "defaults") and "prominence_relative=None (package default 0.3)" in b
             for b in blocks),
         "warning block '… filled with the earlier defaults …' (same function as Calibrate)")
    return failures


# ── part 4: the Validate view ─────────────────────────────────────────────────
def validate_view(root: Path) -> dict:
    os.environ["CYCLOPHASER_APP_DEV"] = "1"
    from streamlit.testing.v1 import AppTest

    def ok(at):
        assert not at.exception, [str(e) for e in at.exception]
        return at

    def w(at, kind, key):
        return next(x for x in getattr(at, kind) if x.key == key)

    def click(at, key):
        at.button(key=key).click()
        return ok(at.run())

    def set_(at, kind, key, value):
        w(at, kind, key).set_value(value)
        return ok(at.run())

    at = AppTest.from_file(str(root / "tools" / "calibration_app" / "app.py"),
                           default_timeout=1800)
    ok(at.run())
    at.switch_page("app_pages/validate.py")
    ok(at.run())
    w(at, "checkbox", "val_include_batch").check()
    ok(at.run())
    click(at, "val_add_defaults")
    set_(at, "selectbox", "val_pick_config", "cyclophaser_params-track.yaml")
    click(at, "val_add_config")
    set_(at, "selectbox", "val_pick_snapshot", "v2.0.0")
    click(at, "val_add_snapshot")
    click(at, "val_run")
    set_(at, "selectbox", "val_reference", "params-track")
    set_(at, "radio", "val_figure_layout", "Stacked")
    w(at, "checkbox", "val_only_disagreeing").check()
    ok(at.run())

    widgets = []
    for kind in ("button", "checkbox", "radio", "selectbox", "multiselect",
                 "text_area", "toggle"):
        for e in getattr(at, kind):
            widgets.append([kind, e.key, str(e.label), repr(getattr(e, "value", None)),
                            list(map(str, getattr(e, "options", None) or ())),
                            str(getattr(e, "help", None))])
    texts = sorted(str(e.value) for kind in ("title", "subheader", "markdown", "caption",
                                             "info", "warning", "error", "code")
                   for e in getattr(at, kind))
    res = at.session_state["_val_results"]
    cells = {str(cid): {sid: [c.get("error"), c["runs"] and [list(r) for r in c["runs"]],
                              bool(c.get("missing"))]
                        for sid, c in col.items()}
             for cid, col in res["cells"].items()}
    return {"widgets": sorted(widgets), "texts": texts,
            "frames": [df.value.to_csv() for df in at.dataframe],
            "cells": [cells], "ids": [res["ids"]],
            "n_images": len(at.get("image")) + len(at.get("imgs")),
            "expanders": sorted(e.label for e in at.expander)}


_COMMIT = re.compile(r"\b[0-9a-f]{40}\b|(?<=code `)[0-9a-f]{12}(?=`)")


def _undo_f5(v):
    if isinstance(v, list):
        return [_undo_f5(x) for x in v]
    if not isinstance(v, str):
        return v
    v = _COMMIT.sub("<commit>", v)
    return v.replace(" tracks differ", " differ").replace(
        " tracks with a boundary outside its tolerance", " with a boundary outside its tolerance")


# ── views in their own process ────────────────────────────────────────────────
def _view(kind: str, root: Path, tmp: Path) -> dict:
    out = tmp / f"{kind}_{abs(hash(str(root)))}.json"
    if kind == "compare":
        cmd = [sys.executable, "-W", "ignore", str(I2), "--compare-view", str(root),
               "--json", str(out)]
    else:
        cmd = [sys.executable, "-W", "ignore", __file__, "--validate-view", str(root),
               "--json", str(out)]
    subprocess.run(cmd, check=True, cwd=str(root), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    return json.loads(out.read_text())


def _compare_dicts(a: dict, b: dict) -> int:
    differing = 0
    for k in sorted(set(a) | set(b)):
        va, vb = a.get(k), b.get(k)
        if va == vb:
            log(f"    {k}: identical")
            continue
        differing += 1
        if isinstance(va, list) and isinstance(vb, list):
            only_a = [x for x in va if x not in vb]
            only_b = [x for x in vb if x not in va]
            log(f"    {k}: DIFFERS — {len(only_a)} only in base, {len(only_b)} only here")
            for x in only_a[:8]:
                log(f"      base: {str(x)[:300]}")
            for x in only_b[:8]:
                log(f"      here: {str(x)[:300]}")
        else:
            log(f"    {k}: DIFFERS — base {str(va)[:200]} | here {str(vb)[:200]}")
    return differing


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--out")
    ap.add_argument("--validate-view")
    ap.add_argument("--json")
    args = ap.parse_args()
    if args.validate_view:
        Path(args.json).write_text(json.dumps(validate_view(Path(args.validate_view))))
        return
    import streamlit
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    log(f"streamlit {streamlit.__version__} | python "
        f"{sys.executable.replace(str(Path.home()), '~')} | HEAD {head} | base {args.base.replace(str(Path.home()), '~')}")
    log("1 · every P function on the Compare page (i1/check_inventory.py, part 1, unchanged)")
    f1 = run_part(I1, "check_compare")
    log("1b · the three card items of part 1 whose detector reads I1's format, in "
        "the current format")
    f1b = run_part(Path(__file__), "check_card_items_current_format")
    log("2 · every D function on the Validate page (i2/check_inventory.py, part 1, unchanged)")
    f2 = run_part(I2, "check_validate")
    base = Path(args.base)
    with tempfile.TemporaryDirectory() as tmp:
        log("3 · the Compare page, this checkout vs c1617a0 — raw")
        f3 = _compare_dicts(_view("compare", base, Path(tmp)), _view("compare", ROOT, Path(tmp)))
        log("4 · the Validate page, this checkout vs c1617a0 — raw")
        a, b = _view("validate", base, Path(tmp)), _view("validate", ROOT, Path(tmp))
        raw4 = _compare_dicts(a, b)
        log("  after undoing F5 only:")
        def undo(d):
            return {k: (sorted(_undo_f5(v), key=str) if isinstance(v, list) else v)
                    for k, v in d.items()}
        f4 = _compare_dicts(undo(a), undo(b))
    log(f"RESULT: {'PASS' if f1b == f2 == f3 == f4 == 0 and f1 <= 3 else 'FAIL'} "
        f"({f1} P item(s) reported missing by the I1 detectors, {f1b} of the three "
        f"missing in the current format, {f2} D item(s) missing, {f3} Compare part(s) "
        f"differing raw, {raw4} Validate part(s) differing raw, {f4} after undoing F5)")
    Path(args.out).write_text("\n".join(LINES).replace(str(Path.home()), "~") + "\n")


if __name__ == "__main__":
    main()
