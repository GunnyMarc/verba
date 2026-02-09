from fastapi import APIRouter, Request, Form

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
        "stored_keys": keystore.masked_keys(),
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

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "active_page": "settings",
        "settings": settings,
        "whisper_models": WHISPER_MODELS,
        "device_choices": DEVICE_CHOICES,
        "markdown_styles": MARKDOWN_STYLES,
        "vendor_names": VENDOR_DISPLAY_NAMES,
        "stored_keys": keystore.masked_keys(),
        "saved": True,
    })


@router.post("/keys/add")
async def add_key(request: Request, api_vendor: str = Form(""), api_key: str = Form("")):
    keystore = request.app.state.keystore
    templates = request.app.state.templates

    if api_vendor and api_key:
        keystore.save_key(api_vendor, api_key)
        keystore.apply_to_env()

    return templates.TemplateResponse("partials/stored_keys.html", {
        "request": request,
        "stored_keys": keystore.masked_keys(),
        "vendor_names": VENDOR_DISPLAY_NAMES,
    })


@router.post("/keys/delete")
async def delete_key(request: Request, vendor: str = Form("")):
    keystore = request.app.state.keystore
    templates = request.app.state.templates

    if vendor == "__all__":
        keystore.delete_all()
        # Re-initialise so the keystore can generate a fresh key next time
        keystore.__init__()
    elif vendor:
        keystore.delete_key(vendor)

    keystore.apply_to_env()

    return templates.TemplateResponse("partials/stored_keys.html", {
        "request": request,
        "stored_keys": keystore.masked_keys(),
        "vendor_names": VENDOR_DISPLAY_NAMES,
    })
