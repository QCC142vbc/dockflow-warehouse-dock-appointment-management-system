from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Dock Appointment Scheduling"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./dock_appointments.db"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = "http://localhost:5173"
    SERVICE_AUTH_SECRET: str | None = None
    SERVICE_AUTH_TOKEN_EXPIRE_SECONDS: int = 300
    SERVICE_AUTH_ISSUER: str = "dock-appointment-scheduling"
    SERVICE_AUTH_AUDIENCE: str = "dockflow-operations"
    YMS_SERVICE_AUTH_SECRET: str | None = None
    YMS_SERVICE_AUTH_ISSUER: str = "dockflow-yms"
    YMS_SERVICE_AUTH_AUDIENCE: str = "dock-appointment-scheduling"
    
    JWT_ISSUER: str = "dock-appointment-scheduling"
    JWT_AUDIENCE: str = "dock-appointment-api"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        secret = value.strip()
        if not secret:
            raise ValueError("SECRET_KEY must be configured")
        if len(secret) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters.")
        return secret

    @field_validator("SERVICE_AUTH_SECRET")
    @classmethod
    def validate_service_auth_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        secret = value.strip()
        if not secret or len(secret) < 32:
            raise ValueError("SERVICE_AUTH_SECRET must be at least 32 characters.")
        return secret

    @field_validator("YMS_SERVICE_AUTH_SECRET")
    @classmethod
    def validate_yms_service_auth_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        secret = value.strip()
        if not secret or len(secret) < 32:
            raise ValueError("YMS_SERVICE_AUTH_SECRET must be at least 32 characters.")
        return secret

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()