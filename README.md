# Verba

A web-based media processing suite for transcribing video/audio files and summarizing transcripts using Whisper and LLMs.

Built with **FastAPI**, **HTMX**, and **Jinja2**. Jobs run in background threads with real-time SSE progress streaming to the browser.

## Application Architecture

### Overview

```
Browser (HTMX) <──SSE/HTML──> FastAPI (Uvicorn) ──> Adapters ──> Processing Pipelines
                                    │
                                    ├── JobManager    (in-memory, thread-safe)
                                    ├── KeyStore      (Fernet-encrypted API keys)
                                    └── WebSettings   (mutable runtime config)
```

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **App Factory** | `web/app.py` | Creates the FastAPI app, mounts static files, registers route blueprints, and initializes shared state via the async lifespan context |
| **Config** | `web/config.py` | Supported file formats, Whisper model/device choices, LLM model definitions, API key vendor mapping, and the `WebSettings` class |
| **Job Manager** | `web/jobs.py` | Thread-safe `Job` and `JobManager` classes for creating, tracking, and querying processing jobs with progress callbacks |
| **KeyStore** | `web/keystore.py` | Fernet-encrypted on-disk storage for API keys (`.verba.key` + `.verba_keys.dat`), with `apply_to_env()` to inject keys into environment variables |
| **Entry Point** | `web/run.py` | Launches Uvicorn on port `30319` with hot-reload and optional SSL (`web/certs/`) |

### Processing Pipeline

1. User submits a file or text via an HTMX form
2. The route handler saves the upload, creates a `Job`, and submits work to a `ThreadPoolExecutor` (3 workers)
3. The appropriate **Adapter** calls the external pipeline (`videotr`, `audiotr`, or `transtr`) and updates job progress
4. The browser receives real-time progress via **Server-Sent Events** (SSE) rendered as HTML partials
5. On completion, the result partial replaces the progress card with output preview and download link

### Adapters

Adapters wrap external sibling packages and expose a uniform `run()` / `run_batch()` interface:

| Adapter | External Package | Function |
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
| `/settings` | `routes/settings_routes.py` | Global settings and API key management |

### Frontend

- **HTMX** handles form submissions, SSE subscriptions, and partial HTML swaps (no custom JavaScript framework)
- **Jinja2** templates with a shared `base.html` layout (nav bar, main content area, footer)
- **Partials** (`progress.html`, `progress_bar.html`, `result.html`, `error.html`) are returned as HTML fragments for in-page updates
- Dark-themed UI styled via `static/style.css` with CSS custom properties

## File Structure

```
verba/
├── README.md
├── .gitignore
└── web/
    ├── __init__.py
    ├── app.py                  # FastAPI app factory & lifespan
    ├── config.py               # Settings, format constants, model defs
    ├── jobs.py                 # Job / JobManager (thread-safe)
    ├── keystore.py             # Fernet-encrypted API key storage
    ├── run.py                  # Uvicorn entry point (port 30319)
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
    │   └── settings_routes.py  # /settings
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
        ├── settings.html       # Settings & API key management
        └── partials/
            ├── error.html      # Error message fragment
            ├── progress.html   # SSE progress container
            ├── progress_bar.html # Progress bar update fragment
            └── result.html     # Job result display fragment
```

**Runtime directories** (gitignored, created automatically on startup):

| Directory | Purpose |
|-----------|---------|
| `web/uploads/` | Temporarily stores uploaded files |
| `web/output/` | Stores generated transcripts/summaries |
| `web/certs/` | Optional SSL certificate and key (`cert.pem`, `key.pem`) |
| `videotr/input/` | Drop folder for video batch processing |
| `audiotr/input/` | Drop folder for audio batch processing |
| `transtr/input/` | Drop folder for transcript batch processing |

## Usage

### Prerequisites

- Python 3.10+
- External sibling packages (`videotr`, `audiotr`, `transtr`) installed at the repo root for full pipeline functionality
- For transcription: a Whisper-compatible environment
- For summarization: Ollama running locally, or API keys for OpenAI / Google

### Installation

```bash
cd verba
python -m venv venv
source venv/bin/activate
pip install -r web/requirements.txt
```

### Running the Server

```bash
python -m web.run
```

The application starts on **https://localhost:30319** with hot-reload enabled.

To enable HTTPS, place `cert.pem` and `key.pem` in `web/certs/`.

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

### API Keys

API keys for cloud LLM providers are managed on the Settings page. Keys are encrypted at rest using Fernet symmetric encryption and injected into environment variables at startup.

Supported vendors: **OpenAI**, **Google**, **Anthropic**, **Ollama**, **Circuit**, **Abacus ChatLLM**

### Batch Processing

Each tool supports batch mode. Place files in the corresponding input directory and enable the "Batch Process" toggle:

- `videotr/input/` for video files
- `audiotr/input/` for audio files
- `transtr/input/` for transcript files
