"""
Face Recognition Engine for Grabpic.
Handles face detection, encoding, and matching using DeepFace.
"""
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple

from app.config import FACE_MODEL, DETECTOR_BACKEND, MATCH_THRESHOLD

logger = logging.getLogger(__name__)


def detect_and_encode_faces(image_path: str) -> List[Dict]:
    """
    Detect faces in an image and return their encodings and bounding boxes.

    Args:
        image_path: Path to the image file.

    Returns:
        List of dicts, each with:
            - 'encoding': numpy array (128-d for Facenet)
            - 'bbox': dict with top, right, bottom, left coordinates
    """
    # Import here to avoid slow startup (model loading)
    from deepface import DeepFace

    try:
        representations = DeepFace.represent(
            img_path=image_path,
            model_name=FACE_MODEL,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=False
        )

        faces = []
        for rep in representations:
            embedding = np.array(rep["embedding"], dtype=np.float64)
            facial_area = rep["facial_area"]

            # Skip very low confidence detections
            if rep.get("face_confidence", 1.0) < 0.50:
                continue

            faces.append({
                "encoding": embedding,
                "bbox": {
                    "top": facial_area["y"],
                    "right": facial_area["x"] + facial_area["w"],
                    "bottom": facial_area["y"] + facial_area["h"],
                    "left": facial_area["x"]
                }
            })

        return faces

    except Exception as e:
        logger.error(f"Error detecting faces in {image_path}: {e}")
        return []


def cosine_distance(enc1: np.ndarray, enc2: np.ndarray) -> float:
    """Compute cosine distance between two face encodings."""
    dot = np.dot(enc1, enc2)
    norm1 = np.linalg.norm(enc1)
    norm2 = np.linalg.norm(enc2)
    if norm1 == 0 or norm2 == 0:
        return 1.0
    similarity = dot / (norm1 * norm2)
    return 1.0 - similarity


def find_matching_face(
    encoding: np.ndarray,
    known_faces: List[Tuple[str, np.ndarray]],
    threshold: float = MATCH_THRESHOLD
) -> Optional[Tuple[str, float]]:
    """
    Compare a face encoding against all known faces and return the best match.

    Args:
        encoding: The face encoding to match (128-d numpy array).
        known_faces: List of (grab_id, encoding) tuples from the database.
        threshold: Maximum cosine distance for a valid match.

    Returns:
        Tuple of (grab_id, confidence) if a match is found, None otherwise.
        Confidence is 1.0 - cosine_distance (higher is better).
    """
    if not known_faces:
        return None

    best_match_id = None
    best_distance = float("inf")

    for grab_id, known_encoding in known_faces:
        distance = cosine_distance(encoding, known_encoding)
        if distance < best_distance:
            best_distance = distance
            best_match_id = grab_id

    if best_distance <= threshold:
        confidence = round(1.0 - best_distance, 4)
        return (best_match_id, confidence)

    return None


def encoding_to_bytes(encoding: np.ndarray) -> bytes:
    """Serialize a numpy face encoding to bytes for database storage."""
    return encoding.astype(np.float64).tobytes()


def bytes_to_encoding(data: bytes) -> np.ndarray:
    """Deserialize bytes back to a numpy face encoding."""
    return np.frombuffer(data, dtype=np.float64)
