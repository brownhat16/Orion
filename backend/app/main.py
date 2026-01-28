"""
FastAPI Application Entry Point

Main application with CORS, routers, and lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import projects, generation, websocket, story_editor
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    print(f"🚀 Starting {settings.app_name}")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Production-grade multi-agent system for AI-powered novel writing",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
    redirect_slashes=False,  # Prevent 307 redirects
)

# CORS configuration - allow all origins for now (or specific ones)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://frontend-jzyeb6ril-nick1234s-projects.vercel.app",
        "https://*.vercel.app",  # Allow all Vercel preview URLs
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Regex for Vercel subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(generation.router, prefix="/api/generation", tags=["Generation"])
app.include_router(story_editor.router, prefix="/api/story-editor", tags=["Story Editor"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "debug": settings.debug,
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
