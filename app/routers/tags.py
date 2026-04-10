"""Tags router — tag management within a team."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tag, Team
from app.schemas import TagCreate, TagResponse

router = APIRouter(prefix="/teams/{team_id}/tags", tags=["Tags"])


def _get_team_or_404(team_id: int, db: Session) -> Team:
    """Return a Team by id or raise 404."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


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
