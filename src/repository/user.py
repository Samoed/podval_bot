from datetime import datetime

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import User, get_session


class RepoUser:
    @staticmethod
    async def create_user(
        username: str, nickname: str, birthday: datetime, session: AsyncSession | None = None
    ) -> User:
        session = session or await get_session()
        user = User(username=username, nickname=nickname, birthday=birthday)
        session.add(user)
        await session.commit()
        return user

    @staticmethod
    async def get_user_by_id(user_id: int, session: AsyncSession) -> User | None:
        session = session or await get_session()
        return await session.get(User, user_id)

    @staticmethod
    async def create_users(
        usernames: list[str], nickname: list[str], birthdays: list[datetime], session: AsyncSession | None = None
    ) -> list[User]:
        session = session or await get_session()
        users = [
            User(username=username, nickname=nickname, birthday=birthday)
            for username, nickname, birthday in zip(usernames, nickname, birthdays)
        ]
        session.add_all(users)
        await session.commit()
        return users

    @staticmethod
    async def get_users_with_birthday(birthday: datetime, session: AsyncSession | None = None) -> list[User]:
        session = session or await get_session()
        return (
            await session.scalars(
                select(User).where(
                    extract("day", User.birthday) == birthday.day, extract("month", User.birthday) == birthday.month
                )
            )
        ).all()  # type: ignore

    @staticmethod
    async def create_or_update_users(
        usernames: list[str], nicknames: list[str], birthdays: list[datetime], session: AsyncSession | None = None
    ) -> list[User]:
        session = session or await get_session()
        fixed_usernames = [username if username[0] == "@" else "@" + username for username in usernames]
        users = (await session.scalars(select(User).where(User.username.in_(fixed_usernames)))).all()
        users_dict = {user.username: user for user in users}
        new_users = []
        for username, nickname, birthday in zip(fixed_usernames, nicknames, birthdays):
            if username in users_dict:
                users_dict[username].nickname = nickname
                users_dict[username].birthday = birthday
            else:
                new_users.append(User(username=username, nickname=nickname, birthday=birthday))
        session.add_all(new_users)
        await session.commit()
        return new_users
