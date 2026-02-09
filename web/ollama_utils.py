"""Ollama utility functions: check availability, list models, pull models."""

import subprocess
import shutil
import urllib.request
import json
from typing import Optional


def is_ollama_available() -> bool:
    """Check if ollama CLI is available."""
    return shutil.which("ollama") is not None


def get_installed_models() -> set[str]:
    """Return set of installed Ollama model names."""
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )
        models = set()
        for line in result.stdout.strip().splitlines()[1:]:  # skip header
            if line.strip():
                models.add(line.split()[0])
        return models
    except Exception:
        return set()


def is_model_installed(model: str) -> bool:
    """Check if a specific Ollama model is installed."""
    return model in get_installed_models()


def get_model_download_size(model: str) -> Optional[int]:
    """Query the Ollama registry for the total download size of a model in bytes.

    Returns None if the size cannot be determined.
    """
    # Split "name:tag" — default tag is "latest"
    if ":" in model:
        name, tag = model.rsplit(":", 1)
    else:
        name, tag = model, "latest"

    url = f"https://registry.ollama.ai/v2/library/{name}/manifests/{tag}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            manifest = json.loads(resp.read())
        total = 0
        for layer in manifest.get("layers", []):
            total += layer.get("size", 0)
        config_size = manifest.get("config", {}).get("size", 0)
        total += config_size
        return total if total > 0 else None
    except Exception:
        return None


def format_size(size_bytes: int) -> str:
    """Format byte count into a human-readable string."""
    if size_bytes >= 1 << 30:
        return f"{size_bytes / (1 << 30):.1f} GB"
    if size_bytes >= 1 << 20:
        return f"{size_bytes / (1 << 20):.1f} MB"
    if size_bytes >= 1 << 10:
        return f"{size_bytes / (1 << 10):.1f} KB"
    return f"{size_bytes} B"


def pull_model(model: str, job) -> bool:
    """Pull an Ollama model, updating job progress. Returns True on success.

    Stores the subprocess on job._process so it can be terminated externally.
    """
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        job._process = process
        for line in process.stdout:
            line = line.strip()
            if line:
                job.update_progress(50, f"Downloading: {line}")
        process.wait()
        return process.returncode == 0
    except Exception as e:
        job.fail(str(e))
        return False
