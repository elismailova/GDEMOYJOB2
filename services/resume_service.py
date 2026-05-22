"""Оркестрация: парсинг файла → NLP-анализ → сохранение в БД."""
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import UserRepo, ResumeRepo
from nlp.parser import extract_text
from nlp.analyzer import ResumeAnalyzer


class ResumeService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepo(session)
        self._resume_repo = ResumeRepo(session)
        self._analyzer = ResumeAnalyzer()

    async def process_file(
        self, telegram_id: int, file_bytes: bytes, filename: str
    ) -> dict:
        """Извлекает текст, анализирует резюме и сохраняет в БД."""
        raw_text = extract_text(file_bytes, filename)
        return await self._save_and_analyze(telegram_id, raw_text)

    async def process_text(self, telegram_id: int, text: str) -> dict:
        """Сохраняет и анализирует резюме, введённое текстом."""
        return await self._save_and_analyze(telegram_id, text)

    async def _save_and_analyze(self, telegram_id: int, raw_text: str) -> dict:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise RuntimeError("Пользователь не найден. Используйте /start")

        parsed = self._analyzer.analyze(raw_text)
        await self._resume_repo.upsert(user.id, raw_text, parsed)
        return parsed

    async def get_resume(self, telegram_id: int) -> dict | None:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        resume = await self._resume_repo.get_latest(user.id)
        if not resume:
            return None
        return {"raw_text": resume.raw_text, "parsed": resume.parsed_data}
