## Decisões aprovadas pelo Danilo (2026-09-28)

Texto escrito à mão; os números que sustentam cada item estão nas seções geradas acima e em "Dados gerados das
decisões" abaixo. A proposta original do Passo 0 (as perguntas) está no commit `f17d802`.

1. **`feat/label-tab-toplevel` → tag de arquivo.** As re-rotulagens de treino NÃO são recuperadas; entram como
   pendência aberta no documento único (Passo 2), com as três diferenças regeradas por
   `passo0/relabel_diff.py` (tabela em "Dados gerados": `20150656` fronteira `residual` 91→100; `20170409`
   fronteira `decay` 74→71; `20170154` veredito boundary(incipient_end_idx 6)→ambiguous).
2. **`.pypirc` → removido do versionamento** (commit 1 do Passo 1; conteúdo não aberto). A senha já foi trocada
   pelo Danilo; o histórico não é reescrito.
3. **Rótulo "2.0.0"**: os textos são corrigidos no Passo 1 (CHANGELOG, docstrings, `docs/usage.rst`) contra a tag
   `v2.0.0` real; o renome dos arquivos para "pre-item31" fica para o Passo 4, em commit próprio.
4. **App publicado × PyPI**: fora de escopo; registrado como insumo da frente de release.
5. **`fix/inspector-min-depth-params` → tag de arquivo.** `research/item20c-duration-ratio` e
   `research/v3-topology-proxy`: o texto dos itens 23 e 18 entra no documento único (Passo 2), depois tag de arquivo.
6. **Branches de registro → tags `archive/*`.** Remoção de branch remota só com autorização explícita por branch
   (Passo 6).
7. **Tag `archive/research-diagnostics-pre-cleanup`** antes de qualquer remoção (Passo 3).
8. **Dependências vivas em `diagnostics/` ficam onde estão.**
9. **Os dois medidores de "mature correta" ficam;** o documento único diz qual governa o quê. As três cópias
   locais de `pair_by_overlap` saem com seus diagnósticos.
10. **`Pipfile` sai. `requirements.txt` da raiz**: listar quem o lê (CI, docs, Streamlit, setup); sai se ninguém,
    senão fica. Só listado agora — ver "Dados gerados".
11. **Defaults literais do app**: decidir no Passo 4.
12. **C1 muda só `process_vorticity` e `determine_periods`**; as funções do filtro já usam `"reflect"` e não
    são tocadas.
13. **Migrações de texto aprovadas** (Passo 1, commits 3 e 4).
14. **`geometric_vs_plateau.csv`**: a tabela entra no documento único antes de remover.

Correções de destino no manifesto, pedidas junto com as decisões: `diag/front-b-distance-inert` → tag de
arquivo (patch-equivalente, NÃO ancestral; hash `491a5d0` citado em `front_b/sensitivity_probe.py` e
`front_b/sweep_distance.py`); `research/incipient_plateau/measure_incipient_smoothing.py` → manter (citado por
`cyclophaser/find_stages.py`).

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
  No Passo 1 saiu do versionamento sem ser aberto.
* **Branches**: a contagem de remotas inclui `develop-v2.1` e `master`. As branches locais sem remota foram
  só registradas (fora do escopo), com destaque para `exp/pre-peak-normalization`, que não está em develop.
* **Achado fora do que foi pedido**: o rótulo "2.0.0" do item 31 (decisão 3), e as re-rotulagens fora de
  develop (decisão 1).
* **0.4**: um grupo homogêneo (ex.: `item30/figs_cf/*.png`) conta como uma entrada.
* **Passo 1 — regeração em HEAD novo.** O inventário foi regerado sobre a árvore do commit 1 do Passo 1 (sem
  `.pypirc`), e `branches.py` depois de `git fetch origin`: a contagem de remotas inclui agora
  `origin/chore/repo-cleanup` (publicada ao fim do Passo 0), com destino "manter".
* **Passo 1 — previsões gravadas neste commit.** `passo1/PREVISOES.md` vai no commit do manifesto (e não no de
  evidências) para que o git prove que as previsões precedem toda medição do Passo 1.
