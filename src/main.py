from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import pymongo.errors
import asyncio
import threading
import json
import time
from datetime import datetime, timezone
from typing import List

from src.config import settings
# Import routers
from src.auth.router import router as auth_router
from src.devices.router import router as devices_router
from src.telemetry.router import router as telemetry_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()


@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def start_pubsub_listener():
    # Attempt to load GCP configuration
    try:
        from src.gcp.client import gcp_client
        from src.gcp import config
        from google.cloud import pubsub_v1
    except Exception as e:
        print(f"GCP SDK imports failed: {e}")
        gcp_client = None

    # Callback when a message is received
    def callback(message):
        try:
            payload_str = message.data.decode('utf-8')
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.broadcast(payload_str))
            loop.close()
        except Exception as e:
            print(f"Error in pubsub broadcast callback: {e}")
        message.ack()

    # If GCP is configured, run client
    if gcp_client and gcp_client.credentials and getattr(config, 'PROJECT_ID', None):
        try:
            subscriber = pubsub_v1.SubscriberClient(credentials=gcp_client.credentials)
            subscription_path = subscriber.subscription_path(config.PROJECT_ID, "digital_twin_sub")
            streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
            print(f"Pub/Sub Background Listener started on: {subscription_path}")
            streaming_pull_future.result()
        except Exception as e:
            print(f"Failed to start GCP PubSub subscriber: {e}")
    else:
        print("GCP Pub/Sub credentials not found or unconfigured. Background Listener stopped.")


@app.on_event("startup")
async def startup_event():
    # Start the subscriber loop in a background daemon thread
    thread = threading.Thread(target=start_pubsub_listener, daemon=True)
    thread.start()


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
app.include_router(devices_router, prefix=settings.API_PREFIX)
app.include_router(telemetry_router, prefix=settings.API_PREFIX)

