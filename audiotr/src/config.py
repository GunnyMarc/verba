"""
Configuration manager for audiotr.

Handles reading, writing, and prompting for audiotr.conf settings.
"""

import os
import sys
import platform
import configparser
import shutil
from pathlib import Path
from typing import Optional


# Base directory is where main.py lives
BASE_DIR = Path(__file__).parent.parent
CONF_DIR = BASE_DIR / "conf"
CONF_FILE = CONF_DIR / "audiotr.conf"

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
DEVICE_CHOICES = ["auto", "cuda", "cpu"]


def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed. If not, print install instructions and exit."""
    if shutil.which("ffmpeg") is not None:
        return True

    system = platform.system().lower()
    print("ERROR: ffmpeg is not installed or not found in PATH.")
    print("")
    if system == "darwin":
        print("  Install with Homebrew:")
        print("    brew install ffmpeg")
    elif system == "linux":
        distro = ""
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.strip().split("=")[1].strip('"')
                        break
        except FileNotFoundError:
            pass
        if distro in ("ubuntu", "debian"):
            print("  Install with apt:")
            print("    sudo apt update && sudo apt install ffmpeg")
        elif distro in ("fedora", "rhel", "centos"):
            print("  Install with dnf:")
            print("    sudo dnf install ffmpeg")
        elif distro in ("arch", "manjaro"):
            print("  Install with pacman:")
            print("    sudo pacman -S ffmpeg")
        else:
            print("  Install ffmpeg using your package manager, e.g.:")
            print("    sudo apt install ffmpeg")
            print("    sudo dnf install ffmpeg")
    elif system == "windows":
        print("  Download from: https://ffmpeg.org/download.html")
        print("  Or install with: choco install ffmpeg")
        print("  Or install with: winget install ffmpeg")
    else:
        print("  Download from: https://ffmpeg.org/download.html")
    print("")
    sys.exit(1)


def ensure_conf_dir_and_file():
    """Ensure conf directory and audiotr.conf exist, creating them if needed."""
    created_dir = False
    created_file = False

    if not CONF_DIR.exists():
        CONF_DIR.mkdir(parents=True, exist_ok=True)
        created_dir = True
        print(f"Created configuration directory: {CONF_DIR}")

    if not CONF_FILE.exists():
        CONF_FILE.touch()
        created_file = True
        print(f"Created configuration file: {CONF_FILE}")

    return created_dir, created_file


def load_config() -> configparser.ConfigParser:
    """Load the config file."""
    config = configparser.ConfigParser()
    if CONF_FILE.exists():
        config.read(str(CONF_FILE))
    return config


def save_config(config: configparser.ConfigParser):
    """Save the config file."""
    with open(CONF_FILE, "w") as f:
        config.write(f)


def config_is_empty(config: configparser.ConfigParser) -> bool:
    """Check if the config has no meaningful content."""
    return len(config.sections()) == 0


def prompt_directory(prompt_text: str, default: Optional[str] = None) -> str:
    """Prompt the user for a directory path and create it if needed."""
    while True:
        if default:
            raw = input(f"{prompt_text} [{default}]: ").strip()
            if not raw:
                raw = default
        else:
            raw = input(f"{prompt_text}: ").strip()

        if not raw:
            print("  Please enter a valid path.")
            continue

        path = os.path.expanduser(raw)
        path = os.path.abspath(path)

        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                print(f"  Created: {path}")
            except OSError as e:
                print(f"  Error creating directory: {e}")
                continue

        return path


def prompt_directories(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """Prompt the user for input_dir, stage_dir, output_dir, logs_dir."""
    print("")
    print("Configure working directories:")
    print("-" * 40)

    if not config.has_section("Directories"):
        config.add_section("Directories")

    for key, label in [
        ("input_dir", "Input directory (source audio files)"),
        ("stage_dir", "Staging directory (temporary files)"),
        ("output_dir", "Output directory (transcription results)"),
        ("logs_dir", "Logs directory"),
    ]:
        existing = config.get("Directories", key, fallback=None)
        value = prompt_directory(f"  {label}", default=existing)
        config.set("Directories", key, value)

    return config


def prompt_model(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """Prompt the user to select a Whisper model."""
    if not config.has_section("Model"):
        config.add_section("Model")

    print("")
    print("Select Whisper model:")
    for i, m in enumerate(WHISPER_MODELS, 1):
        print(f"  {i}. {m}")

    while True:
        raw = input(f"Choose model [1-{len(WHISPER_MODELS)}] (default: 2/base): ").strip()
        if not raw:
            choice = "base"
            break
        try:
            idx = int(raw)
            if 1 <= idx <= len(WHISPER_MODELS):
                choice = WHISPER_MODELS[idx - 1]
                break
        except ValueError:
            if raw in WHISPER_MODELS:
                choice = raw
                break
        print("  Invalid selection.")

    config.set("Model", "model", choice)
    return config


def prompt_language(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """Prompt the user for the transcription language."""
    if not config.has_section("Language"):
        config.add_section("Language")

    raw = input("Transcription language (2-char locale, e.g. en, es, fr) [auto]: ").strip()
    if not raw or raw.lower() == "auto":
        config.set("Language", "language", "auto")
    else:
        config.set("Language", "language", raw[:2].lower())

    return config


def prompt_device(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """Prompt the user for processing device."""
    if not config.has_section("Processing"):
        config.add_section("Processing")

    print("")
    print("Select processing device:")
    print("  1. auto (auto-detect GPU/CPU)")
    print("  2. cuda (GPU - requires NVIDIA GPU with CUDA)")
    print("  3. cpu")

    while True:
        raw = input("Choose device [1-3] (default: 1/auto): ").strip()
        if not raw:
            choice = "auto"
            break
        try:
            idx = int(raw)
            if idx == 1:
                choice = "auto"
                break
            elif idx == 2:
                choice = "cuda"
                break
            elif idx == 3:
                choice = "cpu"
                break
        except ValueError:
            if raw in DEVICE_CHOICES:
                choice = raw
                break
        print("  Invalid selection.")

    config.set("Processing", "device", choice)
    return config


def prompt_location(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """Prompt the user for the source file location."""
    if not config.has_section("Location"):
        config.add_section("Location")

    source = prompt_directory("Source file location")
    config.set("Location", "source", source)
    return config


def display_config(config: configparser.ConfigParser):
    """Display the current configuration."""
    print("")
    print("=" * 55)
    print("  audiotr Configuration (audiotr.conf)")
    print("=" * 55)

    if config.has_section("Model"):
        print(f"  Model:      {config.get('Model', 'model', fallback='N/A')}")

    if config.has_section("Directories"):
        print(f"  Input dir:  {config.get('Directories', 'input_dir', fallback='N/A')}")
        print(f"  Stage dir:  {config.get('Directories', 'stage_dir', fallback='N/A')}")
        print(f"  Output dir: {config.get('Directories', 'output_dir', fallback='N/A')}")
        print(f"  Logs dir:   {config.get('Directories', 'logs_dir', fallback='N/A')}")

    if config.has_section("Location"):
        print(f"  Source:     {config.get('Location', 'source', fallback='N/A')}")

    if config.has_section("Language"):
        print(f"  Language:   {config.get('Language', 'language', fallback='N/A')}")

    if config.has_section("Processing"):
        print(f"  Device:     {config.get('Processing', 'device', fallback='N/A')}")

    print("=" * 55)
    print("")


def initialize_config(cli_model: Optional[str] = None,
                      cli_device: Optional[str] = None) -> configparser.ConfigParser:
    """
    Full startup config initialization flow.

    Returns a fully populated config. CLI args override conf values.
    """
    ensure_conf_dir_and_file()
    config = load_config()

    if config_is_empty(config):
        print("No configuration found. Let's set up audiotr.")
        config = prompt_directories(config)
        config = prompt_model(config)
        config = prompt_language(config)
        config = prompt_device(config)
        save_config(config)
    else:
        # Verify directories exist, create if missing
        if config.has_section("Directories"):
            for key in ["input_dir", "stage_dir", "output_dir", "logs_dir"]:
                d = config.get("Directories", key, fallback=None)
                if d and not os.path.exists(d):
                    try:
                        os.makedirs(d, exist_ok=True)
                        print(f"  Created missing directory: {d}")
                    except OSError:
                        print(f"  Cannot create directory: {d}")
                        print("  Directory paths may be from another system. Re-prompting...")
                        config = prompt_directories(config)
                        save_config(config)
                        break

    # Prompt for anything still missing
    if not config.has_section("Directories") or not config.get("Directories", "input_dir", fallback=None):
        config = prompt_directories(config)
        save_config(config)

    if not config.has_section("Model") or not config.get("Model", "model", fallback=None):
        config = prompt_model(config)
        save_config(config)

    if not config.has_section("Language") or not config.get("Language", "language", fallback=None):
        config = prompt_language(config)
        save_config(config)

    if not config.has_section("Processing") or not config.get("Processing", "device", fallback=None):
        config = prompt_device(config)
        save_config(config)

    # CLI overrides
    if cli_model:
        if not config.has_section("Model"):
            config.add_section("Model")
        config.set("Model", "model", cli_model)

    if cli_device:
        if not config.has_section("Processing"):
            config.add_section("Processing")
        config.set("Processing", "device", cli_device)

    display_config(config)
    return config


def configure_settings(config: configparser.ConfigParser) -> configparser.ConfigParser:
    """
    Walk through every entry in audiotr.conf and let the user change values.

    Current values are shown as defaults; pressing Enter keeps them.
    If a value is blank, the user is prompted to provide one.
    """
    print("")
    print("=" * 55)
    print("  audiotr Configuration Editor")
    print("=" * 55)

    for section in config.sections():
        print(f"\n[{section}]")
        for key in config.options(section):
            current = config.get(section, key, fallback="")
            if current:
                raw = input(f"  {key} [{current}]: ").strip()
                if not raw:
                    raw = current
            else:
                raw = input(f"  {key}: ").strip()
            config.set(section, key, raw)

    print("")
    return config


def clear_cache():
    """Remove all __pycache__ directories under the project root."""
    removed = 0
    for dirpath, dirnames, _ in os.walk(str(BASE_DIR)):
        for d in dirnames:
            if d == "__pycache__":
                target = os.path.join(dirpath, d)
                shutil.rmtree(target)
                print(f"  Removed: {target}")
                removed += 1
    if removed:
        print(f"\nCleared {removed} __pycache__ director{'y' if removed == 1 else 'ies'}.")
    else:
        print("No __pycache__ directories found.")


def get_effective_device(config: configparser.ConfigParser) -> Optional[str]:
    """Get the device setting, returning None for 'auto' (let whisper decide)."""
    device = config.get("Processing", "device", fallback="auto")
    if device == "auto":
        return None
    return device


def get_effective_language(config: configparser.ConfigParser) -> Optional[str]:
    """Get the language setting, returning None for 'auto'."""
    lang = config.get("Language", "language", fallback="auto")
    if lang == "auto":
        return None
    return lang
