from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
from .auth import router as auth_router
from .recommend import router as recommend_router
from .workshops import router as workshops_router
from .admin import router as admin_router
from .database import init_db
from .geocoding import get_workshop_coordinates, WORKSHOP_GEOCODING_CACHE

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dance Song Recommender",
    description="A platform for discovering dance songs and workshops",
    version="3.0.0"
)

# Initialize database on startup
init_db()

# Pre-cache all workshop coordinates to prevent API hangs
def precache_workshops():
    """Pre-load all workshop coordinates into cache."""
    try:
        from .database import get_db
        with get_db() as conn:
            c = conn.cursor()
            c.execute('SELECT DISTINCT location, city FROM workshops ORDER BY city, location')
            locations = c.fetchall()

        logger.info(f"🔄 Pre-caching {len(locations)} workshop coordinates...")
        for location, city in locations:
            get_workshop_coordinates(location, city)

        logger.info(f"✅ Pre-caching complete! {len(WORKSHOP_GEOCODING_CACHE)} coordinates cached")
    except Exception as e:
        logger.warning(f"⚠️  Pre-caching failed: {e}")

precache_workshops()

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
app.include_router(admin_router)

@app.get("/api/home/{user_id}")
def home(user_id: int):
    """User home page (placeholder)."""
    return {"msg": f"Welcome user {user_id}! Visit /songs/{user_id} or /workshops."}

# Serve static files (frontend) - LAST so it doesn't override API routes
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

