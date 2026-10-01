from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DUQB_",
        extra="ignore",
    )

    app_name: str = "Question Bank API"
    environment: str = "development"
    debug: bool = False

    database_url: str = "sqlite:///./duqbank.db"

    secret_key: str = "dev-secret-change-me"
    device_token_salt: str = "device-token-v1"
    admin_session_secret: str = "dev-admin-session-change-me"

    cors_origins: str = "*"

    auto_migrate: bool = False

    rate_limit_per_minute: int = 120
    auth_rate_limit_per_minute: int = 20
    default_page_size: int = 25
    max_page_size: int = 100

    @property
    def cors_origin_list(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if not raw or raw == "*":
            return ["*"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except ValueError:
                parsed = None
            if isinstance(parsed, list) and parsed:
                return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
