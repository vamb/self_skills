#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


FORMAT_SETTINGS = {
    "wav": {"extension": ".wav", "codec_args": ["-c:a", "pcm_s16le"], "compressed": False},
    "m4a": {"extension": ".m4a", "codec_args": ["-c:a", "aac"], "compressed": True},
    "mp3": {"extension": ".mp3", "codec_args": ["-c:a", "libmp3lame"], "compressed": True},
}


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except FileNotFoundError as exc:
        raise SystemExit(f"Required executable not found: {command[0]}. Install FFmpeg and ensure it is on PATH.") from exc
    except PermissionError as exc:
        raise SystemExit(f"Permission denied while running {command[0]}. Check that FFmpeg can be executed on this machine.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise SystemExit(f"Command failed ({command[0]}){detail}") from exc


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Required executable not found: {name}. Install FFmpeg and ensure it is on PATH.")


def ffprobe(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(completed.stdout)


def bitrate_to_bps(value: str) -> int:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([kKmM]?)", value.strip())
    if not match:
        raise SystemExit(f"Invalid bitrate: {value!r}. Use values like 128k.")
    number = float(match.group(1))
    unit = match.group(2).lower()
    multiplier = 1_000_000 if unit == "m" else 1_000 if unit == "k" else 1
    return int(number * multiplier)


def estimated_audio_bps(audio_format: str, sample_rate: int, channels: int, bitrate: str) -> int:
    if FORMAT_SETTINGS[audio_format]["compressed"]:
        return bitrate_to_bps(bitrate)
    # pcm_s16le: 16 bits per sample, so 2 bytes per channel per sample.
    return sample_rate * channels * 16


def choose_output_path(input_path: Path, output_arg: str | None, audio_format: str) -> Path:
    extension = FORMAT_SETTINGS[audio_format]["extension"]
    if output_arg:
        output = Path(output_arg).expanduser().resolve()
        if output.suffix.lower() != extension:
            output = output.with_suffix(extension)
        return output
    return input_path.with_name(f"{input_path.stem}.audio{extension}")


def split_output_dir(input_path: Path, output_arg: str | None) -> tuple[Path, str]:
    if not output_arg:
        return input_path.with_name(f"{input_path.stem}.audio-segments"), input_path.stem
    output = Path(output_arg).expanduser().resolve()
    if output.suffix:
        return output.parent / output.stem, output.stem
    return output, input_path.stem


def media_summary(path: Path, probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams", [])
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    fmt = probe.get("format", {})
    return {
        "path": str(path),
        "duration": float(fmt["duration"]) if fmt.get("duration") not in {None, "N/A"} else None,
        "size_bytes": int(fmt.get("size", 0) or 0),
        "audio": None
        if audio is None
        else {
            "codec": audio.get("codec_name"),
            "sample_rate": int(audio.get("sample_rate", 0) or 0),
            "channels": int(audio.get("channels", 0) or 0),
            "channel_layout": audio.get("channel_layout"),
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def detect_silence_points(input_path: Path, noise: str, min_silence: float) -> list[float]:
    completed = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(input_path),
            "-vn",
            "-af",
            f"silencedetect=noise={noise}:d={min_silence}",
            "-f",
            "null",
            "-",
        ],
        capture=True,
    )
    starts: list[float] = []
    points: list[float] = []
    for line in completed.stderr.splitlines():
        start_match = re.search(r"silence_start:\s*(\d+(?:\.\d+)?)", line)
        if start_match:
            starts.append(float(start_match.group(1)))
            continue
        end_match = re.search(r"silence_end:\s*(\d+(?:\.\d+)?)", line)
        if end_match:
            end = float(end_match.group(1))
            start = starts.pop(0) if starts else max(0.0, end - min_silence)
            points.append(round((start + end) / 2.0, 3))
    return sorted(set(points))


def build_ranges(duration: float, silence_points: list[float], max_segment_duration: float, min_segment_duration: float) -> list[dict[str, Any]]:
    ranges: list[dict[str, Any]] = []
    cursor = 0.0
    while cursor < duration - 0.001:
        remaining = duration - cursor
        if remaining <= max_segment_duration:
            ranges.append({"start": round(cursor, 3), "end": round(duration, 3), "cut": "end", "forced_cut": False})
            break
        target = cursor + max_segment_duration
        candidates = [point for point in silence_points if cursor + min_segment_duration <= point <= target]
        if candidates:
            cut = candidates[-1]
            forced = False
            cut_kind = "silence"
        else:
            cut = target
            forced = True
            cut_kind = "duration-limit"
        if cut <= cursor + 0.001:
            cut = min(duration, cursor + max_segment_duration)
            forced = True
            cut_kind = "duration-limit"
        ranges.append({"start": round(cursor, 3), "end": round(cut, 3), "cut": cut_kind, "forced_cut": forced})
        cursor = cut
    return ranges


def encode_audio(
    input_path: Path,
    output_path: Path,
    audio_format: str,
    channels: int,
    sample_rate: int,
    bitrate: str,
    overwrite: bool,
    start: float | None = None,
    end: float | None = None,
) -> list[str]:
    settings = FORMAT_SETTINGS[audio_format]
    command = ["ffmpeg", "-y" if overwrite else "-n", "-hide_banner", "-loglevel", "error"]
    if start is not None:
        command.extend(["-ss", f"{start:.3f}"])
    if end is not None and start is not None:
        command.extend(["-t", f"{max(0.0, end - start):.3f}"])
    command.extend(
        [
            "-i",
            str(input_path),
            "-vn",
            "-map",
            "0:a:0",
            "-ac",
            str(channels),
            "-ar",
            str(sample_rate),
            *settings["codec_args"],
        ]
    )
    if settings["compressed"]:
        command.extend(["-b:a", bitrate])
    command.append(str(output_path))
    run(command)
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract an audio track from a video file.")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", help="Output audio path, output prefix, or segment directory")
    parser.add_argument("--format", choices=sorted(FORMAT_SETTINGS), default="wav", help="Output audio format")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Output sample rate for WAV/MP3/M4A")
    parser.add_argument("--channels", type=int, choices=[1, 2], default=1, help="Output channels: 1 mono, 2 stereo")
    parser.add_argument("--bitrate", default="128k", help="Compressed output audio bitrate, e.g. 128k")
    parser.add_argument("--manifest", help="Optional JSON manifest output path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it already exists")
    parser.add_argument("--split-on-silence", action="store_true", help="Create multiple audio files, cutting near silence")
    parser.add_argument("--max-size-mb", type=float, default=10.0, help="Maximum target size per segment in MB")
    parser.add_argument("--silence-noise", default="-35dB", help="FFmpeg silencedetect noise threshold")
    parser.add_argument("--min-silence", type=float, default=0.45, help="Minimum silence duration in seconds")
    parser.add_argument("--min-segment-seconds", type=float, default=20.0, help="Avoid silence cuts before this segment length")
    parser.add_argument("--size-safety-ratio", type=float, default=0.88, help="Reserve space for container overhead when estimating segment duration")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_tool("ffmpeg")
    require_tool("ffprobe")

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input video not found: {input_path}")

    source_probe = ffprobe(input_path)
    source_summary = media_summary(input_path, source_probe)
    if source_summary["audio"] is None:
        raise SystemExit(f"No audio stream found in video: {input_path}")
    duration = float(source_summary.get("duration") or 0)
    if duration <= 0:
        raise SystemExit(f"Cannot determine media duration: {input_path}")

    if not args.split_on_silence:
        output_path = choose_output_path(input_path, args.output, args.format)
        if output_path.exists() and not args.overwrite:
            raise SystemExit(f"Output already exists: {output_path}. Use --overwrite or choose a different --output.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = encode_audio(
            input_path,
            output_path,
            args.format,
            args.channels,
            args.sample_rate,
            args.bitrate,
            args.overwrite,
        )
        output_probe = ffprobe(output_path)
        output_summary = media_summary(output_path, output_probe)
        manifest = {
            "ok": True,
            "mode": "single",
            "source": source_summary,
            "output": output_summary,
            "format": args.format,
            "sample_rate": args.sample_rate,
            "channels": args.channels,
            "bitrate": args.bitrate if FORMAT_SETTINGS[args.format]["compressed"] else None,
            "command": command,
        }
        if args.manifest:
            write_json(Path(args.manifest).expanduser().resolve(), manifest)
        print(json.dumps({"ok": True, "mode": "single", "audio_path": str(output_path), "manifest_path": args.manifest}, ensure_ascii=False))
        return 0

    if args.max_size_mb <= 0:
        raise SystemExit("--max-size-mb must be greater than 0.")

    estimated_bps = estimated_audio_bps(args.format, args.sample_rate, args.channels, args.bitrate)
    max_bytes = int(args.max_size_mb * 1024 * 1024)
    max_segment_duration = max(1.0, (max_bytes * 8 / estimated_bps) * args.size_safety_ratio)
    max_segment_duration = max(max_segment_duration, args.min_segment_seconds)
    silence_points = detect_silence_points(input_path, args.silence_noise, args.min_silence)
    ranges = build_ranges(duration, silence_points, max_segment_duration, args.min_segment_seconds)

    out_dir, prefix = split_output_dir(input_path, args.output)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"Segment output directory is not empty: {out_dir}. Use --overwrite or choose a different --output.")
    out_dir.mkdir(parents=True, exist_ok=True)

    extension = FORMAT_SETTINGS[args.format]["extension"]
    files: list[dict[str, Any]] = []
    commands: list[list[str]] = []
    oversize_files: list[dict[str, Any]] = []
    for index, item in enumerate(ranges, start=1):
        output_path = out_dir / f"{prefix}.part{index:03d}{extension}"
        command = encode_audio(
            input_path,
            output_path,
            args.format,
            args.channels,
            args.sample_rate,
            args.bitrate,
            True,
            float(item["start"]),
            float(item["end"]),
        )
        commands.append(command)
        output_summary = media_summary(output_path, ffprobe(output_path))
        record = {
            "index": index,
            "path": str(output_path),
            "start": item["start"],
            "end": item["end"],
            "duration": round(float(item["end"]) - float(item["start"]), 3),
            "cut": item["cut"],
            "forced_cut": item["forced_cut"],
            "size_bytes": output_summary["size_bytes"],
            "under_limit": output_summary["size_bytes"] <= max_bytes,
        }
        if not record["under_limit"]:
            oversize_files.append(record)
        files.append(record)

    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else out_dir / f"{prefix}.audio-segments.json"
    manifest = {
        "ok": not oversize_files,
        "mode": "segments",
        "source": source_summary,
        "output_dir": str(out_dir),
        "files": files,
        "format": args.format,
        "sample_rate": args.sample_rate,
        "channels": args.channels,
        "bitrate": args.bitrate if FORMAT_SETTINGS[args.format]["compressed"] else None,
        "max_size_mb": args.max_size_mb,
        "max_size_bytes": max_bytes,
        "estimated_audio_bps": estimated_bps,
        "estimated_max_segment_duration": round(max_segment_duration, 3),
        "silence_detection": {
            "noise": args.silence_noise,
            "min_silence": args.min_silence,
            "points_found": len(silence_points),
        },
        "oversize_files": oversize_files,
        "commands": commands,
    }
    write_json(manifest_path, manifest)
    print(
        json.dumps(
            {
                "ok": manifest["ok"],
                "mode": "segments",
                "output_dir": str(out_dir),
                "manifest_path": str(manifest_path),
                "file_count": len(files),
                "oversize_count": len(oversize_files),
            },
            ensure_ascii=False,
        )
    )
    return 0 if manifest["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
