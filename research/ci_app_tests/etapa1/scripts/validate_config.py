"""Check .circleci/config.yml before a push, without the circleci CLI.

    python validate_config.py <config.yml> <schema.json>

1. JSON-schema validation against CircleCI's own config schema (the one its
   YAML language server ships: github.com/CircleCI-Public/
   circleci-yaml-language-server, schema.json). Weaker than
   `circleci config validate` (no server-side compile), stated as such.
2. Structural facts the front depends on, read from the parsed YAML:
   which jobs each branch class gets, what the publishing jobs require, and
   that no publishing job can run on a ci/* branch.

Prints a JSON report; exits 1 if the schema rejects the file or a fact fails.
"""

import hashlib
import json
import re
import sys

import jsonschema
import yaml


def branch_runs(filters, branch):
    br = (filters or {}).get("branches")
    if not br:
        return True
    def match(pats):
        for p in pats if isinstance(pats, list) else [pats]:
            if p.startswith("/") and p.endswith("/"):
                if re.fullmatch(p[1:-1], branch):
                    return True
            elif p == branch:
                return True
        return False
    if "only" in br:
        return match(br["only"])
    if "ignore" in br:
        return not match(br["ignore"])
    return True


def expand(wf_jobs):
    """(name, job, filters, requires) for every workflow entry, matrix expanded."""
    out = []
    for entry in wf_jobs:
        if isinstance(entry, str):
            out.append((entry, entry, None, []))
            continue
        (job, conf), = entry.items()
        conf = conf or {}
        matrix = (conf.get("matrix") or {}).get("parameters")
        if matrix:
            (pname, values), = matrix.items()   # one parameter is all this config uses
            for v in values:
                name = conf.get("name", job).replace(f"<< matrix.{pname} >>", str(v))
                out.append((name, job, conf.get("filters"), conf.get("requires", [])))
        else:
            out.append((conf.get("name", job), job, conf.get("filters"),
                        conf.get("requires", [])))
    return out


def main(cfg_path, schema_path):
    text = open(cfg_path).read()
    cfg = yaml.safe_load(text)
    schema = json.load(open(schema_path))
    errors = [f"{list(e.absolute_path)}: {e.message}"
              for e in jsonschema.Draft7Validator(schema).iter_errors(cfg)]
    report = {"config_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "schema_sha256": hashlib.sha256(open(schema_path, "rb").read()).hexdigest(),
              "schema_errors": errors, "workflows": {}}
    facts = []
    for wname, wf in cfg["workflows"].items():
        if not isinstance(wf, dict) or "jobs" not in wf:
            continue
        entries = expand(wf["jobs"])
        names = {e[0] for e in entries}
        per_branch = {b: sorted(e[0] for e in entries if branch_runs(e[2], b))
                      for b in ("develop", "master", "ci/app-tests",
                                "ci/app-tests-controls", "feat/anything")}
        report["workflows"][wname] = {
            "jobs": sorted(names), "per_branch": per_branch,
            "requires": {e[0]: e[3] for e in entries if e[3]},
            "unknown_requires": sorted({r for e in entries for r in e[3]} - names),
        }
        pub = {"test_pypi_publish", "pypi_publish"}
        for b, jobs in per_branch.items():
            if b.startswith("ci/"):
                facts.append((f"{wname}: no publishing job on {b}", not (pub & set(jobs))))
        for e in entries:
            if e[1] in pub:
                facts.append((f"{wname}: {e[0]} requires build_test + both app legs",
                              set(e[3]) == {"build_test", "app_test_floor", "app_test_newest"}))
                # a required job must run on every branch the publisher runs on
                for b in ("develop", "master"):
                    if branch_runs(e[2], b):
                        facts.append((f"{wname}: every job {e[0]} requires runs on {b}",
                                      set(e[3]) <= set(per_branch[b])))
        facts.append((f"{wname}: no unknown requires",
                      not report["workflows"][wname]["unknown_requires"]))
    app = cfg["jobs"].get("app_test", {})
    facts.append(("app_test resource_class is medium", app.get("resource_class") == "medium"))
    for jname in ("build_test", "app_test"):
        stores = [s["store_test_results"] for s in cfg["jobs"].get(jname, {}).get("steps", [])
                  if isinstance(s, dict) and "store_test_results" in s]
        facts.append((f"{jname}: store_test_results when: always",
                      bool(stores) and all(s.get("when") == "always" for s in stores)))
    report["facts"] = [{"fact": f, "ok": ok} for f, ok in facts]
    print(json.dumps(report, indent=2))
    return 1 if errors or not all(ok for _, ok in facts) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
