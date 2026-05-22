import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./job_matcher.db"
        )
    )
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024
    TOP_VACANCIES: int = 5
    MIN_RELEVANCE_SCORE: float = 0.1
    HH_FETCH_LIMIT: int = 50
    HH_API_BASE: str = "https://api.hh.ru"
    HH_USER_AGENT: str = "JobMatcherBot/1.0 (vadimmmalchenko@gmail.com)"
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"


config = Config()
