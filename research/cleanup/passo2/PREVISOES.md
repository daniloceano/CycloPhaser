# Passo 2 — previsões declaradas ANTES de escrever o documento único

Copiadas do prompt do Passo 2 (2026-09-28), sem ajuste. Versionadas em commit
próprio, anterior a `docs/findings.md` e a todo script de verificação deste passo.

| id | previsão |
|---|---|
| Q1 | todos os 40 arquivos "consolidar" do manifesto têm seus achados mapeados para uma seção do documento (0 sem destino) |
| Q2 | os 2 itens "SÓ AQUI" (`geometric_vs_plateau.csv` e seu gerador) estão representados em S02 |
| Q3 | na tabela de rastreabilidade final, 0 linhas apontam para arquivo com destino "consolidar" ou "remover" |
| Q4 | verificação de citações: 0 números citados que não aparecem na linha citada, no commit citado |
| Q5 | suíte (`-m "not browser"`) após o passo: 0 falhas; diff de `cyclophaser/` neste passo: vazio |

Definições operacionais (fixadas aqui, antes de medir):

* **Arquivo "consolidar"**: linha do `research/cleanup/MANIFEST.md` com destino
  `**consolidar**` (grupos homogêneos contam como seus membros).
* **Q1 — mapeado**: o arquivo aparece na tabela de S10 com destino numa seção
  S01–S12 que existe em `docs/findings.md`, e é citado ao menos uma vez no corpo
  do documento como fonte (`caminho:linha@hash`).
* **Q2 — representado**: a seção S02 contém a tabela de
  `research/incipient_plateau/geometric_vs_plateau.csv` (uma linha por linha do
  CSV) e cita o CSV e o gerador `gen_geometric_vs_plateau.py` como fonte.
* **Q3 — aponta para arquivo que sai**: a coluna de destino da tabela de S10
  contém o caminho de um arquivo cujo destino no manifesto é "consolidar" ou
  "remover". Citar um arquivo que sai como FONTE (`@hash`) é permitido; como
  destino, não.
* **Q4 — número citado**: todo token numérico de uma linha (item de lista ou linha
  de tabela) de `docs/findings.md` que traga ao menos uma citação
  `caminho:linha@hash`, excluídos: o texto das próprias citações; rótulos
  (S01…S12, item/itens N, stage/part N, §N, E01…, P1…, Q1…, C1/C2′); datas
  AAAA-MM-DD; hashes. O número passa se aparecer como token numérico em ao menos
  uma das linhas citadas naquela linha, lida com `git show <hash>:<caminho>`.
* **Q5**: `git diff 33dc4e1 HEAD -- cyclophaser/` vazio no fim do passo; suíte
  rodada no ambiente dedicado, com o assert de `cyclophaser.__file__`.
