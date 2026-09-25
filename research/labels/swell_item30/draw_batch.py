"""Draw the item-30 swell batch: 10 tracks to be labelled, split 7 train / 3 test.

Front 30, selection part. The labelled set has no case where the end of the
incipient plateau falls after the intensity peak and wipes out the
intensification, so a fix for that pattern could only be calibrated on visual
marks. This draws 10 swell tracks into the labelled set, by a seeded rule, and
splits them into train and test BEFORE any of them is labelled.

It runs NO detector and draws NO figure. The existing split (the top-level
`seed`/`strata`/`train`/`test`/`source` of split.yaml, seed 20260905, 47/16) is
not touched in any line: the batch is APPENDED to split.yaml as a separate,
frozen block under `batches: swell_item30`.

Declared before drawing (this file is committed before it is run)
-----------------------------------------------------------------
* Seed: 20260925, `numpy.random.default_rng`, one generator for the whole draw.
* Population: the three groups of `groups_params11.yaml` (sha256 pinned below).
* Exclusion: the swell tracks that are ALREADY among the 51 labelled real
  series leave every group before the draw — 20180733 (train) and 20203389
  (test), found by id and confirmed by identical start, length and series
  (item 30 step 0c). If any group is then smaller than its draw, stop.
* Draw, groups in the order R, S, C; each group's members sorted by id first:
      chosen = rng.choice(members, size=k, replace=False)   # draw order kept
      order  = rng.permutation(k)
      train  = chosen[order[:n_train]];  test = chosen[order[n_train:]]
  with (k, n_train, n_test) = R (5, 4, 1) · S (3, 2, 1) · C (2, 1, 1).
  Total 7 train / 3 test.

Run once:
    python research/labels/swell_item30/draw_batch.py --source <dir with the 200 standard-format swell tracks>

`--source` is the local folder `cyclophaser_swell_tracks_test/standard/`
(`{id}.txt`, `time;min_max_zeta_850`, value = -1e-5 * vor42). The 10 drawn files
are copied BYTE FOR BYTE to tests/calibration_data/swell_item30/{id}.csv — the
51 real series' own format, one level down so the non-recursive
`glob("*.csv")` readers of tests/calibration_data keep seeing exactly 51.

Refuses to run if split.yaml already holds the batch: a draw redone after its
result has been seen is not a draw.
"""

import argparse
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(HERE.parent))
import labels_core as lc  # noqa: E402

BATCH = lc.SWELL_BATCH
SEED = 20260925
GROUPS_FILE = HERE / "groups_params11.yaml"
GROUPS_SHA256 = "382de59cff9d268bcafb4767155042f961ef5802fbd3af642bab0d465c985949"
DRAW = {"R": (5, 4, 1), "S": (3, 2, 1), "C": (2, 1, 1)}
EXCLUDED_OVERLAP = {"20180733": "train", "20203389": "test"}
PROVENANCE_FILE = HERE / "provenance.yaml"

RULE = (
    "Seed 20260925, numpy.random.default_rng, one generator. Swell tracks already "
    "among the 51 labelled real series leave every group first. Groups in order "
    "R, S, C, members sorted by id: chosen = rng.choice(members, k, replace=False); "
    "order = rng.permutation(k); train = chosen[order[:n_train]], test = the rest. "
    "(k, n_train, n_test): R (5, 4, 1), S (3, 2, 1), C (2, 1, 1).")

LABELLING_NOTE = (
    "Os casos do grupo R foram vistos por Danilo com a detecção antes da "
    "rotulagem; rotulagem não cega nesses casos. A detecção em tela foi a do "
    "arquivo que o app exportou como cyclophaser_params-11.yaml (sha256 "
    "6df2cc0721d080acc294d943a06e03fa0967fd7d91c81b9dccb48a347251f739), cujos "
    "parâmetros de filtro e de fase são idênticos aos de params-14 "
    "(intensification_min_depth 0.05, mature_min_depth 0.80, reclassify_index0 "
    "true) — não os do params-11 do repo (24dd7f22…), sob o qual os grupos foram "
    "calculados. A assinatura que define os grupos não lê esses dois pisos. Os "
    "200 tracks passaram pela mesma avaliação, então S e C também foram vistos "
    "com detecção, sem a marca de ruim.")


PROVENANCE = {
    "base": ("Gramcianinov et al. (2020), Atlantic extratropical cyclone tracks "
             "(TRACK on ERA5), Mendeley Data 4, 108111 — the same base as the 51 "
             "labelled real series"),
    "via": ("cyclone_monitor: per-cyclone Parquet files under "
            "data/processed/tracks_by_id on swell; 200 of 6789 drawn with "
            "random.Random(29).sample over the sorted list"),
    "id": "the original TRACK id of the cyclone_monitor file, unchanged",
    "conversion": "min_max_zeta_850 = -1e-5 * vor42 (vor42 in 1e-5 s^-1, positive)",
    "conversion_check": (
        "MEASURED (item 30 step 0d) on 20180733, the one swell track that is also "
        "a labelled TRAIN series: -1e-5 * vor42 vs the repo series — same 257 "
        "hourly times (lag 0), max|diff| 1.36e-20 (max relative 1.7e-16, 1 ulp; "
        "218/257 bit-identical), mean ratio 1.000, sign 257/257 negative; the "
        "standard-format file itself is byte-identical to "
        "tests/calibration_data/20180733.csv. 20203389 (TEST) is byte-identical "
        "too; its label was not read."),
    "format": "time;min_max_zeta_850, hourly, copied byte for byte",
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def draw(groups: dict[str, list[str]]) -> tuple[dict, dict]:
    """(assignment {id: (group, split)}, sizes after exclusion). Pure given SEED."""
    rng = np.random.default_rng(SEED)
    out, sizes = {}, {}
    for g in ("R", "S", "C"):
        members = sorted(set(groups[g]) - set(EXCLUDED_OVERLAP))
        sizes[g] = len(members)
        k, n_train, n_test = DRAW[g]
        if len(members) < k:
            raise SystemExit(f"STOP: group {g} has {len(members)} after exclusion, "
                             f"fewer than the {k} to draw")
        chosen = [str(x) for x in rng.choice(members, size=k, replace=False)]
        order = rng.permutation(k)
        for j, i in enumerate(order):
            out[chosen[i]] = (g, "train" if j < n_train else "test")
    return out, sizes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    args = ap.parse_args()

    split_text = lc.SPLIT_PATH.read_text(encoding="utf-8")
    if BATCH in (yaml.safe_load(split_text).get("batches") or {}):
        raise SystemExit(f"{lc.SPLIT_PATH.name} already holds batch {BATCH!r} — refusing to redraw")

    got = sha256_file(GROUPS_FILE)
    if got != GROUPS_SHA256:
        raise SystemExit(f"{GROUPS_FILE.name} sha256 {got} != pinned {GROUPS_SHA256}")
    gdoc = yaml.safe_load(GROUPS_FILE.read_text(encoding="utf-8"))
    groups = gdoc["groups"]
    everyone = set().union(*map(set, groups.values()))
    assert set(EXCLUDED_OVERLAP) <= everyone | set(gdoc["bad_marks"]), EXCLUDED_OVERLAP

    assignment, sizes = draw(groups)
    print("group sizes after exclusion:", sizes)

    dest = REPO_ROOT / lc.SWELL_BATCH_DATA_DIR
    dest.mkdir(parents=True, exist_ok=False)
    files = {}
    for sid in sorted(assignment):
        src = args.source / f"{sid}.txt"
        head = src.read_text(encoding="utf-8").splitlines()[0]
        if head != "time;min_max_zeta_850":
            raise SystemExit(f"{src.name}: unexpected header {head!r}")
        shutil.copyfile(src, dest / f"{sid}.csv")
        files[sid] = sha256_file(dest / f"{sid}.csv")

    ids = sorted(assignment)
    block = {"batches": {BATCH: {
        "frozen": True,
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "seed": SEED,
        "rng": "numpy.random.default_rng",
        "rule": RULE,
        "draw_script": "research/labels/swell_item30/draw_batch.py",
        "groups_file": "research/labels/swell_item30/groups_params11.yaml",
        "groups_file_sha256": GROUPS_SHA256,
        "group_definition": ("R = marked bad AND plateau_boundary > peak_idx; "
                             "S = good AND plateau_boundary > peak_idx; "
                             "C = good AND NOT plateau_boundary > peak_idx "
                             "(repo params-11, see groups_file)"),
        "excluded_overlap": dict(EXCLUDED_OVERLAP),
        "group_sizes_after_exclusion": sizes,
        "draw": {g: {"n": k, "n_train": a, "n_test": b} for g, (k, a, b) in DRAW.items()},
        "data_dir": lc.SWELL_BATCH_DATA_DIR,
        "train": [s for s in ids if assignment[s][1] == "train"],
        "test": [s for s in ids if assignment[s][1] == "test"],
        "group": {s: assignment[s][0] for s in ids},
        "source": {s: "real" for s in ids},
        "file_sha256": files,
        "labelling_note": LABELLING_NOTE,
    }}}
    sep = "" if split_text.endswith("\n") else "\n"
    lc.atomic_write_text(lc.SPLIT_PATH, split_text + sep + yaml.safe_dump(
        block, sort_keys=False, default_flow_style=False, allow_unicode=True, width=88))

    per_file = {}
    for sid in ids:
        lines = (dest / f"{sid}.csv").read_text(encoding="utf-8").splitlines()[1:]
        per_file[sid] = {"file": f"{lc.SWELL_BATCH_DATA_DIR}/{sid}.csv",
                         "sha256": files[sid], "original_id": sid,
                         "n_steps": len(lines),
                         "first_time": lines[0].split(";")[0],
                         "last_time": lines[-1].split(";")[0],
                         "group": assignment[sid][0], "split": assignment[sid][1]}
    PROVENANCE_FILE.write_text(yaml.safe_dump(
        {"batch": BATCH, **PROVENANCE, "files": per_file},
        sort_keys=False, default_flow_style=False, allow_unicode=True, width=88),
        encoding="utf-8")

    print(yaml.safe_dump({k: block["batches"][BATCH][k] for k in ("train", "test", "group")},
                         sort_keys=False))


if __name__ == "__main__":
    main()
