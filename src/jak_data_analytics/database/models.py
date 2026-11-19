"""
JAK Data Analytics
Database Models

Defines the main database tables for:

- Users
- Projects
- Datasets
- Analysis Jobs
- Saved Dashboards
- Reports
- Activity Logs
- Contact Messages

Uses SQLAlchemy ORM.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Float,
    JSON,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import relationship

from .connection import Base


# ==================================================
# USER MODEL
# ==================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    fullname = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    phone = Column(
        String(30),
        nullable=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(30),
        nullable=False,
        default="user",
        index=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="active",
        index=True
    )

    email_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )

    profile_picture = Column(
        String(500),
        nullable=True
    )

    location = Column(
        String(150),
        nullable=True
    )

    bio = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    last_login = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships

    projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    datasets = relationship(
        "Dataset",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    analysis_jobs = relationship(
        "AnalysisJob",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    dashboards = relationship(
        "SavedDashboard",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    reports = relationship(
        "Report",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    activities = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return (
            f"<User id={self.id} "
            f"email={self.email}>"
        )


# ==================================================
# PROJECT MODEL
# ==================================================

class Project(Base):

    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    category = Column(
        String(100),
        nullable=True
    )

    status = Column(
        String(30),
        default="active",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="projects"
    )

    datasets = relationship(
        "Dataset",
        back_populates="project"
    )

    __table_args__ = (
        Index(
            "ix_projects_user_name",
            "user_id",
            "name"
        ),
    )


# ==================================================
# DATASET MODEL
# ==================================================

class Dataset(Base):

    __tablename__ = "datasets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    original_filename = Column(
        String(255),
        nullable=True
    )

    file_path = Column(
        String(1000),
        nullable=True
    )

    file_format = Column(
        String(30),
        nullable=True
    )

    file_size = Column(
        Integer,
        default=0
    )

    row_count = Column(
        Integer,
        default=0
    )

    column_count = Column(
        Integer,
        default=0
    )

    quality_score = Column(
        Float,
        nullable=True
    )

    status = Column(
        String(30),
        default="uploaded",
        nullable=False,
        index=True
    )

    dataset_metadata = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="datasets"
    )

    project = relationship(
        "Project",
        back_populates="datasets"
    )

    analysis_jobs = relationship(
        "AnalysisJob",
        back_populates="dataset"
    )

    reports = relationship(
        "Report",
        back_populates="dataset"
    )

    __table_args__ = (
        Index(
            "ix_datasets_user_name",
            "user_id",
            "name"
        ),
    )


# ==================================================
# ANALYSIS JOB MODEL
# ==================================================

class AnalysisJob(Base):

    __tablename__ = "analysis_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    job_name = Column(
        String(200),
        nullable=False
    )

    analysis_type = Column(
        String(100),
        nullable=False,
        index=True
    )

    status = Column(
        String(30),
        default="pending",
        nullable=False,
        index=True
    )

    parameters = Column(
        JSON,
        nullable=True
    )

    results = Column(
        JSON,
        nullable=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="analysis_jobs"
    )

    dataset = relationship(
        "Dataset",
        back_populates="analysis_jobs"
    )


# ==================================================
# SAVED DASHBOARD MODEL
# ==================================================

class SavedDashboard(Base):

    __tablename__ = "saved_dashboards"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    layout_config = Column(
        JSON,
        nullable=True
    )

    is_favorite = Column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="dashboards"
    )


# ==================================================
# REPORT MODEL
# ==================================================

class Report(Base):

    __tablename__ = "reports"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    report_type = Column(
        String(100),
        nullable=True
    )

    file_path = Column(
        String(1000),
        nullable=True
    )

    file_format = Column(
        String(30),
        nullable=True
    )

    report_metadata = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="reports"
    )

    dataset = relationship(
        "Dataset",
        back_populates="reports"
    )


# ==================================================
# ACTIVITY LOG MODEL
# ==================================================

class ActivityLog(Base):

    __tablename__ = "activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    action = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    activity_metadata = Column(
        JSON,
        nullable=True
    )

    ip_address = Column(
        String(45),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="activities"
    )


# ==================================================
# CONTACT MESSAGE MODEL
# ==================================================

class ContactMessage(Base):

    __tablename__ = "contact_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    fullname = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=False,
        index=True
    )

    subject = Column(
        String(200),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    status = Column(
        String(30),
        default="unread",
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


# ==================================================
# DATABASE MODEL SUMMARY
# ==================================================

def get_model_names():

    return [
        table.name
        for table in Base.metadata.sorted_tables
    ]