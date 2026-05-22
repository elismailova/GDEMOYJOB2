"""NLP-анализ резюме: извлечение навыков, опыта, образования, должности."""
import re
import logging
from typing import Any
from .skills_vocab import ALL_SKILLS, EXPERIENCE_LEVELS

logger = logging.getLogger(__name__)

# Регулярки для извлечения структурированных данных
_SALARY_RE = re.compile(
    r"(?:зарплата|salary|от|from)?\s*(\d[\d\s]{2,})\s*(?:₽|руб|rub|рублей|\$|usd|€|eur)",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"[\+]?[78]?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")

_SECTION_HEADERS = {
    "experience": [
        "опыт работы", "experience", "трудовой стаж", "работа",
        "professional experience", "work experience",
    ],
    "education": [
        "образование", "education", "учёба", "обучение",
        "academic background", "qualifications",
    ],
    "skills": [
        "навыки", "skills", "компетенции", "технологии", "стек",
        "hard skills", "soft skills", "ключевые навыки",
    ],
    "about": ["о себе", "about", "summary", "profile", "цель", "objective"],
}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found: list[str] = []
    for skill in ALL_SKILLS:
        escaped = re.escape(skill)
        # Граница: не буква и не цифра (работает для латиницы и кириллицы)
        pattern = r"(?<![а-яёa-zA-Z0-9\-])" + escaped + r"(?![а-яёa-zA-Z0-9\-])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def _extract_experience_level(text: str) -> str | None:
    text_lower = text.lower()
    for level, keywords in EXPERIENCE_LEVELS.items():
        for kw in keywords:
            if kw in text_lower:
                return level
    return None


def _extract_years_of_experience(text: str) -> int | None:
    """Пытается найти упоминание стажа в годах."""
    patterns = [
        r"(\d+)\s*(?:лет|год[ау]?|years?)\s*(?:опыта|experience|стажа)?",
        r"опыт\s*(?:работы)?\s*[-–—]?\s*(\d+)\s*(?:лет|год)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    # Считаем по году первой работы
    years = list(map(int, _YEAR_RE.findall(text)))
    if len(years) >= 2:
        span = max(years) - min(years)
        if 0 < span < 50:
            return span
    return None


_POSITION_SKIP = {
    "резюме", "cv", "curriculum vitae", "resume", "анкета",
    "профиль", "profile",
}

_POSITION_KEYWORDS = [
    "аналитик", "разработчик", "инженер", "менеджер", "дизайнер",
    "тестировщик", "специалист", "программист", "администратор",
    "директор", "руководитель", "консультант", "маркетолог",
    "analyst", "developer", "engineer", "manager", "designer",
    "scientist", "architect", "lead", "head", "officer",
]


def _extract_desired_position(text: str) -> str | None:
    # Явные паттерны с меткой должности
    labeled = [
        r"(?:желаемая должность|ищу работу|соискатель|позиция|position|цель|objective)[:\s]+([^\n]{5,80})",
        r"(?:должность|вакансия)[:\s]+([^\n]{5,80})",
    ]
    for p in labeled:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # Ищем строку с ключевым словом должности во ВСЁМ тексте (не только в первых строках)
    all_lines = [l.strip() for l in text.split("\n") if l.strip()]
    for candidate in all_lines:
        low = candidate.lower()
        if (3 < len(candidate) < 100
                and not _EMAIL_RE.search(candidate)
                and not _PHONE_RE.search(candidate)
                and low not in _POSITION_SKIP
                and not candidate[0].isdigit()
                and any(kw in low for kw in _POSITION_KEYWORDS)):
            return candidate
    return None


def _extract_education(text: str) -> list[str]:
    edu_kws = [
        "университет", "институт", "академия", "колледж", "университе",
        "university", "institute", "college", "bachelor", "master",
        "бакалавр", "магистр", "специалист", "аспирант", "phd",
    ]
    lines = text.split("\n")
    edu: list[str] = []
    for line in lines:
        low = line.lower()
        if any(kw in low for kw in edu_kws):
            clean = line.strip()
            if 5 < len(clean) < 200:
                edu.append(clean)
    return edu[:5]


def _extract_salary_expectation(text: str) -> int | None:
    m = _SALARY_RE.search(text)
    if m:
        try:
            return int(m.group(1).replace(" ", ""))
        except ValueError:
            pass
    return None


class ResumeAnalyzer:
    """Парсит сырой текст резюме в структурированный словарь."""

    def analyze(self, raw_text: str) -> dict[str, Any]:
        skills = _extract_skills(raw_text)
        level = _extract_experience_level(raw_text)
        years_exp = _extract_years_of_experience(raw_text)
        position = _extract_desired_position(raw_text)
        education = _extract_education(raw_text)
        salary = _extract_salary_expectation(raw_text)
        email = m.group() if (m := _EMAIL_RE.search(raw_text)) else None
        phone = m.group() if (m := _PHONE_RE.search(raw_text)) else None

        return {
            "skills": skills,
            "experience_level": level,
            "years_of_experience": years_exp,
            "desired_position": position,
            "education": education,
            "salary_expectation": salary,
            "email": email,
            "phone": phone,
            "text_length": len(raw_text),
        }

    def extract_skills_from_text(self, text: str) -> list[str]:
        return _extract_skills(text)
