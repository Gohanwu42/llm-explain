# Interactive HTML explanations

Make interaction answer a learning question: change a cause and observe its effect, compare alternatives, reveal a step, or test a prediction. Every control must change meaningful content.

Use the supplied [offline explainer](../assets/explainer.html) as a tested starting point when its structure fits. It is a complete water-tank example, with an explicit model boundary. Adapt content and logic together. Keep the design consistent without imposing a named style on every learner.

## Build

1. Start with a visible answer. Put the central relationship and one useful interaction near it. Reveal derivation and extra detail progressively.
2. Separate content, model calculations, and presentation within the file. Use existing suitable components before adding dependencies. A single offline file is preferred when it meets the goal; it is not a restriction on richer authorized work.
3. Make labels, units, input bounds, error states, and assumptions explicit. Provide useful content before interaction. Use native controls, visible focus, readable contrast, and reduced-motion support.
4. In polished mode, show one working representative interaction for direction approval. Carry the approved typography, spacing, color, and hierarchy through the whole artifact.

## Verify in a browser

- Open the actual output, then operate the main control at typical and boundary values. Compare outputs to independently calculated expectations.
- Test empty, invalid, and out-of-range input where the interface accepts it. The model must state when its assumptions stop applying.
- Check desktop and a narrow viewport. Inspect labels, overflow, text size, and keyboard operation. Reset temporary viewport changes afterward.
- Check browser errors and local/external dependencies. A source inspection alone is not a browser check.
- If browser execution cannot be performed, identify the unverified interactions instead of claiming they work.

Deliver the working page and source. Publishing or adding analytics is a separate user-authorized action. The starter makes no network requests and needs no build step.
