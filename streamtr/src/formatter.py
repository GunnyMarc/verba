"""
Markdown formatter for stream transcription output.

Converts transcription results to various markdown formats.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from enum import Enum

from .transcriber import TranscriptionResult, TranscriptSegment
from .capture import sanitize_url_to_filename


class MarkdownStyle(Enum):
    """Available markdown formatting styles."""
    SIMPLE = "simple"           # Just the text
    TIMESTAMPED = "timestamped"  # Text with timestamps
    DETAILED = "detailed"        # Full details with metadata
    SRT_STYLE = "srt_style"     # SRT subtitle format in markdown


class MarkdownFormatter:
    """Format transcription results as markdown."""

    def __init__(
        self,
        style: str = "timestamped",
        include_metadata: bool = True,
        include_toc: bool = False,
        timestamp_format: str = "inline"  # "inline" or "header"
    ):
        """
        Initialize the markdown formatter.

        Args:
            style: Formatting style (simple, timestamped, detailed, srt_style).
            include_metadata: Include stream/transcription metadata.
            include_toc: Include table of contents.
            timestamp_format: How to display timestamps.
        """
        self.style = MarkdownStyle(style)
        self.include_metadata = include_metadata
        self.include_toc = include_toc
        self.timestamp_format = timestamp_format

    def format(
        self,
        result: TranscriptionResult,
        source_url: Optional[str] = None,
        stream_info: Optional[dict] = None,
        capture_info: Optional[dict] = None
    ) -> str:
        """
        Format transcription result as markdown.

        Args:
            result: The transcription result to format.
            source_url: Optional source stream URL.
            stream_info: Optional stream metadata dictionary.
            capture_info: Optional capture process metadata.

        Returns:
            Formatted markdown string.
        """
        if self.style == MarkdownStyle.SIMPLE:
            return self._format_simple(result, source_url, stream_info, capture_info)
        elif self.style == MarkdownStyle.TIMESTAMPED:
            return self._format_timestamped(result, source_url, stream_info, capture_info)
        elif self.style == MarkdownStyle.DETAILED:
            return self._format_detailed(result, source_url, stream_info, capture_info)
        elif self.style == MarkdownStyle.SRT_STYLE:
            return self._format_srt_style(result, source_url, stream_info, capture_info)
        else:
            return self._format_timestamped(result, source_url, stream_info, capture_info)

    def _format_header(
        self,
        source_url: Optional[str],
        stream_info: Optional[dict],
        capture_info: Optional[dict],
        result: TranscriptionResult
    ) -> str:
        """Generate markdown header with metadata."""
        lines = []

        # Title
        if source_url:
            name = sanitize_url_to_filename(source_url)
            lines.append(f"# Transcript: {name}")
        else:
            lines.append("# Stream Transcript")

        lines.append("")

        if self.include_metadata:
            lines.append("## Metadata")
            lines.append("")

            if source_url:
                lines.append(f"- **Source URL:** `{source_url}`")

            if stream_info:
                if stream_info.get("duration_formatted"):
                    lines.append(f"- **Stream Duration:** {stream_info['duration_formatted']}")
                if stream_info.get("format"):
                    lines.append(f"- **Format:** {stream_info['format']}")
                if stream_info.get("sample_rate"):
                    lines.append(f"- **Sample Rate:** {stream_info['sample_rate']} Hz")
                if stream_info.get("channels"):
                    ch = stream_info["channels"]
                    ch_label = "Mono" if ch == 1 else "Stereo" if ch == 2 else str(ch)
                    lines.append(f"- **Channels:** {ch_label}")

            if capture_info:
                elapsed = capture_info.get("elapsed")
                if elapsed is not None:
                    lines.append(f"- **Duration Captured:** {self._format_duration(elapsed)}")
                if capture_info.get("interrupted"):
                    lines.append(f"- **Capture Interrupted:** Yes")
                file_size_mb = capture_info.get("file_size_mb")
                if file_size_mb is not None:
                    lines.append(f"- **Capture Size:** {file_size_mb} MB")

            lines.append(f"- **Language:** {result.language}")
            lines.append(f"- **Model Used:** Whisper {result.model_used}")
            lines.append(f"- **Word Count:** {result.word_count:,}")
            lines.append(f"- **Segments:** {result.segment_count}")
            lines.append(f"- **Transcribed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

        return "\n".join(lines)

    def _format_simple(
        self,
        result: TranscriptionResult,
        source_url: Optional[str],
        stream_info: Optional[dict],
        capture_info: Optional[dict]
    ) -> str:
        """Format as simple text without timestamps."""
        lines = []

        if self.include_metadata:
            lines.append(self._format_header(source_url, stream_info, capture_info, result))

        lines.append("## Transcript")
        lines.append("")
        lines.append(result.text)
        lines.append("")

        return "\n".join(lines)

    def _format_timestamped(
        self,
        result: TranscriptionResult,
        source_url: Optional[str],
        stream_info: Optional[dict],
        capture_info: Optional[dict]
    ) -> str:
        """Format with inline timestamps."""
        lines = []

        if self.include_metadata:
            lines.append(self._format_header(source_url, stream_info, capture_info, result))

        lines.append("## Transcript")
        lines.append("")

        if self.include_toc:
            lines.append(self._generate_toc(result.segments))
            lines.append("")

        for segment in result.segments:
            if self.timestamp_format == "inline":
                lines.append(
                    f"**[{segment.start_formatted}]** {segment.text}"
                )
            else:
                lines.append(f"### {segment.start_formatted}")
                lines.append("")
                lines.append(segment.text)
                lines.append("")

        lines.append("")
        return "\n".join(lines)

    def _format_detailed(
        self,
        result: TranscriptionResult,
        source_url: Optional[str],
        stream_info: Optional[dict],
        capture_info: Optional[dict]
    ) -> str:
        """Format with full details including segment durations."""
        lines = []

        lines.append(self._format_header(source_url, stream_info, capture_info, result))

        if self.include_toc:
            lines.append("## Table of Contents")
            lines.append("")
            lines.append(self._generate_toc(result.segments))
            lines.append("")

        lines.append("## Transcript")
        lines.append("")

        for segment in result.segments:
            # Create anchor for TOC
            anchor = f"segment-{segment.id}"

            lines.append(f"### <a name=\"{anchor}\"></a>Segment {segment.id + 1}")
            lines.append("")
            lines.append(f"| Property | Value |")
            lines.append(f"|----------|-------|")
            lines.append(f"| Start | {segment.start_formatted} |")
            lines.append(f"| End | {segment.end_formatted} |")
            lines.append(f"| Duration | {segment.duration:.2f}s |")
            lines.append("")
            lines.append(f"> {segment.text}")
            lines.append("")

        # Summary statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Duration | {self._format_duration(result.duration)} |")
        lines.append(f"| Total Words | {result.word_count:,} |")
        lines.append(f"| Total Segments | {result.segment_count} |")
        avg_words = result.word_count / result.segment_count if result.segment_count > 0 else 0
        lines.append(f"| Avg Words/Segment | {avg_words:.1f} |")
        wpm = (result.word_count / result.duration * 60) if result.duration > 0 else 0
        lines.append(f"| Words per Minute | {wpm:.0f} |")
        lines.append("")

        return "\n".join(lines)

    def _format_srt_style(
        self,
        result: TranscriptionResult,
        source_url: Optional[str],
        stream_info: Optional[dict],
        capture_info: Optional[dict]
    ) -> str:
        """Format in SRT subtitle style within markdown."""
        lines = []

        if self.include_metadata:
            lines.append(self._format_header(source_url, stream_info, capture_info, result))

        lines.append("## Transcript (Subtitle Format)")
        lines.append("")
        lines.append("```srt")

        for segment in result.segments:
            lines.append(str(segment.id + 1))
            lines.append(
                f"{self._format_srt_time(segment.start)} --> "
                f"{self._format_srt_time(segment.end)}"
            )
            lines.append(segment.text)
            lines.append("")

        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    def _generate_toc(self, segments: List[TranscriptSegment]) -> str:
        """Generate table of contents from segments."""
        lines = []
        lines.append("| Time | Preview |")
        lines.append("|------|---------|")

        for segment in segments[:20]:  # Limit to first 20 for TOC
            preview = segment.text[:50] + "..." if len(segment.text) > 50 else segment.text
            anchor = f"segment-{segment.id}"
            lines.append(f"| [{segment.start_formatted}](#{anchor}) | {preview} |")

        if len(segments) > 20:
            lines.append(f"| ... | *({len(segments) - 20} more segments)* |")

        return "\n".join(lines)

    def save(
        self,
        content: str,
        output_path: str,
        create_dirs: bool = True
    ) -> str:
        """
        Save markdown content to a file.

        Args:
            content: Markdown content to save.
            output_path: Path to save the file.
            create_dirs: Create parent directories if needed.

        Returns:
            Absolute path to the saved file.
        """
        output_path = os.path.abspath(output_path)

        if create_dirs:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def generate_output_path(
        self,
        source_url: str,
        output_dir: Optional[str] = None,
        suffix: str = "_transcript"
    ) -> str:
        """
        Generate an output path for the markdown file.

        Args:
            source_url: The source stream URL.
            output_dir: Optional output directory.
            suffix: Suffix to add to the filename.

        Returns:
            Generated output path.
        """
        source_name = sanitize_url_to_filename(source_url)

        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = Path(".")

        return str(output_dir / f"{source_name}{suffix}.md")
