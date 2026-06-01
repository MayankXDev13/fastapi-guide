from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from models import ProjectMember, ProjectMemberRole


def get_project_members(project_id: str, db: Session) -> list[ProjectMember]:
    return db.exec(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    ).all()


def add_member_to_project(
    project_id: str,
    user_id: str,
    db: Session,
    role: ProjectMemberRole = ProjectMemberRole.member,
) -> ProjectMember:
    existing = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a project member",
        )

    member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member_role(
    project_id: str, user_id: str, new_role: ProjectMemberRole | str, db: Session
) -> ProjectMember:
    member = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found",
        )

    member.role = ProjectMemberRole(new_role) if isinstance(new_role, str) else new_role
    member.updated_at = datetime.now(timezone.utc)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member_from_project(project_id: str, user_id: str, db: Session) -> None:
    member = db.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project member not found",
        )
    db.delete(member)
    db.commit()
