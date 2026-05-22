from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from .models import User, Resume, SearchHistory


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int, username: str | None, first_name: str | None) -> User:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create(self, telegram_id: int, username: str | None, first_name: str | None) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False
        user = await self.create(telegram_id, username, first_name)
        return user, True


class ResumeRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, user_id: int) -> Optional[Resume]:
        result = await self.session.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(desc(Resume.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: int, raw_text: str, parsed_data: dict) -> Resume:
        existing = await self.get_latest(user_id)
        if existing:
            existing.raw_text = raw_text
            existing.parsed_data = parsed_data
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        resume = Resume(user_id=user_id, raw_text=raw_text, parsed_data=parsed_data)
        self.session.add(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume


class SearchHistoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, query_params: dict, results_count: int, top_score: float | None) -> SearchHistory:
        entry = SearchHistory(
            user_id=user_id,
            query_params=query_params,
            results_count=results_count,
            top_score=top_score,
        )
        self.session.add(entry)
        await self.session.commit()
        return entry

    async def get_recent(self, user_id: int, limit: int = 5) -> list[SearchHistory]:
        result = await self.session.execute(
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
