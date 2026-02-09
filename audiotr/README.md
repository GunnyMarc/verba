# audiotr — Audio Transcription Pipeline

Processes audio files directly via OpenAI Whisper and outputs formatted markdown transcripts. Converts audio to the optimal format (16kHz mono WAV) before transcription.

## Architecture

```
TranscriptionPipeline.process(audio_path)
│
├─ [0%]  Validate audio file (format, existence)
├─ [5%]  Get audio info via FFprobe (duration, codec, sample rate)
├─ [10%] Prepare audio via FFmpeg (convert to 16kHz mono WAV if needed)
├─ [20%] Audio preparation complete
├─ [25%] Load Whisper model (auto-detect GPU/CPU)
├─ [30%] Transcribe audio (→ segments with timestamps)
├─ [80%] Format as markdown (selected style)
├─ [90%] Save markdown file
└─ [100%] Complete → PipelineResult
```

## Modules

| File | Class/Function | Purpose |
|------|---------------|---------|
| `src/pipeline.py` | `TranscriptionPipeline` | Orchestrates the full workflow: prepare → transcribe → format → save |
| `src/processor.py` | `AudioProcessor` | Audio format validation, metadata extraction, and conversion via FFmpeg |
| `src/transcriber.py` | `Transcriber` | Speech-to-text transcription using OpenAI Whisper |
| `src/formatter.py` | `MarkdownFormatter` | Converts transcription results to styled markdown |
| `src/config.py` | Configuration | FFmpeg verification, config file management, model/device prompts |
| `src/cli.py` | CLI | Click-based command-line interface |

## Supported Audio Formats

| Extension | Description |
|-----------|-------------|
| `.mp3` | MPEG Audio Layer III |
| `.wav` | Waveform Audio File |
| `.aac` | Advanced Audio Coding |
| `.flac` | Free Lossless Audio Codec |
| `.m4a` | MPEG-4 Audio |
| `.ogg` | Ogg Vorbis Audio |
| `.wma` | Windows Media Audio |
| `.opus` | Opus Audio |
| `.aiff` | Audio Interchange File Format |
| `.alac` | Apple Lossless Audio Codec |

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
python -m audiotr.src.cli [OPTIONS]
```

### Main Options

| Flag | Description | Default |
|------|-------------|---------|
| `-m`, `--model` | Whisper model (`tiny`..`large-v3`) | from config |
| `--device` | Processing device (`cuda`, `cpu`) | from config |
| `-l`, `--language` | Language code (e.g., `en`, `es`) or auto-detect | from config |
| `-s`, `--style` | Markdown style (`simple`, `timestamped`, `detailed`, `srt_style`) | `timestamped` |
| `--keep-converted` | Keep the converted WAV file after processing | off |
| `--no-metadata` | Exclude metadata header from output | off |
| `-q`, `--quiet` | Suppress progress output (only print output path) | off |
| `--configure` | Interactive configuration editor | — |
| `--clear-cache` | Remove `__pycache__` directories and exit | — |

### Subcommands

| Command | Description |
|---------|-------------|
| `info AUDIO` | Display audio metadata (duration, codec, sample rate, channels, bitrate) |
| `models` | List available Whisper models with parameters and VRAM requirements |
| `formats` | List supported audio formats |

### Transcription Modes

When run interactively, the CLI prompts for a mode:

1. **Transcribe** — Process a single audio file
2. **Batch** — Process multiple files (comma-separated filenames or `all` for everything in the source directory)

## Configuration

Configuration is stored in `conf/audiotr.conf` (INI format):

```ini
[Directories]
input_dir = /path/to/audio
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

## Audio Conversion

The processor automatically checks if conversion is needed before calling FFmpeg. Audio is skipped if already in the correct format (16kHz mono WAV).

**Conversion command:**
```bash
ffmpeg -i INPUT -acodec pcm_s16le -ar 16000 -ac 1 -y OUTPUT.wav
```

**Audio info:**
```bash
ffprobe -v error -print_format json -show_format -show_streams AUDIO
```

**Segment extraction:**
```bash
ffmpeg -i INPUT -ss START -t DURATION -acodec pcm_s16le -ar 16000 -ac 1 -y OUTPUT.wav
```

## Output Naming

- **CLI**: `{audio_name}_transcript.md` (configurable suffix)
- **Web UI**: `{audio_name}_audiotr.md`

## Dependencies

- Python 3.10+
- FFmpeg (must be on PATH)
- OpenAI Whisper (`openai-whisper`)
- Click (CLI framework)
- PyTorch (GPU acceleration via CUDA, optional)
