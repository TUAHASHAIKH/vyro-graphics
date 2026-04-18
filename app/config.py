"""
Grabpic Configuration
"""
import os

# Base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Storage for ingested images
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

# Temporary directory for selfie auth uploads
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# SQLite database path
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'grabpic.db')}"

# Supported image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Face recognition settings
FACE_MODEL = "Facenet"
DETECTOR_BACKEND = "opencv"
MATCH_THRESHOLD = 0.45  # cosine distance threshold for Facenet (tuned for varied angles)
