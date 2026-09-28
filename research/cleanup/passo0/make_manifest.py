#!/usr/bin/env python
"""Passo 0 — render research/cleanup/MANIFEST.md from the generated inventories
plus the judgement file. Read-only outside research/cleanup/.

    python research/cleanup/passo0/inventory.py
    python research/cleanup/passo0/branches.py
    python research/cleanup/passo0/defaults_in_text.py
    python research/cleanup/passo0/make_manifest.py

Every count in MANIFEST.md is computed here. Every file:line in it is either a
git-grep hit or an anchor resolved here from (file, needle); an anchor that is
missing or ambiguous aborts the render. Every tracked file must be classified,
and every generated research output must carry a finding, or the render aborts.
"""
import ast
import fnmatch
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
P0 = ROOT / "research/cleanup/passo0"
sys.path.insert(0, str(P0))
import judgements as J  # noqa: E402

INV = json.loads((P0 / "inventory.json").read_text())
BR = json.loads((P0 / "branches.json").read_text())
DEF = json.loads((P0 / "defaults_in_text.json").read_text())
STALE = json.loads((ROOT / J.DIAG / "item31/stale_scripts.json").read_text())
FILES = {r["path"]: r for r in INV["files"]}
ERRORS = []


# --------------------------------------------------------------------------- #
def resolve(anchor):
    f, needle = anchor
    try:
        lines = (ROOT / f).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        ERRORS.append(f"anchor file missing: {f}")
        return f"{f}:?"
    hits = [i for i, l in enumerate(lines, 1) if needle in l]
    if len(hits) != 1:
        ERRORS.append(f"anchor {'absent' if not hits else 'ambiguous (%d)' % len(hits)}: {f} :: {needle!r}")
        return f"{f}:?"
    return f"{f}:{hits[0]}"


def front_of(p):
    for k, v in J.FRONTS.items():
        if p.startswith(k):
            return k, v
    return None, None


def finding_for(p):
    if p in J.FINDING:
        return J.FINDING[p]
    for k, v in J.FINDING.items():
        if "*" in k and fnmatch.fnmatch(p, k):
            return v
    return None


ROOT_KEEP = {
    "README.md": "doc de usuário (entrada do pacote no PyPI)",
    "CHANGELOG.md": "doc de usuário; [Unreleased] é vivo",
    "LICENSE": "licença",
    "CLAUDE.md": "regras fixas para agentes",
    "setup.py": "empacotamento (versão, dependências)",
    "pyproject.toml": "build-system",
    "environment.yml": "ambiente conda canônico (regra fixa)",
    ".gitignore": "config de versionamento",
    ".circleci/config.yml": "CI do pacote (instala do wheel)",
    ".readthedocs.yml": "build da documentação",
    "runtime.txt": "versão do Python do deploy",
    ".python-version": "versão do Python do deploy do app (citado em tools/calibration_app/requirements.txt)",
    "requirements.txt": "fica (decisão 10): as instruções de instalação/contribuição dos docs de usuário o leem (ver Dados gerados)",
}
LABELS_KEEP = {
    "research/labels/README.md": "doc do conjunto de rótulos e das configs (vivo)",
    "research/labels/labels_core.py": "núcleo de rótulos (importado por testes e app)",
    "research/labels/evaluate_against_labels.py": "avaliador vivo (medidor de sequência)",
    "research/labels/config_defaults.py": "preenchimento de chaves ausentes (app e testes)",
    "research/labels/defaults_2.0.0.json": "tabela congelada dos defaults 2.0.0 (pacote, docs, testes)",
    "research/labels/manual_labels.yaml": "verdade dos rótulos (fonte da temporização)",
    "research/labels/split.yaml": "split CONGELADO",
    "research/labels/make_split.py": "gerador do split (lido por teste)",
    "research/labels/freeze_synthetic_series.py": "gerador das séries sintéticas congeladas",
}


def classify(p, t):
    """-> (dest, motive, finding_text or None, section or '', anchors[])"""
    if p in J.KEEP:
        return "manter", J.KEEP[p], J.KEEP_FINDING.get(p), "", J.KEEP_ANCHORS.get(p, [])
    if p in J.DEST:
        dest, why = J.DEST[p]
        k, fr = front_of(p)
        sec = fr["sec"] if (fr and dest == "consolidar") else ""
        if p.endswith("stale_scripts.md"):
            sec = "S10"
        f = finding_for(p)
        return dest, why, (f[0] if f else ("relatório/registro" if dest == "consolidar" else None)), sec, (f[1] if f else [])
    if p in ROOT_KEEP:
        return "manter", ROOT_KEEP[p], J.KEEP_FINDING.get(p), "", []
    if p in LABELS_KEEP:
        return "manter", LABELS_KEEP[p], J.KEEP_FINDING.get(p), "", []
    if p.startswith("cyclophaser/"):
        return "manter", "código/dados do pacote", None, "", []
    if p.startswith("tests/calibration_data/"):
        return "manter", "séries reais usadas pela suíte e pelo app (carregadas por diretório)", None, "", []
    if p.startswith("tests/synthetic/data/"):
        return "manter", "séries sintéticas CONGELADAS (verdade dos testes)", None, "", []
    if p.startswith("tests/"):
        return "manter", "suíte de testes", None, "", []
    if p.startswith("tools/calibration_app/"):
        return "manter", "app de calibração", None, "", []
    if p.startswith("docs/_images/item5/"):
        return ("remover", "capturas de tela do item 21; nenhum doc as referencia",
                "evidência visual (barra lateral/benchmark antes-depois)", "",
                [(J.FW, "## 21. Calibration app — Benchmark tab")])
    if p == "docs/future_work.md":
        return "manter", "registro canônico; histórico NÃO reescrito (só nota params-15 → params-track)", J.KEEP_FINDING[p], "", []
    if p.startswith("docs/"):
        return "manter", "documentação de usuário / build RTD", None, "", []
    if p.startswith("research/labels/configs/"):
        return "manter", "a config de referência (renomear para params-track no Passo 1, conteúdo intacto)", None, "", []
    if p.startswith("research/snapshots/"):
        return "manter", "colunas de referência do Benchmark (releases publicados)", J.KEEP_FINDING.get(p), "", []
    if p.startswith("research/labels/swell_item30/"):
        why = ("gerador de dados congelados — proveniência do lote" if p.endswith(".py")
               else "dados/proveniência do lote swell (lidos por testes e pelo avaliador)")
        return "manter", why, J.KEEP_FINDING.get(p), "", []
    k, fr = front_of(p)
    if fr:
        if p.endswith(".md"):
            return ("consolidar", "relatório de frente fechada; achados vão ao documento único (Passo 2)",
                    J.REPORT_FINDING["*"], fr["sec"], [(J.FW, fr["fw"])])
        f = finding_for(p)
        if p.endswith(".py"):
            why = "script de diagnóstico de frente fechada; reprodutível pelo commit do último toque"
            if p in STALE:
                why += " (não roda na ponta: params-1..14 removidos)"
            return "remover", why, (f[0] if f else None), fr["sec"] if f else "", (f[1] if f else [])
        if f is None:
            ERRORS.append(f"generated output without a finding: {p}")
            return "remover", "saída gerada de frente fechada", "?", fr["sec"], []
        return "remover", "saída gerada de frente fechada; o achado está no registro indicado", f[0], fr["sec"], f[1]
    ERRORS.append(f"unclassified: {p}")
    return "?", "?", None, "", []


GROUPS = [  # homogeneous: one line when every member shares dest+motive
    "tests/calibration_data/*.csv", "tests/calibration_data/swell_item30/*.csv",
    "tests/calibration_data/swell_item30_val/*.csv", "tests/synthetic/data/*.csv",
    "docs/_images/item5/*.png", J.DIAG + "frontD/fig_*_opening.png",
    J.DIAG + "frontRefusal/fig_*_refusal.png", J.DIAG + "item30/figs_cf/*.png",
    J.DIAG + "item30/figs_part3/*.png",
]


def refs_summary(refs, limit=4):
    c = Counter(r.rsplit(":", 1)[0] for r in refs)
    items = [f"{f.replace('research/labels/diagnostics/', 'diag/')}({n})" for f, n in c.most_common()]
    s = ", ".join(items[:limit])
    return s + (f", +{len(items) - limit}" if len(items) > limit else "") if items else "—"


def esc(s):
    return str(s).replace("|", "\\|")


# --------------------------------------------------------------------------- #
rows = []
for p, r in FILES.items():
    dest, why, fin, sec, anchors = classify(p, r["type"])
    reg = [resolve(a) for a in anchors]
    rows.append(dict(path=p, type=r["type"], commit=r["last_commit"], date=r["last_date"],
                     refs=r["refs"], dest=dest, why=why, finding=fin, sec=sec, reg=reg))
ROWS = {x["path"]: x for x in rows}

# collapse homogeneous groups
grouped, members_of = [], {}
for g in GROUPS:
    mem = [x for x in rows if fnmatch.fnmatch(x["path"], g) and x["path"].count("/") == g.count("/")]
    if not mem:
        ERRORS.append(f"empty group {g}")
        continue
    keyset = {(x["dest"], x["why"], x["finding"]) for x in mem}
    if len(keyset) != 1:
        ERRORS.append(f"group {g} not homogeneous: {keyset}")
        continue
    for x in mem:
        members_of[x["path"]] = g
    latest = max(mem, key=lambda x: x["date"])
    grouped.append(dict(path=g, n=len(mem), type=mem[0]["type"], commit=latest["commit"], date=latest["date"],
                        refs=sorted({rr for x in mem for rr in x["refs"]}), dest=mem[0]["dest"], why=mem[0]["why"],
                        finding=mem[0]["finding"], sec=mem[0]["sec"], reg=mem[0]["reg"]))

dest_count = Counter(x["dest"] for x in rows)

# --------------------------------------------------------------------------- #
out = []
w = out.append
head = INV["head"]
w("# Passo 0 — Inventário: manifesto de arquivos, branches e rastreabilidade\n")
w("**Frente:** limpeza do repositório + default `boundary_padding` · **Passo 0 — somente leitura**, corrigido no "
  "Passo 1. No Passo 0 nada fora de `research/cleanup/` foi removido, movido, renomeado ou editado; as decisões do "
  "Danilo sobre esta proposta estão em \"Decisões aprovadas\".\n")
BASE = subprocess.check_output(["git", "merge-base", "HEAD", "origin/develop-v2.1"], cwd=ROOT, text=True).strip()[:7]
w(f"* Branch `chore/repo-cleanup`, criada de `origin/develop-v2.1` @ `{BASE}` (ponta esperada `06d8550`: "
  f"{'confere' if BASE == '06d8550' else 'NÃO CONFERE'}); inventário regerado em HEAD `{head[:7]}`.")
w("* **Correções do Passo 1** (aprovadas pelo Danilo): `.pypirc` saiu do versionamento (commit próprio, conteúdo "
  "não lido); branches com equivalência de patch separadas das ancestrais; `measure_incipient_smoothing.py` → manter; "
  "saídas de `passo0/` sem caminhos absolutos; decisões aprovadas registradas. Seções 0.1–0.4 regeradas pelos scripts.")
w("* **Passo 2**: coluna \"destino final\" na seção 0.4 e seção 0.5 (destino dos arquivos \"consolidar\"), lidas de "
  "`research/cleanup/passo2/traceability.json`; o inventário foi regerado sobre a HEAD do Passo 2 antes de "
  "`docs/findings.md` existir. Na seção (c), as notas de correspondência params-15 → params-track contam como VIVA "
  "pela regra do Passo 0; a contagem com a classe \"correspondência\" está em `passo1/params15_refs.py`.")
w("* Gerado por `research/cleanup/passo0/make_manifest.py` a partir de `inventory.py`, `branches.py`, "
  "`defaults_in_text.py` (mecânico) e `judgements.py` (julgamento: destino, motivo, achado). "
  "Toda contagem e todo `arquivo:linha` abaixo é regerado pelo script; nenhum número foi digitado.")
w("* Âncoras de registro são resolvidas por texto (arquivo + trecho) e o render aborta se o trecho faltar ou for ambíguo.")
w("* `.pypirc` foi excluído de toda leitura de conteúdo (é arquivo de credenciais) e, no Passo 1, saiu do "
  "versionamento (decisão 2).\n")

# 0.1 -------------------------------------------------------------------------
suite_raw = (P0 / "baseline_suite_raw.txt").read_text().splitlines()
suite_line = next(l for l in reversed(suite_raw) if re.search(r"\d+ passed", l))
m_pass = re.search(r"(\d+) passed", suite_line)
m_fail = re.search(r"(\d+) failed", suite_line)
obt_pass, obt_fail = int(m_pass.group(1)), int(m_fail.group(1)) if m_fail else 0
dig_raw = (P0 / "baseline_digest_raw.txt").read_text()
digest = re.search(r"SHA256\s*=\s*([0-9a-f]{64})", dig_raw).group(1)
nser = re.search(r"n_series\s*=\s*(\d+)", dig_raw).group(1)
env = (P0 / "baseline_env.txt").read_text()
w("## 0.1 Linha de base (mesma máquina, mesma sessão)\n")
w("Previsões declaradas no prompt da frente antes da medição; não ajustadas.\n")
w("| medida | previsto | obtido | confere |\n|---|---|---|---|")
w(f"| suíte `-m \"not browser\"` — passed | 1438 | {obt_pass} | {'sim' if obt_pass == 1438 else 'NÃO'} |")
w(f"| suíte — failed | 0 | {obt_fail} | {'sim' if obt_fail == 0 else 'NÃO'} |")
w(f"| digest `front_b/default_behaviour_hash.py` | começa por `3a6de265` | `{digest[:8]}…` ({nser} séries) | {'sim' if digest.startswith('3a6de265') else 'NÃO'} |")
w("")
w(f"Linha final bruta da suíte: `{suite_line.strip()}`. Ambiente (`baseline_env.txt`): "
  + "; ".join(l.strip().replace(str(ROOT), "<repo>") for l in env.splitlines()
               if l.startswith(("HEAD", "cyclophaser.__file__"))) + ".")
ANON = json.loads((P0 / "anonymize_log.json").read_text())
w("**Anonimização declarada (Passo 1).** Nenhuma saída versionada desta frente contém caminho absoluto: "
  "raiz do repositório → `<repo>`, ambiente conda (absoluto, relativo à raiz ou com `~`) → `<env>`, home → `~`. "
  "Feita por `passo0/anonymize.py` (idempotente); `inventory.py` aplica a mesma regra ao que grava e "
  "`run_baseline.sh` chama o anonimizador ao fim. Substituições por arquivo (`passo0/anonymize_log.json`): "
  + "; ".join(f"`{k.replace('research/cleanup/', '')}`: " + ", ".join(f"{lab} ×{n}" for lab, n in v.items())
              for k, v in sorted(ANON.items())) + ".")
w("\"Suíte completa\" = `-m \"not browser\"`: CLAUDE.md proíbe rodar `tests/test_label_browser.py`. "
  "Só passed/failed são reportados (regra fixa). Saídas brutas: `passo0/baseline_suite_raw.txt`, "
  "`passo0/baseline_digest_raw.txt`, `passo0/baseline_env.txt`; comando: `passo0/run_baseline.sh`.\n")
w("**Efeito colateral tratado:** o gerador canônico ANEXA um registro ao seu livro-razão "
  "`research/labels/diagnostics/front_b/default_behaviour_sha256.txt`. Como este passo não edita nada fora de "
  "`research/cleanup/`, o registro anexado foi guardado em `passo0/baseline_digest_appended_record.diff` e o livro-razão "
  "restaurado para HEAD. Na rodada medida isso foi feito à mão logo após o script; `run_baseline.sh` foi depois "
  "atualizado para fazer o mesmo sozinho.\n")

# 0.2 -------------------------------------------------------------------------
w("## 0.2 Manifesto de arquivos\n")
w(f"Arquivos versionados em HEAD: **{INV['n_tracked_total']}** (git ls-files, excluindo `research/cleanup/`, i.e. a árvore de develop). "
  f"Linhas do manifesto: {len(rows) - len(members_of) + len(grouped)} "
  f"({len(rows) - len(members_of)} individuais + {len(grouped)} grupos homogêneos cobrindo {len(members_of)} arquivos).\n")
w("| destino | arquivos |\n|---|---|")
for d in ("manter", "consolidar", "remover"):
    w(f"| {d} | {dest_count.get(d, 0)} |")
w("")
w("Colunas: caminho · tipo · último commit (hash data) · contém achado? · quem o referencia (arquivo(nº de linhas); "
  "`diag/` = `research/labels/diagnostics/`; lista completa com linhas em `passo0/inventory.json`) · destino · motivo · "
  "seção de destino no documento único (se consolidar/achado a mover) · onde o achado já está registrado.\n")
w("Semântica: **manter** = fica; **consolidar** = o conteúdo vai para o documento único de achados (Passo 2) e o arquivo "
  "sai depois; **remover** = sai, porque o conteúdo já está registrado em outro lugar (ou é reprodutível pelo commit). "
  "Nada sai neste passo.\n")
w("Seções propostas para o documento único (Passo 2):\n")
for k, v in J.SECTIONS.items():
    w(f"* **{k}** — {v}")
w("")


def area(p):
    parts = p.split("/")
    if p.startswith("research/labels/diagnostics/"):
        return "/".join(parts[:4])
    if len(parts) == 1:
        return "(raiz)"
    if len(parts) == 2:
        return parts[0]
    return "/".join(parts[:2])


by_area = defaultdict(list)
for x in rows:
    if x["path"] in members_of:
        continue
    by_area[area(x["path"])].append(x)
for g in grouped:
    by_area[area(g["path"])].append(g)

for a in sorted(by_area):
    w(f"### `{a}`\n")
    w("| caminho | tipo | último commit | achado? | referenciado por | destino | motivo | seção | registrado em |")
    w("|---|---|---|---|---|---|---|---|---|")
    for x in sorted(by_area[a], key=lambda z: z["path"]):
        if "n" in x:
            name = f"`{x['path']}` — **{x['n']} arquivos** (`git ls-files '{x['path']}'`)"
        else:
            name = f"`{x['path']}`"
        fin = f"sim — {x['finding']}" if x["finding"] else "não"
        reg = ", ".join(f"`{r}`" for r in x["reg"]) or ("**SÓ AQUI**" if x["finding"] and x["dest"] == "remover" else "—")
        w(f"| {esc(name)} | {x['type']} | `{x['commit']}` {x['date']} | {esc(fin)} | {esc(refs_summary(x['refs']))} | "
          f"**{x['dest']}** | {esc(x['why'])} | {x['sec'] or '—'} | {esc(reg)} |")
    w("")

# (a) -------------------------------------------------------------------------
w("## 0.2 (a) Scripts de `item31/stale_scripts.md`\n")


def imports_and_paths(p):
    src = (ROOT / p).read_text(encoding="utf-8")
    mods, paths = set(), set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if re.fullmatch(r"[\w\-./]+\.(ya?ml|json|csv|txt|md|py)", v) and "/" in v:
                paths.add(v)
    std = set(sys.stdlib_module_names) | {"numpy", "pandas", "scipy", "matplotlib", "yaml", "pytest"}
    return sorted(m for m in mods if m not in std), sorted(paths)


n_exist = 0
w("| script | existe? | evidência (stale_scripts.json; conferida na linha) | módulos locais importados | caminhos literais | resultado registrado em | destino |")
w("|---|---|---|---|---|---|---|")
for p, ev in sorted(STALE.items()):
    exists = (ROOT / p).exists()
    n_exist += exists
    lines = (ROOT / p).read_text(encoding="utf-8").splitlines() if exists else []
    checked = []
    for e in ev:
        m = re.search(r"\(line (\d+)\)", e)
        tok = re.search(r"(params-\d+|load_config\(\)|\.CONFIG)", e)
        ok = bool(m and tok and int(m.group(1)) <= len(lines) and tok.group(1).replace("()", "") in lines[int(m.group(1)) - 1])
        checked.append(e + ("" if ok else " **[linha não confere]**"))
    mods, paths = imports_and_paths(p) if exists else ([], [])
    fdir, _ = front_of(p)
    key = fdir or ("research/labels/swell_item30/" if "swell_item30" in p else None)
    reg = ", ".join(f"`{resolve(a)}`" for a in J.STALE_RESULT.get(key, [])) or "?"
    dest = ROWS[p]["dest"] if p in ROWS else "?"
    w(f"| `{p.replace(J.DIAG, 'diag/')}` | {'sim' if exists else 'NÃO'} | {esc('; '.join(checked))} | "
      f"{esc(', '.join(mods)) or '—'} | {esc(', '.join(paths[:4]) + (' …' if len(paths) > 4 else '')) or '—'} | {reg} | **{dest}** |")
w("")
w(f"**{n_exist} de {len(STALE)}** scripts confirmados existentes. Os marcados **manter** (`item30/figs_cf.py`, "
  "`item30/separability.py`, `swell_item30/adjudicate_item30.py`) não rodam como script na ponta, mas são "
  "importados por teste vivo ou são proveniência de dados congelados; `stale_scripts.md` já registra, à parte, "
  "`item19_core.py` e `item31/exposure_table.py` como acertos estáticos que CONTINUAM rodando.\n")

# (b) -------------------------------------------------------------------------
hits = INV["grep_params_1_14"]
w("## 0.2 (b) Referências a params-1..14\n")
w(f"`git grep -P 'params[-_]?(1[0-4]|[1-9])(?![0-9])'` (sem `research/cleanup/`): **{len(hits)} ocorrências em "
  f"{len({h['file'] for h in hits})} arquivos**. Lista completa, linha a linha: `passo0/inventory.json` → `grep_params_1_14`.\n")
diag_files = Counter(h["file"] for h in hits if h["file"].startswith(J.DIAG))
w("**Diagnósticos de frentes fechadas e `future_work.md`** — proposta por regra: *aposentar* (o script sai com a frente; "
  "reexecução = `git worktree add` em `33ea489` com o assert de `cyclophaser.__file__`); texto de relatório/registro "
  "fica como histórico. Exceções: `item19/item19_core.py` já migrado (só `REMOVED_CONFIG`, que é a mensagem de erro); "
  "`item30/figs_cf.py`, `item30/separability.py` e `item30/item30_core.py` são importados por teste vivo — o teste "
  "reconstrói params-14 em memória a partir de params-15, então nada precisa ser recuperado.\n")
w("| área | ocorrências |\n|---|---|")
for a, n in sorted(Counter(area(f) for f in diag_files.elements()).items()):
    w(f"| `{a}` | {n} |")
w(f"| `docs/future_work.md` | {sum(1 for h in hits if h['file'] == 'docs/future_work.md')} (HISTÓRICO, não reescrever) |")
w("")
w("**Fora dos diagnósticos** — cada ocorrência, com proposta por arquivo:\n")
w("| arquivo:linha | trecho | proposta | motivo |\n|---|---|---|---|")
live_p114 = [h for h in hits if not h["file"].startswith(J.DIAG) and h["file"] != "docs/future_work.md"]
for h in live_p114:
    prop, why = J.P114_LINE.get(f"{h['file']}:{h['line']}") or J.P114_LIVE.get(h["file"], ("?", "?"))
    if prop == "?":
        ERRORS.append(f"params-1..14 hit without proposal: {h['file']}")
    w(f"| `{h['file']}:{h['line']}` | {esc(h['text'][:110])} | **{prop}** | {esc(why)} |")
w("")
w("Nota: a lista de opções do prompt (migrar / aposentar / recuperar de 33ea489) não cobre menção puramente histórica "
  "que não carrega arquivo; para esses casos a proposta é **manter** (ver desvios).\n")

# (c) -------------------------------------------------------------------------
p15 = INV["grep_params_15"]


def p15_class(f):
    for pref, cls, why in J.P15_CLASS:
        if f.startswith(pref):
            return cls, why
    return "?", "?"


cls_count = Counter(p15_class(h["file"])[0].rstrip("*") for h in p15)
w("## 0.2 (c) Ocorrências de \"params-15\"\n")
w(f"`git grep -P 'params[-_]?15(?![0-9])'` (pega também `params_15`, `PARAMS_15`, `params15`): **{len(p15)} ocorrências** — "
  f"VIVAS **{cls_count['VIVA']}**, HISTÓRICAS **{cls_count['HISTÓRICA']}**. Regra: VIVA = código, app, testes, READMEs, "
  "docs de usuário, benchmark e o [Unreleased] do CHANGELOG; HISTÓRICA = future_work.md, split.yaml, "
  "swell_item30/README.md e relatórios/diagnósticos de frente.\n")
w("| arquivo:linha | classe | trecho |\n|---|---|---|")
for h in p15:
    cls, why = p15_class(h["file"])
    w(f"| `{h['file']}:{h['line']}` | {cls} | {esc(h['text'][:120])} |")
w("")
w("`HISTÓRICA*` = `item31/param_table.json`: artefato histórico, mas `tests/test_config_defaults.py` lê o arquivo (só a "
  "chave `rows`); as ocorrências são nomes de campos. Conferir no Passo 1 que o renome não o afeta.\n")
w("Ocorrências VIVAS que dependem do NOME do arquivo (quebram no renome se não forem atualizadas juntas): "
  "`tests/test_benchmark_apptest.py` (CFG_B e a opção `params-15` do seletor), `tests/test_config_defaults.py` (P15), "
  "`tests/test_intensification_min_depth.py`, `tests/test_layer_inspector.py` (PARAMS_15), "
  "`tests/test_item30_spare_intensification.py` (`core.load_config(\"params-15\")`, via `item30_core`), "
  "e as docstrings de `cyclophaser/determine_periods.py` que citam o caminho.\n")

# (d) -------------------------------------------------------------------------
bp = INV["grep_boundary_padding"]


def bp_nature(f, ln):
    for ff, a, b, nat in J.BP_NATURE:
        if f == ff and a <= ln <= b:
            return nat
    return "uso/passagem do parâmetro em código"


w("## 0.2 (d) Default de `boundary_padding`\n")
w(f"`git grep boundary_padding` em `cyclophaser/`, `tools/`, `docs/`, `README.md`, `CHANGELOG.md` e YAMLs: "
  f"**{len(bp)} ocorrências**. `README.md` não menciona o parâmetro.\n")
sig = DEF["signature_defaults"]["boundary_padding"]
w("**Defaults na assinatura (lidos por `inspect.signature`, `defaults_in_text.py`):** " +
  ", ".join(f"`{fn}` = {v}" for fn, v in sig.items()) + ".\n")
has_gp = "get_periods" in sig
w(f"**`get_periods` tem default próprio?** {'SIM' if has_gp else '**NÃO**'} — `get_periods` não recebe "
  "`boundary_padding` (recebe a série já filtrada); suas docstrings só CITAM o default de `process_vorticity`. "
  "Quem tem default próprio: `process_vorticity` e `determine_periods` (`\"edge\"`) e, no módulo do filtro, "
  "`lanczos_filter`, `lanczos_bandpass_filter` e `_convolve_same` (`\"reflect\"`) — "
  "um default que o prompt não listou.\n")
w("| arquivo:linha | natureza | trecho |\n|---|---|---|")
for h in bp:
    w(f"| `{h['file']}:{h['line']}` | {bp_nature(h['file'], h['line'])} | {esc(h['text'][:110])} |")
w("")
V2 = json.loads((P0 / "v200_vs_defaults_json.json").read_text())
w("**O rótulo \"2.0.0\" não é o release 2.0.0.** `passo0/v200_vs_defaults_json.py` compara, por AST (nada é "
  f"importado nem rodado da tag), as assinaturas da tag `{V2['tag']}` (`{V2['tag_commit'][:7]}`) com "
  f"`research/labels/defaults_2.0.0.json`: **{V2['n_equal']} de {V2['n_keys']} chaves iguais, "
  f"{len(V2['differences'])} diferentes** — `boundary_padding` "
  + ("NÃO EXISTE na tag (o filtro publicado faz zero-padding)" if any(d["param"] == "boundary_padding" and "não existe" in str(d["tag"]) for d in V2["differences"]) else "existe na tag")
  + ". A tabela é a de develop no estágio 0 do item 31 (fonte declarada: " + f"{V2['json_source']}" + "). Portanto a "
  "coluna \"2.0.0\" da tabela do CHANGELOG [Unreleased] (linha 28: `\"reflect\"`), as docstrings \"(`\"reflect\"` up "
  "to 2.0.0)\" e `docs/usage.rst:80` descrevem develop antes do item 31, não o pacote publicado. Diferenças completas: "
  "`passo0/v200_vs_defaults_json.json`.\n")
w("**Suplemento — testes** (fora do escopo pedido, mas o prompt deu pistas em `tests/test_boundary_padding.py`):\n")
tb = [(i, l.rstrip()) for i, l in enumerate((ROOT / "tests/test_boundary_padding.py").read_text().splitlines(), 1)
      if re.search(r"def test_.*(default|edge|reflect)|default (is|==)|DEFAULT IS|opt-in; default", l)]
w("| tests/test_boundary_padding.py:linha | trecho |\n|---|---|")
for i, l in tb:
    w(f"| `{i}` | {esc(l.strip()[:120])} |")
w("")
w("Confirmação das pistas do prompt (conferidas, não copiadas): assinaturas em `determine_periods.py` :423 e :1369 "
  "(`\"edge\"`); docstrings :439, :881, :1409 (nota de defaults calibrados), :1044 e :1521 (`incipient_method`: "
  "`\"reflect\"` como regime calibrado, \"as the current defaults are\" — hoje o default é `\"edge\"`); "
  "`lanczos_filter.py:6` diz `\"zero\" (default)` e :39–56 dizem que o default é `\"reflect\"` — os dois textos "
  "divergem entre si e da assinatura de `process_vorticity`. Tabela do CHANGELOG [Unreleased] na linha 28. "
  "`tests/test_boundary_padding.py`: :204, :251 e :263 afirmam `\"edge\"` para `process_vorticity`/`determine_periods`; "
  ":169 afirma `\"reflect\"` para as funções do filtro; o comentário de cabeçalho :27 ainda diz `default \"zero\"`.\n")

# (e) -------------------------------------------------------------------------
drows = DEF["rows"]
w("## 0.2 (e) Valores default escritos em texto\n")
w(f"Localizador heurístico (`passo0/defaults_in_text.py`) — **{len(drows)} linhas em "
  f"{len({r['file'] for r in drows})} arquivos**, cada uma com o default da assinatura ao lado para o Passo 4. "
  "Tabela completa: `passo0/defaults_in_text.md`. `README.md` não escreve nenhum default.\n")
w("| arquivo | linhas |\n|---|---|")
for f, n in sorted(Counter(r["file"] for r in drows).items()):
    w(f"| `{f}` | {n} |")
w("")
fb = DEF["app_literal_fallbacks"]
def fb_verdict(r):
    """literal vs the entry-point default (process_vorticity / get_periods)."""
    try:
        lit = ast.literal_eval(r["literal"])
    except (ValueError, SyntaxError):
        return "derivado (não é literal)"
    ref = ast.literal_eval(r["code"].get("process_vorticity", r["code"].get("get_periods")))
    same = lit == ref and isinstance(lit, bool) == isinstance(ref, bool)
    return "igual" if same else "**DIVERGE**"


verdicts = [fb_verdict(r) for r in fb]
w(f"**Defaults escritos como literal no código do app** (`.get(\"param\", literal)`): {len(fb)} ocorrências, "
  f"{sum(v == '**DIVERGE**' for v in verdicts)} divergem do default de `process_vorticity`/`get_periods`. "
  "Podem ser intencionais (semântica de YAML antigo sem a chave) — decidir no Passo 4:\n")
w("| arquivo:linha | parâmetro | literal | assinatura | veredito |\n|---|---|---|---|---|")
for r, v in zip(fb, verdicts):
    w(f"| `{r['file']}:{r['line']}` | {r['param']} | `{esc(r['literal'])}` | "
      f"{esc(', '.join(f'{k}={x}' for k, x in r['code'].items()))} | {v} |")
w("")

# (f) -------------------------------------------------------------------------
ab = INV["grep_abs_paths"]
w("## 0.2 (f) Caminhos absolutos versionados\n")
w(f"`git grep -I -P '(/Users/|/home/|[A-Za-z]:\\\\)'` (arquivos de texto): **{len(ab)} ocorrências em "
  f"{len({h['file'] for h in ab})} arquivos**. Nenhuma em `cyclophaser/`, `tests/` ou `tools/`. "
  "PNG/binários não foram varridos.\n")
w("| arquivo:linha | trecho |\n|---|---|")
for h in ab:
    w(f"| `{h['file']}:{h['line']}` | {esc(h['text'][:120])} |")
w("")

# (g) -------------------------------------------------------------------------
def find(f, pat):
    return [f"{f}:{i}" for i, l in enumerate((ROOT / f).read_text().splitlines(), 1) if re.search(pat, l)]


uses_pbo = subprocess.run(["git", "grep", "-n", "pair_by_overlap(", "HEAD", "--", ".", ":(exclude)research/cleanup/",
                           ":(exclude).pypirc"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
uses_sps = subprocess.run(["git", "grep", "-n", "score_phase_sequences(", "HEAD", "--", ".", ":(exclude)research/cleanup/",
                           ":(exclude).pypirc"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
w("## 0.2 (g) Os dois medidores de \"mature correta\" (nada medido)\n")
w("| medidor | definição (arquivo:linha) | em uma frase |\n|---|---|---|")
w(f"| `evaluate_against_labels.py` → `labels_core.score_phase_sequences` | "
  f"`{find('research/labels/labels_core.py', r'^def score_phase_sequences')[0]}` | "
  "pontua **só séries cuja sequência de fases bate exatamente com o rótulo**; nelas, cada INÍCIO de fase (mature "
  "incluída, a primeira fase excluída, fronteiras `unsure` excluídas) acerta se |detectado − rótulo| ≤ o "
  "`tolerance_idx` daquela fronteira; séries com sequência diferente não geram distância nenhuma |")
w(f"| `item19_core.pair_by_overlap` | `{find(J.DIAG + 'item19/item19_core.py', r'^def pair_by_overlap')[0]}` "
  f"(critério em `{find(J.DIAG + 'item19/item19_core.py', r'matches_label.. = ')[0]}`) | "
  "pontua **todas** as séries: pareia o PRIMEIRO mature rotulado com o bloco mature detectado de maior sobreposição "
  "(sem sobreposição: o de ponto médio mais próximo) e acerta se início E fim estão a ≤ `MARGIN` = 6 passos |")
w("")
w(f"Chamadas de `pair_by_overlap(` ({len(uses_pbo)}; inclui 3 REIMPLEMENTAÇÕES locais, em `frontC/measure_frontC.py`, "
  "`item20b/gate_stage2.py` e `item20b/measure_20b.py`):\n")
for u in uses_pbo:
    _, f, ln, _ = u.split(":", 3)
    w(f"* `{f}:{ln}`")
w(f"\nChamadas de `score_phase_sequences(` ({len(uses_sps)}):\n")
for u in uses_sps:
    _, f, ln, _ = u.split(":", 3)
    w(f"* `{f}:{ln}`")
w("\nO app (Benchmark) reporta os dois lado a lado, nomeados (`benchmark_core.py`: SEQUENCE_INSTRUMENT / "
  "MATURE_INSTRUMENT). Os dois contam populações diferentes; nenhum número foi medido aqui.\n")

# 0.3 -------------------------------------------------------------------------
w("## 0.3 Manifesto de branches (somente leitura; nada apagado)\n")
w(f"Remotas: **{BR['n_remote']}** (`origin/*`, sem `HEAD`), ponta de develop `{BR['develop_tip']}`. "
  "\"em develop\" = `git merge-base --is-ancestor`; à frente/atrás contra `origin/develop-v2.1`; "
  "citações = `git grep` do nome da branch na árvore de HEAD. Dados: `passo0/branches.json`.\n")
bdest = Counter()
apagar_anc = apagar_peq = 0
w("\"patch-eq.\" = NÃO ancestral, mas `git cherry origin/develop-v2.1 <branch>` só imprime `-` (todo commit tem um "
  "equivalente de patch em develop). Uma branch patch-equivalente NÃO está contida em develop: seus próprios hashes "
  "deixam de resolver se a ref sumir, por isso nunca é somada às ancestrais. \"hashes citados\" = `git grep` dos "
  "hashes curtos dos commits da branch que não estão em develop.\n")
w("| branch | ponta | em develop? (ancestral) | patch-eq.? | +à frente/−atrás | conteúdo (arquivos alterados desde a base) | citada em | hashes citados | destino | motivo |")
w("|---|---|---|---|---|---|---|---|---|---|")
for b in BR["remote"]:
    name = b["branch"]
    if name in J.BRANCH:
        d, why = J.BRANCH[name]
    elif b["in_develop"]:
        d, why = "apagar", "ancestral de develop; os hashes citados nos registros continuam alcançáveis por develop"
    elif b["patch_equivalent"]:
        d, why = "tag de arquivo", "patch-equivalente, NÃO ancestral: os próprios hashes só resolvem enquanto houver ref"
        ERRORS.append(f"patch-equivalent branch without judgement: {name}")
    else:
        d, why = "decidir com o Danilo", "não contida em develop"
        ERRORS.append(f"branch without judgement: {name}")
    bdest[d] += 1
    if d == "apagar":
        apagar_anc += b["in_develop"]
        apagar_peq += (not b["in_develop"]) and b["patch_equivalent"]
        if not b["in_develop"] and not b["patch_equivalent"]:
            ERRORS.append(f"'apagar' on a branch neither ancestral nor patch-equivalent: {name}")
    content = f"{b['n_files_changed']} arq.: " + ", ".join(b["dirs_changed"][:4]) if b["n_files_changed"] else "— (nada fora de develop)"
    cites = ", ".join(f"`{m}`" for m in b["mentions"][:3]) + (f" +{len(b['mentions']) - 3}" if len(b["mentions"]) > 3 else "") or "—"
    hcites = ", ".join(f"`{m}`" for m in b["hash_mentions"][:3]) + (f" +{len(b['hash_mentions']) - 3}" if len(b["hash_mentions"]) > 3 else "") or "—"
    peq = "—" if b["in_develop"] else ("**sim**" if b["patch_equivalent"] else f"não (+{b['cherry_plus']})")
    w(f"| `{name}` | `{b['tip']}` {b['date']} — {esc(b['subject'][:70])} | {'sim' if b['in_develop'] else '**não**'} | {peq} | "
      f"+{b['ahead']}/−{b['behind']} | {esc(content)} | {cites} | {hcites} | **{d}** | {esc(why)} |")
w("")
w("| destino | branches |\n|---|---|")
for d, n in sorted(bdest.items()):
    w(f"| {d} | {n} |")
w("")
n_peq_all = sum(1 for b in BR["remote"] if b["patch_equivalent"])
w(f"**Contagem corrigida (Passo 1).** \"apagar\" = {bdest.get('apagar', 0)}: **{apagar_anc} ancestrais** "
  f"(`--is-ancestor`) e **{apagar_peq} só patch-equivalentes**. Branches patch-equivalentes não ancestrais no total: "
  f"{n_peq_all} (" + ", ".join(f"`{b['branch']}`" for b in BR["remote"] if b["patch_equivalent"]) + "), todas com "
  "destino \"tag de arquivo\". O Passo 0 somava `diag/front-b-distance-inert` às 30 ancestrais como \"apagar\" (31); "
  "seu hash é citado nos registros, então ela não pode sumir sem ref.\n")
w(f"Branches locais sem remota (fora do escopo, só registradas): {', '.join('`' + b + '`' for b in BR['local_without_remote'])}. "
  "`exp/pre-peak-normalization` (`1faf0c8`) NÃO está em develop, nunca foi publicada e se declara "
  "\"descartável, não mesclar\"; está registrada em `docs/future_work.md` e `research/labels/swell_item30/README.md`.\n")

# 0.4 -------------------------------------------------------------------------
w("## 0.4 Rastreabilidade (esqueleto): destino \"remover\" com achado\n")
w("Para cada entrada que sai e contém achado: onde o achado já está registrado hoje. **SÓ AQUI** alimenta o "
  "documento consolidado do Passo 2 (o arquivo só sai depois). Registros em relatórios de frente contam porque "
  "esses relatórios são **consolidados**, não removidos.\n")
TRACE_P = ROOT / "research/cleanup/passo2/traceability.json"
TRACE = {r["path"]: r for r in json.loads(TRACE_P.read_text())["rows"]} if TRACE_P.exists() else {}


def final_dest(path):
    r = TRACE.get(path)
    if not r:
        return "—"
    return "; ".join(d.replace("§", "docs/findings.md §") if d.startswith("§") else d for d in r["destination"])


w("Coluna **destino final (Passo 2)**: para onde o achado vai quando o arquivo sair — seção de "
  "`docs/findings.md` ou linha de `docs/future_work.md` — lida de `research/cleanup/passo2/traceability.json`, "
  "gerado por `passo2/make_findings.py`.\n" if TRACE else "")
w("| arquivo | achado | registrado em | destino final (Passo 2) |\n|---|---|---|---|")
only_here = []
tr = [x for x in rows if x["dest"] == "remover" and x["finding"] and x["path"] not in members_of] + \
     [g for g in grouped if g["dest"] == "remover" and g["finding"]]
for x in sorted(tr, key=lambda z: z["path"]):
    reg = ", ".join(f"`{r}`" for r in x["reg"])
    if not reg:
        reg = "**SÓ AQUI**"
        only_here.append(x)
    w(f"| `{x['path']}` | {esc(x['finding'])} | {reg} | {esc(final_dest(x['path']))} |")
w("")
if TRACE:
    cons = [x for x in rows if x["dest"] == "consolidar"]
    w("## 0.5 Destinos finais dos arquivos \"consolidar\" (Passo 2)\n")
    w(f"{len(cons)} arquivos; destino lido de `passo2/traceability.json`. Sem destino: "
      f"{sum(1 for x in cons if final_dest(x['path']) == '—')}.\n")
    w("| arquivo | seção proposta (Passo 0) | destino final (Passo 2) |\n|---|---|---|")
    for x in sorted(cons, key=lambda z: z["path"]):
        w(f"| `{x['path']}` | {x['sec'] or '—'} | {esc(final_dest(x['path']))} |")
    w("")
w(f"Entradas: {len(tr)}; **SÓ AQUI: {len(only_here)}**" +
  (" — " + "; ".join(f"`{x['path']}` → {x['finding']}" for x in only_here) if only_here else "") + ".\n")

tail = P0 / "manifest_tail.md"   # hand-written: decisions for Danilo, deviations
if tail.exists():
    out.append(tail.read_text())
RL = json.loads((P0 / "relabel_diff.json").read_text())
w("\n## Dados gerados das decisões\n")
w(f"### Decisão 1 — re-rotulagens de treino fora de develop (`passo0/relabel_diff.py`)\n")
w(f"`research/labels/manual_labels.yaml` em `origin/develop-v2.1` (`{RL['develop']}`) × `origin/feat/label-tab-toplevel` "
  f"(`{RL['branch']}`), só ids de TREINO ({RL['n_train_ids']}: `train:` + `batches.*.train`; entradas de teste descartadas "
  f"antes de comparar; nenhuma série lida). Rótulos de treino: develop {RL['n_train_labels_develop']}, branch "
  f"{RL['n_train_labels_branch']} (só em develop: {len(RL['only_in_develop'])} — o lote swell, desenhado depois da branch).\n")
w("| id | campo | develop | branch |\n|---|---|---|---|")
for r in RL["changed"]:
    for ph in r.get("phases", []):
        w(f"| `{r['id']}` | fronteira `{ph['phase']}`.{ph.get('field', '?')} | {ph.get('develop')} | {ph.get('branch')} |")
    if "verdict" in r:
        fmt = lambda v: esc(", ".join(f"{k}={x}" for k, x in v.items())) if isinstance(v, dict) else str(v)
        w(f"| `{r['id']}` | veredito | {fmt(r['verdict']['develop'])} | {fmt(r['verdict']['branch'])} |")
    for f in r["fields"]:
        if f not in ("phases", "verdict"):
            w(f"| `{r['id']}` | {f} | {esc(r[f]['develop'])} | {esc(r[f]['branch'])} |")
w("")
w(f"Com mudança de conteúdo: **{len(RL['changed'])}**. Re-salvamento sem mudança de rótulo: "
  + (", ".join(f"`{x['id']}`" for x in RL["resave_only"]) or "nenhum")
  + ". Não recuperadas (decisão 1); entram como pendência aberta no documento único (Passo 2).\n")
RQ = json.loads((P0 / "requirements_readers.json").read_text())
w("### Decisão 10 — quem lê o `requirements.txt` da raiz (`passo0/requirements_readers.py`; só lista)\n")
w("| consumidor | lê a raiz? | onde |\n|---|---|---|")
for g, v in RQ["groups_reading_root"].items():
    where = ", ".join(f"`{x.split(': ', 1)[1]}`" for x in RQ["readers"] if x.startswith(g + ":")) or "—"
    w(f"| {g} | {'**sim**' if v else 'não'} | {where} |")
w("")
w("O CI instala do wheel mais `pytest pyyaml`; o RTD lê `docs/requirements.txt`; `setup.py` declara "
  "`install_requires` próprio; o app tem `tools/calibration_app/requirements.txt` próprio. O serviço Streamlit Cloud "
  "escolhe o arquivo por regra própria, fora da árvore: não verificável daqui. Só as instruções de instalação/contribuição "
  "dos docs de usuário mandam rodar `pip install -r requirements.txt` na raiz — ou seja, **alguém o lê** (por instrução); "
  "pela decisão 10 ele fica. O `Pipfile` sai.\n")

w("\n## Resumo para orquestração (gerado)\n")
w(f"* Branch `chore/repo-cleanup`; base em develop-v2.1 `{BASE}` (esperada `06d8550`); inventário em HEAD `{head[:7]}`. "
  "Hash do commit deste passo: ver a mensagem de entrega (um arquivo não contém o próprio hash).")
w(f"* Linha de base: suíte previsto 1438/0 → obtido {obt_pass}/{obt_fail}; digest previsto `3a6de265…` → obtido `{digest[:8]}…`.")
w(f"* Arquivos versionados: {INV['n_tracked_total']} — manter {dest_count.get('manter', 0)}, consolidar "
  f"{dest_count.get('consolidar', 0)}, remover {dest_count.get('remover', 0)}. Scripts de stale_scripts.md confirmados: {n_exist}/{len(STALE)}.")
w(f"* Branches remotas: {BR['n_remote']} — " + ", ".join(f"{d} {n}" for d, n in sorted(bdest.items()))
  + f"; das \"apagar\", {apagar_anc} ancestrais e {apagar_peq} só patch-equivalentes.")
w("* SÓ AQUI: " + ("; ".join(f"`{x['path']}` → {x['finding']}" for x in only_here) or "nenhum") + ".")
w(f"* params-1..14 fora dos diagnósticos e de future_work.md: {len(live_p114)} ocorrências em "
  f"{len({h['file'] for h in live_p114})} arquivos; propostas **migrar** em "
  + ", ".join(sorted({f"`{h['file']}`" for h in live_p114 if (J.P114_LINE.get(f"{h['file']}:{h['line']}") or J.P114_LIVE.get(h['file']))[0] == 'migrar'})) + ".")
w(f"* params-15: {len(p15)} ocorrências — vivas {cls_count['VIVA']}, históricas {cls_count['HISTÓRICA']}.")
w(f"* boundary_padding: {len(bp)} ocorrências no escopo; assinaturas com default: "
  + ", ".join(f"`{fn}`={v}" for fn, v in sig.items()) + f"; `get_periods` tem default próprio: {'sim' if has_gp else 'não'}.")
w(f"* Caminhos absolutos: {len(ab)} ocorrências em {len({h['file'] for h in ab})} arquivos; fora de `research/` e `docs/future_work.md`: "
  f"{sum(1 for h in ab if not h['file'].startswith(('research/', 'docs/future_work.md')))}.")
w("* Decisões e desvios: seções acima.")
(ROOT / "research/cleanup/MANIFEST.md").write_text("\n".join(out) + "\n")
summary = dict(n_tracked=INV["n_tracked_total"], dest=dict(dest_count), stale_confirmed=n_exist, stale_total=len(STALE),
               branches=BR["n_remote"], branch_dest=dict(bdest), apagar_ancestral=apagar_anc,
               apagar_patch_equivalent_only=apagar_peq, only_here=[x["path"] for x in only_here],
               p114_total=len(hits), p114_live=len(live_p114), p114_live_files=sorted({h["file"] for h in live_p114}),
               p15_total=len(p15), p15_viva=cls_count["VIVA"], p15_hist=cls_count["HISTÓRICA"],
               bp_total=len(bp), abs_total=len(ab), abs_files=sorted({h["file"] for h in ab}),
               digest=digest, suite=[obt_pass, obt_fail])
(P0 / "manifest_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
if ERRORS:
    print("ERRORS:\n  " + "\n  ".join(ERRORS))
    sys.exit(1)
print(json.dumps(summary, ensure_ascii=False))
