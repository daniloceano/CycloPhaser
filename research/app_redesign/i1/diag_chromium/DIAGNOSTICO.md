# I1, segunda correção: diagnóstico dos 3 testes de Chromium em streamlit 1.56.0

Feito ANTES de qualquer correção, com `diagnose.py` (mesmo harness dos testes,
chave de desenvolvedor ligada). O script reproduz cada teste até o controle que ele
espera, procura o controle do mesmo jeito que o teste (timeout de 10 s) e salva a
captura daquele momento e um dump dos controles na tela (tag, papel, nome acessível,
valor). Rodado em dois interpretadores:

- `st1.56.0/` — venv novo, streamlit 1.56.0, playwright 1.62.0: **as 3 buscas falham**;
- `conda_st1.63.0/` — env conda `cyclophaser`, streamlit 1.63.0: **as 3 acham o controle**.

`report.json` em cada pasta tem o dump completo; as capturas são `a_phase_row_0.png`,
`b_boundary_padding.png`, `c_sidebar_slider.png`.

| Teste | Busca do teste | Em 1.56.0 (captura + dump) | Em 1.63.0 | Classe |
|---|---|---|---|---|
| `test_label_browser.py::test_the_table_shows_a_row_per_phase` | `get_by_label("phase, row 0", exact=True)` | Na tela, com o valor certo: combobox de nome acessível **`Selected incipient. phase, row 0`**, `<input>` com valor vazio | nome `phase, row 0`, valor `incipient` no `<input>` | **TESTE** |
| `test_app_pages_browser.py::test_an_uploaded_track_and_an_imported_yaml_…` | `get_by_label("Boundary padding", exact=True)` | Na tela, com o valor certo: combobox de nome **`Selected reflect. Boundary padding`**, `<input>` vazio | nome `Boundary padding`, valor `reflect` | **TESTE** |
| `test_app_pages_browser.py::test_sidebar_values_set_in_the_ui_…` | `[data-testid="stSlider"] input[type="range"]` | Na tela, com o valor certo: 17 sliders como **`<div role="slider">`** com `aria-valuenow` (Low cutoff 168, High cutoff 18, …) | 17 `<input type="range">` com os mesmos nomes e valores | **TESTE** |

Nos três casos o controle está na tela, com o valor certo, mas com outra estrutura de
DOM: o Streamlit trocou o seletor e o slider de componente entre 1.56 e 1.63. Nenhum
é defeito do app, então o piso não precisa subir por causa deles.

Correção (só testes): `tests/browser_harness.py` ganhou `selectbox(page, label)`
(acha o combobox pelos dois nomes), `selectbox_value(page, label)` (lê o valor do
`<input>` ou do nome "Selected …") e `SLIDER_HANDLE` (os dois tipos de slider);
`LabelPage.phase_name` e `tests/test_app_pages_browser.py` passaram a usá-los. O
retrato da barra lateral desse arquivo lê os dois tipos de slider e normaliza o nome
"Selected …".
