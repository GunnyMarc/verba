"""
Transcription pipeline that orchestrates the full audio-to-markdown workflow.

Combines audio processing, transcription, and markdown formatting.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

from .processor import AudioProcessor, AudioProcessingError
from .transcriber import Transcriber, TranscriptionResult, TranscriptionError
from .formatter import MarkdownFormatter


@dataclass
class PipelineResult:
    """Result of a transcription pipeline run."""
    success: bool
    audio_path: str
    output_path: Optional[str]
    transcription: Optional[TranscriptionResult]
    audio_info: Optional[dict]
    error: Optional[str] = None

    @property
    def markdown_content(self) -> Optional[str]:
        """Read the markdown content if available."""
        if self.output_path and os.path.exists(self.output_path):
            with open(self.output_path, "r", encoding="utf-8") as f:
                return f.read()
        return None


class TranscriptionPipeline:
    """
    Complete audio transcription pipeline.

    Handles the full workflow from audio file to markdown output.
    """

    def __init__(
        self,
        model: str = "base",
        style: str = "timestamped",
        language: Optional[str] = None,
        device: Optional[str] = None,
        keep_converted: bool = False,
        include_metadata: bool = True
    ):
        """
        Initialize the transcription pipeline.

        Args:
            model: Whisper model to use (tiny, base, small, medium, large).
            style: Markdown style (simple, timestamped, detailed, srt_style).
            language: Language code or None for auto-detection.
            device: Device to use (cuda, cpu, or None for auto).
            keep_converted: Keep converted audio files (only relevant when
                           format conversion occurs).
            include_metadata: Include metadata in markdown output.
        """
        self.model = model
        self.style = style
        self.language = language
        self.device = device
        self.keep_converted = keep_converted
        self.include_metadata = include_metadata

        # Initialize components lazily
        self._processor = None
        self._transcriber = None
        self._formatter = None

    @property
    def processor(self) -> AudioProcessor:
        """Get or create the audio processor."""
        if self._processor is None:
            self._processor = AudioProcessor()
        return self._processor

    @property
    def transcriber(self) -> Transcriber:
        """Get or create the transcriber."""
        if self._transcriber is None:
            self._transcriber = Transcriber(
                model_name=self.model,
                device=self.device
            )
        return self._transcriber

    @property
    def formatter(self) -> MarkdownFormatter:
        """Get or create the markdown formatter."""
        if self._formatter is None:
            self._formatter = MarkdownFormatter(
                style=self.style,
                include_metadata=self.include_metadata
            )
        return self._formatter

    def process(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> PipelineResult:
        """
        Process an audio file and generate markdown transcript.

        Args:
            audio_path: Path to the audio file.
            output_path: Optional output path for markdown file.
            progress_callback: Optional callback for progress updates.

        Returns:
            PipelineResult with transcription details.
        """
        audio_path = os.path.abspath(audio_path)
        converted_path = None

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
            print(f"[{progress*100:.0f}%] {message}")

        try:
            # Validate audio file
            update_progress(0.0, "Validating audio file...")

            if not os.path.exists(audio_path):
                return PipelineResult(
                    success=False,
                    audio_path=audio_path,
                    output_path=None,
                    transcription=None,
                    audio_info=None,
                    error=f"Audio file not found: {audio_path}"
                )

            if not self.processor.is_supported_format(audio_path):
                ext = Path(audio_path).suffix
                return PipelineResult(
                    success=False,
                    audio_path=audio_path,
                    output_path=None,
                    transcription=None,
                    audio_info=None,
                    error=f"Unsupported format: {ext}"
                )

            # Get audio info (non-fatal — metadata is optional)
            update_progress(0.05, "Getting audio information...")
            try:
                audio_info = self.processor.get_audio_info(audio_path)
            except AudioProcessingError:
                audio_info = {}

            # Prepare audio for transcription
            update_progress(0.1, "Preparing audio for transcription...")
            whisper_path, was_converted = self.processor.prepare_audio(audio_path)
            converted_path = whisper_path if was_converted else None
            update_progress(0.2, "Audio preparation complete.")

            # Transcribe
            update_progress(0.25, f"Loading Whisper model ({self.model})...")
            self.transcriber.load_model()

            update_progress(0.3, "Transcribing audio...")
            transcription = self.transcriber.transcribe(
                whisper_path,
                language=self.language,
                verbose=False
            )
            update_progress(0.8, "Transcription complete.")

            # Format as markdown
            update_progress(0.85, "Formatting markdown...")
            markdown_content = self.formatter.format(
                transcription,
                audio_path=audio_path,
                audio_info=audio_info
            )

            # Generate output path if not provided
            if output_path is None:
                output_path = self.formatter.generate_output_path(audio_path)

            # Save markdown
            update_progress(0.9, "Saving markdown file...")
            output_path = self.formatter.save(markdown_content, output_path)

            update_progress(1.0, f"Done! Saved to: {output_path}")

            return PipelineResult(
                success=True,
                audio_path=audio_path,
                output_path=output_path,
                transcription=transcription,
                audio_info=audio_info
            )

        except (AudioProcessingError, TranscriptionError) as e:
            return PipelineResult(
                success=False,
                audio_path=audio_path,
                output_path=None,
                transcription=None,
                audio_info=None,
                error=str(e)
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                audio_path=audio_path,
                output_path=None,
                transcription=None,
                audio_info=None,
                error=f"Unexpected error: {str(e)}"
            )

        finally:
            # Cleanup converted file only if conversion was performed
            if converted_path and not self.keep_converted:
                if os.path.exists(converted_path):
                    try:
                        os.remove(converted_path)
                    except OSError:
                        pass

    def process_batch(
        self,
        audio_paths: List[str],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[PipelineResult]:
        """
        Process multiple audio files.

        Args:
            audio_paths: List of audio file paths.
            output_dir: Optional output directory for all transcripts.
            progress_callback: Optional callback(current, total, message).

        Returns:
            List of PipelineResult for each audio file.
        """
        results = []
        total = len(audio_paths)

        for i, audio_path in enumerate(audio_paths):
            if progress_callback:
                progress_callback(i, total, f"Processing: {Path(audio_path).name}")

            # Generate output path
            if output_dir:
                output_path = self.formatter.generate_output_path(
                    audio_path,
                    output_dir=output_dir
                )
            else:
                output_path = None

            result = self.process(audio_path, output_path)
            results.append(result)

        if progress_callback:
            progress_callback(total, total, "Batch processing complete!")

        return results

    def cleanup(self):
        """Cleanup resources."""
        if self._transcriber:
            self._transcriber.unload_model()
