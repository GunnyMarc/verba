"""
Audio processing module for audio files.

Validates, analyzes, and converts audio files for Whisper transcription.
Supports .mp3, .wav, .aac, .flac, .m4a, .ogg, .wma, .opus, .aiff, and .alac.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

# Supported audio formats
SUPPORTED_FORMATS = {
    ".mp3", ".wav", ".aac", ".flac", ".m4a",
    ".ogg", ".wma", ".opus", ".aiff", ".alac"
}


class AudioProcessingError(Exception):
    """Exception raised when audio processing fails."""
    pass


class AudioProcessor:
    """Validate, analyze, and convert audio files for Whisper transcription."""

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the audio processor.

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
            raise AudioProcessingError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  - macOS: brew install ffmpeg\n"
                "  - Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  - Windows: Download from https://ffmpeg.org/download.html"
            )
        except subprocess.CalledProcessError as e:
            raise AudioProcessingError(f"FFmpeg error: {e.stderr}")

    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported.

        Args:
            file_path: Path to the audio file.

        Returns:
            True if the format is supported, False otherwise.
        """
        ext = Path(file_path).suffix.lower()
        return ext in SUPPORTED_FORMATS

    def get_audio_info(self, audio_path: str) -> dict:
        """
        Get information about an audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            Dictionary with audio information (duration, codec, sample rate, etc.)
        """
        if not os.path.exists(audio_path):
            raise AudioProcessingError(f"Audio file not found: {audio_path}")

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            audio_path
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
                "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
                "sample_rate": audio_stream.get("sample_rate") if audio_stream else None,
                "channels": audio_stream.get("channels") if audio_stream else None,
                "bitrate": audio_stream.get("bit_rate") if audio_stream else None,
                "format": info.get("format", {}).get("format_name"),
            }
        except subprocess.CalledProcessError as e:
            raise AudioProcessingError(f"Failed to get audio info: {e.stderr}")
        except Exception as e:
            raise AudioProcessingError(f"Failed to parse audio info: {str(e)}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _needs_conversion(self, audio_path: str) -> bool:
        """
        Check if the audio file needs conversion for Whisper compatibility.

        Whisper works best with 16kHz mono WAV. If the file is already in that
        format, conversion can be skipped entirely.

        Args:
            audio_path: Path to the audio file.

        Returns:
            True if conversion is needed, False if the file can be used directly.
        """
        ext = Path(audio_path).suffix.lower()
        if ext != ".wav":
            return True

        # Check sample rate and channels via ffprobe
        info = self.get_audio_info(audio_path)
        if info.get("sample_rate") != "16000":
            return True
        if info.get("channels") != 1:
            return True
        return False

    def prepare_audio(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        sample_rate: int = 16000,
        mono: bool = True
    ) -> Tuple[str, bool]:
        """
        Prepare an audio file for Whisper transcription.

        If the file is already Whisper-compatible (16kHz mono WAV), returns the
        original path with was_converted=False. Otherwise, converts it to a
        temporary WAV file.

        Args:
            audio_path: Path to the input audio file.
            output_path: Optional path for the converted audio file.
                        If None, creates a temporary file.
            sample_rate: Audio sample rate in Hz (default: 16000 for Whisper).
            mono: Convert to mono audio (default: True for Whisper).

        Returns:
            Tuple of (prepared_path, was_converted). If was_converted is False,
            the prepared_path is the original file (no cleanup needed).

        Raises:
            AudioProcessingError: If processing fails.
        """
        audio_path = os.path.abspath(audio_path)

        if not os.path.exists(audio_path):
            raise AudioProcessingError(f"Audio file not found: {audio_path}")

        if not self.is_supported_format(audio_path):
            ext = Path(audio_path).suffix
            raise AudioProcessingError(
                f"Unsupported format: {ext}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

        # Check if conversion is needed
        if not self._needs_conversion(audio_path):
            return audio_path, False

        # Generate output path if not provided
        if output_path is None:
            audio_name = Path(audio_path).stem
            output_path = os.path.join(
                self.temp_dir,
                f"{audio_name}_converted.wav"
            )

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
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
            return output_path, True
        except subprocess.CalledProcessError as e:
            raise AudioProcessingError(
                f"Failed to prepare audio: {e.stderr}"
            )

    def prepare_audio_segment(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract a specific segment from an audio file.

        Args:
            audio_path: Path to the input audio file.
            start_time: Start time in seconds.
            end_time: End time in seconds.
            output_path: Optional path for the output audio file.

        Returns:
            Path to the extracted audio segment.
        """
        audio_path = os.path.abspath(audio_path)

        if output_path is None:
            audio_name = Path(audio_path).stem
            output_path = os.path.join(
                self.temp_dir,
                f"{audio_name}_{start_time}_{end_time}.wav"
            )

        duration = end_time - start_time

        cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(duration),
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
            raise AudioProcessingError(
                f"Failed to prepare audio segment: {e.stderr}"
            )

    def cleanup(self, audio_path: str) -> None:
        """
        Remove a temporary audio file.

        Args:
            audio_path: Path to the audio file to remove.
        """
        if os.path.exists(audio_path):
            os.remove(audio_path)
