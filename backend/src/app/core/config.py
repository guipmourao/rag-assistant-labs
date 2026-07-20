from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RAG Assistant Lab"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
    api_key: str | None = None
    root_path: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
