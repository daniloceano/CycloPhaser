"""Release v2.1, part A, passo 2 — checks on the edited manual_labels.yaml.

  a. every record (vigente and each `superseded` entry) passes labels_core's
     validators: validate_phases (with n_steps), validate_verdict, not legacy;
  b. parsed-label diff (not text) between develop-v2.1 and the working tree:
     exactly 3 ids differ, and every changed field is listed;
  c. first_blind_record returns the ORIGINAL values for the 3 series, the vigente
     record the corrected ones;
  d. the 10 swell_item30 labels are present and unchanged.

Writes checks.txt next to this file. Run:
  conda run -n cyclophaser python -P research/release_v21/passo2/check_labels_file.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "research" / "labels"))
import labels_core as lc  # noqa: E402

BASE = "develop-v2.1"
IDS = ("20150656", "20170409", "20170154")


def flat(d, prefix=""):
    """{dotted.path: leaf} for a nested record, so field diffs are listed by path."""
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            out.update(flat(v, f"{prefix}.{k}" if prefix else str(k)))
        return out
    if isinstance(d, list) and d and all(isinstance(x, dict) for x in d):
        out = {}
        for i, v in enumerate(d):
            out.update(flat(v, f"{prefix}[{i}]"))
        return out
    return {prefix: d}


def main() -> None:
    out, fails = [], []

    def check(ok: bool, msg: str) -> None:
        out.append(f"  [{'OK' if ok else 'FAIL'}] {msg}")
        if not ok:
            fails.append(msg)

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                          text=True, check=True).stdout.strip()
    base_sha = subprocess.run(["git", "rev-parse", BASE], cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
    out.append("RELEASE v2.1 — PART A — PASSO 2 — checks on manual_labels.yaml")
    out.append(f"labels_core: {Path(lc.__file__).resolve().relative_to(REPO)}")
    out.append(f"HEAD {head}; base {BASE} = {base_sha}")

    new = lc.read_labels()
    base_doc = yaml.safe_load(subprocess.run(
        ["git", "show", f"{BASE}:research/labels/manual_labels.yaml"], cwd=REPO,
        capture_output=True, text=True, check=True).stdout)
    old = {r["id"]: r for r in base_doc["labels"]}
    new_doc = yaml.safe_load(lc.LABELS_PATH.read_text())

    # a.
    out.append("\na. labels_core validators")
    errs = []
    n_checked = 0
    for sid, rec in new.items():
        for i, r in enumerate(lc.label_history(rec)):
            n_checked += 1
            try:
                assert not lc.is_legacy_record(r), "legacy"
                ph = lc.validate_phases(r["phases"], n_steps=int(r["n_steps"]))
                assert ph == r["phases"], "validate_phases normalises the stored phases"
                assert lc.validate_verdict(r["verdict"]) == r["verdict"], \
                    "validate_verdict normalises the stored verdict"
            except Exception as e:  # noqa: BLE001
                errs.append(f"{sid} history[{i}]: {e!r}")
    check(not errs, f"{n_checked} record versions ({len(new)} cases) validate "
                    f"unchanged{'' if not errs else ': ' + '; '.join(errs)}")
    check(new_doc["schema"] == lc.LABELS_SCHEMA == base_doc["schema"],
          f"schema {new_doc['schema']} (labels_core.LABELS_SCHEMA {lc.LABELS_SCHEMA})")
    check(new_doc["n_labels"] == len(new) == len(old),
          f"n_labels {new_doc['n_labels']} == {len(new)} records == {len(old)} on {BASE}")
    check({k: v for k, v in new_doc.items() if k != "labels"}
          == {k: v for k, v in base_doc.items() if k != "labels"},
          "document header (schema, updated, n_labels) unchanged")

    # b.
    out.append(f"\nb. parsed-label diff {BASE} -> working tree")
    changed = sorted(s for s in set(old) | set(new) if old.get(s) != new.get(s))
    check(set(old) == set(new), "same set of ids")
    check(tuple(sorted(changed)) == tuple(sorted(IDS)),
          f"ids that differ: {changed}")
    for sid in changed:
        fo, fn = flat(old.get(sid, {})), flat(new.get(sid, {}))
        out.append(f"  {sid}:")
        for k in sorted(set(fo) | set(fn), key=lambda k: (k.startswith("superseded"), k)):
            if fo.get(k, "<absent>") != fn.get(k, "<absent>"):
                if k.startswith("superseded"):
                    continue
                out.append(f"    {k}: {fo.get(k, '<absent>')!r} -> {fn.get(k, '<absent>')!r}")
        sup = new[sid].get("superseded")
        cur_old = {k: v for k, v in old[sid].items() if k != "superseded"}
        out.append(f"    superseded: <absent> -> list of {len(sup)} "
                   f"(entry 0 == {BASE} record, field for field: {sup == [cur_old]})")
        check(sup == [cur_old], f"{sid}: superseded[0] equals the {BASE} record")

    # c.
    out.append("\nc. first_blind_record vs vigente")

    def vals(r):
        return {"20150656": ("residual start_idx", r["phases"][3]["start_idx"]),
                "20170409": ("decay start_idx", r["phases"][3]["start_idx"]),
                "20170154": ("verdict", r["verdict"])}

    want_blind = {"20150656": 91, "20170409": 74,
                  "20170154": {"kind": "boundary", "incipient_end_idx": 6}}
    want_cur = {"20150656": 100, "20170409": 71, "20170154": {"kind": "ambiguous"}}
    for sid in IDS:
        fb = lc.first_blind_record(new[sid])
        name, vb = vals(fb)[sid]
        _, vc = vals(new[sid])[sid]
        out.append(f"  {sid}: first_blind_record {name} = {vb!r} "
                   f"(labeled_at {fb['labeled_at']}, overlays_shown "
                   f"{fb.get('overlays_shown', '<absent>')!r}); vigente {name} = {vc!r} "
                   f"(labeled_at {new[sid]['labeled_at']}, overlays_shown "
                   f"{new[sid].get('overlays_shown')!r}, is_blind {lc.is_blind(new[sid])})")
        check(vb == want_blind[sid], f"{sid}: first_blind_record returns the original {want_blind[sid]!r}")
        check(vc == want_cur[sid], f"{sid}: vigente returns the corrected {want_cur[sid]!r}")

    # d.
    out.append("\nd. swell_item30")
    swell = sorted(lc.batch_membership())
    check(len(swell) == 10, f"{len(swell)} ids in batches.swell_item30 of split.yaml")
    missing = [s for s in swell if s not in new]
    moved = [s for s in swell if s in new and new[s] != old.get(s)]
    check(not missing, f"all present ({'missing ' + str(missing) if missing else '10/10'})")
    check(not moved, f"all unchanged, parsed ({'changed ' + str(moved) if moved else '10/10'})")

    out.append(f"\nRESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} failed checks)")
    text = "\n".join(out) + "\n"
    (HERE / "checks.txt").write_text(text)
    print(text)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
