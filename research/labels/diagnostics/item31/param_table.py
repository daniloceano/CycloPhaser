"""Item 31, stage 0, task 1 — parameter table: package defaults vs params-15.

Generated from the CODE (`inspect.signature` of `process_vorticity`, `get_periods`
and `determine_periods`) and from the raw YAML of params-15 (yaml.safe_load, so
YAML types survive: `5.0` stays a float). Nothing is typed in by hand.

Columns
-------
* default      — the signature default (repr + type). A parameter present in
                 more than one signature must carry the same default and type in
                 each; that is asserted and reported (`consistency`).
* params-15    — the value in `research/labels/configs/cyclophaser_params-15.yaml`
                 (repr + type), with the YAML section it sits in.
* group        — `filtragem` (a `process_vorticity` argument), `fase` (a
                 `get_periods` argument that changes detection) or `outro`
                 (output options plot/plot_steps/export_dict, and the
                 `determine_periods`-only x and hemisphere).
* igual?       — three answers, never merged into one:
                   `strict`    value equal AND same type (bool is not int);
                   `value`     `==` only;
                   `behaviour` equal in effect, justified by a cited code line.
                 Only two behaviour equivalences are admitted, each with its
                 line: `use_filter` True ≡ 'auto' and a float window/polyorder
                 cast by `int()`. Everything else falls back to `value`.

Outputs: param_table.md (table + counts), param_table.json.

Run: python research/labels/diagnostics/item31/param_table.py
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

dp = core.dp
FUNCS = {"process_vorticity": dp.process_vorticity, "get_periods": dp.get_periods,
         "determine_periods": dp.determine_periods}
DATA_ARGS = {"zeta_df", "vorticity", "series"}
OUTPUT_ARGS = {"plot", "plot_steps", "export_dict"}    # outputs, not detection


def _src_line(path: Path, needle: str) -> str:
    """'file:line' of the first line containing `needle` (asserted to exist)."""
    for i, ln in enumerate(path.read_text().splitlines(), 1):
        if needle in ln:
            return f"{path.relative_to(core.REPO)}:{i}"
    raise AssertionError(f"{needle!r} not found in {path}")


DP_PY = core.REPO / "cyclophaser" / "determine_periods.py"
FS_PY = core.REPO / "cyclophaser" / "find_stages.py"
BEHAVIOUR = {
    # (param, default, p15) -> justification with a line located in the code now
    "use_filter": lambda d, v: (d == "auto" and v is True,
                                "True → window len//2, same as 'auto'; only adds a "
                                "UserWarning (" + _src_line(DP_PY, "if isinstance(use_filter, bool):")
                                + ", " + _src_line(DP_PY, "elif use_filter == 'auto':") + ")"),
    "incipient_smooth_window": lambda d, v: (
        isinstance(v, float) and v.is_integer(),
        "cast by int() before use (" + _src_line(FS_PY, "w = int(window)") + ")"),
    "incipient_smooth_polyorder": lambda d, v: (
        isinstance(v, float) and v.is_integer(),
        "cast by int() before use (" + _src_line(FS_PY, "if w <= int(polyorder):") + ")"),
}


def _fmt(v) -> str:
    return f"`{v!r}` ({type(v).__name__})"


def main() -> None:
    env = core.assert_environment()
    doc = yaml.safe_load(core.config_path("params-15").read_text())
    p15 = {}
    for section in ("filter_params", "phase_params"):
        for k, v in (doc.get(section) or {}).items():
            assert k not in p15, f"{k} in two YAML sections"
            p15[k] = (section, v)

    sigs = {f: inspect.signature(fn).parameters for f, fn in FUNCS.items()}
    names = []
    for f in ("determine_periods", "process_vorticity", "get_periods"):
        for k in sigs[f]:
            if k not in DATA_ARGS and k not in names:
                names.append(k)
    extra_yaml = [k for k in p15 if k not in names]

    rows, consistency = [], []
    for k in names:
        where = [f for f in FUNCS if k in sigs[f]]
        defaults = {f: sigs[f][k].default for f in where}
        vals = list(defaults.values())
        same = all(v == vals[0] and type(v) is type(vals[0]) for v in vals)
        consistency.append((k, where, same))
        d = vals[0]
        group = ("filtragem" if k in sigs["process_vorticity"]
                 else "outro" if k in OUTPUT_ARGS
                 else "fase" if k in sigs["get_periods"] else "outro")
        row = {"param": k, "functions": where, "default": d, "group": group,
               "defaults_consistent": same}
        if k in p15:
            section, v = p15[k]
            strict = (v == d) and (type(v) is type(d))
            value = bool(v == d)
            beh, why = (strict or value), ""
            if not beh and k in BEHAVIOUR:
                beh, why = BEHAVIOUR[k](d, v)
            elif value and not strict and k in BEHAVIOUR:
                _, why = BEHAVIOUR[k](d, v)
            row.update({"p15": v, "section": section, "strict": strict,
                        "value": value, "behaviour": beh, "why": why})
        rows.append(row)

    in15 = [r for r in rows if "p15" in r]
    counts = {
        "params_15_keys": len(p15),
        "params_15_keys_matched_to_a_signature": len(in15),
        "yaml_keys_in_no_signature": extra_yaml,
        "differ_strict": sum(not r["strict"] for r in in15),
        "differ_value": sum(not r["value"] for r in in15),
        "differ_behaviour": sum(not r["behaviour"] for r in in15),
        "by_group_differ_behaviour": {
            g: f"{sum(not r['behaviour'] for r in in15 if r['group'] == g)}"
               f"/{sum(1 for r in in15 if r['group'] == g)}"
            for g in ("filtragem", "fase")},
        "type_only_differences": [r["param"] for r in in15
                                  if r["value"] and not r["strict"]],
        "behaviour_only_equivalences": [r["param"] for r in in15
                                        if not r["value"] and r["behaviour"]],
        "signature_params_absent_from_params_15": [r["param"] for r in rows
                                                   if "p15" not in r],
        "defaults_inconsistent_across_signatures": [k for k, _, s in consistency if not s],
    }

    out = ["# Item 31 — package defaults vs params-15 (generated)", "",
           f"Generated by `param_table.py` at HEAD of this branch; environment: "
           f"`{json.dumps(env)}`.", "",
           "| parameter | default atual | params-15 | grupo | igual? strict / value / behaviour | nota |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        if "p15" in r:
            eq = " / ".join("sim" if r[c] else "**não**" for c in ("strict", "value", "behaviour"))
            out.append(f"| `{r['param']}` | {_fmt(r['default'])} | {_fmt(r['p15'])} | "
                       f"{r['group']} | {eq} | {r['why']} |")
    out += ["", "Signature parameters params-15 does not set (they take the default "
            "under both, so they cannot differ):", ""]
    for r in rows:
        if "p15" not in r:
            out.append(f"* `{r['param']}` = {_fmt(r['default'])} — {r['group']} "
                       f"({', '.join(r['functions'])})")
    out += ["", "## Default consistency across signatures", "",
            "| parameter | in | same default and type everywhere |", "|---|---|---|"]
    for k, where, same in consistency:
        if len(where) > 1:
            out.append(f"| `{k}` | {', '.join(where)} | {'sim' if same else '**NÃO**'} |")
    out += ["", "## Counts", "", "```", json.dumps(counts, indent=2, default=str), "```", ""]
    (HERE / "param_table.md").write_text("\n".join(out))
    (HERE / "param_table.json").write_text(json.dumps(
        {"environment": env, "counts": counts, "rows": rows}, indent=2, default=repr))
    print("\n".join(out))


if __name__ == "__main__":
    main()
