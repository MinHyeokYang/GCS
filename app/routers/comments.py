"""Comments router - CRUD for todo comments within a team."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Team, TeamMember, Todo, User
from app.schemas import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(prefix="/teams/{team_id}/todos/{todo_id}/comments", tags=["Comments"])


def _get_team_or_404(team_id: int, db: Session) -> Team:
    """Return a Team by id or raise 404."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


def _get_todo_or_404(team_id: int, todo_id: int, db: Session) -> Todo:
    """Return a Todo by id/team or raise 404."""
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.team_id == team_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found.")
    return todo


def _get_user_or_404(user_id: int, db: Session) -> User:
    """Return a User by id or raise 404."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _assert_team_member(team_id: int, user_id: int, db: Session) -> None:
    """Raise 400 if the user is not a team member."""
    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this team.",
        )


def _get_comment_or_404(team_id: int, todo_id: int, comment_id: int, db: Session) -> Comment:
    """Return a comment by id/team/todo or raise 404."""
    comment = (
        db.query(Comment)
        .join(Todo, Comment.todo_id == Todo.id)
        .filter(Comment.id == comment_id, Comment.todo_id == todo_id, Todo.team_id == team_id)
        .first()
    )
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    return comment


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment",
    description="Create a comment on a todo. `user_id` must belong to a team member.",
)
def create_comment(
    team_id: int, todo_id: int, body: CommentCreate, db: Session = Depends(get_db)
) -> Comment:
    """Create a todo comment."""
    _get_team_or_404(team_id, db)
    _get_todo_or_404(team_id, todo_id, db)
    _get_user_or_404(body.user_id, db)
    _assert_team_member(team_id, body.user_id, db)

    comment = Comment(todo_id=todo_id, user_id=body.user_id, content=body.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get(
    "",
    response_model=list[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="List comments",
    description="List comments of a todo.",
)
def list_comments(team_id: int, todo_id: int, db: Session = Depends(get_db)) -> list[Comment]:
    """List todo comments."""
    _get_team_or_404(team_id, db)
    _get_todo_or_404(team_id, todo_id, db)
    return db.query(Comment).filter(Comment.todo_id == todo_id).all()


@router.get(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a comment",
    description="Return a single comment by ID.",
)
def get_comment(
    team_id: int, todo_id: int, comment_id: int, db: Session = Depends(get_db)
) -> Comment:
    """Get a single comment."""
    _get_team_or_404(team_id, db)
    _get_todo_or_404(team_id, todo_id, db)
    return _get_comment_or_404(team_id, todo_id, comment_id, db)


@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a comment",
    description="Partially update a comment.",
)
def update_comment(
    team_id: int, todo_id: int, comment_id: int, body: CommentUpdate, db: Session = Depends(get_db)
) -> Comment:
    """Partially update a comment."""
    _get_team_or_404(team_id, db)
    _get_todo_or_404(team_id, todo_id, db)
    comment = _get_comment_or_404(team_id, todo_id, comment_id, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(comment, field, value)

    db.commit()
    db.refresh(comment)
    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description="Delete a comment by ID.",
)
def delete_comment(team_id: int, todo_id: int, comment_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a comment."""
    _get_team_or_404(team_id, db)
    _get_todo_or_404(team_id, todo_id, db)
    comment = _get_comment_or_404(team_id, todo_id, comment_id, db)
    db.delete(comment)
    db.commit()
