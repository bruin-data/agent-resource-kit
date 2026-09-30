#!/usr/bin/env python3
"""Validate, render, probe and contact-sheet a VHS terminal demo tape.

Sample code: read it before you run it.

The point of this script is the verification, not the rendering: `vhs` alone can
exit 0 having written a truncated video, so this wraps it with `vhs validate`
first, a scan of the render log for VHS's own `error:` lines, an `ffprobe` of
the artifact, and a contact sheet an agent or a human can actually look at.

Standard library only. Needs `vhs` on PATH, plus `ffmpeg` and `ffprobe` unless
you pass --no-contact-sheet and --no-probe.

    python3 render_demo.py path/to/demo.tape
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

MEDIA_SUFFIXES = {".gif", ".mp4", ".webm"}

# Six frames in a 3x2 grid is enough to spot a failed command, a clipped line or
# an unreadable colour without opening the video.
SHEET_COLUMNS = 3
SHEET_ROWS = 2


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(command: list[str], *, cwd: Path) -> None:
    print("+ " + shlex.join(command))
    subprocess.run(command, cwd=cwd, check=True)


def run_captured(command: list[str], *, cwd: Path) -> str:
    print("+ " + shlex.join(command))
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        fail(f"command exited with status {result.returncode}: {shlex.join(command)}")
    return result.stdout + result.stderr


def tape_outputs(tape: Path) -> list[str]:
    """Return every path named by an `Output` directive in the tape."""
    outputs: list[str] = []
    for line_number, raw_line in enumerate(tape.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line)
        except ValueError as exc:
            fail(f"cannot parse {tape}:{line_number}: {exc}")
        if parts and parts[0] == "Output":
            if len(parts) != 2:
                fail(f"expected one Output path at {tape}:{line_number}")
            outputs.append(parts[1])
    if not outputs:
        fail(f"{tape} has no Output directive")
    return outputs


def require_tools(*names: str) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        fail(
            "missing required tools: "
            + ", ".join(missing)
            + ". See the resource README for install commands."
        )


def probe(media: Path) -> tuple[float, int]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(media),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)["format"]
    duration = float(data["duration"])
    size = int(data["size"])
    if duration <= 0 or size <= 0:
        fail(f"invalid rendered artifact: {media}")
    return duration, size


def contact_sheet(media: Path, destination: Path, duration: float) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    frames = SHEET_COLUMNS * SHEET_ROWS
    frames_per_second = frames / duration
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(media),
            "-vf",
            f"fps={frames_per_second:.8f},scale=640:-1,"
            f"tile={SHEET_COLUMNS}x{SHEET_ROWS}",
            "-frames:v",
            "1",
            str(destination),
        ],
        cwd=media.parent,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tape", type=Path, help="path to a .tape file")
    parser.add_argument(
        "--qa-dir",
        type=Path,
        help="where to write contact sheets. Default: beside the rendered media.",
    )
    parser.add_argument(
        "--no-contact-sheet",
        action="store_true",
        help="skip the contact sheet, and with it the ffmpeg requirement.",
    )
    parser.add_argument(
        "--no-probe",
        action="store_true",
        help="skip the ffprobe duration check. Implies --no-contact-sheet.",
    )
    args = parser.parse_args()

    if args.no_probe:
        args.no_contact_sheet = True

    required = ["vhs"]
    if not args.no_probe:
        required.append("ffprobe")
    if not args.no_contact_sheet:
        required.append("ffmpeg")
    require_tools(*required)

    tape = args.tape.resolve()
    if tape.suffix != ".tape" or not tape.is_file():
        fail(f"not a VHS tape file: {tape}")

    # VHS resolves Output paths relative to its working directory, so always run
    # it from the tape's own directory and resolve the same way here.
    output_paths = [(tape.parent / value).resolve() for value in tape_outputs(tape)]
    for output in output_paths:
        output.parent.mkdir(parents=True, exist_ok=True)

    run(["vhs", "validate", tape.name], cwd=tape.parent)
    render_log = run_captured(["vhs", tape.name], cwd=tape.parent)
    # Some VHS versions write a partial video after an EOF error and still exit 0.
    if any(line.lower().startswith("error:") for line in render_log.splitlines()):
        fail("VHS reported an internal error and may have produced a partial artifact")

    media_paths = [p for p in output_paths if p.suffix.lower() in MEDIA_SUFFIXES]
    if not media_paths:
        fail("the tape has no GIF, MP4 or WebM output to inspect")

    for media in media_paths:
        if not media.is_file():
            fail(f"VHS did not create expected output: {media}")
        print(f"artifact: {media}")
        if args.no_probe:
            print(f"size: {media.stat().st_size} bytes")
            continue
        duration, size = probe(media)
        print(f"duration: {duration:.2f}s")
        print(f"size: {size} bytes")
        if args.no_contact_sheet:
            continue
        qa_dir = (args.qa_dir or media.parent).resolve()
        qa_path = qa_dir / f"{tape.stem}-{media.stem}-contact-sheet.png"
        contact_sheet(media, qa_path, duration)
        print(f"qa: {qa_path}")


if __name__ == "__main__":
    main()
