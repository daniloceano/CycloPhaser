# I3 — previsão (escrita, commitada e enviada antes de qualquer medição; não editar)

Data: 2026-10-06. Branch `feat/app-redesign`; base do I2 = 6016486. Nenhum número
de tempo ou de contagem do I3 foi medido antes deste arquivo ser commitado e
enviado. O único número citado, os 13,2 s, é o do I2, medido no próprio I2.

## O que será medido

O mesmo procedimento do I2 (`research/app_redesign/i2/measure_slider.py`), copiado
para `research/app_redesign/i3/measure_slider.py` com três variantes:

- `i2`: árvore em 6016486 (checkout separado);
- `i3`: árvore do I3, estatísticas ligadas;
- `i3_nostats`: árvore do I3 com a função que desenha o bloco de estatísticas
  trocada por uma que não faz nada. A troca é feita pelo LANÇADOR de medição; o
  código do app não muda para medir. Isso só é possível porque o bloco de
  estatísticas fica numa função de um módulo próprio, chamada uma vez por
  execução.

Em todas: Chromium, viewport 1600×1000, env conda `cyclophaser` (streamlit
1.63.0). Calibrate com os 51 tracks de amostra ("Sample data (51 TRACK
cyclones)"), modo Grid, 2 colunas (padrão), página 1, tamanho de página 12
(padrão do I3). Interação: 5 × seta para a direita no slider "High cutoff
(hours)" (18→19→…→23), sempre valores novos, para que cada passo seja falta de
cache de verdade.

Por passo:

- **gerações de PNG**: chamadas a `Figure.savefig`, agrupadas pela função do app
  que chamou (como no I2);
- **chamadas de detecção**: chamadas a `cyclophaser.determine_periods.get_periods`
  durante o passo (o lançador envolve a função antes de o app importá-la);
- **tempo no servidor**: soma das execuções do script causadas pelo passo;
- só em `i3`: **tempo do bloco de estatísticas**, medido em volta da função que o
  desenha.

## Previsão

A da frente, literal:

> 12 figuras em vez de 51, e o tempo cai em relação aos 13,2 s do I2.

Operacionalização, fixada aqui:

1. Figuras por passo: `i2` = **51**; `i3` = **12**, todas de `_render_periods_png`.
   `i3_nostats` = 12 também.
2. Chamadas de detecção por passo: **51** nas três variantes. A detecção continua
   rodando para todos os ciclones, e as estatísticas não fazem nenhuma chamada
   extra.
3. "O tempo cai": mediana no servidor de `i3` < mediana de `i2`, medidas na mesma
   sessão. Expectativa minha, não da frente: `i3` ≤ 0,6 × `i2`.
4. Custo das estatísticas (observação). Expectativa minha: o tempo do bloco é
   ≤ 0,5 s por passo e < 10 % da mediana de `i3`. A diferença de medianas
   `i3` − `i3_nostats` fica do mesmo tamanho, dentro do ruído entre passos.

Isto é uma observação e não é critério de aprovação do portão.
