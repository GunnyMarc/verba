# Verba

A web-based media processing suite for transcribing video/audio files and summarizing transcripts using Whisper and LLMs.

Built with **FastAPI**, **HTMX**, and **Jinja2**. Jobs run in background threads with real-time SSE progress streaming to the browser. All traffic is served over **HTTPS on port 30319**.

## Application Architecture

### Overview

```
Browser (HTMX) <──SSE/HTML──> FastAPI (Uvicorn/HTTPS) ──> Adapters ──> Processing Pipelines
                                        │
                                        ├── JobManager    (in-memory, thread-safe)
                                        ├── KeyStore      (Fernet-encrypted API keys)
                                        └── WebSettings   (mutable runtime config)

  verba.sh ──> web/run.py ──> Uvicorn (HTTPS, localhost:30319, auto-reload)
                   └── auto-generates self-signed TLS cert on first run
```

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **Startup Script** | `verba.sh` | Bash entry point for start/stop/status/log management; creates the virtual environment (`web/webui`) and launches the server as a background process |
| **App Factory** | `web/app.py` | Creates the FastAPI app, mounts static files, registers route blueprints, and initializes shared state via the async lifespan context |
| **Config** | `web/config.py` | Supported file formats, Whisper model/device choices, LLM model definitions, API key vendor mapping, and the `WebSettings` class |
| **Job Manager** | `web/jobs.py` | Thread-safe `Job` and `JobManager` classes for creating, tracking, and querying processing jobs with progress callbacks |
| **KeyStore** | `web/keystore.py` | Fernet-encrypted on-disk storage for API keys (`.verba.key` + `.verba_keys.dat`), with `apply_to_env()` to inject keys into environment variables |
| **Entry Point** | `web/run.py` | Launches Uvicorn over HTTPS on `localhost:30319` with hot-reload; auto-generates a self-signed TLS certificate via the `cryptography` library if none exists |

### Processing Pipelines

The processing pipelines are bundled as sibling packages at the repository root:

| Package | Purpose |
|---------|---------|
| `videotr/` | Video-to-text transcription — extracts audio from video files, transcribes via Whisper, and formats as markdown |
| `audiotr/` | Audio-to-text transcription — processes audio files directly via Whisper and formats as markdown |
| `transtr/` | Transcript summarization — sends text to LLMs (Ollama, OpenAI, or Google Gemini) with configurable instructions |

Each pipeline is called by a corresponding **Adapter** in `web/adapters/` that provides a uniform `run()` / `run_batch()` interface with real-time progress tracking.

### Processing Flow

1. User submits a file or text via an HTMX form
2. The route handler saves the upload, creates a `Job`, and submits work to a `ThreadPoolExecutor` (3 workers)
3. The appropriate **Adapter** calls the pipeline and updates job progress via callbacks
4. The browser receives real-time progress via **Server-Sent Events** (SSE) rendered as HTML partials
5. On completion, the result partial replaces the progress card with output preview and download link

### Progress Tracking

Progress is tracked end-to-end from the pipeline to the browser:

- **Single file mode**: The pipeline reports granular progress (validating → extracting audio → loading model → transcribing → formatting → saving) with percentage updates at each stage
- **Batch mode**: Overall progress is divided across files, with per-file pipeline progress mapped into the batch's percentage range (e.g., file 3 of 5 at 50% transcription = 50% overall)
- **SSE delivery**: The server polls the job every 0.5 seconds and streams HTML progress bar updates to the browser via HTMX's SSE extension

### Adapters

Adapters wrap the sibling pipeline packages and expose a uniform interface:

| Adapter | Pipeline Package | Function |
|---------|-----------------|----------|
| `VideotrAdapter` | `videotr.src.pipeline` | Video-to-text transcription via Whisper |
| `AudiotrAdapter` | `audiotr.src.pipeline` | Audio-to-text transcription via Whisper |
| `TranstrAdapter` | `transtr.summarizer` | Transcript summarization via LLMs (Ollama, OpenAI, Google) |

### Routes

| Prefix | Module | Endpoints |
|--------|--------|-----------|
| `/` | `routes/dashboard.py` | Dashboard with tool cards and recent jobs |
| `/videotr` | `routes/videotr_routes.py` | Form, upload, SSE stream, result, download |
| `/audiotr` | `routes/audiotr_routes.py` | Form, upload, SSE stream, result, download |
| `/transtr` | `routes/transtr_routes.py` | Form, process (text or file), SSE stream, result |
| `/settings` | `routes/settings_routes.py` | Global settings, API key management, directory browser |

### Frontend

- **HTMX** handles form submissions, SSE subscriptions, and partial HTML swaps (no custom JavaScript framework)
- **Jinja2** templates with a shared `base.html` layout (nav bar, main content area, footer)
- **Partials** (`progress.html`, `progress_bar.html`, `result.html`, `error.html`, `browse.html`) are returned as HTML fragments for in-page updates
- Dark-themed UI styled via `static/style.css` with CSS custom properties

## File Structure

```
verba/
├── README.md
├── .gitignore
├── verba.sh                    # Startup script (start/stop/status/log/clear-cache)
│
├── videotr/                    # Video transcription pipeline
│   ├── __init__.py
│   ├── input/                  # Default batch input directory
│   └── src/
│       ├── __init__.py
│       ├── pipeline.py         # TranscriptionPipeline (orchestrates full workflow)
│       ├── extractor.py        # AudioExtractor (video → audio via FFmpeg)
│       ├── transcriber.py      # Transcriber (audio → text via Whisper)
│       ├── formatter.py        # MarkdownFormatter (text → styled markdown)
│       ├── config.py           # Pipeline configuration
│       └── cli.py              # CLI entry point
│
├── audiotr/                    # Audio transcription pipeline
│   ├── __init__.py
│   ├── input/                  # Default batch input directory
│   └── src/
│       ├── __init__.py
│       ├── pipeline.py         # TranscriptionPipeline (orchestrates full workflow)
│       ├── processor.py        # AudioProcessor (format conversion via FFmpeg)
│       ├── transcriber.py      # Transcriber (audio → text via Whisper)
│       ├── formatter.py        # MarkdownFormatter (text → styled markdown)
│       ├── config.py           # Pipeline configuration
│       └── cli.py              # CLI entry point
│
├── transtr/                    # Transcript summarization
│   ├── __init__.py
│   ├── input/                  # Default batch input directory
│   ├── summarizer.py           # summarize() — routes to Ollama, OpenAI, or Google
│   ├── config_manager.py       # Model definitions, vendor detection
│   ├── system_checks.py        # Runtime environment checks
│   └── conf/                   # Configuration files
│
└── web/                        # FastAPI web application
    ├── __init__.py
    ├── app.py                  # FastAPI app factory & lifespan
    ├── config.py               # Settings, format constants, model defs
    ├── jobs.py                 # Job / JobManager (thread-safe)
    ├── keystore.py             # Fernet-encrypted API key storage
    ├── run.py                  # Uvicorn entry point (HTTPS, localhost:30319)
    ├── requirements.txt        # Python dependencies
    │
    ├── adapters/
    │   ├── __init__.py
    │   ├── base.py             # suppress_stdout(), make_progress_callback()
    │   ├── videotr_adapter.py  # VideotrAdapter.run() / run_batch()
    │   ├── audiotr_adapter.py  # AudiotrAdapter.run() / run_batch()
    │   └── transtr_adapter.py  # TranstrAdapter.run() / run_batch()
    │
    ├── routes/
    │   ├── __init__.py
    │   ├── dashboard.py        # GET /
    │   ├── videotr_routes.py   # /videotr/*
    │   ├── audiotr_routes.py   # /audiotr/*
    │   ├── transtr_routes.py   # /transtr/*
    │   └── settings_routes.py  # /settings, /settings/browse
    │
    ├── static/
    │   └── style.css           # Dark-themed UI styles
    │
    └── templates/
        ├── base.html           # Shared layout (nav, content, footer)
        ├── dashboard.html      # Tool cards + recent jobs
        ├── videotr.html        # Video transcription form
        ├── audiotr.html        # Audio transcription form
        ├── transtr.html        # Transcript summarization form
        ├── settings.html       # Settings, file locations, API key management
        └── partials/
            ├── browse.html     # Directory browser modal fragment
            ├── error.html      # Error message fragment
            ├── progress.html   # SSE progress container
            ├── progress_bar.html # Progress bar update fragment
            └── result.html     # Job result display fragment
```

**Runtime directories** (gitignored, created automatically):

| Directory | Purpose |
|-----------|---------|
| `web/webui/` | Python virtual environment (created by `verba.sh --start`) |
| `web/uploads/` | Temporarily stores uploaded files |
| `web/output/` | Default output directory for transcripts/summaries (configurable via Settings) |
| `web/certs/` | Auto-generated self-signed TLS certificate and key (`cert.pem`, `key.pem`) |
| `web/log/` | Timestamped server log files |

## Usage

### Prerequisites

- Python 3.9+
- FFmpeg installed and available on `PATH` (required for audio extraction)
- For transcription: a Whisper-compatible environment
- For summarization: Ollama running locally, or API keys for OpenAI / Google

### Starting the Application

```bash
./verba.sh --start
```

On first run this will:
1. Create a Python virtual environment in `web/webui/`
2. Install all dependencies from `web/requirements.txt`
3. Auto-generate a self-signed TLS certificate in `web/certs/`
4. Launch the server as a background process

Once started the application is available at **https://localhost:30319**.

To use your own TLS certificate, place `cert.pem` and `key.pem` in `web/certs/` before starting.

### Management Commands

| Command | Description |
|---------|-------------|
| `./verba.sh --start` | Start the application in the background |
| `./verba.sh --stop` | Gracefully stop the application (SIGTERM, 10s timeout) |
| `./verba.sh --force-stop` | Force kill the application and any processes on port 30319 |
| `./verba.sh --status` | Show running status, PID, URL, and latest log path |
| `./verba.sh --log` | Tail the latest log file |
| `./verba.sh --version` | Show version, port, and Python info |
| `./verba.sh --clear-cache` | Stop the app, remove venv, `__pycache__`, and API key files |
| `./verba.sh --help` | Show help message |

### Manual Start (without verba.sh)

```bash
cd verba
python -m venv web/webui
source web/webui/bin/activate
pip install -r web/requirements.txt
python -m web.run
```

### Supported File Formats

| Tool | Formats |
|------|---------|
| Video Transcription | `.mov` `.mp4` `.mkv` `.mpeg` `.avi` `.webm` |
| Audio Transcription | `.mp3` `.wav` `.flac` `.m4a` `.ogg` `.aac` `.wma` `.opus` `.aiff` `.alac` |
| Summarization | `.txt` `.md` `.csv` `.rtf` `.tsv` |

### Transcription Settings

Configurable via the Settings page or per-job overrides on each tool page:

| Setting | Options | Default |
|---------|---------|---------|
| Whisper Model | `tiny`, `base`, `small`, `medium`, `large` | `base` |
| Device | `auto`, `cpu`, `cuda`, `mps` | `auto` |
| Language | ISO 639-1 code or `auto` | `auto` |
| Markdown Style | `simple`, `timestamped`, `detailed`, `srt_style` | `timestamped` |
| Include Metadata | on/off | on |

### File Locations

Input and output directories for each tool are configurable from the Settings page under the **File Locations** section. Each directory field includes a **Browse** button that opens a directory browser modal for GUI-based navigation (including hidden and mounted directories).

| Setting | Default | Used By |
|---------|---------|---------|
| Video Input | `videotr/input/` | Video batch processing input directory |
| Video Transcribe Output | `web/output/` | Video transcription output (single and batch) |
| Audio Input | `audiotr/input/` | Audio batch processing input directory |
| Audio Transcribe Output | `web/output/` | Audio transcription output (single and batch) |
| Summary Input | `transtr/input/` | Summary batch processing input directory |
| Summary Output | `web/output/` | Reserved for future summary file output |

Custom directories are created automatically when saved. Paths reset to defaults on application restart.

### API Keys

API keys for cloud LLM providers are managed on the Settings page. Keys are encrypted at rest using Fernet symmetric encryption and injected into environment variables at startup.

Supported vendors: **OpenAI**, **Google**, **Anthropic**, **Ollama**, **Circuit**, **Abacus ChatLLM**

### Batch Processing

Each tool supports batch mode. Place files in the corresponding input directory (configurable under Settings > File Locations) and enable the "Batch Process" toggle on the tool page. Default input directories:

- `videotr/input/` for video files
- `audiotr/input/` for audio files
- `transtr/input/` for transcript files

### Summarization Models

The Summarize tool supports local and cloud LLM models, grouped by provider:

| Provider | Models |
|----------|--------|
| **Ollama (Local)** | `llama:latest`, `mistral:7b`, `mixtral:8x7b`, `mixtral:8x22b`, `qwen2.5:latest`, `gemma2:latest`, `gemma3:latest` |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini` (requires API key) |
| **Google** | `gemini-1.5-flash`, `gemini-1.5-pro` (requires API key) |
