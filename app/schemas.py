"""
Pydantic response schemas for Grabpic API endpoints.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ─── Ingest Responses ───────────────────────────────────────────────

class IngestImageDetail(BaseModel):
    """Detail info for a single processed image."""
    filename: str
    image_id: Optional[str] = None
    faces_found: int = 0
    grab_ids: List[str] = []
    new_ids: int = 0
    matched_ids: int = 0
    status: str  # "processed", "no_faces_detected", "skipped", "already_processed"
    reason: Optional[str] = None


class IngestResponse(BaseModel):
    """Response from image ingestion endpoints."""
    success: bool
    images_processed: int
    faces_discovered: int
    new_grab_ids_created: int
    existing_grab_ids_matched: int
    details: List[IngestImageDetail]


# ─── Auth Responses ─────────────────────────────────────────────────

class AuthResponse(BaseModel):
    """Response from selfie authentication."""
    success: bool
    authenticated: bool
    grab_id: Optional[str] = None
    confidence: Optional[float] = None
    total_images: Optional[int] = None
    message: str


# ─── Image & Face Retrieval ─────────────────────────────────────────

class ImageInfo(BaseModel):
    """Information about a single image."""
    image_id: str
    filename: str
    url: str
    width: Optional[int] = None
    height: Optional[int] = None
    ingested_at: datetime

    class Config:
        from_attributes = True


class ImagesResponse(BaseModel):
    """Response when fetching images for a grab_id."""
    success: bool
    grab_id: str
    total_images: int
    images: List[ImageInfo]


class FaceInfo(BaseModel):
    """Summary info for a known face identity."""
    grab_id: str
    image_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class FacesListResponse(BaseModel):
    """Response when listing all known face identities."""
    success: bool
    total_faces: int
    faces: List[FaceInfo]


# ─── Error Response ─────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    detail: str
