#!/usr/bin/env bash
# Release v2.1, part B, passo 1 — items 5 and 6 (read-only; nothing in the repo is changed).
#   SCRATCH=<dir outside the repo> bash research/release_v21/parteB_passo1/run_import_and_wheel.sh REV
# In a detached worktree of REV and a NEW python3.12 venv, the CI's own install steps
# (pip install --upgrade pip build; python -m build; pip install dist/*.whl;
# pip install pytest pyyaml), then:
#   item 6: wheel and sdist file lists (wheel_files.txt, sdist_files.txt) for the comparison;
#   item 5: the suite under several invocations; for each, cyclophaser.__file__ as seen
#           from INSIDE the session (cp_import_probe.py, via -p) and the junit counts.
# Built artefacts are removed from the worktree right after the build, so the worktree
# holds only the checkout while the suite runs. .github/ and every tracked file are untouched.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
REV="$(git rev-parse "$1")"
OUT="$ROOT/research/release_v21/parteB_passo1"
WT="$SCRATCH/pb1_wt"; VENV="$SCRATCH/pb1_venv"; PROBE="$SCRATCH/pb1_probe"
OUTSIDE="$SCRATCH/pb1_outside"; DIST="$SCRATCH/pb1_dist"; RAW="$SCRATCH/pb1_raw"
rm -rf "$WT" "$VENV" "$PROBE" "$OUTSIDE" "$DIST" "$RAW"
mkdir -p "$PROBE" "$OUTSIDE" "$DIST" "$RAW"
cp "$OUT/cp_import_probe.py" "$PROBE/"
git worktree add -q --detach "$WT" "$REV"
cd "$WT"
LOG="$OUT/05_06_run_raw.txt"
{
  echo "worktree HEAD: $(git rev-parse HEAD) | changed files: $(git status --porcelain | wc -l | tr -d ' ') | date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  /opt/homebrew/bin/python3.12 -m venv "$VENV"
  . "$VENV/bin/activate"
  echo "python: $(python --version 2>&1) | venv: new"
  pip install -q --upgrade pip build; echo "pip/build exit $?"
  python -m build --outdir "$DIST" > "$RAW/build.log" 2>&1; echo "build exit $?"; tail -1 "$RAW/build.log"
  rm -rf build ./*.egg-info
  echo "worktree after build: $(git status --porcelain --ignored | tr '\n' ' ')"
  pip install -q "$DIST"/*.whl; echo "wheel install exit $?"
  pip install -q pytest pyyaml; echo "pytest/pyyaml exit $?"
  echo "installed: $(pip list --format=freeze 2>/dev/null | tr '\n' ' ')"
  echo "playwright importable: $(python -c 'import playwright' 2>/dev/null && echo yes || echo no)"
  echo "wheel: $(basename "$DIST"/*.whl) sha256 $(shasum -a 256 "$DIST"/*.whl | cut -c1-16)…"
} > "$LOG" 2>&1

python3 - "$DIST" "$OUT" <<'PYEOF'
import sys, zipfile, tarfile, glob, os
dist, out = sys.argv[1:]
whl = glob.glob(os.path.join(dist, "*.whl"))[0]
sd = glob.glob(os.path.join(dist, "*.tar.gz"))[0]
with open(os.path.join(out, "06_wheel_files.txt"), "w") as fh:
    fh.write(f"# {os.path.basename(whl)}\n")
    for zi in sorted(zipfile.ZipFile(whl).infolist(), key=lambda z: z.filename):
        fh.write(f"{zi.file_size:>9}  {zi.filename}\n")
with open(os.path.join(out, "06_sdist_files.txt"), "w") as fh:
    fh.write(f"# {os.path.basename(sd)}\n")
    for m in sorted(tarfile.open(sd).getmembers(), key=lambda m: m.name):
        if m.isfile():
            fh.write(f"{m.size:>9}  {m.name}\n")
PYEOF

run() {  # label, dir, command...
  local label="$1" dir="$2"; shift 2
  {
    echo; echo "=== $label"; echo "cwd: $dir"; echo "\$ $*"
    ( cd "$dir" && CP_PROBE_OUT="$RAW/$label.json" PYTHONPATH="$PROBE" "$@" \
        -p cp_import_probe -p no:cacheprovider -q -rfE --junitxml="$RAW/$label.xml" ) \
        > "$RAW/$label.log" 2>&1
    echo "EXIT $?"
    grep -E "^CP_PROBE|^=+ .*(passed|failed|error|skipped).* =+$|^(FAILED|ERROR) " "$RAW/$label.log" | head -40
  } >> "$LOG"
}
. "$VENV/bin/activate"
run R0_ci_recipe            "$WT"      python -m pytest
run A1_bare_importlib       "$WT"      pytest --import-mode=importlib
run A2_bare_append          "$WT"      pytest --import-mode=append
run A3_outside_prepend      "$OUTSIDE" python -m pytest "$WT"
run A4_outside_P_importlib  "$OUTSIDE" python -P -m pytest --import-mode=importlib "$WT"
deactivate

python3 - "$RAW" "$OUT/05_import_summary.json" "$WT" "$VENV" <<'PYEOF'
import json, sys, os, collections, xml.etree.ElementTree as ET
raw, out, wt, venv = sys.argv[1:]
res = {}
for label in ["R0_ci_recipe", "A1_bare_importlib", "A2_bare_append",
              "A3_outside_prepend", "A4_outside_P_importlib"]:
    c = dict(passed=0, failed=0, skipped=0, failed_ids=[])
    xp = os.path.join(raw, label + ".xml")
    if os.path.exists(xp):
        for tc in ET.parse(xp).getroot().iter("testcase"):
            k = {x.tag for x in tc}
            if k & {"failure", "error"}:
                c["failed"] += 1; c["failed_ids"].append(f"{tc.get('classname')}::{tc.get('name')}")
            elif "skipped" in k:
                c["skipped"] += 1
            else:
                c["passed"] += 1
    c["failed_by_module"] = dict(collections.Counter(i.split("::")[0] for i in c["failed_ids"]))
    pj = os.path.join(raw, label + ".json")
    probe = json.load(open(pj)) if os.path.exists(pj) else None
    if probe:
        files = set()
        for stage in ("at_collection_end", "at_session_end"):
            files |= {os.path.dirname(f) for f in probe[stage]["modules"].values() if f}
        c["cyclophaser_file"] = probe["at_session_end"]["modules"].get("cyclophaser")
        c["all_cyclophaser_modules_dirs"] = sorted(files)
        c["dist_version"] = probe["at_session_end"]["dist_version"]
        c["sys_path_head"] = probe["at_session_end"]["sys_path_head"]
    res[label] = c
s = json.dumps(res, indent=1).replace(venv, "<venv>").replace(wt, "<wt>")
open(out, "w").write(s)
print(s)
PYEOF

cd "$ROOT"; git worktree remove --force "$WT"
sed -i '' -e "s#$VENV#<venv>#g; s#$WT#<wt>#g; s#$SCRATCH#<scratch>#g; s#$HOME#~#g" -e "s#/private/var/folders/[^ '\"]*#<tmp>#g" "$LOG"
