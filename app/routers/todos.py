"""Todos router — CRUD for todos within a team."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Tag, Team, TeamMember, Todo, TodoTag
from app.schemas import Priority, TodoCreate, TodoResponse, TodoStatus, TodoUpdate

router = APIRouter(prefix="/teams/{team_id}/todos", tags=["Todos"])


def _get_team_or_404(team_id: int, db: Session) -> Team:
    """Return a Team by id or raise 404."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


def _get_todo_or_404(todo_id: int, team_id: int, db: Session) -> Todo:
    """Return a Todo belonging to the given team, or raise 404."""
    todo = (
        db.query(Todo)
        .options(selectinload(Todo.todo_tags).selectinload(TodoTag.tag))
        .filter(Todo.id == todo_id, Todo.team_id == team_id)
        .first()
    )
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found.")
    return todo


def _assert_team_member(team_id: int, user_id: int, db: Session) -> None:
    """Raise 400 if the user is not a member of the team."""
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


@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a todo",
    description="Create a todo in the given team. `created_by` must be a team member. "
    "If `assignee_id` is provided, that user must also be a team member.",
)
def create_todo(team_id: int, body: TodoCreate, db: Session = Depends(get_db)) -> Todo:
    """Create a new todo item for the team."""
    _get_team_or_404(team_id, db)
    _assert_team_member(team_id, body.created_by, db)
    if body.assignee_id is not None:
        _assert_team_member(team_id, body.assignee_id, db)

    todo = Todo(
        title=body.title,
        description=body.description,
        status=body.status.value,
        priority=body.priority.value,
        due_date=body.due_date,
        team_id=team_id,
        assignee_id=body.assignee_id,
        created_by=body.created_by,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return _get_todo_or_404(todo.id, team_id, db)


@router.get(
    "",
    response_model=list[TodoResponse],
    status_code=status.HTTP_200_OK,
    summary="List todos",
    description="Return todos for a team. Supports filtering by status, priority, assignee_id, tag_id.",
)
def list_todos(
    team_id: int,
    db: Session = Depends(get_db),
    todo_status: TodoStatus | None = Query(None, alias="status", description="Filter by status"),
    priority: Priority | None = Query(None, description="Filter by priority"),
    assignee_id: int | None = Query(None, description="Filter by assignee user ID"),
    tag_id: int | None = Query(None, description="Filter by tag ID"),
) -> list[Todo]:
    """Return a filtered list of todos for the given team."""
    _get_team_or_404(team_id, db)

    q = (
        db.query(Todo)
        .options(selectinload(Todo.todo_tags).selectinload(TodoTag.tag))
        .filter(Todo.team_id == team_id)
    )
    if todo_status is not None:
        q = q.filter(Todo.status == todo_status.value)
    if priority is not None:
        q = q.filter(Todo.priority == priority.value)
    if assignee_id is not None:
        q = q.filter(Todo.assignee_id == assignee_id)
    if tag_id is not None:
        q = q.join(TodoTag).filter(TodoTag.tag_id == tag_id)

    return q.all()


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a todo",
    description="Return a single todo by ID.",
)
def get_todo(team_id: int, todo_id: int, db: Session = Depends(get_db)) -> Todo:
    """Return a single todo."""
    _get_team_or_404(team_id, db)
    return _get_todo_or_404(todo_id, team_id, db)


@router.patch(
    "/{todo_id}",
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a todo",
    description="Partially update a todo. Only provided fields are changed.",
)
def update_todo(
    team_id: int, todo_id: int, body: TodoUpdate, db: Session = Depends(get_db)
) -> Todo:
    """Partially update a todo item."""
    _get_team_or_404(team_id, db)
    todo = _get_todo_or_404(todo_id, team_id, db)

    if body.assignee_id is not None:
        _assert_team_member(team_id, body.assignee_id, db)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, TodoStatus | Priority):
            setattr(todo, field, value.value)
        else:
            setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return _get_todo_or_404(todo.id, team_id, db)


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo",
    description="Permanently delete a todo.",
)
def delete_todo(team_id: int, todo_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a todo item."""
    _get_team_or_404(team_id, db)
    todo = _get_todo_or_404(todo_id, team_id, db)
    db.delete(todo)
    db.commit()


# ---------------------------------------------------------------------------
# Tag attachment (nested under todos)
# ---------------------------------------------------------------------------


@router.post(
    "/{todo_id}/tags/{tag_id}",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attach a tag to a todo",
    description="Attach a team tag to a todo. Tag must belong to the same team.",
)
def attach_tag(team_id: int, todo_id: int, tag_id: int, db: Session = Depends(get_db)) -> Todo:
    """Attach a tag to a todo."""
    _get_team_or_404(team_id, db)
    todo = _get_todo_or_404(todo_id, team_id, db)

    tag = db.get(Tag, tag_id)
    if tag is None or tag.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found in this team.",
        )

    already = (
        db.query(TodoTag)
        .filter(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
        .first()
    )
    if already:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag is already attached to this todo.",
        )

    db.add(TodoTag(todo_id=todo_id, tag_id=tag_id))
    db.commit()
    return _get_todo_or_404(todo_id, team_id, db)


@router.delete(
    "/{todo_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Detach a tag from a todo",
    description="Remove a tag from a todo.",
)
def detach_tag(team_id: int, todo_id: int, tag_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a tag from a todo."""
    _get_team_or_404(team_id, db)
    _get_todo_or_404(todo_id, team_id, db)

    todo_tag = (
        db.query(TodoTag)
        .filter(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
        .first()
    )
    if todo_tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag is not attached to this todo.",
        )
    db.delete(todo_tag)
    db.commit()
