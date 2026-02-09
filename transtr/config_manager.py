"""Configuration manager: read/write transtr.conf, directory setup."""

import configparser
import os

CONF_DIR_NAME = "conf"
CONF_FILE_NAME = "transtr.conf"

AVAILABLE_MODELS = {
    "Ollama (Local)": [
        "llama3:latest",
        "llama3.2:latest",
        "mistral:latest",
        "mistral:7b",
        "mixtral:8x7b",
        "mixtral:8x22b",
        "qwen2.5:latest",
        "gemma2:latest",
        "gemma3:latest",
    ],
    "OpenAI (Commercial)": [
        "gpt-4o",
        "gpt-4o-mini",
    ],
    "Google (Commercial)": [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
    "Circuit (Cisco-only)": [
        "circuit-internal",
        "circuit-anthropic",
        "circuit-openai",
        "circuit-google",
    ],
}

# Display labels for the model selection menu
MODEL_DISPLAY_LABELS = {
    "llama3:latest": "Llama 3 (Local)",
    "llama3.2:latest": "Llama 3.2 (Local)",
    "mistral:latest": "Mistral (Local)",
    "mistral:7b": "Mistral 7B",
    "mixtral:8x7b": "Mixtral 8x7B",
    "mixtral:8x22b": "Mixtral 8x22B",
    "qwen2.5:latest": "Qwen 2.5",
    "gemma2:latest": "Gemma 2",
    "gemma3:latest": "Gemma 3",
    "gpt-4o": "OpenAI GPT-4o (Commercial/$$$)",
    "gpt-4o-mini": "OpenAI GPT-4o-mini (Commercial/$$$)",
    "gemini-1.5-flash": "Google Gemini 1.5 Flash (Commercial/$$$)",
    "gemini-1.5-pro": "Google Gemini 1.5 Pro (Commercial/$$$)",
    "circuit-internal": "Circuit-Internal Cisco Data (Cisco-only)",
    "circuit-anthropic": "Circuit-Anthropic (Cisco-only)",
    "circuit-openai": "Circuit-OpenAI (Cisco-only)",
    "circuit-google": "Circuit-Google (Cisco-only)",
}

OPENAI_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
}

GOOGLE_MODELS = {
    "gemini-1.5-flash",
    "gemini-1.5-pro",
}

CIRCUIT_MODELS = {
    "circuit-internal",
    "circuit-anthropic",
    "circuit-openai",
    "circuit-google",
}

COMMERCIAL_MODELS = OPENAI_MODELS | GOOGLE_MODELS | CIRCUIT_MODELS


def get_conf_paths(base_dir: str) -> tuple[str, str]:
    """Return (conf_dir, conf_file) paths relative to base_dir."""
    conf_dir = os.path.join(base_dir, CONF_DIR_NAME)
    conf_file = os.path.join(conf_dir, CONF_FILE_NAME)
    return conf_dir, conf_file


def ensure_conf(base_dir: str) -> tuple[str, configparser.ConfigParser, bool]:
    """Ensure conf dir and file exist. Returns (conf_file_path, config, is_new)."""
    conf_dir, conf_file = get_conf_paths(base_dir)

    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir, exist_ok=True)
        print(f"  Created config directory: {conf_dir}")

    config = configparser.ConfigParser()
    is_new = False

    if os.path.isfile(conf_file) and os.path.getsize(conf_file) > 0:
        config.read(conf_file)
        print(f"  Loaded config: {conf_file}")
    else:
        is_new = True
        if not os.path.isfile(conf_file):
            open(conf_file, "w").close()
            print(f"  Created config file: {conf_file}")
        else:
            print(f"  Config file is empty: {conf_file}")

    return conf_file, config, is_new


def save_config(conf_file: str, config: configparser.ConfigParser):
    """Write config to disk."""
    with open(conf_file, "w", encoding="utf-8") as f:
        config.write(f)


def is_openai_model(model: str) -> bool:
    """Return True if the model is an OpenAI model."""
    return model in OPENAI_MODELS


def is_google_model(model: str) -> bool:
    """Return True if the model is a Google Gemini model."""
    return model in GOOGLE_MODELS


def is_circuit_model(model: str) -> bool:
    """Return True if the model is a Circuit (Cisco) model."""
    return model in CIRCUIT_MODELS


def is_cloud_model(model: str) -> bool:
    """Return True if the model is a commercial/cloud model."""
    return model in COMMERCIAL_MODELS


def get_openai_api_key() -> str:
    """Retrieve the OpenAI API key from the environment, prompting if not set."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        print("  OPENAI_API_KEY detected in environment [OK]")
        return key

    print("\n  OPENAI_API_KEY environment variable is not set.")
    print("  You can set it permanently by adding the following to your shell profile:")
    print('    export OPENAI_API_KEY="your-key-here"')
    key = input("\n  Enter your OpenAI API key: ").strip()
    if not key:
        print("  ERROR: API key cannot be empty.")
        import sys
        sys.exit(1)

    os.environ["OPENAI_API_KEY"] = key
    print("  API key set for this session.")
    return key


def get_google_api_key() -> str:
    """Retrieve the Google API key from the environment, prompting if not set."""
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if key:
        print("  GOOGLE_API_KEY detected in environment [OK]")
        return key

    print("\n  GOOGLE_API_KEY environment variable is not set.")
    print("  You can set it permanently by adding the following to your shell profile:")
    print('    export GOOGLE_API_KEY="your-key-here"')
    key = input("\n  Enter your Google API key: ").strip()
    if not key:
        print("  ERROR: API key cannot be empty.")
        import sys
        sys.exit(1)

    os.environ["GOOGLE_API_KEY"] = key
    print("  API key set for this session.")
    return key


def prompt_model_selection() -> str:
    """Prompt user to select a model."""
    print("\nSelect a model:")
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        label = MODEL_DISPLAY_LABELS.get(model, model)
        if model in OPENAI_MODELS:
            env_note = "  [requires OPENAI_API_KEY]"
        elif model in GOOGLE_MODELS:
            env_note = "  [requires GOOGLE_API_KEY]"
        else:
            env_note = ""
        print(f"  {i:>2}. {label}{env_note}")
    num_models = len(AVAILABLE_MODELS)
    valid_choices = {str(i) for i in range(1, num_models + 1)}
    while True:
        choice = input(f"Enter selection (1-{num_models}): ").strip()
        if choice in valid_choices:
            selected = AVAILABLE_MODELS[int(choice) - 1]
            print(f"  Selected: {selected}")
            return selected
        print(f"  Invalid selection. Please enter 1-{num_models}.")


def prompt_directory(label: str) -> str:
    """Prompt user for a directory path, create if it doesn't exist."""
    while True:
        path = input(f"Enter path for {label}: ").strip()
        if not path:
            print("  Path cannot be empty.")
            continue
        expanded = os.path.expanduser(path)
        if not os.path.isdir(expanded):
            os.makedirs(expanded, exist_ok=True)
            print(f"  Created directory: {expanded}")
        return expanded


def ensure_directory_config(config: configparser.ConfigParser, conf_file: str, key: str, label: str) -> str:
    """Check config for a directory entry; prompt if missing. Returns the path."""
    if not config.has_section("directories"):
        config.add_section("directories")

    path = config.get("directories", key, fallback="").strip()
    if path and os.path.isdir(path):
        return path

    if path and not os.path.isdir(path):
        print(f"  Directory for {label} not found at: {path}")

    path = prompt_directory(label)
    config.set("directories", key, path)
    save_config(conf_file, config)
    return path


def ensure_instructions_file(config: configparser.ConfigParser, conf_file: str, instructions_dir: str) -> str:
    """Check config for instructions_file entry; prompt if missing. Returns the full path."""
    if not config.has_section("instructions"):
        config.add_section("instructions")

    filename = config.get("instructions", "instructions_file", fallback="").strip()

    if filename:
        full_path = os.path.join(instructions_dir, filename)
        if os.path.isfile(full_path) and os.access(full_path, os.R_OK):
            return full_path
        print(f"  Instructions file not found or not readable: {full_path}")

    while True:
        filename = input("Enter instructions filename: ").strip()
        if not filename:
            print("  Filename cannot be empty.")
            continue
        full_path = os.path.join(instructions_dir, filename)
        if os.path.isfile(full_path) and os.access(full_path, os.R_OK):
            config.set("instructions", "instructions_file", filename)
            save_config(conf_file, config)
            return full_path
        print(f"  File not found or not readable: {full_path}")
        print("Provide the processing instructions file and restart application")
        return ""


def display_config(config: configparser.ConfigParser):
    """Display current configuration to user."""
    print("\n--- Current Configuration ---")
    model = config.get("model", "name", fallback="(not set)")
    print(f"  Model            : {model}")
    print(f"  OS               : {config.get('system', 'os', fallback='(not set)')}")
    print(f"  Python           : {config.get('system', 'python_version', fallback='(not set)')}")
    print(f"  input_dir        : {config.get('directories', 'input_dir', fallback='(not set)')}")
    print(f"  stage_dir        : {config.get('directories', 'stage_dir', fallback='(not set)')}")
    print(f"  output_dir       : {config.get('directories', 'output_dir', fallback='(not set)')}")
    print(f"  instructions_dir : {config.get('directories', 'instructions_dir', fallback='(not set)')}")
    print(f"  instructions_file: {config.get('instructions', 'instructions_file', fallback='(not set)')}")
    print(f"  log_dir          : {config.get('directories', 'log_dir', fallback='(not set)')}")
    print("-----------------------------\n")


def reconfigure(conf_file: str, config: configparser.ConfigParser):
    """Walk through all config settings, letting the user keep or change each one."""
    print("\n--- Reconfigure Transtr ---")
    print("  Press Enter to keep current value, or type a new value.\n")

    # Model
    if not config.has_section("model"):
        config.add_section("model")
    current_model = config.get("model", "name", fallback="")
    print("  Available models:")
    for i, m in enumerate(AVAILABLE_MODELS, 1):
        label = MODEL_DISPLAY_LABELS.get(m, m)
        print(f"    {i:>2}. {label}")
    choice = input(f"  Model [{current_model}]: ").strip()
    if choice:
        if choice.isdigit() and 1 <= int(choice) <= len(AVAILABLE_MODELS):
            config.set("model", "name", AVAILABLE_MODELS[int(choice) - 1])
        else:
            print(f"  Invalid selection, keeping: {current_model}")

    # Directories
    if not config.has_section("directories"):
        config.add_section("directories")
    for key in ("input_dir", "stage_dir", "output_dir", "instructions_dir", "log_dir"):
        current = config.get("directories", key, fallback="")
        new_val = input(f"  {key} [{current}]: ").strip()
        if new_val:
            expanded = os.path.expanduser(new_val)
            if not os.path.isdir(expanded):
                os.makedirs(expanded, exist_ok=True)
                print(f"    Created directory: {expanded}")
            config.set("directories", key, expanded)

    # Instructions file
    if not config.has_section("instructions"):
        config.add_section("instructions")
    current_file = config.get("instructions", "instructions_file", fallback="")
    new_val = input(f"  instructions_file [{current_file}]: ").strip()
    if new_val:
        config.set("instructions", "instructions_file", new_val)

    save_config(conf_file, config)
    print("\n  Configuration saved.\n")
