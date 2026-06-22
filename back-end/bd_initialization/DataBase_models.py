import os
from sqlalchemy import INTEGER, JSON, TEXT, Column, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from dotenv import load_dotenv
load_dotenv()
# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

# Retrieve database credentials from environment variables
# Note: Check the spelling of "POSTGRESS_LINK" in your .env file if connection fails
db_url = os.getenv("DB_URL")

# Create database engine and session factory
engine = create_engine(url=db_url)
session_local = sessionmaker(bind=engine, autoflush=False)

# Declarative base class for ORM models
Base = declarative_base()


# ==============================================================================
# ORM MODELS (TABLES)
# ==============================================================================

class Worker(Base):
    """
    Model representing an employee / worker.
    Manages personal details, roles, face recognition images,
    and relationships with the assigned administrator and attendances.
    """
    __tablename__ = "worker"

    # Columns
    id = Column(INTEGER, primary_key=True, nullable=False, autoincrement=True)
    last_name = Column(TEXT, nullable=False)
    first_name = Column(TEXT, nullable=False)
    phone_number = Column(TEXT, nullable=False)
    address = Column(TEXT, nullable=False)
    role = Column(TEXT, nullable=False)
    age = Column(TEXT, nullable=False)       # Stored as TEXT (Consider INTEGER for numeric filtering)
    gender = Column(TEXT, nullable=False)
    status = Column(TEXT, nullable=True)
    admin_id = Column(INTEGER, ForeignKey("admin.id"))
    face_image_path = Column(TEXT, nullable=True)

    # Relationships
    # One worker can have multiple attendance records (One-to-Many)
    attendances = relationship(
        "Attendance",
        back_populates="worker",
        foreign_keys="Attendance.worker_id",
    )
    # A worker is assigned to a single administrator (Many-to-One)
    admin = relationship(
        "Admin", 
        back_populates="workers", 
        foreign_keys=[admin_id]
    )


class Admin(Base):
    """
    Model representing an Administrator (Admin).
    Has management rights over workers and supervises incidents.
    """
    __tablename__ = "admin"

    # Columns
    id = Column(INTEGER, primary_key=True, nullable=False, autoincrement=True)
    email = Column(TEXT, nullable=False, unique=True)
    last_name = Column(TEXT, nullable=False)
    first_name = Column(TEXT, nullable=False)
    phone_number = Column(TEXT, nullable=False)
    address = Column(TEXT, nullable=False)
    age = Column(TEXT, nullable=False)
    password = Column(TEXT, nullable=False)  # Stores the hashed password

    # Relationships
    # An admin can supervise multiple incidents (One-to-Many)
    incidents = relationship(
        "Incident", 
        back_populates="admin", 
        foreign_keys="Incident.admin_id"
    )
    # An admin can manage multiple workers (One-to-Many)
    workers = relationship(
        "Worker", 
        back_populates="admin", 
        foreign_keys="Worker.admin_id"
    )


class Incident(Base):
    """
    Model representing an Incident detected via video analysis.
    Contains file paths for videos and detection logs (Fire, PPE) in JSON format.
    """
    __tablename__ = "incident"

    # Columns
    id = Column(INTEGER, primary_key=True, nullable=False, autoincrement=True)
    original_video_path = Column(TEXT, nullable=True)
    analyzed_video_path = Column(TEXT, nullable=False)
    admin_id = Column(INTEGER, ForeignKey("admin.id"), nullable=False)
    date = Column(TEXT, nullable=False)
    fire_detections = Column(JSON, nullable=False)  # Fire detection logs
    ppe_detections = Column(JSON, nullable=False)   # Personal Protective Equipment logs

    # Relationships
    # The incident is linked to the managing administrator (Many-to-One)
    admin = relationship(
        "Admin", 
        back_populates="incidents", 
        foreign_keys=[admin_id]
    )


class Attendance(Base):
    """
    Model representing the attendance log of a worker.
    Records the date, check-in time, and status (e.g., Present, Late).
    """
    __tablename__ = "attendance"

    # Columns
    id = Column(INTEGER, primary_key=True, nullable=False, autoincrement=True)
    date = Column(TEXT, nullable=False)
    worker_id = Column(INTEGER, ForeignKey("worker.id"))
    check_in_time = Column(TEXT, nullable=True)
    status = Column(TEXT, nullable=False)

    # Relationships
    # The attendance record belongs to a specific worker (Many-to-One)
    worker = relationship(
        "Worker", 
        back_populates="attendances", 
        foreign_keys=[worker_id]
    )


# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

# Generate all tables in the database if they do not exist
Base.metadata.create_all(bind=engine)