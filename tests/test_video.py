"""Behavior tests for the optional, local-only video helper."""

import importlib.util
import errno
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import wave
import zlib


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "assemble_video.py"


def write_png(path, rgb=(30, 100, 160)):
    """Create a tiny real image without third-party dependencies."""
    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    width, height = 8, 8
    pixels = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


def write_wav(path, seconds=0.25, sample_rate=8000):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        samples = [int(2500 * math.sin(2 * math.pi * 440 * i / sample_rate))
                   for i in range(round(sample_rate * seconds))]
        audio.writeframes(struct.pack("<" + "h" * len(samples), *samples))


def write_bmp(path, rgb=(160, 70, 30)):
    width, height = 8, 8
    pixels = bytes(reversed(rgb)) * width * height
    header = struct.pack("<2sIHHI", b"BM", 54 + len(pixels), 0, 0, 54)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0,
                      len(pixels), 2835, 2835, 0, 0)
    path.write_bytes(header + dib + pixels)


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        write_png(self.directory / "frame.png")
        write_wav(self.directory / "voice.wav")
        self.manifest = self.directory / "storyboard.json"
        self.data = {
            "width": 320,
            "height": 180,
            "fps": 24,
            "segments": [{"image": "frame.png", "audio": "voice.wav",
                          "caption": "Water increases by one liter each minute."}],
        }
        self.save_manifest()

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def module(self):
        self.assertTrue(SCRIPT.is_file(), "The video assembly helper is not implemented.")
        spec = importlib.util.spec_from_file_location("llm_explain_video", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_relative_media_paths_resolve_against_manifest(self):
        storyboard = self.module().load_manifest(self.manifest)
        self.assertEqual(storyboard.width, 320)
        self.assertEqual(storyboard.segments[0].image, self.directory / "frame.png")
        self.assertEqual(storyboard.segments[0].audio, self.directory / "voice.wav")

    def test_missing_media_is_rejected_before_rendering(self):
        self.data["segments"][0]["image"] = "missing.png"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "image"):
            self.module().load_manifest(self.manifest)

    def test_remote_media_is_rejected(self):
        self.data["segments"][0]["audio"] = "https://example.com/voice.wav"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "local"):
            self.module().load_manifest(self.manifest)

    def test_malformed_json_is_an_actionable_validation_error(self):
        self.manifest.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON"):
            self.module().load_manifest(self.manifest)

    def test_empty_segments_are_rejected(self):
        self.data["segments"] = []
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "segments"):
            self.module().load_manifest(self.manifest)

    def test_dimensions_reject_zero_negative_boolean_and_odd_values(self):
        module = self.module()
        for value in (0, -2, True, 319, 2.5):
            with self.subTest(width=value):
                self.data["width"] = value
                self.save_manifest()
                with self.assertRaisesRegex(ValueError, "width"):
                    module.load_manifest(self.manifest)

    def test_non_object_segment_is_rejected(self):
        self.data["segments"] = ["frame.png"]
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "segment"):
            self.module().load_manifest(self.manifest)

    def test_empty_caption_is_rejected(self):
        self.data["segments"][0]["caption"] = "  "
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "caption"):
            self.module().load_manifest(self.manifest)

    def test_subtitles_use_cumulative_narration_time(self):
        actual = self.module().make_srt([1.25, 2.5], ["First scene.", "Second scene."])
        self.assertEqual(actual, "1\n00:00:00,000 --> 00:00:01,250\nFirst scene.\n\n"
                         "2\n00:00:01,250 --> 00:00:03,750\nSecond scene.\n\n")

    def test_subtitles_carry_millisecond_rounding_across_seconds(self):
        actual = self.module().make_srt([59.9996, 0.5], ["Before.", "After."])
        self.assertIn("00:00:00,000 --> 00:01:00,000", actual)
        self.assertIn("00:01:00,000 --> 00:01:00,500", actual)

    def test_subtitles_reject_invalid_or_submillisecond_durations(self):
        module = self.module()
        for duration in (0, -1, float("nan"), float("inf"), 0.0001):
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    module.make_srt([duration], ["Scene."])

    def test_subtitles_reject_mismatched_segment_counts(self):
        with self.assertRaises(ValueError):
            self.module().make_srt([1, 2], ["Only one caption."])

    def test_existing_video_or_subtitle_is_never_overwritten(self):
        module = self.module()
        storyboard = module.load_manifest(self.manifest)
        output = self.directory / "result.mp4"
        for existing in (output, output.with_suffix(".srt")):
            with self.subTest(existing=existing.name):
                existing.write_bytes(b"Keep this file.")
                with self.assertRaisesRegex(ValueError, "exists"):
                    module.validate_outputs(storyboard, output)
                self.assertEqual(existing.read_bytes(), b"Keep this file.")
                existing.unlink()

    def test_output_cannot_replace_any_input(self):
        module = self.module()
        self.data["segments"][0]["audio"] = "voice.mp4"
        (self.directory / "voice.wav").rename(self.directory / "voice.mp4")
        self.save_manifest()
        storyboard = module.load_manifest(self.manifest)
        with self.assertRaises(ValueError):
            module.validate_outputs(storyboard, self.directory / "voice.mp4")

    def test_cli_help_does_not_require_ffmpeg(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--manifest", result.stdout)
        self.assertIn("--ffmpeg", result.stdout)

    def test_cli_missing_ffmpeg_does_not_create_outputs(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(self.manifest),
                                 "--output", str(self.directory / "result.mp4"),
                                 "--ffmpeg", str(self.directory / "missing-ffmpeg")],
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FFmpeg", result.stderr)
        self.assertFalse((self.directory / "result.mp4").exists())
        self.assertFalse((self.directory / "result.srt").exists())

    def available_ffmpeg(self):
        executable = os.environ.get("LLM_EXPLAIN_FFMPEG") or shutil.which("ffmpeg")
        if not executable:
            self.skipTest("Set LLM_EXPLAIN_FFMPEG to run actual MP4 integration checks.")
        return executable

    def test_actual_video_matches_two_images_and_measured_audio(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        write_png(self.directory / "second.png", (160, 70, 30))
        write_wav(self.directory / "second.wav", 0.5)
        self.data["segments"].append({"image": "second.png", "audio": "second.wav",
                                      "caption": "Second scene."})
        self.save_manifest()
        try:
            output, subtitle, duration = module.assemble(module.load_manifest(self.manifest),
                                                         self.directory / "actual.mp4", ffmpeg)
        except ValueError as error:
            self.fail(f"Cannot assemble the actual two-scene video: {error}")
        self.assertAlmostEqual(duration, 0.75, places=3)
        self.assertEqual(subtitle.read_text(encoding="utf-8"),
                         "1\n00:00:00,000 --> 00:00:00,250\n"
                         "Water increases by one liter each minute.\n\n"
                         "2\n00:00:00,250 --> 00:00:00,750\nSecond scene.\n\n")
        inspected = subprocess.run([ffmpeg, "-hide_banner", "-i", str(output),
                                    "-f", "null", "-"], capture_output=True, text=True, timeout=30)
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        self.assertIn("320x180", inspected.stderr)
        self.assertIn("Audio: aac", inspected.stderr)
        for moment, expected in (("0.125", (30, 100, 160)), ("0.5", (160, 70, 30))):
            frame = subprocess.run([ffmpeg, "-loglevel", "error", "-ss", moment,
                                    "-i", str(output), "-frames:v", "1", "-f", "rawvideo",
                                    "-pix_fmt", "rgb24", "pipe:1"],
                                   capture_output=True, timeout=30)
            self.assertEqual(frame.returncode, 0, frame.stderr)
            center = (90 * 320 + 160) * 3
            actual = frame.stdout[center:center + 3]
            self.assertEqual(len(actual), 3)
            for channel, wanted in zip(actual, expected):
                self.assertLessEqual(abs(channel - wanted), 12)

    def test_corrupt_audio_fails_without_publishing_video(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        (self.directory / "voice.wav").write_bytes(b"Not audio.")
        with self.assertRaisesRegex(ValueError, "FFmpeg failed"):
            module.assemble(module.load_manifest(self.manifest),
                            self.directory / "corrupt.mp4", ffmpeg)
        self.assertFalse((self.directory / "corrupt.mp4").exists())
        self.assertFalse((self.directory / "corrupt.srt").exists())

    def test_actual_video_accepts_spaces_and_quotes_in_media_filenames(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        (self.directory / "frame.png").rename(self.directory / "frame's odd name.png'")
        (self.directory / "voice.wav").rename(self.directory / "voice's odd name.wav")
        self.data["segments"][0].update({"image": "frame's odd name.png'",
                                          "audio": "voice's odd name.wav"})
        self.save_manifest()
        try:
            output, _, _ = module.assemble(module.load_manifest(self.manifest),
                                           self.directory / "quoted.mp4", ffmpeg)
        except ValueError as error:
            self.fail(f"Valid local media filenames could not be assembled: {error}")
        self.assertGreater(output.stat().st_size, 0)

    def test_actual_video_preserves_scenes_with_different_image_formats(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        write_bmp(self.directory / "second.bmp")
        self.data["segments"].append({"image": "second.bmp", "audio": "voice.wav",
                                      "caption": "Second format."})
        self.save_manifest()
        try:
            output, _, _ = module.assemble(module.load_manifest(self.manifest),
                                           self.directory / "mixed.mp4", ffmpeg)
        except ValueError as error:
            self.fail(f"Mixed local image formats could not be assembled: {error}")
        frame = subprocess.run([ffmpeg, "-loglevel", "error", "-ss", "0.375",
                                "-i", str(output), "-frames:v", "1", "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "pipe:1"], capture_output=True, timeout=30)
        self.assertEqual(frame.returncode, 0, frame.stderr)
        center = (90 * 320 + 160) * 3
        actual = frame.stdout[center:center + 3]
        self.assertEqual(len(actual), 3)
        for channel, wanted in zip(actual, (160, 70, 30)):
            self.assertLessEqual(abs(channel - wanted), 12)

    def test_sub_frame_narration_is_rejected_without_publishing_output(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        write_wav(self.directory / "voice.wav", 0.001, sample_rate=48000)
        with self.assertRaisesRegex(ValueError, "at least.*frame"):
            module.assemble(module.load_manifest(self.manifest),
                            self.directory / "too-short.mp4", ffmpeg)
        self.assertFalse((self.directory / "too-short.mp4").exists())
        self.assertFalse((self.directory / "too-short.srt").exists())

    def test_sub_frame_second_scene_is_rejected_at_selected_fps(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        self.data["fps"] = 1
        write_wav(self.directory / "first.wav", 1, sample_rate=48000)
        self.data["segments"] = [
            {"image": "frame.png", "audio": "first.wav", "caption": "One full frame."},
            {"image": "frame.png", "audio": "voice.wav", "caption": "Too short at one fps."},
        ]
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "Segment 2.*at least.*frame"):
            module.assemble(module.load_manifest(self.manifest),
                            self.directory / "second-too-short.mp4", ffmpeg)
        self.assertFalse((self.directory / "second-too-short.mp4").exists())
        self.assertFalse((self.directory / "second-too-short.srt").exists())

    def test_exact_one_frame_narration_produces_a_decodable_video_frame(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        write_wav(self.directory / "voice.wav", 1 / 24, sample_rate=48000)
        try:
            output, subtitle, duration = module.assemble(module.load_manifest(self.manifest),
                                                         self.directory / "one-frame.mp4", ffmpeg)
        except ValueError as error:
            self.fail(f"Exactly one frame of narration was rejected: {error}")
        self.assertAlmostEqual(duration, 1 / 24, places=7)
        self.assertIn("00:00:00,000 --> 00:00:00,042", subtitle.read_text(encoding="utf-8"))
        frame = subprocess.run([ffmpeg, "-loglevel", "error", "-i", str(output),
                                "-map", "0:v:0", "-frames:v", "1", "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "pipe:1"], capture_output=True, timeout=30)
        self.assertEqual(frame.returncode, 0, frame.stderr)
        self.assertEqual(len(frame.stdout), 320 * 180 * 3)

    def test_audio_only_encoder_output_is_not_published_as_video(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        wrapper = self.directory / "faulty-encoder"
        wrapper.write_text(
            f"#!{sys.executable}\n"
            "import subprocess, sys\n"
            f"executable = {ffmpeg!r}\n"
            "arguments = sys.argv[1:]\n"
            "if arguments[-1] == 'result.mp4':\n"
            "    arguments = ['-nostdin', '-loglevel', 'error', '-n', '-i', "
            "'narration.wav', '-vn', '-c:a', 'aac', 'result.mp4']\n"
            "sys.exit(subprocess.call([executable] + arguments))\n",
            encoding="utf-8")
        wrapper.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "video frame"):
            module.assemble(module.load_manifest(self.manifest),
                            self.directory / "audio-only.mp4", str(wrapper))
        self.assertFalse((self.directory / "audio-only.mp4").exists())
        self.assertFalse((self.directory / "audio-only.srt").exists())

    def test_unsupported_hardlinks_fall_back_to_exclusive_file_copy(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        unsupported = OSError(errno.ENOTSUP, "Hard links are not supported on this filesystem.")
        with mock.patch.object(module.os, "link", side_effect=unsupported):
            try:
                output, subtitle, _ = module.assemble(module.load_manifest(self.manifest),
                                                       self.directory / "copied.mp4", ffmpeg)
            except ValueError as error:
                self.fail(f"A writable filesystem without hard links was rejected: {error}")
        self.assertGreater(output.stat().st_size, 0)
        self.assertIn("00:00:00,000 --> 00:00:00,250", subtitle.read_text(encoding="utf-8"))
        inspected = subprocess.run([ffmpeg, "-loglevel", "error", "-i", str(output),
                                    "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-"],
                                   capture_output=True, timeout=30)
        self.assertEqual(inspected.returncode, 0, inspected.stderr)

    def test_copy_fallback_preserves_a_competing_subtitle_and_removes_own_video(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        output = self.directory / "race.mp4"
        subtitle = output.with_suffix(".srt")

        def unsupported_link(source, target):
            if Path(target).suffix == ".srt":
                subtitle.write_bytes(b"Keep this competing subtitle.")
            raise OSError(errno.ENOTSUP, "Hard links are unsupported.")

        with mock.patch.object(module.os, "link", side_effect=unsupported_link):
            with self.assertRaisesRegex(ValueError, "without overwriting"):
                module.assemble(module.load_manifest(self.manifest), output, ffmpeg)
        self.assertFalse(output.exists())
        self.assertTrue(subtitle.is_file(), "Publication never reached the subtitle collision.")
        self.assertEqual(subtitle.read_bytes(), b"Keep this competing subtitle.")

    def test_hardlink_file_exists_error_never_enters_copy_fallback(self):
        ffmpeg = self.available_ffmpeg()
        module = self.module()
        output = self.directory / "exists.mp4"

        def colliding_link(source, target):
            output.write_bytes(b"Keep this competing video.")
            raise FileExistsError(errno.EEXIST, "A competing output exists.")

        with mock.patch.object(module.os, "link", side_effect=colliding_link):
            with self.assertRaisesRegex(ValueError, "without overwriting"):
                module.assemble(module.load_manifest(self.manifest), output, ffmpeg)
        self.assertEqual(output.read_bytes(), b"Keep this competing video.")
        self.assertFalse(output.with_suffix(".srt").exists())


if __name__ == "__main__":
    unittest.main()
