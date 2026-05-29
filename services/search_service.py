"""Оркестрация: поиск вакансий на Trudvsem.ru → NLP-ранжирование → сохранение истории."""
import asyncio
from functools import partial
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import UserRepo, ResumeRepo, SearchHistoryRepo
from integrations.trudvsem_api import TrudvsemApiClient
from nlp.matcher import VacancyMatcher
from config import config


def _salary_matches(salary: dict | None, min_salary: int) -> bool:
    if not salary:
        return True
    sal_from = salary.get("from")
    sal_to = salary.get("to")
    if sal_to and sal_to >= min_salary:
        return True
    if sal_from and sal_from >= min_salary:
        return True
    return False


class SearchService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepo(session)
        self._resume_repo = ResumeRepo(session)
        self._history_repo = SearchHistoryRepo(session)
        self._api = TrudvsemApiClient()
        self._matcher = VacancyMatcher()

    async def search(
        self,
        telegram_id: int,
        position: str | None = None,
        area: str | None = None,
        salary: int | None = None,
        experience: str | None = None,
        employment: str | None = None,
    ) -> list[dict]:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise RuntimeError("Пользователь не найден.")

        resume = await self._resume_repo.get_latest(user.id)
        if not resume:
            raise RuntimeError("Резюме не загружено. Сначала загрузите резюме.")

        parsed = resume.parsed_data or {}
        resume_skills: list[str] = parsed.get("skills", [])

        search_text = (
            position
            or parsed.get("desired_position")
            or " ".join(resume_skills[:5])
            or "специалист"
        )

        vacancies = await self._api.search_vacancies(
            text=search_text,
            region_code=area,
            per_page=config.HH_FETCH_LIMIT,
        )

        if salary:
            vacancies = [v for v in vacancies if _salary_matches(v.get("salary"), salary)]

        # NLP-ранжирование блокирует event loop — выносим в поток
        loop = asyncio.get_event_loop()
        ranked = await loop.run_in_executor(
            None,
            partial(self._matcher.rank, resume.raw_text, resume_skills, vacancies),
        )

        top_score = ranked[0]["score"] if ranked else None
        await self._history_repo.add(
            user_id=user.id,
            query_params={
                "position": search_text,
                "area": area,
                "salary": salary,
                "experience": experience,
                "employment": employment,
            },
            results_count=len(ranked),
            top_score=top_score,
        )

        return ranked

    def get_skill_gap_summary(
        self, top_results: list[dict], resume_skills: list[str]
    ) -> list[tuple[str, int]]:
        return self._matcher.analyze_skill_gap(resume_skills, top_results)
