"""
Auth Router — Selfie Authentication endpoint.
Users upload a selfie to authenticate and receive their grab_id.
"""
import os
import uuid
import logging

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.config import TEMP_DIR, ALLOWED_EXTENSIONS
from app.database import get_db, Face, FaceImage
from app.face_engine import (
    detect_and_encode_faces,
    find_matching_face,
    bytes_to_encoding,
)
from app.schemas import AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Selfie Authentication"])


@router.post(
    "/selfie",
    response_model=AuthResponse,
    summary="Authenticate via selfie",
    description="Upload a selfie photo. The system extracts the face, compares it "
    "against all known identities, and returns the matching grab_id.",
)
async def selfie_auth(
    file: UploadFile = File(..., description="Selfie image for authentication"),
    db: Session = Depends(get_db),
):
    # Validate file type
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return AuthResponse(
            success=False,
            authenticated=False,
            message=f"Unsupported file type: {ext}. Supported: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save selfie to temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}{ext}")

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Detect faces in the selfie
        faces = detect_and_encode_faces(temp_path)

        if not faces:
            return AuthResponse(
                success=True,
                authenticated=False,
                message="No face detected in the uploaded image. Please upload a clear selfie with your face visible.",
            )

        # If multiple faces detected, use the largest one (most prominent)
        if len(faces) > 1:
            faces.sort(
                key=lambda f: (
                    (f["bbox"]["right"] - f["bbox"]["left"])
                    * (f["bbox"]["bottom"] - f["bbox"]["top"])
                ),
                reverse=True,
            )

        selfie_encoding = faces[0]["encoding"]

        # Load all known face encodings from DB
        known_faces_db = db.query(Face).all()
        known_faces = [(f.id, bytes_to_encoding(f.encoding)) for f in known_faces_db]

        if not known_faces:
            return AuthResponse(
                success=True,
                authenticated=False,
                message="No faces registered in the system yet. Please ingest images first.",
            )

        # Find the best match
        match = find_matching_face(selfie_encoding, known_faces)

        if match:
            grab_id, confidence = match
            # Count how many images this person appears in
            image_count = (
                db.query(FaceImage).filter(FaceImage.face_id == grab_id).count()
            )

            return AuthResponse(
                success=True,
                authenticated=True,
                grab_id=grab_id,
                confidence=confidence,
                total_images=image_count,
                message=f"Successfully authenticated. Found {image_count} image(s) for this identity.",
            )
        else:
            return AuthResponse(
                success=True,
                authenticated=False,
                message="Face not recognized. No matching identity found in the system.",
            )

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
