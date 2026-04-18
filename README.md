# 🎯 Grabpic — Intelligent Identity & Retrieval Engine

A high-performance image processing backend designed for large-scale events. Imagine a marathon with 500 runners and 50,000 photos — Grabpic uses **facial recognition** to automatically group images by identity and provides a **Selfie-as-a-Key** retrieval system.

## Judge Testing

For a quick evaluator flow, see [JUDGE_TESTING.md](JUDGE_TESTING.md).

For evaluation, please use sample images from the `test_images/` folder in this repository. These are the images used for the latest functional verification.

## Public Demo Links

- Swagger UI: https://mysimon-wet-basin-understood.trycloudflare.com/docs
- ReDoc: https://mysimon-wet-basin-understood.trycloudflare.com/redoc

Note: This is a quick Cloudflare Tunnel URL and works only while the local tunnel process is running.

## API Documentation

Detailed endpoint documentation is available in [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Server                     │
│                                                      │
│  POST /ingest ──→ Face Detection ──→ Assign grab_id │
│  POST /auth/selfie ──→ Face Match ──→ Return grab_id│
│  GET /images/{grab_id} ──→ Fetch user images         │
│                                                      │
├──────────────────────────────────────────────────────┤
│           DeepFace (Facenet Model)                    │
│     128-d face embeddings + cosine matching           │
├──────────────────────────────────────────────────────┤
│              SQLite + SQLAlchemy                      │
│   faces ←──→ face_images ←──→ images                 │
│          (many-to-many mapping)                       │
└──────────────────────────────────────────────────────┘
```

## Database Schema

| Table | Purpose |
|-------|---------|
| `faces` | Unique identities with `grab_id` (UUID) and 128-d face encoding |
| `images` | Ingested image metadata (filename, path, dimensions) |
| `face_images` | Many-to-many junction: maps faces ↔ images with bounding box |

## Setup & Run

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd grabpic

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**Swagger Docs**: `http://localhost:8000/docs`
**ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Ingest Images (Upload)
Upload one image for face discovery per request:
```bash
# Single image
curl -X POST http://localhost:8000/ingest \
  -F "file=@photo1.jpg"
```

To ingest multiple files, call `/ingest` multiple times or use `/ingest/crawl`.

**Response:**
```json
{
  "success": true,
  "images_processed": 1,
  "faces_discovered": 1,
  "new_grab_ids_created": 1,
  "existing_grab_ids_matched": 0,
  "details": [...]
}
```

### 3. Ingest Images (Crawl Directory)
Crawl a folder to ingest all images:
```bash
curl -X POST http://localhost:8000/ingest/crawl \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "./storage/marathon_photos"}'
```

### 4. Selfie Authentication
Upload a selfie to get your `grab_id`:
```bash
curl -X POST http://localhost:8000/auth/selfie \
  -F "file=@my_selfie.jpg"
```

**Response:**
```json
{
  "success": true,
  "authenticated": true,
  "grab_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "confidence": 0.87,
  "total_images": 12,
  "message": "Successfully authenticated. Found 12 image(s) for this identity."
}
```

### 5. Get Images by Identity
Fetch all images for a person:
```bash
curl http://localhost:8000/images/{grab_id}
```

**Response:**
```json
{
  "success": true,
  "grab_id": "a1b2c3d4-...",
  "total_images": 12,
  "images": [
    {
      "image_id": "...",
      "filename": "IMG_001.jpg",
      "url": "/image/.../file",
      "width": 1920,
      "height": 1080
    }
  ]
}
```

### 6. Download Image File
```bash
curl http://localhost:8000/image/{image_id}/file --output photo.jpg
```

### 7. List All Known Identities
```bash
curl http://localhost:8000/faces
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI (Python) |
| Face Recognition | DeepFace (Facenet model) |
| Database | SQLite + SQLAlchemy ORM |
| Face Matching | Cosine distance on 128-d embeddings |
| Docs | Auto-generated Swagger & ReDoc |

## Key Design Decisions

- **Facenet model**: 128-dimensional embeddings offer good balance of speed and accuracy
- **Cosine distance** with threshold 0.45 for face matching
- **Many-to-many schema**: `face_images` junction table allows one image → many faces and one face → many images
- **UUID-based grab_ids**: Unique, collision-resistant identifiers
- **Lazy model loading**: DeepFace model loaded on first request to speed up startup
# vyro-graphics
