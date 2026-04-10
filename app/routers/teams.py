"""Teams router — team CRUD and member management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Team, TeamMember, User
from app.schemas import MemberAdd, MemberResponse, TeamCreate, TeamResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


def _get_team_or_404(team_id: int, db: Session) -> Team:
    """Return a Team by id or raise 404."""
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


def _get_user_or_404(user_id: int, db: Session) -> User:
    """Return a User by id or raise 404."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team",
    description="Create a new team.",
)
def create_team(body: TeamCreate, db: Session = Depends(get_db)) -> Team:
    """Create and persist a new team."""
    team = Team(name=body.name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a team",
    description="Return team info by ID.",
)
def get_team(team_id: int, db: Session = Depends(get_db)) -> Team:
    """Return a team by its ID."""
    return _get_team_or_404(team_id, db)


@router.post(
    "/{team_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to a team",
    description="Add an existing user to a team. Returns 400 if already a member.",
)
def add_member(team_id: int, body: MemberAdd, db: Session = Depends(get_db)) -> TeamMember:
    """Add a user to the team."""
    _get_team_or_404(team_id, db)
    _get_user_or_404(body.user_id, db)

    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == body.user_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team.",
        )

    member = TeamMember(team_id=team_id, user_id=body.user_id)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from a team",
    description="Remove a user from a team. Returns 404 if the membership does not exist.",
)
def remove_member(team_id: int, user_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a user from the team."""
    _get_team_or_404(team_id, db)
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found.",
        )
    db.delete(member)
    db.commit()
