"""I2 gate (b): 1-to-1 inventory of every Calibrate control and every export.

    # one process per checkout (two app checkouts clash on sibling imports):
    python research/app_redesign/i2/make_inventory.py collect <checkout root> <out.json>
    python research/app_redesign/i2/make_inventory.py compare <before.json> <after.json> <out.md>

`collect` runs the checkout's Calibrate page through AppTest (public API) in the
states needed to draw every conditional control — the smoothing windows, the
absolute prominence, the amplitude/plateau/geometric branches, the probe
smoothing, the Inspector view, the custom-format fields (in the dialog since I2),
the developer-only controls — and walks the element tree, recording for each
widget key: kind, label, where it is (sidebar heading › expander, main area, or
dialog) and the value it is first drawn with in the default state. It also lists
every download button, and reads `_DEFAULTS` and `_PARAM_WIDGET_KEYS` out of the
checkout's app.py source.

`compare` matches the two by key and writes the table: where each control was,
where it is, whether the key and the default are the same; keys that disappear
or appear; `_DEFAULTS` cross-checked (every key, same default); and the exports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# ── collect ───────────────────────────────────────────────────────────────────
def _decls(app: Path) -> dict:
    src = app.read_text()
    ns: dict = {}
    a = src.index("_DEFAULTS: dict = {")
    b = src.index("_DEFAULTS.update(_sidebar_defaults_from_signature())")
    b = src.index("\n", b) + 1
    exec(compile(src[a:b], str(app), "exec"), ns)
    pa = src.index("_PARAM_WIDGET_KEYS: dict[str, tuple[str, ...]] = {")
    pb = src.index("\n}\n", pa) + 3
    exec(compile(src[pa:pb], str(app), "exec"), ns)
    return {"defaults": {k: repr(v) for k, v in ns["_DEFAULTS"].items()},
            "param_widget_keys": {k: list(v) for k, v in ns["_PARAM_WIDGET_KEYS"].items()}}


WIDGET_TYPES = {"slider", "select_slider", "checkbox", "toggle", "radio", "selectbox",
                "multiselect", "number_input", "text_input", "file_uploader", "button",
                "download_button", "text_area", "color_picker", "date_input"}


def _walk(node, where: list[str], heading: str | None, out: dict, root: str) -> str | None:
    for ch in getattr(node, "children", {}).values():
        t = getattr(ch, "type", None)
        if t in ("header", "subheader"):
            heading = str(ch.value)
            continue
        if t == "expander":
            _walk(ch, where + [f"expander '{ch.label}'"], heading, out, root)
            continue
        if t == "dialog" or type(ch).__name__ == "Dialog":
            _walk(ch, ["dialog"], None, out, root)
            continue
        if t in WIDGET_TYPES and getattr(ch, "key", None):
            loc = " › ".join([root] + ([f"'{heading}'"] if heading else []) + where)
            if t == "download_button":
                out["downloads"].setdefault(ch.label, loc)
            out["widgets"].setdefault(ch.key, {
                "kind": t, "label": str(getattr(ch, "label", "")), "where": loc})
            continue
        if t in ("download_button", "button"):
            loc = " › ".join([root] + ([f"'{heading}'"] if heading else []) + where)
            out["downloads" if t == "download_button" else "buttons"].setdefault(
                str(ch.label), loc)
            continue
        heading = _walk(ch, where, heading, out, root) or heading
    return heading


def _set(at, key, value) -> bool:
    for kind in ("slider", "selectbox", "radio", "checkbox", "number_input",
                 "select_slider", "text_input"):
        for w in getattr(at, kind):
            if w.key == key and not w.disabled:
                w.set_value(value)
                return True
    return False


def collect(root: Path, out_path: Path) -> None:
    from streamlit.testing.v1 import AppTest
    app = root / "tools" / "calibration_app" / "app.py"
    new_layout = (root / "tools" / "calibration_app" / "app_pages").is_dir() and \
        "btn_save_results" in app.read_text()
    out = {"root": str(root), "new_layout": new_layout, "widgets": {}, "downloads": {},
           "buttons": {},
           "states": [], **_decls(app)}
    first_values: dict = {}

    def fresh(dev: bool):
        at = AppTest.from_file(str(app), default_timeout=300)
        if dev:
            at.secrets["developer_mode"] = True
        at.run()
        return at

    def record(at, state: str, values: bool = False):
        before = set(out["widgets"])
        _walk(at.main, [], None, out, "main")
        _walk(at.sidebar, [], None, out, "sidebar")
        # a dialog's contents sit outside both main and sidebar in AppTest's
        # tree; the typed collections still list them, so whatever they hold
        # that the walk did not reach is in the open dialog
        for kind in sorted(WIDGET_TYPES):
            for w in at.get(kind):
                key = getattr(w, "key", None)
                if kind == "download_button":
                    out["downloads"].setdefault(str(w.label), "dialog")
                if key and key not in out["widgets"]:
                    out["widgets"][key] = {"kind": kind, "label": str(getattr(w, "label", "")),
                                           "where": "dialog"}
        for k in set(out["widgets"]) - before:
            out["widgets"][k]["first_seen_in_state"] = state
        if values:
            for kind in ("slider", "selectbox", "radio", "checkbox", "number_input",
                         "select_slider", "text_input", "multiselect"):
                for w in at.get(kind):
                    if getattr(w, "key", None) and w.key not in first_values:
                        first_values[w.key] = repr(w.value)
        out["states"].append(state)

    def load_data(at):
        if new_layout:
            at.button(key="btn_example").click()
        at.run()                                   # the old layout loads it silently

    # 1. defaults, public, no data
    at = fresh(dev=False)
    record(at, "default (public, as opened)", values=True)
    # 2. developer key, data loaded, Grid
    at = fresh(dev=True)
    load_data(at)
    record(at, "developer key, example loaded, Grid", values=True)
    # 2b. one-column Grid: the per-cyclone downloads
    _set(at, "n_cols", 1)
    at.run()
    record(at, "one-column Grid")
    _set(at, "n_cols", 2)
    at.run()
    # 3. Inspector view
    _set(at, "view_mode", "Inspector")
    at.run()
    record(at, "Inspector view", values=True)
    # 4. conditional branches A
    at = fresh(dev=True)
    for k, v in (("sm_mode", "manual"), ("sm2_mode", "manual"),
                 ("extrema_prominence_mode", "absolute"), ("mature_method", "amplitude"),
                 ("incipient_method", "geometric")):
        _set(at, k, v)
        at.run()
    record(at, "manual windows, absolute prominence, amplitude, geometric")
    # 5. conditional branches B
    at = fresh(dev=True)
    for k, v in (("incipient_method", "plateau"), ("incipient_plateau_signal", "vorticity"),
                 ("incipient_plateau_crossing", "sustained")):
        _set(at, k, v)
        at.run()
    record(at, "plateau, vorticity signal, sustained crossing")
    # 6. custom-format fields
    at = fresh(dev=True)
    if new_layout:
        at.button(key="open_custom_format").click()
        at.run()
    record(at, "custom format shown", values=True)
    _set(at, "track_custom_on", True)
    at.run()
    if new_layout:
        at.button(key="open_custom_format").click()
        at.run()
    record(at, "custom format enabled")
    # 7. Save results dialog (I2)
    if new_layout:
        at = fresh(dev=True)
        load_data(at)
        at.button(key="btn_save_results").click()
        at.run()
        record(at, "Save results dialog", values=True)
        at.button(key="save_prepare").click()
        at.run()
        record(at, "Save results dialog, package prepared")
    for k, v in first_values.items():
        if k in out["widgets"]:
            out["widgets"][k]["first_value"] = v
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(out['widgets'])} widget keys, {len(out['downloads'])} downloads -> {out_path}")


# ── compare ───────────────────────────────────────────────────────────────────
def compare(before_p: Path, after_p: Path, out_p: Path) -> None:
    b, a = (json.loads(Path(x).read_text()) for x in (before_p, after_p))
    bw, aw = b["widgets"], a["widgets"]
    lines = ["# I2 — control and export inventory (generated by make_inventory.py)", "",
             f"Before: `{Path(b['root']).name}` · After: `{Path(a['root']).name}`.", "",
             "Location = `sidebar|main|dialog › 'heading' › expander`. Default = the value "
             "the widget is first drawn with in the default state (or, for one drawn "
             "only in another state, `_DEFAULTS` is the authority, checked below).", "",
             "## Every widget key", "",
             "| Key | Kind | Before | After | Same key | Default before → after |",
             "|---|---|---|---|---|---|"]
    for k in sorted(set(bw) | set(aw)):
        x, y = bw.get(k), aw.get(k)
        kind = (y or x)["kind"]
        vb = (x or {}).get("first_value", "—")
        va = (y or {}).get("first_value", "—")
        same_default = "same" if vb == va else f"{vb} → {va}"
        lines.append(f"| `{k}` | {kind} | {(x or {}).get('where', '**absent**')} | "
                     f"{(y or {}).get('where', '**absent**')} | "
                     f"{'yes' if x and y else 'NO'} | {same_default} |")
    gone = sorted(set(bw) - set(aw))
    new = sorted(set(aw) - set(bw))
    lines += ["", "## Keys gone / new", "",
              f"- gone ({len(gone)}): " + (", ".join(f"`{k}`" for k in gone) or "none"),
              f"- new ({len(new)}): " + (", ".join(f"`{k}`" for k in new) or "none")]
    db, da = b["defaults"], a["defaults"]
    diff = {k: (db.get(k), da.get(k)) for k in set(db) | set(da) if db.get(k) != da.get(k)}
    lines += ["", "## `_DEFAULTS` cross-check", "",
              f"- keys before: {len(db)}, after: {len(da)}; differing (key or value): "
              + (", ".join(f"`{k}` {v[0]} → {v[1]}" for k, v in sorted(diff.items())) or "**none**")]
    drawn = set(aw)
    not_drawn = sorted(k for k in da if k not in drawn)
    lines.append("- every `_DEFAULTS` key is drawn by a widget after: "
                 + ("**yes**" if not not_drawn else "NO — " + ", ".join(not_drawn)))
    pk = a["param_widget_keys"]
    missing = sorted(k for ks in pk.values() for k in ks if k not in drawn)
    lines.append(f"- every key named in `_PARAM_WIDGET_KEYS` ({sum(len(v) for v in pk.values())}) "
                 "is drawn after: " + ("**yes**" if not missing else "NO — " + ", ".join(missing)))
    lines += ["", "## Downloads (export functions)", "", "| Label | Before | After |", "|---|---|---|"]
    for lab in sorted(set(b["downloads"]) | set(a["downloads"])):
        lines.append(f"| {lab} | {b['downloads'].get(lab, '**absent**')} | "
                     f"{a['downloads'].get(lab, '**absent**')} |")
    lines += ["", "## Buttons without a key (by label)", "", "| Label | Before | After |",
              "|---|---|---|"]
    for lab in sorted(set(b["buttons"]) | set(a["buttons"])):
        lines.append(f"| {lab} | {b['buttons'].get(lab, '**absent**')} | "
                     f"{a['buttons'].get(lab, '**absent**')} |")
    lines += ["", "States walked, before: " + "; ".join(b["states"]),
              "", "States walked, after: " + "; ".join(a["states"]), ""]
    out_p.write_text("\n".join(lines))
    print(f"wrote {out_p}: {len(gone)} gone, {len(new)} new, defaults diff {len(diff)}")


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        collect(Path(sys.argv[2]).resolve(), Path(sys.argv[3]))
    else:
        compare(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
