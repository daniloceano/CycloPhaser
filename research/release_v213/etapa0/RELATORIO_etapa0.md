# Release 2.1.3 — etapa 0: medições (2026-10-14)

Previsões: PREVISOES_etapa0.md (enviadas ao Danilo no chat antes de medir;
não foram commitadas antes porque esta sessão não tem credencial de push).
Ambiente: container Linux limpo, /usr/bin/python3.12, um venv novo por linha, CWD
fora de qualquer checkout; cyclophaser do PyPI; smoke.py confere que
`cyclophaser.__file__` está no site-packages do venv e roda determine_periods
no example_file.

| id | previsão | medido | bate? |
|---|---|---|---|
| M1 instalação nova 2.1.2 | cmocean 4.0.3, import OK | cmocean 4.0.3, numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, matplotlib 3.11.2, xarray 2026.9.0; import e determine_periods OK | sim |
| M2 cmocean 4.0.1 pré-instalado | pip mantém, import FALHA | "Requirement already satisfied: cmocean>=4.0 … (4.0.1)"; FileNotFoundError …/cmocean/rgb/inverted/thermal_i-rgb.txt | sim |
| M3 pisos (uv lowest-direct, only-binary) | cmocean 4.0.1, import FALHA | cmocean 4.0.1, numpy 2.1.0, pandas 2.2.2, scipy 1.14.0, matplotlib 3.9.0, xarray 2024.9.0; mesma FileNotFoundError | sim |
| M4 = M3 com cmocean>=4.0.3 | import OK | cmocean 4.0.3, numpy 2.1.0, pandas 2.2.2; import e determine_periods OK | sim |
| M5 wheel 2.1.2 | só cyclophaser/ + LICENSE; 21 Requires-Dist + pytest extra | exatamente isso (6 arquivos do pacote, licenses/LICENSE) | sim |
| M6 sdist 2.1.2 | tests/*.py sem dados; pytest não passa | 40 entradas em tests/ (só test_*.py do nível de cima; sem conftest.py, __init__.py, synthetic/, calibration_data/, sample_tracks/); pytest: 10 erros de coleta, interrompido | sim |
| M7 streamlit mais novo no PyPI | (não é previsão) | 1.66.0 | — |
| M8 streamlit do app público | NÃO 1.66.0 | menu ⋮ do app: "Made with Streamlit v1.66.0"; app mostra "CycloPhaser 2.1.2" | NÃO (previsão errada) |

Leituras do repo (develop 4287d5b):
- `git diff v2.1.2 develop -- cyclophaser setup.py pyproject.toml` vazio.
- Diferença v2.1.2..develop fora de research/: .circleci (config + check_app_skips),
  CLAUDE.md, docs/future_work.md, tests/conftest.py, tests/sample_tracks/ (2 CSV),
  2 arquivos de teste. 20 commits.
- setup.py não declara pyyaml; `pandas>=2.2` e `pyyaml>=6.0` imprecisos estão em
  tools/calibration_app/requirements.txt (que também tem `cmocean>=4.0`).
- Código do pacote importa só numpy, pandas, scipy, xarray, matplotlib, cmocean
  (+ biblioteca padrão). Os outros 15 itens de install_requires são dependências
  de dependências ou ferramentas (iniconfig, pluggy = pytest; setuptools, wheel = build).
- CHANGELOG: link [Unreleased] já compara v2.1.2...HEAD (item resolvido);
  a seção [Unreleased] está vazia.
- sys.path.insert(0, raiz): evaluate_against_labels.py:83 e item19_core.py:23
  continuam lá; também default_behaviour_hash.py:79 (de propósito),
  front_g_deviation_table.py:14, measure_incipient_smoothing.py:52.
- Gerador do hash: research/labels/diagnostics/front_b/default_behaviour_hash.py
  existe em develop e em v2.1.2; recusa rodar se cyclophaser não vier da árvore
  de trabalho; anexa um registro ao .txt versionado.
- CircleCI: test_pypi_publish só em develop; pypi_publish só em master; ambos exigem
  build_test + app_test_floor + app_test_newest (config de develop).
- Suíte de navegador (defs): app_pages 9, compare 3, validate 3 (=15), label 27
  (não roda pelo agente, CLAUDE.md).

Nota: M1_smoke.log foi gerado com uma versão anterior da última linha do smoke.py
(imprimia a 1ª coluna como "phases"); o import e o determine_periods rodaram
do mesmo jeito. As outras execuções usam o smoke.py desta pasta.

## Decisões do Danilo (2026-10-14, 19:00): "Sigo com o que você recomendar"
1. cmocean>=4.0.3 no setup.py.
2. install_requires reduzido às 6 dependências importadas pelo código:
   cmocean>=4.0.3, matplotlib>=3.9, numpy>=2.1, pandas>=2.2.2, scipy>=1.14,
   xarray>=2024.9; extras_require test (pytest>=8.3) mantido.
3. sdist sem tests/ (MANIFEST.in com `prune tests`).
4. tools/calibration_app/requirements.txt: cmocean>=4.0.3, pandas>=2.2.2,
   pyyaml>=6.0.1 (pisos reais; não muda comportamento do app).
5. `cyclophaser>=2.1.0` do app NÃO sobe (com >=2.1.3 o rebuild do push na
   master quebraria até a 2.1.3 chegar ao PyPI).
6. Fora: insert(0) em research/labels, Python além de 3.12, job em tags.
7. Plano de release e critério (a)–(h) como no prompt da etapa 1.
