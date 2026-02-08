"""
Speech-to-text transcription module using OpenAI Whisper.

Converts audio to text with timestamp information.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class WhisperModel(Enum):
    """Available Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"


@dataclass
class TranscriptSegment:
    """A segment of transcribed text with timing information."""
    id: int
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str
    confidence: Optional[float] = None
    words: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Get the duration of this segment in seconds."""
        return self.end - self.start

    @property
    def start_formatted(self) -> str:
        """Get formatted start time (HH:MM:SS or MM:SS)."""
        return self._format_time(self.start)

    @property
    def end_formatted(self) -> str:
        """Get formatted end time (HH:MM:SS or MM:SS)."""
        return self._format_time(self.end)

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to timestamp string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    text: str  # Full transcribed text
    segments: List[TranscriptSegment]
    language: str
    language_probability: float
    duration: float  # Total duration in seconds
    model_used: str

    @property
    def word_count(self) -> int:
        """Get total word count."""
        return len(self.text.split())

    @property
    def segment_count(self) -> int:
        """Get number of segments."""
        return len(self.segments)


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""
    pass


class Transcriber:
    """
    Speech-to-text transcriber using OpenAI Whisper.

    Supports multiple model sizes for different speed/accuracy tradeoffs.
    """

    def __init__(
        self,
        model_name: str = "base",
        device: Optional[str] = None,
        compute_type: str = "float16"
    ):
        """
        Initialize the transcriber.

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large).
            device: Device to run on ("cuda", "cpu", or None for auto-detect).
            compute_type: Computation type ("float16", "float32", "int8").
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._loaded = False

    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        if self._loaded:
            return

        try:
            import whisper
            import torch

            # Determine device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            print(f"Loading Whisper model '{self.model_name}' on {self.device}...")
            self.model = whisper.load_model(self.model_name, device=self.device)
            self._loaded = True
            print(f"Model loaded successfully.")

        except ImportError:
            raise TranscriptionError(
                "OpenAI Whisper not installed. Install with: pip install openai-whisper"
            )
        except Exception as e:
            raise TranscriptionError(f"Failed to load Whisper model: {str(e)}")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        word_timestamps: bool = False,
        verbose: bool = False
    ) -> TranscriptionResult:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file.
            language: Language code (e.g., "en", "es"). None for auto-detection.
            task: "transcribe" or "translate" (translate to English).
            word_timestamps: Include word-level timestamps.
            verbose: Print progress information.

        Returns:
            TranscriptionResult with transcribed text and segments.

        Raises:
            TranscriptionError: If transcription fails.
        """
        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        # Load model if not already loaded
        self.load_model()

        try:
            # Run transcription
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                word_timestamps=word_timestamps,
                verbose=verbose
            )

            # Convert segments to TranscriptSegment objects
            segments = []
            for i, seg in enumerate(result.get("segments", [])):
                segment = TranscriptSegment(
                    id=i,
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                    words=seg.get("words", [])
                )
                segments.append(segment)

            # Calculate total duration
            duration = segments[-1].end if segments else 0.0

            # Get language info
            detected_language = result.get("language", "unknown")

            return TranscriptionResult(
                text=result["text"].strip(),
                segments=segments,
                language=detected_language,
                language_probability=1.0,  # Whisper doesn't expose this directly
                duration=duration,
                model_used=self.model_name
            )

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")

    def transcribe_with_progress(
        self,
        audio_path: str,
        callback=None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe with progress callback.

        Args:
            audio_path: Path to the audio file.
            callback: Optional callback function(progress: float, message: str).
            **kwargs: Additional arguments passed to transcribe().

        Returns:
            TranscriptionResult with transcribed text and segments.
        """
        if callback:
            callback(0.0, "Loading model...")

        self.load_model()

        if callback:
            callback(0.1, "Starting transcription...")

        result = self.transcribe(audio_path, **kwargs)

        if callback:
            callback(1.0, "Transcription complete!")

        return result

    def detect_language(self, audio_path: str) -> tuple:
        """
        Detect the language of an audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            Tuple of (language_code, probability).
        """
        self.load_model()

        try:
            import whisper

            # Load audio and pad/trim to 30 seconds
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)

            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)

            return detected_lang, probs[detected_lang]

        except Exception as e:
            raise TranscriptionError(f"Language detection failed: {str(e)}")

    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models."""
        return [m.value for m in WhisperModel]

    def unload_model(self) -> None:
        """Unload the model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            self._loaded = False

            # Try to free GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
