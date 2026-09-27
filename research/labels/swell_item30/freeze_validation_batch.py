"""Item 30, part 3, step 2 — freeze the 5-track VALIDATION batch (no label, no detection).

Role: VALIDATION — neither train nor test, and in no aggregate. The 5 exist to be
labelled blind by Danilo and to measure prediction V of
`diagnostics/item30/PREDICTIONS_part3.md` once.

Selection (deterministic, fixed before this script): the swell tracks that part 2
found with the signal AND with E defined, minus the ones already drawn into the
`swell_item30` batch — part 2's own per-track table,
`separability_swell17_params14.csv`, written OUTSIDE the repo. The selection is
CHECKED against that table, which is read, never printed; no detector is run
here.

What it does:

1. copies the 5 standard-format files byte for byte into
   `tests/calibration_data/swell_item30_val/` (one level down, so every
   non-recursive `*.csv` reader still sees 51);
2. appends `batches.swell_item30_val` at the END of split.yaml and proves the
   previous text is an exact prefix of the new one (so the 47/16 split and the
   swell_item30 block are byte-identical);
3. writes `provenance_val.yaml` (sha256, steps, first/last time per file).

Only counts are printed. Run once:
    python research/labels/swell_item30/freeze_validation_batch.py \
        --source <.../cyclophaser_swell_tracks_test/standard> \
        --part2-table <.../diag_item30/separability_swell17_params14.csv>
"""

import argparse
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import labels_core as lc  # noqa: E402

VAL = ["19900808", "19940737", "19960808", "20000821", "19861089"]
PROVENANCE_FILE = HERE / "provenance_val.yaml"
RULE = ("The swell tracks with the item-30 signal (plateau boundary > peak) and E "
        "defined under params-14 (part 2, separability.py step 2: 10 of 17), minus "
        "those already drawn into batches.swell_item30 — 5 tracks. Deterministic; "
        "fixed by Danilo's part-3 brief before this batch was frozen.")
NOTE = ("Sem rótulo e sem detecção ao congelar. Os 5 estão entre os 200 da amostra "
        "swell vistos por Danilo com detecção no Grid em 2026-09-24 (avaliação de "
        "marcas ruins), então a rotulagem de validação não é cega nesse sentido. "
        "Nesta parte nenhum aparece por caso em tabela, figura, log ou benchmark.")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--part2-table", type=Path, required=True)
    a = ap.parse_args()

    t = pd.read_csv(a.part2_table, dtype={"track_id": str})
    selected = set(t.track_id[t.E_start.notna() & ~t.drawn.astype(bool)])
    same = selected == set(VAL)
    print(f"selection check against part 2's table: {len(selected)} selected, "
          f"equal to the brief's 5: {same}")
    assert same

    split_text = lc.SPLIT_PATH.read_text(encoding="utf-8")
    before = yaml.safe_load(split_text)
    assert lc.VALIDATION_BATCH not in (before.get("batches") or {})
    assert set(VAL).isdisjoint(set(before["train"]) | set(before["test"])
                               | set(lc.batch_membership(split_doc=before)))

    dest = REPO_ROOT / lc.VALIDATION_BATCH_DATA_DIR
    dest.mkdir(parents=True, exist_ok=False)
    files = {}
    for sid in sorted(VAL):
        src = a.source / f"{sid}.txt"
        assert src.read_text(encoding="utf-8").splitlines()[0] == "time;min_max_zeta_850"
        shutil.copyfile(src, dest / f"{sid}.csv")
        files[sid] = sha256_file(dest / f"{sid}.csv")
        assert files[sid] == sha256_file(src)

    block = {lc.VALIDATION_BATCH: {
        "frozen": True,
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "role": "validation",
        "rule": RULE,
        "freeze_script": "research/labels/swell_item30/freeze_validation_batch.py",
        "data_dir": lc.VALIDATION_BATCH_DATA_DIR,
        "train": [],
        "test": [],
        "validation": sorted(VAL),
        "source": {s: "real" for s in sorted(VAL)},
        "file_sha256": files,
        "labelling_note": NOTE,
    }}
    dumped = yaml.safe_dump(block, sort_keys=False, default_flow_style=False,
                            allow_unicode=True, width=88)
    sep = "" if split_text.endswith("\n") else "\n"
    new_text = split_text + sep + "".join("  " + ln + "\n" for ln in dumped.splitlines())
    lc.atomic_write_text(lc.SPLIT_PATH, new_text)

    after_text = lc.SPLIT_PATH.read_text(encoding="utf-8")
    after = yaml.safe_load(after_text)
    assert after_text.startswith(split_text)
    assert after["train"] == before["train"] and after["test"] == before["test"]
    assert after["batches"][lc.SWELL_BATCH] == before["batches"][lc.SWELL_BATCH]
    assert lc.batch_membership(lc.VALIDATION_BATCH) == {s: "validation" for s in VAL}
    assert set(lc.load_batch_series(lc.VALIDATION_BATCH)) == set(VAL)

    per_file = {}
    for sid in sorted(VAL):
        lines = (dest / f"{sid}.csv").read_text(encoding="utf-8").splitlines()[1:]
        per_file[sid] = {"file": f"{lc.VALIDATION_BATCH_DATA_DIR}/{sid}.csv",
                         "sha256": files[sid], "original_id": sid, "n_steps": len(lines),
                         "first_time": lines[0].split(";")[0],
                         "last_time": lines[-1].split(";")[0], "role": "validation"}
    prov = yaml.safe_load((HERE / "provenance.yaml").read_text(encoding="utf-8"))
    PROVENANCE_FILE.write_text(yaml.safe_dump(
        {"batch": lc.VALIDATION_BATCH,
         **{k: prov[k] for k in ("base", "via", "id", "conversion", "format")},
         "files": per_file},
        sort_keys=False, default_flow_style=False, allow_unicode=True, width=88),
        encoding="utf-8")
    print(f"frozen: {len(VAL)} files copied byte for byte, sha256 recorded; "
          f"split.yaml previous text is an exact prefix: True")


if __name__ == "__main__":
    main()
