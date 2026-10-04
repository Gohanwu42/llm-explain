# Multimodal explainer video

Video is available only after the learner explicitly chooses it. Confirm the actual rendering, narration, caption, playback, and delivery capabilities before committing to a finished video.

## Storyboard from the learning goal

For each scene, specify the relationship to understand, what the picture reveals, what narration explains, and which short annotation directs attention. Use a concrete anchor before abstraction. Build an overview, a mechanism or comparison, and a concise recap.

- Narration carries the logical explanation.
- Captions faithfully track narration.
- Pictures show changes, mechanisms, spatial relationships, or counterexamples. They may carry meaning beyond the spoken words while staying relevant to that moment.
- Annotations highlight where to look and what changed.
- Timing leaves room to inspect the important relationship. Music and motion must support intelligibility.

Choose duration from the concept and selected production level. Polished mode needs a representative real-content clip before full production. A script or storyboard is a clearly labeled intermediate artifact.

## Tool paths

Use the environment's supported video and speech tools. Generate diagrams, animation, or imagery through the appropriate host tools. Do not add paid services implicitly.

For a low-dependency still-scene video, [assemble_video.py](../scripts/assemble_video.py) combines local image/narration pairs into an MP4 and synchronized SRT. It needs Python 3 and FFmpeg; it does not synthesize speech, draw frames, or choose their meaning. Run `python3 scripts/assemble_video.py --help` for the exact manifest schema and options. [storyboard.example.json](../assets/storyboard.example.json) shows the input shape; its referenced media must be supplied.

Choose this simple path only when still scenes sufficiently explain the relationship. Dynamic mechanisms may need actual animation; richer production can use another supported renderer. Missing tools call for a clear limitation and a learner-selected alternative.

## Verify

Review the final video, including key transitions. Reserve a readable caption area so subtitles do not cover important labels. Check visual/narration correspondence, legible labels, units, caption accuracy and timing, audible speech, and enough time to inspect the visual. Metadata and file existence alone do not establish playback quality.

Deliver the playable video, captions, and available reusable sources. Report any unperformed playback or timing checks. Offer the optional understanding question in accompanying text so the learner can answer at their own pace.
