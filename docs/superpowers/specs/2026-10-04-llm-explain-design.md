# LLM Explain: Design Specification

Status: Approved for implementation by the user on 2026-10-04. This specification defines the agreed behavior, strength calibration, production limits, and delivery checks. Implementation and test results are tracked separately.

See [CONTEXT.md](../../../CONTEXT.md) for terminology. The working name is `llm-explain`.

## 1. Goal and Scope

**Help users understand complex concepts, explain key relationships, and apply them to simple new examples.** Users choose the medium and production level. The skill organizes the content into clear, useful, reusable explanation artifacts.

- Support different users, languages, and LLM tool capabilities.
- Use one primary medium per run: text, diagram, interactive HTML, or video. Add supporting text, annotations, or images when needed.
- Lightweight mode minimizes production cost. Polished mode adds customization and visual polish.
- The learning objective determines explanation depth. Both production levels require accuracy, clarity, and usability.
- Understanding, practical use, and reuse are design goals. Improved learning efficiency requires evidence from actual use.
- This version delivers a distributable skill, references loaded as needed, and a small set of production resources. A learning platform, long-term learner records, automatic publishing, and paid-service activation are outside scope.

**Honor choices the user has already made.** Text requires only one configuration choice per run: STE-inspired strength. Each other medium requires a production level; STE-inspired strength is optional. Use choices already stated in the request.

## 2. User Flow

**Let the skill make production decisions and the user make choices that affect the result.** At each stage, ask only for information still missing.

| Stage | Behavior | Completion condition |
|---|---|---|
| Read context | Extract the topic, learning objective, prior knowledge, difficulty, materials, and explicit constraints; briefly inspect exposed tool capabilities | Known information and actual gaps are clear |
| Choose medium | If missing, present the four media and known capability limits | The user explicitly chooses the primary medium; video always requires an explicit choice |
| Choose configuration | For text, ask only for strength; for other media, ask only for a production level; never repeat a supplied choice | Required parameters for this run are complete |
| Calibrate the explanation | Derive the learning objective from context; ask one short question only when a gap would change the explanation | The key relationship to explain is clear |
| Check production conditions | Load only the selected medium's references; confirm production, preview, inspection, and delivery capabilities | A viable delivery path exists; if capabilities are insufficient, the user chooses an alternative |
| Produce | Produce lightweight work directly; for polished work, provide a representative preview and complete the artifact after direction approval | The agreed artifact exists |
| Verify the artifact | Check content and sources, then render or functionally inspect the selected medium | Critical problems are fixed; unperformed checks are disclosed |
| Check understanding | Offer one optional explanation or application question; after the user responds, clarify only the relationship they missed | Feedback is provided, or understanding remains unverified |

**Follow-up explanations and corrections within a run retain its configuration.** A new learning task or a change of primary medium starts a new run. Explicit choices in the new request take precedence. Personal preferences or the previous run's settings cannot replace a required choice for the current run.

**Avoid repetition.** In short outputs, combine the overview with the answer and combine paragraph wrap-ups with the final conclusion. Structure should aid reading. Users may provide aesthetic references; the skill does not require an extra style menu.

## 3. How Strength Changes Text

**Strength controls how strongly expression is constrained.** Accept any user-selected value from 0% to 100%, with no default. Intermediate values are valid. The table gives calibration anchors; do not silently replace a requested value with a preset.

| Anchor | Behavior |
|---|---|
| 0% | Use natural, clear expression without additional STE-inspired language constraints |
| 60% | Keep terminology consistent and prefer active expression; allow natural compound sentences, necessary modifiers, and connected prose |
| 80% | Prefer one statement per short sentence; make subjects and causal relationships explicit; split nested conditions; reduce asides and synonym changes |
| 100% | Apply direct sentence structures, explicit relationships, and stable terminology as strictly as practical while preserving accuracy, necessary conditions, and natural readability |

- At every strength, preserve facts, qualifications, key relationships, and necessary explanation depth.
- Higher strength does not guarantee fewer total words or formal ASD-STE100 compliance.
- For Chinese, split sentences by meaning, subject, and condition, and use Chinese punctuation. Do not mechanically apply English word-count limits. Adapt other languages to their own conventions.
- Put the overview and answer before the explanation. Begin each paragraph with a bold sentence that states its main point, and leave blank lines between paragraphs.
- Use bullets for parallel points, numbered lists for steps, and tables for comparisons. Keep continuous reasoning connected.
- End paragraphs with a wrap-up or transition. Close with the core relationship without repeatedly restating the same sentence.
- Create diagrams, HTML, or video only when the user selects that medium. If the current medium cannot support the learning objective, suggest a switch and let the user decide.

### 60% and 80% Calibration Examples Using the Same Material

**The examples use an explicitly bounded model.** A tank holds 40 liters and starts with 20 liters. Water flows in at 3 liters per minute and out at 2 liters per minute. Both rates remain constant during observation. Ignore other losses. Discuss only the period before the tank is full and the instant it becomes full.

**60%: Retain natural compound sentences.**

> **The tank gains 1 liter per minute, so it becomes full after 20 minutes.** It starts with 20 liters and holds up to 40 liters; although 3 liters enter each minute, 2 liters also leave, giving a net increase of 1 liter per minute.
>
> - After 10 minutes: 20 + (3 - 2) × 10 = 30 liters.
> - After 20 minutes: 20 + (3 - 2) × 20 = 40 liters. The tank is exactly full.
>
> **The water volume depends on the difference between inflow and outflow.** These calculations assume constant flow rates and ignore other losses; their scope ends when the tank becomes full.

**80%: Separate calculations and conditions.**

> **The tank gains 1 liter per minute and becomes full after 20 minutes.** It starts with 20 liters. Its capacity is 40 liters.
>
> - Each minute, 3 liters enter and 2 liters leave.
> - Net increase per minute: 3 - 2 = 1 liter.
> - Water volume after 10 minutes: 20 + 1 × 10 = 30 liters.
> - Water volume after 20 minutes: 20 + 1 × 20 = 40 liters. The tank is exactly full.
>
> **The change in water volume depends on the difference between inflow and outflow.** The calculations assume constant flow rates and ignore other losses. Their scope ends when the tank becomes full.

**Both versions must preserve the same facts and boundaries.** Calibrate sentence organization and terminology consistency, not a supposed percentage of compliant sentences. These examples illustrate the intended behavior; they do not yet show that different models will reliably produce this distinction.

## 4. How Production Level Controls Investment

**Production level applies only to diagrams, HTML, and video.** Users choose lightweight or polished. The skill determines image count, interactions, duration, and tools while honoring explicit requirements.

| Item | Lightweight | Polished |
|---|---|---|
| Production approach | Reuse suitable templates, components, and simple presentation methods | Customize visual hierarchy and presentation for the content |
| Production preview | Produce directly to reduce waiting | First provide one representative preview using real content |
| Preview content | No required preview | A diagram's key relationship, HTML's main interaction, or a short video segment |
| Aesthetic alignment | Follow stated preferences and principles of clear expression | Use optional references to create the preview; allow at most one revision round when needed, then seek direction approval |
| Full production | One complete approach | Complete one full approach after direction approval |
| Automatic repair | At most two targeted repair-and-recheck rounds after the initial inspection | Same as lightweight |

**These counts are the agreed production limits.** One automatic repair round means locally fixing identified problems and rechecking them, not regenerating the entire artifact. If critical errors remain, explain them and do not deliver the artifact as a usable finished product. The user chooses whether to invest further.

- Keep the preview small but sufficient to test information hierarchy or audiovisual relationships. A style name alone is not a preview.
- An explicit change of production level or a more specific budget takes precedence.
- Consider tokens, media-generation fees, and waiting time separately. Give monetary or token figures only with reliable data; otherwise explain the estimate's basis and uncertainty.
- Choosing a production level does not authorize purchasing a new service or exceeding an explicit budget. Ask only when an actual additional-spending choice arises.
- When a response reveals a learning gap, first clarify the relevant relationship. Recreating complete media is additional production and requires the intended investment to be specified again.

## 5. Delivery and Checks for the Four Media

| Medium | Deliverable | Main checks |
|---|---|---|
| Text | A directly readable Markdown explanation | Answer first; consistent terminology; complete conditions; expression matches selected strength; no repeated overview |
| Diagram | An explanation image viewable in the current environment; retain editable source files when tools support them | Clear main question; accurate nodes, arrows, and labels; clear hierarchy; readable text without obvious overlap |
| HTML | An openable page and reusable source files | Actually operate key interactions; check calculations and state; inspect narrow screens, keyboard use, hierarchy, and reading order |
| Video | A video playable in the current environment, requested companion files such as subtitles, and available production sources | Check key frames and transitions; actually play the video to inspect narration, subtitles, and visuals together; keep names, numbers, and units consistent |

**Organize every medium around one clear learning question.** Diagrams show the main relationships. HTML interactions let users observe changes. Video uses visuals to show mechanisms, narration to explain logic, subtitles to support listening, and annotations to focus attention.

- Pair abstract relationships with a concrete anchor. Added decoration must help understanding.
- Present dense content in steps or split the artifact. The learning objective determines image count and duration.
- Synchronize video subtitles with narration. Match visuals to the meaning of each segment; show derivations, mechanisms, and comparisons where useful.
- Let content structure drive a small set of suitable HTML components. Use verified templates when needed. Check template appearance and layout constraints; a slide's fixed aspect ratio is not automatically a webpage requirement.
- Follow licenses and retain required attribution for external templates and assets. Do not include assets with unverified sources in the general distribution package.

**When capabilities are insufficient, agree on what can actually be delivered.** If the environment can write HTML but cannot preview it, state that source files can be provided but execution is unverified. Without video-production capabilities, offer a diagram, HTML, or script and continue after the user chooses. Name scripts, storyboards, code, and generation prompts according to what they actually are.

## 6. Content Reliability and Evidence of Understanding

**Verify the explanation, then check the user's understanding.** Track correctness, usability, and the user's response separately; none substitutes for another.

- Extract key facts, conditions, relationships, and unknowns into a short internal checklist.
- For user-provided material, distinguish its claims from verified facts. Preserve uncertainty when claims conflict.
- Time-sensitive, high-risk, or uncertain facts require reliable sources. Disclose limits when verification tools are unavailable. State assumptions directly for demonstration models.
- Check relationships and calculations before production. Recheck the finished artifact before delivery to catch conflicts between visuals and narration.
- A generated file or a template's built-in check marker is not evidence that a check was performed.
- Test only one key relationship or simple transfer in the understanding question. Do not reveal the answer in advance. Users may skip it.
- For correct answers, acknowledge the reasoning. For incorrect answers, locate the misunderstanding and clarify it locally. If skipped or unanswered, understanding remains unverified.
- Claims of improved learning efficiency require a separate comparison with real learners or an evaluation of repeated use. Skill acceptance does not establish that outcome.

## 7. Module Boundaries and Distribution

**Use a lightweight core and references loaded as needed.** The core covers choices for the current run, an internal explanation brief, routing, shared checks, and understanding feedback. Load medium details only after selection.

| Module | Responsibility | Dependencies |
|---|---|---|
| Core `SKILL.md` | Recognize intent, obtain required choices, maintain run state, route work, and deliver | Current conversation and available tool information |
| Text reference | Strength anchors, language rules, and calibration examples | Explanation brief and user-selected strength |
| Diagram reference | Relationship layout, information selection, and diagram checks | Explanation brief and available drawing tools |
| HTML reference | Content-to-component mapping, useful interactions, and browser checks | Suitable templates plus page-production and inspection capabilities |
| Video reference | Storyboarding, division of work among visuals/narration/subtitles, previews, and playback checks | Actually available video and audio tools |
| Production resources | Reusable original templates and components, or resources with clear licenses | Used only for the selected production path |
| Acceptance examples | Inputs, expected observable behavior, and actual results | Development acceptance; not loaded for routine explanations |

**The internal explanation brief is the shared module input.** Keep only the learning objective, key relationships, a concrete example, facts and assumptions, selected parameters, and delivery conditions. Users do not fill out a technical form. The selected module returns the artifact, actual check records, and critical limitations.

- Use `llm-explain` as the working name. Skill instructions, descriptions, and UI metadata are in English; explanations follow the user's language.
- The core text workflow works in ordinary chat environments. Media production depends on existing capabilities. The package does not depend on one paid model provider.
- Use the environment's supported skill-discovery mechanism. The description should target concept explanation and learning materials rather than all ordinary questions.
- Do not turn an individual's identity, personal directories, accounts, or specific aesthetic references into requirements for all users.
- Verify local artifacts and portable packaged paths separately. Design documents and development tests do not automatically enter the routine loading path.
- Installation and publication are separate delivery operations. This specification defines the distributable contents.

## 8. Acceptance Plan and Evidence at Approval

**Verify behavior before judging production quality.** During development, use the same tank model across all four media to compare preservation of facts and boundaries.

| Scenario | Expected observable behavior |
|---|---|
| Initial request without a medium | Present four choices and wait; do not start video automatically |
| Request for "text, 80%" | Use 80% directly; do not ask again for strength or production level |
| Request for "text" without strength | Ask only for strength; do not default to 80% |
| New task versus a follow-up within the same run | Obtain the new task's choices; retain settings for a same-run follow-up |
| Same material at 60% and 80% | Preserve facts, conditions, and numbers; produce a discernible difference in sentence organization |
| Request for a lightweight diagram | Produce and check directly; do not require a production preview |
| Request for polished HTML | Provide a representative preview with real content, then complete after direction approval |
| HTML parameter change | Actual interaction produces results consistent with the model; clearly identify parameter values outside the model's scope |
| Video requested without production tools | State the capability limit and wait for the user to choose an alternative medium |
| Video tools available | Produce an actually playable file and check key relationships among visuals, narration, and subtitles |
| Critical errors remain at the repair limit | Report the errors and actual delivery status; do not label the artifact as verified |
| Understanding question skipped or answered incorrectly | Keep understanding unverified if skipped; clarify only the missed relationship if incorrect |
| References loaded as needed | Read only the core and selected medium's required references; do not load video resources for text tasks |

**Cross-model conclusions must state the actual test scope.** When possible, run key scenarios with at least two models of different capabilities. Record the model, tools, inputs, results, duration, and available token or cost data. With limited runs, report observations without generalizing a stable success rate. If only one model is available, report results only within that scope.

**At approval, evidence consisted of specification checks and the text calibration examples above.** Production in all four media, cross-model performance, and real learning outcomes remained to be verified. Subsequent implementation and test reports must state what was actually checked.
