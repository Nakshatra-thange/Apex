import uuid
from typing import List
from fastapi import Depends, HTTPException, status, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, dependencies, crud
from .database import get_db
from .user_roles import UserRole
from .project_roles import ProjectRole


def is_admin(current_user: models.User = Depends(dependencies.get_current_user)) -> models.User:
    """
    A dependency that checks if the current user is an admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action. Administrator role required.",
        )
    return current_user


def require_project_role(required_roles: List[ProjectRole]):
    """
    A dependency factory that checks if the current user has a specific role
    on a project and creates an audit log on failure.
    """
    
    async def project_role_checker(
        request: Request,
        project_id: uuid.UUID = Path(...),
        current_user: models.User = Depends(dependencies.get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> models.Project:
        
        project = await crud.get_project_by_id(db, project_id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )
            
        membership = next(
            (m for m in project.member_associations if m.user_id == current_user.id),
            None
        )
        
        if not membership or membership.role not in required_roles:
            await crud.create_audit_log(
                db=db,
                action="PROJECT_ACCESS_DENIED",
                user_id=current_user.id,
                request=request,
                resource_type="project",
                resource_id=project_id,
                details={
                    "reason": "User is not a member or lacks required role.",
                    "required_roles": [role.value for role in required_roles],
                    "user_role": membership.role.value if membership else "not_a_member"
                }
            )
            
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of this project.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have the required permissions.",
                )
        
        return project

    return project_role_checker