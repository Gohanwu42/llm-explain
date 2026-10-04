# Test evidence

This report separates instruction-following, executable resources, packaging, and learning outcomes. Tests were performed on 2026-10-04. Limited samples do not establish a universal success rate.

## Behavior

The reproducible runner is `tests/behavior/run_eval.py`. It starts fresh, ephemeral Codex CLI sessions and records the next response. The final runs explicitly requested `gpt-6.1-sol` and record UTC start time and elapsed seconds; both control and guided runs used the same local runtime. The response API did not independently echo a model identifier, which is stated in each record. The runtime includes ordinary agent instructions, so this is a within-runtime comparison, not an isolated model benchmark.

| Check | Observation |
|---|---|
| Missing text strength, no skill, five matching runs | All five explained immediately without asking for a percentage. The explanations were mathematically correct; they did not implement the custom choice contract. |
| Missing text strength, skill supplied, five matching runs | All five asked for a user-selected 0–100% strength before explaining. |
| Eleven guided scenarios | Responses respected the tested choices, explicit parameters, same-run follow-up, new-run reset, invalid percentage, missing investment, absent video tools, and skipped understanding check. |
| 60%, 80%, and 100% text examples | Preserved the tank facts and boundaries. Wording and sentence structure varied. No formal compliance score or word-count benefit was inferred. |
| Independent end-to-end HTML application | The agent read the core, Production, HTML, and the HTML asset; it produced a real offline page in an isolated temporary directory. It did not load the text or video references. It reported browser limitations rather than claiming a visual pass. |

The eleven scenarios include a further missing-strength case, explicit 80%, 60%, 100%, invalid 130%, missing medium, same-run follow-up, new run, no video tools, missing investment, and a skipped check. All 21 final processes (five control, five guided, and eleven scenarios) exited successfully and their responses were inspected. An earlier same-run evaluation timed out once; the final 21 runs had no infrastructure errors. The timeout is not counted as a passed response.

Sanitized prompts, responses, and reported usage are retained under `tests/behavior/results/`. Token counts include the host runtime and are not estimates of the skill's isolated cost. No statistically meaningful cross-model comparison or real-learner study was conducted.

## Executable resources

| Resource | Performed checks |
|---|---|
| HTML | 18 Node tests: 12 execute the embedded calculation model; six run the shipped interface script with a small DOM boundary double. They cover the model, stable expanded slider ranges, reset/presets, operand precision, and approximate-result labels. The DOM double does not test native controls or visual layout. |
| Video helper | 27 Python tests cover validation, measured narration and cumulative SRT timing, actual media assembly, sub-frame narration, decoded video presence, output preservation, and filesystem publication races. Eleven require FFmpeg. |
| Release builder | Four Python tests cover the single portable root, development-file exclusion, reproducible bytes/checksum, missing files, symlinks, and unsafe version input. |

Initial tests were run before their corresponding implementations. The final full run passed all 31 Python tests with FFmpeg and no skips, plus all 18 Node tests.

An independent `gpt-6-astra` review identified issues that were fixed and covered by regression checks:

- Each narration segment must last at least one frame at the selected frame rate; one output frame is decoded before publication.
- Unsupported hard links fall back to exclusive file copies while preserving competing files.
- Expanded slider ranges remain stable until reset or a preset deliberately restores them.
- Visible equations preserve input precision and mark rounded results as approximate.
- Evaluation records include the requested model, UTC start time, and elapsed seconds.

### Package checks

The rebuilt `llm-explain-1.0.0.zip` contains 12 files in one portable skill root and is 27,104 bytes. A repeated build produced identical bytes. ZIP CRC checks and validation of the extracted skill passed. A public-file scan found no private paths or non-English documentation.

SHA-256: `b8f684a5e20f536a46a947a3572197728815961b349272c42fd89ccdf4d41c21`.

These are local package checks. Remote publication and download verification are separate release steps.

### Browser checks

The actual HTML was opened in Chrome from a local server. Checks included:

- Default: 30 L at 10 minutes; exactly full: 40 L at 20 minutes.
- A 30-minute request shows the last valid state at 20 minutes and labels the request outside the model.
- Balanced flows preserve 20 L; the draining preset reaches 0 L at 10 minutes.
- Empty elapsed time hides the calculation and shows a useful validation message.
- ArrowRight changes the time slider from 10 to 10.4 minutes and updates the output.
- After setting inflow to 100, ArrowLeft changes it to 99 while the slider maximum stays 100; End restores 100. Reset restores the standard range.
- Inflow 3.0004, outflow 3.0003, and 10,000 minutes display distinct operands and an approximate 21 L result.
- A 390-pixel viewport keeps the content readable without horizontal clipping; the temporary viewport override was reset.
- No browser console errors were observed in the checked interaction sequence.

Browser inspection caught an ambiguous time label. It was changed from “Time until full” to “Full at,” with the equivalent empty-tank label. The chart legend now identifies the last valid time for out-of-domain requests. Both changes were rechecked in the actual page.

The SVG was also opened and visually inspected: flow directions, 3/2/1 L-per-minute values, the 30 L state, formula, starting-level marker, and model boundary are consistent. Full keyboard navigation, screen-reader operation, and 320/375-pixel layouts were not tested. See the [UI checklist](../tests/ui-checklist.md) for the remaining checks.

### Narrated video smoke test

A three-scene, 18.888-second MP4 was produced with local speech narration, H.264 video at 960×540/24 fps, and an AAC audio stream. Full decoding succeeded. Audio was non-silent. Scene-level SRT boundaries were 0, 3.727, 9.058, and 18.888 seconds.

Chrome playback advanced normally, with readyState 4 and visible captions. Inspection found a caption overlapping a numeric label in the initial demo; the demo was regenerated and playback rechecked with a clear caption area. The helper provides scene-level captions, not word-level alignment. Automated audio checks and browser playback do not establish voice quality or listening comprehension.

See [video test details](../tests/video-smoke/README.md). FFmpeg 7.1 came from the `imageio-ffmpeg==0.6.0` PyPI wheel in temporary tooling. No FFmpeg binary or third-party Python package is bundled in the skill.

## Reproduce

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_explainer.mjs
LLM_EXPLAIN_FFMPEG=/path/to/ffmpeg python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/build_release.py --version 1.0.0
```

Without FFmpeg, 11 integration tests are explicitly skipped; the other Python tests still run. Behavioral evaluation requires an authenticated Codex CLI and consumes model usage:

```sh
python3 tests/behavior/run_eval.py --model gpt-6.1-sol --case missing-strength --repetitions 5 --baseline --output /tmp/llm-explain-control
python3 tests/behavior/run_eval.py --model gpt-6.1-sol --case missing-strength --repetitions 5 --output /tmp/llm-explain-guided
python3 tests/behavior/run_eval.py --model gpt-6.1-sol --case all --output /tmp/llm-explain-scenarios
```

## What remains unproven

- Reliability across other models, host environments, and arbitrary complex subjects.
- Durable learner understanding, retention, or an improvement in learning efficiency.
- Professional narration quality and high-end video aesthetics.

These are material limits on the claims, not failed packaging tests. The release is a tested workflow and set of reusable resources, not a guarantee of those outcomes.
