"""Клиент для работы с публичным API SuperJob."""
import asyncio
import logging
from typing import Any
import aiohttp
from config import config

logger = logging.getLogger(__name__)

SJ_AREAS = {
    "Россия": None,
    "Москва": 4,
    "Санкт-Петербург": 14,
    "Новосибирск": 6,
    "Екатеринбург": 8,
    "Казань": 55,
    "Нижний Новгород": 9,
    "Краснодар": 35,
    "Самара": 78,
    "Удалённо": None,
}

SJ_EXPERIENCE = {
    "Без опыта": 1,
    "1–3 года": 2,
    "3–6 лет": 3,
    "Более 6 лет": 4,
}

SJ_EMPLOYMENT = {
    "Полная занятость": 6,
    "Частичная занятость": 2,
    "Проектная работа": 4,
    "Стажировка": 7,
    "Удалённо": 6,
}

SJ_PLACE_OF_WORK = {
    "Удалённо": 2,
}


def _normalize_vacancy(v: dict) -> dict:
    """Приводит вакансию SuperJob к единому формату."""
    salary_from = v.get("payment_from") or None
    salary_to = v.get("payment_to") or None
    currency = v.get("currency", "rub").upper()
    if currency == "RUR":
        currency = "RUR"
    elif currency == "RUB":
        currency = "RUR"

    salary = None
    if salary_from or salary_to:
        salary = {
            "from": salary_from if salary_from else None,
            "to": salary_to if salary_to else None,
            "currency": currency,
        }

    town = v.get("town") or {}
    employer_name = v.get("firm_name") or v.get("client", {}).get("title", "")

    requirement = v.get("candidat", "") or ""
    responsibility = v.get("work", "") or ""

    return {
        "id": str(v.get("id", "")),
        "name": v.get("profession", ""),
        "employer": {"name": employer_name},
        "area": {"name": town.get("title", "") if isinstance(town, dict) else ""},
        "salary": salary,
        "snippet": {
            "requirement": requirement[:500] if requirement else "",
            "responsibility": responsibility[:500] if responsibility else "",
        },
        "alternate_url": v.get("link", "https://superjob.ru"),
    }


class SuperJobApiClient:
    BASE = "https://api.superjob.ru/2.0"

    @property
    def _headers(self) -> dict:
        headers = {
            "User-Agent": "JobMatcherBot/1.0",
            "Accept": "application/json",
        }
        if config.SJ_API_KEY:
            headers["X-Api-App-Id"] = config.SJ_API_KEY
        return headers

    async def search_vacancies(
        self,
        text: str,
        area: int | None = None,
        salary: int | None = None,
        experience: int | None = None,
        employment: int | None = None,
        place_of_work: int | None = None,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "keyword": text,
            "count": min(per_page, 100),
            "page": 0,
            "no_agreement": 0,
        }
        if area:
            params["town"] = area
        if salary:
            params["payment_from"] = salary
        if experience:
            params["experience"] = experience
        if employment:
            params["type_of_work"] = employment
        if place_of_work:
            params["place_of_work"] = place_of_work

        async with aiohttp.ClientSession(headers=self._headers) as session:
            try:
                async with session.get(
                    f"{self.BASE}/vacancies/",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.error("SuperJob API error: %s %s", resp.status, await resp.text())
                        return []
                    data = await resp.json()
                    raw = data.get("objects", [])
                    return [_normalize_vacancy(v) for v in raw]
            except asyncio.TimeoutError:
                logger.error("SuperJob API timeout")
                return []
            except aiohttp.ClientError as e:
                logger.error("SuperJob API connection error: %s", e)
                return []

    @staticmethod
    def format_salary(salary: dict | None) -> str:
        if not salary:
            return "не указана"
        lo = salary.get("from")
        hi = salary.get("to")
        cur = salary.get("currency", "RUR")
        cur_sym = {"RUR": "₽", "USD": "$", "EUR": "€", "KZT": "₸"}.get(cur, cur)
        if lo and hi:
            return f"{lo:,} – {hi:,} {cur_sym}"
        if lo:
            return f"от {lo:,} {cur_sym}"
        if hi:
            return f"до {hi:,} {cur_sym}"
        return "не указана"
