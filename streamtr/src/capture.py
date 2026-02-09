"""
Stream capture module using FFmpeg.

Captures audio from streaming URLs and converts to WAV for Whisper transcription.
"""

import json
import os
import re
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


class StreamCaptureError(Exception):
    """Exception raised when stream capture fails."""
    pass


def parse_duration(duration_str: str) -> float:
    """
    Parse a duration string into seconds.

    Supports:
        - Plain seconds: "60", "90.5"
        - Minutes: "5m"
        - Hours: "1h"
        - Combinations: "1h30m", "2h15m30s"

    Args:
        duration_str: Duration string to parse.

    Returns:
        Duration in seconds as a float.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    duration_str = duration_str.strip()

    # Try plain number (seconds)
    try:
        return float(duration_str)
    except ValueError:
        pass

    # Parse h/m/s components
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?$'
    match = re.match(pattern, duration_str, re.IGNORECASE)

    if not match or not any(match.groups()):
        raise ValueError(
            f"Invalid duration format: '{duration_str}'. "
            f"Use seconds (60), minutes (5m), hours (1h), or combos (1h30m)."
        )

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = float(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def sanitize_url_to_filename(url: str) -> str:
    """
    Convert a URL to a safe filename stem.

    Extracts the last meaningful path segment, strips extension,
    and replaces unsafe characters.

    Args:
        url: The source URL.

    Returns:
        A filesystem-safe filename stem.
    """
    parsed = urlparse(url)

    # Try to get a meaningful name from the path
    path = parsed.path.rstrip("/")
    if path:
        name = Path(path).stem or Path(path).name
    else:
        name = parsed.hostname or "stream"

    # Replace unsafe characters
    name = re.sub(r'[^\w\-.]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores
    name = name.strip('_')

    return name or "stream"


class StreamCapture:
    """Capture audio from streaming URLs via FFmpeg."""

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the stream capture module.

        Args:
            temp_dir: Optional directory for temporary files.
                     If None, uses system temp directory.
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self._verify_ffmpeg()

    def _verify_ffmpeg(self) -> None:
        """Verify that FFmpeg is installed and accessible."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=True
            )
        except FileNotFoundError:
            raise StreamCaptureError(
                "FFmpeg not found. Please install FFmpeg:\n"
                "  - macOS: brew install ffmpeg\n"
                "  - Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  - Windows: Download from https://ffmpeg.org/download.html"
            )
        except subprocess.CalledProcessError as e:
            raise StreamCaptureError(f"FFmpeg error: {e.stderr}")

    def get_stream_info(self, url: str) -> dict:
        """
        Probe a stream URL for metadata using ffprobe.

        Non-fatal: returns partial or empty dict on timeout/failure.

        Args:
            url: The stream URL to probe.

        Returns:
            Dictionary with stream information.
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            url
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return {}

            info = json.loads(result.stdout)

            # Extract relevant information
            duration = info.get("format", {}).get("duration")
            duration = float(duration) if duration else None

            # Find audio stream
            audio_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            return {
                "duration": duration,
                "duration_formatted": self._format_duration(duration) if duration else None,
                "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
                "sample_rate": audio_stream.get("sample_rate") if audio_stream else None,
                "channels": audio_stream.get("channels") if audio_stream else None,
                "bitrate": audio_stream.get("bit_rate") if audio_stream else None,
                "format": info.get("format", {}).get("format_name"),
                "url": url,
            }

        except subprocess.TimeoutExpired:
            print("  Stream probe timed out (30s). Proceeding without metadata.")
            return {"url": url}
        except Exception:
            return {"url": url}

    def capture_audio(
        self,
        url: str,
        output_path: Optional[str] = None,
        duration: Optional[float] = None
    ) -> Tuple[str, dict]:
        """
        Capture audio from a stream URL to a WAV file.

        Uses FFmpeg to strip video (-vn) and convert to 16kHz mono PCM WAV
        suitable for Whisper transcription. Handles Ctrl+C gracefully by
        terminating FFmpeg and keeping the partial capture.

        Args:
            url: The stream URL to capture from.
            output_path: Optional output path for the WAV file.
                        If None, creates a temporary file.
            duration: Optional duration in seconds to capture.
                     If None, captures until stream ends.

        Returns:
            Tuple of (wav_path, capture_info) where capture_info contains
            metadata about the capture process.

        Raises:
            StreamCaptureError: If capture fails.
        """
        if output_path is None:
            name = sanitize_url_to_filename(url)
            output_path = os.path.join(
                self.temp_dir,
                f"{name}_capture.wav"
            )

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", url,
            "-vn",                  # Strip video
            "-acodec", "pcm_s16le", # 16-bit PCM
            "-ar", "16000",         # 16kHz sample rate
            "-ac", "1",             # Mono
        ]

        if duration is not None:
            cmd.extend(["-t", str(duration)])

        cmd.extend(["-y", output_path])  # Overwrite output

        capture_info = {
            "url": url,
            "output_path": output_path,
            "duration_requested": duration,
            "interrupted": False,
            "start_time": time.time(),
        }

        process = None
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for process to complete
            _, stderr = process.communicate()

            capture_info["end_time"] = time.time()
            capture_info["elapsed"] = capture_info["end_time"] - capture_info["start_time"]

            if process.returncode != 0 and not os.path.exists(output_path):
                stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""
                raise StreamCaptureError(
                    f"FFmpeg capture failed (exit code {process.returncode}):\n{stderr_text}"
                )

        except KeyboardInterrupt:
            # Graceful Ctrl+C handling: terminate FFmpeg, keep partial capture
            capture_info["interrupted"] = True
            capture_info["end_time"] = time.time()
            capture_info["elapsed"] = capture_info["end_time"] - capture_info["start_time"]

            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            print("\n  Capture interrupted. Keeping partial audio.")

        # Verify output exists and has content
        if not os.path.exists(output_path):
            raise StreamCaptureError("Capture produced no output file.")

        file_size = os.path.getsize(output_path)
        if file_size < 100:  # WAV header alone is ~44 bytes
            raise StreamCaptureError("Capture produced an empty or invalid audio file.")

        capture_info["file_size"] = file_size
        capture_info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

        return output_path, capture_info

    def cleanup(self, audio_path: str) -> None:
        """
        Remove a temporary audio file.

        Args:
            audio_path: Path to the audio file to remove.
        """
        if os.path.exists(audio_path):
            os.remove(audio_path)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
