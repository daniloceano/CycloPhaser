# Item 30 — label × params-13 × params-14 × counterfactual (TRAIN only)

Diagnostic for Danilo's review of his own labels. **The counterfactual is not a rule proposal.** It uses params-14: s5 with [0, E.start) written as incipient when E exists and c3 = 1, and otherwise s6. Figures are in `figs_cf/`, one per case, plus `board_8_cases.png`.

* P controls, the two largest c3 in P (part 2's table): 20180608, 20150436.
* params-13 vs params-14, final map: identical in all 8 cases.
* Counterfactual == s6 in 20180608 (yes), 20150436 (yes), 19790612 (yes).
* **Incipient end** follows the label's convention: the start of the phase after a leading incipient run. A map that does not open in incipient ends it at step 0 (a counterfactual with E.start = 0 writes no incipient at all). The column gives label / params-14 / counterfactual, then |p14 − label| → |cf − label|.
* **Sequence** is compared by edit distance to the label's sequence (phases inserted, removed or substituted), params-14 → counterfactual. 0 = identical.
* 'closer' / 'further' / 'same' compare the counterfactual's distance with params-14's, per column.

| id | group | c3 | label sequence | params-14 sequence | counterfactual sequence | incipient end (label / p14 / cf; distance) | sequence edit distance |
|---|---|---|---|---|---|---|---|
| 20120297 | L | 1 | incipient > intensification > mature > decay > residual | incipient > decay > residual | intensification > mature > decay > residual | 2 / 10 / 0; 8 → 2 **closer** | 2 → 1 **closer** |
| 19940445 | L | 1 | incipient > intensification > mature > decay > intensification > mature > decay | incipient > decay | intensification > mature > decay | 8 / 38 / 0; 30 → 8 **closer** | 5 → 4 **closer** |
| 19810854 | L | 1 | incipient > intensification > mature > decay | incipient > decay | intensification > mature > decay | 3 / 62 / 0; 59 → 3 **closer** | 2 → 1 **closer** |
| 19790612 | K | — | incipient > decay | incipient > decay | incipient > decay | 13 / 15 / 15; 2 → 2 **same** | 0 → 0 **same** |
| 19860380 | K | 1 | incipient > decay | incipient > mature > decay | intensification > mature > decay | 14 / 12 / 0; 2 → 14 **further** | 1 → 2 **further** |
| 19870927 | K | 1 | incipient > decay | incipient > mature > decay | incipient > intensification > mature > decay > intensification > mature > decay | 64 / 66 / 8; 2 → 56 **further** | 1 → 5 **further** |
| 20180608 | P | 0.529 | incipient > intensification > mature > decay | incipient > intensification > mature > decay | incipient > intensification > mature > decay | 37 / 38 / 38; 1 → 1 **same** | 0 → 0 **same** |
| 20150436 | P | 0.345 | incipient > intensification > mature > decay | incipient > intensification > mature > decay | incipient > intensification > mature > decay | 16 / 20 / 20; 4 → 4 **same** | 0 → 0 **same** |
