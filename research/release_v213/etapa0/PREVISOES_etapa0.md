# Release 2.1.3 — etapa 0: previsões (declaradas antes de medir, 2026-10-14)

Ambiente das medições: container Linux limpo, Python 3.12 (/usr/bin/python3.12),
um venv novo por combinação, CWD fora de qualquer checkout do repo. Pacote
vindo do PyPI (cyclophaser==2.1.2), nunca da árvore-fonte. Cada execução
verifica `cyclophaser.__file__` dentro do site-packages do venv.

Cadeia de import (lida no código, não medida): `import cyclophaser` →
determine_periods.py:28 `from cyclophaser.plots import ...` → plots.py:5
`import cmocean.cm`. Logo, se o cmocean não importa, o cyclophaser não importa.

| id | combinação | previsão |
|---|---|---|
| M1 | `pip install cyclophaser==2.1.2` num venv vazio (o que um usuário novo faz hoje) | instala; cmocean resolvido = 4.0.3; `import cyclophaser` OK; `determine_periods` no example_file roda |
| M2 | venv com `cmocean==4.0.1` já instalado, depois `pip install cyclophaser==2.1.2` | pip mantém 4.0.1 ("already satisfied"); `import cyclophaser` FALHA com FileNotFoundError (…/rgb/inverted/…) |
| M3 | pisos declarados: `uv pip install --resolution lowest-direct --only-binary :all:` com os 21 itens de install_requires + cyclophaser==2.1.2 | instala; cmocean = 4.0.1 (não existe 4.0 no PyPI); `import cyclophaser` FALHA como em M2 |
| M4 | igual a M3, mas com `cmocean>=4.0.3` (a correção proposta) | instala; `import cyclophaser` OK; example_file roda |
| M5 | wheel 2.1.2 do PyPI: conteúdo e Requires-Dist | só `cyclophaser/` (5 .py + example_data/example_file.csv) + metadados com LICENSE; sem tests/; Requires-Dist = os 21 de install_requires + pytest>=8.3 com extra "test" |
| M6 | sdist 2.1.2 do PyPI: conteúdo | contém arquivos de tests/ (.py) mas NÃO contém tests/synthetic/data/*.csv nem tests/calibration_data/*.csv; rodar pytest a partir dele num venv limpo NÃO passa (falhas/erros por dados ausentes) |
| M7 | streamlit no PyPI hoje | 1.66.0 (já visto ao checar o acesso ao PyPI, antes desta lista; não é previsão) |
| M8 | streamlit do app público (menu ⋮ → About) | NÃO 1.66.0: o último rebuild foi o push de 2.1.2 na master (10/out), antes de 1.66.0 sair (14/out 16:07Z); previsão 1.65.0 ou anterior |

Já verificado por leitura do repo (sem previsão a declarar, não são medições de comportamento):
- cyclophaser/ e setup.py idênticos entre v2.1.2 e develop (4287d5b).
- `pyyaml>=6.0` e `pandas>=2.2` imprecisos estão no requirements.txt do APP; setup.py não declara pyyaml.
- Link [Unreleased] do CHANGELOG já compara a partir de v2.1.2 (item resolvido).
- `test_pypi_publish` roda só em `develop`.
