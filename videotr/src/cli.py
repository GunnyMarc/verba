"""
Command-line interface for video transcription.

Provides a user-friendly CLI for transcribing video files to markdown.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click

from .pipeline import TranscriptionPipeline
from .extractor import SUPPORTED_FORMATS
from .config import (
    WHISPER_MODELS, DEVICE_CHOICES,
    check_ffmpeg, initialize_config, load_config, save_config,
    prompt_location, display_config, ensure_conf_dir_and_file,
    configure_settings,
    clear_cache as clear_pycache,
    get_effective_device, get_effective_language,
)


MARKDOWN_STYLES = ["simple", "timestamped", "detailed", "srt_style"]


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║           VIDEO TRANSCRIBER - Video to Markdown           ║
║        Supports: .mov, .mpeg, .mkv, .mp4, .avi, .webm     ║
╚═══════════════════════════════════════════════════════════╝
    """
    click.echo(click.style(banner, fg="cyan"))


def validate_video_path(ctx, param, value):
    """Validate that the video file exists and is supported."""
    if value is None:
        return None

    path = Path(value)

    if not path.exists():
        raise click.BadParameter(f"File not found: {value}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise click.BadParameter(
            f"Unsupported format: {path.suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    return str(path.absolute())


def validate_video_paths(ctx, param, value):
    """Validate multiple video file paths."""
    validated = []
    for v in value:
        validated.append(validate_video_path(ctx, param, v))
    return validated


def prompt_transcription_mode() -> str:
    """Prompt the user to select a transcription mode."""
    print("")
    print("Transcription Mode:")
    print("  1. transcribe  - Transcribe a single video file")
    print("  2. batch       - Batch transcribe multiple video files")
    print("")

    while True:
        raw = input("Select mode [1/2]: ").strip()
        if raw == "1" or raw.lower() == "transcribe":
            return "transcribe"
        elif raw == "2" or raw.lower() == "batch":
            return "batch"
        print("  Invalid selection. Enter 1 or 2.")


def get_source_location(config):
    """Get source file location from config or prompt the user."""
    source = config.get("Location", "source", fallback=None)
    if source and os.path.isdir(source):
        return source, config

    config = prompt_location(config)
    save_config(config)
    return config.get("Location", "source"), config


def run_transcribe_mode(config, cli_model, cli_device, cli_language,
                        style, keep_audio, no_metadata, quiet):
    """Run single-file transcription mode."""
    source, config = get_source_location(config)

    # Prompt for specific video file
    video_path = input("Video file to transcribe (path or filename in source dir): ").strip()
    if not video_path:
        click.echo(click.style("No file specified.", fg="red"), err=True)
        sys.exit(1)

    # Resolve relative to source dir if not absolute
    if not os.path.isabs(video_path):
        video_path = os.path.join(source, video_path)

    video_path = os.path.abspath(video_path)

    if not os.path.exists(video_path):
        click.echo(click.style(f"File not found: {video_path}", fg="red"), err=True)
        sys.exit(1)

    if Path(video_path).suffix.lower() not in SUPPORTED_FORMATS:
        click.echo(click.style(
            f"Unsupported format: {Path(video_path).suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            fg="red"), err=True)
        sys.exit(1)

    model = cli_model or config.get("Model", "model", fallback="base")
    device = cli_device or get_effective_device(config)
    language = cli_language or get_effective_language(config)
    output_dir = config.get("Directories", "output_dir", fallback=None)

    if not quiet:
        click.echo(f"Input:    {video_path}")
        click.echo(f"Model:    {model}")
        click.echo(f"Style:    {style}")
        click.echo(f"Language: {language or 'auto-detect'}")
        click.echo(f"Device:   {device or 'auto-detect'}")
        click.echo("")

    pipeline = TranscriptionPipeline(
        model=model,
        style=style,
        language=language,
        device=device,
        keep_audio=keep_audio,
        include_metadata=not no_metadata,
    )

    def progress_callback(progress: float, message: str):
        if not quiet:
            bar_width = 30
            filled = int(bar_width * progress)
            bar = "█" * filled + "░" * (bar_width - filled)
            click.echo(f"\r[{bar}] {progress*100:5.1f}% - {message}", nl=False)
            if progress >= 1.0:
                click.echo("")

    output_path = None
    if output_dir:
        output_path = os.path.join(
            output_dir,
            Path(video_path).stem + "_transcript.md"
        )

    result = pipeline.process(video_path, output_path, progress_callback if not quiet else None)

    if result.success:
        if not quiet:
            click.echo("")
            click.echo(click.style("Transcription complete!", fg="green", bold=True))
            click.echo(f"  Output:   {result.output_path}")
            click.echo(f"  Language: {result.transcription.language}")
            click.echo(f"  Words:    {result.transcription.word_count:,}")
            click.echo(f"  Segments: {result.transcription.segment_count}")
        else:
            click.echo(result.output_path)
    else:
        click.echo(click.style(f"Error: {result.error}", fg="red"), err=True)
        sys.exit(1)


def run_batch_mode(config, cli_model, cli_device, cli_language,
                   style, keep_audio, no_metadata, quiet):
    """Run batch transcription mode."""
    source, config = get_source_location(config)

    # Prompt for source files
    print(f"Source directory: {source}")
    raw = input("Enter video files (comma-separated names/paths, or 'all' for all in source dir): ").strip()

    if not raw:
        click.echo(click.style("No files specified.", fg="red"), err=True)
        sys.exit(1)

    if raw.lower() == "all":
        # Find all supported video files in source dir
        videos = []
        for f in sorted(os.listdir(source)):
            if Path(f).suffix.lower() in SUPPORTED_FORMATS:
                videos.append(os.path.join(source, f))
        if not videos:
            click.echo(click.style(f"No supported video files found in {source}", fg="red"), err=True)
            sys.exit(1)
    else:
        videos = []
        for entry in raw.split(","):
            entry = entry.strip()
            if not entry:
                continue
            if not os.path.isabs(entry):
                entry = os.path.join(source, entry)
            entry = os.path.abspath(entry)
            if not os.path.exists(entry):
                click.echo(click.style(f"File not found: {entry}", fg="red"), err=True)
                sys.exit(1)
            videos.append(entry)

    if not videos:
        click.echo(click.style("No files to process.", fg="red"), err=True)
        sys.exit(1)

    model = cli_model or config.get("Model", "model", fallback="base")
    device = cli_device or get_effective_device(config)
    language = cli_language or get_effective_language(config)
    output_dir = config.get("Directories", "output_dir", fallback=None)

    click.echo(f"Processing {len(videos)} video(s)...")
    click.echo("")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    pipeline = TranscriptionPipeline(
        model=model,
        style=style,
        language=language,
        device=device,
        keep_audio=keep_audio,
        include_metadata=not no_metadata,
    )

    def batch_callback(current: int, total: int, message: str):
        click.echo(f"[{current + 1}/{total}] {message}")

    results = pipeline.process_batch(videos, output_dir, batch_callback)

    # Summary
    click.echo("")
    click.echo("=" * 50)
    click.echo("BATCH PROCESSING SUMMARY")
    click.echo("=" * 50)

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    click.echo(f"Total: {len(results)}")
    click.echo(click.style(f"Successful: {len(successful)}", fg="green"))

    if failed:
        click.echo(click.style(f"Failed: {len(failed)}", fg="red"))
        click.echo("")
        click.echo("Failed files:")
        for r in failed:
            click.echo(f"  - {Path(r.video_path).name}: {r.error}")

    if successful:
        click.echo("")
        click.echo("Output files:")
        for r in successful:
            click.echo(f"  - {r.output_path}")


@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0", prog_name="video-transcribe")
@click.option(
    "-m", "--model",
    type=click.Choice(WHISPER_MODELS, case_sensitive=False),
    default=None,
    help="Whisper model to use. Overrides videotr.conf setting."
)
@click.option(
    "--device",
    type=click.Choice(["cuda", "cpu"]),
    default=None,
    help="Device to use (cuda/cpu). Overrides videotr.conf setting."
)
@click.option(
    "-l", "--language",
    type=str,
    default=None,
    help="Language code (e.g., 'en', 'es'). Overrides videotr.conf setting."
)
@click.option(
    "-s", "--style",
    type=click.Choice(MARKDOWN_STYLES, case_sensitive=False),
    default="timestamped",
    help="Markdown formatting style."
)
@click.option(
    "--keep-audio",
    is_flag=True,
    help="Keep the extracted audio file."
)
@click.option(
    "--no-metadata",
    is_flag=True,
    help="Exclude metadata from the markdown output."
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Suppress progress output."
)
@click.option(
    "--configure",
    is_flag=True,
    help="Review and update videotr.conf settings interactively."
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="Remove all __pycache__ directories and exit."
)
@click.pass_context
def main(
    ctx,
    model: Optional[str],
    device: Optional[str],
    language: Optional[str],
    style: str,
    keep_audio: bool,
    no_metadata: bool,
    quiet: bool,
    configure: bool,
    clear_cache: bool
):
    """
    Video Transcriber - Convert video files to markdown transcripts.

    Supports .mov, .mpeg, .mkv, .mp4, .avi, and .webm formats.
    Uses OpenAI Whisper for accurate speech-to-text transcription.

    At startup, reads or creates videotr.conf in the conf/ directory.
    Command-line flags override configuration file defaults.

    \b
    Subcommands:
        info VIDEO   Display video metadata
        models       List available Whisper models
        formats      List supported video formats

    \b
    Examples:
        python main.py --model medium --device cuda
        python main.py -l en --style detailed
        python main.py info video.mov
        python main.py models
        python main.py formats
    """
    # If a subcommand was invoked, let it handle everything
    if ctx.invoked_subcommand is not None:
        return

    if not quiet:
        print_banner()

    # Handle --clear-cache before anything else
    if clear_cache:
        clear_pycache()
        sys.exit(0)

    # Step 1: Check for ffmpeg
    check_ffmpeg()

    # Handle --configure: let user edit existing config entries
    if configure:
        ensure_conf_dir_and_file()
        config = load_config()
        configure_settings(config)
        save_config(config)
        display_config(config)
        print("Configuration updated.")
        sys.exit(0)

    # Step 2: Initialize configuration (conf dir, videotr.conf, directories)
    config = initialize_config(cli_model=model, cli_device=device)

    # Step 3: Override language if CLI flag provided
    if language:
        if not config.has_section("Language"):
            config.add_section("Language")
        config.set("Language", "language", language)

    # Step 4: Confirm settings before proceeding
    while True:
        proceed = input("Do you want to proceed? [Y/n]: ").strip().lower()
        if proceed in ("", "y"):
            break
        elif proceed == "n":
            print("Exiting videotr.")
            sys.exit(0)
        print("  Invalid selection. Enter Y or N.")

    # Step 5: Prompt transcription mode
    mode = prompt_transcription_mode()

    # Step 6: Run the selected mode
    if mode == "transcribe":
        run_transcribe_mode(
            config, model, device, language,
            style, keep_audio, no_metadata, quiet
        )
    else:
        run_batch_mode(
            config, model, device, language,
            style, keep_audio, no_metadata, quiet
        )


@main.command()
@click.argument("video", callback=validate_video_path)
def info(video: str):
    """
    Display information about a video file.

    VIDEO: Path to the video file.
    """
    from .extractor import AudioExtractor

    print_banner()

    extractor = AudioExtractor()
    video_info = extractor.get_video_info(video)

    click.echo(f"File: {Path(video).name}")
    click.echo("")
    click.echo("Video Information:")
    click.echo(f"  Duration: {video_info.get('duration_formatted', 'Unknown')}")
    click.echo(f"  Format: {video_info.get('format', 'Unknown')}")
    click.echo(f"  Has Audio: {'Yes' if video_info.get('has_audio') else 'No'}")

    if video_info.get("has_audio"):
        click.echo("")
        click.echo("Audio Track:")
        click.echo(f"  Codec: {video_info.get('audio_codec', 'Unknown')}")
        click.echo(f"  Sample Rate: {video_info.get('sample_rate', 'Unknown')} Hz")
        click.echo(f"  Channels: {video_info.get('channels', 'Unknown')}")


@main.command()
def models():
    """List available Whisper models with descriptions."""
    print_banner()

    click.echo("Available Whisper Models:")
    click.echo("")

    model_info = [
        ("tiny", "~39M params", "Fastest, lowest accuracy", "~1GB VRAM"),
        ("base", "~74M params", "Good balance for quick transcriptions", "~1GB VRAM"),
        ("small", "~244M params", "Better accuracy, reasonable speed", "~2GB VRAM"),
        ("medium", "~769M params", "High accuracy, slower", "~5GB VRAM"),
        ("large", "~1550M params", "Best accuracy, slowest", "~10GB VRAM"),
        ("large-v2", "~1550M params", "Improved large model", "~10GB VRAM"),
        ("large-v3", "~1550M params", "Latest large model", "~10GB VRAM"),
    ]

    for name, params, desc, vram in model_info:
        click.echo(f"  {name:12} {params:15} {desc:40} {vram}")

    click.echo("")
    click.echo("Recommendation:")
    click.echo("  - Use 'base' for quick transcriptions")
    click.echo("  - Use 'small' or 'medium' for better accuracy")
    click.echo("  - Use 'large-v3' for best quality (requires GPU)")


@main.command()
def formats():
    """List supported video formats."""
    print_banner()

    click.echo("Supported Video Formats:")
    click.echo("")

    format_info = [
        (".mov", "Apple QuickTime Movie"),
        (".mpeg/.mpg", "MPEG Video"),
        (".mkv", "Matroska Video"),
        (".mp4", "MPEG-4 Video"),
        (".avi", "Audio Video Interleave"),
        (".webm", "WebM Video"),
    ]

    for ext, desc in format_info:
        click.echo(f"  {ext:15} {desc}")


if __name__ == "__main__":
    main()
