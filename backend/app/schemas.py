from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid
from typing import Optional, List, Dict, Any

from .user_roles import UserRole
from .project_roles import ProjectRole

# ======================================================================================
# User Schemas (Shared)
# ======================================================================================
class UserBasicInfo(BaseModel):
    id: uuid.UUID
    email: EmailStr
    class Config: from_attributes = True

# ======================================================================================
# Project Member Schemas
# ======================================================================================
class ProjectMemberRead(BaseModel):
    user: UserBasicInfo
    role: ProjectRole
    class Config: from_attributes = True

class ProjectMemberInvite(BaseModel):
    email: EmailStr
    role: ProjectRole = Field(default=ProjectRole.VIEWER)

class ProjectMemberUpdate(BaseModel):
    role: ProjectRole

# ======================================================================================
# Project Schemas
# ======================================================================================
class ProjectSettings(BaseModel):
    default_review_branch: str = "main"
    auto_scan_on_commit: bool = False

class ProjectStats(BaseModel):
    member_count: int
    snippet_count: int
    review_count: int

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None

class ProjectCreateFromTemplate(BaseModel):
    template_project_id: uuid.UUID
    new_project_name: str = Field(..., min_length=3, max_length=100)

class ProjectRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    settings: ProjectSettings
    created_at: datetime
    updated_at: datetime
    member_associations: List[ProjectMemberRead]
    class Config: from_attributes = True

# ======================================================================================
# Other Schemas (Unchanged)
# ======================================================================================
class CodeSnippetRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: Optional[str]
    language: str
    file_size: int
    created_at: datetime
    class Config: from_attributes = True

class UserPreferences(BaseModel):
    theme: str = "dark"
    email_notifications_enabled: bool = True

class UserStats(BaseModel):
    project_count: int
    review_count: int
    snippets_analyzed: int

class SubscriptionUpdate(BaseModel):
    subscription_tier: str

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: UserRole
    subscription_tier: str
    status: str
    email_verified: bool
    preferences: Optional[UserPreferences] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserRoleUpdate(BaseModel):
    role: UserRole

class CodeSnippetRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    filename: Optional[str]
    language: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True