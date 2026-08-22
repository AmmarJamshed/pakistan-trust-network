from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ptn_env: str = Field(default="development", alias="PTN_ENV")
    ptn_debug: bool = Field(default=False, alias="PTN_DEBUG")
    ptn_app_name: str = Field(default="Pakistan Trust Network", alias="PTN_APP_NAME")
    ptn_api_url: str = Field(default="http://localhost:8000", alias="PTN_API_URL")
    ptn_frontend_url: str = Field(default="http://localhost:3000", alias="PTN_FRONTEND_URL")
    ptn_cors_origins: str = Field(
        default="http://localhost:3000",
        alias="PTN_CORS_ORIGINS",
    )

    database_url: str = Field(
        default="postgresql+psycopg://ptn:ptn_dev_password@localhost:5432/ptn",
        alias="DATABASE_URL",
    )

    jwt_secret: str = Field(default="dev-only-change-me-please-32chars!", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=14, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    encryption_key: str = Field(
        default="dev-only-fernet-key-not-for-prod!!",
        alias="ENCRYPTION_KEY",
    )

    ledger_validator_id: str = Field(default="ptn:validator:genesis", alias="LEDGER_VALIDATOR_ID")
    ledger_node_name: str = Field(default="ptn-node-primary", alias="LEDGER_NODE_NAME")

    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    seed_demo_data: bool = Field(default=True, alias="SEED_DEMO_DATA")
    demo_password: str = Field(default="DemoPass123!", alias="DEMO_PASSWORD")
    admin_email: str = Field(default="admin@ptn.demo", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="AdminPass123!", alias="ADMIN_PASSWORD")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ptn_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ptn_env.lower() == "production"

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
