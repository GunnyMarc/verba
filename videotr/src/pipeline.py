"""
Transcription pipeline that orchestrates the full video-to-markdown workflow.

Combines audio extraction, transcription, and markdown formatting.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass

from .extractor import AudioExtractor, AudioExtractionError
from .transcriber import Transcriber, TranscriptionResult, TranscriptionError
from .formatter import MarkdownFormatter


@dataclass
class PipelineResult:
    """Result of a transcription pipeline run."""
    success: bool
    video_path: str
    output_path: Optional[str]
    transcription: Optional[TranscriptionResult]
    video_info: Optional[dict]
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
    Complete video transcription pipeline.

    Handles the full workflow from video file to markdown output.
    """

    def __init__(
        self,
        model: str = "base",
        style: str = "timestamped",
        language: Optional[str] = None,
        device: Optional[str] = None,
        keep_audio: bool = False,
        include_metadata: bool = True
    ):
        """
        Initialize the transcription pipeline.

        Args:
            model: Whisper model to use (tiny, base, small, medium, large).
            style: Markdown style (simple, timestamped, detailed, srt_style).
            language: Language code or None for auto-detection.
            device: Device to use (cuda, cpu, or None for auto).
            keep_audio: Keep extracted audio files.
            include_metadata: Include metadata in markdown output.
        """
        self.model = model
        self.style = style
        self.language = language
        self.device = device
        self.keep_audio = keep_audio
        self.include_metadata = include_metadata

        # Initialize components lazily
        self._extractor = None
        self._transcriber = None
        self._formatter = None

    @property
    def extractor(self) -> AudioExtractor:
        """Get or create the audio extractor."""
        if self._extractor is None:
            self._extractor = AudioExtractor()
        return self._extractor

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
        video_path: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> PipelineResult:
        """
        Process a video file and generate markdown transcript.

        Args:
            video_path: Path to the video file.
            output_path: Optional output path for markdown file.
            progress_callback: Optional callback for progress updates.

        Returns:
            PipelineResult with transcription details.
        """
        video_path = os.path.abspath(video_path)
        audio_path = None

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
            print(f"[{progress*100:.0f}%] {message}")

        try:
            # Validate video file
            update_progress(0.0, "Validating video file...")

            if not os.path.exists(video_path):
                return PipelineResult(
                    success=False,
                    video_path=video_path,
                    output_path=None,
                    transcription=None,
                    video_info=None,
                    error=f"Video file not found: {video_path}"
                )

            if not self.extractor.is_supported_format(video_path):
                ext = Path(video_path).suffix
                return PipelineResult(
                    success=False,
                    video_path=video_path,
                    output_path=None,
                    transcription=None,
                    video_info=None,
                    error=f"Unsupported format: {ext}"
                )

            # Get video info
            update_progress(0.05, "Getting video information...")
            video_info = self.extractor.get_video_info(video_path)

            if not video_info.get("has_audio"):
                return PipelineResult(
                    success=False,
                    video_path=video_path,
                    output_path=None,
                    transcription=None,
                    video_info=video_info,
                    error="Video has no audio track"
                )

            # Extract audio
            update_progress(0.1, "Extracting audio from video...")
            audio_path = self.extractor.extract_audio(video_path)
            update_progress(0.2, "Audio extraction complete.")

            # Transcribe
            update_progress(0.25, f"Loading Whisper model ({self.model})...")
            self.transcriber.load_model()

            update_progress(0.3, "Transcribing audio...")
            transcription = self.transcriber.transcribe(
                audio_path,
                language=self.language,
                verbose=False
            )
            update_progress(0.8, "Transcription complete.")

            # Format as markdown
            update_progress(0.85, "Formatting markdown...")
            markdown_content = self.formatter.format(
                transcription,
                video_path=video_path,
                video_info=video_info
            )

            # Generate output path if not provided
            if output_path is None:
                output_path = self.formatter.generate_output_path(video_path)

            # Save markdown
            update_progress(0.9, "Saving markdown file...")
            output_path = self.formatter.save(markdown_content, output_path)

            update_progress(1.0, f"Done! Saved to: {output_path}")

            return PipelineResult(
                success=True,
                video_path=video_path,
                output_path=output_path,
                transcription=transcription,
                video_info=video_info
            )

        except (AudioExtractionError, TranscriptionError) as e:
            return PipelineResult(
                success=False,
                video_path=video_path,
                output_path=None,
                transcription=None,
                video_info=None,
                error=str(e)
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                video_path=video_path,
                output_path=None,
                transcription=None,
                video_info=None,
                error=f"Unexpected error: {str(e)}"
            )

        finally:
            # Cleanup audio file
            if audio_path and not self.keep_audio:
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        pass

    def process_batch(
        self,
        video_paths: List[str],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[PipelineResult]:
        """
        Process multiple video files.

        Args:
            video_paths: List of video file paths.
            output_dir: Optional output directory for all transcripts.
            progress_callback: Optional callback(current, total, message).

        Returns:
            List of PipelineResult for each video.
        """
        results = []
        total = len(video_paths)

        for i, video_path in enumerate(video_paths):
            if progress_callback:
                progress_callback(i, total, f"Processing: {Path(video_path).name}")

            # Generate output path
            if output_dir:
                output_path = self.formatter.generate_output_path(
                    video_path,
                    output_dir=output_dir
                )
            else:
                output_path = None

            result = self.process(video_path, output_path)
            results.append(result)

        if progress_callback:
            progress_callback(total, total, "Batch processing complete!")

        return results

    def cleanup(self):
        """Cleanup resources."""
        if self._transcriber:
            self._transcriber.unload_model()
