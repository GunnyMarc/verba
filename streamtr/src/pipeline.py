"""
Transcription pipeline that orchestrates the full stream-to-markdown workflow.

Combines stream capture, transcription, and markdown formatting.
"""

import os
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass
from urllib.parse import urlparse

from .capture import StreamCapture, StreamCaptureError
from .transcriber import Transcriber, TranscriptionResult, TranscriptionError
from .formatter import MarkdownFormatter


@dataclass
class PipelineResult:
    """Result of a transcription pipeline run."""
    success: bool
    stream_url: str
    output_path: Optional[str]
    transcription: Optional[TranscriptionResult]
    stream_info: Optional[dict]
    capture_info: Optional[dict]
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
    Complete stream transcription pipeline.

    Handles the full workflow from stream URL to markdown output.
    """

    def __init__(
        self,
        model: str = "base",
        style: str = "timestamped",
        language: Optional[str] = None,
        device: Optional[str] = None,
        duration: Optional[float] = None,
        keep_captured: bool = False,
        include_metadata: bool = True
    ):
        """
        Initialize the transcription pipeline.

        Args:
            model: Whisper model to use (tiny, base, small, medium, large).
            style: Markdown style (simple, timestamped, detailed, srt_style).
            language: Language code or None for auto-detection.
            device: Device to use (cuda, cpu, or None for auto).
            duration: Optional capture duration in seconds.
            keep_captured: Keep captured WAV files after transcription.
            include_metadata: Include metadata in markdown output.
        """
        self.model = model
        self.style = style
        self.language = language
        self.device = device
        self.duration = duration
        self.keep_captured = keep_captured
        self.include_metadata = include_metadata

        # Initialize components lazily
        self._capture = None
        self._transcriber = None
        self._formatter = None

    @property
    def capture(self) -> StreamCapture:
        """Get or create the stream capture module."""
        if self._capture is None:
            self._capture = StreamCapture()
        return self._capture

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
        url: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> PipelineResult:
        """
        Process a stream URL and generate markdown transcript.

        Args:
            url: The stream URL to capture and transcribe.
            output_path: Optional output path for markdown file.
            progress_callback: Optional callback for progress updates.

        Returns:
            PipelineResult with transcription details.
        """
        captured_path = None

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
            print(f"[{progress*100:.0f}%] {message}")

        try:
            # Validate URL
            update_progress(0.0, "Validating stream URL...")
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return PipelineResult(
                    success=False,
                    stream_url=url,
                    output_path=None,
                    transcription=None,
                    stream_info=None,
                    capture_info=None,
                    error=f"Invalid URL: {url}. Must include scheme (http/https/rtmp/etc)."
                )

            # Probe stream info (non-fatal)
            update_progress(0.05, "Probing stream info...")
            try:
                stream_info = self.capture.get_stream_info(url)
            except StreamCaptureError:
                stream_info = {}

            # Capture audio via FFmpeg
            update_progress(0.1, "Capturing audio from stream...")
            captured_path, capture_info = self.capture.capture_audio(
                url, duration=self.duration
            )
            update_progress(0.5, "Capture complete.")

            # Transcribe
            update_progress(0.55, f"Loading Whisper model ({self.model})...")
            self.transcriber.load_model()

            update_progress(0.6, "Transcribing audio...")
            transcription = self.transcriber.transcribe(
                captured_path,
                language=self.language,
                verbose=False
            )
            update_progress(0.9, "Transcription complete.")

            # Format as markdown
            update_progress(0.9, "Formatting markdown...")
            markdown_content = self.formatter.format(
                transcription,
                source_url=url,
                stream_info=stream_info,
                capture_info=capture_info
            )

            # Generate output path if not provided
            if output_path is None:
                output_path = self.formatter.generate_output_path(url)

            # Save markdown
            update_progress(0.95, "Saving markdown file...")
            output_path = self.formatter.save(markdown_content, output_path)

            update_progress(1.0, f"Done! Saved to: {output_path}")

            return PipelineResult(
                success=True,
                stream_url=url,
                output_path=output_path,
                transcription=transcription,
                stream_info=stream_info,
                capture_info=capture_info
            )

        except (StreamCaptureError, TranscriptionError) as e:
            return PipelineResult(
                success=False,
                stream_url=url,
                output_path=None,
                transcription=None,
                stream_info=None,
                capture_info=None,
                error=str(e)
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                stream_url=url,
                output_path=None,
                transcription=None,
                stream_info=None,
                capture_info=None,
                error=f"Unexpected error: {str(e)}"
            )

        finally:
            # Cleanup captured WAV unless keep_captured
            if captured_path and not self.keep_captured:
                if os.path.exists(captured_path):
                    try:
                        os.remove(captured_path)
                    except OSError:
                        pass

    def process_batch(
        self,
        urls: List[str],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[PipelineResult]:
        """
        Process multiple stream URLs.

        Args:
            urls: List of stream URLs.
            output_dir: Optional output directory for all transcripts.
            progress_callback: Optional callback(current, total, message).

        Returns:
            List of PipelineResult for each URL.
        """
        results = []
        total = len(urls)

        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i, total, f"Processing: {url}")

            # Generate output path
            if output_dir:
                output_path = self.formatter.generate_output_path(
                    url,
                    output_dir=output_dir
                )
            else:
                output_path = None

            result = self.process(url, output_path)
            results.append(result)

        if progress_callback:
            progress_callback(total, total, "Batch processing complete!")

        return results

    def cleanup(self):
        """Cleanup resources."""
        if self._transcriber:
            self._transcriber.unload_model()
