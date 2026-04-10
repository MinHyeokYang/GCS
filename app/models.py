"""SQLAlchemy ORM models."""

import datetime

from sqlalchemy import DATE, VARCHAR, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    """Represents an application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    email: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_todos: Mapped[list["Todo"]] = relationship(
        "Todo", foreign_keys="Todo.assignee_id", back_populates="assignee"
    )
    created_todos: Mapped[list["Todo"]] = relationship(
        "Todo", foreign_keys="Todo.created_by", back_populates="creator"
    )


class Team(Base):
    """Represents a team that owns todos and tags."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    todos: Mapped[list["Todo"]] = relationship(
        "Todo", back_populates="team", cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", back_populates="team", cascade="all, delete-orphan"
    )


class TeamMember(Base):
    """Join table between User and Team."""

    __tablename__ = "team_members"

    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")


class Todo(Base):
    """Represents a todo item belonging to a team."""

    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, default="todo")
    priority: Mapped[str] = mapped_column(VARCHAR(10), nullable=False, default="medium")
    due_date: Mapped[datetime.date | None] = mapped_column(DATE, nullable=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    team: Mapped["Team"] = relationship("Team", back_populates="todos")
    assignee: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assignee_id], back_populates="assigned_todos"
    )
    creator: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_todos"
    )
    todo_tags: Mapped[list["TodoTag"]] = relationship(
        "TodoTag", back_populates="todo", cascade="all, delete-orphan"
    )

    @property
    def tags(self) -> list["Tag"]:
        """Return the list of Tag objects attached to this todo."""
        return [tt.tag for tt in self.todo_tags]


class Tag(Base):
    """Represents a label that can be attached to todos within a team."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("name", "team_id", name="uq_tag_name_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )

    team: Mapped["Team"] = relationship("Team", back_populates="tags")
    todo_tags: Mapped[list["TodoTag"]] = relationship(
        "TodoTag", back_populates="tag", cascade="all, delete-orphan"
    )


class TodoTag(Base):
    """Join table between Todo and Tag."""

    __tablename__ = "todo_tags"

    todo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("todos.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    todo: Mapped["Todo"] = relationship("Todo", back_populates="todo_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="todo_tags")
