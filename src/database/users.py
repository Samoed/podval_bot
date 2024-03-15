from datetime import date

from database.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True)
    nickname: Mapped[str]
    birthday: Mapped[date] = mapped_column(index=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, nickname={self.nickname}, birthday={self.birthday})>"
