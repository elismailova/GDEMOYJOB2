import pytest
from nlp.analyzer import (
    ResumeAnalyzer,
    _extract_skills,
    _extract_experience_level,
    _extract_years_of_experience,
    _extract_salary_expectation,
    _extract_desired_position,
    _extract_education,
)


class TestExtractSkills:
    def test_finds_python_in_text(self):
        assert "python" in _extract_skills("Опыт работы с Python и Django")

    def test_finds_multiple_skills(self):
        skills = _extract_skills("Stack: Python, PostgreSQL, Docker, Git")
        assert "python" in skills
        assert "postgresql" in skills
        assert "docker" in skills
        assert "git" in skills

    def test_no_false_positives_in_partial_match(self):
        # "pythonista" не должен давать "python" (граница слова)
        skills = _extract_skills("pythonista разработчик")
        assert "python" not in skills

    def test_returns_sorted_unique(self):
        skills = _extract_skills("python python python")
        assert skills == sorted(set(skills))

    def test_empty_text(self):
        assert _extract_skills("") == []


class TestExtractExperienceLevel:
    def test_junior_detected(self):
        assert _extract_experience_level("junior python developer") == "junior"

    def test_senior_detected(self):
        assert _extract_experience_level("ищу senior инженера") == "senior"

    def test_returns_none_if_no_level(self):
        assert _extract_experience_level("разработчик на Python") is None


class TestExtractYearsOfExperience:
    def test_explicit_years_ru(self):
        assert _extract_years_of_experience("опыт работы 5 лет") == 5

    def test_explicit_years_en(self):
        assert _extract_years_of_experience("3 years of experience") == 3

    def test_explicit_years_opyta(self):
        assert _extract_years_of_experience("опыт работы — 7 лет") == 7

    def test_returns_none_if_not_found(self):
        assert _extract_years_of_experience("нет информации") is None


class TestExtractSalary:
    def test_rub_sign(self):
        assert _extract_salary_expectation("ожидаемая зарплата 150000 ₽") == 150000

    def test_rub_word(self):
        assert _extract_salary_expectation("от 80 000 руб") == 80000

    def test_no_salary(self):
        assert _extract_salary_expectation("опыт работы 3 года") is None


class TestExtractDesiredPosition:
    def test_finds_labeled_position(self):
        pos = _extract_desired_position("Желаемая должность: Python Developer")
        assert pos is not None
        assert "Python Developer" in pos

    def test_finds_position_by_keyword(self):
        text = "Иван Иванов\nPython разработчик\nМосква"
        pos = _extract_desired_position(text)
        assert pos is not None

    def test_returns_none_for_plain_text(self):
        assert _extract_desired_position("Москва, 30 лет") is None


class TestExtractEducation:
    def test_finds_university(self):
        text = "Московский государственный университет, 2020"
        edu = _extract_education(text)
        assert len(edu) == 1
        assert "университет" in edu[0].lower()

    def test_finds_multiple_institutions(self):
        text = "Бакалавр, МГТУ\nМагистр, НИУ ВШЭ"
        edu = _extract_education(text)
        assert len(edu) == 2

    def test_empty_if_no_education(self):
        assert _extract_education("разработчик Python, 5 лет опыта") == []


class TestResumeAnalyzer:
    def setup_method(self):
        self.analyzer = ResumeAnalyzer()

    def test_analyze_returns_all_keys(self):
        result = self.analyzer.analyze("Python developer, 3 years experience")
        expected_keys = {
            "skills", "experience_level", "years_of_experience",
            "desired_position", "education", "salary_expectation",
            "email", "phone", "text_length",
        }
        assert expected_keys == set(result.keys())

    def test_analyze_text_length(self):
        text = "Python developer"
        result = self.analyzer.analyze(text)
        assert result["text_length"] == len(text)

    def test_analyze_extracts_email(self):
        result = self.analyzer.analyze("Контакт: user@example.com")
        assert result["email"] == "user@example.com"

    def test_analyze_extracts_phone(self):
        result = self.analyzer.analyze("Телефон: +7 (999) 123-45-67")
        assert result["phone"] is not None

    def test_extract_skills_from_text(self):
        skills = self.analyzer.extract_skills_from_text("знаю Python и SQL")
        assert "python" in skills
        assert "sql" in skills
