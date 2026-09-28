"""Item 31, stage 0 — shared helpers: environment guard, configs, the detector run.

DESIGN ONLY. Nothing here changes cyclophaser/; the package functions are called,
never re-implemented. No function here reads a TEST label or runs the detector on
a TEST series: `train_series` drops every TEST id (split and batch) by id before
any series is loaded into the returned dict, and asserts it.

The detector is run exactly the way `evaluate_against_labels.run_detector` runs
it — `get_periods(process_vorticity(DataFrame({'zeta': values}), **pv), **gp)`,
with `pv`/`gp` from `evaluate_against_labels.load_config` — so every sequence
here is on the evaluator's own ruler (`detected_phase_starts`).
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
LABELS = REPO / "research" / "labels"
CONFIGS = LABELS / "configs"
for p in (REPO, LABELS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import cyclophaser  # noqa: E402
from cyclophaser import determine_periods as _dp_mod  # noqa: E402,F401

dp = sys.modules["cyclophaser.determine_periods"]   # the MODULE, not the function
import evaluate_against_labels as ev  # noqa: E402
import labels_core as lc  # noqa: E402


def assert_environment() -> dict:
    """Refuse to run against anything but this working tree's package.

    The dedicated env is a worktree-shadowing vector (item 27): an editable
    install can point at another checkout. So the guard is on the resolved
    `cyclophaser.__file__`, not on the env name alone.
    """
    import numpy as np
    import scipy
    f = Path(cyclophaser.__file__).resolve()
    assert f.is_relative_to(REPO), f"cyclophaser imported from {f}, not {REPO}"
    assert Path(dp.__file__).resolve().is_relative_to(REPO), dp.__file__
    assert Path(sys.prefix).name == "cyclophaser", f"sys.prefix = {sys.prefix}"
    return {"cyclophaser.__file__": str(f.relative_to(REPO)),
            "sys.prefix": Path(sys.prefix).name, "python": sys.version.split()[0],
            "numpy": np.__version__, "scipy": scipy.__version__,
            "pandas": pd.__version__}


def config_path(name: str) -> Path:
    return CONFIGS / f"cyclophaser_{name}.yaml"


def load_config(name: str | None) -> tuple[dict, dict]:
    """(process_vorticity kwargs, get_periods kwargs) — the evaluator's loader.

    None = package defaults ({}, {}), exactly as the evaluator without --config.
    """
    return ev.load_config(None if name is None else config_path(name))


def run(values: pd.Series, pv: dict, gp: dict) -> list:
    """The final `periods` column as a list (the evaluator's call, warnings muted)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vort = dp.process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        res = dp.get_periods(vort, **gp)
    return res["periods"].astype(object).tolist()


def sequence(periods: list) -> tuple[str, ...]:
    """Normalised phase sequence, on the evaluator's own ruler."""
    return tuple(p for p, _ in ev.detected_phase_starts(pd.Series(periods, dtype=object)))


def incipient_end(periods: list):
    return ev.detected_incipient_end(pd.Series(periods, dtype=object))


def split_sets() -> dict[str, set]:
    sp = lc.read_split()
    bm = lc.batch_membership(lc.SWELL_BATCH, split_doc=sp)
    return {"train": set(sp["train"]), "test": set(sp["test"]),
            "batch_train": {s for s, m in bm.items() if m == "train"},
            "batch_test": {s for s, m in bm.items() if m == "test"},
            "source": dict(sp["source"])}


def test_ids() -> set:
    s = split_sets()
    return s["test"] | s["batch_test"]


def train_series() -> dict[str, dict[str, pd.Series]]:
    """{'original_real': 35, 'synthetic': 12, 'batch_train': 7} — TRAIN only.

    The loaders return every series in their folder (TEST included); the dicts
    below keep TRAIN ids only, and nothing from the loaders' raw return value
    leaves this function.
    """
    s = split_sets()
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    batch = lc.load_batch_series(lc.SWELL_BATCH)
    out = {
        "original_real": {k: real[k] for k in sorted(real) if k in s["train"]},
        "synthetic": {k: synth[k] for k in sorted(synth) if k in s["train"]},
        "batch_train": {k: batch[k] for k in sorted(batch) if k in s["batch_train"]},
    }
    got = set().union(*(set(d) for d in out.values()))
    assert got.isdisjoint(test_ids())
    assert [len(out[g]) for g in ("original_real", "synthetic", "batch_train")] == [35, 12, 7]
    for sid, v in (out["original_real"] | out["synthetic"]).items():
        assert s["source"][sid] == ("real" if sid in out["original_real"] else "synthetic")
    return out
