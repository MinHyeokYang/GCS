"""Users router — POST /users, GET /users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description="Create a new user. Email must be unique.",
)
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create and persist a new user."""
    user = User(name=body.name, email=body.email)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    db.refresh(user)
    return user


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users",
    description="Return a list of all registered users.",
)
def list_users(db: Session = Depends(get_db)) -> list[User]:
    """Return all users."""
    return db.query(User).all()
