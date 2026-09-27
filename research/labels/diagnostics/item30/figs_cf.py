"""Item 30 — figures: label × params-13 × params-14 × counterfactual, case by case.

DIAGNOSTIC ONLY. Nothing in cyclophaser/ changes, and no rule is proposed: the
counterfactual exists so that Danilo can review his own labels against what the
plateau overwrite erased. It is NOT a candidate rule.

Cases (TRAIN only; the 16 test ids of the split and the 3 of the batch are
excluded by id before anything is read):

* L: 20120297, 19940445, 19810854; K: 19790612, 19860380, 19870927;
* P controls: the two P cases with the largest c3 in
  `separability_train_params14.csv` (part 2), chosen by that file, not by hand.

Counterfactual (closed definition, params-14, no variants):

* s5 = step 5 of the ribbon (pre-incipient), s6 = step 6 (final);
* E = the first intensification block of s5 that starts before the plateau
  boundary (part 2's definition, `separability.candidates`);
* if E exists and c3 = 1: counterfactual = s5 with [0, E.start) written as
  incipient (nothing written if E.start = 0); otherwise counterfactual = s6.

Outputs: figs_cf/<id>.png, figs_cf/board_8_cases.png, REPORT_figs_cf.md.

Run: python research/labels/diagnostics/item30/figs_cf.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import item30_core as core  # noqa: E402
import separability as sep  # noqa: E402

lc, li, dp = core.lc, core.li, core.dp
import cyclophaser  # noqa: E402

OUT = HERE / "figs_cf"
L, K = sep.L, sep.K
# The app's colours (tools/calibration_app/app.py PHASE_COLORS).
PHASE_COLORS = {"incipient": "#65a1e6", "intensification": "#f7b538",
                "mature": "#d62828", "decay": "#9aa981", "residual": "gray"}
LAYERS = ("filtered_vorticity", "vorticity_smoothed", "vorticity_smoothed2")


def p_controls() -> list[str]:
    t = pd.read_csv(HERE / "separability_train_params14.csv", dtype={"id": str})
    p = t[t.group == "P"].sort_values("c3", ascending=False)
    return list(p.id[:2])


def norm_runs(labels) -> list[tuple[str, int, int]]:
    return [(lc.normalize_phase(ph), a, b) for ph, a, b in core.runs(labels)]


def seq_of(rs) -> str:
    out = []
    for ph, _, _ in rs:
        if not out or out[-1] != ph:
            out.append(ph)
    return " > ".join(out)


def incipient_end(rs) -> int:
    """Start of the phase after a leading incipient run (the label's convention:
    `incipient_end_idx` is the next phase's start_idx). A map that does not open
    in incipient has its incipient ending at step 0 — it is 0, not missing, so
    the distance to the label stays defined."""
    if not rs or rs[0][0] != "incipient":
        return 0
    return rs[1][1] if len(rs) > 1 else rs[0][2] + 1


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance between two ' > '-joined phase sequences, by phase."""
    a, b = a.split(" > "), b.split(" > ")
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[-1]


def compare(p14: int, cf: int) -> str:
    return "same" if p14 == cf else ("closer" if cf < p14 else "further")


def label_runs(rec) -> list[tuple[str, int, int]]:
    return [(lc.normalize_phase(p), a, b) for p, a, b in core.bc.label_runs_for(rec)]


def counterfactual(r: dict, cand: dict) -> tuple[list, bool]:
    """(map, built_from_s5)."""
    if cand["E_start"] is not None and cand["c3"] == 1:
        cf = list(r["pre"])
        cf[:cand["E_start"]] = ["incipient"] * cand["E_start"]
        return cf, True
    return list(r["final"]), False


def case(sid, values, cfg13, cfg14, rec, group) -> dict:
    r14 = core.run_series(values, *cfg14)
    r13 = core.run_series(values, *cfg13)
    cand = sep.candidates(r14, pd.Series(r14["z"]))
    cf, from_s5 = counterfactual(r14, cand)
    with np.errstate(all="ignore"):
        v = dp.process_vorticity(pd.DataFrame({"zeta": values}), **cfg14[0])
    raw = li.rescaler([v["zeta"].values], True)(v["zeta"].values)
    grp = li.rescaler([v[n].values for n in LAYERS], True)
    return {"id": sid, "group": group, "r14": r14, "cand": cand,
            "same_13_14": r13["final"] == r14["final"],
            "diff_13_14": [i for i, (a, b) in enumerate(zip(r13["final"], r14["final"]))
                           if a != b],
            "maps": {"label": label_runs(rec), "params-13": norm_runs(r13["final"]),
                     "params-14": norm_runs(r14["final"]), "counterfactual": norm_runs(cf)},
            "cf_from_s5": from_s5, "cf_equals_s6": cf == r14["final"],
            "raw01": raw, "smooth01": grp(v["vorticity_smoothed2"].values)}


def _fmt(x):
    return "—" if x is None else f"{x:.3g}"


def draw(axes, c) -> None:
    ax, bands = axes[0], axes[1:]
    n, r, cand = c["r14"]["n"], c["r14"], c["cand"]
    x = np.arange(n)
    ax.plot(x, c["raw01"], color="dimgray", lw=1.0, label="raw ζ (own 0-1 band)")
    ax.plot(x, c["smooth01"], color="#e63946", lw=1.4,
            label="vorticity_smoothed2 (processed-group 0-1 band)")
    marks = [(r["boundary"], "plateau boundary", "k", "-"),
             (r["peak"], "peak (argmin z)", "#6a4c93", "--")]
    if cand["E_start"] is not None:
        marks += [(cand["E_start"], "E start", "#f7b538", ":"),
                  (cand["E_end"], "E end", "#f7b538", "-.")]
    for pos, lab, col, ls in marks:
        ax.axvline(pos, color=col, ls=ls, lw=1.1, label=f"{lab} = {pos}")
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("0-1", fontsize=7)
    ax.legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    ax.set_title(f"{c['id']} · group {c['group']} · c1 {_fmt(cand['c1'])} · "
                 f"c2 {_fmt(cand['c2'])} · c3 {_fmt(cand['c3'])}", fontsize=9)
    for bax, (name, rs) in zip(bands, c["maps"].items()):
        for ph, a, b in rs:
            bax.axvspan(a - 0.5, b + 0.5, color=PHASE_COLORS.get(ph, "white"), lw=0)
        bax.set_yticks([])
        bax.set_ylabel(name, fontsize=7, rotation=0, ha="right", va="center")
        if name == "params-13" and c["same_13_14"]:
            bax.text(0.5, 0.5, "identical to params-14", transform=bax.transAxes,
                     ha="center", va="center", fontsize=7,
                     bbox=dict(facecolor="white", alpha=0.8, lw=0))
    bands[-1].set_xlabel("step", fontsize=7)
    for a in axes:
        a.set_xlim(-0.5, n - 0.5)
        a.tick_params(labelsize=6)


def figure(cases, path) -> None:
    rows = []
    for _ in cases:
        rows += [3.2, 0.45, 0.45, 0.45, 0.45, 1.3]
    fig = plt.figure(figsize=(9, 0.75 * sum(rows)))
    gs = fig.add_gridspec(len(rows), 1, height_ratios=rows, hspace=0.08)
    for k, c in enumerate(cases):
        ax0 = fig.add_subplot(gs[6 * k])
        axes = [ax0] + [fig.add_subplot(gs[6 * k + j], sharex=ax0) for j in range(1, 5)]
        for a in axes[:-1]:
            a.tick_params(labelbottom=False)
        draw(axes, c)
    handles = [plt.Rectangle((0, 0), 1, 1, color=v) for v in PHASE_COLORS.values()]
    fig.legend(handles, PHASE_COLORS, loc="lower center", ncol=5, fontsize=7,
               frameon=False)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    print("cyclophaser.__file__ =", cyclophaser.__file__)
    print("layer_inspector.__file__ =", li.__file__)
    assert Path(cyclophaser.__file__).resolve().is_relative_to(core.REPO)
    assert Path(li.__file__).resolve().is_relative_to(core.REPO)
    print("environment:", core.environment())

    P = p_controls()
    ids = L + K + P
    groups = {**{s: "L" for s in L}, **{s: "K" for s in K}, **{s: "P" for s in P}}
    sets, excl = core.split_sets(), core.excluded_ids()
    train_ids = sets["train"] | sets["batch_train"]
    assert all(s in train_ids and s not in excl for s in ids), ids

    series = {k: v for k, v in lc.load_real_series().items() if k in ids}
    series |= {k: v for k, v in lc.load_batch_series().items()
               if k in ids and k in sets["batch_train"]}
    assert set(series) == set(ids)
    labels = core.train_labels()
    cfg13, cfg14 = core.load_config("params-13"), core.load_config("params-14")

    cases = [case(s, series[s], cfg13, cfg14, labels[s], groups[s]) for s in ids]
    OUT.mkdir(exist_ok=True)
    for c in cases:
        figure([c], OUT / f"{c['id']}.png")
    figure(cases, OUT / "board_8_cases.png")

    print("P controls (largest c3 in P):", P)
    print("params-13 == params-14 (final map):",
          {c["id"]: c["same_13_14"] for c in cases})
    for s in P + ["19790612"]:
        c = next(c for c in cases if c["id"] == s)
        print(f"{s}: counterfactual == s6 -> {c['cf_equals_s6']}")
        assert c["cf_equals_s6"], s

    lines = [
        "# Item 30 — label × params-13 × params-14 × counterfactual (TRAIN only)",
        "",
        "Diagnostic for Danilo's review of his own labels. **The counterfactual is not "
        "a rule proposal.** It uses params-14: s5 with [0, E.start) written as incipient "
        "when E exists and c3 = 1, and otherwise s6. Figures are in `figs_cf/`, one per "
        "case, plus `board_8_cases.png`.",
        "",
        f"* P controls, the two largest c3 in P (part 2's table): {', '.join(P)}.",
        "* params-13 vs params-14, final map: "
        + ("identical in all 8 cases." if all(c["same_13_14"] for c in cases) else
           "; ".join(f"{c['id']} differs at {c['diff_13_14']}" for c in cases
                     if not c["same_13_14"])),
        "* Counterfactual == s6 in "
        + ", ".join(f"{s} ({'yes' if next(c for c in cases if c['id'] == s)['cf_equals_s6'] else 'NO'})"
                    for s in P + ["19790612"]) + ".",
        "* **Incipient end** follows the label's convention: the start of the phase "
        "after a leading incipient run. A map that does not open in incipient ends it "
        "at step 0 (a counterfactual with E.start = 0 writes no incipient at all). "
        "The column gives label / params-14 / counterfactual, then |p14 − label| → "
        "|cf − label|.",
        "* **Sequence** is compared by edit distance to the label's sequence (phases "
        "inserted, removed or substituted), params-14 → counterfactual. 0 = identical.",
        "* 'closer' / 'further' / 'same' compare the counterfactual's distance with "
        "params-14's, per column.",
        "",
        "| id | group | c3 | label sequence | params-14 sequence | counterfactual sequence "
        "| incipient end (label / p14 / cf; distance) | sequence edit distance |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in cases:
        rec = labels[c["id"]]
        lab_end = core.label_marks(rec)["label_incipient_end"]
        assert isinstance(lab_end, int), (c["id"], lab_end)   # true for all 8
        m = c["maps"]
        e14, ecf = incipient_end(m["params-14"]), incipient_end(m["counterfactual"])
        d14, dcf = abs(e14 - lab_end), abs(ecf - lab_end)
        sl, s14, scf = seq_of(m["label"]), seq_of(m["params-14"]), seq_of(m["counterfactual"])
        q14, qcf = edit_distance(s14, sl), edit_distance(scf, sl)
        lines.append(f"| {c['id']} | {c['group']} | {_fmt(c['cand']['c3'])} | {sl} | {s14} "
                     f"| {scf} | {lab_end} / {e14} / {ecf}; {d14} → {dcf} "
                     f"**{compare(d14, dcf)}** | {q14} → {qcf} **{compare(q14, qcf)}** |")
    (HERE / "REPORT_figs_cf.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-len(cases) - 2:]))


if __name__ == "__main__":
    main()
