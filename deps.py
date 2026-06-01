from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from database import get_session
from models import User


def get_current_user(
    request: Request, db: Session = Depends(get_session)
) -> User:
    user: User | None = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user