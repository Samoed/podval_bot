from database.recipes import Recipes
from database.session_manager import with_async_session
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class RecipiesRepo:
    @staticmethod
    @with_async_session
    async def add_recipe(name: str, link: str, session: AsyncSession) -> Recipes:
        recipe = Recipes(name=name, link=link)
        session.add(recipe)
        await session.commit()
        return recipe

    @staticmethod
    @with_async_session
    async def add_recipes(recipes: list[Recipes], session: AsyncSession) -> list[Recipes]:
        session.add_all(recipes)
        await session.commit()
        return recipes

    @staticmethod
    @with_async_session
    async def count_recipes(session: AsyncSession) -> int:
        query = select(func.count(Recipes.id))
        return (await session.execute(query)).scalar()

    @staticmethod
    @with_async_session
    async def search_recipe_by_name(name: str, session: AsyncSession) -> list[Recipes]:
        query = select(Recipes).where(Recipes.name.like(f"%{name.lower()}%"))
        return (await session.execute(query)).scalars().all()
