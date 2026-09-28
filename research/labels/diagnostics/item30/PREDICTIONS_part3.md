# Item 30, parte 3 — regra opt-in e params-15: previsões (registradas 2026-09-27T15:05:32Z, antes de qualquer implementação ou medição)

Texto recebido, sem alteração:

R1 treino (42 reais + 12 sintéticas): a regra muda o mapa final em
   exatamente 20120297, 19940445, 19810854, 19860380, 19870927 e em
   nenhuma outra; nessas 5, o mapa final == contrafactual de 1a3ad76.
R2 regra desligada (padrão): saída byte-idêntica (hash de comportamento
   padrão com o gerador canônico front_b/default_behaviour_hash.py,
   baseline e alterado na MESMA sessão).
R3 swell 196: a regra muda exatamente 10 tracks (8 ruins com padrão +
   19810854 + 19861089); só a contagem é reportada.
R4 nas 49 séries de treino NÃO adjudicadas, o escore de params-15 é
   idêntico ao de params-14 (consequência de R1).
V  validação (5 casos, rótulos novos de Danilo, se ele rotular): distância
   de sequência params-15 ≤ params-14 em 5/5 e < em ≥ 3/5. Medido depois.
   Se Danilo não rotular, params-15 só pode ser adotado registrado como
   "adotado sem validação independente".
