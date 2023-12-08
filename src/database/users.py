from datetime import date

from sqlalchemy.orm import Mapped, mapped_column

from src.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(index=True)
    nickname: Mapped[str]
    birthday: Mapped[date] = mapped_column(index=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, nickname={self.nickname}, birthday={self.birthday})>"
