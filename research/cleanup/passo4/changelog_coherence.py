#!/usr/bin/env python
"""Passo 4, commit 17 — CHANGELOG [Unreleased] coherence: every entry that
introduced a parameter as opt-in gets one line with the CURRENT default, read
from the signature (never typed); "Default X" sentences that describe the value
at introduction are marked as the pre-item-31 default, checked against
research/labels/defaults_2.0.0.json. Idempotence is not needed: run once.

    <cyclophaser env python> -P research/cleanup/passo4/changelog_coherence.py
"""
import inspect
import json
from pathlib import Path

import cyclophaser
from cyclophaser.determine_periods import determine_periods

ROOT = Path(__file__).resolve().parents[3]
assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
SIG = {k: v.default for k, v in inspect.signature(determine_periods).parameters.items()}
PRE = json.loads((ROOT / "research/labels/defaults_2.0.0.json").read_text())
PRE = {**PRE["filter_params"], **PRE["phase_params"]}


def lit(v):
    return f'"{v}"' if isinstance(v, str) else repr(v)


def note(*names):
    now = ", ".join(f"`{n}={lit(SIG[n])}`" for n in names)
    return (f"*Current default: {now} (see the first entry of this section); "
            f"the text below describes the option as it was introduced.*")


p = ROOT / "CHANGELOG.md"
s = p.read_text()
log = []


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)
    log.append((old, new))


# notes after the headline of each opt-in entry (values from the signature)
for head, names in [
    ("segments may be accepted as intensification.**\n", ("intensification_min_depth",)),
    ("**`mature_min_depth` — an opt-in depth floor", ("mature_min_depth",)),
    ("unchanged by default)**\n", ("incipient_method",)),
    ("for the incipient probe (opt-in, default off)**\n", ("incipient_smooth_window", "incipient_smooth_polyorder")),
    ("**`boundary_padding` — opt-in fix for the Lanczos zero-padding edge artifact**\n", ("boundary_padding",)),
]:
    i = s.index(head)
    j = s.index("\n\n", i)                         # end of the headline paragraph
    rep(s[i:j + 2], s[i:j + 2] + note(*names) + "\n\n")

# "Default X" sentences that are the value at introduction = the pre-item-31 default
assert PRE["intensification_min_depth"] == 0.0 and PRE["mature_min_depth"] == 0.0
assert PRE["incipient_smooth_window"] == 0
rep("**Default `0.0` switches the floor off entirely**",
    "**`0.0` (the default before item 31) switches the floor off entirely**")
rep("**Default `0.0` is a no-op**", "**`0.0` (the default before item 31) is a no-op**")
rep("controlled by `incipient_smooth_window` (default `0`,\ndisabled — previous behaviour byte for byte)",
    "controlled by `incipient_smooth_window` (`0`, the default before item 31,\ndisables it — previous behaviour byte for byte)")
p.write_text(s)
out = ROOT / "research/cleanup/passo4/changelog_coherence_log.json"
out.write_text(json.dumps([dict(old=o, new=n) for o, n in log], indent=1, ensure_ascii=False))
print(f"{len(log)} edits; log {out.relative_to(ROOT)}")
