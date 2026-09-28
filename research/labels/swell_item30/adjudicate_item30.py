"""Item 30, part 3, step 1 — adjudicate 5 TRAIN labels to the item-30 counterfactual.

Danilo's decision (27 Sept 2026): in the 5 TRAIN cases where the counterfactual of
`1a3ad76` differs from params-14 (20120297, 19940445, 19810854, 19860380,
19870927), the label becomes the counterfactual's phases.

What this script does, in order, and refuses to do twice:

1. **Snapshot.** The 7 TRAIN labels of the swell batch, as they are in
   `manual_labels.yaml` right now, block by block (the exact text of each
   `- id:` block) with the sha256 of each block, into `labels_v1_snapshot.yaml`.
   The 3 TEST blocks of the batch are not touched: only the `- id:` lines are
   scanned to find where blocks end.
2. **Counterfactual.** Recomputed with the code that produced `1a3ad76`
   (`diagnostics/item30/figs_cf.py`, unchanged since), under params-14, and
   asserted equal to the sequences recorded in `REPORT_figs_cf.md`.
3. **Records.** Built by `make_label_record` (validated like any label), through
   `upsert_label`, so the original also stays in the record's `superseded`.
   * `series_sha256` asserted equal to the original's.
   * `notes` = `labels_core.ADJUDICATED_NOTE` — the provenance, in an existing
     optional field; no validator or schema change.
   * Tolerance kept from the original. The top-level `tolerance_idx` is the
     original's. Per phase, the k-th phase of a given name takes the tolerance
     of the original's k-th phase of that name; a phase the original never had
     takes the original's top-level tolerance.
   * `unsure` False on every boundary (an adjudication is a decision);
     `open_unsure` / `close_unsure` as in the original.
   * `overlays_shown` = the original's ∪ {"item30_counterfactual"}: the label
     IS detector output and must not read as blind.
4. **Proof.** Every one of the other 68 `- id:` blocks is byte-identical before
   and after (compared by bytes, never parsed here).

Run once: python research/labels/swell_item30/adjudicate_item30.py
"""

import hashlib
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
LABELS_DIR = HERE.parent
ITEM30 = LABELS_DIR / "diagnostics" / "item30"
sys.path.insert(0, str(ITEM30))
import figs_cf  # noqa: E402
import item30_core as core  # noqa: E402

lc = core.lc
SNAPSHOT = HERE / "labels_v1_snapshot.yaml"
ADJ = ["20120297", "19940445", "19810854", "19860380", "19870927"]
# REPORT_figs_cf.md (1a3ad76), counterfactual column.
EXPECTED = {
    "20120297": "intensification > mature > decay > residual",
    "19940445": "intensification > mature > decay",
    "19810854": "intensification > mature > decay",
    "19860380": "intensification > mature > decay",
    "19870927": "incipient > intensification > mature > decay > intensification "
                "> mature > decay",
}


def blocks(text: str) -> dict[str, str]:
    """{id: exact text of its `- id:` block} — split on the id lines only."""
    starts = [(m.start(), m.group(1)) for m in
              re.finditer(r"^- id: '?([^'\n]+)'?\n", text, flags=re.M)]
    out = {}
    for k, (pos, sid) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text)
        out[sid] = text[pos:end]
    return out


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


class _Literal(str):
    pass


yaml.SafeDumper.add_representer(
    _Literal, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"))


def snapshot(text: str, train7: list[str]) -> None:
    b = blocks(text)
    doc = {
        "what": "the 7 TRAIN labels of the swell_item30 batch before the item-30 "
                "adjudication, each `- id:` block of manual_labels.yaml byte for byte",
        "source_file": "research/labels/manual_labels.yaml",
        "source_file_sha256": sha(text),
        "taken": "2026-09-27",
        "labels": {sid: {"block_sha256": sha(b[sid]), "block": _Literal(b[sid])}
                   for sid in train7},
    }
    SNAPSHOT.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    back = yaml.safe_load(SNAPSHOT.read_text())["labels"]
    for sid in train7:
        assert back[sid]["block"] == b[sid] and sha(back[sid]["block"]) == back[sid]["block_sha256"], sid


def phases_from(cf_runs, orig: dict) -> list[dict]:
    by_name: dict[str, list[int]] = {}
    for p in orig["phases"]:
        by_name.setdefault(lc.normalize_phase(p["phase"]), []).append(int(p["tolerance_idx"]))
    seen: dict[str, int] = {}
    out = []
    for ph, a, _ in cf_runs:
        k = seen.get(ph, 0)
        seen[ph] = k + 1
        tols = by_name.get(ph, [])
        out.append({"phase": ph, "start_idx": int(a),
                    "tolerance_idx": tols[k] if k < len(tols) else int(orig["tolerance_idx"]),
                    "unsure": False})
    return out


def main() -> None:
    assert not SNAPSHOT.exists(), f"{SNAPSHOT} exists — this script runs once"
    sets = core.split_sets()
    train7 = sorted(sets["batch_train"])
    assert len(train7) == 7 and set(ADJ) <= set(train7)
    assert set(ADJ).isdisjoint(core.excluded_ids())

    before = lc.LABELS_PATH.read_text()
    snapshot(before, train7)
    labels = core.train_labels()                    # TRAIN records only
    assert not any(lc.is_adjudicated(labels[s]) for s in ADJ), "already adjudicated"

    batch = lc.load_batch_series()
    cfg14 = core.load_config("params-14")
    new = {}
    for sid in ADJ:
        r14 = core.run_series(batch[sid], *cfg14)
        cand = figs_cf.sep.candidates(r14, pd.Series(r14["z"]))
        cf, from_s5 = figs_cf.counterfactual(r14, cand)
        assert from_s5 and cf != r14["final"], sid
        runs = figs_cf.norm_runs(cf)
        assert figs_cf.seq_of(runs) == EXPECTED[sid], (sid, figs_cf.seq_of(runs))
        orig = labels[sid]
        rec = lc.make_label_record(
            sid, orig["source"], batch[sid], phases_from(runs, orig),
            notes=lc.ADJUDICATED_NOTE, open_unsure=orig.get("open_unsure", False),
            close_unsure=orig.get("close_unsure", False),
            overlays_shown=list(orig.get("overlays_shown") or []) + ["item30_counterfactual"])
        assert rec["series_sha256"] == orig["series_sha256"], sid
        rec["tolerance_idx"] = int(orig["tolerance_idx"])
        new[sid] = rec

    for sid in ADJ:
        lc.upsert_label(new[sid])

    after = lc.LABELS_PATH.read_text()
    bb, ba = blocks(before), blocks(after)
    assert set(bb) == set(ba) and len(bb) == 73
    others = [s for s in bb if s not in ADJ]
    same = [s for s in others if bb[s] == ba[s]]
    assert len(others) == 68 and len(same) == 68, (len(others), len(same))
    hb, ha = before.split("labels:\n", 1)[0], after.split("labels:\n", 1)[0]
    print(f"snapshot: {SNAPSHOT.name}, 7 TRAIN blocks, sha256 each, round-trip OK")
    print(f"adjudicated: {len(ADJ)} — {', '.join(ADJ)}")
    print(f"other blocks byte-identical: {len(same)}/{len(others)}")
    print(f"header before: {hb.strip()!r}\nheader after:  {ha.strip()!r}")
    print(f"manual_labels.yaml sha256 before {sha(before)[:16]} after {sha(after)[:16]}")


if __name__ == "__main__":
    main()
