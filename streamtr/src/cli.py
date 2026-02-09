"""
Command-line interface for stream transcription.

Provides a user-friendly CLI for capturing and transcribing streaming audio to markdown.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click

from .pipeline import TranscriptionPipeline
from .capture import parse_duration
from .config import (
    WHISPER_MODELS, DEVICE_CHOICES,
    check_ffmpeg, initialize_config, load_config, save_config,
    display_config, ensure_conf_dir_and_file,
    configure_settings,
    clear_cache as clear_pycache,
    get_effective_device, get_effective_language,
)


MARKDOWN_STYLES = ["simple", "timestamped", "detailed", "srt_style"]


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║          STREAM TRANSCRIBER — Stream to Markdown              ║
║     Captures audio from streaming URLs via FFmpeg              ║
╚═══════════════════════════════════════════════════════════════╝
    """
    click.echo(click.style(banner, fg="cyan"))


def prompt_transcription_mode() -> str:
    """Prompt the user to select a transcription mode."""
    print("")
    print("Transcription Mode:")
    print("  1. transcribe  - Transcribe a single stream URL")
    print("  2. batch       - Batch transcribe multiple stream URLs")
    print("")

    while True:
        raw = input("Select mode [1/2]: ").strip()
        if raw == "1" or raw.lower() == "transcribe":
            return "transcribe"
        elif raw == "2" or raw.lower() == "batch":
            return "batch"
        print("  Invalid selection. Enter 1 or 2.")


def run_transcribe_mode(config, cli_model, cli_device, cli_language,
                        style, duration, keep_captured, no_metadata, quiet):
    """Run single-URL transcription mode."""
    # Prompt for stream URL
    url = input("Stream URL to transcribe: ").strip()
    if not url:
        click.echo(click.style("No URL specified.", fg="red"), err=True)
        sys.exit(1)

    model = cli_model or config.get("Model", "model", fallback="base")
    device = cli_device or get_effective_device(config)
    language = cli_language or get_effective_language(config)
    output_dir = config.get("Directories", "output_dir", fallback=None)

    # Parse duration if provided
    duration_seconds = None
    if duration:
        try:
            duration_seconds = parse_duration(duration)
        except ValueError as e:
            click.echo(click.style(str(e), fg="red"), err=True)
            sys.exit(1)

    if not quiet:
        click.echo(f"URL:      {url}")
        click.echo(f"Model:    {model}")
        click.echo(f"Style:    {style}")
        click.echo(f"Duration: {duration or 'until stream ends'}")
        click.echo(f"Language: {language or 'auto-detect'}")
        click.echo(f"Device:   {device or 'auto-detect'}")
        click.echo("")

    pipeline = TranscriptionPipeline(
        model=model,
        style=style,
        language=language,
        device=device,
        duration=duration_seconds,
        keep_captured=keep_captured,
        include_metadata=not no_metadata,
    )

    def progress_callback(progress: float, message: str):
        if not quiet:
            bar_width = 30
            filled = int(bar_width * progress)
            bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
            click.echo(f"\r[{bar}] {progress*100:5.1f}% - {message}", nl=False)
            if progress >= 1.0:
                click.echo("")

    output_path = None
    if output_dir:
        from .capture import sanitize_url_to_filename
        output_path = os.path.join(
            output_dir,
            sanitize_url_to_filename(url) + "_transcript.md"
        )

    result = pipeline.process(url, output_path, progress_callback if not quiet else None)

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
                   style, duration, keep_captured, no_metadata, quiet):
    """Run batch transcription mode."""
    print("")
    print("Enter stream URLs (one per line, or path to a text file containing URLs).")
    raw = input("URLs or file path: ").strip()

    if not raw:
        click.echo(click.style("No URLs specified.", fg="red"), err=True)
        sys.exit(1)

    # Check if it's a file path
    if os.path.isfile(raw):
        with open(raw, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        # Treat as comma-separated or single URL
        urls = [u.strip() for u in raw.split(",") if u.strip()]

    if not urls:
        click.echo(click.style("No URLs to process.", fg="red"), err=True)
        sys.exit(1)

    model = cli_model or config.get("Model", "model", fallback="base")
    device = cli_device or get_effective_device(config)
    language = cli_language or get_effective_language(config)
    output_dir = config.get("Directories", "output_dir", fallback=None)

    # Parse duration if provided
    duration_seconds = None
    if duration:
        try:
            duration_seconds = parse_duration(duration)
        except ValueError as e:
            click.echo(click.style(str(e), fg="red"), err=True)
            sys.exit(1)

    click.echo(f"Processing {len(urls)} stream URL(s)...")
    click.echo("")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    pipeline = TranscriptionPipeline(
        model=model,
        style=style,
        language=language,
        device=device,
        duration=duration_seconds,
        keep_captured=keep_captured,
        include_metadata=not no_metadata,
    )

    def batch_callback(current: int, total: int, message: str):
        click.echo(f"[{current + 1}/{total}] {message}")

    results = pipeline.process_batch(urls, output_dir, batch_callback)

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
        click.echo("Failed URLs:")
        for r in failed:
            click.echo(f"  - {r.stream_url}: {r.error}")

    if successful:
        click.echo("")
        click.echo("Output files:")
        for r in successful:
            click.echo(f"  - {r.output_path}")


@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0", prog_name="stream-transcribe")
@click.option(
    "-m", "--model",
    type=click.Choice(WHISPER_MODELS, case_sensitive=False),
    default=None,
    help="Whisper model to use. Overrides streamtr.conf setting."
)
@click.option(
    "--device",
    type=click.Choice(["cuda", "cpu"]),
    default=None,
    help="Device to use (cuda/cpu). Overrides streamtr.conf setting."
)
@click.option(
    "-l", "--language",
    type=str,
    default=None,
    help="Language code (e.g., 'en', 'es'). Overrides streamtr.conf setting."
)
@click.option(
    "-s", "--style",
    type=click.Choice(MARKDOWN_STYLES, case_sensitive=False),
    default="timestamped",
    help="Markdown formatting style."
)
@click.option(
    "-d", "--duration",
    type=str,
    default=None,
    help="Capture duration (e.g., '60', '5m', '1h30m'). Default: until stream ends."
)
@click.option(
    "--keep-captured",
    is_flag=True,
    help="Keep the captured WAV file after transcription."
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
    help="Review and update streamtr.conf settings interactively."
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
    duration: Optional[str],
    keep_captured: bool,
    no_metadata: bool,
    quiet: bool,
    configure: bool,
    clear_cache: bool
):
    """
    Stream Transcriber - Capture and transcribe streaming audio to markdown.

    Captures audio from streaming URLs via FFmpeg and transcribes using
    OpenAI Whisper for accurate speech-to-text transcription.

    At startup, reads or creates streamtr.conf in the conf/ directory.
    Command-line flags override configuration file defaults.

    \b
    Subcommands:
        models       List available Whisper models

    \b
    Examples:
        python -m streamtr.src.cli https://example.com/stream
        python -m streamtr.src.cli --model medium --device cuda
        python -m streamtr.src.cli -d 5m --style detailed
        python -m streamtr.src.cli models
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

    # Step 2: Initialize configuration (conf dir, streamtr.conf, directories)
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
            print("Exiting streamtr.")
            sys.exit(0)
        print("  Invalid selection. Enter Y or N.")

    # Step 5: Prompt transcription mode
    mode = prompt_transcription_mode()

    # Step 6: Run the selected mode
    if mode == "transcribe":
        run_transcribe_mode(
            config, model, device, language,
            style, duration, keep_captured, no_metadata, quiet
        )
    else:
        run_batch_mode(
            config, model, device, language,
            style, duration, keep_captured, no_metadata, quiet
        )


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


if __name__ == "__main__":
    main()
