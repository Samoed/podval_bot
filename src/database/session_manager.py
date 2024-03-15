from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import Settings


class SessionManager:
    """
    A class that implements the necessary functionality for working with the database:
    issuing sessions, storing and updating connection settings.
    """

    def __init__(self) -> None:
        self.refresh()

    def __new__(cls) -> "SessionManager":
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(self.engine, expire_on_commit=False)

    def refresh(self) -> None:
        self.engine = create_async_engine(Settings().database_uri, echo=True, future=True)


def with_async_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session_maker = SessionManager().get_session_maker()
        async with session_maker() as session:
            try:
                return await func(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    return wrapper
