import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User

logger = logging.getLogger("ai_job_assistant.auth")


def get_current_user_optional(
    x_user_id: Optional[int] = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Resolve the current user from the X-User-Id header if present.

    Returns None when the header is not provided.
    Raises HTTP 401 when the header is present but does not match a user.
    """
    if x_user_id is None:
        return None

    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        logger.warning("invalid X-User-Id header user_id=%s", x_user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user header.",
        )
    return user
