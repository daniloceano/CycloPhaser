"""I1 gate (b): the inventory, checked by running the app.

    python research/benchmark_review/i1/check_inventory.py --base <checkout of 39e658c> --out <txt>

Two parts, AppTest, public API only:

1. Every function the inventory (research/benchmark_review/stage0/DECISIONS.md)
   marks **P** is found on the Compare page of THIS checkout, each with the
   element that carries it.
2. The Benchmark page is unchanged: the same interactions (Exploration, "All
   real" plus three ids, a sidebar column, a configs/ column, Run, the reference
   on the manual label, "Also score the labelled rows", Stacked) are driven on
   THIS checkout and on `--base`, and everything the page shows is compared:
   every widget (kind, key, label, value, options), every text element, every
   table, and the per-cell results the run stored.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

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


def _app(root: Path, data=True) -> AppTest:
    at = AppTest.from_file(str(root / "tools" / "calibration_app" / "app.py"),
                           default_timeout=1800)
    at.run()
    if data:
        at.button(key="btn_sample").click()
        at.run()
    return _ok(at)


# ── part 1 ────────────────────────────────────────────────────────────────────
def check_compare() -> int:
    failures = 0

    def item(name, cond, evidence):
        nonlocal failures
        failures += not cond
        log(f"  [{'OK' if cond else 'MISSING'}] {name} — {evidence}")

    at = _app(ROOT)
    _w(at, "slider", "cutoff_high").set_value(48)
    _ok(at.run())
    at.switch_page("app_pages/compare.py").run()
    _ok(at)
    keys = {b.key for b in at.button}
    item("count of selected tracks", any(m.value.startswith("**51 of 51**") for m in at.markdown),
         "markdown '51 of 51 track(s) selected'")
    labels = {b.key: b.label for b in at.button}
    for k, n in (("cmp_all", "All"), ("cmp_invert", "Invert selection"), ("cmp_clear", "Clear")):
        item(f"button {n}", labels.get(k) == n, f"{k} labelled '{labels.get(k)}'")
    item("choose individually", any(m.key == "cmp_tracks" for m in at.multiselect),
         "multiselect cmp_tracks inside 'Choose individually'")
    item("Run blocked, reason in visible text",
         _w(at, "button", "cmp_run").disabled and
         "To run, add at least one configuration." in [i.value for i in at.info],
         "st.info next to the disabled Run")
    item("add column from the sidebar", "cmp_add_current" in keys, "button 'Add Current settings'")
    item("upload a YAML", len(at.get("file_uploader")) == 1,
         "file_uploader cmp_yaml_upload (driven in Chromium, T2)")
    at.button(key="cmp_add_current").click()
    _ok(at.run())
    at.button(key="cmp_add_defaults").click()
    _ok(at.run())
    caps = [c.value for c in at.caption]
    item("reference selector (columns only)",
         list(_w(at, "selectbox", "cmp_reference").options) == ["Current settings", "Defaults"],
         "selectbox cmp_reference, options = the columns")
    item("card: name", any(m.value.startswith("**Current settings**") for m in at.markdown),
         "markdown with the column name")
    item("card: the reference names itself",
         "Reference — the other configurations are compared with this one." in caps,
         "caption on the reference card")
    item("card: differences from the reference",
         "Differs from **Current settings** in 1 parameter(s):" in caps
         and any("filter_params.cutoff_high</code>: 18 → 48" in m.value for m in at.markdown),
         "caption + one line per parameter ('`section.key`: this → reference') on the Defaults card")
    item("card: full configuration",
         any(e.label == "Full configuration (YAML)" for e in at.expander) and len(at.code) >= 2,
         "expander 'Full configuration (YAML)' with st.code")
    item("card: Edit / Apply", any(t.key == "cmp_edit_2" for t in at.text_area)
         and "cmp_apply_2" in {b.key for b in at.button}, "text_area cmp_edit_2 + Apply")
    item("card: Remove", "cmp_remove_2" in {b.key for b in at.button}, "button cmp_remove_2")
    # ignored and filled keys: an edit that drops one key and adds one unknown
    import yaml
    doc = at.session_state["cmp_columns"][1]["doc"]
    # round 2: only filled keys whose value differs from the package's default
    # are listed, so the dropped key is prominence_relative (filled None, package
    # default 0.3); a dropped boundary_padding is filled with the package's own
    # 'reflect' and is not listed any more
    edited = {"filter_params": dict(doc["filter_params"]),
              "phase_params": {**{k: v for k, v in doc["phase_params"].items()
                                  if k != "prominence_relative"}, "distance": 3}}
    _w(at, "text_area", "cmp_edit_2").set_value(yaml.safe_dump(edited))
    _ok(at.run())
    at.button(key="cmp_apply_2").click()
    _ok(at.run())
    warns = [w.value for w in at.warning]
    item("card: ignored keys", "Ignored keys: phase_params.distance" in warns,
         "warning 'Ignored keys: …' (config_text, the Calibrate import's sentence)")
    item("card: filled keys",
         any(w.startswith("1 key(s) absent from this file were filled with the earlier "
                          "defaults") and "prominence_relative=None (package default 0.3)" in w
             for w in warns),
         "warning '… filled with the earlier defaults …' (same function as Calibrate)")
    item("caption on the run count / cache",
         any(c.startswith("Results are kept per configuration and track content")
             for c in [c.value for c in at.caption]), "caption under Run")
    item("no results yet message (before any Run)",
         "No results yet — add configurations, then press **Run**." in [i.value for i in at.info],
         "st.info in '4 · Results'")
    at.button(key="cmp_run").click()
    _ok(at.run())
    frames = [df.value for df in at.dataframe]
    rel = next(f for f in frames if "Sequence changed" in list(f.index))
    for row in ("Tracks compared", "Sequence changed", "Boundary shift, median (steps)",
                "Boundary shift, max (steps)", "Phases appeared", "Phases disappeared"):
        item(f"relative table: {row}", row in list(rel.index), "row of 'Relative to Current settings'")
    per = next(f for f in frames if any("Incipient absent" in str(i) for i in f.index))
    item("incipient absent, per column, outside the relative table",
         list(per.columns) == ["Current settings", "Defaults"], "'Per configuration' table")
    item("boundary-shift caption", any("Boundary shift is measured only on tracks" in c.value
                                       for c in at.caption), "caption under the table")
    item("figure layout", any(r.key == "cmp_figure_layout" for r in at.radio), "radio cmp_figure_layout")
    item("legend", any("intensification" in m.value and "residual" in m.value
                       for m in at.markdown), "phase colour key + curve caption")
    names = list(at.session_state["_compare_live_tracks"])
    item("per-track header", any(m.value == f"**{names[0]}**" for m in at.markdown),
         "markdown with the track name")
    n_img = len(at.get("image")) + len(at.get("imgs"))
    item("side-by-side figures", n_img == 24, f"{n_img} images (12 tracks × 2 columns)")
    item("note: sequence differs from reference",
         any(c.value == "sequence differs from reference" for c in at.caption),
         "caption under a differing cell")
    _w(at, "radio", "cmp_figure_layout").set_value("Stacked")
    _ok(at.run())
    n_img = len(at.get("image")) + len(at.get("imgs"))
    item("stacked figures", n_img == 12, f"{n_img} images (one per track)")
    bad = {"filter_params": {**edited["filter_params"], "boundary_padding": "bogus"},
           "phase_params": edited["phase_params"]}
    _w(at, "text_area", "cmp_edit_2").set_value(yaml.safe_dump(bad))
    _ok(at.run())
    at.button(key="cmp_apply_2").click()
    _ok(at.run())
    at.button(key="cmp_run").click()
    _ok(at.run())
    errs = [e.value for e in at.error if e.value.startswith("Defaults: ")]
    item("error per cell", len(errs) == 12, f"{len(errs)} st.error 'Defaults: …' (one per track shown)")
    return failures


# ── part 2 ────────────────────────────────────────────────────────────────────
def benchmark_view(root: Path) -> dict:
    at = _app(root)
    at.switch_page("app_pages/benchmark.py").run()
    _ok(at)
    _w(at, "radio", "bench_mode").set_value("Exploration")
    _ok(at.run())
    at.button(key="bench_pick_real").click()
    _ok(at.run())
    real = list(at.session_state["bench_selected_ids"])
    _w(at, "multiselect", "bench_ids_widget").set_value(real[:3])
    _ok(at.run())
    at.button(key="bench_add_sidebar").click()
    _ok(at.run())
    _w(at, "selectbox", "bench_pick_config").set_value("cyclophaser_params-track.yaml")
    _ok(at.run())
    at.button(key="bench_add_config").click()
    _ok(at.run())
    at.button(key="bench_run").click()
    _ok(at.run())
    _w(at, "selectbox", "bench_reference").set_value("Manual label")
    _ok(at.run())
    _w(at, "checkbox", "bench_score_labelled_subset").set_value(True)
    _ok(at.run())
    _w(at, "radio", "bench_figure_layout").set_value("Stacked")
    _ok(at.run())

    def widgets():
        out = []
        for kind in ("button", "checkbox", "radio", "selectbox", "multiselect",
                     "text_area", "toggle"):
            for e in getattr(at, kind):
                out.append((kind, e.key, str(e.label), repr(getattr(e, "value", None)),
                            tuple(map(str, getattr(e, "options", None) or ()))))
        return sorted(out)

    texts = sorted(str(e.value) for kind in ("markdown", "caption", "info", "warning",
                                             "error", "code")
                   for e in getattr(at, kind)
                   # the running code's commit differs between the two checkouts
                   if "code `" not in str(e.value) and "running code commit" not in str(e.value))
    frames = [df.value.to_csv() for df in at.dataframe]
    runs = [{sid: (None if r["error"] else [list(x) for x in r["runs"]])
             for sid, r in col.items()} for col in at.session_state["_bench_runs"]]
    return {"widgets": widgets(), "texts": texts, "frames": frames, "runs": runs,
            "n_images": len(at.get("image")) + len(at.get("imgs")),
            "expanders": sorted(e.label for e in at.expander)}


def _view_in_own_process(root: Path, tmp: Path) -> dict:
    """benchmark_view(root) in a NEW interpreter: in one process the second
    checkout would reuse the first one's benchmark_tab / benchmark_core from
    sys.modules, and the comparison would compare a checkout with itself."""
    import json
    import subprocess
    out = tmp / f"view_{abs(hash(str(root)))}.json"
    subprocess.run([sys.executable, "-W", "ignore", __file__, "--view", str(root),
                    "--json", str(out)], check=True, cwd=str(root),
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.loads(out.read_text())


def check_benchmark(base: Path) -> int:
    import tempfile
    log(f"  base checkout: {base}")
    with tempfile.TemporaryDirectory() as tmp:
        a = _view_in_own_process(base, Path(tmp))
        b = _view_in_own_process(ROOT, Path(tmp))
    failures = 0
    for k in a:
        same = a[k] == b[k]
        failures += not same
        n = len(a[k]) if hasattr(a[k], "__len__") else a[k]
        log(f"  [{'SAME' if same else 'DIFFERS'}] {k} ({n})")
        if not same and isinstance(a[k], list):
            for x in [x for x in a[k] if x not in b[k]][:5]:
                log(f"      only in base: {x!r}"[:300])
            for x in [x for x in b[k] if x not in a[k]][:5]:
                log(f"      only here:    {x!r}"[:300])
    return failures


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--out")
    ap.add_argument("--view", help="internal: dump the Benchmark view of this checkout")
    ap.add_argument("--json")
    args = ap.parse_args()
    if args.view:
        import json
        Path(args.json).write_text(json.dumps(benchmark_view(Path(args.view))))
        return
    import streamlit
    log(f"streamlit {streamlit.__version__} | python {sys.executable.replace(str(Path.home()), '~')}")
    log("1 · every P function on the Compare page")
    f1 = check_compare()
    log("2 · the Benchmark page, this checkout vs the base")
    f2 = check_benchmark(Path(args.base))
    log(f"RESULT: {'PASS' if f1 == 0 and f2 == 0 else 'FAIL'} "
        f"({f1} P item(s) missing, {f2} Benchmark part(s) differing)")
    Path(args.out).write_text("\n".join(LINES).replace(str(Path.home()), "~") + "\n")


if __name__ == "__main__":
    main()
