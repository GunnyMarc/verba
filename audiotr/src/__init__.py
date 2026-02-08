"""
Audio Transcriber - Transcribe audio files to markdown.

Supports .mp3, .wav, .aac, .flac, .m4a, .ogg, .wma, .opus, .aiff, and .alac audio formats.
Uses OpenAI Whisper for speech-to-text transcription.
"""

__version__ = "1.0.0"
__author__ = "Audio Transcriber Team"

from .processor import AudioProcessor
from .transcriber import Transcriber
from .formatter import MarkdownFormatter
from .pipeline import TranscriptionPipeline

__all__ = [
    "AudioProcessor",
    "Transcriber",
    "MarkdownFormatter",
    "TranscriptionPipeline",
]
