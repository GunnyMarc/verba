"""Ollama utility functions: check availability, list models, pull models."""

import subprocess
import shutil


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


def pull_model(model: str, job) -> bool:
    """Pull an Ollama model, updating job progress. Returns True on success."""
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                job.update_progress(50, f"Downloading: {line}")
        process.wait()
        return process.returncode == 0
    except Exception as e:
        job.fail(str(e))
        return False
