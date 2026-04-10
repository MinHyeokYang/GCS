"""Users router — POST /users, GET /users."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate

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


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user",
    description="Return a single user by ID.",
)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    """Return a single user by ID."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description="Partially update a user by ID.",
)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db)) -> User:
    """Update a user by ID."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

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


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="Delete a user by ID. Fails when the user is still referenced by restricted resources.",
)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a user by ID."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db.delete(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User cannot be deleted because related resources still exist.",
        )
