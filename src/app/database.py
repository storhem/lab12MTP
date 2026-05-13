from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    return create_async_engine(settings.DATABASE_URL, echo=False)


def _make_session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


engine = _make_engine()
async_session_factory = _make_session_factory(engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
