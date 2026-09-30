# Passo 4, parte 4a — relatório (gerado)

Gerado por `passo4/make_report_4a.py` a partir das saídas de `passo4/`. Previsões: `passo4/PREVISOES.md` (commits 16 e 16c; não editadas).

| id | previsto | obtido | confere |
|---|---|---|---|
| D1 (antes) | 0 divergências em `cyclophaser/` | oficial (`before.json`): 14, 1 em `cyclophaser/`; corrigida (`before_corrected.json`): 13, 1 em `cyclophaser/` | **NÃO** |
| D1a | 0 divergências FORA de `docs/*.rst` após o commit 17 | 4 no total, 0 fora de `docs/*.rst` (por arquivo: {'docs/api.rst': 4}) | sim |
| D4 suíte | 0 falhas | 1438 passed / 0 failed (HEAD `bffa6fe`) | sim |
| D4 diff | diff de `cyclophaser/` desde 16b (`129b04d`) vazio | vazio | sim |
| D4 R4 | 0 referências vivas (scanner corrigido do Passo 3) | 0 referências; caminhos removidos 308; saídas próprias 13 | sim |
| D5 | 1 configuração chega aos caminhos de reserva; resultados inalterados | 0 configurações; resultados alterados: nenhum | **NÃO** |

## D5 — detalhe

* Reservas com literal ANTES (`b9991c4`): `_preset_to_widgets` {'use_filter': False, 'replace_endpoints_with_lowpass': 0, 'savgol_polynomial': 3, 'boundary_padding': 'reflect', 'cutoff_low': 168, 'cutoff_high': 48, 'use_smoothing': 'auto', 'use_smoothing_twice': 'auto'}; `mature_ledger` {'length_scale': 'global', 'mature_method': 'derivative', 'mature_amplitude_fraction': 0.9, 'mature_min_depth': 0.0}.
* Em HEAD: `_preset_to_widgets` nenhuma; `mature_ledger` nenhuma (lidas da assinatura).
* `SYNTHETIC_CLEAN_PRESET`: chaves ausentes nenhuma; widgets antes == depois: True
* `SYNTHETIC_NOISY_PRESET`: chaves ausentes nenhuma; widgets antes == depois: True
* `mature_ledger`: chaves sempre passadas por `build_args_periods`: {'length_scale': True, 'mature_method': True, 'mature_amplitude_fraction': True, 'mature_min_depth': True}.
* A previsão (1) vinha de supor que o preset "clean" não traz todas as chaves de filtragem; os dois presets trazem todas. **D5 = FAIL na contagem**; resultados inalterados.

## D1a — divergências restantes (todas em `docs/*.rst`, revisão do Danilo)

* `docs/api.rst:22` `replace_endpoints_with_lowpass`: escrito `24`, código {'process_vorticity': '0', 'determine_periods': '0'}
* `docs/api.rst:24` `use_smoothing_twice`: escrito `auto`, código {'process_vorticity': 'False', 'determine_periods': 'False'}
* `docs/api.rst:29` `threshold_mature_distance`: escrito `0.125`, código {'get_periods': '0.18', 'determine_periods': '0.18'}
* `docs/api.rst:30` `threshold_mature_length`: escrito `0.03`, código {'get_periods': '0.15', 'determine_periods': '0.15'}

Linha final da suíte: `1438 passed, 1 skipped, 29 deselected, 89 warnings in 426.87s (0:07:06)`.
