from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import pymongo.errors

from src.config import settings
# Import routers
from src.auth.router import router as auth_router
from src.posts.router import router as posts_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(pymongo.errors.PyMongoError)
async def pymongo_exception_handler(request: Request, exc: pymongo.errors.PyMongoError):
    error_msg = str(exc)
    hint = "Please configure your actual database credentials (e.g. replacing '<db_password>') in your .env file."
    if "bad auth" in error_msg.lower() or "authentication failed" in error_msg.lower():
         return JSONResponse(
             status_code=503,
             content={"detail": "Database authentication failed.", "hint": hint, "error": error_msg}
         )
    return JSONResponse(
        status_code=500,
        content={"detail": "Database connection or execution failed.", "error": error_msg}
    )

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 templates directory
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def read_root(request: Request):
    """
    Serves the landing dashboard template.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "api_prefix": settings.API_PREFIX
        }
    )


@app.get("/health", tags=["health"])
async def health_check():
    """
    Liveness and readiness probe endpoint.
    Crucial for GCP Cloud Run and container orchestration.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }

# Include routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(posts_router, prefix=settings.API_PREFIX)
