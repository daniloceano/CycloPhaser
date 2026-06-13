"""Generate diagnostic figures for all synthetic lifecycle cases.

Run from the repo root:
    python -m tests.synthetic.generate_figures

Figures are saved to tests/synthetic/figures/<case_id>.png.
"""

import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from cyclophaser.determine_periods import determine_periods, periods_to_dict
from tests.synthetic.cases import CASES

FIGDIR = Path(__file__).parent / "figures"
FIGDIR.mkdir(exist_ok=True)

PHASE_COLORS = {
    "incipient":       "#65a1e6",
    "intensification": "#f7b538",
    "mature":          "#d62828",
    "decay":           "#9aa981",
    "residual":        "gray",
}
_DEFAULT_COLOR = "#cccccc"


def _normalize(name: str) -> str:
    return name.rstrip(" 0123456789").strip()


def _color(phase: str) -> str:
    return PHASE_COLORS.get(_normalize(phase), _DEFAULT_COLOR)


def plot_case(case_id: str, case: dict) -> Path:
    series = case["series"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = determine_periods(series, x=series.index)
    d = periods_to_dict(df)

    fig, (ax_z, ax_dz) = plt.subplots(
        2, 1, figsize=(12, 6), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    fig.suptitle(case_id, fontsize=13, fontweight="bold")

    for ph, (st, en) in d.items():
        c = _color(ph)
        ax_z.axvspan(st, en, alpha=0.25, color=c)
        ax_dz.axvspan(st, en, alpha=0.25, color=c)

    ax_z.plot(series.index, series.values, "k-", lw=1.0, label="ζ raw")

    if "dz" in df.columns:
        ax_dz.plot(df.index, df["dz"], color="dimgray", lw=1.0)
    ax_dz.axhline(0, color="k", lw=0.5, ls="--")

    # Ground-truth segment boundaries (dotted vertical lines)
    for idx in (case.get("expected_starts_idx") or {}).values():
        ts = series.index[idx]
        ax_z.axvline(ts, color="navy", ls=":", lw=1.1, alpha=0.6)

    patches = [
        mpatches.Patch(color=_color(ph), label=ph, alpha=0.6)
        for ph in d
    ]
    ax_z.legend(handles=patches, loc="lower left", fontsize=8, ncol=3)

    ax_z.set_ylabel("ζ (s⁻¹)")
    ax_dz.set_ylabel("dz")
    ax_dz.set_xlabel("Time")
    fig.tight_layout()

    out = FIGDIR / f"{case_id}.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


if __name__ == "__main__":
    for cid, case in CASES.items():
        out = plot_case(cid, case)
        print(f"saved {out}")
    print(f"\nAll {len(CASES)} figures saved to {FIGDIR}")
