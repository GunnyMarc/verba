"""
Audio extraction module for video files.

Extracts audio from .mov, .mpeg, and .mkv video files using FFmpeg.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

# Supported video formats
SUPPORTED_FORMATS = {".mov", ".mpeg", ".mpg", ".mkv", ".mp4", ".avi", ".webm"}


class AudioExtractionError(Exception):
    """Exception raised when audio extraction fails."""
    pass


class AudioExtractor:
    """Extract audio from video files using FFmpeg."""

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the audio extractor.

        Args:
            temp_dir: Optional directory for temporary files.
                     If None, uses system temp directory.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self._verify_ffmpeg()

    def _verify_ffmpeg(self) -> None:
        """Verify that FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=True
            )
        except FileNotFoundError:
            raise AudioExtractionError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  - macOS: brew install ffmpeg\n"
                "  - Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  - Windows: Download from https://ffmpeg.org/download.html"
            )
        except subprocess.CalledProcessError as e:
            raise AudioExtractionError(f"FFmpeg error: {e.stderr}")

    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported.

        Args:
            file_path: Path to the video file.

        Returns:
            True if the format is supported, False otherwise.
        """
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_FORMATS

    def get_video_info(self, video_path: str) -> dict:
        """
        Get information about the video file.

        Args:
            video_path: Path to the video file.

        Returns:
            Dictionary with video information (duration, codec, etc.)
        """
        if not os.path.exists(video_path):
            raise AudioExtractionError(f"Video file not found: {video_path}")

        cmd = [
            "ffprobe",
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            info = json.loads(result.stdout)

            # Extract relevant information
            duration = float(info.get("format", {}).get("duration", 0))

            # Find audio stream
            audio_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            return {
                "duration": duration,
                "duration_formatted": self._format_duration(duration),
                "has_audio": audio_stream is not None,
                "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
                "sample_rate": audio_stream.get("sample_rate") if audio_stream else None,
                "channels": audio_stream.get("channels") if audio_stream else None,
                "format": info.get("format", {}).get("format_name"),
            }
        except subprocess.CalledProcessError as e:
            raise AudioExtractionError(f"Failed to get video info: {e.stderr}")
        except Exception as e:
            raise AudioExtractionError(f"Failed to parse video info: {str(e)}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        audio_format: str = "wav",
        sample_rate: int = 16000,
        mono: bool = True
    ) -> str:
        """
        Extract audio from a video file.

        Args:
            video_path: Path to the input video file.
            output_path: Optional path for the output audio file.
                        If None, creates a temporary file.
            audio_format: Output audio format (default: wav for best compatibility).
            sample_rate: Audio sample rate in Hz (default: 16000 for Whisper).
            mono: Convert to mono audio (default: True for Whisper).

        Returns:
            Path to the extracted audio file.

        Raises:
            AudioExtractionError: If extraction fails.
        """
        video_path = os.path.abspath(video_path)

        if not os.path.exists(video_path):
            raise AudioExtractionError(f"Video file not found: {video_path}")

        if not self.is_supported_format(video_path):
            ext = Path(video_path).suffix
            raise AudioExtractionError(
                f"Unsupported format: {ext}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

        # Check for audio track (non-fatal probe — let ffmpeg try regardless)
        try:
            info = self.get_video_info(video_path)
            if not info["has_audio"]:
                raise AudioExtractionError("Video file has no audio track")
        except AudioExtractionError as e:
            if "no audio track" in str(e):
                raise

        # Generate output path if not provided
        if output_path is None:
            video_name = Path(video_path).stem
            output_path = os.path.join(
                self.temp_dir,
                f"{video_name}_audio.{audio_format}"
            )

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
            "-ar", str(sample_rate),  # Sample rate
            "-y",  # Overwrite output
        ]

        if mono:
            cmd.extend(["-ac", "1"])  # Mono audio

        cmd.append(output_path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return output_path
        except subprocess.CalledProcessError as e:
            raise AudioExtractionError(
                f"Failed to extract audio: {e.stderr}"
            )

    def extract_audio_segment(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract a specific segment of audio from a video file.

        Args:
            video_path: Path to the input video file.
            start_time: Start time in seconds.
            end_time: End time in seconds.
            output_path: Optional path for the output audio file.

        Returns:
            Path to the extracted audio segment.
        """
        video_path = os.path.abspath(video_path)

        if output_path is None:
            video_name = Path(video_path).stem
            output_path = os.path.join(
                self.temp_dir,
                f"{video_name}_{start_time}_{end_time}.wav"
            )

        duration = end_time - start_time

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            output_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise AudioExtractionError(
                f"Failed to extract audio segment: {e.stderr}"
            )

    def cleanup(self, audio_path: str) -> None:
        """
        Remove a temporary audio file.

        Args:
            audio_path: Path to the audio file to remove.
        """
        if os.path.exists(audio_path):
            os.remove(audio_path)
