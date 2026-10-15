"""Correção antes do merge: which jobs run on which branch, with release/*.

    python check_filters.py <config.yml> <schema.json>

Schema validation as in validate_config.py, then the jobs each test branch gets,
read from the parsed YAML with validate_config.expand/branch_runs, and four
facts:

F1  app_test_floor and app_test_newest run on release/v9.9.9
F2  they run on ci/x
F3  they do NOT run on feat/x
F4  test_pypi_publish runs only on develop and pypi_publish only on master,
    among the branches below

Prints a JSON report; exits 1 on a schema error or a false fact.
"""

import json
import sys
from pathlib import Path

import jsonschema
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from validate_config import branch_runs, expand  # noqa: E402

BRANCHES = ("develop", "master", "release/v9.9.9", "ci/x", "feat/x")
LEGS = {"app_test_floor", "app_test_newest"}


def main(cfg_path, schema_path):
    cfg = yaml.safe_load(open(cfg_path))
    errors = [f"{list(e.absolute_path)}: {e.message[:300]}" for e in
              jsonschema.Draft7Validator(json.load(open(schema_path))).iter_errors(cfg)]
    entries = expand(cfg["workflows"]["build_test_publish"]["jobs"])
    per = {b: sorted(e[0] for e in entries if branch_runs(e[2], b)) for b in BRANCHES}
    on = {b: set(v) for b, v in per.items()}
    facts = {
        "F1 app legs run on release/v9.9.9": LEGS <= on["release/v9.9.9"],
        "F2 app legs run on ci/x": LEGS <= on["ci/x"],
        "F3 app legs do NOT run on feat/x": not (LEGS & on["feat/x"]),
        "F4 publishing only on develop (TestPyPI) / master (PyPI)":
            [b for b in BRANCHES if "test_pypi_publish" in on[b]] == ["develop"]
            and [b for b in BRANCHES if "pypi_publish" in on[b]] == ["master"],
    }
    print(json.dumps({"config": cfg_path, "schema_errors": errors,
                      "per_branch": per, "facts": facts}, indent=2))
    return 1 if errors or not all(facts.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
