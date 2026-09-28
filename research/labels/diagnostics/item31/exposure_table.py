"""Item 31, stage 0, task 3 — per-series exposure of the TEST series, from the repo's records.

Source policy: every row is reconstructed from a record committed in this repo
(docs/future_work.md, research/**/REPORT*.md, research/labels/swell_item30/README.md,
split.yaml). The item-31 opening brief is NOT a source. No test label is read,
no detector is run.

Each event below carries a SOURCE ANCHOR — an exact substring of the cited file.
The script locates it, reports `file:line`, and asserts that every series the
event names individually appears within a small window around that line. A
record that moved or was reworded fails loudly instead of being cited blind.

Exposure kinds
--------------
  P  parameters chosen/calibrated with the series in the set (visual criterion)
  D  detector output SEEN by a person (plot / app / render)
  M  detector output COMPUTED and written to a committed record (mechanical, no label)
  L  label content read (whole or partial)
  S  scored against its label / spent (a result on the record)
  ?  risk the records cannot settle — a question for Danilo

Outputs: exposure_table.md, exposure_table.json.
Run: python -P research/labels/diagnostics/item31/exposure_table.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item31_core as core  # noqa: E402

FW = "docs/future_work.md"
ALL16 = "ALL16"
BATCH3 = "BATCH3"
WINDOW = (-4, 10)          # lines around the anchor in which a named id must appear

EVENTS = [
    # id, kind, series, config, when, what, source, anchor
    ("E01", "P,D", ALL16, "pre-split configs (items 3b/3c)", "≤ 2026-09-03 (pre-split)",
     "The 51 real tracks were the package's visual calibration set; the "
     "'bad cases' evaluation ran over all 51, test-to-be included.",
     FW, "**Remaining bad cases (4/51) and diagnoses:**"),
    ("E02", "P,D", ["20206498", "20150561"], "pre-split", "≤ 2026-09-03 (pre-split)",
     "Named as remaining bad cases of the pre-split calibration.",
     FW, "**Remaining bad cases (4/51) and diagnoses:**"),
    ("E03", "D", ["20160030"], "pre-split (mature_method work, item 3b)", "pre-split",
     "Used as the concrete case for mature_method='amplitude'.",
     FW, "actually most intense — observed concretely on case 20160030"),
    ("E04", "M", ALL16, "pipeline of 01c4492", "2026-09-04 (pre-split)",
     "Incipient characterisation measured on all 51 tracks.",
     "research/incipient_plateau/REPORT_incipient_characterisation.md",
     "| Data | 51 tracks in `tests/calibration_data/`"),
    ("E05", "M,D", ["20206498", "20150377", "20203373", "20170225", "20204655"],
     "incipient smoothing sweep", "2026-09 (pre-labels)",
     "Per-track values tabulated and discussed in the smoothing report.",
     "research/incipient_plateau/REPORT_incipient_smoothing.md", "| 20206498 | 0.677 |"),
    ("E06", "P", ["20150561", "20160030", "20180654", "20203373"],
     "pre-correction config", "before item 24",
     "4 of the 7 documented 'convert' cases calibrating decay_tail_amplitude_fraction "
     "(docstrings of tests/test_decay_tail_amplitude_fraction.py).",
     FW, "**4 of the 7 documented convert cases are in the frozen test split**"),
    ("E07", "M", ALL16, "inert-parameter sweep", "2026-09-10 (post-split)",
     "Inertia sweep and default-output sha256 over all 51 tracks.",
     "research/inert_params/REPORT_inertia_sweep.md", "over all 51 `tests/calibration_data` tracks"),
    ("E08", "D", ["20150561", "20170225"], "item-3 fix before/after", "2026-09-10 (post-split)",
     "Before/after renders of the item-3 fix reviewed visually "
     "(research/labels/diagnostics/04_item3_*).",
     FW, "calibration tracks**: `20150561`, `20150656`, `20170225`"),
    ("E09", "D", ALL16, "params-10", "≤ 2026-09-17",
     "The 16 test cases inspected visually in the calibration app.",
     FW, "**Exposure on the record:** the 16 test cases were inspected visually under"),
    ("E10", "L", ["20150377"], "—", "split check",
     "Its label was read during the split check.",
     FW, "label for `20150377` was read during the split check"),
    ("E11", "S", ["20180654"], "front C (intensification_min_depth)", "2026-09-22",
     "Measured and reported, with authorisation: a declared spend.",
     FW, "**`20180654` was measured and reported with Danilo's explicit authorisation**"),
    ("E12", "D", ["20160030"], "params-13", "2026-09 (front D opening)",
     "Detector output (absence of incipient) seen by Danilo.",
     FW, "**Exposure on the record:** `20160030`"),
    ("E13", "D", ["20150646"], "—", "front D opening",
     "The case that motivated front D; NOT measured, NOT spent.",
     FW, "`20150646`, the"),
    ("E14", "M", ["20206498"], "params of fronts A/A′/28", "2026-09-23/24",
     "Run mechanically; sequence and index-0 typing reported (label never read).",
     FW, "`20206498` (test), and `peak->valley` on `20190639`."),
    ("E15", "M", ["20170756"], "front 28 stage 1", "2026-09-23",
     "Index-0 typing and leading decay reported.",
     FW, "**A leading `decay` does not require a `valley` at index 0.** `20170756` (test"),
    ("E16", "L,S", "15 of 16 (which 15 not recorded)", "front 28 stage 2 gate", "2026-09-24",
     "Labels of 15 TEST tracks were read into a sequence-match AGGREGATE "
     "('62 label-carrying series: 42 → 42'); corrected at the source.",
     FW, "series: 42 → 42\", which had read the labels of 15 held-out TEST tracks into an"),
    ("E17", "M", ALL16, "params-14 / floors 0.0", "2026-09-25",
     "Inspector fidelity sweeps over all 51 real tracks, test included (no label).",
     FW, "all 51 real tracks, test split included"),
    ("E18", "M", ["20180654", "20206498"], "30a first pass", "2026-09-25",
     "Pinned in tests in the first pass, replaced before verification; "
     "MATURE_TRACKS still lists 20206498.",
     FW, "first pass pinned 20180654 and 20206498, both TEST tracks"),
    ("E19", "D", ["20203389"], "params-14 values (export named params-11)", "2026-09-24",
     "Among the 200 swell tracks evaluated with detection in the Grid; label not read.",
     FW, "the original TEST series **20203389** was among the 200 swell"),
    ("E20", "D", BATCH3, "params-14", "2026-09-25",
     "Batch test cases were seen with params-14 detection before being labelled once.",
     FW, "fact all 10, were seen with the `params-14` detection before labelling"),
    ("E21", "L", ["20111118"], "—", "2026-09-25",
     "1 bit: stored verdict ≠ verdict derived from its phases.",
     FW, "It observed that **20111118's stored verdict ≠ the verdict derived from"),
    ("E22", "D", ALL16 + "+" + BATCH3, "**params-15**", "2026-09-27",
     "All 19 test series (+20203389) evaluated visually in the Grid UNDER PARAMS-15, "
     "the comparator stage 1 would score; 20150377 and 20206498 marked bad; marks "
     "used in no decision.",
     FW, "the 16 of the split, the 3 of the batch and 20203389. Danilo marked 20150377"),
    # Stage 0 recorded E23 as "?" (anchored at future_work.md: the 'Train then
    # Test' bug). Danilo answered on 2026-09-28; the answer is recorded in
    # DESIGN.md §8.3, which is now the source.
    ("E23", "S", ALL16, "UNRECORDED — may include **params-15**", "since 2026-09-18",
     "Danilo CONFIRMS having displayed TEST blocks in the Benchmark tab (sequence + "
     "mature scored against the 16 test labels); the configs were not recorded and may "
     "include params-15. Answered 2026-09-28 (stage 0 had it as '?').",
     "research/labels/diagnostics/item31/DESIGN.md",
     "3. **E23, answered.** **Danilo confirms that he displayed TEST blocks in the"),
]


def locate(path: str, anchor: str) -> int:
    lines = (core.REPO / path).read_text().splitlines()
    hits = [i for i, ln in enumerate(lines, 1) if anchor in ln]
    assert hits, f"anchor not found in {path}: {anchor!r}"
    return hits[0]


def named_ids_near(path: str, line: int, ids) -> None:
    lines = (core.REPO / path).read_text().splitlines()
    lo, hi = max(0, line - 1 + WINDOW[0]), min(len(lines), line + WINDOW[1])
    block = "\n".join(lines[lo:hi])
    for sid in ids:
        assert sid in block, f"{sid} not within {WINDOW} lines of {path}:{line}"


def main() -> None:
    core.assert_environment()
    sets = core.split_sets()
    test16, batch3 = sorted(sets["test"]), sorted(sets["batch_test"])
    assert len(test16) == 16 and len(batch3) == 3

    events = []
    for eid, kind, series, cfg, when, what, src, anchor in EVENTS:
        line = locate(src, anchor)
        if isinstance(series, list):
            named_ids_near(src, line, series)
            members = series
        elif series == ALL16:
            members = test16
        elif series == BATCH3:
            members = batch3
        elif series == ALL16 + "+" + BATCH3:
            members = test16 + batch3
        else:
            members = []           # set-level, unnamed ("15 of 16")
        assert set(members) <= set(test16) | set(batch3), (eid, members)
        events.append({"id": eid, "kind": kind, "series": series if isinstance(series, str)
                       else ", ".join(series), "members": members, "config": cfg,
                       "when": when, "what": what, "source": f"{src}:{line}"})

    per = {sid: [e for e in events if sid in e["members"]] for sid in test16 + batch3}
    unnamed = [e for e in events if not e["members"]]

    md = ["# Item 31 — exposure of the TEST series, reconstructed from the repo's records",
          "", "Generated by `exposure_table.py`. Every source is `file:line`, located by an "
          "exact anchor and checked at generation time. The opening brief of item 31 is not "
          "a source. Kinds: **P** parameters chosen with it in the set · **D** detector "
          "output seen · **M** detector output computed into a record · **L** label content "
          "read · **S** scored/spent · **?** unsettled by the records.", "",
          "## Events", "", "| event | kind | series | config | when | what | source |",
          "|---|---|---|---|---|---|---|"]
    for e in events:
        md.append(f"| {e['id']} | {e['kind']} | {e['series']} | {e['config']} | {e['when']} | "
                  f"{e['what']} | `{e['source']}` |")
    md += ["", "## Per series", "",
           "| series | block | strongest kind (named events) | + set-level | events | sources |",
           "|---|---|---|---|---|---|"]
    for sid in test16 + batch3:
        ev = per[sid]
        kinds = {k for e in ev for k in e["kind"].split(",")}
        strongest = next((k for k in "SLDMP?" if k in kinds), "—")
        setlevel = ("L,S possible (E16: 15 of the 16, unnamed)" if sid in test16 else "—")
        md.append(f"| {sid} | {'split test' if sid in test16 else 'batch test'} | {strongest} | "
                  f"{setlevel} | "
                  f"{', '.join(e['id'] for e in ev)} | "
                  f"{'; '.join(sorted({e['source'] for e in ev}))} |")
    md += ["", "Set-level events that name no series: "
           + "; ".join(f"{e['id']} ({e['series']}, `{e['source']}`)" for e in unnamed), ""]
    (HERE / "exposure_table.md").write_text("\n".join(md))
    (HERE / "exposure_table.json").write_text(json.dumps(
        {"events": events, "per_series": {k: [e["id"] for e in v] for k, v in per.items()}},
        indent=2))
    print("\n".join(md))


if __name__ == "__main__":
    main()
