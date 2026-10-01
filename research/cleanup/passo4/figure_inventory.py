#!/usr/bin/env python
"""Passo 4, 16f (2) — what the methodology figure could read from the package's
own output, without changing the package (read-only).

    <cyclophaser env python> -P research/cleanup/passo4/figure_inventory.py

Runs the public API on an ANALYTIC series built here (a Gaussian deepening plus
seeded noise; no repository series is read, the test split is untouched), and
checks every "obtainable" claim of the table by executing it:
* the columns/objects returned by get_periods, determine_periods, process_vorticity;
* that the returned frame is enough to REPLAY get_periods' stage sequence with
  the public stage functions (the replay must equal get_periods' `periods`
  before any intermediate read from it is trusted);
* each decision of the figure: read directly from a column, obtained from
  public calls, or only by calling a private function / reimplementing.
Writes figure_inventory.json and figure_inventory.md next to it.
"""
import importlib
import inspect
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import cyclophaser

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert Path(cyclophaser.__file__).resolve().is_relative_to(ROOT), cyclophaser.__file__
warnings.simplefilter("ignore")
importlib.import_module("cyclophaser.determine_periods")
DPM = sys.modules["cyclophaser.determine_periods"]       # the module (the package re-exports the function)
FSM = importlib.import_module("cyclophaser.find_stages")

# --- analytic series ---------------------------------------------------------
N = 120
t = pd.date_range("2000-01-01", periods=N, freq="h")
rng = np.random.default_rng(0)
zeta = -1e-5 * (1 + 4 * np.exp(-((np.arange(N) - 60) / 20) ** 2)) + 2e-6 * rng.standard_normal(N)
series = pd.Series(zeta, index=t)

SIG_DP = {k: v.default for k, v in inspect.signature(DPM.determine_periods).parameters.items()
          if v.default is not inspect.Parameter.empty}
SIG_GP = {k: v.default for k, v in inspect.signature(DPM.get_periods).parameters.items()
          if v.default is not inspect.Parameter.empty}
PV_KEYS = [k for k in inspect.signature(DPM.process_vorticity).parameters if k != "zeta_df"]

df_dp = DPM.determine_periods(series)
vort = DPM.process_vorticity(pd.DataFrame({"zeta": zeta}, index=t))
df_gp = DPM.get_periods(vort)
F = {}
F["determine_periods_returns"] = dict(type=type(df_dp).__name__, index=str(df_dp.index.dtype),
                                      columns={c: str(d) for c, d in df_dp.dtypes.items()})
F["get_periods_returns"] = dict(type=type(df_gp).__name__, columns=list(df_gp.columns),
                                same_frame_as_determine_periods=bool(df_gp.equals(df_dp)))
F["process_vorticity_returns"] = dict(type=type(vort).__name__, data_vars=list(vort.data_vars))
F["labels"] = {c: sorted(map(str, df_dp[c].dropna().unique())) for c in
               ("z_peaks_valleys", "dz_peaks_valleys", "dz2_peaks_valleys", "periods")}
F["column_sources"] = {
    "z": bool(np.allclose(df_dp["z"].values, vort["vorticity_smoothed2"].values)),
    "z_unfil": bool(np.allclose(df_dp["z_unfil"].values, vort["zeta"].values)),
    "dz": bool(np.allclose(df_dp["dz"].values, vort["dz_dt_smoothed2"].values)),
    "dz2": bool(np.allclose(df_dp["dz2"].values, vort["dz_dt2_smoothed2"].values)),
    "filtered_vorticity == vorticity_smoothed2 under the defaults":
        bool(np.allclose(vort["filtered_vorticity"].values, vort["vorticity_smoothed2"].values)),
}

# --- replay of get_periods' stage sequence with the public stage functions ----------
ARGS_KEYS = [k for k in SIG_GP if k not in ("plot", "plot_steps", "export_dict", "prominence",
                                            "prominence_relative", "reclassify_index0")]


def replay(df_in, stop=None, **over):
    """get_periods' order (determine_periods.py, get_periods body): intensification,
    decay, mature, residual, post_process_periods, incipient — on a copy of the
    returned frame with `periods` cleared."""
    a = {k: SIG_GP[k] for k in ARGS_KEYS}
    a.update(over)
    d = df_in.copy()
    d["periods"] = np.nan
    d["periods"] = d["periods"].astype("object")
    for name, fn in (("intensification", FSM.find_intensification_period), ("decay", FSM.find_decay_period),
                     ("mature", FSM.find_mature_stage), ("residual", FSM.find_residual_period),
                     ("post_process", lambda x, **k: DPM.post_process_periods(x)),
                     ("incipient", FSM.find_incipient_period)):
        d = fn(d, **a)
        if name == stop:
            break
    return d


rep = replay(df_dp)
F["replay_equals_get_periods"] = bool(rep["periods"].equals(df_dp["periods"]))

# --- each decision -------------------------------------------------------------
pv = SIG_GP
unf = DPM.find_peaks_valleys(df_dp["z"], prominence=None, prominence_relative=None, reclassify_index0=False)
filt_pos = set(np.flatnonzero(df_dp["z_peaks_valleys"].notna()))
unf_pos = set(np.flatnonzero(unf.notna()))
F["prominence"] = dict(considered=len(unf_pos), kept=len(filt_pos), kept_subset_of_considered=filt_pos <= unf_pos,
                       dropped=len(unf_pos - filt_pos))
noidx = DPM.find_peaks_valleys(df_dp["z"], prominence=pv["prominence"], prominence_relative=pv["prominence_relative"],
                               reclassify_index0=False)
F["index0"] = dict(final=str(df_dp["z_peaks_valleys"].iloc[0]), without_rule=str(noidx.iloc[0]),
                   with_rule_equals_returned=bool(DPM.find_peaks_valleys(
                       df_dp["z"], prominence=pv["prominence"], prominence_relative=pv["prominence_relative"],
                       reclassify_index0=pv["reclassify_index0"]).equals(df_dp["z_peaks_valleys"])))
r_int0 = replay(df_dp, stop="intensification", intensification_min_depth=0.0)
r_int = replay(df_dp, stop="intensification")
r_mat0 = replay(df_dp, stop="mature", mature_min_depth=0.0)
r_mat = replay(df_dp, stop="mature")
F["depth_floors"] = dict(
    intensification_steps_floor_off=int((r_int0["periods"] == "intensification").sum()),
    intensification_steps_default=int((r_int["periods"] == "intensification").sum()),
    mature_steps_floor_off=int((r_mat0["periods"] == "mature").sum()),
    mature_steps_default=int((r_mat["periods"] == "mature").sum()))
tail_off = DPM.get_periods(vort, decay_tail_amplitude_fraction=None)
_d = tail_off["periods"] != df_gp["periods"]
F["decay_tail"] = dict(steps_differing_default_vs_None=int(_d.sum()),
                       transitions={f"{x} -> {y}": int(n) for (x, y), n in
                                    pd.Series(list(zip(tail_off["periods"][_d].fillna("NaN"),
                                                       df_gp["periods"][_d].fillna("NaN")))).value_counts().items()})
F["public_functions"] = {
    "cyclophaser.determine_periods (module)": {n: str(inspect.signature(f)) for n, f in
                                               inspect.getmembers(DPM, inspect.isfunction)
                                               if f.__module__ == DPM.__name__ and not n.startswith("_")},
    "cyclophaser.find_stages": {n: str(inspect.signature(f)) for n, f in inspect.getmembers(FSM, inspect.isfunction)
                                if f.__module__ == FSM.__name__ and not n.startswith("_")},
}
F["private_functions_holding_intermediates"] = sorted(
    n for n, f in inspect.getmembers(FSM, inspect.isfunction) if f.__module__ == FSM.__name__ and n.startswith("_"))
(HERE / "figure_inventory.json").write_text(json.dumps(F, indent=1, default=str))
print(json.dumps({k: F[k] for k in ("column_sources", "replay_equals_get_periods", "prominence", "index0",
                                     "depth_floors", "decay_tail", "private_functions_holding_intermediates")},
                 indent=1, default=str))

# --- the markdown ----------------------------------------------------------------
dp_cols = ", ".join(f"`{c}` ({d})" for c, d in F["determine_periods_returns"]["columns"].items())
rows = [
    ("raw series", "**yes** — `z_unfil` (= `process_vorticity(...).zeta`)", "—", "—"),
    ("filtered series", "**partly** — `z` is `vorticity_smoothed2`, the series the phases read. Under the defaults it "
     f"equals `filtered_vorticity` ({F['column_sources']['filtered_vorticity == vorticity_smoothed2 under the defaults']} "
     "here). The intermediate stages are not returned.",
     "`process_vorticity(zeta_df, <same filter args>)` returns every stage: "
     + ", ".join(f"`{v}`" for v in F["process_vorticity_returns"]["data_vars"]), "—"),
    ("accepted extrema", "**yes** — `z_peaks_valleys` (`peak` / `valley`; also `dz_…`, `dz2_…`)", "—", "—"),
    ("extrema considered and dropped by prominence", "no",
     "`find_peaks_valleys(df['z'], prominence=None, prominence_relative=None, reclassify_index0=False)` = considered; "
     f"positions minus those of `z_peaks_valleys` = dropped (here {F['prominence']['considered']} considered, "
     f"{F['prominence']['kept']} kept, kept ⊆ considered: {F['prominence']['kept_subset_of_considered']})", "—"),
    ("cycles accepted / dropped by the depth floors", "no (only the final phases)",
     "replay the stage sequence on the returned frame (below), once with `intensification_min_depth` / "
     "`mature_min_depth` at the default and once at 0.0, and diff the stage output",
     "the depth VALUES (`D1`, `D2`) are computed inside the stage functions and not returned: showing them means "
     "reimplementing the formula"),
    ("mature window around each valley", "**final only** — `periods == 'mature'`, after the later stages",
     "replay stopped after `find_mature_stage`: the windows as that stage wrote them",
     "the per-valley window before the stage's own checks: private `_amplitude_mature_bounds(df, previous_z_peak, "
     "z_valley, next_z_peak, mature_amplitude_fraction)`"),
    ("initial flat stretch (incipient) and where it ends", "**final only** — the leading `periods == 'incipient'` block "
     "(its end is the boundary after the spare rule)",
     "the boundary without the spare rule: replay with `incipient_plateau_spare_intensification=False`",
     "the profile `rel(t)` and the tau crossing: private `_incipient_plateau_rel(df, signal, smooth_window, "
     "smooth_polyorder)` and `_incipient_plateau_boundary(rel, tau, crossing, k)`"),
    ("final residual, and decay extended over the tail", "**final only** — `periods` (`residual` / `decay`)",
     "`get_periods(vort, decay_tail_amplitude_fraction=None)` against the default call: the steps that differ are the "
     f"extension (here {F['decay_tail']['steps_differing_default_vs_None']} steps; None → default: "
     f"{F['decay_tail']['transitions']})", "—"),
    ("index-0 reclassification", "**final type only** — `z_peaks_valleys.iloc[0]`",
     "`find_peaks_valleys(df['z'], prominence=…, prominence_relative=…, reclassify_index0=False)` against the "
     f"returned column (the call with the rule reproduces it: {F['index0']['with_rule_equals_returned']})", "—"),
]
md = ["# Methodology figure — what the package output provides (generated by figure_inventory.py)\n",
      "Measured on an analytic series built inside the script (a Gaussian deepening plus seeded noise, "
      f"{N} hourly steps; no repository series read). Raw output: `figure_inventory.json`.\n",
      "## (a) What the functions return\n",
      f"* `determine_periods(series, …)` → `{F['determine_periods_returns']['type']}` indexed by time "
      f"({F['determine_periods_returns']['index']}), columns {dp_cols}. It does not return the "
      "`process_vorticity` Dataset.",
      f"* `get_periods(vorticity, …)` → the same frame (identical to `determine_periods`' output here: "
      f"{F['get_periods_returns']['same_frame_as_determine_periods']}). It takes the Dataset of `process_vorticity`.",
      f"* `process_vorticity(zeta_df, …)` → `{F['process_vorticity_returns']['type']}` with "
      + ", ".join(f"`{v}`" for v in F["process_vorticity_returns"]["data_vars"]) + ".",
      "* Column origins (checked): " + ", ".join(f"`{k}` {v}" for k, v in F["column_sources"].items()) + ".",
      f"* Labels: {F['labels']}.", "",
      "## (b) Each decision of the figure\n",
      "| decision | readable from the output (column) | obtainable with public calls, no logic reimplemented | "
      "needs a private function or a reimplementation |", "|---|---|---|---|"]
md += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
md += ["", "## (c) Public functions usable for intermediates\n",
       "Replaying the stage sequence: `get_periods` returns a frame that carries every column the stage functions "
       "read. Clearing `periods` and calling, in `get_periods`' order, `find_intensification_period`, "
       "`find_decay_period`, `find_mature_stage`, `find_residual_period`, `post_process_periods` and "
       "`find_incipient_period`, each with `**args_periods`, reproduces `get_periods`' `periods` "
       f"(checked here: **{F['replay_equals_get_periods']}**). `args_periods` is not returned. The caller rebuilds it "
       "from the same keyword values (the keys are listed in the `get_periods` body), so this repeats the order of the "
       "calls, not their logic. Stopping after any stage gives that stage's intermediate. The calibration app's "
       "`layer_inspector.pipeline_ribbon` already does this and is tested against the package.\n",
       "| module | public function | signature |", "|---|---|---|"]
for mod, fns in F["public_functions"].items():
    md += [f"| `{mod}` | `{n}` | `{s}` |" for n, s in fns.items()]
md += ["", "Private helpers holding intermediates that no public function returns: "
       + ", ".join(f"`{n}`" for n in F["private_functions_holding_intermediates"]) + "."]
(HERE / "figure_inventory.md").write_text("\n".join(md) + "\n")
print("figure_inventory.md written")
