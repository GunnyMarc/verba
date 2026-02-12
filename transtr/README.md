# transtr — Transcript Summarization

Summarizes transcript text using LLMs. Supports local inference via Ollama and cloud providers (OpenAI, Google Gemini, Anthropic Claude, Circuit/Cisco).

## Architecture

```
summarize(transcript_text, instructions, model, base_url)
│
├─ is_circuit_model(model)?    → _summarize_circuit()   [Circuit API]
├─ is_anthropic_model(model)?  → _summarize_anthropic() [Anthropic SDK]
├─ is_openai_model(model)?     → _summarize_openai()    [OpenAI SDK]
├─ is_google_model(model)?     → _summarize_google()    [Google SDK]
└─ default                     → _summarize_ollama()    [Ollama /api/chat]
```

All backends use the same message structure:
- **System message**: Summarization instructions (markdown)
- **User message**: Transcript text to summarize

## Modules

| File | Purpose |
|------|---------|
| `summarizer.py` | Core `summarize()` function with backend routing to Ollama, OpenAI, Google, and Circuit |
| `config_manager.py` | Model definitions, vendor detection functions, configuration file management |
| `system_checks.py` | OS detection, Python version check, Ollama model installation verification |
| `conf/transtr.conf` | INI configuration file |

## Available Models

### Ollama (Local)

| Model | Display Name |
|-------|-------------|
| `llama3:latest` | Llama 3 (Local) |
| `llama3.2:latest` | Llama 3.2 (Local) |
| `mistral:latest` | Mistral (Local) |
| `mistral:7b` | Mistral 7B |
| `mixtral:8x7b` | Mixtral 8x7B |
| `mixtral:8x22b` | Mixtral 8x22B |
| `qwen2.5:latest` | Qwen 2.5 |
| `gemma2:latest` | Gemma 2 |
| `gemma3:latest` | Gemma 3 |

### OpenAI (Commercial)

| Model | Display Name | Requires |
|-------|-------------|----------|
| `gpt-4o` | OpenAI GPT-4o | `OPENAI_API_KEY` |
| `gpt-4o-mini` | OpenAI GPT-4o-mini | `OPENAI_API_KEY` |

### Google (Commercial)

| Model | Display Name | Requires |
|-------|-------------|----------|
| `gemini-1.5-flash` | Google Gemini 1.5 Flash | `GOOGLE_API_KEY` |
| `gemini-1.5-pro` | Google Gemini 1.5 Pro | `GOOGLE_API_KEY` |

### Anthropic (Commercial)

| Model | Display Name | Requires |
|-------|-------------|----------|
| `claude-opus-4-6` | Anthropic Claude Opus 4 (6) | `ANTHROPIC_API_KEY` |
| `claude-sonnet-4-5-20250929` | Anthropic Claude Sonnet 4.5 | `ANTHROPIC_API_KEY` |
| `claude-haiku-4-5-20251001` | Anthropic Claude Haiku 4.5 | `ANTHROPIC_API_KEY` |

### Circuit (Cisco-only)

| Model | Display Name | Requires |
|-------|-------------|----------|
| `circuit-internal` | Circuit-Internal Cisco Data | `CIRCUIT_API_KEY` |
| `circuit-anthropic` | Circuit-Anthropic | `CIRCUIT_API_KEY` |
| `circuit-openai` | Circuit-OpenAI | `CIRCUIT_API_KEY` |
| `circuit-google` | Circuit-Google | `CIRCUIT_API_KEY` |

## Backend Details

### Ollama

- **Endpoint**: `POST {base_url}/api/chat` (default: `http://localhost:11434/api/chat`)
- **Auth**: None (local service)
- **Timeout**: 600 seconds
- **Response**: `response.json()["message"]["content"]`

### OpenAI

- **Client**: `openai.OpenAI()` (reads `OPENAI_API_KEY` from env)
- **Max tokens**: 4096
- **Response**: `response.choices[0].message.content`

### Google Gemini

- **Client**: `google.generativeai` (reads `GOOGLE_API_KEY` from env)
- **System instruction**: Passed via `GenerativeModel(system_instruction=...)`
- **Response**: `response.text`

### Anthropic Claude

- **Client**: `anthropic.Anthropic()` (reads `ANTHROPIC_API_KEY` from env)
- **System message**: Passed via `system=...` parameter
- **Max tokens**: 4096
- **Response**: `response.content[0].text`

### Circuit (Cisco)

- **Endpoint**: `POST {CIRCUIT_BASE_URL}/chat/completions` (default: `https://circuit.cisco.com/v1`)
- **Auth**: Bearer token via `CIRCUIT_API_KEY`
- **Max tokens**: 4096
- **Timeout**: 600 seconds
- **Response**: OpenAI-compatible format `response.json()["choices"][0]["message"]["content"]`

## Environment Variables

| Variable | Required For | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI models | — |
| `GOOGLE_API_KEY` | Google models | — |
| `ANTHROPIC_API_KEY` | Anthropic models | — |
| `CIRCUIT_API_KEY` | Circuit models | — |
| `CIRCUIT_BASE_URL` | Circuit endpoint | `https://circuit.cisco.com/v1` |

## Configuration

Configuration is stored in `conf/transtr.conf` (INI format):

```ini
[system]
os = macos:latest
python_version = 3.14.2

[model]
name = llama3:latest

[directories]
input_dir = /path/to/transcripts
stage_dir = /path/to/stage
output_dir = /path/to/output
instructions_dir = /path/to/instructions
log_dir = /path/to/logs

[instructions]
instructions_file = instructions_main.md
```

### Configuration Functions

| Function | Purpose |
|----------|---------|
| `ensure_conf()` | Create config directory and file if missing |
| `save_config()` | Write config to disk |
| `display_config()` | Print current settings |
| `reconfigure()` | Interactive editor for all settings |

### Model Detection Functions

| Function | Returns `True` for |
|----------|-------------------|
| `is_openai_model(model)` | `gpt-4o`, `gpt-4o-mini` |
| `is_google_model(model)` | `gemini-1.5-flash`, `gemini-1.5-pro` |
| `is_anthropic_model(model)` | `claude-opus-4-6`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001` |
| `is_circuit_model(model)` | `circuit-internal`, `circuit-anthropic`, `circuit-openai`, `circuit-google` |
| `is_cloud_model(model)` | All of the above |

## System Checks

`system_checks.py` provides runtime verification:

| Function | Purpose |
|----------|---------|
| `detect_os()` | Detect host OS (macOS, Windows, Ubuntu, RHEL, SuSE, Rocky) |
| `get_python_version()` | Return Python version string |
| `check_python_version()` | Verify Python >= 3.10 |
| `check_model_installed()` | Verify Ollama model is available (skips for cloud models) |

## Output Naming

- **Web UI**: `{input_name}_summary.md`

## Dependencies

- Python 3.10+
- `requests` (Ollama and Circuit HTTP calls)
- `openai` (OpenAI SDK)
- `anthropic` (Anthropic SDK)
- `google-generativeai` (Google Gemini SDK)
- Ollama (optional, for local models) — [ollama.com/download](https://ollama.com/download)
