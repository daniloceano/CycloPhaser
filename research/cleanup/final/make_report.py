#!/usr/bin/env python
"""Renders research/cleanup/RELATORIO_FINAL.md from the outputs of final/run_gate.sh
(read-only; every number is read from those files).

    python research/cleanup/final/make_report.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_DIGEST = "7552bc67"


def j(name):
    return json.loads((HERE / name).read_text())


def t(name):
    return (HERE / name).read_text()


def exit_code(name):
    return int(re.findall(r"^EXIT (\d+)", t(name), re.M)[-1])


def last_pytest_line(name):
    return [l for l in t(name).splitlines() if re.search(r"\d+ (passed|failed|errors?)\b", l) and re.search(r" in [\d.]+s", l)][-1].strip()


def pf(ok):
    return "**PASS**" if ok else "**FAIL**"


hdr = t("gate_header.txt").strip().splitlines()
rows = []

# (a)
a = j("gate_a.json")
others = [r for r in a["commits"] if "role" not in r]
ev = "; ".join(
    f"`{r['commit']}`: árvore sem docstrings pai→commit idêntica = {r['remeasured_parent_vs_commit']['identical']}, "
    f"só .py = {r['only_py']}; registrado: `{r['recorded']['tree_check']}` idêntica = {r['recorded']['tree_identical']}, "
    f"digest `{r['recorded']['digest_before']}…` → `{r['recorded']['digest_after']}…`" for r in others)
rows.append(("(a)", a["ok"],
             f"`git log -- cyclophaser/` desde develop-v2.1 (merge-base `{a['merge_base']}`): "
             f"{', '.join(f'`{c}`' for c in a['commits_listed'])}. C1 = `742e685`. {ev}. "
             f"HEAD × `742e685`, árvore sem docstrings: idêntica = {a['head_vs_c1']['identical']} "
             f"({a['head_vs_c1']['files']} arquivos). Saída: `final/gate_a.json`."))

# (b)
dig = re.search(r"SHA256\s*=\s*([0-9a-f]{64})", t("b_digest_raw.txt"))
dig = dig.group(1) if dig else None
s = j("b_summary.json")
suite_line = last_pytest_line("b_suite_raw.txt")
pinned_line = last_pytest_line("b_app_pinned_raw.txt")
pinned_env = next((l for l in t("b_app_pinned_raw.txt").splitlines() if l.startswith("python ")), "")
b_ok = (exit_code("b_suite_raw.txt") == 0 and s["suite"]["failed"] == 0 and s["app_dedicated"]["failed"] == 0 and s["app_pinned"]["failed"] == 0
        and dig is not None and dig.startswith(EXPECTED_DIGEST) and exit_code("b_digest_raw.txt") == 0)
rows.append(("(b)", b_ok,
             f"suíte (`-m \"not browser\"`, ambiente `cyclophaser`): {s['suite']['passed']} passed / "
             f"{s['suite']['failed']} failed, exit {exit_code('b_suite_raw.txt')} (linha final `{suite_line}`). Testes do app "
             f"({s['app_test_files']} arquivos, `final/b_app_tests.txt`): ambiente dedicado "
             f"{s['app_dedicated']['passed']} passed / {s['app_dedicated']['failed']} failed (da mesma rodada); "
             f"venv novo com `requirements-app.txt` ({pinned_env}): {s['app_pinned']['passed']} passed / "
             f"{s['app_pinned']['failed']} failed (`{pinned_line}`). Digest default, mesma sessão: "
             f"`{dig[:8] if dig else None}…` (esperado `{EXPECTED_DIGEST}…`)."))

# (c)
tt = j("c_tag_and_trace.json")
vc = j("c_verify_citations.json")
c_ok = not tt["R3"]["failures"] and not vc["failures"] and vc["citations_resolved"] == vc["citations_total"]
rows.append(("(c)", c_ok,
             f"S10 de `docs/findings.md`: {tt['R3']['rows']} linhas, {len(tt['R3']['failures'])} falhas "
             f"(`passo3/tag_and_trace.py`: arquivo na tag `archive/research-diagnostics-pre-cleanup` ou na árvore, "
             f"seção de destino existe, linha de `future_work.md` igual à citada). `verify_citations`: "
             f"{vc['citations_resolved']}/{vc['citations_total']} citações resolvidas, {len(vc['failures'])} falhas, "
             f"{vc['weak_citations']} fracas (listadas, não são falha)."))

# (d)
d = j("d_defaults.json")
rows.append(("(d)", d["divergences"] == 0,
             f"`passo4/check_documented_defaults.py`: {d['claims']} afirmações de default, "
             f"{d['divergences']} divergências (em `cyclophaser/`: {d['divergences_in_cyclophaser']}). "
             f"Saída: `final/d_defaults.md`."))

# (e)
e = j("e_d2.json")
rows.append(("(e)", e["unreviewed"] == 0 and e["attributing"] == 0,
             f"D2 refeito sobre a árvore medida (`final/d2_head.py`): {e['score_lines']} linhas sobre escore/medição; "
             f"{e['flagged']} sinalizadas; veredito mantido de `{e['ref_for_carried_verdicts']}` (arquivo, texto e "
             f"contexto de 5 linhas idênticos) {e['carried']}, revisadas nesta branch {e['reviewed_on_branch']}, "
             f"sem veredito {e['unreviewed']}; atribuem ao default atual escore medido sob `edge`: "
             f"**{e['attributing']}**. Lista: `final/e_d2.md`."))

# (f)
f = j("f_post_6b.json")
f_ok = f["deleted_equals_authorised"] and not f["new_remote_branches_since_6a"] and \
    f["remote_branches_now"] == ["chore/repo-cleanup", "develop-v2.1", "master"]
rows.append(("(f)", f_ok,
             f"`git ls-remote origin`: branches remotas {', '.join(f'`{b}`' for b in f['remote_branches_now'])}; "
             f"apagadas ({len(f['deleted_remote'])} de {f['remote_branches_before']}) = lista autorizada "
             f"(`passo6/removal_list.md` @ `fbeff00`): {f['deleted_equals_authorised']}; apagadas fora da lista: "
             f"{len(f['deleted_not_authorised'])}; autorizadas não apagadas: {len(f['authorised_not_deleted'])}. "
             f"Tags de arquivo no origin na ponta: {sum(r['ok'] for r in f['tags'])}/{len(f['tags'])}. "
             f"Commits citados: {f['distinct_cited_commits']}, inalcançáveis a partir do origin: "
             f"{f['unreachable_from_origin']}."))

notes = []
coll = re.findall(r"^_+ ERROR collecting (\S+) _+$", t("b_suite_raw.txt"), re.M)
if coll:
    notes.append(f"(b): the suite stopped at collection — `ERROR collecting {', '.join(coll)}` (`final/b_suite_raw.txt`): "
                 f"a research script named `test_*.py`, collected by pytest from the repository root, runs its "
                 f"module-level code with pytest's argv. No test ran, so the dedicated-env app tests count 0/0.")
for r in f["unreachable_rows"]:
    notes.append(f"(f), reachability (not part of the criterion): `{r['commit']}` is cited at `{r['first_citation']}` "
                 f"in the measured worktree; unreachable from all local refs: {f['unreachable_from_all_local_refs']}.")

md = ["# Clean-up front — final gate (generated by `final/make_report.py`)\n",
      "Measured once by `research/cleanup/final/run_gate.sh`, in a detached git worktree of "
      "`chore/repo-cleanup` (a clean copy, never the working tree). Outputs in `research/cleanup/final/`, "
      "machine paths masked.\n"]
md += [f"* {l}" for l in hdr]
md += ["", "| critério | resultado | evidência |", "|---|---|---|"]
md += [f"| {k} | {pf(ok)} | {ev.replace('|', chr(92) + '|')} |" for k, ok, ev in rows]
md += ["", f"**Portão: {'PASS' if all(ok for _, ok, _ in rows) else 'FAIL'}** "
       f"({sum(ok for _, ok, _ in rows)}/{len(rows)} critérios).", ""]
if notes:
    md += ["## Notas (lidas das saídas)", ""] + [f"* {n}" for n in notes] + [""]
(HERE.parent / "RELATORIO_FINAL.md").write_text("\n".join(md))
print("\n".join(md))
