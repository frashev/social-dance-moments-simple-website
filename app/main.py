from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from .auth import router as auth_router
from .recommend import router as recommend_router
from .workshops import router as workshops_router
from .events import router as events_router
from .admin import router as admin_router
from .dance_sequences import router as dance_sequences_router
from .database import init_db

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Social Dance Moments",
    description="A platform for discovering latin dance events & workshops",
    version="3.0.0"
)

# Initialize database on startup
init_db()


# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers FIRST (must come before static files)
app.include_router(auth_router)
app.include_router(recommend_router)
app.include_router(workshops_router)
app.include_router(events_router)
app.include_router(admin_router)
app.include_router(dance_sequences_router)

# Serve uploads directory
uploads_path = Path(__file__).parent.parent / "frontend" / "uploads"
uploads_path.mkdir(exist_ok=True)
if uploads_path.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Serve static files (frontend) - LAST so it doesn't override API routes
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

