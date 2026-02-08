import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse

from ..adapters.audiotr_adapter import AudiotrAdapter
from ..config import AUDIO_FORMATS, WHISPER_MODELS, MARKDOWN_STYLES, DEVICE_CHOICES
from ..jobs import JobStatus

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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
):
    templates = request.app.state.templates
    settings = request.app.state.settings
    job_manager = request.app.state.job_manager
    executor = request.app.state.executor
    upload_dir = request.app.state.upload_dir
    output_dir = request.app.state.output_dir

    job_settings = {
        "whisper_model": model or settings.whisper_model,
        "markdown_style": style or settings.markdown_style,
        "language": language or settings.language,
        "device": device or settings.device,
        "include_metadata": include_metadata == "on" if include_metadata else settings.include_metadata,
    }

    # Batch mode
    if batch_process == "on":
        input_dir = REPO_ROOT / "audiotr" / "input"
        file_paths = [
            str(f) for f in input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in AUDIO_FORMATS
        ]
        if not file_paths:
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error": "No audio files found in audiotr/input/ directory.",
            })
        job = job_manager.create_job("audiotr", f"Batch ({len(file_paths)} files)", job_settings)
        executor.submit(AudiotrAdapter.run_batch, job, file_paths, str(output_dir), job_settings)
        return templates.TemplateResponse("partials/progress.html", {
            "request": request,
            "job_id": job.id,
            "tool": "audiotr",
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
    content = await file.read()
    save_path.write_bytes(content)

    job = job_manager.create_job("audiotr", file.filename, job_settings)
    executor.submit(AudiotrAdapter.run, job, str(save_path), str(output_dir), job_settings)

    return templates.TemplateResponse("partials/progress.html", {
        "request": request,
        "job_id": job.id,
        "tool": "audiotr",
    })


@router.get("/jobs/{job_id}/stream")
async def audiotr_stream(request: Request, job_id: str):
    job_manager = request.app.state.job_manager
    templates = request.app.state.templates

    async def event_generator():
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

            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
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
