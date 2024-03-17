from datetime import datetime

from database import User
from database.session_manager import with_async_session
from sqlalchemy import delete, extract, select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepo:
    @staticmethod
    @with_async_session
    async def create_user(username: str, nickname: str, birthday: datetime, session: AsyncSession) -> User:
        user = User(username=username, nickname=nickname, birthday=birthday)
        session.add(user)
        await session.commit()
        return user

    @staticmethod
    @with_async_session
    async def get_user_by_id(user_id: int, session: AsyncSession) -> User | None:
        return await session.get(User, user_id)

    @staticmethod
    @with_async_session
    async def create_users(
        usernames: list[str], nickname: list[str], birthdays: list[datetime], session: AsyncSession
    ) -> list[User]:
        users = [
            User(username=username, nickname=nickname, birthday=birthday)
            for username, nickname, birthday in zip(usernames, nickname, birthdays, strict=True)
        ]
        session.add_all(users)
        await session.commit()
        return users

    @staticmethod
    @with_async_session
    async def get_users_with_birthday(birthday: datetime, session: AsyncSession) -> list[User]:
        return (
            await session.scalars(
                select(User).where(
                    extract("day", User.birthday) == birthday.day, extract("month", User.birthday) == birthday.month
                )
            )
        ).all()  # type: ignore

    @staticmethod
    @with_async_session
    async def remove_users(usernames: list[str], session: AsyncSession) -> list[User]:
        to_delete = (await session.scalars(select(User).where(User.username.notin_(usernames)))).all()
        await session.execute(delete(User).where(User.username.notin_(usernames)))
        await session.commit()
        return to_delete  # type: ignore

    @staticmethod
    @with_async_session
    async def create_or_update_users(
        usernames: list[str], nicknames: list[str], birthdays: list[datetime], session: AsyncSession
    ) -> tuple[list[User], list[User]]:
        fixed_usernames = [username if username[0] == "@" else "@" + username for username in usernames]
        users = (await session.scalars(select(User).where(User.username.in_(fixed_usernames)))).all()
        users_dict = {user.username: user for user in users}
        new_users = []
        for username, nickname, birthday in zip(fixed_usernames, nicknames, birthdays, strict=True):
            if username in users_dict:
                users_dict[username].nickname = nickname
                users_dict[username].birthday = birthday
            else:
                new_users.append(User(username=username, nickname=nickname, birthday=birthday))
        session.add_all(new_users)
        await session.commit()
        to_delete_users = []
        if len(fixed_usernames) > 0:
            to_delete_users = await UserRepo.remove_users(fixed_usernames)
        return new_users, to_delete_users
