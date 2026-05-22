import numpy as np
import pytest
from unittest.mock import MagicMock

from nlp.matcher import (
    VacancyMatcher,
    _vacancy_to_text,
    _skill_overlap_score,
    _skill_gap,
)
from nlp.analyzer import ResumeAnalyzer


class TestVacancyToText:
    def test_combines_name_requirement_responsibility(self):
        vacancy = {
            "name": "Python Developer",
            "snippet": {
                "requirement": "знание Django",
                "responsibility": "разработка API",
            },
            "employer": {"name": "Tech Co"},
        }
        text = _vacancy_to_text(vacancy)
        assert "Python Developer" in text
        assert "Django" in text
        assert "API" in text
        assert "Tech Co" in text

    def test_handles_missing_snippet(self):
        vacancy = {"name": "Аналитик", "snippet": {}, "employer": {}}
        assert _vacancy_to_text(vacancy) == "Аналитик"

    def test_empty_vacancy(self):
        assert _vacancy_to_text({}) == ""


class TestSkillOverlapScore:
    def test_full_overlap(self):
        score, matched = _skill_overlap_score(["python", "sql"], "python sql developer")
        assert score == 1.0
        assert set(matched) == {"python", "sql"}

    def test_partial_overlap(self):
        score, matched = _skill_overlap_score(["python", "java"], "python developer")
        assert score == 0.5
        assert matched == ["python"]

    def test_no_overlap(self):
        score, matched = _skill_overlap_score(["python"], "java developer")
        assert score == 0.0
        assert matched == []

    def test_empty_skills(self):
        score, matched = _skill_overlap_score([], "python developer")
        assert score == 0.0
        assert matched == []

    def test_score_capped_at_one(self):
        score, _ = _skill_overlap_score(["python"], "python python python")
        assert score <= 1.0


class TestSkillGap:
    def test_returns_missing_skills(self):
        analyzer = ResumeAnalyzer()
        gap = _skill_gap(["python"], "требуется python и docker и git", analyzer)
        assert "docker" in gap or "git" in gap

    def test_empty_gap_when_all_present(self):
        analyzer = ResumeAnalyzer()
        vacancy_text = "нужен python разработчик"
        gap = _skill_gap(["python"], vacancy_text, analyzer)
        assert "python" not in gap

    def test_gap_is_sorted(self):
        analyzer = ResumeAnalyzer()
        gap = _skill_gap([], "python docker git sql", analyzer)
        assert gap == sorted(gap)


class TestVacancyMatcher:
    def setup_method(self):
        self.matcher = VacancyMatcher()

    def test_rank_empty_vacancies(self):
        assert self.matcher.rank("some text", ["python"], []) == []

    def test_rank_returns_list(self, monkeypatch):
        import nlp.matcher as m

        mock_model = MagicMock()
        mock_model.encode.side_effect = [
            np.array([[1.0, 0.0]]),
            np.array([[1.0, 0.0], [0.0, 1.0]]),
        ]
        monkeypatch.setattr(m, "get_embedding_model", lambda: mock_model)

        vacancies = [
            {"name": "Python Dev", "snippet": {"requirement": "python"}, "employer": {"name": "A"}},
            {"name": "Designer", "snippet": {"requirement": "figma"}, "employer": {"name": "B"}},
        ]
        results = self.matcher.rank("python developer", ["python"], vacancies)
        assert isinstance(results, list)
        for r in results:
            assert "score" in r
            assert "vacancy" in r
            assert "matched_skills" in r
            assert "skill_gap" in r

    def test_rank_results_sorted_by_score(self, monkeypatch):
        import nlp.matcher as m

        mock_model = MagicMock()
        mock_model.encode.side_effect = [
            np.array([[1.0, 0.0]]),
            np.array([[0.9, 0.1], [0.5, 0.5], [0.1, 0.9]]),
        ]
        monkeypatch.setattr(m, "get_embedding_model", lambda: mock_model)

        vacancies = [
            {"name": "A", "snippet": {}, "employer": {}},
            {"name": "B", "snippet": {}, "employer": {}},
            {"name": "C", "snippet": {}, "employer": {}},
        ]
        results = self.matcher.rank("text", [], vacancies)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_analyze_skill_gap_aggregates_frequency(self):
        top_results = [
            {"skill_gap": ["docker", "git"]},
            {"skill_gap": ["docker", "sql"]},
            {"skill_gap": ["git"]},
        ]
        gap = self.matcher.analyze_skill_gap([], top_results)
        gap_dict = dict(gap)
        assert gap_dict["docker"] == 2
        assert gap_dict["git"] == 2
        assert gap_dict["sql"] == 1

    def test_analyze_skill_gap_sorted_by_frequency(self):
        top_results = [
            {"skill_gap": ["docker", "docker", "sql"]},
            {"skill_gap": ["docker"]},
        ]
        gap = self.matcher.analyze_skill_gap([], top_results)
        frequencies = [freq for _, freq in gap]
        assert frequencies == sorted(frequencies, reverse=True)

    def test_analyze_skill_gap_empty(self):
        assert self.matcher.analyze_skill_gap([], []) == []
