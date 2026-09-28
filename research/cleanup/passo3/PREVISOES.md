# Passo 3 — previsões declaradas ANTES de qualquer remoção ou tag

Do prompt do Passo 3 e da retomada (2026-09-28), sem ajuste. Versionadas no
commit 11, o commit em que a tag `archive/research-diagnostics-pre-cleanup` é
criada, antes do commit de remoção. R1 foi regerado depois do commit 10b por
`passo3/removal_list.py` (lista lida do MANIFEST, nunca digitada).

| id | previsão |
|---|---|
| R1 | arquivos removidos = entradas remover + consolidar do MANIFEST após o commit 10b = **309** (valor regerado: `removal_list.py` → 309; `manifest_summary.json` remover 272 + consolidar 37 = 309) |
| R2 | todo arquivo da lista existe na tag (`git cat-file -e <tag>:<caminho>`): 100 % |
| R3 | rastreabilidade (S10 de `docs/findings.md`): toda linha resolve — o arquivo removido existe na tag, a seção de destino existe em `docs/findings.md`, a linha de `docs/future_work.md` existe em HEAD; 0 falhas |
| R4 | referências a caminhos removidos em arquivos VIVOS, depois do commit de remoção: 0 |
| R5 | todo `.py` mantido sob `research/` e `tools/` compila e tem seus imports locais resolvidos (AST: módulo local importado existe como arquivo mantido): 0 falhas |
| R6 | suíte (`-m "not browser"`) após a remoção: 0 falhas; diff de `cyclophaser/` no passo: vazio |
| R7 | digest default (gerador canônico) igual antes e depois da remoção, na mesma sessão |
| R8 | `verify_citations.py` após a remoção: 0 falhas (citações fixadas em hash) |

## Definições operacionais (fixadas aqui, antes de medir)

* **Arquivos vivos (R4):** `cyclophaser/`, `tests/`, `tools/`, `README.md`,
  `CLAUDE.md`, `docs/*.rst`, `research/labels/README.md`,
  `research/labels/swell_item30/README.md` e todo `.py` mantido sob `research/`.
  Fora do conjunto vivo (registros históricos): `docs/future_work.md`,
  `docs/findings.md`, `CHANGELOG.md`, `research/cleanup/`.
* **Referência viva (R4):** menção, num arquivo vivo, a um caminho da lista de
  remoção — o caminho completo a partir da raiz, ou, para um arquivo vivo no
  mesmo diretório, o caminho relativo a esse diretório (o nome do arquivo).
  **Não conta** como referência viva:
  * o nome de um arquivo que o próprio script mantido grava (`to_csv`,
    `write_text`, `write_bytes`, `savefig`, `json.dump`, `open(..., "w")`, ou uma
    constante atribuída na mesma linha e usada numa dessas chamadas), pois rodar
    o script o recria. Essas ocorrências são listadas à parte em
    `passo3/own_outputs.txt`, com `arquivo:linha`;
  * a forma `archive/research-diagnostics-pre-cleanup:<caminho>`, que resolve
    pela tag.
* **Correção de referência viva:** fora de `cyclophaser/`, reescrita para
  `archive/research-diagnostics-pre-cleanup:<caminho>` ou para a seção de
  `docs/findings.md`. Em `cyclophaser/`: PARE.
* **Import local (R5):** módulo cujo nome coincide com um `.py` rastreado no
  repositório antes da remoção; resolvido se existir um `.py` mantido com esse
  nome.
* **R7:** `research/labels/diagnostics/front_b/default_behaviour_hash.py` rodado
  com HEAD = commit 11 (árvore limpa) e depois sobre a árvore do commit 12, na
  mesma sessão; o registro anexado ao livro-razão é restaurado se o digest não
  mudar.
