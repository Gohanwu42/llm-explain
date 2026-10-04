#!/usr/bin/env python3
"""Assemble local still images and narration into MP4 plus synchronized SRT.

Requires Python 3.9+ and FFmpeg with libx264/AAC support. No Python packages,
network access, narration service, or FFprobe executable are required.
Media paths in the manifest are relative to the manifest's directory.
Existing output files are never overwritten.
"""

import argparse
from dataclasses import dataclass
import errno
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import wave


@dataclass(frozen=True)
class Segment:
    image: Path
    audio: Path
    caption: str


@dataclass(frozen=True)
class Storyboard:
    manifest: Path
    width: int
    height: int
    fps: int
    segments: tuple


def _integer(value, name, minimum, maximum, even=False):
    if (type(value) is not int or not minimum <= value <= maximum
            or (even and value % 2)):
        qualifier = "even " if even else ""
        raise ValueError(f"{name} must be an {qualifier}integer from {minimum} to {maximum}.")
    return value


def _caption(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 10000:
        raise ValueError("Each caption must contain 1 to 10,000 characters of text.")
    if any(ord(character) < 32 and character not in "\n\r\t" for character in value):
        raise ValueError("A caption contains an unsupported control character.")
    # Blank lines delimit SRT cues, so keep line breaks but remove blank lines.
    return "\n".join(line.strip() for line in value.splitlines() if line.strip())


def _media_path(value, base, kind, index):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError(f"Segment {index} {kind} must be a local file path.")
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", value):
        raise ValueError(f"Segment {index} {kind} must be local; URLs are not supported.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"Segment {index} {kind} file is missing or is not a regular file: {path}")
    return path


def load_manifest(path):
    """Validate a storyboard before any subprocess or output creation."""
    path = Path(path).expanduser().resolve()
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("The manifest exceeds the 1 MiB limit.")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read manifest JSON: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("The manifest JSON must be an object.")
    unknown = set(data) - {"width", "height", "fps", "segments"}
    if unknown:
        raise ValueError(f"Unknown manifest fields: {', '.join(sorted(unknown))}")
    width = _integer(data.get("width"), "width", 2, 4096, even=True)
    height = _integer(data.get("height"), "height", 2, 4096, even=True)
    fps = _integer(data.get("fps", 24), "fps", 1, 60)
    rows = data.get("segments")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
        raise ValueError("segments must be a list with 1 to 100 entries.")
    segments = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Each segment must be an object; segment {index} is invalid.")
        if set(row) - {"image", "audio", "caption"}:
            raise ValueError(f"Segment {index} has unknown fields; use image, audio, and caption.")
        segments.append(Segment(
            _media_path(row.get("image"), path.parent, "image", index),
            _media_path(row.get("audio"), path.parent, "audio", index),
            _caption(row.get("caption")),
        ))
    return Storyboard(path, width, height, fps, tuple(segments))


def _timestamp(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def make_srt(durations, captions):
    """Use cumulative audio durations; round cue boundaries only once."""
    if not durations or len(durations) != len(captions):
        raise ValueError("Subtitle durations and captions must have the same nonzero length.")
    elapsed = 0.0
    start_ms = 0
    cues = []
    for index, (duration, caption) in enumerate(zip(durations, captions), 1):
        if (isinstance(duration, bool) or not isinstance(duration, (int, float))
                or not math.isfinite(duration) or duration < 0.001):
            raise ValueError("Subtitle durations must be finite and at least one millisecond.")
        elapsed += duration
        if elapsed > 3600:
            raise ValueError("The total narration exceeds the one-hour limit.")
        end_ms = round(elapsed * 1000)
        if end_ms <= start_ms:
            raise ValueError("Every subtitle must have a positive displayed duration.")
        cues.append(f"{index}\n{_timestamp(start_ms)} --> {_timestamp(end_ms)}\n"
                    f"{_caption(caption)}\n\n")
        start_ms = end_ms
    return "".join(cues)


def validate_outputs(storyboard, output):
    """Refuse collisions, including symlinks and the companion subtitle path."""
    output = Path(output).expanduser().absolute()
    if output.suffix.lower() != ".mp4":
        raise ValueError("The output filename must end in .mp4.")
    if not output.parent.is_dir():
        raise ValueError("The output parent directory must already exist.")
    subtitle = output.with_suffix(".srt")
    inputs = {storyboard.manifest}
    for segment in storyboard.segments:
        inputs.update((segment.image, segment.audio))
    for target in (output, subtitle):
        if target.resolve() in inputs:
            raise ValueError(f"An output would replace an input file: {target}")
        if target.exists() or target.is_symlink():
            raise ValueError(f"Output already exists; choose a new filename: {target}")
    return output, subtitle


def _find_ffmpeg(requested):
    executable = shutil.which(requested or "ffmpeg")
    if not executable:
        raise ValueError("FFmpeg is unavailable. Install it separately or pass --ffmpeg /path/to/ffmpeg.")
    return str(Path(executable).resolve())


def _run(command, directory, timeout):
    try:
        result = subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"FFmpeg exceeded the {timeout}-second process limit.") from error
    except OSError as error:
        raise ValueError(f"Cannot run FFmpeg: {error}") from error
    if result.returncode:
        detail = result.stderr[-4000:].strip() or f"exit status {result.returncode}"
        raise ValueError(f"FFmpeg failed: {detail}")


def _remove_owned(path, identity):
    """Do not remove a file that replaced one created by this invocation."""
    try:
        current = Path(path).lstat()
        if (current.st_dev, current.st_ino) == identity:
            Path(path).unlink()
    except FileNotFoundError:
        pass


def _publish_new(source, target):
    """Prefer a hard link; use exclusive copy on filesystems without links."""
    try:
        os.link(source, target)
    except OSError as error:
        unsupported = {errno.EXDEV, errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}
        if error.errno not in unsupported:
            raise
        identity = None
        try:
            with Path(source).open("rb") as original, Path(target).open("xb") as created:
                stat = os.fstat(created.fileno())
                identity = (stat.st_dev, stat.st_ino)
                shutil.copyfileobj(original, created)
        except BaseException:
            if identity is not None:
                _remove_owned(target, identity)
            raise
        return identity
    stat = Path(source).stat()
    return stat.st_dev, stat.st_ino


def assemble(storyboard, output, ffmpeg=None):
    """Decode, measure, render, and publish two new files without overwrites."""
    output, subtitle = validate_outputs(storyboard, output)
    executable = _find_ffmpeg(ffmpeg)
    # A sibling workspace allows atomic hard links where supported. Publication
    # falls back to exclusive creation on writable filesystems without links.
    with tempfile.TemporaryDirectory(prefix="llm-explain-video-", dir=output.parent) as temp:
        directory = Path(temp)
        durations = []
        image_lines = ["ffconcat version 1.0"]
        with wave.open(str(directory / "narration.wav"), "wb") as joined:
            joined.setnchannels(1)
            joined.setsampwidth(2)
            joined.setframerate(48000)
            for index, segment in enumerate(storyboard.segments):
                audio = directory / f"audio-{index:04}.wav"
                _run([executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                      "-protocol_whitelist", "file,pipe", "-i", str(segment.audio),
                      "-map", "0:a:0", "-vn", "-sn", "-dn", "-ac", "1", "-ar", "48000",
                      "-c:a", "pcm_s16le", str(audio)], directory, 120)
                with wave.open(str(audio), "rb") as decoded:
                    duration = decoded.getnframes() / decoded.getframerate()
                    if not math.isfinite(duration) or duration < 0.001:
                        raise ValueError(f"Segment {index + 1} has empty or invalid narration.")
                    # Compare sample counts exactly, including the one-frame boundary.
                    if decoded.getnframes() * storyboard.fps < decoded.getframerate():
                        raise ValueError(
                            f"Segment {index + 1} narration must last at least one video frame "
                            f"({1 / storyboard.fps:.6f} seconds at {storyboard.fps} fps). "
                            "Supply longer narration."
                        )
                    durations.append(duration)
                    if sum(durations) > 3600:
                        raise ValueError("The total narration exceeds the one-hour limit.")
                    while True:
                        frames = decoded.readframes(65536)
                        if not frames:
                            break
                        joined.writeframesraw(frames)
                # Normalize formats and sizes; the concat demuxer uses one codec.
                # Generated filenames also avoid FFconcat path-escaping issues.
                image_name = f"image-{index:04}.png"
                image_filter = (
                    f"scale={storyboard.width}:{storyboard.height}:force_original_aspect_ratio=decrease,"
                    f"pad={storyboard.width}:{storyboard.height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                    "setsar=1,format=rgb24"
                )
                _run([executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                      "-protocol_whitelist", "file,pipe", "-i", str(segment.image),
                      "-vf", image_filter, "-frames:v", "1", "-update", "1", image_name],
                     directory, 30)
                image_lines.extend((f"file '{image_name}'", "option framerate 1000",
                                    f"duration {duration:.9f}"))
        image_lines.extend((f"file '{image_name}'", "option framerate 1000"))
        (directory / "images.ffconcat").write_text("\n".join(image_lines) + "\n", encoding="utf-8")
        captions = make_srt(durations, [segment.caption for segment in storyboard.segments])
        (directory / "result.srt").write_text(captions, encoding="utf-8")
        filters = (f"scale={storyboard.width}:{storyboard.height}:force_original_aspect_ratio=decrease,"
                   f"pad={storyboard.width}:{storyboard.height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                   f"setsar=1,fps={storyboard.fps},format=yuv420p")
        _run([executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
              "-protocol_whitelist", "file,pipe", "-f", "concat", "-safe", "0",
              "-i", "images.ffconcat", "-i", "narration.wav", "-map", "0:v:0", "-map", "1:a:0",
              "-vf", filters, "-t", f"{sum(durations):.9f}", "-c:v", "libx264",
              "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
              "-movflags", "+faststart", "result.mp4"], directory, 600)
        if (directory / "result.mp4").stat().st_size == 0:
            raise ValueError("FFmpeg produced an empty video.")
        # A nonempty MP4 can still contain only audio. Decode a real video frame
        # before publishing either file, rather than relying on container size.
        try:
            _run([executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                  "-protocol_whitelist", "file,pipe", "-i", "result.mp4", "-map", "0:v:0",
                  "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "frame-check.rgb"],
                 directory, 30)
        except ValueError as error:
            raise ValueError(f"The rendered MP4 has no decodable video frame: {error}") from error
        frame = directory / "frame-check.rgb"
        if not frame.is_file() or frame.stat().st_size != storyboard.width * storyboard.height * 3:
            raise ValueError("The rendered MP4 has no complete video frame at the requested dimensions.")
        # Both publication paths create only a new name; neither overwrites.
        try:
            video_identity = _publish_new(directory / "result.mp4", output)
        except OSError as error:
            raise ValueError(f"Cannot publish video without overwriting: {error}") from error
        try:
            _publish_new(directory / "result.srt", subtitle)
        except OSError as error:
            _remove_owned(output, video_identity)
            raise ValueError(f"Cannot publish subtitles without overwriting: {error}") from error
    return output, subtitle, sum(durations)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Local JSON storyboard.")
    parser.add_argument("--output", required=True, type=Path, help="New .mp4 path; creates a sibling .srt.")
    parser.add_argument("--ffmpeg", help="Optional FFmpeg executable path or command name.")
    arguments = parser.parse_args(argv)
    try:
        video, subtitles, duration = assemble(load_manifest(arguments.manifest),
                                               arguments.output, arguments.ffmpeg)
    except (ValueError, OSError, wave.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Created {video} and {subtitles} ({duration:.3f} seconds of narration).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
