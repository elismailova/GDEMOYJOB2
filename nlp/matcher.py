"""Семантическое сопоставление резюме с вакансиями + Skill Gap Analysis."""
import logging
from typing import Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import config
from .analyzer import ResumeAnalyzer

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Загрузка embedding-модели '%s'...", config.EMBEDDING_MODEL)
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Модель загружена.")
    return _model


def _vacancy_to_text(vacancy: dict) -> str:
    parts = [vacancy.get("name", "")]
    snippet = vacancy.get("snippet", {})
    if snippet.get("requirement"):
        parts.append(snippet["requirement"])
    if snippet.get("responsibility"):
        parts.append(snippet["responsibility"])
    employer = vacancy.get("employer", {})
    if employer.get("name"):
        parts.append(employer["name"])
    return " ".join(p for p in parts if p).strip()


def _skill_overlap_score(resume_skills: list[str], vacancy_text: str) -> tuple[float, list[str]]:
    """Возвращает долю навыков из резюме, найденных в тексте вакансии, и список совпадений."""
    if not resume_skills:
        return 0.0, []
    vacancy_lower = vacancy_text.lower()
    matched = [s for s in resume_skills if s in vacancy_lower]
    score = len(matched) / len(resume_skills)
    return min(score, 1.0), matched


def _skill_gap(resume_skills: list[str], vacancy_text: str, analyzer: ResumeAnalyzer) -> list[str]:
    """Навыки из вакансии, которых нет в резюме."""
    vacancy_skills = set(analyzer.extract_skills_from_text(vacancy_text))
    resume_set = set(resume_skills)
    return sorted(vacancy_skills - resume_set)


class VacancyMatcher:
    def __init__(self):
        self._analyzer = ResumeAnalyzer()

    def rank(
        self,
        resume_text: str,
        resume_skills: list[str],
        vacancies: list[dict],
    ) -> list[dict[str, Any]]:
        """
        Ранжирует вакансии по релевантности резюме.
        Возвращает топ-N с score >= MIN_RELEVANCE_SCORE.
        """
        if not vacancies:
            return []

        model = get_embedding_model()
        resume_emb = model.encode([resume_text], convert_to_numpy=True)

        vac_texts = [_vacancy_to_text(v) for v in vacancies]
        vac_embs = model.encode(vac_texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False)

        semantic_scores = cosine_similarity(resume_emb, vac_embs)[0]

        results = []
        for i, vacancy in enumerate(vacancies):
            sem = float(semantic_scores[i])
            skill_score, matched_skills = _skill_overlap_score(resume_skills, vac_texts[i])
            combined = 0.6 * sem + 0.4 * skill_score

            if combined < config.MIN_RELEVANCE_SCORE:
                continue

            gap = _skill_gap(resume_skills, vac_texts[i], self._analyzer)

            results.append({
                "vacancy": vacancy,
                "score": round(combined, 3),
                "semantic_score": round(sem, 3),
                "skill_score": round(skill_score, 3),
                "matched_skills": matched_skills,
                "skill_gap": gap,
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[: config.TOP_VACANCIES]

    def analyze_skill_gap(
        self, resume_skills: list[str], top_results: list[dict]
    ) -> list[tuple[str, int]]:
        """
        Анализирует дефицит навыков по топ-вакансиям.
        Возвращает список (навык, частота) отсортированный по убыванию.
        """
        gap_counter: dict[str, int] = {}
        for r in top_results:
            for skill in r.get("skill_gap", []):
                gap_counter[skill] = gap_counter.get(skill, 0) + 1
        return sorted(gap_counter.items(), key=lambda x: x[1], reverse=True)
