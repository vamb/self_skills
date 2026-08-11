---
name: video-to-audio
description: Extract audio from a provided video file, optionally splitting the extracted audio near silence into size-limited chunks while preserving the default WAV extraction behavior. Use when the user supplies MP4, MOV, MKV, AVI, WEBM, or another video file and wants the speech/audio separated for ASR, transcription, editing, archiving, reuse, or third-party upload limits such as 10MB or 20MB per file. This skill does not transcribe speech or create ASR JSON.
---

# Video to Audio

Extract audio from a video file with the bundled Python script. Keep the default behavior aligned with the original extractor: WAV output, 16 kHz, mono, PCM audio. When a service has a file-size limit, split that WAV audio into chunks near silence instead of lowering audio quality by default.

## Workflow

1. Confirm the input video path exists.
2. Choose one mode:
   - Single audio file: extract one WAV file.
   - Size-limited chunks: extract WAV segments, cutting near silence when possible.
3. Run `scripts/extract_audio.py` with the selected options.
4. Return the output audio path, or the segment directory and manifest path.
5. If extraction fails, report the script error clearly and do not invent output paths.

## Single WAV File

Use WAV by default:

```bash
python scripts/extract_audio.py --input /absolute/path/input.mp4
```

The default output is created next to the input video as `<stem>.audio.wav` using 16 kHz mono PCM audio.

To choose the exact output path:

```bash
python scripts/extract_audio.py \
  --input /absolute/path/input.mp4 \
  --output /absolute/path/input.wav
```

## Size-Limited WAV Chunks

When a third-party ASR service limits upload size, split the extracted WAV audio into chunks. The script estimates how many seconds of PCM audio fit into the requested size, detects silence with FFmpeg `silencedetect`, and cuts near silence when possible.

```bash
python scripts/extract_audio.py \
  --input /absolute/path/input.mp4 \
  --output /absolute/path/input-audio-parts \
  --split-on-silence \
  --max-size-mb 10 \
  --manifest /absolute/path/input-audio-parts.json
```

Typical output:

```text
input-audio-parts/
  input.part001.wav
  input.part002.wav
  input.part003.wav
input-audio-parts.json
```

The manifest records each segment path, source start/end time, size, whether it stayed under the limit, and whether the cut was forced. If no silence exists near the size boundary, the script uses a duration-based cut and records `forced_cut: true`.

## Useful Options

- `--output /path/audio.wav`: choose the output path, segment directory, or output prefix.
- `--format wav|m4a|mp3`: choose the output container/codec; default remains `wav`.
- `--sample-rate 16000`: choose output sample rate; default remains 16 kHz.
- `--channels 1`: choose mono or stereo output; default remains mono.
- `--split-on-silence`: create multiple size-limited chunks near silence.
- `--max-size-mb 10`: target maximum size per chunk.
- `--silence-noise -35dB`: adjust silence threshold.
- `--min-silence 0.45`: adjust minimum silence duration.
- `--manifest /path/audio.manifest.json`: write machine-readable extraction details.
- `--overwrite`: replace existing output files or reuse a non-empty segment directory.

## Boundaries

- Do not transcribe speech.
- Do not create `asr.json`.
- Do not modify or delete the source video.
- Do not change the default output away from WAV.
- Do not reduce quality by default to satisfy size limits; use splitting first.
- Require FFmpeg and ffprobe to be available on PATH.
- If the video has no audio stream, stop and explain that no audio can be extracted.
- If a chunk still exceeds the requested size limit, report the manifest warning and suggest lowering `--max-size-mb` or allowing a compressed format explicitly.
