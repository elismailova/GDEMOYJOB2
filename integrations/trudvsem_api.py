"""Клиент для работы с открытым API Trudvsem.ru (Работа в России)."""
import asyncio
import logging
from typing import Any
from urllib.parse import quote_plus
import aiohttp

logger = logging.getLogger(__name__)

TRUDVSEM_AREAS = {
    "Россия": None,
    "Москва": "77",
    "Санкт-Петербург": "78",
    "Новосибирск": "54",
    "Екатеринбург": "65",
    "Казань": "92",
    "Нижний Новгород": "22",
    "Краснодар": "03",
    "Самара": "36",
    "Удалённо": None,
}

TRUDVSEM_EXPERIENCE = {
    "Без опыта": "Без опыта",
    "1–3 года": "1-3 года",
    "3–6 лет": "3-6 лет",
    "Более 6 лет": "более 6 лет",
}

TRUDVSEM_EMPLOYMENT = {
    "Полная занятость": "Полная занятость",
    "Частичная занятость": "Частичная занятость",
    "Проектная работа": "Проектная работа",
    "Стажировка": "Стажировка",
}


def _normalize_vacancy(v: dict) -> dict:
    """Приводит вакансию Trudvsem к единому формату."""
    vac = v.get("vacancy", v)

    salary_min = vac.get("salary_min")
    salary_max = vac.get("salary_max")
    salary = None
    if salary_min or salary_max:
        salary = {
            "from": int(salary_min) if salary_min else None,
            "to": int(salary_max) if salary_max else None,
            "currency": "RUR",
        }

    region = vac.get("region") or {}
    company = vac.get("company") or {}
    requirement = vac.get("requirement") or {}

    req_parts = []
    if requirement.get("experience"):
        req_parts.append(f"Опыт: {requirement['experience']}")
    if requirement.get("education"):
        req_parts.append(f"Образование: {requirement['education']}")
    if requirement.get("qualification"):
        req_parts.append(requirement["qualification"])

    duty = vac.get("duty") or ""
    vac_id = vac.get("id", "")
    job_name = vac.get("job-name") or ""

    # API возвращает vac_url формата /vacancy/card/{companycode}/{uuid} — рабочая ссылка
    vac_url = (
        vac.get("vac_url")
        or f"https://trudvsem.ru/vacancy/search?text={quote_plus(job_name)}"
    )

    return {
        "id": str(vac_id),
        "name": vac.get("job-name") or "",
        "employer": {"name": company.get("name") or ""},
        "area": {"name": (region.get("name") or "").replace("г.", "").strip()},
        "salary": salary,
        "snippet": {
            "requirement": " ".join(req_parts)[:500],
            "responsibility": duty[:500],
        },
        "alternate_url": vac_url,
    }


class TrudvsemApiClient:
    BASE = "https://opendata.trudvsem.ru/api/v1"
    HEADERS = {
        "User-Agent": "JobMatcherBot/1.0",
        "Accept": "application/json",
    }

    async def search_vacancies(
        self,
        text: str,
        region_code: str | None = None,
        salary: int | None = None,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "text": text,
            "limit": min(per_page, 100),
            "offset": 0,
        }
        if region_code:
            params["regionCode"] = region_code
        if salary:
            params["salaryFrom"] = salary

        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            try:
                async with session.get(
                    f"{self.BASE}/vacancies",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        logger.error("Trudvsem API error: %s %s", resp.status, await resp.text())
                        return []
                    data = await resp.json()
                    raw = (data.get("results") or {}).get("vacancies") or []
                    normalized = [_normalize_vacancy(v) for v in raw]
                    logger.info("Trudvsem вернул %d вакансий по запросу '%s'", len(normalized), text)
                    return normalized
            except asyncio.TimeoutError:
                logger.error("Trudvsem API timeout")
                return []
            except aiohttp.ClientError as e:
                logger.error("Trudvsem API connection error: %s", e)
                return []

    @staticmethod
    def format_salary(salary: dict | None) -> str:
        if not salary:
            return "не указана"
        lo = salary.get("from")
        hi = salary.get("to")
        cur_sym = {"RUR": "₽", "USD": "$", "EUR": "€", "KZT": "₸"}.get(
            salary.get("currency", "RUR"), "₽"
        )
        if lo and hi:
            return f"{lo:,} – {hi:,} {cur_sym}"
        if lo:
            return f"от {lo:,} {cur_sym}"
        if hi:
            return f"до {hi:,} {cur_sym}"
        return "не указана"
