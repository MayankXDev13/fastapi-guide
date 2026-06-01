from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from models import ProjectTaskComment


def create_comment(comment_data: dict[str, Any], db: Session) -> ProjectTaskComment:
    comment = ProjectTaskComment(**comment_data)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments_for_task(task_id: str, db: Session) -> list[ProjectTaskComment]:
    return db.exec(
        select(ProjectTaskComment).where(ProjectTaskComment.task_id == task_id)
    ).all()


def update_comment(
    comment_id: str, updated_data: dict[str, Any], db: Session
) -> ProjectTaskComment:
    comment = db.get(ProjectTaskComment, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if "comment" in updated_data and updated_data["comment"] is not None:
        comment.comment = updated_data["comment"]

    comment.updated_at = datetime.now(timezone.utc)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(comment_id: str, db: Session) -> None:
    comment = db.get(ProjectTaskComment, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    db.delete(comment)
    db.commit()
