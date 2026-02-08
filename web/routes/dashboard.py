from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")
async def dashboard(request: Request):
    templates = request.app.state.templates
    job_manager = request.app.state.job_manager
    recent_jobs = job_manager.list_jobs()[:10]
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "recent_jobs": [j.to_dict() for j in recent_jobs],
    })
