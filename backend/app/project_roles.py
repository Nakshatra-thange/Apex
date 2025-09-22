# File: apex/backend/app/project_roles.py

from enum import Enum

class ProjectRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"