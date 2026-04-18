"""
Database models and session management for Grabpic.
Uses SQLAlchemy ORM with SQLite backend.
"""
import datetime
from sqlalchemy import (
    create_engine, Column, String, LargeBinary,
    Integer, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Face(Base):
    """
    Represents a unique face identity.
    Each face gets a unique grab_id (UUID) and stores its 128-d encoding.
    """
    __tablename__ = "faces"

    id = Column(String, primary_key=True)              # grab_id (UUID)
    encoding = Column(LargeBinary, nullable=False)      # numpy array as bytes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to images through junction table
    images = relationship("Image", secondary="face_images", back_populates="faces")


class Image(Base):
    """
    Represents an ingested image file.
    """
    __tablename__ = "images"

    id = Column(String, primary_key=True)               # image_id (UUID)
    filename = Column(String, nullable=False)            # original filename
    filepath = Column(String, nullable=False)            # full path on disk
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationship to faces through junction table
    faces = relationship("Face", secondary="face_images", back_populates="images")


class FaceImage(Base):
    """
    Junction table mapping faces to images (many-to-many).
    One image can contain multiple faces, and one face can appear in multiple images.
    Also stores the bounding box of the face within the image.
    """
    __tablename__ = "face_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    face_id = Column(String, ForeignKey("faces.id"), nullable=False)
    image_id = Column(String, ForeignKey("images.id"), nullable=False)
    bbox_top = Column(Integer)
    bbox_right = Column(Integer)
    bbox_bottom = Column(Integer)
    bbox_left = Column(Integer)

    __table_args__ = (
        UniqueConstraint("face_id", "image_id", name="uq_face_image"),
    )


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
