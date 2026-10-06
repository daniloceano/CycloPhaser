# I2 — previsão (escrita antes de qualquer medição; não editar)

Data: 2026-10-05. Branch `feat/app-redesign`; base do I1 = 63f074f. Nenhum número
de tempo ou de contagem foi medido antes deste arquivo ser escrito.

## O que será medido

Calibrate com os 51 tracks de amostra carregados ("Load all test cyclones" no I1;
"Sample data (51 TRACK cyclones)" no I2), Grid com o número de colunas padrão (2),
Chromium, viewport 1600×1000. Interação: mudar o slider "High cutoff (hours)" com a
seta do teclado, 5 vezes seguidas, sempre para um valor ainda não visto na sessão
(18→19→…→23), para que cada passo seja falta de cache de verdade.

Para cada passo, duas grandezas:

- **gerações de PNG**: chamadas a `matplotlib.figure.Figure.savefig` durante a
  interação, agrupadas pela função do app que chamou (`_render_periods_png`,
  `_render_compact_png`, …). Contadas por um lançador de medição que envolve
  `Figure.savefig` antes de o script rodar; o código do app não muda para medir.
  Acerto de cache não chega ao `savefig`, então não conta.
- **tempo no servidor**: soma da duração das execuções do script causadas pelo
  passo (lançador em volta de `ScriptRunner._run_script`, como no I1).

Medido em 63f074f (I1) e na árvore do I2, mesmo ambiente.

## Previsão (a da frente, literal)

> No I2, as figuras do pacote de exportação deixam de ser geradas a cada mudança
> (só as da tela), e o tempo cai.

Operacionalização, fixada aqui:

- I1: cerca de **102** gerações por passo: 51 do pacote de exportação (12×5,
  geradas no laço de pré-processamento a cada execução) + 51 da tela (Grid de 2
  colunas, outro tamanho).
- I2: **51** gerações por passo, todas da tela; **0** vindas da exportação. As
  figuras do pacote só são geradas quando o usuário pede em Save results.
- "o tempo cai": mediana do tempo no servidor no I2 < mediana no I1. Expectativa
  minha, não da frente: I2 ≤ 0,75 × I1.

Registro como observação. Não é critério de aprovação do portão.
