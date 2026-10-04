# Text and language strength

The learner's percentage controls **language constraint strength inspired by ASD-STE100**. It is not a compliance score, factual compression ratio, reading age, or guarantee of fewer words. Do not claim certified or complete ASD-STE100 compliance. This skill includes no proprietary standard dictionary.

Accept any number from 0 through 100. Use intermediate values as intermediate strength; do not silently round to a preset. If the value is invalid or genuinely ambiguous, ask for a valid percentage. Keep facts, conditions, uncertainty, and necessary depth at every strength.

| Anchor | Observable writing behavior |
|---|---|
| 0% | Natural, clear language without added STE-inspired constraints. |
| 60% | Stable terminology and active voice; allow natural compound sentences, useful modifiers, and connected narration. |
| 80% | Prefer one short statement per sentence; explicit subjects and relationships; split nested conditions; minimize parenthetical interruptions and synonym changes. |
| 100% | Apply direct sentences, explicit relationships, and stable terms as strongly as readability and accuracy allow. This remains an informal style setting. |

## Output shape

- Begin with the answer and a short overview. Explain afterward.
- Use Markdown and blank lines between paragraphs. Give each paragraph one point and a bold opening sentence that states it.
- Use bullets for parallel points, numbers for steps, and tables for comparisons. Preserve the connection between steps in reasoning.
- End paragraphs with a useful closure or transition. End the response with the key relationship; merge redundant openings and recaps in short answers.
- Put essential conditions beside the claim they qualify. Define necessary technical terms once and use them consistently.
- Adapt syntax to the language. For Chinese, use explicit semantic units and appropriate Chinese punctuation instead of importing English word-count limits. Honor explicit user preferences.

## Calibration: the same bounded model

Facts: a tank starts with 20 L, holds 40 L, receives 3 L/min, and drains 2 L/min. Rates are constant; ignore other losses. The model ends when the tank first becomes full or empty.

### 60%

**The tank gains 1 liter each minute, so it becomes full after 20 minutes.** It starts with 20 liters and holds 40; although 3 liters enter each minute, 2 liters also leave, giving a net gain of 1 liter per minute.

- After 10 minutes: 20 + (3 − 2) × 10 = 30 liters.
- After 20 minutes: 20 + (3 − 2) × 20 = 40 liters, exactly full.

**The difference between inflow and outflow determines the change in stored water.** These calculations assume constant rates and no other losses, and apply only until the tank first becomes full or empty.

### 80%

**The tank gains 1 liter each minute and becomes full after 20 minutes.** It starts with 20 liters. It holds 40 liters.

- Each minute, 3 liters enter and 2 liters leave.
- Net gain: 3 − 2 = 1 liter per minute.
- After 10 minutes: 20 + 1 × 10 = 30 liters.
- After 20 minutes: 20 + 1 × 20 = 40 liters. The tank is full.

**The change in stored water depends on inflow minus outflow.** The rates stay constant. There are no other losses. The model ends when the tank first becomes full or empty.

The examples illustrate the intended difference; they are not a sentence-level percentage calculation. Check that both versions preserve the same facts and boundaries.
