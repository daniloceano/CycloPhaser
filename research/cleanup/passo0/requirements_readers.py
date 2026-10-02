#!/usr/bin/env python
"""Decisão 10 — who reads the ROOT `requirements.txt`? (list only; nothing changes)

    python research/cleanup/passo0/requirements_readers.py

Read-only. For each consumer that could install from a requirements file — CI
(`.circleci/config.yml`), Read the Docs (`.readthedocs.yml`), packaging
(`setup.py`, `pyproject.toml`), the Streamlit app (`tools/calibration_app/`),
the conda environment (`environment.yml`) and the user docs (`docs/*.rst`,
`README.md`; `docs/future_work.md` is a register and is skipped) — every line mentioning `requirements` is classified by the file it
points at: the root `requirements.txt` (a bare `requirements.txt` in a command
or config, not prefixed by a directory), another requirements file, or prose.
Writes requirements_readers.json next to it.

What this cannot see: services configured outside the repository. The Streamlit
Community Cloud deployment reads a requirements file chosen by its own lookup
rule, not by anything in the tree; the app directory carries its own
`requirements.txt`, which is recorded here as a fact of the tree only.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
CONSUMERS = {
    "CI": [".circleci/config.yml"],
    "docs build (RTD)": [".readthedocs.yml", "docs/conf.py"],
    "setup / packaging": ["setup.py", "pyproject.toml", "MANIFEST.in"],
    "Streamlit app": ["tools/calibration_app/"],
    "conda env": ["environment.yml"],
    "user docs": ["docs/", "README.md"],
}
BARE = re.compile(r"(?<![\w./-])requirements\.txt")
OTHER = re.compile(r"[\w.-]+/requirements[\w-]*\.txt|requirements-[\w-]+\.txt")


def main():
    out = {}
    for group, paths in CONSUMERS.items():
        rows = []
        for p in paths:
            if not (ROOT / p).exists():
                rows.append(dict(where=p, kind="(arquivo ausente)"))
                continue
            res = subprocess.run(["git", "grep", "-n", "-I", "-e", "requirements", "HEAD", "--", p],
                                 cwd=ROOT, capture_output=True, text=True).stdout
            for line in res.splitlines():
                _, f, ln, text = line.split(":", 3)
                if f.endswith("requirements.txt") and f != "requirements.txt":
                    continue  # the other requirements files' own contents
                if f == "docs/future_work.md":
                    continue  # the historical register is not a consumer
                if text.lstrip().startswith("#") and f.endswith((".yml", ".yaml", ".py")):
                    kind = "comentário (cita, não instala)"
                elif BARE.search(text):
                    kind = "LÊ a raiz requirements.txt"
                elif OTHER.search(text):
                    kind = "outro arquivo: " + OTHER.search(text).group(0)
                else:
                    kind = "prosa (não aponta arquivo)"
                rows.append(dict(where=f"{f}:{ln}", kind=kind, text=text.strip()[:140]))
        out[group] = rows
    readers = sorted({(g, r["where"]) for g, rows in out.items() for r in rows
                      if r["kind"].startswith("LÊ")})
    summary = dict(root_file_exists=(ROOT / "requirements.txt").exists(),
                   readers=[f"{g}: {w}" for g, w in readers],
                   groups_reading_root={g: any(r["kind"].startswith("LÊ") for r in rows) for g, rows in out.items()},
                   app_has_own_requirements=(ROOT / "tools/calibration_app/requirements.txt").exists(),
                   detail=out)
    (ROOT / "research/cleanup/passo0/requirements_readers.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False))
    for g, v in summary["groups_reading_root"].items():
        print(f"{g:22s} reads root requirements.txt: {v}")
    for r in summary["readers"]:
        print("  ", r)


if __name__ == "__main__":
    main()
