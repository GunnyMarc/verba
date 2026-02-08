import sys
from pathlib import Path

# Add repo root to sys.path so sibling packages can be imported
REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Add transtr/ to sys.path for bare imports within that package
TRANSTR_DIR = REPO_ROOT / "transtr"
if str(TRANSTR_DIR) not in sys.path:
    sys.path.insert(0, str(TRANSTR_DIR))

# Supported file formats
VIDEO_FORMATS = {".mov", ".mp4", ".mkv", ".mpeg", ".avi", ".webm"}
AUDIO_FORMATS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".opus", ".aiff", ".alac"}
TRANSCRIPT_FORMATS = {".txt", ".md", ".csv", ".rtf", ".tsv"}

# Whisper configuration
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEVICE_CHOICES = ["auto", "cpu", "cuda", "mps"]
MARKDOWN_STYLES = ["simple", "timestamped", "detailed", "srt_style"]

# Try to import model definitions from transtr
try:
    from transtr.config_manager import (
        AVAILABLE_MODELS,
        MODEL_DISPLAY_LABELS,
        is_openai_model,
        is_google_model,
    )
except ImportError:
    AVAILABLE_MODELS = {"ollama": ["llama3:latest"]}
    MODEL_DISPLAY_LABELS = {"llama3:latest": "Llama 3 (Local)"}
    def is_openai_model(model: str) -> bool:
        return model.startswith("gpt-")
    def is_google_model(model: str) -> bool:
        return model.startswith("gemini")

# API key vendor mapping to environment variable names
VENDOR_ENV_MAP = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    "circuit": "CIRCUIT_API_KEY",
    "abacus": "ABACUS_CHATLLM_API_KEY",
}

VENDOR_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "google": "Google",
    "anthropic": "Anthropic",
    "ollama": "Ollama",
    "circuit": "Circuit",
    "abacus": "Abacus ChatLLM",
}


class WebSettings:
    """Mutable runtime settings stored in app.state.settings."""

    def __init__(self):
        self.whisper_model: str = "base"
        self.device: str = "auto"
        self.language: str = "auto"
        self.markdown_style: str = "timestamped"
        self.include_metadata: bool = True
        self.ollama_base_url: str = "http://localhost:11434"
        # File location settings
        self.video_input_dir: str = str(REPO_ROOT / "videotr" / "input")
        self.video_output_dir: str = str(WEB_DIR / "output")
        self.audio_input_dir: str = str(REPO_ROOT / "audiotr" / "input")
        self.audio_output_dir: str = str(WEB_DIR / "output")
        self.summary_input_dir: str = str(REPO_ROOT / "transtr" / "input")
        self.summary_output_dir: str = str(WEB_DIR / "output")

    def to_dict(self) -> dict:
        return {
            "whisper_model": self.whisper_model,
            "device": self.device,
            "language": self.language,
            "markdown_style": self.markdown_style,
            "include_metadata": self.include_metadata,
            "ollama_base_url": self.ollama_base_url,
            "video_input_dir": self.video_input_dir,
            "video_output_dir": self.video_output_dir,
            "audio_input_dir": self.audio_input_dir,
            "audio_output_dir": self.audio_output_dir,
            "summary_input_dir": self.summary_input_dir,
            "summary_output_dir": self.summary_output_dir,
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
