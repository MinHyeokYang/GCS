"""Concurrent stress test — database connection pool under load.

Run with:
    pytest tests/test_stress_concurrent.py -v -s

Five scenarios:
    1. Concurrent reads       – 100 GET requests, concurrency=20
    2. Concurrent writes      – 50 POST requests, concurrency=10
    3. Mixed read/write       – 100 requests (70 R / 30 W), concurrency=15
    4. Connection pool burst   – 200 simultaneous GETs (concurrency=200)
    5. Write contention       – 30 concurrent PATCHes on the same row

Each scenario prints a latency/error-rate report to stdout.

Pool notes
----------
StaticPool (used in unit tests) shares one connection across all threads —
concurrent writes from FastAPI's thread pool will corrupt cursor state.
This file uses NullPool (no pooling; fresh connection per checkout) which
mirrors the production behaviour under high concurrency and avoids
false positives from pool implementation artefacts.
"""

from __future__ import annotations

import asyncio
import os
import statistics
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from dataclasses import field

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database import Base
from app.database import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Temporary file-based DB with NullPool
# ---------------------------------------------------------------------------

_tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmpfile.close()
_DB_URL = f"sqlite:///{_tmpfile.name}"

# NullPool: each session.checkout() opens a brand-new OS-level connection;
# SQLite WAL serialises writers at the file level — no shared-cursor corruption.
_engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db: Session = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class StressResult:
    total: int = 0
    success: int = 0
    errors: Counter = field(default_factory=Counter)
    latencies: list[float] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        return (self.total - self.success) / self.total if self.total else 0.0

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        s = sorted(self.latencies)
        return s[min(int(len(s) * p / 100), len(s) - 1)]

    def report(self, label: str) -> str:
        lat = self.latencies
        lines = [
            "",
            "─" * 62,
            f"  {label}",
            "─" * 62,
            f"  Total     : {self.total}",
            f"  OK        : {self.success}",
            f"  Error rate: {self.error_rate:.1%}",
        ]
        if lat:
            lines += [
                f"  Latency (ms)",
                f"    min  : {min(lat) * 1000:7.1f}",
                f"    mean : {statistics.mean(lat) * 1000:7.1f}",
                f"    p50  : {self.percentile(50) * 1000:7.1f}",
                f"    p95  : {self.percentile(95) * 1000:7.1f}",
                f"    p99  : {self.percentile(99) * 1000:7.1f}",
                f"    max  : {max(lat) * 1000:7.1f}",
            ]
        if self.errors:
            lines.append(f"  Errors    : {dict(self.errors)}")
        lines.append("─" * 62)
        return "\n".join(lines)


async def _run(coro_factory, *, concurrency: int, total: int) -> StressResult:
    """Run *total* coroutines with at most *concurrency* in-flight."""
    sem = asyncio.Semaphore(concurrency)
    result = StressResult(total=total)

    async def _one(i: int) -> None:
        async with sem:
            t0 = time.perf_counter()
            status_code, ok = await coro_factory(i)
            result.latencies.append(time.perf_counter() - t0)
            if ok:
                result.success += 1
            else:
                result.errors[status_code] += 1

    await asyncio.gather(*[_one(i) for i in range(total)])
    return result


def _transport() -> httpx.ASGITransport:
    return httpx.ASGITransport(app=app)


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def _db():
    Base.metadata.create_all(bind=_engine)
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()
    try:
        os.unlink(_tmpfile.name)
    except OSError:
        pass


@pytest.fixture(scope="module")
def seed(_db):
    """Seed 5 users, 1 team, 20 todos synchronously before any test runs."""

    async def _seed():
        async with httpx.AsyncClient(transport=_transport(), base_url="http://test") as c:
            user_ids = []
            for i in range(5):
                r = await c.post("/users", json={"name": f"U{i}", "email": f"u{i}@stress-test.com"})
                assert r.status_code == 201, r.text
                user_ids.append(r.json()["id"])

            r = await c.post("/teams", json={"name": "StressTeam"})
            assert r.status_code == 201, r.text
            team_id = r.json()["id"]

            for uid in user_ids:
                r = await c.post(f"/teams/{team_id}/members", json={"user_id": uid})
                assert r.status_code == 201, r.text

            todo_ids = []
            for i in range(20):
                r = await c.post(
                    f"/teams/{team_id}/todos",
                    json={
                        "title": f"Seed {i}",
                        "status": "todo",
                        "priority": "medium",
                        "created_by": user_ids[i % 5],
                    },
                )
                assert r.status_code == 201, r.text
                todo_ids.append(r.json()["id"])

        return {"team_id": team_id, "user_ids": user_ids, "todo_ids": todo_ids}

    return asyncio.run(_seed())


# ---------------------------------------------------------------------------
# Stress tests
# ---------------------------------------------------------------------------


def test_concurrent_reads(seed, capsys):
    """100 GET /todos requests at concurrency=20 — read throughput."""
    team_id = seed["team_id"]

    async def _read(i: int):
        async with httpx.AsyncClient(transport=_transport(), base_url="http://test") as c:
            r = await c.get(f"/teams/{team_id}/todos")
            return r.status_code, r.status_code == 200

    result = asyncio.run(_run(_read, concurrency=20, total=100))
    with capsys.disabled():
        print(result.report("CONCURRENT READS  [concurrency=20, total=100]"))

    assert result.error_rate == 0.0, f"Read errors: {dict(result.errors)}"
    assert result.percentile(95) < 3.0, f"p95={result.percentile(95)*1000:.0f}ms exceeded 3 s"


def test_concurrent_writes(seed, capsys):
    """50 POST /todos requests at concurrency=10 — write serialisation."""
    team_id = seed["team_id"]
    user_ids = seed["user_ids"]

    async def _write(i: int):
        async with httpx.AsyncClient(transport=_transport(), base_url="http://test") as c:
            r = await c.post(
                f"/teams/{team_id}/todos",
                json={
                    "title": f"ConcurrentWrite {i}",
                    "status": "todo",
                    "priority": "medium",
                    "created_by": user_ids[i % len(user_ids)],
                },
            )
            return r.status_code, r.status_code == 201

    result = asyncio.run(_run(_write, concurrency=10, total=50))
    with capsys.disabled():
        print(result.report("CONCURRENT WRITES  [concurrency=10, total=50]"))

    assert result.error_rate == 0.0, (
        f"Write errors (possible SQLite lock contention): {dict(result.errors)}"
    )


def test_concurrent_mixed_rw(seed, capsys):
    """100 requests (≈70 R / 30 W) at concurrency=15 — mixed load."""
    team_id = seed["team_id"]
    user_ids = seed["user_ids"]
    todo_ids = seed["todo_ids"]

    async def _mixed(i: int):
        async with httpx.AsyncClient(transport=_transport(), base_url="http://test") as c:
            if i % 3 == 0:  # ~33 % writes
                r = await c.post(
                    f"/teams/{team_id}/todos",
                    json={
                        "title": f"Mixed {i}",
                        "status": "todo",
                        "priority": "low",
                        "created_by": user_ids[i % len(user_ids)],
                    },
                )
                return r.status_code, r.status_code == 201
            else:
                tid = todo_ids[i % len(todo_ids)]
                r = await c.get(f"/teams/{team_id}/todos/{tid}")
                return r.status_code, r.status_code == 200

    result = asyncio.run(_run(_mixed, concurrency=15, total=100))
    with capsys.disabled():
        print(result.report("CONCURRENT MIXED R/W  [concurrency=15, total=100]"))

    assert result.error_rate == 0.0, f"Mixed R/W errors: {dict(result.errors)}"


def test_connection_pool_burst(seed, capsys):
    """200 simultaneous GETs — exercises max connection pool pressure."""
    team_id = seed["team_id"]

    async def _burst(i: int):
        async with httpx.AsyncClient(transport=_transport(), base_url="http://test") as c:
            r = await c.get(f"/teams/{team_id}/todos")
            return r.status_code, r.status_code == 200

    result = asyncio.run(_run(_burst, concurrency=200, total=200))
    with capsys.disabled():
        print(result.report("CONNECTION POOL BURST  [concurrency=200, total=200]"))

    assert result.error_rate == 0.0, (
        f"Pool exhaustion errors: {dict(result.errors)}\n"
        "Fix: add pool_size/max_overflow to create_engine() or switch to NullPool."
    )


def test_write_contention_same_row(seed, capsys):
    """30 concurrent PATCHes on the same todo row — detects write contention."""
    team_id = seed["team_id"]
    todo_id = seed["todo_ids"][0]
    statuses = ["todo", "in_progress", "done"]

    async def _patch(i: int):
        async with httpx.AsyncClient(transport=_transport(), base_url="http://test") as c:
            r = await c.patch(
                f"/teams/{team_id}/todos/{todo_id}",
                json={"status": statuses[i % 3]},
            )
            return r.status_code, r.status_code == 200

    result = asyncio.run(_run(_patch, concurrency=10, total=30))
    with capsys.disabled():
        print(result.report("WRITE CONTENTION SAME ROW  [concurrency=10, total=30]"))

    assert result.error_rate == 0.0, f"Contention errors: {dict(result.errors)}"
