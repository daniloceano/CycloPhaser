"""I2 gate (b): the inventory, checked by running the app.

    python research/benchmark_review/i2/check_inventory.py \
        --bench-base <checkout of 39e658c> --compare-base <checkout of f3008fc> --out <txt>

Three parts, AppTest, public API only, developer key on:

1. Every function the inventory (research/benchmark_review/stage0/DECISIONS.md)
   marks **D** is found on the Validate page of THIS checkout, with the element
   that carries it. Two D items exist only because the manual label could be a
   reference; the I2 brief removes that (finding A1). They are listed as
   "REPLACED", with the decision, and not counted as present.
2. The Benchmark page is unchanged against 39e658c: the I1 script's own view
   (research/benchmark_review/i1/check_inventory.py --view), each checkout in
   its own interpreter.
3. The Compare page is unchanged against f3008fc except for the I1 pending items
   1-2, R1 and the "Results are current" line (I2 round 2): the same
   interactions on both checkouts, every widget, text, table and stored result
   compared raw, and then again after undoing exactly those (the "(reference: …)"
   wording, the "<wbr>" break points and the line-breaking style, the warning
   block of `config_text.warning_html` around the unchanged sentence, and the
   "Results are current: …" caption). Raw differences are listed; after the
   normalisation there must be none.
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
I1_SCRIPT = ROOT / "research" / "benchmark_review" / "i1" / "check_inventory.py"
os.environ["CYCLOPHASER_APP_DEV"] = "1"

from streamlit.testing.v1 import AppTest  # noqa: E402

LINES: list[str] = []


def log(s: str) -> None:
    LINES.append(s)
    print(s, flush=True)


def _ok(at):
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _w(at, kind, key):
    return next(w for w in getattr(at, kind) if w.key == key)


def _app(root: Path) -> AppTest:
    at = AppTest.from_file(str(root / "tools" / "calibration_app" / "app.py"),
                           default_timeout=1800)
    return _ok(at.run())


def _click(at, key):
    at.button(key=key).click()
    return _ok(at.run())


def _set(at, kind, key, value):
    _w(at, kind, key).set_value(value)
    return _ok(at.run())


# ── part 1 ────────────────────────────────────────────────────────────────────
def check_validate() -> int:
    import yaml
    failures = 0

    def item(name, cond, evidence):
        nonlocal failures
        failures += not cond
        log(f"  [{'OK' if cond else 'MISSING'}] {name} — {evidence}")

    def replaced(name, why):
        log(f"  [REPLACED] {name} — {why}")

    at = _app(ROOT)
    at.switch_page("app_pages/validate.py").run()
    _ok(at)
    md = [m.value for m in at.markdown]
    item("status line: labels available (the old 'ground truth' badge)",
         any("manual labels: 47 of 47" in m and "reference:" in m for m in md),
         "markdown status line '… manual labels: 47 of 47 · reference: …'")
    item("Include swell_item30 batch", any(c.key == "val_include_batch" for c in at.checkbox),
         "checkbox val_include_batch")
    item("All synthetic", _w(at, "button", "val_all_synthetic").label == "All synthetic",
         "button val_all_synthetic")
    item("Train (preset)",
         sorted(_w(at, "multiselect", "val_tracks").value) == sorted(
             str(s) for s in __import__("labels_core").read_split()["train"]),
         "every offered track is in the train split and all 47 start selected; "
         "'All real' + 'All synthetic' split it by source (no separate Train button: "
         "the brief fixes the selection controls)")
    item("From a saved configuration (research/labels/configs/)",
         _w(at, "selectbox", "val_pick_config").label.endswith("(research/labels/configs/)"),
         "selectbox val_pick_config + button 'Add file'")
    item("From a frozen published version (snapshots)",
         _w(at, "selectbox", "val_pick_snapshot").label.endswith("(research/snapshots/)"),
         "selectbox val_pick_snapshot + button 'Add release'")
    _w(at, "checkbox", "val_include_batch").check()
    _ok(at.run())
    caps = [c.value for c in at.caption]
    item("batch caption", any(c.startswith("swell_item30: 7 train tracks loaded") for c in caps),
         "caption 'swell_item30: 7 train tracks loaded, 5 of them …'")
    item("batch error message", "The swell_item30 batch could not be loaded"
         in (ROOT / "tools/calibration_app/validate_tab.py").read_text(),
         "st.error when the batch cannot be loaded (source; needs a broken file)")
    _w(at, "checkbox", "val_include_batch").uncheck()
    _ok(at.run())
    _click(at, "val_add_defaults")
    # a calibration file: params-track with an `evaluation` block and an absent
    # boundary_padding, in a temporary configs dir (removed below)
    import benchmark_core as bc
    doc = yaml.safe_load((bc.CONFIGS_DIR / "cyclophaser_params-track.yaml").read_text())
    del doc["filter_params"]["boundary_padding"]
    doc["evaluation"] = {"bad_cases": ["x"], "bad_cases_count": 1, "total_cyclones": 51}
    tmp = Path(tempfile.mkdtemp())
    (tmp / "cyclophaser_params-older.yaml").write_text(yaml.safe_dump(doc))
    real_dir = bc.CONFIGS_DIR
    bc.CONFIGS_DIR = tmp
    try:
        _ok(at.run())                    # redraw the file list from the temporary dir
        _set(at, "selectbox", "val_pick_config", "cyclophaser_params-older.yaml")
        _click(at, "val_add_config")
    finally:
        bc.CONFIGS_DIR = real_dir
        (tmp / "cyclophaser_params-older.yaml").unlink()
        tmp.rmdir()
    _set(at, "selectbox", "val_pick_snapshot", "v2.0.0")
    _click(at, "val_add_snapshot")
    caps = [c.value for c in at.caption]
    warns = [w.value for w in at.warning]
    item("card: short sha256 · commit", any(re.match(r"^`[0-9a-f]{12}` · code `[0-9a-f]{12}`$", c)
                                            for c in caps), "caption '`<sha>` · code `<commit>`'")
    item("card: pre-filter-fix warning", bc.PRE_FILTER_FIX_SHORT in warns, "st.warning on the card")
    item("card: snapshot caption", "A published release: no parameters of its own to compare." in caps,
         "caption on the snapshot card")
    item("Provenance 1 · sha256", any(c.startswith("**1 · sha256 of the file** — `") for c in caps),
         "caption in 'Provenance'")
    item("Provenance 2 · commit", any(c.startswith("**2 · running code commit** — `") for c in caps),
         "caption in 'Provenance'")
    item("Provenance 5 · pre-filter-fix", any(c.startswith("**5 · pre-filter-fix warning** — This YAML")
                                              for c in caps), "caption in 'Provenance'")
    item("historical annotation, 'not a score'", "**Historical annotation — not a score**" in caps,
         "caption in 'Provenance'")
    item("frozen snapshot data", any(c.startswith("**3 · published release** — Frozen reference")
                                     for c in caps) and any(c.startswith("parameters: ") for c in caps),
         "captions in the snapshot card's 'Provenance'")
    replaced("reference selector option 'Manual label'",
             "removed by the I2 brief (A1): the reference is a column, "
             f"options = {list(_w(at, 'selectbox', 'val_reference').options)}")
    replaced("caption 'manual label has no parameters… baseline'",
             "existed only for the label as reference (A1)")
    _click(at, "val_run")
    md = [m.value for m in at.markdown]
    item("agreement panel, train block", "##### Train — n = 47" in md,
         "'#### Agreement with manual labels' → '##### Train — n = 47', two instrument tables")
    item("'Also score the labelled rows' + scoring expander (Exploration)",
         "#### Agreement with manual labels" in md,
         "no modes: the agreement section is always shown, over labelled tracks only "
         "(every offered track is labelled)")
    item("per-track header: source · split · batch",
         any(re.match(r"^\*\*\d+\*\* · real · train$", m) for m in md), "markdown '**id** · real · train'")
    item("Show manual labels (label panel)",
         any(t.key == "val_show_label" and t.value is True for t in at.toggle),
         "toggle 'Show the label panel', on by default")
    item("label panel", len(at.get("image")) + len(at.get("imgs")) == 12 * 4,
         "12 tracks × (label + 3 columns) images")
    item("notes per cell (sequence vs label, mature)",
         any(c.value in ("sequence agrees with label", "sequence differs from label")
             for c in at.caption)
         and any(c.value.endswith("vs label (margin 6)") for c in at.caption),
         "captions under each cell")
    _w(at, "checkbox", "val_include_batch").check()
    _ok(at.run())
    _click(at, "val_run")
    md = [m.value for m in at.markdown]
    item("adjudicated block", "##### Adjudicated — n = 5" in md and "##### Train — n = 49" in md,
         "'##### Adjudicated — n = 5', apart from '##### Train — n = 49'")
    _w(at, "checkbox", "val_include_batch").uncheck()
    _ok(at.run())
    _w(at, "checkbox", "val_only_disagreeing").check()
    _ok(at.run())
    _click(at, "val_all_real")
    while True:          # page forward until a batch track of the last run shows
        if any("no longer loaded (swell_item30 batch excluded)" in c.value for c in at.caption):
            break
        nxt = [b for b in at.button if b.key == "val_next"]
        if not nxt or nxt[0].disabled:
            break
        _click(at, "val_next")
    item("'no longer loaded (swell_item30 batch excluded)'",
         any("no longer loaded (swell_item30 batch excluded)" in c.value for c in at.caption),
         "caption for a batch track of the last run after the batch is switched off")
    return failures


# ── part 2 ────────────────────────────────────────────────────────────────────
def _i1_view(root: Path, tmp: Path) -> dict:
    out = tmp / f"bench_{abs(hash(str(root)))}.json"
    subprocess.run([sys.executable, "-W", "ignore", str(I1_SCRIPT), "--view", str(root),
                    "--json", str(out)], check=True, cwd=str(root),
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.loads(out.read_text())


def _compare_dicts(a: dict, b: dict, norm=None) -> int:
    failures = 0
    for k in a:
        x, y = a[k], b[k]
        if norm is not None:
            x, y = norm(x), norm(y)
        same = x == y
        failures += not same
        n = len(x) if hasattr(x, "__len__") else x
        log(f"  [{'SAME' if same else 'DIFFERS'}] {k} ({n})")
        if not same and isinstance(x, list):
            for v in [v for v in x if v not in y][:6]:
                log(f"      only in base: {v!r}"[:400])
            for v in [v for v in y if v not in x][:6]:
                log(f"      only here:    {v!r}"[:400])
    return failures


def check_benchmark(base: Path) -> int:
    log(f"  base checkout: {base}")
    with tempfile.TemporaryDirectory() as tmp:
        a = _i1_view(base, Path(tmp))
        b = _i1_view(ROOT, Path(tmp))
    return _compare_dicts(a, b)


# ── part 3 ────────────────────────────────────────────────────────────────────
def compare_view(root: Path) -> dict:
    import yaml
    at = _app(root)
    at.button(key="btn_sample").click()
    _ok(at.run())
    _set(at, "slider", "cutoff_high", 48)
    at.switch_page("app_pages/compare.py").run()
    _ok(at)
    _click(at, "cmp_add_current")
    _click(at, "cmp_add_defaults")
    doc = at.session_state["cmp_columns"][1]["doc"]
    edited = {"filter_params": dict(doc["filter_params"]),
              "phase_params": {**{k: v for k, v in doc["phase_params"].items()
                                  if k != "prominence_relative"}, "distance": 3}}
    _set(at, "text_area", "cmp_edit_2", yaml.safe_dump(edited))
    _click(at, "cmp_apply_2")
    _click(at, "cmp_run")
    _set(at, "selectbox", "cmp_reference", "Defaults")
    _set(at, "radio", "cmp_figure_layout", "Stacked")
    _w(at, "checkbox", "cmp_only_differing").check()
    _ok(at.run())

    def widgets():
        out = []
        for kind in ("button", "checkbox", "radio", "selectbox", "multiselect",
                     "text_area", "toggle"):
            for e in getattr(at, kind):
                out.append([kind, e.key, str(e.label), repr(getattr(e, "value", None)),
                            list(map(str, getattr(e, "options", None) or ())),
                            str(getattr(e, "help", None))])
        return sorted(out)

    texts = sorted(str(e.value) for kind in ("title", "subheader", "markdown", "caption",
                                             "info", "warning", "error", "code")
                   for e in getattr(at, kind))
    frames = [df.value.to_csv() for df in at.dataframe]
    cells = {str(cid): {sid: c["runs"] and [list(r) for r in c["runs"]]
                        for sid, c in col.items()}
             for cid, col in at.session_state["_cmp_results"]["cells"].items()}
    return {"widgets": widgets(), "texts": texts, "frames": frames, "cells": [cells],
            "n_images": len(at.get("image")) + len(at.get("imgs")),
            "expanders": sorted(e.label for e in at.expander)}


def _compare_in_own_process(root: Path, tmp: Path) -> dict:
    out = tmp / f"cmp_{abs(hash(str(root)))}.json"
    subprocess.run([sys.executable, "-W", "ignore", __file__, "--compare-view", str(root),
                    "--json", str(out)], check=True, cwd=str(root),
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.loads(out.read_text())


_OLD_LINE = re.compile(r"</code>: (.*?) → (.*?)</div>")
_NEW_LINE = re.compile(r"</code>: (.*?) \(reference: (.*?)\)</div>")


def _undo_pending(v):
    """Undo exactly I1's pending items 1-2 on any text."""
    if isinstance(v, list):
        return [_undo_pending(x) for x in v]
    if not isinstance(v, str):
        return v
    v = v.replace("\u200b", "").replace("<wbr>", "")
    v = re.sub(r"^<div class='cp-config-warning' style='[^']*'>(.*)</div>$", r"\1", v,
               flags=re.S)
    v = re.sub(r"style='[^']*'", "style=''", v)
    v = _OLD_LINE.sub(r"</code>: \1 | \2</div>", v)
    v = _NEW_LINE.sub(r"</code>: \1 | \2</div>", v)
    return v


def check_compare(base: Path) -> int:
    log(f"  base checkout: {base}")
    with tempfile.TemporaryDirectory() as tmp:
        a = _compare_in_own_process(base, Path(tmp))
        b = _compare_in_own_process(ROOT, Path(tmp))
    log("  raw (every difference listed):")
    _compare_dicts(a, b)
    log("  after undoing pending items 1-2, R1 and the 'Results are current' line only:")
    b = {**b, "texts": [t for t in b["texts"] if not t.startswith("Results are current: ")]}
    return _compare_dicts({k: sorted(_undo_pending(v)) if isinstance(v, list) else v
                           for k, v in a.items()},
                          {k: sorted(_undo_pending(v)) if isinstance(v, list) else v
                           for k, v in b.items()})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench-base")
    ap.add_argument("--compare-base")
    ap.add_argument("--out")
    ap.add_argument("--compare-view", help="internal: dump the Compare view of this checkout")
    ap.add_argument("--json")
    args = ap.parse_args()
    if args.compare_view:
        Path(args.json).write_text(json.dumps(compare_view(Path(args.compare_view))))
        return
    import streamlit
    log(f"streamlit {streamlit.__version__} | python {sys.executable.replace(str(Path.home()), '~')}"
        f" | HEAD {subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()}")
    log("1 · every D function on the Validate page")
    f1 = check_validate()
    log("2 · the Benchmark page, this checkout vs 39e658c")
    f2 = check_benchmark(Path(args.bench_base))
    log("3 · the Compare page, this checkout vs f3008fc (pending items 1-2, R1, 'Results are current' undone)")
    f3 = check_compare(Path(args.compare_base))
    log(f"RESULT: {'PASS' if f1 == f2 == f3 == 0 else 'FAIL'} "
        f"({f1} D item(s) missing, {f2} Benchmark part(s) differing, "
        f"{f3} Compare part(s) differing beyond pending items 1-2, R1, F2)")
    Path(args.out).write_text("\n".join(LINES).replace(str(Path.home()), "~") + "\n")


if __name__ == "__main__":
    main()
