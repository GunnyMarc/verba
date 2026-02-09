import asyncio
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from sse_starlette.sse import EventSourceResponse

from ..adapters.transtr_adapter import TranstrAdapter
from ..config import TRANSCRIPT_FORMATS, INSTRUCTIONS_FORMATS, AVAILABLE_MODELS, MODEL_DISPLAY_LABELS
from ..file_readers import read_instructions_file
from ..jobs import JobStatus

router = APIRouter()


@router.get("")
async def transtr_form(request: Request):
    templates = request.app.state.templates
    settings = request.app.state.settings
    return templates.TemplateResponse("transtr.html", {
        "request": request,
        "active_page": "transtr",
        "settings": settings,
        "available_models": AVAILABLE_MODELS,
        "model_labels": MODEL_DISPLAY_LABELS,
        "supported_formats": ", ".join(sorted(TRANSCRIPT_FORMATS)),
        "instructions_formats": ", ".join(sorted(INSTRUCTIONS_FORMATS)),
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
        "browse_url": "/transtr/browse",
    })


@router.post("/browse/mkdir")
async def browse_mkdir(request: Request, path: str = Form(""), name: str = Form(""), target: str = Form("")):
    templates = request.app.state.templates

    parent = Path(path) if path else Path.home()
    if name:
        new_dir = parent / name
        new_dir.mkdir(parents=True, exist_ok=True)

    browse_path = new_dir if name and new_dir.is_dir() else parent
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
        "browse_url": "/transtr/browse",
    })


@router.post("/process")
async def transtr_process(
    request: Request,
    text: str = Form(""),
    file: UploadFile = File(None),
    model: str = Form("llama3:latest"),
    instructions: str = Form(""),
    instructions_file: UploadFile = File(None),
    batch_process: str = Form(""),
    input_dir: str = Form(""),
    output_dir: str = Form(""),
):
    templates = request.app.state.templates
    settings = request.app.state.settings
    job_manager = request.app.state.job_manager
    executor = request.app.state.executor
    resolved_output = Path(output_dir) if output_dir else Path(settings.summary_output_dir)
    resolved_output.mkdir(parents=True, exist_ok=True)

    job_settings = {
        "model": model,
        "ollama_base_url": settings.ollama_base_url,
    }

    # Read instructions from uploaded file if provided
    if instructions_file and instructions_file.filename:
        ext = Path(instructions_file.filename).suffix.lower()
        if ext not in INSTRUCTIONS_FORMATS:
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error": f"Unsupported instructions format '{ext}'. Supported: {', '.join(sorted(INSTRUCTIONS_FORMATS))}",
            })
        try:
            file_data = await instructions_file.read()
            default_instructions = read_instructions_file(file_data, instructions_file.filename)
        except Exception as e:
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error": f"Failed to read instructions file: {e}",
            })
    else:
        default_instructions = instructions or "Summarize the following transcript clearly and concisely."

    # Batch mode
    if batch_process == "on":
        resolved_input = Path(input_dir) if input_dir else Path(settings.summary_input_dir)
        texts = []
        for f in sorted(resolved_input.iterdir()):
            if f.is_file() and f.suffix.lower() in TRANSCRIPT_FORMATS:
                try:
                    content = f.read_text(encoding="utf-8")
                    texts.append({"filename": f.name, "text": content})
                except Exception:
                    pass
        if not texts:
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error": f"No transcript files found in {resolved_input} directory.",
            })
        job = job_manager.create_job("transtr", f"Batch ({len(texts)} files)", job_settings)
        executor.submit(TranstrAdapter.run_batch, job, texts, default_instructions, job_settings, str(resolved_output))
        return templates.TemplateResponse("partials/progress.html", {
            "request": request,
            "job_id": job.id,
            "tool": "transtr",
        })

    # Get text from file upload if no direct text
    input_text = text.strip()
    filename = "direct input"

    if not input_text and file and file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in TRANSCRIPT_FORMATS:
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error": f"Unsupported format '{ext}'. Supported: {', '.join(sorted(TRANSCRIPT_FORMATS))}",
            })
        content = await file.read()
        input_text = content.decode("utf-8", errors="replace")
        filename = file.filename

    if not input_text:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": "No text provided. Please paste text or upload a file.",
        })

    job = job_manager.create_job("transtr", filename, job_settings)
    executor.submit(TranstrAdapter.run, job, input_text, default_instructions, job_settings, str(resolved_output), filename)

    return templates.TemplateResponse("partials/progress.html", {
        "request": request,
        "job_id": job.id,
        "tool": "transtr",
    })


@router.get("/jobs/{job_id}/stream")
async def transtr_stream(request: Request, job_id: str):
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
async def transtr_result(request: Request, job_id: str):
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
        "tool": "transtr",
    })
