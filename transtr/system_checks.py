"""System checks: OS detection, Python version, model verification."""

import platform
import subprocess
import sys


LINUX_DISTRO_MAP = {
    "ubuntu": "Ubuntu:latest",
    "rhel": "RHEL:latest",
    "red hat": "RHEL:latest",
    "suse": "SuSe Linux:latest",
    "sles": "SuSe Linux:latest",
    "rocky": "RockOS:latest",
}

MODEL_INSTALL_INSTRUCTIONS = """\
=== How to install Ollama models ===

1. Install Ollama (if not already installed):
     Visit: https://ollama.com/download

2. Start the Ollama service:
     macOS / Linux : ollama serve
     Windows       : Ollama runs automatically after installation

3. Pull the desired model:
     ollama pull llama:latest
     ollama pull mistral:7b
     ollama pull mixtral:8x7b
     ollama pull mixtral:8x22b
     ollama pull qwen2.5:latest
     ollama pull gemma2:latest
     ollama pull gemma3:latest

4. Verify the model is available:
     ollama list

5. Re-run Transtr:
     python main.py
========================================
"""


def detect_os() -> str:
    """Detect host OS and return the canonical OS string from the allowed list."""
    system = platform.system()

    if system == "Darwin":
        return "macos:latest"

    if system == "Windows":
        return "Windows Server:latest"

    if system == "Linux":
        distro_id = ""
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro_id = line.strip().split("=", 1)[1].strip('"').lower()
                    elif line.startswith("ID_LIKE="):
                        distro_id = distro_id or line.strip().split("=", 1)[1].strip('"').lower()
        except FileNotFoundError:
            pass

        for key, value in LINUX_DISTRO_MAP.items():
            if key in distro_id:
                return value

        print(f"WARNING: Linux distribution '{distro_id}' not in allowed OS list.")
        print("Allowed: Ubuntu:latest | macos:latest | RHEL:latest | SuSe Linux:latest | RockOS:latest | Windows Server:latest")
        sys.exit(1)

    print(f"ERROR: Unsupported platform '{system}'.")
    sys.exit(1)


def get_python_version() -> str:
    """Return the current Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_python_version():
    """Verify Python version is 3.10+."""
    if sys.version_info < (3, 10):
        print(f"ERROR: Python 3.10+ required. Current: {get_python_version()}")
        sys.exit(1)
    print(f"  Python version: {get_python_version()} [OK]")


def check_model_installed(model: str, is_cloud: bool = False):
    """Check if the selected model is available. Skips local check for cloud models."""
    if is_cloud:
        print(f"  Model '{model}' is a cloud model — skipping local install check [OK]")
        return
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        print("ERROR: 'ollama' command not found. Please install Ollama first.")
        print(MODEL_INSTALL_INSTRUCTIONS)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("ERROR: Failed to query Ollama for installed models.")
        print(MODEL_INSTALL_INSTRUCTIONS)
        sys.exit(1)

    # Parse ollama list output — model names appear in the first column
    installed = set()
    for line in result.stdout.strip().splitlines()[1:]:  # skip header
        parts = line.split()
        if parts:
            installed.add(parts[0].strip())

    # Check with and without tag for flexibility (e.g. "llama:latest" or "llama")
    model_base = model.split(":")[0]
    found = any(
        m == model or m == model_base or m.startswith(model_base + ":")
        for m in installed
    )

    if found:
        print(f"  Model '{model}' is installed [OK]")
    else:
        print(f"\nERROR: Model '{model}' is not installed.")
        print(f"  Installed models: {', '.join(sorted(installed)) if installed else '(none)'}")
        print(MODEL_INSTALL_INSTRUCTIONS)
        sys.exit(1)
