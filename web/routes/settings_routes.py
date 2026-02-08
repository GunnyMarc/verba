from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from ..config import (
    WHISPER_MODELS, DEVICE_CHOICES, MARKDOWN_STYLES,
    VENDOR_DISPLAY_NAMES,
)

router = APIRouter()


@router.get("")
async def settings_page(request: Request):
    templates = request.app.state.templates
    settings = request.app.state.settings
    keystore = request.app.state.keystore
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "active_page": "settings",
        "settings": settings,
        "whisper_models": WHISPER_MODELS,
        "device_choices": DEVICE_CHOICES,
        "markdown_styles": MARKDOWN_STYLES,
        "vendor_names": VENDOR_DISPLAY_NAMES,
        "stored_vendors": keystore.stored_vendors(),
    })


@router.post("")
async def settings_update(
    request: Request,
    whisper_model: str = Form(""),
    device: str = Form(""),
    language: str = Form(""),
    markdown_style: str = Form(""),
    include_metadata: str = Form(""),
    ollama_base_url: str = Form(""),
    video_input_dir: str = Form(""),
    video_output_dir: str = Form(""),
    audio_input_dir: str = Form(""),
    audio_output_dir: str = Form(""),
    summary_input_dir: str = Form(""),
    summary_output_dir: str = Form(""),
    api_vendor: str = Form(""),
    api_key: str = Form(""),
):
    settings = request.app.state.settings
    keystore = request.app.state.keystore
    templates = request.app.state.templates

    # Update transcription settings
    if whisper_model:
        settings.whisper_model = whisper_model
    if device:
        settings.device = device
    if language:
        settings.language = language
    if markdown_style:
        settings.markdown_style = markdown_style
    settings.include_metadata = include_metadata == "on"
    if ollama_base_url:
        settings.ollama_base_url = ollama_base_url

    # Update file location settings
    for field_name, field_value in (
        ("video_input_dir", video_input_dir),
        ("video_output_dir", video_output_dir),
        ("audio_input_dir", audio_input_dir),
        ("audio_output_dir", audio_output_dir),
        ("summary_input_dir", summary_input_dir),
        ("summary_output_dir", summary_output_dir),
    ):
        if field_value:
            setattr(settings, field_name, field_value)
            Path(field_value).mkdir(parents=True, exist_ok=True)

    # Save API key if provided
    if api_vendor and api_key:
        keystore.save_key(api_vendor, api_key)
        keystore.apply_to_env()

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "active_page": "settings",
        "settings": settings,
        "whisper_models": WHISPER_MODELS,
        "device_choices": DEVICE_CHOICES,
        "markdown_styles": MARKDOWN_STYLES,
        "vendor_names": VENDOR_DISPLAY_NAMES,
        "stored_vendors": keystore.stored_vendors(),
        "saved": True,
    })


@router.get("/browse")
async def browse_directories(request: Request, path: str = "", target: str = ""):
    templates = request.app.state.templates

    browse_path = Path(path) if path else Path.home()
    if not browse_path.is_dir():
        browse_path = browse_path.parent if browse_path.parent.is_dir() else Path.home()

    dirs = []
    try:
        for entry in sorted(browse_path.iterdir()):
            if entry.is_dir():
                dirs.append(entry.name)
    except PermissionError:
        pass

    return templates.TemplateResponse("partials/browse.html", {
        "request": request,
        "current_path": str(browse_path),
        "parent_path": str(browse_path.parent),
        "dirs": dirs,
        "target": target,
    })
