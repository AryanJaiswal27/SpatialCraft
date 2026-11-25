import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ROOT_UPLOADS_DIR = ROOT_DIR / "uploads"
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
CROPS_DIR = STORAGE_DIR / "crops"
SCENES_DIR = STORAGE_DIR / "scenes"
STATIC_DIR = BASE_DIR / "static"
MODELS_DIR = STATIC_DIR / "models"
TUNNEL_URL_FILE = ROOT_DIR / "LATEST_TUNNEL_URL.txt"
FRONTEND_TUNNEL_FILE = ROOT_DIR / "frontend" / "public" / "tunnel_url.json"

# Ensure directories exist
for directory in [ROOT_UPLOADS_DIR, UPLOADS_DIR, CROPS_DIR, SCENES_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
