# Grabpic Judge Testing Guide

Use this guide to quickly verify the API during judging.

## Live URLs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Test Images For Judges

Please use images from the `test_images/` folder in this repository.
These are the same files used for the latest short-window validation before submission.

## What to Test First

1. Open Swagger UI at `/docs`.
2. Run `GET /health`.
3. Ingest one or more test images.
4. Test selfie authentication with a matching face.
5. Fetch images using the returned `grab_id`.
6. Review identity listing with `GET /faces`.

## Recommended Test Flow

### 1. Health Check

Endpoint: `GET /health`

Expected result:

- `status: "healthy"`
- `service: "grabpic"`

### 2. Ingest Images

Endpoint: `POST /ingest`

In Swagger:

- Click `Try it out`
- Upload one single-face image first
- Upload one multi-face image next (run the endpoint again)

Expected result:

- `success: true`
- `images_processed` should be `1` per request
- `faces_discovered` reflects detected faces
- `details` contains one entry per uploaded file
- Each face should map to a `grab_id`

### 3. Selfie Authentication

Endpoint: `POST /auth/selfie`

Upload a clear selfie of a face that was already ingested.

Expected result:

- `authenticated: true`
- `grab_id` returned for the matched identity
- `total_images` shows how many images contain that face
- `confidence` should be present when a match is found

If the face is unknown:

- `authenticated: false`

### 4. Retrieve Images by Identity

Endpoint: `GET /images/{grab_id}`

Use the `grab_id` returned from `/auth/selfie` or `/faces`.

Expected result:

- `success: true`
- `grab_id` matches the requested identity
- `total_images` lists all linked images
- Each item includes `image_id`, `filename`, and `url`

### 5. List All Known Faces

Endpoint: `GET /faces`

Expected result:

- `success: true`
- `total_faces` shows how many identities were discovered
- Each face includes a `grab_id` and `image_count`

### 6. Serve an Image File

Endpoint: `GET /image/{image_id}/file`

Use an `image_id` from the `/images/{grab_id}` response.

Expected result:

- The raw image file downloads or opens in the browser

## Suggested Judge Checklist

- Confirm the API loads in Swagger and ReDoc.
- Confirm at least one face becomes a `grab_id` after ingestion.
- Confirm one image can contain multiple faces.
- Confirm selfie authentication returns the same `grab_id` for a matching face.
- Confirm retrieval by `grab_id` returns the correct image set.

## Quick cURL Examples

Health:

```bash
curl http://localhost:8000/health
```

Ingest a single image:

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@path/to/image.jpg"
```

Ingest multiple images:

```bash
# Run one request per file
curl -X POST http://localhost:8000/ingest \
  -F "file=@path/to/image1.jpg"

curl -X POST http://localhost:8000/ingest \
  -F "file=@path/to/image2.jpg"
```

Selfie auth:

```bash
curl -X POST http://localhost:8000/auth/selfie \
  -F "file=@path/to/selfie.jpg"
```

Retrieve by identity:

```bash
curl http://localhost:8000/images/{grab_id}
```

List all faces:

```bash
curl http://localhost:8000/faces
```

Download one image:

```bash
curl http://localhost:8000/image/{image_id}/file --output photo.jpg
```

## Notes For Judges

- Swagger UI is the best place to submit file uploads.
- ReDoc is best for reviewing schemas and endpoint contracts.
- The main demo path is: ingest -> selfie auth -> retrieve images.
- If no face is detected in an upload, the API should return a clear message instead of failing.