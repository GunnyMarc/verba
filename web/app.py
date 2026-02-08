from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import WebSettings
from .jobs import JobManager
from .keystore import KeyStore

WEB_DIR = Path(__file__).resolve().parent
REPO_ROOT = WEB_DIR.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    # Create working directories
    upload_dir = WEB_DIR / "uploads"
    output_dir = WEB_DIR / "output"
    upload_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # Create batch input directories
    for tool in ("videotr", "audiotr", "transtr"):
        (REPO_ROOT / tool / "input").mkdir(parents=True, exist_ok=True)

    # Initialize shared state
    app.state.settings = WebSettings()
    app.state.job_manager = JobManager()
    app.state.executor = ThreadPoolExecutor(max_workers=3)
    app.state.keystore = KeyStore()
    app.state.keystore.apply_to_env()
    app.state.templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
    app.state.upload_dir = upload_dir
    app.state.output_dir = output_dir

    yield

    # --- Shutdown ---
    app.state.executor.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Verba", lifespan=lifespan)

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    # Register routes
    from .routes.dashboard import router as dashboard_router
    from .routes.videotr_routes import router as videotr_router
    from .routes.audiotr_routes import router as audiotr_router
    from .routes.transtr_routes import router as transtr_router
    from .routes.settings_routes import router as settings_router

    app.include_router(dashboard_router)
    app.include_router(videotr_router, prefix="/videotr")
    app.include_router(audiotr_router, prefix="/audiotr")
    app.include_router(transtr_router, prefix="/transtr")
    app.include_router(settings_router, prefix="/settings")

    return app


app = create_app()
