"""Release v2.1, part A, passo 2 — apply Danilo's 3 re-labels to manual_labels.yaml.

Applies, ONLY to the records of 20150656, 20170409 and 20170154, the version saved
by the Label tab in commit 0c63145 ("data: save 4 manual label re-labels made
through the app"): the corrected value, the new `labeled_at`, the schema-4
interface fields (`open_unsure`/`close_unsure`/`overlays_shown`, which the current
file already uses on other records) and the `superseded` block holding the
previous record.

The file is NOT copied from the tag. Each of the 3 record blocks is replaced in
the text of the current file by the tag's block for the same id; every other byte
is asserted unchanged (20180170, s5dcc0f79 and the header included). Before
writing, the script asserts that each tag block is, parsed, the current record
plus exactly the expected changes, and that its `superseded[0]` equals the current
record field for field — so the history preserves the original blind label.

Run once: conda run -n cyclophaser python -P research/release_v21/passo2/apply_relabels.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
LABELS = REPO / "research" / "labels" / "manual_labels.yaml"
TAG = "0c63145"
IDS = ("20150656", "20170409", "20170154")


def blocks(text: str) -> tuple[str, dict[str, str]]:
    """Split the document into (header, {id: record block text}), in file order."""
    starts = [m.start() for m in re.finditer(r"^- id: ", text, flags=re.M)]
    header = text[:starts[0]]
    out = {}
    for a, b in zip(starts, starts[1:] + [len(text)]):
        blk = text[a:b]
        sid = yaml.safe_load(blk)[0]["id"]
        assert sid not in out, sid
        out[sid] = blk
    assert header + "".join(out.values()) == text
    return header, out


def main() -> None:
    cur_text = LABELS.read_text()
    tag_text = subprocess.run(["git", "show", f"{TAG}:research/labels/manual_labels.yaml"],
                              cwd=REPO, capture_output=True, text=True, check=True).stdout
    header, cur = blocks(cur_text)
    _, tag = blocks(tag_text)

    expected_value_change = {
        "20150656": lambda r: r["phases"][3].__setitem__("start_idx", 100),
        "20170409": lambda r: r["phases"][3].__setitem__("start_idx", 71),
        "20170154": lambda r: r.__setitem__("verdict", {"kind": "ambiguous"}),
    }
    new = dict(cur)
    for sid in IDS:
        c = yaml.safe_load(cur[sid])[0]
        t = yaml.safe_load(tag[sid])[0]
        assert "superseded" not in c, sid
        # history: the tag's superseded entry IS the current record
        assert t["superseded"] == [c], sid
        # the vigente record: current + the value change + new labeled_at + interface fields
        want = {k: v for k, v in yaml.safe_load(cur[sid])[0].items()}
        expected_value_change[sid](want)
        want["labeled_at"] = t["labeled_at"]
        for k in ("open_unsure", "close_unsure", "overlays_shown"):
            want[k] = t[k]
        got = {k: v for k, v in t.items() if k != "superseded"}
        assert got == want, (sid, got, want)
        new[sid] = tag[sid]

    out = header + "".join(new.values())
    # nothing outside the 3 blocks moved
    _, chk = blocks(out)
    assert list(chk) == list(cur)
    assert all(chk[s] == cur[s] for s in cur if s not in IDS)
    LABELS.write_text(out)
    print(f"rewrote {len(IDS)} record blocks in {LABELS.relative_to(REPO)}")


if __name__ == "__main__":
    main()
