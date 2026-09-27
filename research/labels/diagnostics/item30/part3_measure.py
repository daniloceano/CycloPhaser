"""Item 30, part 3, step 4 — R1, R3, R4 and the three-block score, params-14 vs params-15.

Predictions: PREDICTIONS_part3.md (84f7c89), committed before the rule existed.
R2 is answered by front_b/default_behaviour_hash.py (see REPORT_part3.md).

BLIND VALIDATION. The 5 tracks of `batches.swell_item30_val` are part of the
swell 196 used for R3 and nowhere else. Nothing here prints, tabulates or draws
any of them per case: R3 is reported as counts only, and no per-track swell
table is written anywhere.

Populations (TEST excluded by id before anything is read):

* R1 / R4 — TRAIN: 35 real + 12 synthetic of the split, 7 of the swell batch.
* R3 — the 200 swell tracks minus the 3 batch TEST ids and 20203389 = 196.

Outputs: part3_measure_output.txt (via tee), evaluator runs under
part3_eval_params14.txt / part3_eval_params15.txt, figs_part3/*.png.

Run: python research/labels/diagnostics/item30/part3_measure.py --swell <.../standard>
"""

import argparse
import contextlib
import io
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figs_cf  # noqa: E402
import item30_core as core  # noqa: E402

lc, li = core.lc, core.li
import cyclophaser  # noqa: E402

LABELS = HERE.parent.parent
ADJ = ["20120297", "19940445", "19810854", "19860380", "19870927"]
GROUP = {"20120297": "L", "19940445": "L", "19810854": "L", "19860380": "K",
         "19870927": "K"}
EXCLUDED_SWELL = {"20203389"}           # the one swell track in the split's TEST


def final_map(values, cfg) -> list:
    return core.run_series(values, *cfg)["final"]


def r1(train, cfg14, cfg15) -> None:
    changed, equal_cf = [], {}
    for sid in sorted(train):
        f14, f15 = final_map(train[sid], cfg14), final_map(train[sid], cfg15)
        if f14 != f15:
            changed.append(sid)
    for sid in ADJ:
        r14 = core.run_series(train[sid], *cfg14)
        cand = figs_cf.sep.candidates(r14, pd.Series(r14["z"]))
        cf, _ = figs_cf.counterfactual(r14, cand)
        equal_cf[sid] = final_map(train[sid], cfg15) == cf
    print(f"R1: {len(train)} TRAIN series; params-15 final map differs from params-14 "
          f"in {len(changed)}: {', '.join(changed)}")
    print(f"R1: changed set == the predicted 5: {set(changed) == set(ADJ)}")
    print("R1: final map == counterfactual of 1a3ad76 in the 5: "
          + ", ".join(f"{s} {equal_cf[s]}" for s in ADJ))


def r3(swell_dir: Path, cfg14, cfg15) -> None:
    import track_io
    excl = core.excluded_ids() | EXCLUDED_SWELL
    ids = [p.stem for p in sorted(swell_dir.glob("*.txt")) if p.stem not in excl]
    assert len(ids) == 196, len(ids)
    groups = yaml.safe_load((LABELS / "swell_item30/groups_params11.yaml").read_text())
    r_group = set(groups["groups"]["R"]) & set(ids)
    predicted = r_group | {"19810854", "19861089"}
    changed, signal = set(), set()
    for tid in ids:
        s = track_io.read_track((swell_dir / f"{tid}.txt").read_bytes())
        r14 = core.run_series(s, *cfg14)
        if r14["signal"]:
            signal.add(tid)
        if r14["final"] != final_map(s, cfg15):
            changed.add(tid)
    # Counts only: the 5 validation tracks are inside these sets.
    print(f"R3: swell {len(ids)}; changed {len(changed)} | predicted {len(predicted)} "
          f"(R group in the 196: {len(r_group)}, + 2) | changed ∩ predicted "
          f"{len(changed & predicted)} | changed outside predicted "
          f"{len(changed - predicted)} | predicted unchanged {len(predicted - changed)}")
    extra = changed - predicted
    bad = set(groups["bad_marks"])
    print(f"R3: the {len(extra)} changed outside the prediction — with the signal "
          f"(boundary > peak, params-14) {len(extra & signal)}, without "
          f"{len(extra - signal)} | marked bad {len(extra & bad)}, not {len(extra - bad)}"
          f" | in a labelled batch {len(extra & set(core.split_sets()['batch_train']))}")


def evaluator(config: str) -> str:
    import evaluate_against_labels as ev
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert ev.main(["--config", str(LABELS / "configs" / f"cyclophaser_{config}.yaml"),
                        "--batch-train", lc.SWELL_BATCH]) == 0
    return buf.getvalue()


def blocks(text: str) -> dict[str, str]:
    """The evaluator's scored blocks by header line (config line dropped)."""
    out, cur = {}, None
    for ln in text.splitlines():
        if ln.startswith("  TRAIN") or ln.startswith("  BATCH") or ln.startswith("  ADJUDICATED"):
            cur = ln.split("(")[0].strip()
            out[cur] = ""
        elif ln.startswith("  TEST split held out"):
            cur = None
        elif cur:
            out[cur] += ln + "\n"
    return out


def figures(train, cfg14, cfg15, labels) -> None:
    snap = yaml.safe_load((LABELS / "swell_item30/labels_v1_snapshot.yaml").read_text())
    out = HERE / "figs_part3"
    out.mkdir(exist_ok=True)
    cases = []
    for sid in ADJ:
        orig = yaml.safe_load(snap["labels"][sid]["block"])[0]
        c = figs_cf.case(sid, train[sid], cfg15, cfg14, labels[sid], GROUP[sid])
        c["maps"] = {"original label": figs_cf.label_runs(orig),
                     "adjudicated label": figs_cf.label_runs(labels[sid]),
                     "params-14": c["maps"]["params-14"],
                     "params-15": c["maps"]["params-13"]}      # case() ran cfg15 there
        c["same_13_14"] = False
        cases.append(c)
        figs_cf.figure([c], out / f"{sid}.png")
    figs_cf.figure(cases, out / "board_5_adjudicated.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--swell", type=Path, required=True)
    a = ap.parse_args()
    print("cyclophaser.__file__ =", cyclophaser.__file__)
    print("layer_inspector.__file__ =", li.__file__)
    assert Path(cyclophaser.__file__).resolve().is_relative_to(core.REPO)
    assert Path(li.__file__).resolve().is_relative_to(core.REPO)
    print("environment:", core.environment())

    sets = core.split_sets()
    real = lc.load_real_series()
    synth, _ = lc.load_synthetic_series()
    batch = lc.load_batch_series()
    train = {k: v for k, v in {**real, **synth}.items() if k in sets["train"]}
    train |= {k: v for k, v in batch.items() if k in sets["batch_train"]}
    assert len(train) == 54 and set(train).isdisjoint(core.excluded_ids())
    val = set(lc.batch_membership(lc.VALIDATION_BATCH))
    assert len(val) == 5 and val.isdisjoint(train)
    cfg14, cfg15 = core.load_config("params-14"), core.load_config("params-15")
    assert cfg15[1] == {**cfg14[1], "incipient_plateau_spare_intensification": True}

    r1(train, cfg14, cfg15)
    r3(a.swell, cfg14, cfg15)

    e14, e15 = evaluator("params-14"), evaluator("params-15")
    (HERE / "part3_eval_params14.txt").write_text(e14)
    (HERE / "part3_eval_params15.txt").write_text(e15)
    b14, b15 = blocks(e14), blocks(e15)
    assert set(b14) == set(b15)
    for name in b14:
        print(f"R4/score block {name!r}: identical under params-14 and params-15 = "
              f"{b14[name] == b15[name]}")

    figures(train, cfg14, cfg15, core.train_labels())
    print("figures: figs_part3/ (5 adjudicated + board)")


if __name__ == "__main__":
    main()
