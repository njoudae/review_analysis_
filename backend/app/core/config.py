from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Customer Experience Intelligence"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    api_key: str = Field(default="change-me-in-production", alias="APP_API_KEY")
    database_url: str = Field(default="sqlite:///./cx_reviews.db", alias="DATABASE_URL")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    apify_token: str | None = Field(default=None, alias="APIFY_TOKEN")
    actor_id: str | None = Field(default=None, alias="ACTOR_ID")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")
    dashboard_url: str | None = Field(default=None, alias="DASHBOARD_URL")

    worker_poll_seconds: int = Field(default=5, alias="WORKER_POLL_SECONDS")
    external_max_attempts: int = Field(default=3, alias="EXTERNAL_MAX_ATTEMPTS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @model_validator(mode="after")
    def reject_insecure_production_defaults(self):
        if self.environment.lower() == "production" and (
            self.api_key == "change-me-in-production" or len(self.api_key) < 24
        ):
            raise ValueError("APP_API_KEY must be a unique value of at least 24 characters in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
