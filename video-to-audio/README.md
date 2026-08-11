# video-to-audio

Extract the audio track from a video file. The default behavior stays the same as the first version: output WAV, 16 kHz, mono, PCM audio.

This skill does not transcribe speech and does not create `asr.json`.

## Single WAV Output

Extract one WAV file next to the source video:

```bash
python scripts/extract_audio.py --input "C:\path\to\input.mp4"
```

Default output:

```text
C:\path\to\input.audio.wav
```

Extract one WAV file with the same base name as the video:

```bash
python scripts/extract_audio.py ^
  --input "C:\path\to\input.mp4" ^
  --output "C:\path\to\input.wav"
```

## Split WAV By Silence And Size

Use this when an ASR service has an upload limit, such as 10 MB per file. This keeps WAV output and cuts near speech silence when possible:

```bash
python scripts/extract_audio.py ^
  --input "C:\path\to\input.mp4" ^
  --output "C:\path\to\input-audio-parts" ^
  --split-on-silence ^
  --max-size-mb 10 ^
  --manifest "C:\path\to\input-audio-parts.json"
```

Typical output:

```text
input-audio-parts\
  input.part001.wav
  input.part002.wav
  input.part003.wav
input-audio-parts.json
```

The manifest records each segment path, start/end time, file size, whether it stayed under the limit, and whether the cut was forced. If no silence is available near the size boundary, the script uses a duration-based cut and records `forced_cut: true`.

## Common Options

- `--max-size-mb 10`: target maximum size per segment.
- `--silence-noise -35dB`: silence detection threshold.
- `--min-silence 0.45`: minimum silence duration in seconds.
- `--overwrite`: overwrite existing outputs.
- `--format wav|m4a|mp3`: optional format override; default remains `wav`.

## Notes

- Requires `ffmpeg` and `ffprobe` on PATH.
- The source video is never modified.
- Size limiting is handled by splitting first, not by reducing quality by default.