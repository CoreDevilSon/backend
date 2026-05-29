from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "MMD Backend"
    environment: str = "development"
    database_url: str = "sqlite:///./app.db"

    admin_email: str = "admin@example.com"
    admin_password: str = "ChangeMe123!"
    admin_full_name: str = "System Administrator"

    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = ""
    github_repo_branch: str = "main"
    github_image_base_path: str = "uploads/images"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
