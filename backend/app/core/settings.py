from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource, PydanticBaseSettingsSource


class CustomEnvSettingsSource(EnvSettingsSource):
    def decode_complex_value(self, field_name: str, field: FieldInfo, value: Any) -> Any:
        return value


class CustomDotEnvSettingsSource(DotEnvSettingsSource):
    def decode_complex_value(self, field_name: str, field: FieldInfo, value: Any) -> Any:
        return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore", case_sensitive=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type["BaseSettings"],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CustomEnvSettingsSource(settings_cls),
            CustomDotEnvSettingsSource(settings_cls),
            file_secret_settings,
        )

    # Postgres
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432

    # MinIO
    minio_root_user: str
    minio_root_password: SecretStr
    minio_bucket: str
    minio_endpoint: str
    minio_use_ssl: bool = False

    # App
    app_env: str = "dev"
    app_secret_key: SecretStr
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    cors_origins: list[str] = Field(default_factory=list)

    # Observability
    log_level: str = "INFO"
    metrics_enabled: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("app_secret_key")
    @classmethod
    def secret_long_enough(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters")
        return v

    @property
    def db_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
