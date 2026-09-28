## Decisões que precisam do Danilo

Texto escrito à mão (julgamento). Contagens e `arquivo:linha` que sustentam cada item estão nas seções geradas acima.

1. **Re-rotulagens de treino fora de develop** (`origin/feat/label-tab-toplevel`, commit `0c63145`, 2026-09-15).
   Três rótulos de treino do Danilo nunca chegaram a `research/labels/manual_labels.yaml` de develop:
   `20150656` (fronteira `residual`), `20170409` (fronteira `decay`), `20170154` (veredito → `ambiguous`);
   o quarto (`20180170`) era um re-salvamento sem mudança. Comparação feita lendo o YAML nas duas pontas
   (as quatro ids conferidas no split de treino; nenhuma série lida). Toda frente desde então rodou sobre os
   rótulos antigos. Opções: recuperar os três (muda escores de frentes fechadas; teste intocado) /
   descartar / manter a branch só como registro. O código de UI da mesma branch foi superado.
2. **`.pypirc` versionado** desde 2023. Não foi lido. Verificar o conteúdo; se houver token, revogá-lo
   (continua no histórico do git mesmo após remover do versionamento); proposta: remover do versionamento
   e pôr no `.gitignore`.
3. **"2.0.0" não é o release 2.0.0** (seção (d)). `research/labels/defaults_2.0.0.json`,
   `tests/baselines/*_2_0_0.csv`, `tests/legacy_defaults.py`, `item31/make_defaults_2_0_0.py`, a coluna
   "2.0.0" da tabela do CHANGELOG [Unreleased], as docstrings "(… up to 2.0.0)" e `docs/usage.rst`
   descrevem develop no estágio 0 do item 31, não o pacote publicado (que não tem `boundary_padding` e
   usa `replace_endpoints_with_lowpass=24`). Renomear/re-rotular ("pré-item-31") no Passo 1/4? Toca nomes
   de arquivo lidos por pacote, testes e app.
4. **App publicado × pacote publicado.** `tools/calibration_app/requirements.txt` instala
   `cyclophaser>=2.0.0` do PyPI, e a versão mais nova no PyPI é 2.0.0 (`pip index versions`, hoje).
   `tools/calibration_app/app.py:219` indexa `sig["intensification_min_depth"]`, chave que a assinatura
   da tag v2.0.0 não tem (seção (d)) → leitura estática: o app de develop quebraria na inicialização contra
   o 2.0.0 do PyPI (não executado). Relevante para a ordem release → merge em master → deploy.
5. **Branches "decidir"**: `feat/label-tab-toplevel` (item 1); `fix/inspector-min-depth-params`
   (superada por `52ecb04`; future_work diz que o destino é desta frente); `research/item20c-duration-ratio`
   e `research/v3-topology-proxy` — o texto dos itens 23 e 18 de future_work só existe nelas
   (develop pula de 17 para 19 e de 22 para 24). Mergear só a documentação, manter como registro, ou
   converter em tag?
6. **Branches "manter como registro"** → converter em tags anotadas `archive/*` (já existe o precedente
   `archive/app-phase-focus`) e então apagar as branches? Os hashes citados nos registros continuariam
   resolvíveis.
7. **Remoção dos diagnósticos de frentes fechadas.** Antes de remover, criar uma tag anotada no último
   commit que os contém (ex.: `archive/research-diagnostics-pre-cleanup`), para que todo caminho citado em
   `docs/future_work.md` (que não será reescrito) resolva com `git show <tag>:<caminho>`. Os scripts de
   frentes fechadas saem mesmo quando ainda rodam: são reprodutíveis pelo commit.
8. **Dependências vivas dentro de `diagnostics/`** (`item19/item19_core.py` importado pelo app;
   `item30/item30_core.py`, `figs_cf.py`, `separability.py` importados por teste; `item31/param_table.json`
   lido por teste; `item31/recovery_table.*`): manter onde estão (proposta atual) ou mover para um lugar
   vivo (ex.: `research/labels/instruments/`) no Passo 1, atualizando imports?
9. **Três reimplementações locais de `pair_by_overlap`** (seção (g)) saem com seus diagnósticos; nada vivo
   depende delas. Registrar no documento único que o medidor canônico é `item19_core.pair_by_overlap`?
10. **`Pipfile`** (remover) e **`requirements.txt`** da raiz (manter, mas sobrepõe `docs/requirements.txt`
    e `setup.py`; inclui `pipenv`): confirmar.
11. **Defaults literais do app** que divergem da assinatura (seção (e)): intencionais (semântica de YAML
    antigo sem a chave) ou dívida? Decidir no Passo 4. Com C1 (`reflect`), `app.py:1439` passa a coincidir.
12. **Default próprio das funções do filtro.** `lanczos_filter`, `lanczos_bandpass_filter` e `_convolve_same`
    têm default `"reflect"`; `process_vorticity`/`determine_periods` têm `"edge"`. C1 alinha os dois; confirmar
    que C1 muda só `process_vorticity`/`determine_periods` (o prompt cita só essas assinaturas).
13. **Textos vivos defasados encontrados** (edição no Passo 1, proposta "migrar"): docstring/comentário de
    `benchmark_core.py` (`item19_core.CONFIG`, "onze configurações"); docstrings de `layer_inspector.py`
    ("sob params-14"); comentário de `tests/test_intensification_min_depth.py:69-71`; `CHANGELOG.md:232`
    e `:288` (arquivos de config removidos); `lanczos_filter.py:6` ("zero" default) contra :39–56
    ("reflect"); `determine_periods.py:1044`/`:1521` ("as the current defaults are" para `reflect`);
    comentário de cabeçalho de `tests/test_boundary_padding.py:27` ("default zero").
14. **SÓ AQUI**: `research/incipient_plateau/geometric_vs_plateau.csv` e seu gerador — consolidar a tabela
    em S02 antes de remover.

## Desvios do prompt, e por quê

* **Suíte completa = `-m "not browser"`.** CLAUDE.md proíbe rodar `tests/test_label_browser.py`.
* **O gerador canônico escreve fora de `research/cleanup/`** (anexa ao livro-razão do digest). O registro
  anexado foi preservado em `passo0/` e o livro-razão restaurado; `run_baseline.sh` passou a fazer isso
  sozinho *depois* da rodada medida (na rodada, foi feito à mão logo em seguida).
* **(b)**: as opções do prompt (migrar / aposentar / recuperar de 33ea489) não cobrem menção puramente
  histórica que não carrega arquivo; para essas, a proposta é **manter**.
* **(c)**: o grep pega também `params_15`, `PARAMS_15` e `params15` (nomes de testes, constantes, campos),
  porque também quebram ou confundem no renome.
* **(d)**: incluí as assinaturas de `lanczos_filter.py` (default próprio `"reflect"`, fora das pistas do
  prompt) e um suplemento com `tests/test_boundary_padding.py`. `README*` não menciona o parâmetro.
* **(e)**: o localizador é heurístico (documentado em `defaults_in_text.py`); acrescentei os defaults
  literais no código do app, que não são texto, mas são exatamente a deriva que o Passo 4 procura.
* **Tipo**: acrescentei "script de pesquisa (vivo)" (`labels_core.py`, avaliador, etc.) para não chamá-los
  de "script de diagnóstico".
* **`.pypirc` não foi lido** (arquivo de credenciais; o classificador de permissões também bloqueou).
  Está no manifesto, com destino proposto e a verificação pedida ao Danilo.
* **Branches**: a contagem de remotas inclui `develop-v2.1` e `master`. As branches locais sem remota foram
  só registradas (fora do escopo), com destaque para `exp/pre-peak-normalization`, que não está em develop.
* **Achado fora do que foi pedido**: o rótulo "2.0.0" do item 31 (decisão 3), e as re-rotulagens fora de
  develop (decisão 1).
* **0.4**: um grupo homogêneo (ex.: `item30/figs_cf/*.png`) conta como uma entrada.
