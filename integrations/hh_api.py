"""Клиент для работы с публичным API hh.ru."""
import asyncio
import logging
from typing import Any
import aiohttp
from config import config

logger = logging.getLogger(__name__)

# Коды регионов hh.ru
HH_AREAS = {
    "Россия": 113,
    "Москва": 1,
    "Санкт-Петербург": 2,
    "Новосибирск": 4,
    "Екатеринбург": 3,
    "Казань": 88,
    "Нижний Новгород": 66,
    "Краснодар": 53,
    "Самара": 78,
    "Удалённо": None,
}

HH_EXPERIENCE = {
    "Без опыта": "noExperience",
    "1–3 года": "between1And3",
    "3–6 лет": "between3And6",
    "Более 6 лет": "moreThan6",
}

HH_EMPLOYMENT = {
    "Полная занятость": "full",
    "Частичная занятость": "part",
    "Проектная работа": "project",
    "Стажировка": "probation",
}

HH_SCHEDULE = {
    "Полный день": "fullDay",
    "Гибкий график": "flexible",
    "Удалённая работа": "remote",
    "Сменный график": "shift",
}


class HHApiClient:
    BASE = config.HH_API_BASE
    HEADERS = {
        "User-Agent": config.HH_USER_AGENT,
        "Accept": "application/json",
        "HH-User-Agent": config.HH_USER_AGENT,
    }

    async def search_vacancies(
        self,
        text: str,
        area: int | None = None,
        salary: int | None = None,
        experience: str | None = None,
        employment: str | None = None,
        schedule: str | None = None,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "text": text,
            "per_page": min(per_page, 100),
            "page": 0,
        }
        if area:
            params["area"] = area
        if salary:
            params["salary"] = salary
            params["currency_code"] = "RUR"
            params["only_with_salary"] = "true"
        if experience:
            params["experience"] = experience
        if employment:
            params["employment"] = employment
        if schedule:
            params["schedule"] = schedule

        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            try:
                async with session.get(
                    f"{self.BASE}/vacancies",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.error("HH API error: %s %s", resp.status, await resp.text())
                        return []
                    data = await resp.json()
                    return data.get("items", [])
            except asyncio.TimeoutError:
                logger.error("HH API timeout")
                return []
            except aiohttp.ClientError as e:
                logger.error("HH API connection error: %s", e)
                return []

    async def get_vacancy(self, vacancy_id: str) -> dict[str, Any] | None:
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            try:
                async with session.get(
                    f"{self.BASE}/vacancies/{vacancy_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return None
                    return await resp.json()
            except Exception as e:
                logger.error("HH get_vacancy error: %s", e)
                return None

    async def get_areas(self) -> list[dict]:
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            try:
                async with session.get(f"{self.BASE}/areas") as resp:
                    if resp.status == 200:
                        return await resp.json()
            except Exception:
                pass
        return []

    @staticmethod
    def format_salary(salary: dict | None) -> str:
        if not salary:
            return "не указана"
        lo = salary.get("from")
        hi = salary.get("to")
        cur = salary.get("currency", "RUR")
        cur_sym = {"RUR": "₽", "USD": "$", "EUR": "€", "UAH": "₴", "KZT": "₸"}.get(cur, cur)
        if lo and hi:
            return f"{lo:,} – {hi:,} {cur_sym}"
        if lo:
            return f"от {lo:,} {cur_sym}"
        if hi:
            return f"до {hi:,} {cur_sym}"
        return "не указана"
