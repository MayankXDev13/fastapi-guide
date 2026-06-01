from datetime import datetime
from pydantic import BaseModel


class CreateCommentRequest(BaseModel):
    task_id: str
    comment: str


class UpdateCommentRequest(BaseModel):
    comment: str


class CommentResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    comment: str
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
