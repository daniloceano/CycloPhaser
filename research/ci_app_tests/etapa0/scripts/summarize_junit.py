"""Summarise pytest junit XML files (plain or .gz) into JSON.

    python summarize_junit.py <out.json> <run.xml[.gz]> [...]

Per run: passed / failed / error / skipped, total time, the failing test ids,
skip reasons grouped by reason, and per-file counts and time. A "failed" here
is a <failure>; an <error> (setup/teardown/collection) is counted apart, and
both count against a PASS.
"""

import gzip
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


def _parse(path):
    raw = Path(path).read_bytes()
    if path.endswith(".gz"):
        raw = gzip.decompress(raw)
    return ET.fromstring(raw)


def _file_of(case):
    cls = case.get("classname", "")
    # classname is the dotted module (+ class); keep the module part under tests
    parts = cls.split(".")
    mod = []
    for p in parts:
        mod.append(p)
        if p.startswith("test_") or p == "browser_harness":
            break
    return "/".join(mod) + ".py"


def summarise(path):
    root = _parse(path)
    counts = Counter()
    failures, errors = [], []
    skip_reasons = Counter()
    per_file = defaultdict(lambda: Counter())
    per_file_time = defaultdict(float)
    total_time = 0.0
    for case in root.iter("testcase"):
        tid = f'{case.get("classname")}::{case.get("name")}'
        f = _file_of(case)
        t = float(case.get("time", 0) or 0)
        total_time += t
        per_file_time[f] += t
        if case.find("failure") is not None:
            status = "failed"; failures.append(tid)
        elif case.find("error") is not None:
            status = "error"; errors.append(tid)
        elif case.find("skipped") is not None:
            status = "skipped"
            sk = case.find("skipped")
            skip_reasons[(sk.get("message") or "").strip()[:200]] += 1
        else:
            status = "passed"
        counts[status] += 1
        per_file[f][status] += 1
    return {
        "file": Path(path).name,
        "passed": counts["passed"], "failed": counts["failed"],
        "error": counts["error"], "skipped": counts["skipped"],
        "sum_testcase_time_s": round(total_time, 1),
        "failures": failures, "errors": errors,
        "skip_reasons": dict(skip_reasons.most_common()),
        "per_file": {k: dict(v) | {"time_s": round(per_file_time[k], 2)}
                     for k, v in sorted(per_file.items())},
    }


if __name__ == "__main__":
    out, *paths = sys.argv[1:]
    res = [summarise(p) for p in paths]
    Path(out).write_text(json.dumps(res if len(res) > 1 else res[0], indent=2))
    for r in res:
        print(f'{r["file"]}: {r["passed"]} passed / {r["failed"]} failed'
              f' / {r["error"]} error / {r["skipped"]} skipped'
              f' ({r["sum_testcase_time_s"]} s in testcases)')
