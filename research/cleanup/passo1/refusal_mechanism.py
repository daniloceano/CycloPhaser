#!/usr/bin/env python
"""Passo 1 — POST-HOC explanation of P4 (declared after P4 was measured; not a prediction).

    <cyclophaser env python> -P research/cleanup/passo1/refusal_mechanism.py

P4 predicted 0 incipient refusals on TRAIN under the new default (reflect); the
hygiene run measured 28/54, the same 28 as under edge. Hypothesis checked here:
the package default `incipient_plateau_signal="vorticity"` measures the plateau
on the RAW input (np.gradient of `z_unfil`), so `boundary_padding` cannot reach
the plateau probe; under `"derivative"` (the probe reads dz_dt_smoothed2, the
filtered curve) the padding would matter.

Same TRAIN population, loader and refusal definition as hygiene_train.py
(imported, not copied). Grid: incipient_plateau_signal in {vorticity,
derivative} x boundary_padding in {reflect, edge}; everything else at the
package defaults. No scoring against labels. Writes refusal_mechanism.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hygiene_train as H  # noqa: E402  (asserts env and cyclophaser.__file__ on import)


def main():
    series = H.train_series()
    grid = {}
    for signal in ("vorticity", "derivative"):
        for pad in ("reflect", "edge"):
            refused = []
            for sid, (_, s) in sorted(series.items()):
                r = H.run(s, dict(incipient_plateau_signal=signal, boundary_padding=pad))
                assert r["exception"] is None and r["valid"], (sid, signal, pad, r)
                if r["refused"]:
                    refused.append(sid)
            grid[f"{signal}/{pad}"] = dict(n_refused=len(refused), refused=refused)
            print(f"signal={signal:10s} padding={pad:8s} refusals {len(refused)}/{len(series)}")
    (HERE / "refusal_mechanism.json").write_text(json.dumps(dict(n_train=len(series), grid=grid), indent=1))


if __name__ == "__main__":
    main()
