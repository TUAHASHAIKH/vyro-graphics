# Grabpic API Documentation

Base URL (local): http://localhost:8000

Public demo (Cloudflare Tunnel):

- Swagger UI: https://mysimon-wet-basin-understood.trycloudflare.com/docs
- ReDoc: https://mysimon-wet-basin-understood.trycloudflare.com/redoc

## Overview

Grabpic provides three main workflows:

1. Discovery and transformation via image ingestion
2. Selfie authentication via face matching
3. Data extraction via image retrieval by identity

## Recommended Test Data

For reproducible judge testing, use the sample files in the `test_images/` folder.
These files were used for the latest verification pass of ingest, auth, and retrieval flows.

## Authentication

No token-based authentication is required for these hackathon endpoints.

## Response Pattern

Most endpoints return JSON with a `success` flag and endpoint-specific fields.

## Endpoints

### 1. Health Check

Method: `GET`

Path: `/health`

Purpose: Verify service availability.

Sample response:

```json
{
  "status": "healthy",
  "service": "grabpic"
}
```

### 2. Root Metadata

Method: `GET`

Path: `/`

Purpose: Returns service metadata and endpoint summary.

### 3. Ingest Single Image

Method: `POST`

Path: `/ingest`

Content-Type: `multipart/form-data`

Form fields:

- `file` (required): image file (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`)

Purpose:

- Detect all faces in one uploaded image
- Match to existing identities or create new `grab_id` values
- Store image metadata and face-image mappings

Sample cURL:

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@photo.jpg"
```

Sample response:

```json
{
  "success": true,
  "images_processed": 1,
  "faces_discovered": 3,
  "new_grab_ids_created": 1,
  "existing_grab_ids_matched": 2,
  "details": [
    {
      "filename": "group_photo.jpg",
      "image_id": "uuid",
      "faces_found": 3,
      "grab_ids": ["uuid1", "uuid2", "uuid3"],
      "new_ids": 1,
      "matched_ids": 2,
      "status": "processed",
      "reason": null
    }
  ]
}
```

Notes:

- `images_processed` is `1` per request for `/ingest`.
- To process many files, call `/ingest` repeatedly or use `/ingest/crawl`.

### 4. Crawl Directory for Images

Method: `POST`

Path: `/ingest/crawl`

Content-Type: `application/json`

Body:

```json
{
  "folder_path": "./storage/marathon_photos"
}
```

Purpose: Recursively ingest all supported images from a directory.

Sample cURL:

```bash
curl -X POST http://localhost:8000/ingest/crawl \
  -H "Content-Type: application/json" \
  -d '{"folder_path":"./storage/marathon_photos"}'
```

### 5. Selfie Authentication

Method: `POST`

Path: `/auth/selfie`

Content-Type: `multipart/form-data`

Form fields:

- `file` (required): selfie image

Purpose:

- Encode the selfie face
- Compare with known face encodings
- Return matching `grab_id` when found

Sample cURL:

```bash
curl -X POST http://localhost:8000/auth/selfie \
  -F "file=@selfie.jpg"
```

Sample success response:

```json
{
  "success": true,
  "authenticated": true,
  "grab_id": "uuid",
  "confidence": 0.87,
  "total_images": 4,
  "message": "Successfully authenticated. Found 4 image(s) for this identity."
}
```

Sample non-match response:

```json
{
  "success": true,
  "authenticated": false,
  "grab_id": null,
  "confidence": null,
  "total_images": null,
  "message": "Face not recognized. No matching identity found in the system."
}
```

### 6. Get Images by Identity

Method: `GET`

Path: `/images/{grab_id}`

Path params:

- `grab_id` (required): identity UUID

Purpose: Return all ingested images containing the given identity.

Sample cURL:

```bash
curl http://localhost:8000/images/{grab_id}
```

Sample response:

```json
{
  "success": true,
  "grab_id": "uuid",
  "total_images": 4,
  "images": [
    {
      "image_id": "uuid",
      "filename": "person1_a.jpg",
      "url": "/image/uuid/file",
      "width": 128,
      "height": 128,
      "ingested_at": "2026-04-18T06:17:11.359927"
    }
  ]
}
```

### 7. Serve Image File

Method: `GET`

Path: `/image/{image_id}/file`

Path params:

- `image_id` (required): image UUID

Purpose: Return the raw image file from storage.

Sample cURL:

```bash
curl http://localhost:8000/image/{image_id}/file --output photo.jpg
```

### 8. List All Faces

Method: `GET`

Path: `/faces`

Purpose: List all discovered identities with image counts.

Sample cURL:

```bash
curl http://localhost:8000/faces
```

Sample response:

```json
{
  "success": true,
  "total_faces": 3,
  "faces": [
    {
      "grab_id": "uuid",
      "image_count": 4,
      "created_at": "2026-04-18T06:17:11.359927"
    }
  ]
}
```

## Common Error Cases

- `400` on `/ingest/crawl` when directory does not exist
- `404` on `/images/{grab_id}` when identity is missing
- `404` on `/image/{image_id}/file` when image or file path is missing
- `422` when request body format is invalid
- `500` for unexpected server errors

## Testing Sequence

Recommended end-to-end test flow:

1. `GET /health`
2. `POST /ingest` with a known image
3. `POST /auth/selfie` with a matching selfie
4. `GET /images/{grab_id}`
5. `GET /image/{image_id}/file`
6. `GET /faces`