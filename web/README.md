# web — Verba Web Application

FastAPI web application providing a browser-based interface for video/audio transcription and transcript summarization. Serves over HTTPS with real-time progress streaming via Server-Sent Events.

## Architecture

```
run.py → Uvicorn (HTTPS, localhost:30319, hot-reload)
  │
  └─ app.py (FastAPI lifespan)
       ├── JobManager      (in-memory, thread-safe job tracking)
       ├── KeyStore         (Fernet-encrypted API key storage)
       ├── WebSettings      (mutable runtime configuration)
       └── ThreadPoolExecutor (3 workers for background jobs)

Routes                          Adapters                    Pipelines
──────                          ────────                    ─────────
/            → dashboard.py
/videotr/*   → videotr_routes   → VideotrAdapter.run()   → videotr.src.pipeline
/audiotr/*   → audiotr_routes   → AudiotrAdapter.run()   → audiotr.src.pipeline
/transtr/*   → transtr_routes   → TranstrAdapter.run()   → transtr.summarizer
/settings    → settings_routes
```

## Modules

### Core

| File | Purpose |
|------|---------|
| `run.py` | Entry point. Generates self-signed TLS cert (RSA 2048-bit, SHA256, 365 days), writes PID file, launches Uvicorn |
| `app.py` | FastAPI app factory. Mounts static files, registers route blueprints, initializes shared state via async lifespan |
| `config.py` | `WebSettings` class, supported format constants, Whisper model/device choices, LLM model definitions, API key vendor mapping |
| `jobs.py` | `Job` (thread-safe status/progress tracking with events) and `JobManager` (in-memory job storage) |
| `keystore.py` | `KeyStore` class using Fernet encryption for API key storage (`.verba.key` + `.verba_keys.dat`) |
| `file_readers.py` | Multi-format file reader for instruction uploads (`.txt`, `.csv`, `.xlsx`, `.doc`, `.docx`, `.md`, `.pdf`) |

### Routes

| File | Prefix | Endpoints |
|------|--------|-----------|
| `routes/dashboard.py` | `/` | Dashboard page with tool cards and recent jobs |
| `routes/videotr_routes.py` | `/videotr` | Form, upload, browse, mkdir, SSE stream, result, download |
| `routes/audiotr_routes.py` | `/audiotr` | Form, upload, browse, mkdir, SSE stream, result, download |
| `routes/transtr_routes.py` | `/transtr` | Form, process, browse, mkdir, SSE stream, result |
| `routes/settings_routes.py` | `/settings` | Settings page, API key management |

### Adapters

| File | Class | Pipeline |
|------|-------|----------|
| `adapters/base.py` | Utilities | `suppress_stdout()` context manager, `make_progress_callback()` factory |
| `adapters/videotr_adapter.py` | `VideotrAdapter` | Wraps `videotr.src.pipeline.TranscriptionPipeline` |
| `adapters/audiotr_adapter.py` | `AudiotrAdapter` | Wraps `audiotr.src.pipeline.TranscriptionPipeline` |
| `adapters/transtr_adapter.py` | `TranstrAdapter` | Wraps `transtr.summarizer.summarize()` |

## API Endpoints

### Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard with recent jobs (last 10) |

### Video Transcription

| Method | Path | Description |
|--------|------|-------------|
| GET | `/videotr` | Video transcription form page |
| GET | `/videotr/browse` | Directory browser (query: `path`, `target`) |
| POST | `/videotr/browse/mkdir` | Create new directory (form: `path`, `name`, `target`) |
| POST | `/videotr/upload` | Upload and process video (form: file, settings, batch options) |
| GET | `/videotr/jobs/{job_id}/stream` | SSE progress stream (events: `progress`, `log`, `complete`, `error`) |
| GET | `/videotr/jobs/{job_id}/result` | Result display partial |
| GET | `/videotr/jobs/{job_id}/download` | Download output markdown file |

### Audio Transcription

| Method | Path | Description |
|--------|------|-------------|
| GET | `/audiotr` | Audio transcription form page |
| GET | `/audiotr/browse` | Directory browser |
| POST | `/audiotr/browse/mkdir` | Create new directory |
| POST | `/audiotr/upload` | Upload and process audio |
| GET | `/audiotr/jobs/{job_id}/stream` | SSE progress stream |
| GET | `/audiotr/jobs/{job_id}/result` | Result display partial |
| GET | `/audiotr/jobs/{job_id}/download` | Download output markdown file |

### Transcript Summarization

| Method | Path | Description |
|--------|------|-------------|
| GET | `/transtr` | Summarization form page |
| GET | `/transtr/browse` | Directory browser |
| POST | `/transtr/browse/mkdir` | Create new directory |
| POST | `/transtr/process` | Process transcript (form: text/file, model, instructions, batch options) |
| GET | `/transtr/jobs/{job_id}/stream` | SSE progress stream |
| GET | `/transtr/jobs/{job_id}/result` | Result display partial |

### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings` | Settings page |
| POST | `/settings` | Update settings and API keys |

## Job Lifecycle

```
PENDING → RUNNING → COMPLETED
                  → FAILED
```

- **Job ID**: 8-character hex string
- **Progress**: 0-100 integer with message string
- **Thread safety**: `threading.Lock` for state, `threading.Event` for update signaling
- **SSE polling**: 0.5-second interval

## TLS Certificate

Auto-generated on first run if `certs/cert.pem` and `certs/key.pem` don't exist:

- **Algorithm**: RSA 2048-bit
- **Signature**: SHA256
- **Subject**: `CN=localhost`
- **SANs**: `DNS:localhost`, `IP:127.0.0.1`
- **Validity**: 365 days
- **Key permissions**: `0o600`

Place your own `cert.pem` and `key.pem` in `certs/` to use a custom certificate.

## Encrypted API Key Storage

- **Encryption**: Fernet (AES-128-CBC with HMAC)
- **Key file**: `.verba.key` (permissions `0o600`)
- **Data file**: `.verba_keys.dat` (encrypted JSON)
- **`apply_to_env()`**: Reads stored keys and sets corresponding environment variables

## Templates

| Template | Description |
|----------|-------------|
| `base.html` | Shared layout with navigation bar, content area, footer |
| `dashboard.html` | Tool cards and recent job list |
| `videotr.html` | Video transcription form with batch toggle and browse |
| `audiotr.html` | Audio transcription form with batch toggle and browse |
| `transtr.html` | Summarization form with instructions file upload, batch toggle, browse |
| `settings.html` | Global settings, file locations, API key management |

### Partials (HTML fragments for HTMX swaps)

| Partial | Description |
|---------|-------------|
| `browse.html` | Directory browser modal with New Folder support |
| `error.html` | Error message display |
| `progress.html` | Generic SSE progress container |
| `videotr_progress.html` | Video progress with verbose log output |
| `progress_bar.html` | Progress bar update fragment |
| `result.html` | Job result with output preview and download |

## Runtime Directories

| Directory | Purpose | Created By |
|-----------|---------|------------|
| `webui/` | Python virtual environment | `verba.sh --start` |
| `uploads/` | Temporary file storage | Route handlers |
| `output/` | Default transcript/summary output | Adapters |
| `certs/` | TLS certificate and key | `run.py` |
| `log/` | Timestamped server logs | `verba.sh --start` |

## Dependencies (requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.115.0 | Web framework |
| `uvicorn[standard]` | >=0.32.0 | ASGI server with HTTPS |
| `jinja2` | >=3.1.0 | Template engine |
| `python-multipart` | >=0.0.12 | File upload handling |
| `sse-starlette` | >=2.1.0 | Server-Sent Events |
| `cryptography` | latest | TLS cert generation and Fernet encryption |
| `openai-whisper` | latest | Speech-to-text (used by videotr/audiotr adapters) |
| `openpyxl` | latest | Excel file reading |
| `python-docx` | latest | Word document reading |
| `PyPDF2` | latest | PDF file reading |
| `requests` | latest | HTTP client for Ollama/Circuit |
| `openai` | latest | OpenAI API client |
| `anthropic` | latest | Anthropic API client |
| `google-generativeai` | latest | Google Gemini API client |

## Running

### Via verba.sh (recommended)

```bash
./verba.sh --start    # Creates venv, installs deps, starts server
./verba.sh --stop     # Graceful shutdown
```

### Manual

```bash
python3 -m venv webui
source webui/bin/activate
pip install -r requirements.txt
python -m web.run
```

Server starts at **https://localhost:30319**.
