#!/usr/bin/env python
"""Passo 1 — P2 and the params-track claim, by script.

    <cyclophaser env python> -P research/cleanup/passo1/params_track_vs_defaults.py [PRE_REF]

1. P2: sha256 of `research/labels/configs/cyclophaser_params-15.yaml` at PRE_REF
   (default d8a19cc, the last commit before the rename; read with `git show`)
   against the sha256 of `cyclophaser_params-track.yaml` in the working tree.
2. The sentence "params-track = the package defaults except
   boundary_padding: edge": every key of the YAML's filter_params against
   `process_vorticity`'s signature default and every key of phase_params
   against `get_periods`'s, plus the signature keys the YAML does not carry.

Asserts, in-process, that `cyclophaser` resolves to this working tree.
Writes params_track_vs_defaults.json next to it.
"""
import hashlib
import importlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import cyclophaser  # noqa: E402

assert os.path.realpath(cyclophaser.__file__).startswith(os.path.realpath(ROOT) + os.sep), cyclophaser.__file__
assert os.path.basename(sys.prefix) == "cyclophaser", sys.prefix
dp = importlib.import_module("cyclophaser.determine_periods")

PRE_REF = sys.argv[1] if len(sys.argv) > 1 else "d8a19cc"
OLD = "research/labels/configs/cyclophaser_params-15.yaml"
NEW = "research/labels/configs/cyclophaser_params-track.yaml"


def sig(fn):
    return {k: p.default for k, p in inspect.signature(fn).parameters.items()
            if p.default is not inspect.Parameter.empty}


old_bytes = subprocess.check_output(["git", "show", f"{PRE_REF}:{OLD}"], cwd=ROOT)
new_bytes = (ROOT / NEW).read_bytes()
sha_old = hashlib.sha256(old_bytes).hexdigest()
sha_new = hashlib.sha256(new_bytes).hexdigest()

doc = yaml.safe_load(new_bytes)
rows, missing = [], []
for group, fn in (("filter_params", dp.process_vorticity), ("phase_params", dp.get_periods)):
    s = sig(fn)
    for k, v in doc[group].items():
        d = s.get(k, "(not in signature)")
        rows.append(dict(group=group, key=k, yaml=v, default=d, equal=(v == d and type(v) is type(d)) or v == d))
    missing += [dict(group=group, key=k, default=s[k]) for k in s
                if k not in doc[group] and k not in ("zeta_df", "vorticity")]
diff = [r for r in rows if not r["equal"]]
out = dict(pre_ref=PRE_REF, sha256_params15_before=sha_old, sha256_params_track_after=sha_new,
           identical_bytes=old_bytes == new_bytes, n_yaml_keys=len(rows), differing=diff,
           signature_keys_absent_from_yaml=missing,
           cyclophaser_file=os.path.relpath(cyclophaser.__file__, ROOT))
(Path(__file__).with_name("params_track_vs_defaults.json")).write_text(
    json.dumps(out, indent=1, ensure_ascii=False, default=repr))
print(f"P2: params-15@{PRE_REF} {sha_old[:12]}… -> params-track {sha_new[:12]}… identical={out['identical_bytes']}")
print(f"YAML keys {len(rows)}; differing from the signature defaults: "
      + (", ".join(f"{r['group']}.{r['key']} yaml={r['yaml']!r} default={r['default']!r}" for r in diff) or "none"))
print("signature keys absent from the YAML: "
      + (", ".join(f"{m['group']}.{m['key']}={m['default']!r}" for m in missing) or "none"))
