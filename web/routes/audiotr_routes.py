import asyncio
import uuid
from html import escape
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse

from ..adapters.audiotr_adapter import AudiotrAdapter
from ..config import AUDIO_FORMATS, WHISPER_MODELS, MARKDOWN_STYLES, DEVICE_CHOICES
from ..jobs import JobStatus

router = APIRouter()


@router.get("")
async def audiotr_form(request: Request):
    templates = request.app.state.templates
    settings = request.app.state.settings
    return templates.TemplateResponse("audiotr.html", {
        "request": request,
        "active_page": "audiotr",
        "settings": settings,
        "whisper_models": WHISPER_MODELS,
        "markdown_styles": MARKDOWN_STYLES,
        "device_choices": DEVICE_CHOICES,
        "supported_formats": ", ".join(sorted(AUDIO_FORMATS)),
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
        "browse_url": "/audiotr/browse",
    })


@router.post("/upload")
async def audiotr_upload(
    request: Request,
    file: UploadFile = File(None),
    model: str = Form(""),
    style: str = Form(""),
    language: str = Form(""),
    device: str = Form(""),
    include_metadata: str = Form(""),
    batch_process: str = Form(""),
    input_dir: str = Form(""),
    output_dir: str = Form(""),
):
    templates = request.app.state.templates
    settings = request.app.state.settings
    job_manager = request.app.state.job_manager
    executor = request.app.state.executor
    upload_dir = request.app.state.upload_dir
    resolved_output = Path(output_dir) if output_dir else Path(settings.audio_output_dir)
    resolved_output.mkdir(parents=True, exist_ok=True)

    job_settings = {
        "whisper_model": model or settings.whisper_model,
        "markdown_style": style or settings.markdown_style,
        "language": language or settings.language,
        "device": device or settings.device,
        "include_metadata": include_metadata == "on" if include_metadata else settings.include_metadata,
    }

    # Batch mode
    if batch_process == "on":
        resolved_input = Path(input_dir) if input_dir else Path(settings.audio_input_dir)
        file_paths = [
            str(f) for f in resolved_input.iterdir()
            if f.is_file() and f.suffix.lower() in AUDIO_FORMATS
        ]
        if not file_paths:
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error": f"No audio files found in {resolved_input} directory.",
            })
        job = job_manager.create_job("audiotr", f"Batch ({len(file_paths)} files)", job_settings)
        executor.submit(AudiotrAdapter.run_batch, job, file_paths, str(resolved_output), job_settings)
        return templates.TemplateResponse("partials/audiotr_progress.html", {
            "request": request,
            "job_id": job.id,
        })

    # Single file mode
    if not file or not file.filename:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": "No file selected. Please choose an audio file to upload.",
        })

    ext = Path(file.filename).suffix.lower()
    if ext not in AUDIO_FORMATS:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": f"Unsupported format '{ext}'. Supported: {', '.join(sorted(AUDIO_FORMATS))}",
        })

    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    save_path = upload_dir / unique_name
    await file.seek(0)
    content = await file.read()
    if not content:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": (
                "Upload failed — the file appears to be empty. "
                "If the file is stored in iCloud or another cloud service, "
                "ensure it is fully downloaded to your Mac before uploading."
            ),
        })
    save_path.write_bytes(content)

    job = job_manager.create_job("audiotr", file.filename, job_settings)
    executor.submit(AudiotrAdapter.run, job, str(save_path), str(resolved_output), job_settings, file.filename)

    return templates.TemplateResponse("partials/audiotr_progress.html", {
        "request": request,
        "job_id": job.id,
    })


@router.get("/jobs/{job_id}/stream")
async def audiotr_stream(request: Request, job_id: str):
    job_manager = request.app.state.job_manager
    templates = request.app.state.templates

    async def event_generator():
        last_message = ""
        while True:
            if await request.is_disconnected():
                break

            job = job_manager.get_job(job_id)
            if not job:
                yield {"event": "error", "data": "Job not found"}
                break

            progress_html = templates.get_template("partials/progress_bar.html").render(
                progress=job.progress,
                message=job.progress_message,
            )
            yield {"event": "progress", "data": progress_html}

            # Send verbose log entry when message changes
            if job.progress_message and job.progress_message != last_message:
                last_message = job.progress_message
                safe_msg = escape(job.progress_message)
                log_html = f'<div class="log-line">[{job.progress}%] {safe_msg}</div>'
                yield {"event": "log", "data": log_html}

            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                if job.status == JobStatus.COMPLETED:
                    yield {"event": "log", "data": '<div class="log-line log-line--done">Transcription complete.</div>'}
                else:
                    safe_err = escape(job.error or "Unknown error")
                    yield {"event": "log", "data": f'<div class="log-line log-line--error">Error: {safe_err}</div>'}
                yield {"event": "complete", "data": ""}
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@router.get("/jobs/{job_id}/result")
async def audiotr_result(request: Request, job_id: str):
    templates = request.app.state.templates
    job_manager = request.app.state.job_manager
    job = job_manager.get_job(job_id)
    if not job:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": "Job not found.",
        })
    return templates.TemplateResponse("partials/result.html", {
        "request": request,
        "job": job.to_dict(),
        "tool": "audiotr",
    })


@router.get("/jobs/{job_id}/download")
async def audiotr_download(request: Request, job_id: str):
    job_manager = request.app.state.job_manager
    job = job_manager.get_job(job_id)
    if not job or not job.result or "output_path" not in job.result:
        return HTMLResponse("File not available", status_code=404)
    output_path = Path(job.result["output_path"])
    if not output_path.exists():
        return HTMLResponse("File not found", status_code=404)
    return FileResponse(
        str(output_path),
        media_type="text/markdown",
        filename=output_path.name,
    )
