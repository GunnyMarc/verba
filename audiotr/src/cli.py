"""
Command-line interface for audio transcription.

Provides a user-friendly CLI for transcribing audio files to markdown.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click

from .pipeline import TranscriptionPipeline
from .processor import SUPPORTED_FORMATS
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
╔═══════════════════════════════════════════════════════════════╗
║              AUDIO TRANSCRIBER - Audio to Markdown             ║
║   Supports: .mp3, .wav, .aac, .flac, .m4a, .ogg, .wma, etc.  ║
╚═══════════════════════════════════════════════════════════════╝
    """
    click.echo(click.style(banner, fg="cyan"))


def validate_audio_path(ctx, param, value):
    """Validate that the audio file exists and is supported."""
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


def validate_audio_paths(ctx, param, value):
    """Validate multiple audio file paths."""
    validated = []
    for v in value:
        validated.append(validate_audio_path(ctx, param, v))
    return validated


def prompt_transcription_mode() -> str:
    """Prompt the user to select a transcription mode."""
    print("")
    print("Transcription Mode:")
    print("  1. transcribe  - Transcribe a single audio file")
    print("  2. batch       - Batch transcribe multiple audio files")
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
                        style, keep_converted, no_metadata, quiet):
    """Run single-file transcription mode."""
    source, config = get_source_location(config)

    # Prompt for specific audio file
    audio_path = input("Audio file to transcribe (path or filename in source dir): ").strip()
    if not audio_path:
        click.echo(click.style("No file specified.", fg="red"), err=True)
        sys.exit(1)

    # Resolve relative to source dir if not absolute
    if not os.path.isabs(audio_path):
        audio_path = os.path.join(source, audio_path)

    audio_path = os.path.abspath(audio_path)

    if not os.path.exists(audio_path):
        click.echo(click.style(f"File not found: {audio_path}", fg="red"), err=True)
        sys.exit(1)

    if Path(audio_path).suffix.lower() not in SUPPORTED_FORMATS:
        click.echo(click.style(
            f"Unsupported format: {Path(audio_path).suffix}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
            fg="red"), err=True)
        sys.exit(1)

    model = cli_model or config.get("Model", "model", fallback="base")
    device = cli_device or get_effective_device(config)
    language = cli_language or get_effective_language(config)
    output_dir = config.get("Directories", "output_dir", fallback=None)

    if not quiet:
        click.echo(f"Input:    {audio_path}")
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
        keep_converted=keep_converted,
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
            Path(audio_path).stem + "_transcript.md"
        )

    result = pipeline.process(audio_path, output_path, progress_callback if not quiet else None)

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
                   style, keep_converted, no_metadata, quiet):
    """Run batch transcription mode."""
    source, config = get_source_location(config)

    # Prompt for source files
    print(f"Source directory: {source}")
    raw = input("Enter audio files (comma-separated names/paths, or 'all' for all in source dir): ").strip()

    if not raw:
        click.echo(click.style("No files specified.", fg="red"), err=True)
        sys.exit(1)

    if raw.lower() == "all":
        # Find all supported audio files in source dir
        audios = []
        for f in sorted(os.listdir(source)):
            if Path(f).suffix.lower() in SUPPORTED_FORMATS:
                audios.append(os.path.join(source, f))
        if not audios:
            click.echo(click.style(f"No supported audio files found in {source}", fg="red"), err=True)
            sys.exit(1)
    else:
        audios = []
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
            audios.append(entry)

    if not audios:
        click.echo(click.style("No files to process.", fg="red"), err=True)
        sys.exit(1)

    model = cli_model or config.get("Model", "model", fallback="base")
    device = cli_device or get_effective_device(config)
    language = cli_language or get_effective_language(config)
    output_dir = config.get("Directories", "output_dir", fallback=None)

    click.echo(f"Processing {len(audios)} audio file(s)...")
    click.echo("")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    pipeline = TranscriptionPipeline(
        model=model,
        style=style,
        language=language,
        device=device,
        keep_converted=keep_converted,
        include_metadata=not no_metadata,
    )

    def batch_callback(current: int, total: int, message: str):
        click.echo(f"[{current + 1}/{total}] {message}")

    results = pipeline.process_batch(audios, output_dir, batch_callback)

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
            click.echo(f"  - {Path(r.audio_path).name}: {r.error}")

    if successful:
        click.echo("")
        click.echo("Output files:")
        for r in successful:
            click.echo(f"  - {r.output_path}")


@click.group(invoke_without_command=True)
@click.version_option(version="1.0.0", prog_name="audio-transcribe")
@click.option(
    "-m", "--model",
    type=click.Choice(WHISPER_MODELS, case_sensitive=False),
    default=None,
    help="Whisper model to use. Overrides audiotr.conf setting."
)
@click.option(
    "--device",
    type=click.Choice(["cuda", "cpu"]),
    default=None,
    help="Device to use (cuda/cpu). Overrides audiotr.conf setting."
)
@click.option(
    "-l", "--language",
    type=str,
    default=None,
    help="Language code (e.g., 'en', 'es'). Overrides audiotr.conf setting."
)
@click.option(
    "-s", "--style",
    type=click.Choice(MARKDOWN_STYLES, case_sensitive=False),
    default="timestamped",
    help="Markdown formatting style."
)
@click.option(
    "--keep-converted",
    is_flag=True,
    help="Keep the converted WAV file after transcription."
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
    help="Review and update audiotr.conf settings interactively."
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
    keep_converted: bool,
    no_metadata: bool,
    quiet: bool,
    configure: bool,
    clear_cache: bool
):
    """
    Audio Transcriber - Convert audio files to markdown transcripts.

    Supports .mp3, .wav, .aac, .flac, .m4a, .ogg, .wma, .opus, .aiff, and .alac formats.
    Uses OpenAI Whisper for accurate speech-to-text transcription.

    At startup, reads or creates audiotr.conf in the conf/ directory.
    Command-line flags override configuration file defaults.

    \b
    Subcommands:
        info AUDIO   Display audio file metadata
        models       List available Whisper models
        formats      List supported audio formats

    \b
    Examples:
        python main.py --model medium --device cuda
        python main.py -l en --style detailed
        python main.py info recording.mp3
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

    # Step 2: Initialize configuration (conf dir, audiotr.conf, directories)
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
            print("Exiting audiotr.")
            sys.exit(0)
        print("  Invalid selection. Enter Y or N.")

    # Step 5: Prompt transcription mode
    mode = prompt_transcription_mode()

    # Step 6: Run the selected mode
    if mode == "transcribe":
        run_transcribe_mode(
            config, model, device, language,
            style, keep_converted, no_metadata, quiet
        )
    else:
        run_batch_mode(
            config, model, device, language,
            style, keep_converted, no_metadata, quiet
        )


@main.command()
@click.argument("audio", callback=validate_audio_path)
def info(audio: str):
    """
    Display information about an audio file.

    AUDIO: Path to the audio file.
    """
    from .processor import AudioProcessor

    print_banner()

    processor = AudioProcessor()
    audio_info = processor.get_audio_info(audio)

    click.echo(f"File: {Path(audio).name}")
    click.echo("")
    click.echo("Audio Information:")
    click.echo(f"  Duration: {audio_info.get('duration_formatted', 'Unknown')}")
    click.echo(f"  Format: {audio_info.get('format', 'Unknown')}")
    click.echo(f"  Codec: {audio_info.get('audio_codec', 'Unknown')}")
    click.echo(f"  Sample Rate: {audio_info.get('sample_rate', 'Unknown')} Hz")
    channels = audio_info.get('channels')
    if channels is not None:
        ch_label = "Mono" if channels == 1 else "Stereo" if channels == 2 else str(channels)
        click.echo(f"  Channels: {ch_label}")
    else:
        click.echo(f"  Channels: Unknown")
    bitrate = audio_info.get('bitrate')
    if bitrate:
        click.echo(f"  Bitrate: {int(bitrate) // 1000} kbps")


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
    """List supported audio formats."""
    print_banner()

    click.echo("Supported Audio Formats:")
    click.echo("")

    format_info = [
        (".mp3", "MPEG Audio Layer III"),
        (".wav", "Waveform Audio File"),
        (".aac", "Advanced Audio Coding"),
        (".flac", "Free Lossless Audio Codec"),
        (".m4a", "MPEG-4 Audio"),
        (".ogg", "Ogg Vorbis Audio"),
        (".wma", "Windows Media Audio"),
        (".opus", "Opus Audio"),
        (".aiff", "Audio Interchange File Format"),
        (".alac", "Apple Lossless Audio Codec"),
    ]

    for ext, desc in format_info:
        click.echo(f"  {ext:15} {desc}")


if __name__ == "__main__":
    main()
