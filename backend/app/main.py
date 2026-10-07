import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.api import health, projects, tasks, analysis, patches, verification, reports, history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codepilot")

# Ensure database tables exist immediately on import
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    safe_db_target = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    logger.info("[STARTUP] CodePilot backend initialized on http://127.0.0.1:8001")
    logger.info("[DATABASE] Database connected: %s", safe_db_target)
    yield
    logger.info("[SHUTDOWN] CodePilot backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Software Engineering Agent — PSI09",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount all API routers under /api
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(patches.router, prefix="/api", tags=["Patches"])
app.include_router(verification.router, prefix="/api", tags=["Verification"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(history.router, prefix="/api", tags=["History"])


@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }
