"""
Ingest Router — Discovery & Transformation endpoints.
Handles image upload and directory crawling for face detection and indexing.
"""
import os
import uuid
import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from PIL import Image as PILImage

from app.config import STORAGE_DIR, ALLOWED_EXTENSIONS
from app.database import get_db, Face, Image, FaceImage
from app.face_engine import (
    detect_and_encode_faces,
    find_matching_face,
    encoding_to_bytes,
    bytes_to_encoding,
)
from app.schemas import IngestResponse, IngestImageDetail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Discovery & Transformation"])


def _get_known_faces(db: Session):
    """Load all known face encodings from the database."""
    faces = db.query(Face).all()
    return [(f.id, bytes_to_encoding(f.encoding)) for f in faces]


def _process_image(
    image_path: str, filename: str, db: Session, known_faces: list
) -> IngestImageDetail:
    """
    Process a single image:
    1. Detect all faces
    2. Match each face to existing grab_id or create new one
    3. Create image record and face-image mappings
    """
    # Check if already processed
    existing = db.query(Image).filter(Image.filepath == image_path).first()
    if existing:
        return IngestImageDetail(
            filename=filename,
            image_id=existing.id,
            status="already_processed",
        )

    # Get image dimensions
    try:
        with PILImage.open(image_path) as img:
            width, height = img.size
    except Exception:
        width, height = None, None

    # Detect faces
    detected_faces = detect_and_encode_faces(image_path)

    if not detected_faces:
        # Still store image record so it's not reprocessed
        image_id = str(uuid.uuid4())
        image_record = Image(
            id=image_id,
            filename=filename,
            filepath=image_path,
            width=width,
            height=height,
        )
        db.add(image_record)
        return IngestImageDetail(
            filename=filename,
            image_id=image_id,
            faces_found=0,
            grab_ids=[],
            status="no_faces_detected",
        )

    # Create image record
    image_id = str(uuid.uuid4())
    image_record = Image(
        id=image_id,
        filename=filename,
        filepath=image_path,
        width=width,
        height=height,
    )
    db.add(image_record)

    result_grab_ids = []
    new_ids = 0
    matched_ids = 0

    for face_data in detected_faces:
        encoding = face_data["encoding"]
        bbox = face_data["bbox"]

        # Try to match against known faces
        match = find_matching_face(encoding, known_faces)

        if match:
            grab_id, confidence = match
            matched_ids += 1
        else:
            # Create new unique identity
            grab_id = str(uuid.uuid4())
            face_record = Face(
                id=grab_id,
                encoding=encoding_to_bytes(encoding),
            )
            db.add(face_record)
            # Add to in-memory list for subsequent matches in this batch
            known_faces.append((grab_id, encoding))
            new_ids += 1

        # Check for duplicate face-image mapping
        exists = (
            db.query(FaceImage)
            .filter(FaceImage.face_id == grab_id, FaceImage.image_id == image_id)
            .first()
        )
        if not exists:
            face_image = FaceImage(
                face_id=grab_id,
                image_id=image_id,
                bbox_top=bbox["top"],
                bbox_right=bbox["right"],
                bbox_bottom=bbox["bottom"],
                bbox_left=bbox["left"],
            )
            db.add(face_image)

        result_grab_ids.append(grab_id)

    return IngestImageDetail(
        filename=filename,
        image_id=image_id,
        faces_found=len(detected_faces),
        grab_ids=result_grab_ids,
        new_ids=new_ids,
        matched_ids=matched_ids,
        status="processed",
    )


@router.post(
    "",
    response_model=IngestResponse,
    summary="Upload and ingest images",
    description="Upload one or more images for face discovery and indexing. "
    "Each image is scanned for faces, and each unique face is assigned a grab_id.",
)
async def ingest_images(
    files: List[UploadFile] = File(..., description="Image files to process"),
    db: Session = Depends(get_db),
):
    known_faces = _get_known_faces(db)

    total_faces = 0
    total_new = 0
    total_matched = 0
    details = []
    images_processed = 0

    for file in files:
        # Validate file extension
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            details.append(
                IngestImageDetail(
                    filename=file.filename or "unknown",
                    status="skipped",
                    reason=f"Unsupported file type: {ext}",
                )
            )
            continue

        # Save to storage directory
        os.makedirs(STORAGE_DIR, exist_ok=True)
        save_filename = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(STORAGE_DIR, save_filename)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # Process the image
        result = _process_image(save_path, file.filename or save_filename, db, known_faces)
        details.append(result)
        images_processed += 1
        total_faces += result.faces_found
        total_new += result.new_ids
        total_matched += result.matched_ids

    db.commit()

    return IngestResponse(
        success=True,
        images_processed=images_processed,
        faces_discovered=total_faces,
        new_grab_ids_created=total_new,
        existing_grab_ids_matched=total_matched,
        details=details,
    )


@router.post(
    "/crawl",
    response_model=IngestResponse,
    summary="Crawl a directory for images",
    description="Recursively scan a directory for image files and process each one for face detection.",
)
async def crawl_directory(
    folder_path: str = Body(..., embed=True, description="Path to image directory"),
    db: Session = Depends(get_db),
):
    if not os.path.isdir(folder_path):
        raise HTTPException(
            status_code=400,
            detail=f"Directory not found: {folder_path}",
        )

    known_faces = _get_known_faces(db)

    total_faces = 0
    total_new = 0
    total_matched = 0
    details = []
    images_processed = 0

    for root, dirs, files_list in os.walk(folder_path):
        for filename in files_list:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            file_path = os.path.join(root, filename)
            result = _process_image(file_path, filename, db, known_faces)
            details.append(result)
            images_processed += 1
            total_faces += result.faces_found
            total_new += result.new_ids
            total_matched += result.matched_ids

    db.commit()

    return IngestResponse(
        success=True,
        images_processed=images_processed,
        faces_discovered=total_faces,
        new_grab_ids_created=total_new,
        existing_grab_ids_matched=total_matched,
        details=details,
    )
