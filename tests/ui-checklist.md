# Interactive explainer verification

The 18 Node tests execute the embedded model and the shipped interface script. The interface tests use a small DOM boundary double; native control behavior and visual layout require a real browser. None of these checks establishes learner understanding.

## Automated model checks

- Initial RED run: 12 tests failed because the HTML did not yet expose a model.
- GREEN run after implementing the model: all 12 model tests passed. The final suite passed all 18 tests with `node --test tests/test_explainer.mjs`.
- The tests cover accumulation, equal flows, draining, zero time, exact and exceeded boundaries, starting at a boundary, decimal rounding at a boundary, a transfer example, invalid physical inputs, extreme finite flows, and unrepresentable boundary times.
- Six interface regressions cover stable expanded slider bounds, reset/preset bounds, near-equal and very small decimal operands, approximate-result labels, and full-precision boundary times.

## Real browser checks

The coordinating agent opened the actual HTML in Chrome from a local server on 2026-10-04. The following checks were performed:

- [x] Default: 30 L at 10 minutes, net +1 L/min, full at 20 minutes.
- [x] Elapsed time 20: 40 L and the full boundary. Elapsed time 30: an out-of-model request with the last valid state at 20 minutes and an explicit boundary note.
- [x] Balanced flows: 20 L. Draining preset: 0 L at 10 minutes.
- [x] Empty elapsed-time input: a useful validation message and the old calculation hidden.
- [x] ArrowRight on the time slider: 10 becomes 10.4 minutes and the output updates.
- [x] Inflow 100, then ArrowLeft: 99 with maximum still 100. End restores 100; reset restores the standard range.
- [x] Inflow 3.0004, outflow 3.0003, and 10,000 minutes: distinct equation operands and an approximate 21 L result.
- [x] At 390 px, content remains readable without horizontal clipping; the viewport override was reset.
- [x] No browser console errors in the checked interaction sequence.
- [x] SVG inspected visually: legible labels and connectors, correct 3/2/1 L-per-minute relationships, 30 L state, formula, starting-level marker, and model boundary.

## Remaining UI checks

Unchecked items are not passing claims. Automated model coverage does not replace these browser or assistive-technology checks.

- [ ] Open the HTML directly offline and verify operation without a local server.
- [ ] Check zero time, separate inflow/outflow changes, and a request after the empty boundary in the browser.
- [ ] Test negative input, recovery from invalid input, capacity 0, and starting water greater than capacity; confirm validation behavior in the browser.
- [ ] Inspect the full page at 375 px and 320 px for overflow, clipping, overlap, and readable figures.
- [ ] Complete the full keyboard-only flow with Tab, Shift+Tab, Enter, Space, and arrows; verify every control is reachable, focus is visible, and no focus trap exists.
- [ ] Open the optional question and test no choice, a wrong answer, 30 L, and reset.
- [ ] Test operation with a real screen reader.

## Interpretation limits

- Water is modeled only up to the first full/empty boundary. Overflow, changing pump rates, evaporation, and behavior after emptying are not simulated.
- The controls are native HTML controls and focus styles are provided, but screen-reader operation needs its own real assistive-technology test if that claim is required.
- No learner has answered the question as part of the model suite. Passing these checks does not establish improved comprehension or learning speed.
