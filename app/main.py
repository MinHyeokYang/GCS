"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers import tags, teams, todos, users

app = FastAPI(
    title="Team Todo API",
    version="1.0.0",
    description=(
        "팀 단위 Todo 관리 백엔드. "
        "Swagger UI: `/docs` | ReDoc: `/redoc`"
    ),
)

app.include_router(users.router)
app.include_router(teams.router)
app.include_router(todos.router)
app.include_router(tags.router)
