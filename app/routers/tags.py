"""Tags router — tag management within a team."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tag, Team
from app.schemas import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/teams/{team_id}/tags", tags=["Tags"])


def _get_team_or_404(team_id: int, db: Session) -> Team:
    """Return a Team by id or raise 404."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


def _get_tag_or_404(team_id: int, tag_id: int, db: Session) -> Tag:
    """Return a Tag by id/team or raise 404."""
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.team_id == team_id).first()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    return tag


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tag",
    description="Create a tag for the given team. Tag names must be unique per team.",
)
def create_tag(team_id: int, body: TagCreate, db: Session = Depends(get_db)) -> Tag:
    """Create a new tag for the team."""
    _get_team_or_404(team_id, db)
    tag = Tag(name=body.name, team_id=team_id)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag name already exists in this team.",
        )
    db.refresh(tag)
    return tag


@router.get(
    "",
    response_model=list[TagResponse],
    status_code=status.HTTP_200_OK,
    summary="List tags",
    description="Return all tags for the given team.",
)
def list_tags(team_id: int, db: Session = Depends(get_db)) -> list[Tag]:
    """Return all tags belonging to the team."""
    _get_team_or_404(team_id, db)
    return db.query(Tag).filter(Tag.team_id == team_id).all()


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a tag",
    description="Return a single tag by ID.",
)
def get_tag(team_id: int, tag_id: int, db: Session = Depends(get_db)) -> Tag:
    """Return a single tag."""
    _get_team_or_404(team_id, db)
    return _get_tag_or_404(team_id, tag_id, db)


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a tag",
    description="Partially update a tag by ID.",
)
def update_tag(team_id: int, tag_id: int, body: TagUpdate, db: Session = Depends(get_db)) -> Tag:
    """Partially update a tag."""
    _get_team_or_404(team_id, db)
    tag = _get_tag_or_404(team_id, tag_id, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag name already exists in this team.",
        )
    db.refresh(tag)
    return tag
