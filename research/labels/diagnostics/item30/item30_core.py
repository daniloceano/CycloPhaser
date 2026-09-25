"""Shared core of the item-30 measurement: one series through the pipeline, stage by stage.

MEASUREMENT ONLY. Nothing here changes cyclophaser/; the package functions are
called, never re-implemented.

Per series, `run_series` returns:

* the final phase map, from `get_periods` itself;
* the pre-incipient map: step 5 (`post_process_periods`) of
  `layer_inspector.pipeline_ribbon`. In `get_periods`, step 5 is followed
  directly by `find_incipient_period` (determine_periods.py 1247 → 1250), and
  inside that function the only write to `periods` before the overwrite
  `df.iloc[:boundary] = 'incipient'` (find_stages.py:1134, defect H) is
  `fillna('incipient')`, which only fills NaN cells. So every NON-NaN label of
  step 5 is exactly what line 1134 overwrites;
* the plateau boundary (the start of the first run of k = 5 samples with
  rel >= 0.2), from the package's own `_incipient_plateau_rel` and
  `_incipient_plateau_boundary`;
* the peak, `argmin` of the filtered `z` that `get_periods` returns;
* the blocks overwritten at step 6 (`ribbon_overwrites`), as positions.

Two things are ASSERTED on every series, not assumed:

1. The ribbon's step 6 equals `get_periods`' `periods`, value for value.
2. Every step-6 overwrite lies inside [0, boundary) and writes `incipient`, so
   what is attributed to H is H.

The `args_periods` the ribbon receives is CAPTURED from inside `get_periods` (its
first stage call is wrapped), not transcribed. On this branch
`layer_inspector.build_args_periods` still lacks the two depth floors (the item
30a fix is on develop, not here), so it is deliberately not used.
`build_working_frame` and `pipeline_ribbon` are identical to develop's.

C2' (`reclassify_index0`) runs BEFORE every stage: it is applied inside
`find_peaks_valleys(z)` while the working frame is built
(determine_periods.py 1206–1209; `build_working_frame` here), not in any of the
six steps.
"""

from __future__ import annotations

import inspect
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[4]
for p in (REPO, REPO / "tools" / "calibration_app", REPO / "research" / "labels"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import cyclophaser  # noqa: E402
import cyclophaser.find_stages as fs  # noqa: E402
import layer_inspector as li  # noqa: E402

dp = sys.modules["cyclophaser.determine_periods"]
import benchmark_core as bc  # noqa: E402
import labels_core as lc  # noqa: E402
from package_args import package_use_filter  # noqa: E402

assert Path(cyclophaser.__file__).resolve().is_relative_to(REPO), cyclophaser.__file__
assert Path(li.__file__).resolve().is_relative_to(REPO), li.__file__

CONFIGS = REPO / "research" / "labels" / "configs"
TAU, K = 0.2, 5            # the definitions of the 1faf0c8 exploratory, asserted below


def environment() -> dict:
    import scipy
    return {"cyclophaser": str(Path(cyclophaser.__file__).relative_to(REPO)),
            "layer_inspector": str(Path(li.__file__).relative_to(REPO)),
            "python": sys.version.split()[0], "numpy": np.__version__,
            "scipy": scipy.__version__, "pandas": pd.__version__}


def load_config(name: str) -> tuple[dict, dict]:
    """(process_vorticity kwargs, get_periods kwargs) exactly as the app runs them."""
    doc = yaml.safe_load((CONFIGS / f"cyclophaser_{name}.yaml").read_text())
    pv, gp = bc.split_config(doc)
    return {**pv, "use_filter": package_use_filter(pv["use_filter"])}, gp


def _frame_kwargs(gp: dict) -> dict:
    sig = inspect.signature(dp.get_periods).parameters
    return {k: gp.get(k, sig[k].default)
            for k in ("prominence", "prominence_relative", "reclassify_index0")}


def runs(labels) -> list[tuple[str, int, int]]:
    """[(phase, start, end_inclusive)] of contiguous labels; NaN shown as '—'."""
    out, prev, s = [], object(), 0
    labs = ["—" if (x is None or (isinstance(x, float) and np.isnan(x))) else str(x)
            for x in labels]
    for i, x in enumerate(labs):
        if x != prev:
            if i:
                out.append((prev, s, i - 1))
            prev, s = x, i
    if labs:
        out.append((prev, s, len(labs) - 1))
    return out


def seq(labels) -> str:
    return " > ".join(r[0] for r in runs(labels))


def symptom(final) -> bool:
    """Mature with no intensification before it, in the final map (m1's definition)."""
    R = runs(final)
    first_int = next((a for ph, a, _ in R if ph.startswith("intensification")), None)
    first_mat = next((a for ph, a, _ in R if ph.startswith("mature")), None)
    return first_mat is not None and (first_int is None or first_int > first_mat)


def run_series(values: pd.Series, pv: dict, gp: dict) -> dict:
    captured = {}
    orig = dp.find_intensification_period

    def _cap(df, **a):
        captured.update(a)
        return orig(df, **a)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        v = dp.process_vorticity(pd.DataFrame({"zeta": values}), **pv)
        dp.find_intensification_period = _cap
        try:
            res = dp.get_periods(v, **gp)
        finally:
            dp.find_intensification_period = orig
        df0 = li.build_working_frame(v, **_frame_kwargs(gp))
        steps = li.pipeline_ribbon(df0, **captured)

    final = res["periods"].astype(object).tolist()
    step6 = steps[5][1].astype(object).tolist()
    same = [(a == b) or (pd.isna(a) and pd.isna(b)) for a, b in zip(final, step6)]
    assert len(final) == len(step6) and all(same), "ribbon step 6 != get_periods"

    assert captured["incipient_plateau_tau"] == TAU and captured["incipient_plateau_k"] == K
    assert captured["incipient_plateau_crossing"] == "sustained"
    rel = fs._incipient_plateau_rel(df0, captured["incipient_plateau_signal"],
                                    captured["incipient_smooth_window"],
                                    captured["incipient_smooth_polyorder"])
    boundary = fs._incipient_plateau_boundary(rel, TAU, "sustained", K)
    z = res["z"].to_numpy(float)
    peak = int(np.argmin(z))

    idx = steps[5][1].index
    erased = []
    for o in li.ribbon_overwrites(steps):
        if o["step"] != li.STEP_NAMES[5]:
            continue
        a, b = int(idx.get_loc(o["start"])), int(idx.get_loc(o["end"]))
        assert o["to"] == "incipient" and b < boundary, (o, boundary)
        erased.append((o["from"], a, b))

    return {"n": len(final), "boundary": int(boundary), "peak": peak,
            "signal": boundary > peak, "pre": steps[4][1].astype(object).tolist(),
            "final": final, "erased": erased, "symptom": symptom(final),
            "args": captured}


def int_blocks(labels) -> list[tuple[int, int]]:
    return [(a, b) for ph, a, b in runs(labels) if ph.startswith("intensification")]


# ── populations: TEST is excluded by id before anything else is touched ────────

def split_sets() -> dict[str, set]:
    """{'train', 'test', 'batch_train', 'batch_test'} from split.yaml."""
    sp = lc.read_split()
    bm = lc.batch_membership(split_doc=sp)
    return {"train": set(sp["train"]), "test": set(sp["test"]),
            "batch_train": {s for s, m in bm.items() if m == "train"},
            "batch_test": {s for s, m in bm.items() if m == "test"}}


def excluded_ids() -> set:
    """Every TEST id — the 16 of the split and the 3 of the batch."""
    s = split_sets()
    return s["test"] | s["batch_test"]


def train_labels() -> dict[str, dict]:
    """Labels of TRAIN series only (split train + batch train).

    `read_labels` parses the file and keys it by id; every record whose id is not
    a train id is dropped HERE, by id alone, before any of its fields is read.
    """
    s = split_sets()
    keep = s["train"] | s["batch_train"]
    assert keep.isdisjoint(excluded_ids())
    return {sid: r for sid, r in lc.read_labels().items() if sid in keep}


def label_marks(rec: dict) -> dict:
    """Label's intensification start (first intensification phase) and incipient end."""
    ph = rec["phases"]
    int_start = next((p["start_idx"] for p in ph if p["phase"] == "intensification"), None)
    v = rec["verdict"]
    inc_end = v.get("incipient_end_idx") if v["kind"] == "boundary" else v["kind"]
    return {"label_int_start": int_start, "label_incipient_end": inc_end,
            "label_seq": " > ".join(p["phase"] for p in ph)}
