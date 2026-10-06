"""I3 gate (b): 1-to-1 inventory of the Calibrate main area, before and after.

    # one process per checkout (two app checkouts clash on sibling imports):
    python research/app_redesign/i3/make_inventory.py collect <checkout root> <out.json>
    python research/app_redesign/i3/make_inventory.py compare <before.json> <after.json> <out.md>

Two parts.

1. Every widget key, as in I2: `collect` of research/app_redesign/i2/make_inventory.py,
   reused unchanged (sidebar, main area and dialogs; kind, label, location, first
   value; `_DEFAULTS` and `_PARAM_WIDGET_KEYS` from the source).

2. The main area, function by function. The Calibrate page runs through AppTest
   (public API) with the 51 sample tracks loaded and the developer key on (so the
   developer functions are inventoried too), in the states that draw every part of
   the main area: Grid with 2 columns, Grid with 1 column (per-track downloads,
   step-by-step analysis, detailed diagnostics), the incipient probe on, and the
   Inspector. Every element of the main area is recorded as a FUNCTION label
   (`subheader`, `expander '<label>'`, `download '<label>'`, `image`, `dataframe[<columns>]`,
   `metric '<label>'`, widget kind + key, …) and assigned:
   * to a TRACK when it is drawn under that track's name in the grid (the
     elements that follow a track's subheader inside a grid column);
   * to the PAGE otherwise.
   Where the layout has grid pages (I3), the collector walks every page with the
   public "Next ▶" button and merges the per-track records, so "per track" means
   "reachable for that track on some page". Before (no pages) one run holds all.

`compare` writes, per state: whether every track has the same per-track functions
before and after (and the differences when not), and the page-level functions
before and after with their counts, marking the ones that disappear.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "i2_make_inventory", HERE.parent / "i2" / "make_inventory.py")
i2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(i2)

SKIP = {"markdown", "caption", "divider", "title", "empty", "text", "code", "latex",
        "json", "toast", "balloons", "snow", "help"}
TRACK_RE_PREFIX = "⚠️ "


def _label(node, names: set) -> tuple[str | None, str | None]:
    """(function label, track name if the node is a track's subheader)."""
    t = getattr(node, "type", None) or type(node).__name__
    kind = type(node).__name__
    if t in SKIP:
        return None, None
    if t == "subheader":
        v = str(node.value).removeprefix(TRACK_RE_PREFIX)
        if v in names:
            return None, v
        return f"subheader '{node.value}'", None
    if t == "expander":
        return f"expander '{node.label}'", None
    if t == "dataframe":
        try:
            df = node.value
            cols = ([df.index.name] if df.index.name else []) + [str(c) for c in df.columns]
        except Exception:
            cols = ["?"]
        return f"dataframe[{', '.join(cols)}]", None
    if t in ("metric",):
        return f"metric '{node.label}'", None
    if t in ("image", "imgs"):
        return "image", None
    if t in ("plotly_chart", "pyplot") or kind == "UnknownElement":
        return t, None
    if t in ("warning", "error", "info", "success", "exception"):
        return t, None
    if t == "download_button":
        return f"download '{node.label}'", None
    if t in i2.WIDGET_TYPES:
        key = getattr(node, "key", None)
        lab = str(getattr(node, "label", ""))
        if key and key.startswith("badcase__"):
            key = "badcase__<track>"
        return f"{t} '{lab}'" + (f" key={key}" if key else ""), None
    return None, None


def _walk(node, names: set, page: Counter, tracks: dict, cur: list) -> None:
    """Depth-first over the main area. `cur[0]` is the track whose elements are
    being drawn: set by a track subheader, reset when the grid column closes."""
    for ch in getattr(node, "children", {}).values():
        t = getattr(ch, "type", None)
        lab, track = _label(ch, names)
        if track is not None:
            cur[0] = track
            tracks.setdefault(track, Counter())["subheader '<track>'"] += 1
            continue
        if lab is not None:
            (tracks.setdefault(cur[0], Counter()) if cur[0] else page)[lab] += 1
        if t == "column":
            saved = cur[0]
            _walk(ch, names, page, tracks, cur)
            # A grid column (a track subheader was drawn inside it) closes back
            # to page level; a column nested inside a track's area (the 1-column
            # CSV/PNG download pair) closes back to that track.
            cur[0] = None if cur[0] != saved else saved
            continue
        if getattr(ch, "children", None):
            _walk(ch, names, page, tracks, cur)


def _main_inventory(at, names: set) -> tuple[Counter, dict]:
    page: Counter = Counter()
    tracks: dict = {}
    _walk(at.main, names, page, tracks, [None])
    return page, tracks


def _next_button(at):
    for b in at.button:
        if b.key == "grid_next_top":
            return b
    return None


def _all_pages(at, names: set) -> tuple[list[Counter], dict, int]:
    """Walk every grid page (when the layout has them): page-level counters per
    page, per-track counters merged, and the number of pages walked."""
    pages, tracks = [], {}
    while True:
        p, t = _main_inventory(at, names)
        pages.append(p)
        for n, c in t.items():
            tracks.setdefault(n, Counter()).update(c)
        nxt = _next_button(at)
        if nxt is None or nxt.disabled:
            break
        nxt.click()
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
    return pages, tracks, len(pages)


def collect(root: Path, out_path: Path) -> None:
    from streamlit.testing.v1 import AppTest
    widgets_path = out_path.with_name(out_path.stem + "_widgets.json")
    i2.collect(root, widgets_path)
    app = root / "tools" / "calibration_app" / "app.py"
    sample = sorted(p.stem for p in (root / "tests" / "calibration_data").glob("*.csv"))
    names = set(sample)
    out = {"root": str(root), "n_sample": len(sample), "states": {}}

    def fresh(dev: bool):
        at = AppTest.from_file(str(app), default_timeout=900)
        if dev:
            at.secrets["developer_mode"] = True
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
        return at

    def store(state, at):
        pages, tracks, n_pages = _all_pages(at, names)
        out["states"][state] = {
            "n_pages": n_pages,
            "page_first": dict(pages[0]),
            "page_union": dict(sum(pages, Counter()) if len(pages) == 1 else
                               Counter({k: max(p.get(k, 0) for p in pages)
                                        for p in pages for k in p})),
            "tracks": {n: dict(c) for n, c in sorted(tracks.items())},
        }
        print(f"  {state}: {n_pages} page(s), {len(tracks)} tracks")

    # no data, public
    at = fresh(dev=False)
    p, t = _main_inventory(at, names)
    out["states"]["no data (public)"] = {"n_pages": 1, "page_first": dict(p),
                                         "page_union": dict(p), "tracks": {}}

    def sample_loaded(dev=True):
        at = fresh(dev=dev)
        at.button(key="btn_sample").click()
        at.run()
        assert not at.exception, [str(e) for e in at.exception]
        return at

    store("sample, developer key, Grid 2 columns", sample_loaded())
    store("sample, public, Grid 2 columns", sample_loaded(dev=False))
    at = sample_loaded()
    i2._set(at, "n_cols", 1)
    at.run()
    store("sample, developer key, Grid 1 column", at)
    at = sample_loaded()
    at.checkbox(key="show_incipient_probe").set_value(True)
    at.run()
    store("sample, developer key, Grid 2 columns, incipient probe on", at)
    at = sample_loaded()
    i2._set(at, "view_mode", "Inspector")
    at.run()
    store("sample, developer key, Inspector", at)

    out["widgets_file"] = widgets_path.name
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"-> {out_path}")


def compare(before_p: Path, after_p: Path, out_p: Path) -> None:
    b, a = (json.loads(Path(x).read_text()) for x in (before_p, after_p))
    # part 1: the I2 widget table, unchanged generator
    wmd = out_p.with_name(out_p.stem + "_widgets.md")
    i2.compare(before_p.with_name(b["widgets_file"]), after_p.with_name(a["widgets_file"]), wmd)
    L = ["# I3 — main-area inventory (generated by make_inventory.py)", "",
         f"Before: `{b['root']}` · After: `{a['root']}` · sample tracks: "
         f"{b['n_sample']} / {a['n_sample']}.", "",
         f"Widget keys (sidebar, main, dialogs): `{wmd.name}`.", ""]
    for state in b["states"]:
        sb, sa = b["states"][state], a["states"].get(state)
        L += [f"## {state}", ""]
        if sa is None:
            L += ["**state absent after**", ""]
            continue
        L.append(f"Pages walked: before {sb['n_pages']}, after {sa['n_pages']}.")
        tb, ta = sb["tracks"], sa["tracks"]
        if tb or ta:
            same = [n for n in tb if ta.get(n) == tb[n]]
            L.append(f"Tracks drawn: before {len(tb)}, after {len(ta)} (all pages). "
                     f"Tracks with the same per-track functions: **{len(same)}/{len(tb)}**.")
            diff = sorted(set(tb) ^ set(ta)) + [n for n in tb if n in ta and ta[n] != tb[n]]
            for n in diff[:10]:
                L.append(f"- `{n}`: before {tb.get(n)} · after {ta.get(n)}")
            fn = Counter()
            for c in tb.values():
                fn.update(c)
            fa = Counter()
            for c in ta.values():
                fa.update(c)
            L += ["", "| Per-track function | Before (sum over tracks) | After (sum over tracks, all pages) |",
                  "|---|---|---|"]
            for k in sorted(set(fn) | set(fa)):
                L.append(f"| {k} | {fn.get(k, 0)} | {fa.get(k, 0)} |")
        pb, pa = sb["page_union"], sa["page_union"]
        L += ["", "| Page-level function | Before | After (max over pages) | |", "|---|---|---|---|"]
        for k in sorted(set(pb) | set(pa)):
            mark = "**GONE**" if k in pb and k not in pa else ("new" if k not in pb else "")
            L.append(f"| {k} | {pb.get(k, 0)} | {pa.get(k, 0)} | {mark} |")
        L.append("")
    out_p.write_text("\n".join(L))
    print(f"wrote {out_p}")


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        collect(Path(sys.argv[2]).resolve(), Path(sys.argv[3]))
    else:
        compare(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
