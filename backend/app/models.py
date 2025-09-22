import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, Float
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .user_roles import UserRole
from .project_roles import ProjectRole

Base = declarative_base()

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole), nullable=False, default=ProjectRole.VIEWER)
    user: Mapped["User"] = relationship(back_populates="project_associations")
    project: Mapped["Project"] = relationship(back_populates="member_associations")

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.FREE_USER, server_default=UserRole.FREE_USER.value, nullable=False
    )
    subscription_tier: Mapped[str] = mapped_column(String, default="free", server_default="free")
    status: Mapped[str] = mapped_column(String, default="active", server_default="active")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    
    # --- NEW FIELD ADDED HERE ---
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    project_associations: Mapped[List["ProjectMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    member_associations: Mapped[List["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    code_snippets: Mapped[List["CodeSnippet"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )



class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code_snippet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("code_snippets.id"))
    status: Mapped[str] = mapped_column(String, index=True, default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    progress_stage: Mapped[Optional[str]] = mapped_column(String)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    code_snippet: Mapped["CodeSnippet"] = relationship(back_populates="reviews")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="password_reset_tokens")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    device_info: Mapped[Optional[str]] = mapped_column(String)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column()
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# alembic revision --autogenerate -m "Add preferences column to users table"

# alembic upgrade head




# ... (ProjectMember, User, Project models remain the same) ...

class CodeSnippet(Base):
    __tablename__ = "code_snippets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    filename: Mapped[Optional[str]] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String, index=True)
    hash: Mapped[str] = mapped_column(String, unique=True, index=True) # Original hash
    file_size: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # --- NEW COLUMNS FOR METRICS ---
    loc: Mapped[Optional[int]] = mapped_column(Integer) # Lines of Code
    cyclomatic_complexity: Mapped[Optional[int]] = mapped_column(Integer)
    normalized_hash: Mapped[Optional[str]] = mapped_column(String, index=True)
    detected_language: Mapped[Optional[str]] = mapped_column(String)
    # --- END OF NEW COLUMNS ---

    project: Mapped["Project"] = relationship(back_populates="code_snippets")
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="code_snippet", cascade="all, delete-orphan"
    )
