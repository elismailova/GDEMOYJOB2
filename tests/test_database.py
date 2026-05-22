import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from database.models import Base
from database.repository import UserRepo, ResumeRepo, SearchHistoryRepo


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


class TestUserRepo:
    async def test_create_new_user(self, session: AsyncSession):
        repo = UserRepo(session)
        user, created = await repo.get_or_create(123, "testuser", "Ivan")
        assert created is True
        assert user.telegram_id == 123
        assert user.username == "testuser"

    async def test_get_existing_user(self, session: AsyncSession):
        repo = UserRepo(session)
        await repo.get_or_create(456, "alice", "Alice")
        user, created = await repo.get_or_create(456, "alice", "Alice")
        assert created is False
        assert user.telegram_id == 456

    async def test_get_by_telegram_id_not_found(self, session: AsyncSession):
        repo = UserRepo(session)
        result = await repo.get_by_telegram_id(999)
        assert result is None

    async def test_users_are_independent(self, session: AsyncSession):
        repo = UserRepo(session)
        u1, _ = await repo.get_or_create(1, "u1", "User1")
        u2, _ = await repo.get_or_create(2, "u2", "User2")
        assert u1.id != u2.id


class TestResumeRepo:
    async def test_upsert_creates_resume(self, session: AsyncSession):
        user, _ = await UserRepo(session).get_or_create(100, "user", "User")
        repo = ResumeRepo(session)
        resume = await repo.upsert(user.id, "raw text", {"skills": ["python"]})
        assert resume.raw_text == "raw text"
        assert resume.parsed_data == {"skills": ["python"]}

    async def test_upsert_updates_existing(self, session: AsyncSession):
        user, _ = await UserRepo(session).get_or_create(101, "user2", "User2")
        repo = ResumeRepo(session)
        await repo.upsert(user.id, "old text", {"skills": []})
        updated = await repo.upsert(user.id, "new text", {"skills": ["python", "sql"]})
        assert updated.raw_text == "new text"
        assert "sql" in updated.parsed_data["skills"]

    async def test_get_latest_returns_none_if_no_resume(self, session: AsyncSession):
        user, _ = await UserRepo(session).get_or_create(102, "user3", "User3")
        repo = ResumeRepo(session)
        assert await repo.get_latest(user.id) is None


class TestSearchHistoryRepo:
    async def test_add_and_get_recent(self, session: AsyncSession):
        user, _ = await UserRepo(session).get_or_create(200, "searcher", "Searcher")
        repo = SearchHistoryRepo(session)
        await repo.add(user.id, {"query": "python"}, results_count=5, top_score=0.85)
        await repo.add(user.id, {"query": "django"}, results_count=3, top_score=0.72)
        history = await repo.get_recent(user.id)
        assert len(history) == 2

    async def test_get_recent_respects_limit(self, session: AsyncSession):
        user, _ = await UserRepo(session).get_or_create(201, "searcher2", "Searcher2")
        repo = SearchHistoryRepo(session)
        for i in range(5):
            await repo.add(user.id, {"query": f"q{i}"}, results_count=i, top_score=None)
        history = await repo.get_recent(user.id, limit=2)
        assert len(history) == 2

    async def test_history_empty_for_new_user(self, session: AsyncSession):
        user, _ = await UserRepo(session).get_or_create(202, "new", "New")
        repo = SearchHistoryRepo(session)
        assert await repo.get_recent(user.id) == []
