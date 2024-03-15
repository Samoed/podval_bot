from database import Base
from sqlalchemy.orm import Mapped, mapped_column


class Recipes(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str]
    name: Mapped[str] = mapped_column(index=True)

    def __repr__(self) -> str:
        return f"<Recipes(id={self.id}, link={self.link}, name={self.name})>"
