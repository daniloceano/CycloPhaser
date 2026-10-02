# Commit 16d — relatório (gerado por make_report_16d.py)

| verificação | obtido |
|---|---|
| varredura (`sweep_16d.py`, antes) | 199 linhas; corrigidas 27, mantidas 172 (`sweep_16d_review.md`) |
| edições (`edit_16d.py`) | 27 edições, 31 substituições; destas, 3 são as correções de rst que quebravam a build |
| verificador de defaults depois (`after16d.json`) | divergências em `cyclophaser/`: 0 |
| (i) árvore sintática sem docstrings (`ast_16d.json`, 0522992 → WORKTREE) | idêntica: True (5 arquivos) |
| (ii) digest default, mesma sessão | `7552bc67…` (HEAD `0522992`) → `7552bc67…`; igual: True |
| suíte `-m "not browser"` | 1438 passed / 0 failed |
| `git log -- cyclophaser/` desde develop-v2.1 (`gate_a_16d.txt`) | `c5e298b`; `129b04d`; `742e685` |

Linha final da suíte: `1438 passed, 1 skipped, 29 deselected, 89 warnings in 426.05s (0:07:06)`.
