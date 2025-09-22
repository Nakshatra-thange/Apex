from fastapi import APIRouter, Depends, HTTPException, status, Response, File, UploadFile
from typing import List, Optional
import uuid
import os
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from . import crud, models, schemas
from .dependencies import get_current_user
from .database import get_db
from .permissions import require_project_role
from .project_roles import ProjectRole
from .rate_limiter import rate_limit
from .redis_manager import get_redis_pool
from .user_roles import UserRole
from .upload_config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE_BYTES

router = APIRouter()
@router.post("/", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit())])
async def create_new_project(project_in: schemas.ProjectCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a new project. The creator becomes the owner."""
    return await crud.create_project_with_owner(db=db, project_in=project_in, owner_id=current_user.id)

@router.post("/from-template", response_model=schemas.ProjectRead, dependencies=[Depends(rate_limit())])
async def create_project_from_template(template_in: schemas.ProjectCreateFromTemplate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a new project by cloning an existing one."""
    template_project = await crud.get_project_by_id(db, project_id=template_in.template_project_id)
    if not template_project:
        raise HTTPException(status_code=404, detail="Template project not found.")
    return await crud.create_project_from_template(db, template_project, template_in.new_project_name, current_user)

@router.get("/", response_model=List[schemas.ProjectRead])
async def list_user_projects(current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List all projects the current user is a member of."""
    return await crud.get_projects_for_user(db=db, user_id=current_user.id)

@router.get("/{project_id}", response_model=schemas.ProjectRead)
async def get_project_details(project: models.Project = Depends(require_project_role([ProjectRole.VIEWER, ProjectRole.EDITOR, ProjectRole.OWNER]))):
    """Get details of a specific project. Accessible to all project members."""
    return project

@router.put("/{project_id}", response_model=schemas.ProjectRead)
async def update_existing_project(project_in: schemas.ProjectUpdate, project: models.Project = Depends(require_project_role([ProjectRole.EDITOR, ProjectRole.OWNER])), db: AsyncSession = Depends(get_db)):
    """Update a project's name or description. Accessible to editors and owners."""
    return await crud.update_project(db=db, project=project, project_in=project_in)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_project(project: models.Project = Depends(require_project_role([ProjectRole.OWNER])), db: AsyncSession = Depends(get_db)):
    """Delete a project. Accessible only to the project owner."""
    await crud.delete_project(db=db, project=project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ==============================================================================
# Collaboration / Member Management
# ==============================================================================

@router.get("/{project_id}/members", response_model=List[schemas.ProjectMemberRead])
async def get_project_members(project: models.Project = Depends(require_project_role([ProjectRole.VIEWER, ProjectRole.EDITOR, ProjectRole.OWNER]))):
    """List all members of a project. Accessible to all project members."""
    return project.member_associations

@router.post("/{project_id}/members", response_model=schemas.ProjectMemberRead, status_code=201)
async def invite_project_member(invite_in: schemas.ProjectMemberInvite, project: models.Project = Depends(require_project_role([ProjectRole.OWNER])), db: AsyncSession = Depends(get_db)):
    """Add a new member to a project. Accessible only to the owner."""
    user_to_invite = await crud.get_user_by_email(db, email=invite_in.email)
    if not user_to_invite:
        raise HTTPException(status_code=404, detail="User with that email not found.")
    
    existing_member = next((m for m in project.member_associations if m.user_id == user_to_invite.id), None)
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this project.")
        
    return await crud.add_project_member(db, project, user_to_invite, invite_in.role)

@router.put("/{project_id}/members/{user_id}", response_model=schemas.ProjectMemberRead)
async def update_project_member(user_id: uuid.UUID, update_in: schemas.ProjectMemberUpdate, project: models.Project = Depends(require_project_role([ProjectRole.OWNER])), db: AsyncSession = Depends(get_db)):
    """Update a project member's role. Accessible only to the owner."""
    member_to_update = next((m for m in project.member_associations if m.user_id == user_id), None)
    if not member_to_update:
        raise HTTPException(status_code=404, detail="User is not a member of this project.")
    return await crud.update_project_member_role(db, member_to_update, update_in.role)

@router.delete("/{project_id}/members/{user_id}", status_code=204)
async def remove_project_member(user_id: uuid.UUID, project: models.Project = Depends(require_project_role([ProjectRole.OWNER])), db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Remove a member from a project. Accessible only to the owner."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Owner cannot remove themselves from a project.")
    
    member_to_remove = next((m for m in project.member_associations if m.user_id == user_id), None)
    if not member_to_remove:
        raise HTTPException(status_code=404, detail="User is not a member of this project.")
    
    await crud.remove_project_member(db, member_to_remove)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ==============================================================================
# Settings & Stats
# ==============================================================================

@router.put("/{project_id}/settings", response_model=schemas.ProjectSettings)
async def update_project_settings_endpoint(settings_in: schemas.ProjectSettings, project: models.Project = Depends(require_project_role([ProjectRole.EDITOR, ProjectRole.OWNER])), db: AsyncSession = Depends(get_db)):
    """Update a project's settings. Accessible to editors and owners."""
    return await crud.update_project_settings(db, project, settings_in)

@router.get("/{project_id}/stats", response_model=schemas.ProjectStats)
async def get_project_stats_endpoint(project: models.Project = Depends(require_project_role([ProjectRole.VIEWER, ProjectRole.EDITOR, ProjectRole.OWNER])), db: AsyncSession = Depends(get_db)):
    """Get statistics for a specific project."""
    stats = await crud.get_project_stats(db, project_id=project.id)
    return stats

# (Add this new function to the end of your existing api_projects.py file)



# ... (all existing endpoints) ...

@router.post("/{project_id}/snippets/{snippet_id}/review", status_code=status.HTTP_202_ACCEPTED)
async def submit_snippet_for_review(
    project_id: uuid.UUID,
    snippet_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: ArqRedis = Depends(get_redis_pool)
):
    """
    Submits a code snippet for analysis by a background worker.
    """
    # 1. Authorize: Ensure the user is a member of the project
    project = await crud.get_project_by_id(db, project_id=project_id)
    if not any(member.user_id == current_user.id for member in project.member_associations):
        raise HTTPException(status_code=403, detail="User is not a member of this project")

    # 2. Find the code snippet
    snippet = await crud.get_snippet_by_id(db, snippet_id=snippet_id)
    if not snippet or snippet.project_id != project_id:
        raise HTTPException(status_code=404, detail="Snippet not found in this project")

    # 3. Create a pending review record in the database
    review = await crud.create_review_for_snippet(db, snippet=snippet)

    # 4. Determine which queue to use based on user role
    queue_name = "high_priority" if current_user.role == UserRole.PREMIUM_USER else "default_priority"

    # 5. Enqueue the background job
    await redis.enqueue_job(
        'analyze_code_task',    # The name of the function in tasks.py
        review.id,              # The first argument to the task function
        _queue_name=queue_name  # Specify which queue to use
    )

    return {"message": "Code snippet submitted for analysis.", "review_id": review.id}

@router.post("/{project_id}/snippets/upload", response_model=schemas.CodeSnippetRead, status_code=201)
async def upload_code_snippet_file(
    project: models.Project = Depends(require_project_role([ProjectRole.EDITOR, ProjectRole.OWNER])),
    upload_file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads a code snippet file to a specific project.
    Performs validation for file size, type, and malware.
    """
    # 1. File Size Validation (Tier-Based)
    max_size = MAX_FILE_SIZE_BYTES.get(current_user.role, MAX_FILE_SIZE_BYTES[UserRole.FREE_USER])
    file_contents = await upload_file.read()
    if len(file_contents) > max_size:
        raise HTTPException(status_code=413, detail=f"File size exceeds limit for your tier ({max_size / 1024} KB).")

    # 2. File Type Validation
    _, extension = os.path.splitext(upload_file.filename)
    if extension not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '{extension}' is not allowed.")

    # 3. Malware Scanning
    is_safe, message = scan_for_malware(file_contents)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"Malware scan failed: {message}")

    # 4. Save the snippet to the database
    new_snippet = await crud.create_code_snippet(
        db=db,
        project_id=project.id,
        filename=upload_file.filename,
        content=file_contents.decode('utf-8')
    )
    return new_snippet