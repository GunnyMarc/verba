# Stream Transcriber (`streamtr`)

Capture audio from streaming URLs via FFmpeg and transcribe to markdown using OpenAI Whisper.

## Architecture

```
streamtr/
├── __init__.py           # Package marker
├── README.md             # This file
├── conf/                 # Configuration directory (auto-created)
│   └── streamtr.conf     # Runtime settings
├── input/                # Placeholder for batch URL files
└── src/
    ├── __init__.py       # Package exports
    ├── cli.py            # Click-based CLI entry point
    ├── config.py         # Configuration management
    ├── capture.py        # Stream capture via FFmpeg
    ├── transcriber.py    # Whisper speech-to-text
    ├── formatter.py      # Markdown output formatting
    └── pipeline.py       # Orchestration pipeline
```

## Modules

| Module | Purpose |
|---|---|
| `capture.py` | Captures audio from stream URLs using FFmpeg subprocess |
| `transcriber.py` | Whisper model loading and audio-to-text transcription |
| `formatter.py` | Converts transcription results to markdown (4 styles) |
| `pipeline.py` | Orchestrates capture → transcribe → format → save |
| `config.py` | Manages `streamtr.conf` settings (dirs, model, device) |
| `cli.py` | Click CLI with interactive prompts and subcommands |

## Usage

```bash
# Interactive mode (prompts for URL and settings)
python -m streamtr.src.cli

# With options
python -m streamtr.src.cli --model medium --device cuda -d 5m

# List available Whisper models
python -m streamtr.src.cli models

# Configure settings interactively
python -m streamtr.src.cli --configure
```

## CLI Options

| Flag | Description |
|---|---|
| `-m, --model` | Whisper model (tiny/base/small/medium/large/large-v2/large-v3) |
| `--device` | Processing device (cuda/cpu) |
| `-l, --language` | Language code (e.g., `en`, `es`) |
| `-s, --style` | Markdown style (simple/timestamped/detailed/srt_style) |
| `-d, --duration` | Capture duration (`60`, `5m`, `1h30m`). Default: until stream ends |
| `--keep-captured` | Keep the captured WAV file after transcription |
| `--no-metadata` | Exclude metadata from markdown output |
| `-q, --quiet` | Suppress progress output |
| `--configure` | Edit streamtr.conf interactively |
| `--clear-cache` | Remove `__pycache__` directories |

## FFmpeg Commands

Stream capture:
```bash
ffmpeg -i URL -vn -acodec pcm_s16le -ar 16000 -ac 1 [-t DURATION] -y output.wav
```

Stream probe:
```bash
ffprobe -v error -print_format json -show_format -show_streams URL
```

## Duration Format

- Plain seconds: `60`, `90.5`
- Minutes: `5m`
- Hours: `1h`
- Combinations: `1h30m`, `2h15m30s`

## Dependencies

- Python 3.8+
- [FFmpeg](https://ffmpeg.org/) (must be in PATH)
- [OpenAI Whisper](https://github.com/openai/whisper) (`pip install openai-whisper`)
- [Click](https://click.palletsprojects.com/) (`pip install click`)
- [PyTorch](https://pytorch.org/) (required by Whisper)
