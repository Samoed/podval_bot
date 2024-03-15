from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    token: str
    chat_id: int
    admin_chat_id: int
    menu_channel_id: int

    postgres_db: str
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str
    postgres_password: str

    timezone: str = Field(default="Europe/Moscow")
    sheet_id: str
    sheet_name: str

    openai_api_key: str

    recipes_path: str = Field(default="../recipes/result.json")
    supportive_phrases_path: str = Field(default="../phrases/supportive.json")
    user_supportive_phrases_path: str = Field(default="../phrases/user_supportive.json")

    @property
    def database_settings(self) -> Any:
        """
        Get all settings for connection with database.
        """
        return {
            "database": self.postgres_db,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "host": self.postgres_host,
            "port": self.postgres_port,
        }

    @property
    def database_uri(self) -> str:
        """
        Get uri for connection with database.
        """
        return "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}".format(
            **self.database_settings,
        )

    @property
    def database_uri_sync(self) -> str:
        """
        Get uri for connection with database.
        """
        return "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            **self.database_settings,
        )
