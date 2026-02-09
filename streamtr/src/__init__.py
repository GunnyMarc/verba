"""
Stream Transcriber - Capture and transcribe streaming audio to markdown.

Captures audio from streaming URLs via FFmpeg and transcribes using OpenAI Whisper.
"""

__version__ = "1.0.0"
__author__ = "Stream Transcriber Team"

from .capture import StreamCapture
from .transcriber import Transcriber
from .formatter import MarkdownFormatter
from .pipeline import TranscriptionPipeline

__all__ = [
    "StreamCapture",
    "Transcriber",
    "MarkdownFormatter",
    "TranscriptionPipeline",
]
