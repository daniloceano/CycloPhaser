"""0.3 — Inventory of the app tests, per file, from real runs plus a static scan.

    python inventory.py <repo> <conda_collect_all.txt> <conda_collect_browser.txt>
                        <lean_appsel.xml.gz> <newest.xml.gz> <out_dir>

A test is an "app test" when it PASSES in the app venv (newest) and does NOT
pass in the lean venv (the CI recipe), under the same selection
`-m "not browser and not source_tree"`. Browser tests come from the conda
`--collect-only -m browser`. Per file, the static scan adds: the modules
guarded by `importorskip`/skipif-on-import, and whether the file uses AppTest.
The AppTest / core split is per FILE (a file that uses AppTest anywhere counts
as AppTest), which is stated in the report.
"""

import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

GUARDED = ("streamlit", "yaml", "plotly", "playwright", "pandas")


def junit(path):
    root = ET.fromstring(gzip.decompress(Path(path).read_bytes()))
    res = {}
    for c in root.iter("testcase"):
        cls, name = c.get("classname", ""), c.get("name", "")
        st = ("failed" if c.find("failure") is not None else
              "error" if c.find("error") is not None else
              "skipped" if c.find("skipped") is not None else "passed")
        reason = None
        if st == "skipped":
            sk = c.find("skipped")
            reason = sk.get("message") or ""
            if reason == "collection skipped" and sk.text:
                # module-level skip: the reason sits in the element body,
                # "('<path>', <line>, 'Skipped: <reason>')"
                reason = "module: " + sk.text.split("Skipped: ", 1)[-1].rstrip("')\"")
        if not cls:                      # module-level skip: name is the module
            cls = name
        res[(cls, name)] = (st, float(c.get("time") or 0), reason)
    return res


def file_of(classname):
    out = []
    for p in classname.split("."):
        out.append(p)
        if p.startswith("test_"):
            break
    return "/".join(out) + ".py"


def collected(path):
    ids = [ln.strip() for ln in Path(path).read_text().splitlines()
           if ln.startswith("tests/") and "::" in ln]
    per = defaultdict(int)
    for i in ids:
        per[i.split("::")[0]] += 1
    return ids, dict(per)


def static_scan(repo, rel):
    src = (repo / rel).read_text()
    guards = sorted({m for m in GUARDED
                     if re.search(rf'importorskip\(\s*["\']{m}["\']', src)
                     or re.search(rf'_have\(\s*["\']{m}["\']\)', src)})
    return {"guards": guards, "uses_apptest": "AppTest" in src,
            "markers": sorted(set(re.findall(r"pytest\.mark\.(browser|source_tree)", src)))}


def main(repo, coll_all, coll_browser, lean_xml, newest_xml, out):
    repo, out = Path(repo), Path(out)
    all_ids, per_all = collected(coll_all)
    br_ids, per_br = collected(coll_browser)
    lean, new = junit(lean_xml), junit(newest_xml)

    per_file = defaultdict(lambda: {"app_tests": 0, "app_time_s": 0.0,
                                    "pkg_tests": 0, "lean_skip_reasons": defaultdict(int)})
    lean_by_file_skipped_module = defaultdict(list)
    for key, (st, t, _) in new.items():
        f = file_of(key[0])
        if st != "passed":
            continue
        lst = lean.get(key)
        if lst is None or lst[0] != "passed":
            per_file[f]["app_tests"] += 1
            per_file[f]["app_time_s"] += t
        else:
            per_file[f]["pkg_tests"] += 1
    # module-level skips in the lean run appear as ONE testcase per module
    for key, (st, t, reason) in lean.items():
        if st == "skipped":
            per_file[file_of(key[0])]["lean_skip_reasons"][(reason or "")[:120]] += 1

    rows = []
    files = sorted(set(per_file) | set(per_br) | set(per_all))
    for f in files:
        if not (repo / f).exists():
            continue
        d = per_file.get(f, {"app_tests": 0, "app_time_s": 0.0, "pkg_tests": 0,
                             "lean_skip_reasons": {}})
        if d["app_tests"] == 0 and per_br.get(f, 0) == 0:
            continue
        sc = static_scan(repo, f)
        kind = ("browser" if per_br.get(f) else
                "AppTest" if sc["uses_apptest"] else "core (streamlit/plotly, no AppTest)")
        rows.append({"file": f, "kind": kind, "collected_conda": per_all.get(f, 0),
                     "browser": per_br.get(f, 0), "app_tests": d["app_tests"],
                     "pkg_tests_same_file": d["pkg_tests"],
                     "app_time_s": round(d["app_time_s"], 1), **sc,
                     "lean_skip_reasons": dict(d["lean_skip_reasons"])})

    tot = {
        "collected_conda_all": len(all_ids),
        "browser_collected": len(br_ids),
        "app_tests_non_browser": sum(r["app_tests"] for r in rows),
        "app_time_s": round(sum(r["app_time_s"] for r in rows), 1),
        "by_kind": {},
        "newest_counts": {s: sum(1 for v in new.values() if v[0] == s)
                          for s in ("passed", "failed", "error", "skipped")},
        "lean_counts": {s: sum(1 for v in lean.values() if v[0] == s)
                        for s in ("passed", "failed", "error", "skipped")},
        "newest_skips": sorted({f"{file_of(k[0])}: {v[2]}" for k, v in new.items()
                                if v[0] == "skipped"}),
    }
    for r in rows:
        k = tot["by_kind"].setdefault(r["kind"], {"files": 0, "tests": 0, "time_s": 0.0})
        k["files"] += 1
        k["tests"] += r["app_tests"] if r["kind"] != "browser" else r["browser"]
        k["time_s"] = round(k["time_s"] + r["app_time_s"], 1)
    (out / "inventory.json").write_text(json.dumps({"totals": tot, "files": rows}, indent=2))

    lines = ["| arquivo | tipo | app (não-browser) | browser | tempo app (s) | importorskip | pulo no enxuto |",
             "|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["kind"], r["file"])):
        sk = "; ".join(f"{n}× {m}" for m, n in r["lean_skip_reasons"].items()) or "—"
        lines.append(f'| `{r["file"]}` | {r["kind"]} | {r["app_tests"]} | {r["browser"]} | '
                     f'{r["app_time_s"]} | {", ".join(r["guards"]) or "—"} | {sk} |')
    (out / "inventory_table.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(tot, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:])
