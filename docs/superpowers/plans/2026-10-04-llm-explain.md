# LLM Explain Implementation Plan

> **For agentic workers:** Use the approved specification, implement each task, and preserve test evidence. The user authorized continuous implementation, independent testing, GitHub publication, and a downloadable release on 2026-10-04. That instruction replaces further plan approval checkpoints.

**Goal:** Ship an English, portable explanation skill with four media, user-controlled investment, tested reusable resources, and an accessible GitHub download.

**Architecture:** A concise `SKILL.md` routes to four on-demand references. Original HTML/SVG examples and an optional video assembly helper make production concrete without requiring tools for the text path. Development tests and reports stay outside the installable ZIP.

**Tech Stack:** Markdown, YAML, standalone HTML/CSS/JavaScript, SVG, Python standard library; FFmpeg is optional for video assembly.

**Spec:** `docs/superpowers/specs/2026-10-04-llm-explain-design.md`.

## Global Constraints

- All published instructions, UI metadata, documentation, and examples are English.
- New runs require an explicit medium; text requires a user-selected 0–100% strength, other media require lightweight or polished. Reuse explicit values; same-run repairs keep settings.
- Video requires user selection. Polished work needs a real-content preview unless the user already explicitly waives it.
- Preserve correctness, conditions, and learning depth at all production levels.
- Default production scope: one complete direction, at most one preview revision, at most two local repair cycles. User instructions take precedence.
- State actual tool limitations and actual tests; do not infer comprehension from skipped checks.
- Do not publish private conversation material, local paths, credentials, or unrelated files.

## Review Focus

1. Missing configuration must lead to a concise question, not a silently assumed percentage or tier.
2. Prior-run settings must not leak into a new learning task; same-run follow-ups must not repeat intake.
3. Unavailable video/rendering tools must not produce a false completion claim.
4. HTML model boundaries, narrow screens, keyboard use, and arbitrary numeric input must work.
5. Release ZIP must preserve a single portable skill root, resolve references, and omit development/private files.

## Task 1: Behavioral baseline and skill instructions

**Files:** `SKILL.md`, `agents/openai.yaml`, `references/{text,diagram,html,video,production}.md`, `tests/behavior/`, `docs/testing.md`.

**Interface:** The core selects one mode and passes a brief containing goal, facts/assumptions, relationship, example, explicit settings, and delivery constraints. Mode references return an artifact plus performed checks.

- [x] Run five independent missing-strength baseline responses without the skill; retain responses and observed outcomes.
- [x] Write the smallest core and conditional references covering the agreed rules and observed baseline failure.
- [x] Run five fresh guided responses plus realistic routing, follow-up, capability, and percentage cases; inspect actual output.
- [x] Validate frontmatter and relative reference reachability.

## Task 2: Reusable visual and interactive resources

**Files:** `assets/explainer.html`, `assets/relationship.svg`, `tests/test_explainer.mjs`.

**Interface:** Single-file HTML runs offline; exposes the water-tank model through ordinary accessible controls. SVG is a complete editable relationship diagram, not an empty scaffold.

- [x] Write model tests for accumulation, equal flows, draining, zero time, capacity bounds, and invalid inputs; observe failure before adding the model.
- [x] Implement the reusable HTML example and SVG with accurate labels, clear hierarchy, and a stated model boundary.
- [x] Run the model suite and inspect desktop/mobile rendering and real controls in a browser. Remaining UI checks are recorded in `tests/ui-checklist.md`.

## Task 3: Optional video assembly

**Files:** `scripts/assemble_video.py`, `assets/storyboard.example.json`, `tests/test_video.py`.

**Interface:** A JSON manifest supplies ordered local image/audio pairs, caption text, and output size; Python validates inputs and calls a supplied/discovered FFmpeg executable. Narration length drives segment duration. No paid service or network dependency.

- [x] Test manifest/input errors and subtitle timing with local fixtures before implementation.
- [x] Implement validation, measured audio duration, per-scene media assembly, and synchronized SRT output with bounded subprocess execution.
- [x] Run unit tests and one actual short video smoke test when the runtime permits; report any unperformed checks.

## Task 4: Independent review and documentation

**Files:** `README.md`, `LICENSE`, `docs/testing.md`, English design/plan documents.

- [x] Write installation, invocation examples, capability requirements, limitations, and attribution for public distribution.
- [x] Obtain an independent behavior/code review; fix material issues and rerun affected tests.
- [x] Keep packaging validation, artifact execution, and learning-effect claims separate in the report.

## Task 5: Release and GitHub publication

**Files:** `scripts/build_release.py`, `tests/test_release.py`, `.gitignore`, `dist/llm-explain-1.0.0.zip`, checksums.

- [x] Test archive contents, portable references, excluded private/development files, and reproducibility before implementing the packager.
- [x] Build and reopen the ZIP; validate the extracted skill and run the complete project suite.
- [x] Publish to an existing dedicated repository if found, otherwise create `Gohanwu42/llm-explain` for the user-authorized public skill. Preserve other repositories.
- [x] Upload the release ZIP, verify remote file/commit and downloadable bytes, and provide repository plus direct download links. Release: https://github.com/Gohanwu42/llm-explain/releases/tag/v1.0.0.

## Execution record

- Initial directory contained only the design and glossary; no Git repository or product files existed.
- User's authorization includes implementation and publication without further approval pauses. No global skill installation is implied by publication.
- All five final baseline responses explained immediately without collecting the required strength. All five matching guided responses asked for it. Eleven additional guided scenarios completed and were inspected; the 21 final runs explicitly requested `gpt-6.1-sol` and had no infrastructure errors. An earlier same-run process timeout is recorded separately.
- Independent `gpt-6-astra` review fixes cover minimum narration duration and decoded video presence, exclusive-copy publication fallback, stable slider ranges, visible equation precision, and evaluation metadata.
- Final checks passed: 18 Node tests, 31 Python tests with FFmpeg and no skips, selected Chrome interactions at desktop/390 px, SVG inspection, and corrected 18.888-second video playback with clear captions. The UI checklist states unperformed keyboard, screen-reader, and narrower-screen checks.
- The 12-file release ZIP is 27,104 bytes; repeated builds are byte-identical, CRC checks pass, and the extracted skill passes validation. Remote publication and download verification remain pending.
