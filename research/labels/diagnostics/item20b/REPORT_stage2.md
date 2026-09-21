# Front 20(b), stage 2 — `mature_min_depth`, a depth floor on mature detection

Stage 1 (commit `eb19304`) measured that valley depth **cannot** separate true
from spurious mature blocks across the 35 real train series, and **can**
separate them cleanly inside `20160735`. Stage 2 implements the floor anyway,
at the fixed value 0.80 the brief specifies, and measures what it does.

**Gate verdict at 0.80: PASS on (a)–(f).**

Two things in §7 and §8 qualify how far that result travels, and neither is a
gate criterion: the margin protecting the one true valley that is not its
series' minimum rests on a single sample, and `20205386`'s two spurious blocks
survive the floor untouched.

---

## 1. Provenance

| | |
|---|---|
| branch | `research/item20b-depth-rule` (continues `eb19304`) |
| environment | conda env `cyclophaser`, `/Users/danilocoutodesouza/miniconda3/envs/cyclophaser/bin/python` |
| numpy | **2.5.3** |
| scipy | **1.18.0** |
| pandas | 3.0.5 / python 3.12.14 |
| reference config | `cyclophaser_params-11.yaml`, sha256 `24dd7f22…abe420` — **unmodified**, re-verified |
| new config | `cyclophaser_params-12.yaml`, sha256 **`39262f45785eea00d19e4165d6f52b6a77cabfcf56e14514a0cea2e3c67ebec3`** |
| scope | TRAIN split only: 35 real + 12 synthetic = 47. `read_split()["test"]` is never read. |

`params-12` is `params-11` plus one line (`mature_min_depth: 0.8`) and a fresh
`metadata.timestamp`. Nothing else differs; `diff` confirms exactly those two
lines.

---

## 2. What was implemented

A new `mature_min_depth` float in `[0, 1]`. A z-valley may generate a mature
block only if its normalised depth

```
D1 = (z_max - z[valley]) / (z_max - z_min)
```

on the series' own `df['z']` is at least that value — 1.0 at the series
minimum, 0.0 at its maximum.

**The rule lives entirely in `find_stages.find_mature_stage`**, as a filter on
the `z_valleys` list before the loop that builds windows. It does not touch the
extrema filter, `prominence_relative`, or any other phase. Nothing in the added
code writes to `z` or `z_peaks_valleys`, so intensification, decay, residual and
incipient see byte-identical input.

D1 is computed per valley rather than by normalising the series — arithmetically
identical, and it keeps the package from carrying a normalised copy of `z` that
other phases might later read.

**It applies to both `mature_method` values.** Eligibility of a valley is a
separate question from how the window around it is sized, and the default makes
this free.

**It is not a cap on the number of matures.** Every valley clearing the floor
still emits its own block — deliberately, since a cyclone can have more than one
mature stage.

**Guard.** If `z_max - z_min` is zero or non-finite the series has no depth
scale and D1 is undefined. The floor is skipped for that series and a
`UserWarning` says so. It is not silently ignored. **Triggered on 0 of 47
series**, at both 0.80 and 0.85.

### One unavoidable departure from the brief, stated plainly

The brief says not to touch `determine_periods.py`. **The rule does not touch
it, but the parameter had to.** `get_periods` takes no `**kwargs` and builds its
`args_periods` dict from an explicit literal, and every calibration driver
filters `phase_params` against `inspect.signature(get_periods).parameters`. With
no signature entry, `mature_min_depth` would be dropped before it ever reached
`find_mature_stage` and `params-12` would silently behave as `params-11`.

The change in `determine_periods.py` is therefore **plumbing only**: one
signature default, one `args_periods` entry, one docstring block, in each of
`get_periods` and the `determine_periods` wrapper. No logic. The rule's
behaviour is defined entirely in `find_stages.py`, as instructed.

The calibration app also had to declare the parameter — the suite enforces this
(`tests/test_sidebar_coverage.py::test_every_public_parameter_is_declared`
failed until it did). See §9.

---

## 3. Proof that the default changes nothing

`default_equivalence.py` hashes the **whole `periods` column, step by step**, of
all 47 train series — not a summary statistic, which could coincide while the
series differ. Run on this branch and on a clean `develop-v2.1` worktree
(import path asserted to resolve to the worktree, so the branch's code cannot
shadow it).

| configuration | `develop-v2.1` | this branch |
|---|---|---|
| **A** package defaults | `b01b16b6a86498d18509a0f3bcdac4c5a448615ae86a92c71899ed78aafc752f` | **identical** |
| **B** params-11 (key absent → default 0.0) | `b65551009bb0363bbf20ebc48075088cebf44b7e09286d566cad2269a64054d2` | **identical** |
| **C** params-11 + explicit `mature_min_depth=0.0` | `TypeError` (parameter does not exist there) | `b65551009b…` — equal to B |
| **D** params-12 (`0.80`) | n/a | `ee9541d3c675568c25d4386ac71901983f06ea5bb6631c2130ec4e8c1d233b59` — differs, as intended |

A and B are byte-identical across the two trees. C shows an explicit `0.0` and an
absent key are the same thing. The `TypeError` in C on `develop-v2.1` is itself
confirmation the parameter genuinely did not exist before.

---

## 4. The gate at `mature_min_depth = 0.80`

### (a) `20160735` reduces to one block — **PASS**

```
before  [(7, 11), (53, 64), (150, 181), (224, 235)]   durations 5, 12, 32, 12
after   [(150, 181)]                                  duration  32
label   [(145, 177)]                                  duration  33
```

All three spurious blocks gone, the 32-step block kept. Figure:
`fig_20160735_before_after.png`.

### (b) `20203947` keeps both labelled matures — **PASS**

```
labelled 122-144           -> detected by (129, 136)
labelled 178-188 [UNSURE]  -> detected by (181, 188)
blocks   before [(58,63), (87,93), (129,136), (181,188)]  ->  after [(129,136), (181,188)]
```

Both survive; the two spurious blocks (D1 0.4016 and 0.4860) are removed. The
floor removed blocks from a multi-mature series **without** collapsing it to a
single mature, which is the property the rule was built to preserve.

### (c) Sequence does not regress — **PASS**

**31/47**, against a base of 30/47 and a floor of 30.

* gained: `20170794`
* lost: none

### (d) Synthetics hold — **PASS**

**Synthetic sequence 12/12** (base 12/12) — this is the gate quantity.

Minimum D1 over all synthetic generating valleys: **0.9922**, so all 12 are
comfortably above 0.80 and the floor is inert on them, exactly as stage 1
predicted from the 0.992–1.000 range.

*Instrument note.* The synthetic **mature-boundary ±6** metric is 11/12 — but it
is 11/12 at **baseline too**, and its single miss is `s0596ea57`, which has no
labelled mature *and* no detected mature, so it is vacuously unmatched rather
than failed. That number is unchanged by the floor. It is recorded here because
"12/12" and "11/12" are two different instruments on the same 12 series and
confusing them would misreport the gate.

### (e) Mature boundary holds, incipient untouched, no displacement — **PASS**

* mature boundary **38/47** (base 38/47, floor 38). Gained: none. Lost: none.
* incipient boundary changed on **NONE** of the 47 series.
* **`20205386` explicit check:**

```
paired block   before (60, 63) from valley 61   ->   after (60, 63) from valley 61
all blocks     before [(36,42), (60,63), (80,85)]  ->  after [(36,42), (60,63), (80,85)]
```

The mature stays on valley 61 and does **not** migrate to the deeper spurious
valley 82. The item-20 gate hole — displacement without disappearance — is
checked directly and is not present. Figure: `fig_20205386_before_after.png`.

Note what this also means: **`20205386` is completely unchanged by the floor.**
All three of its valleys (D1 0.8687, 0.8805, 1.0000) clear 0.80, so both of its
spurious blocks survive. The rule does not fix the series stage 1 identified as
the one that refuses depth. It was never going to — that is the stage 1 result,
restated here so the PASS is not read as more than it is.

### (f) No new crash, latent defects quiet — **PASS**

* Full suite, browser tests excluded: **1205 passed, 0 failed.**
* `:152` (loud `IndexError`) fired **0** times; `:160` (silent wrong window)
  fired **0** times. Checked **actively**, by recomputing `amp_prev < 0` /
  `amp_next < 0` for every valley on all 47 series, at 0.80 and at 0.85 — not by
  absence of an exception, which proves nothing for the silent one.
* z-range guard triggered on 0 series.

Neither defect was fixed; both remain latent.

### Gate verdict

| | (a) | (b) | (c) | (d) | (e) | (f) |
|---|---|---|---|---|---|---|
| **0.80** | PASS | PASS | PASS | PASS | PASS | PASS |

**PASS.**

---

## 5. Extra measurement 1 — what filled each removed block

Five series lose a block. For each, what occupies the vacated range afterwards,
and whether the series matched the label before and after:

| series | removed block | now occupied by | label match | sequence |
|---|---|---|---|---|
| `20160735` | 7–11 (5) | intensification 0–8 / decay 9–21 | True → True | False → False |
| `20160735` | 53–64 (12) | intensification 22–58 / decay 59–121 | True → True | False → False |
| `20160735` | 224–235 (12) | **residual 211–258** | True → True | False → False |
| `20170794` | 159–167 (9) | **residual 119–223** | True → True | **False → True** |
| `20191014` | 134–140 (7) | intensification 124–136 / decay 137–205 | False → False | False → False |
| `20203947` | 58–63 (6) | intensification 12–60 / decay 61–74 | False → False | False → False |
| `20203947` | 87–93 (7) | intensification 75–89 / decay 90–106 | False → False | False → False |

**No series lost a label match or a sequence match.** One gained a sequence
match (`20170794`). This was the brief's predicted failure mode — fill-in
breaking a series that already matched — and it did not occur.

The fill-in is of two kinds: the neighbouring intensification and decay simply
close over the gap (5 of 7 blocks), or the vacated range becomes **residual**
(2 of 7). The residual outcome is worth flagging: in `20160735` the whole tail
211–258 is now residual where it previously held an intensification / mature /
decay cycle. That is a real change in how the end of that track is described,
even though it costs nothing on either metric here.

### Defect H watch

`find_incipient_period` overwrites `df.iloc[:boundary]` **unconditionally**
(`find_stages.py:982` on `develop-v2.1`), so a correct-looking phase map can be
the overwrite rather than the detector's own output. Checked explicitly for
every removed block:

```
20160735  incipient boundary None -> None   blocks 7-11, 53-64, 224-235
20170794  incipient boundary None -> None   block 159-167
20191014  incipient boundary 9    -> 9      block 134-140
20203947  incipient boundary 12   -> 12     blocks 58-63, 87-93
```

The incipient overwrite reaches index 9 and 12 in the two series that have one
at all; the earliest removed block starts at 7 in a series whose overwrite is
`None`. **No removed block is touched by the overwrite**, so every fill-in in
the table above is the detector's own output, not defect H masking it. The
incipient boundary is also unchanged on all 47 series, so the defect's input did
not move either.

---

## 6. Extra measurement 2 — is D1's denominator robust?

`z_max` is a single sample. If it is an isolated spike, every D1 in that series
is governed by one point.

Gap `= (z_max − 2nd highest surviving peak) / (z_max − z_min)` over the 35 real
series: **min 0.0052, median 0.3035, max 0.9897**. Nineteen series exceed 0.30.
The most extreme: `20181046` (0.9897), `20171179` (0.8977), `20180263` (0.7593),
`20180170` (0.6853), `20170760` (0.6597), `20190397` (0.6556).

**That figure alone overstates the exposure, and the reason matters.** 30 of the
32 TRUE generating valleys sit at **D1 = 1.0000 exactly** — they *are* the series
minimum, so their D1 is 1 for any finite denominator. A spiky `z_max` cannot
change their verdict. The denominator can only flip a verdict for valleys near
the floor.

Recomputing those with the 2nd highest surviving peak as `z_max` — a
deliberately adverse counterfactual, not a proposed definition:

| series | valley | D1 | D1 (adverse) | shift | gap | verdict at 0.80 |
|---|---|---|---|---|---|---|
| 20160735 | 9 | 0.3833 | 0.3336 | −0.0497 | 0.0746 | cut → cut |
| 20203947 | 61 | 0.4016 | 0.3494 | −0.0522 | 0.0803 | cut → cut |
| 20203947 | 90 | 0.4860 | 0.4411 | −0.0449 | 0.0803 | cut → cut |
| 20160735 | 228 | 0.5133 | 0.4741 | −0.0392 | 0.0746 | cut → cut |
| 20170794 | 163 | 0.6065 | 0.5956 | −0.0108 | 0.0268 | cut → cut |
| 20191014 | 137 | 0.6421 | 0.5252 | −0.1169 | 0.2463 | cut → cut |
| 20160735 | 59 | 0.7077 | 0.6841 | −0.0236 | 0.0746 | cut → cut |
| 20150656 | 143 | 0.8351 | 0.7066 | −0.1285 | 0.4379 | **KEPT → cut** |
| 20205386 | 41 | 0.8687 | 0.7439 | −0.1248 | 0.4874 | **KEPT → cut** |
| **20205386** | **61** | **0.8805** | **0.7669** | **−0.1136** | **0.4874** | **KEPT → cut** |
| 20180733 | 37 | 0.9303 | 0.8999 | −0.0304 | 0.3035 | KEPT → KEPT |
| 20203947 | 185 | 0.9422 | 0.9372 | −0.0050 | 0.0803 | KEPT → KEPT |
| 20180628 | 72 | 0.9980 | 0.9969 | −0.0011 | 0.3505 | KEPT → KEPT |

**`20205386` valley 61 is the exposure.** It is the one TRUE valley closest to
the floor, it is the one true valley that is not its series' minimum, and its
series has a gap of 0.4874 — `z_max` sits nearly half the dynamic range above the
next peak. Under the adverse denominator its D1 falls to 0.7669 and it would be
**cut**, which would lose a true mature.

`20160735`'s three spurious valleys, by contrast, are cut under either
denominator, and their series' gap is small (0.0746). The case the rule was
built for is denominator-insensitive; the case that constrains the floor is not.

The gate is measured on the real `z_max` and passes. This is a statement about
how much slack the 0.08 margin actually has — it is propped up by one sample in
the one series where it matters.

---

## 7. Extra measurement 3 — sensitivity at 0.85

Run as a **diagnostic**, not a candidate. No recommendation is made and no
threshold was swept: exactly the two values the brief names were run.

| criterion | **0.80** (params-12) | **0.85** (diagnostic) |
|---|---|---|
| (a) `20160735` | `[(150,181)]`, 32 steps — **PASS** | `[(150,181)]`, 32 steps — **PASS** |
| (b) `20203947` | both kept — **PASS** | both kept — **PASS** |
| (c) sequence | **31**/47 (gained `20170794`) — PASS | **32**/47 (gained `20150656`, `20170794`) — PASS |
| (d) synthetics | 12/12 seq, min D1 0.9922 — PASS | 12/12 seq, min D1 0.9922 — PASS |
| (e) mature boundary | 38/47, incipient unchanged, `20205386` on valley 61 — PASS | 38/47, incipient unchanged, `20205386` on valley 61 — PASS |
| (f) defects `:152`/`:160` | 0 / 0 — PASS | 0 / 0 — PASS |
| **gate** | **PASS** | **PASS** |

Both pass. 0.85 additionally removes `20150656` v143 (D1 = 0.8351), which buys
one more sequence match.

The trade, stated without a recommendation: 0.85 scores one sequence higher, and
leaves the shallowest true valley (`20205386` v61 at 0.8805) a margin of 0.0305
instead of 0.0805. Under the adverse denominator of §6 that valley is cut at
either floor, so §6's exposure is not what distinguishes them. **The choice
between 0.80 and 0.85 is Danilo's.** `params-12` carries 0.80, as the brief
specifies.

---

## 8. Prohibitions — verified, not assumed

| | |
|---|---|
| threshold sweep | none. Two values run, both named in the brief. No grid, no optimisation. |
| `:152` / `:160` fixed | no — watched by active recomputation, fired 0 times |
| `item19_core.py` | **untouched** — `git diff develop-v2.1` empty; not imported by any stage-2 file |
| `params-11.yaml` | **untouched** — sha256 still `24dd7f22…abe420` |
| test split | never read |
| merge / PR | none. Branch pushed only. |

### Scope of the package diff

| file | why |
|---|---|
| `cyclophaser/find_stages.py` | **the rule** — valley filter, validation, guard, docstring |
| `cyclophaser/determine_periods.py` | **plumbing only** — signature default, `args_periods` entry, docstrings, in `get_periods` and the `determine_periods` wrapper. No logic. See §2. |
| `CHANGELOG.md` | the parameter, documented |
| `tools/calibration_app/app.py` | required by the suite — see §9 |

---

## 9. The calibration app

`tests/test_sidebar_coverage.py::test_every_public_parameter_is_declared`
asserts the sidebar covers the package signature **exactly, in both directions**.
Adding a public parameter failed it until the app declared one:

```
AssertionError: undeclared parameters: ['mature_min_depth']
```

The app now carries a `Mature minimum depth` slider (unconditional — unlike
`mature_amplitude_fraction`, which is hidden under
`mature_method='derivative'` — because the floor applies to both methods),
a default of 0.00, and the parameter is passed to the detector and exported to
YAML.

On import the key is **applied when present but not reported missing when
absent**. That needed an explicit subtraction: `_REQUIRED_PHASE_YAML_KEYS` is
derived from `_YAML_PHASE_MAP`, and a key must be in that map to be applied at
all, so membership of `_OPTIONAL_PHASE_YAML_KEYS` alone (which only suppresses
the "unknown key" warning) would have made every pre-existing config report a
missing key. `params-1` … `params-11` all predate the parameter and import
clean; `params-12`'s `0.8` is applied.

Suite after the app change: **1205 passed, 0 failed.**

---

## 10. The declared prediction, against the result

Declared before measuring, reported without reinterpretation:

> (a) PASS, (b) PASS, (d) PASS, (e) 38/47 held exactly and `20205386` without
> displacement, (c) sequence rises from 30 to 31 or 32 with `20160735` entering.
> ~65% probability of global PASS. Most likely failure mode: not the threshold,
> but (c) or (e) breaking through the fill-in of the vacated stretch in some
> series that already matches.

**(a), (b), (d), (e) — correct**, including 38/47 exactly and `20205386` staying
on valley 61.

**(c) — correct on the number, wrong on which series.** Sequence rose 30 → 31,
inside the predicted range. But the series that entered is **`20170794`**, not
`20160735`. `20160735` still fails its sequence after the fix: its four blocks
became one correctly-placed block, and the sequence still does not match the
label. Removing the spurious matures was necessary but not sufficient for that
series — which was the stated motivation for the whole front, so it is worth
being explicit that the motivating case is still not matching on sequence.

**The predicted failure mode did not occur.** No series lost a label match or a
sequence match to fill-in (§5).

---

## 11. Status

Gate **PASS** at 0.80 on (a)–(f). Implemented, measured, committed and pushed on
`research/item20b-depth-rule`.

**Not merged. No PR.** Merging requires Danilo's explicit written authorisation,
per front. Two open questions are his to decide: whether to merge at all given
that the floor does not help `20205386` and `20160735` still misses its
sequence, and whether the floor should be 0.80 or 0.85.
