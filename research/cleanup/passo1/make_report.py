#!/usr/bin/env python
"""Passo 1 — render research/cleanup/passo1/RELATORIO.md from this step's outputs.

    python research/cleanup/passo1/make_report.py

Every number below is read from a generated file in passo1/ (or passo0/ for the
manifest counts); nothing is typed. The prediction texts restate PREVISOES.md as
committed in d8a19cc, i.e. before any measurement of this step.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P0 = HERE.parent / "passo0"


def j(name, base=HERE):
    return json.loads((base / name).read_text())


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()


def digest(name):
    t = (HERE / name).read_text()
    return (re.search(r"SHA256\s*=\s*([0-9a-f]{64})", t).group(1),
            re.search(r"^HEAD: ([0-9a-f]{40})", t, re.M).group(1),
            re.search(r"n_series\s*=\s*(\d+)", t).group(1))


suite = (HERE / "suite_post_c1_raw.txt").read_text()
last = next(l for l in reversed(suite.splitlines()) if re.search(r"\d+ (passed|failed)", l))
cnt = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|deselected|errors?)", last)}
suite_head = re.search(r"^HEAD: ([0-9a-f]{40})", suite, re.M).group(1)
H = j("hygiene_train.json")["summary"]
R = j("refusal_mechanism.json")
T = j("params_track_vs_defaults.json")
F = j("params15_refs.json")
pre, pre_head, pre_n = digest("digest_pre_raw.txt")
post, post_head, post_n = digest("digest_post_raw.txt")
gate = (HERE / "gate_a.txt").read_text().splitlines()
i = gate.index("$ git log --format=%h origin/develop-v2.1..HEAD -- cyclophaser/")
k = next(n for n in range(i + 1, len(gate)) if gate[n].startswith("$"))
touching = [l.strip() for l in gate[i + 1:k] if l.strip()]
MS = j("manifest_summary.json", P0)
RQ = j("requirements_readers.json", P0)
C1 = git("log", "--format=%h", "-1", "--grep=^feat(C1)")

rows = [
    ("P1", "digest pré-C1 = `3a6de265…`; pós-C1 ≠ `3a6de265…`",
     f"pré `{pre[:8]}…` (HEAD `{pre_head[:7]}`, {pre_n} séries); pós `{post[:8]}…` (HEAD `{post_head[:7]}`)",
     pre.startswith("3a6de265") and not post.startswith("3a6de265")),
    ("P2", "sha256(params-track) = sha256(params-15 antes)",
     f"`{T['sha256_params15_before'][:12]}…` → `{T['sha256_params_track_after'][:12]}…`, bytes idênticos: {T['identical_bytes']}",
     T["identical_bytes"]),
    ("P3", "0 exceções; todas as sequências válidas",
     f"exceções default/edge {H['exceptions']['default']}/{H['exceptions']['edge']}; inválidas "
     f"{H['invalid_sequences']['default']}/{H['invalid_sequences']['edge']} (n={H['n_train']})",
     H["exceptions"]["default"] == 0 and H["invalid_sequences"]["default"] == 0),
    ("P4", "recusas de incipient sob reflect = 0",
     f"**{H['refusals']['default']}/{H['n_train']}** (edge: {H['refusals']['edge']}/{H['n_train']}, as mesmas séries)",
     H["refusals"]["default"] == 0),
    ("P5", "mapas que mudam entre default e edge > 0",
     f"{H['maps_changed']}/{H['n_train']} (sequências: {H['sequences_changed']})", H["maps_changed"] > 0),
    ("P6", "suíte pós-C1: 0 falhas",
     f"{cnt.get('passed', 0)} passed / {cnt.get('failed', 0)} failed (HEAD `{suite_head[:7]}`)",
     cnt.get("failed", 0) == 0 and "error" not in cnt and "errors" not in cnt),
]
L = ["# Passo 1 — relatório (gerado)\n",
     "Gerado por `passo1/make_report.py` a partir das saídas de `passo1/`. Previsões: `passo1/PREVISOES.md`, "
     "versionado em `d8a19cc` antes de qualquer medição deste passo.\n",
     "## Previsões\n", "| id | previsto | obtido | confere |", "|---|---|---|---|"]
L += [f"| {a} | {b} | {c} | {'sim' if ok else '**NÃO**'} |" for a, b, c, ok in rows]
g = R["grid"]
L += ["", "## Higiene (treino, sem pontuação)\n",
      f"`passo1/hygiene_train.md` (tabela por série) e `.json`. Séries: {H['n_train']} "
      f"({', '.join(f'{k}: {v}' for k, v in H['n_by_group'].items())}).\n",
      "| medida | default (reflect) | edge |", "|---|---|---|"]
for key in ("exceptions", "invalid_sequences", "refusals", "defect_I", "dz_t0_rel_zero"):
    L.append(f"| {key} | {H[key]['default']} | {H[key]['edge']} |")
L.append(f"| dz_t0_rel mediana / máx | {H['dz_t0_rel_median']['default']:.3f} / {H['dz_t0_rel_max']['default']:.3f} | "
         f"{H['dz_t0_rel_median']['edge']:.3f} / {H['dz_t0_rel_max']['edge']:.3f} |")
L += ["", f"Mapas que mudam: {H['maps_changed']}; sequências que mudam: {H['sequences_changed']}.\n",
      "**Por que P4 falhou (post-hoc, `refusal_mechanism.py`, declarado depois da medição):** o default "
      "`incipient_plateau_signal=\"vorticity\"` mede o platô na série BRUTA, onde o padding não chega. "
      "Recusas por sinal × padding: " + "; ".join(f"{k}: {v['n_refused']}/{R['n_train']}" for k, v in g.items()) + ".\n",
      "## Rastreabilidade\n",
      f"* Portão (a): commits que tocam `cyclophaser/` desde origin/develop-v2.1: {', '.join(f'`{t}`' for t in touching) or 'nenhum'} "
      f"(C1 = `{C1}`) — {'confere' if touching == [C1] else '**NÃO CONFERE**'}. Saída: `passo1/gate_a.txt`.",
      f"* params-15: vivas restantes **{len(F['live_remaining'])}**; históricas {F['hist_before']} em "
      f"`{F['before_ref']}` → {F['hist_head']} em HEAD, idênticas: {F['hist_identical']}; notas de correspondência: "
      f"{len(F['correspondence'])} (`passo1/params15_refs.json`).",
      f"* params-track × defaults: diferem só em "
      + ", ".join(f"`{d['group']}.{d['key']}` (yaml {d['yaml']!r}, default {d['default']!r})" for d in T["differing"])
      + "; chaves de detecção ausentes do YAML: "
      + ", ".join(f"`{m['key']}`" for m in T["signature_keys_absent_from_yaml"] if m["key"] not in ("plot", "plot_steps", "export_dict"))
      + ".",
      f"* Baselines do CI: `passo1/rebaseline_ci_raw.txt` (gerador `item31/regenerate_baselines_2b.py`).",
      f"* Manifesto: \"apagar\" {MS['branch_dest'].get('apagar', 0)} = {MS['apagar_ancestral']} ancestrais + "
      f"{MS['apagar_patch_equivalent_only']} só patch-equivalentes.",
      "* requirements.txt da raiz — quem lê: " + ("; ".join(RQ["readers"]) or "ninguém") + ".",
      f"* Suíte: linha final `{last.strip()}`, medida em `{suite_head[:7]}` (o C1). O commit seguinte só muda "
      "comentários, docstrings e textos de ajuda: `passo1/commit4_ast_check.txt` → "
      + (HERE / "commit4_ast_check.txt").read_text().strip().splitlines()[-1] + "."]
(HERE / "RELATORIO.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
