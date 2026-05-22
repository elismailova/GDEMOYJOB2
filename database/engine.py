from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import config
from .models import Base

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
