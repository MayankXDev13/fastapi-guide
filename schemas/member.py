from datetime import datetime

from pydantic import BaseModel

from models import ProjectMemberRole


class AddMemberRequest(BaseModel):
    user_id: str
    role: ProjectMemberRole = ProjectMemberRole.member


class UpdateMemberRoleRequest(BaseModel):
    new_role: ProjectMemberRole


class MemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: ProjectMemberRole
    joined_at: datetime
    created_at: datetime
    updated_at: datetime


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
