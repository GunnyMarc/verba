from pathlib import Path

from fastapi import APIRouter, Request, Form

router = APIRouter()


@router.get("")
async def streamtr_form(request: Request):
    templates = request.app.state.templates
    settings = request.app.state.settings
    return templates.TemplateResponse("streamtr.html", {
        "request": request,
        "active_page": "streamtr",
        "settings": settings,
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
        "browse_url": "/streamtr/browse",
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
        "browse_url": "/streamtr/browse",
    })
