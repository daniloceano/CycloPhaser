"""Item 31, stage 2a — write the FROZEN table of 2.0.0 defaults (decision (a), DESIGN §8.1).

Source: `param_table.json`'s "default" column, as committed in e42da8b — the
signature defaults of `process_vorticity` / `get_periods` read by
`inspect.signature` at stage 0, before any default moved. Nothing is typed by
hand: the rows with group `filtragem` become `filter_params`, the rows with group
`fase` become `phase_params`; `outro` (x, hemisphere, plot, plot_steps,
export_dict) is not a detection parameter and is left out.

Checks, asserted:
* the source file is byte-identical to its e42da8b version;
* while the package defaults have not moved (stage 2a), the table equals the
  live signature defaults value for value and type for type — so filling a key
  with it is, today, exactly what omitting the key did.

Output: research/labels/defaults_2.0.0.json (read by research/labels/config_defaults.py).
Run: python -P research/labels/diagnostics/item31/make_defaults_2_0_0.py [--no-live-check]
"""

from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = HERE / "param_table.json"
OUT = REPO / "research" / "labels" / "defaults_2.0.0.json"
SRC_COMMIT = "e42da8b"


def main() -> None:
    committed = subprocess.run(
        ["git", "show", f"{SRC_COMMIT}:{SRC.relative_to(REPO)}"], cwd=REPO,
        capture_output=True, check=True).stdout
    assert committed == SRC.read_bytes(), "param_table.json differs from its e42da8b version"
    rows = json.loads(committed)["rows"]
    table = {"filter_params": {}, "phase_params": {}}
    for r in rows:
        sec = {"filtragem": "filter_params", "fase": "phase_params"}.get(r["group"])
        if sec:
            table[sec][r["param"]] = r["default"]

    if "--no-live-check" not in sys.argv:
        sys.path.insert(0, str(REPO))
        import cyclophaser  # noqa: F401
        dp = sys.modules["cyclophaser.determine_periods"]
        assert Path(dp.__file__).resolve().is_relative_to(REPO), dp.__file__
        for sec, fn in (("filter_params", dp.process_vorticity),
                        ("phase_params", dp.get_periods)):
            sig = inspect.signature(fn).parameters
            for k, v in table[sec].items():
                d = sig[k].default
                assert d == v and type(d) is type(v), (sec, k, d, v)

    doc = {
        "what": "cyclophaser 2.0.0 signature defaults, FROZEN (item 31, decision (a)). "
                "A config key that is absent is filled with this value, never with "
                "whatever the signature says today.",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "source": f"{SRC.relative_to(REPO)} @ {SRC_COMMIT} (column 'default')",
        "source_sha256": hashlib.sha256(committed).hexdigest(),
        "filter_params": table["filter_params"],
        "phase_params": table["phase_params"],
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}: {len(table['filter_params'])} filter + "
          f"{len(table['phase_params'])} phase keys")


if __name__ == "__main__":
    main()
