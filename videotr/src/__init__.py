"""
Video Transcriber - Transcribe video files to markdown.

Supports .mov, .mpeg, and .mkv video formats.
Uses OpenAI Whisper for speech-to-text transcription.
"""

__version__ = "1.0.0"
__author__ = "Video Transcriber Team"

from .extractor import AudioExtractor
from .transcriber import Transcriber
from .formatter import MarkdownFormatter
from .pipeline import TranscriptionPipeline

__all__ = [
    "AudioExtractor",
    "Transcriber",
    "MarkdownFormatter",
    "TranscriptionPipeline",
]
