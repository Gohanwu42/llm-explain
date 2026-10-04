# Video test evidence

The helper uses only the Python standard library. FFmpeg is an optional external
executable. The example manifest names media that the caller must supply; those
placeholder files are not bundled.

Run the validation and subtitle tests:

```sh
python3 -m unittest discover -s tests -p test_video.py -v
```

To include real encoding checks, set the path to a local FFmpeg executable:

```sh
LLM_EXPLAIN_FFMPEG=/path/to/ffmpeg python3 -m unittest discover -s tests -p test_video.py -v
```

## Checks performed on 2026-10-04

- Observed the initial 16 tests fail before implementation, then pass after it.
- Ran 27 tests with Python 3.9 and FFmpeg 7.1; all passed. The real encoding tests
  verify two scene colors, output dimensions, an AAC audio stream, measured cue
  times, mixed PNG/BMP images, filenames with spaces and quotes, and corrupt-audio
  failure without published output. Review regressions also reject sub-frame
  narration and an audio-only encoder result; exactly one frame of narration is
  accepted and decoded successfully. Filesystem regressions use real file I/O
  with only `os.link` fault injection: unsupported hard links fall back to
  exclusive file copies, competing files are preserved, and a subtitle collision
  removes only the video created by the current run.
- Created a separate three-scene water-tank MP4 with local macOS speech narration:
  18.888 seconds of narration, 960 by 540 pixels, H.264 at 24 fps, and AAC mono audio
  at 48 kHz. The SRT boundaries were 0, 3.727, 9.058, and 18.888 seconds.
- Decoded the entire narrated MP4 successfully and inspected an exported frame.
  The decoded audio had an RMS level of approximately -15.97 dB and no NaN or
  infinite samples. These checks establish a valid, non-silent audio stream;
  they do not establish voice quality or human comprehension.
- This worker did not listen to the finished narration or perform a learner
  assessment. Those checks are separate from file assembly and automated tests.

The test executable came from the `imageio-ffmpeg` 0.6.0 macOS ARM64 wheel obtained
from [PyPI](https://pypi.org/project/imageio-ffmpeg/0.6.0/). It was installed into a
temporary directory only. No third-party binary or Python dependency is shipped
in the skill. Narration and media fixtures were also kept in temporary storage.

The helper produces scene-level subtitles as a separate SRT file. It does not
generate narration, infer word timings, or burn captions into the video. Image
transitions occur on video frame boundaries; SRT cues follow measured narration
times to the nearest millisecond. Every narration segment must last at least one
frame at the selected fps. The helper decodes one output frame before publishing
the MP4 and SRT; a nonempty container alone does not count as a verified video.
