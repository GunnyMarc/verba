# videotr — Video Transcription Pipeline

Extracts audio from video files, transcribes speech to text using OpenAI Whisper, and outputs formatted markdown transcripts.

## Architecture

```
TranscriptionPipeline.process(video_path)
│
├─ [0%]  Validate video file (format, existence)
├─ [5%]  Get video info via FFprobe (duration, codec, audio)
├─ [10%] Extract audio via FFmpeg (→ 16kHz mono WAV)
├─ [25%] Load Whisper model (auto-detect GPU/CPU)
├─ [30%] Transcribe audio (→ segments with timestamps)
├─ [80%] Format as markdown (selected style)
├─ [90%] Save markdown file
└─ [100%] Complete → PipelineResult
```

## Modules

| File | Class/Function | Purpose |
|------|---------------|---------|
| `src/pipeline.py` | `TranscriptionPipeline` | Orchestrates the full workflow: extract → transcribe → format → save |
| `src/extractor.py` | `AudioExtractor` | Extracts audio from video files using FFmpeg |
| `src/transcriber.py` | `Transcriber` | Speech-to-text transcription using OpenAI Whisper |
| `src/formatter.py` | `MarkdownFormatter` | Converts transcription results to styled markdown |
| `src/config.py` | Configuration | FFmpeg verification, config file management, model/device prompts |
| `src/cli.py` | CLI | Click-based command-line interface |

## Supported Video Formats

| Extension | Description |
|-----------|-------------|
| `.mov` | Apple QuickTime Movie |
| `.mp4` | MPEG-4 Video |
| `.mkv` | Matroska Video |
| `.mpeg` / `.mpg` | MPEG Video |
| `.avi` | Audio Video Interleave |
| `.webm` | WebM Video |

## Whisper Models

| Model | Parameters | VRAM | Use Case |
|-------|-----------|------|----------|
| `tiny` | ~39M | ~1GB | Quick drafts, testing |
| `base` | ~74M | ~1GB | Default, good balance |
| `small` | ~244M | ~2GB | Better accuracy |
| `medium` | ~769M | ~5GB | Professional use |
| `large` | ~1550M | ~10GB | Premium quality |
| `large-v2` | ~1550M | ~10GB | Improved large |
| `large-v3` | ~1550M | ~10GB | Latest improvements |

## Markdown Output Styles

### simple
Plain text transcription without timestamps.

### timestamped (default)
Text with inline timestamps:
```
**[00:00:05.123]** Segment text here.
```

### detailed
Full metadata, segment tables with start/end/duration, and statistics (total words, words per minute, average words per segment).

### srt_style
SRT subtitle format within a markdown code block:
```
1
00:00:00,000 --> 00:00:05,123
Segment text here.
```

## CLI Usage

```bash
python -m videotr.src.cli [OPTIONS]
```

### Main Options

| Flag | Description | Default |
|------|-------------|---------|
| `-m`, `--model` | Whisper model (`tiny`..`large-v3`) | from config |
| `--device` | Processing device (`cuda`, `cpu`) | from config |
| `-l`, `--language` | Language code (e.g., `en`, `es`) or auto-detect | from config |
| `-s`, `--style` | Markdown style (`simple`, `timestamped`, `detailed`, `srt_style`) | `timestamped` |
| `--keep-audio` | Keep extracted audio file after processing | off |
| `--no-metadata` | Exclude metadata header from output | off |
| `-q`, `--quiet` | Suppress progress output (only print output path) | off |
| `--configure` | Interactive configuration editor | — |
| `--clear-cache` | Remove `__pycache__` directories and exit | — |

### Subcommands

| Command | Description |
|---------|-------------|
| `info VIDEO` | Display video metadata (duration, format, codec, audio info) |
| `models` | List available Whisper models with parameters and VRAM requirements |
| `formats` | List supported video formats |

### Transcription Modes

When run interactively, the CLI prompts for a mode:

1. **Transcribe** — Process a single video file
2. **Batch** — Process multiple files (comma-separated filenames or `all` for everything in the source directory)

## Configuration

Configuration is stored in `conf/videotr.conf` (INI format):

```ini
[Directories]
input_dir = /path/to/videos
stage_dir = /path/to/temp
output_dir = /path/to/output
logs_dir = /path/to/logs

[Model]
model = base

[Language]
language = auto

[Processing]
device = auto
```

On first run, the CLI prompts for all settings. CLI flags override config file values.

## FFmpeg Commands

**Audio extraction:**
```bash
ffmpeg -i INPUT -vn -acodec pcm_s16le -ar 16000 -ac 1 -y OUTPUT.wav
```

**Video info:**
```bash
ffprobe -v error -print_format json -show_format -show_streams VIDEO
```

**Segment extraction:**
```bash
ffmpeg -i INPUT -ss START -t DURATION -vn -acodec pcm_s16le -ar 16000 -ac 1 -y OUTPUT.wav
```

## Output Naming

- **CLI**: `{video_name}_transcript.md` (configurable suffix)
- **Web UI**: `{video_name}_videotr.md`

## Dependencies

- Python 3.10+
- FFmpeg (must be on PATH)
- OpenAI Whisper (`openai-whisper`)
- Click (CLI framework)
- PyTorch (GPU acceleration via CUDA, optional)
