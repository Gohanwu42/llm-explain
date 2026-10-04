# LLM Explain

**Turn complex ideas into explanations people can understand, inspect, and reuse.** Choose text, a diagram, interactive HTML, or video. Choose the language strength or production investment. Let the agent handle the production details.

[Download the installable ZIP](https://github.com/Gohanwu42/llm-explain/releases/latest/download/llm-explain-1.0.0.zip) · [Test evidence](docs/testing.md) · [MIT license](LICENSE)

## Start with a small choice

| Medium | Your required setting | What you receive |
|---|---|---|
| Text | Any 0–100% ASD-STE100-inspired strength | Structured Markdown, answer first |
| Diagram | Lightweight or polished | A focused visual showing a relationship |
| Interactive HTML | Lightweight or polished | An explorable page and reusable source |
| Video | Lightweight or polished | A playable explanation with coordinated narration, pictures, and captions |

If the request already includes these choices, the agent uses them. Missing choices are asked one at a time. Text does not ask for a production tier. Video is never selected automatically.

```text
Use $llm-explain. Explain opportunity cost in text at 80%.

Use $llm-explain. Make a lightweight diagram explaining how a queue grows.

Use $llm-explain. Build a polished interactive HTML explanation of compound growth.

Use $llm-explain. Make a lightweight video about negative feedback.
```

**60% versus 80% changes expression, not truth.** The percentage is an informal strength setting inspired by ASD-STE100. It is not a compliance score, a percentage of facts retained, or a promise of fewer words. Higher settings favor shorter direct statements and more stable terminology. See the [same-content examples](references/text.md).

**Lightweight versus polished changes production investment, not correctness.** Lightweight proceeds directly with suitable reusable components. Polished begins with a real-content preview for direction approval. The default scope is one complete direction, at most one preview revision, and at most two local repair cycles. Explicit user instructions and budgets take precedence.

## Install

1. Download the release ZIP and verify its accompanying SHA-256 checksum if needed.
2. Extract the single `llm-explain` folder into the skills location supported by your agent. For Codex, `~/.agents/skills/llm-explain/` is a supported location. Keep `SKILL.md`, `references`, `assets`, and `scripts` together.
3. Start a fresh session so the agent discovers the skill, then invoke `$llm-explain`.

On a service with skill upload, upload the release ZIP using that service's supported workflow. In an ordinary chat without skill installation, supply `SKILL.md` and the relevant reference; text explanations remain usable, while actual media production depends on the tools available there. This repository does not install anything globally or purchase services.

## What is included

- A compact core that loads only the selected medium's guidance.
- Text calibration, visual composition, interaction, and video-storytelling references.
- An original [standalone HTML example](assets/explainer.html) and [editable SVG](assets/relationship.svg) using the same bounded water-tank model.
- An optional [video assembly helper](scripts/assemble_video.py) for local still images, narration, MP4, and synchronized SRT.

The examples are reusable starting points, not a fixed style library. Keep their content assumptions and calculations correct when adapting them. The installed ZIP excludes development plans, tests, and evaluation logs.

## Capabilities and limits

Text requires no production tools. A diagram needs a supported visual output path; HTML needs file output and ideally browser checks; video needs actual media tools. The agent checks the chosen path and states limitations instead of presenting source code or a storyboard as a rendered artifact.

The optional video helper requires Python 3 and FFmpeg. It does not create images or synthesize speech. Run:

```sh
python3 scripts/assemble_video.py --help
```

The skill offers one skippable understanding question. An answer supports a judgment about that response; skipped questions and attractive artifacts do not prove learning. No claim of universal model reliability or measured learning-efficiency improvement is made.

## Development

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_explainer.mjs
python3 scripts/build_release.py --version 1.0.0
```

Video integration tests require an available FFmpeg binary; see [testing](docs/testing.md) for the exact setup and actual results. The behavior runner under `tests/behavior` uses an authenticated Codex CLI, consumes model usage, and is separate from the installable skill.

## Inspiration and attribution

Inspired by [Andrej Karpathy's post about understanding language-model outputs](https://x.com/karpathy/status/2105819303471976479), then developed into a user-controlled explanation workflow with reusable production resources and explicit verification. This is an independent project, not an official Karpathy or ASD publication, and it does not reproduce the ASD-STE100 standard or dictionary.

The shipped code and visual assets are original to this project and available under the MIT license. External media tools remain under their own licenses.
