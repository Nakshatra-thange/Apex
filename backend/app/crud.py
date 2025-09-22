# File: apex/backend/app/crud.py
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
import hashlib
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timedelta, timezone
from .user_roles import UserRole
from . import models, schemas, security
from .security import REFRESH_TOKEN_EXPIRE_DAYS
from .project_roles import ProjectRole
from sqlalchemy.orm import selectinload
from fastapi import Request
from sqlalchemy import func, select
from . import schemas
from . import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import Dict, Any

PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    hashed_pass = security.hash_password(user.password)
    db_user = models.User(
        email=user.email,
        password_hash=hashed_pass
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_refresh_token(db: AsyncSession, user_id: int, token: str) -> models.RefreshToken:
    token_hash = security.hash_password(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db_refresh_token = models.RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()
    await db.refresh(db_refresh_token)
    return db_refresh_token


async def create_password_reset_token(db: AsyncSession, user_id: int) -> str:
    plain_token = security.generate_secure_token()
    token_hash = security.hash_password(plain_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    db_token = models.PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()
    return plain_token


# --- THIS FUNCTION IS NOW CORRECTED FOR PYTHON 3.9 ---
async def get_user_by_password_reset_token(db: AsyncSession, token: str) -> Optional[models.User]:
    """
    Finds a valid, non-expired password reset token and returns the associated user.
    """
    query = (
        select(models.PasswordResetToken)
        .where(models.PasswordResetToken.expires_at > datetime.now(timezone.utc))
        .options(selectinload(models.PasswordResetToken.user))
    )
    
    async for db_token in await db.stream_scalars(query):
        if security.verify_password(token, db_token.token_hash):
            return db_token.user
            
    return None


async def update_user_password(db: AsyncSession, user: models.User, new_password: str) -> None:
    user.password_hash = security.hash_password(new_password)
    
    # Invalidate all existing password reset tokens for this user for security
    # This requires the relationship to be loaded. We'll handle this in the endpoint.
    # For now, this logic is sufficient.
    for token in user.password_reset_tokens:
        await db.delete(token)
        
    db.add(user)
    await db.commit()

async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.User]:
    """
    Fetches a list of all users from the database with pagination.
    """
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    return result.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[models.User]:
    """
    Fetches a single user by their UUID.
    """
    return await db.get(models.User, user_id)


async def update_user_role(db: AsyncSession, user: models.User, new_role: UserRole) -> models.User:
    """
    Updates a user's role in the database.
    """
    user.role = new_role
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# File: apex/backend/app/crud.py
# (Add this new function to the end of the file)


# ... (all existing functions) ...

async def create_project_with_owner(db: AsyncSession, project_in: schemas.ProjectCreate, owner_id: uuid.UUID) -> models.Project:
    """
    Creates a new project and assigns the creator as the owner.
    """
    # 1. Create the new project instance
    db_project = models.Project(
        name=project_in.name,
        description=project_in.description
    )
    db.add(db_project)
    
    # 2. Create the project membership link
    db_member = models.ProjectMember(
        project=db_project,
        user_id=owner_id,
        role=ProjectRole.OWNER
    )
    db.add(db_member)
    
    await db.commit()
    await db.refresh(db_project)
    return db_project

async def get_projects_for_user(db: AsyncSession, user_id: uuid.UUID) -> List[models.Project]:
    """
    Fetches all projects that a user is a member of.
    """
    query = (
        select(models.Project)
        .join(models.ProjectMember)
        .where(models.ProjectMember.user_id == user_id)
        .order_by(models.Project.created_at.desc())
        .options(selectinload(models.Project.member_associations).selectinload(models.ProjectMember.user))
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_project_by_id(db: AsyncSession, project_id: uuid.UUID) -> Optional[models.Project]:
    """
    Fetches a single project by its ID, pre-loading its members.
    """
    query = (
        select(models.Project)
        .where(models.Project.id == project_id)
        .options(selectinload(models.Project.member_associations).selectinload(models.ProjectMember.user))
    )
    result = await db.execute(query)
    return result.scalars().first()

async def create_audit_log(
    db: AsyncSession,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
):
    """
    Creates a new entry in the audit log.
    """
    ip_address = request.client.host if request else None
    
    db_log = models.AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        details=details,
        resource_type=resource_type,
        resource_id=resource_id
    )
    db.add(db_log)
    await db.commit()

async def update_user_preferences(db: AsyncSession, user: models.User, preferences: schemas.UserPreferences) -> models.User:
    """Updates a user's preferences."""
    user.preferences = preferences.dict()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Calculates and returns usage statistics for a user."""
    project_count_query = (
        select(func.count(models.ProjectMember.project_id))
        .where(models.ProjectMember.user_id == user_id)
    )
    project_count = (await db.execute(project_count_query)).scalar_one()

    review_and_snippet_query = (
        select(func.count(models.Review.id), func.count(models.CodeSnippet.id))
        .join(models.CodeSnippet)
        .join(models.Project)
        .join(models.ProjectMember)
        .where(models.ProjectMember.user_id == user_id)
    )
    review_count, snippet_count = (await db.execute(review_and_snippet_query)).one()

    return {
        "project_count": project_count,
        "review_count": review_count,
        "snippets_analyzed": snippet_count,
    }

async def update_user_subscription(db: AsyncSession, user: models.User, tier: str) -> models.User:
    """Updates a user's subscription tier."""
    user.subscription_tier = tier
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user: models.User):
    """Deletes a user and all their associated data via cascading."""
    await db.delete(user)
    await db.commit()

# (Add these new functions to the end of your existing crud.py file)



# ... (all existing functions from previous steps should be here) ...

async def update_project(db: AsyncSession, project: models.Project, project_in: schemas.ProjectUpdate) -> models.Project:
    """
    Updates a project's details based on the provided Pydantic schema.
    It only updates the fields that are actually provided in the input.
    """
    # Convert the Pydantic model to a dictionary, excluding fields that were not set
    update_data = project_in.dict(exclude_unset=True)
    
    # Update the project object with the new data
    for key, value in update_data.items():
        setattr(project, key, value)
        
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: models.Project):
    """
    Deletes a project from the database.
    """
    await db.delete(project)
    await db.commit()

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
import hashlib

# ... (all existing functions) ...

# --- Collaboration Functions ---

async def add_project_member(db: AsyncSession, project: models.Project, user: models.User, role: ProjectRole) -> models.ProjectMember:
    """Adds a user to a project with a specific role."""
    db_member = models.ProjectMember(project_id=project.id, user_id=user.id, role=role)
    db.add(db_member)
    await db.commit()
    # Eagerly load the 'user' relationship for the response
    await db.refresh(db_member, attribute_names=['user'])
    return db_member

async def update_project_member_role(db: AsyncSession, member: models.ProjectMember, new_role: ProjectRole) -> models.ProjectMember:
    """Updates the role of an existing project member."""
    member.role = new_role
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

async def remove_project_member(db: AsyncSession, member: models.ProjectMember):
    """Removes a member from a project."""
    await db.delete(member)
    await db.commit()

# --- Settings Function ---

async def update_project_settings(db: AsyncSession, project: models.Project, settings_in: schemas.ProjectSettings) -> models.Project:
    """Updates a project's settings JSON field."""
    project.settings = settings_in.dict()
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

# --- Stats/Analytics Function ---

async def get_project_stats(db: AsyncSession, project_id: uuid.UUID) -> dict:
    """Calculates statistics for a single project."""
    member_count_query = select(func.count(models.ProjectMember.user_id)).where(models.ProjectMember.project_id == project_id)
    snippet_count_query = select(func.count(models.CodeSnippet.id)).where(models.CodeSnippet.project_id == project_id)
    review_count_query = select(func.count(models.Review.id)).join(models.CodeSnippet).where(models.CodeSnippet.project_id == project_id)
    
    member_count = (await db.execute(member_count_query)).scalar_one()
    snippet_count = (await db.execute(snippet_count_query)).scalar_one()
    review_count = (await db.execute(review_count_query)).scalar_one()
    
    return {
        "member_count": member_count,
        "snippet_count": snippet_count,
        "review_count": review_count,
    }

# --- Template Function ---

async def create_project_from_template(db: AsyncSession, template_project: models.Project, new_project_name: str, owner: models.User) -> models.Project:
    """Creates a new project by cloning a template."""
    # 1. Create the new project
    new_project = models.Project(
        name=new_project_name,
        description=template_project.description,
        settings=template_project.settings
    )
    db.add(new_project)
    
    # 2. Assign the new owner
    owner_membership = models.ProjectMember(
        project=new_project, user_id=owner.id, role=ProjectRole.OWNER
    )
    db.add(owner_membership)
    
    # 3. (Optional) Copy code snippets from the template
    for snippet in template_project.code_snippets:
        new_snippet = models.CodeSnippet(
            project=new_project,
            filename=f"template_{snippet.filename}",
            content=snippet.content,
            language=snippet.language,
            file_size=snippet.file_size,
            hash=hash_content(snippet.content)
        )
        db.add(new_snippet)
        
    await db.commit()
    await db.refresh(new_project)
    return new_project

# Helper function for templates
def hash_content(content: str) -> str:
    """Helper to hash content for cloned snippets."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

async def add_project_member(db: AsyncSession, project: models.Project, user: models.User, role: ProjectRole) -> models.ProjectMember:
    db_member = models.ProjectMember(project_id=project.id, user_id=user.id, role=role)
    db.add(db_member)
    await db.commit()
    await db.refresh(db_member)
    return db_member

async def update_project_member_role(db: AsyncSession, member: models.ProjectMember, new_role: ProjectRole) -> models.ProjectMember:
    member.role = new_role
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member

async def remove_project_member(db: AsyncSession, member: models.ProjectMember):
    await db.delete(member)
    await db.commit()

# --- Settings Function ---

async def update_project_settings(db: AsyncSession, project: models.Project, settings_in: schemas.ProjectSettings) -> models.Project:
    project.settings = settings_in.dict()
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

# --- Stats/Analytics Function ---

async def get_project_stats(db: AsyncSession, project_id: uuid.UUID) -> dict:
    member_count_query = select(func.count(models.ProjectMember.user_id)).where(models.ProjectMember.project_id == project_id)
    snippet_count_query = select(func.count(models.CodeSnippet.id)).where(models.CodeSnippet.project_id == project_id)
    review_count_query = select(func.count(models.Review.id)).join(models.CodeSnippet).where(models.CodeSnippet.project_id == project_id)
    
    member_count = (await db.execute(member_count_query)).scalar_one()
    snippet_count = (await db.execute(snippet_count_query)).scalar_one()
    review_count = (await db.execute(review_count_query)).scalar_one()
    
    return {
        "member_count": member_count,
        "snippet_count": snippet_count,
        "review_count": review_count,
    }

# --- Template Function ---

async def create_project_from_template(db: AsyncSession, template_project: models.Project, new_project_name: str, owner: models.User) -> models.Project:
    # 1. Create the new project
    new_project = models.Project(
        name=new_project_name,
        description=template_project.description,
        settings=template_project.settings
    )
    db.add(new_project)
    
    # 2. Assign the new owner
    owner_membership = models.ProjectMember(
        project=new_project, user_id=owner.id, role=ProjectRole.OWNER
    )
    db.add(owner_membership)
    
    # 3. (Optional) Copy code snippets from the template
    for snippet in template_project.code_snippets:
        new_snippet = models.CodeSnippet(
            project=new_project,
            filename=f"template_{snippet.filename}",
            content=snippet.content,
            language=snippet.language,
            file_size=snippet.file_size,
            hash=crud.hash_content(snippet.content) # Assumes a hash_content helper
        )
        db.add(new_snippet)
        
    await db.commit()
    await db.refresh(new_project)
    return new_project

# Helper function for templates
def hash_content(content: str) -> str:
    """Helper to hash content for cloned snippets."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


async def create_code_snippet(
    db: AsyncSession,
    project_id: uuid.UUID,
    filename: str,
    content: str,
    language: str
) -> models.CodeSnippet:
    """
    Creates a new code snippet in the database.
    """
    content_hash = hash_content(content)
    file_size = len(content.encode('utf-8'))

    db_snippet = models.CodeSnippet(
        project_id=project_id,
        filename=filename,
        content=content,
        language=language,
        hash=content_hash,
        file_size=file_size
    )
    db.add(db_snippet)
    await db.commit()
    await db.refresh(db_snippet)
    return db_snippet

async def create_review_for_snippet(db: AsyncSession, snippet: models.CodeSnippet, priority: int = 0) -> models.Review:
    """
    Creates a new, pending review record in the database for a given code snippet.
    """
    db_review = models.Review(
        code_snippet_id=snippet.id,
        status="pending",
        priority=priority
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review

async def get_snippet_by_id(db: AsyncSession, snippet_id: uuid.UUID) -> Optional[models.CodeSnippet]:
    """Fetches a single code snippet by its ID."""
    return await db.get(models.CodeSnippet, snippet_id)



# ... (all existing functions) ...

async def update_snippet_metrics(db: AsyncSession, snippet: models.CodeSnippet, metrics: Dict[str, Any]) -> models.CodeSnippet:
    """
    Updates a code snippet with the metrics extracted by the preprocessor.
    """
    snippet.loc = metrics.get("loc")
    snippet.cyclomatic_complexity = metrics.get("cyclomatic_complexity")
    snippet.normalized_hash = metrics.get("normalized_hash")
    snippet.detected_language = metrics.get("detected_language")
    
    db.add(snippet)
    await db.commit()
    await db.refresh(snippet)
    return snippet

