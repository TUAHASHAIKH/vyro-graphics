"""
Images Router — Data Extraction endpoints.
Fetch images by grab_id and list all known identities.
"""
import os
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, Face, Image, FaceImage
from app.schemas import ImagesResponse, ImageInfo, FacesListResponse, FaceInfo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Data Extraction"])


@router.get(
    "/images/{grab_id}",
    response_model=ImagesResponse,
    summary="Get all images for a person",
    description="Retrieve all images containing the person identified by the given grab_id.",
)
async def get_images_by_grab_id(
    grab_id: str,
    db: Session = Depends(get_db),
):
    # Verify grab_id exists
    face = db.query(Face).filter(Face.id == grab_id).first()
    if not face:
        raise HTTPException(
            status_code=404,
            detail=f"Identity with grab_id '{grab_id}' not found.",
        )

    # Get all images linked to this grab_id
    face_images = (
        db.query(Image)
        .join(FaceImage, Image.id == FaceImage.image_id)
        .filter(FaceImage.face_id == grab_id)
        .all()
    )

    images = [
        ImageInfo(
            image_id=img.id,
            filename=img.filename,
            url=f"/image/{img.id}/file",
            width=img.width,
            height=img.height,
            ingested_at=img.ingested_at,
        )
        for img in face_images
    ]

    return ImagesResponse(
        success=True,
        grab_id=grab_id,
        total_images=len(images),
        images=images,
    )


@router.get(
    "/image/{image_id}/file",
    summary="Download an image file",
    description="Serve the actual image file for a given image_id.",
)
async def serve_image_file(
    image_id: str,
    db: Session = Depends(get_db),
):
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found.")

    if not os.path.exists(image.filepath):
        raise HTTPException(status_code=404, detail="Image file not found on disk.")

    # Determine media type from file extension
    ext = os.path.splitext(image.filepath)[1].lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(
        path=image.filepath,
        filename=image.filename,
        media_type=media_type,
    )


@router.get(
    "/faces",
    response_model=FacesListResponse,
    summary="List all known identities",
    description="List all discovered face identities (grab_ids) along with their image counts.",
)
async def list_faces(db: Session = Depends(get_db)):
    results = (
        db.query(Face, func.count(FaceImage.image_id).label("image_count"))
        .outerjoin(FaceImage, Face.id == FaceImage.face_id)
        .group_by(Face.id)
        .all()
    )

    faces = [
        FaceInfo(
            grab_id=face.id,
            image_count=count,
            created_at=face.created_at,
        )
        for face, count in results
    ]

    return FacesListResponse(
        success=True,
        total_faces=len(faces),
        faces=faces,
    )
