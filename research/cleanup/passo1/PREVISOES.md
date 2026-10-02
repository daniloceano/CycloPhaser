# Passo 1 — previsões declaradas ANTES de qualquer medição deste passo

Copiadas do prompt do Passo 1 (2026-09-28), sem ajuste. Versionadas no commit do
manifesto (commit 2 da frente), que precede todo commit e toda medição do C1: a
ordem é verificável por `git log`.

| id | previsão |
|---|---|
| P1 | digest default (gerador canônico `research/labels/diagnostics/front_b/default_behaviour_hash.py`) muda: pré-C1 = `3a6de265…`, pós-C1 ≠ `3a6de265…`, ambos medidos nesta sessão |
| P2 | sha256 do arquivo renomeado (`cyclophaser_params-track.yaml`) = sha256 de `cyclophaser_params-15.yaml` antes do renome (idêntico byte a byte) |
| P3 | higiene nas séries de treino: 0 exceções; todas com sequência de fases válida |
| P4 | séries de treino que recusam incipient: 0 sob o novo default (`reflect`) |
| P5 | número de mapas de fase de treino que mudam entre o default novo e `boundary_padding='edge'`: > 0 (sem valor previsto) |
| P6 | suíte pós-C1 (`-m "not browser"`): 0 falhas |

Definições operacionais (fixadas aqui, antes de medir; implementadas em
`passo1/hygiene_train.py`):

* **séries de treino** = ids em `train:` de `research/labels/split.yaml` mais os
  `train:` de cada bloco em `batches:`; só esses arquivos são lidos.
* **sequência válida** = sem exceção; coluna `periods` do mesmo comprimento da
  série, sem nulos; todo rótulo, sem a numeração, em
  {incipient, intensification, mature, decay, residual}.
* **recusa de incipient** = o mapa final não começa em `incipient` (corrida
  inicial de `incipient` em t0 de comprimento 0).
