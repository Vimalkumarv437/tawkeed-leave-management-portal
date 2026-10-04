from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str
    ENVIRONMENT: str

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Frontend
    FRONTEND_URL: str

    # Login security
    MAX_LOGIN_ATTEMPTS: int
    LOGIN_LOCKOUT_MINUTES: int

    # Tem seed data

    SEED_ADMIN_EMAIL: str | None = None
    SEED_ADMIN_PASSWORD: str | None = None

    SEED_MANAGER_EMAIL: str | None = None
    SEED_MANAGER_PASSWORD: str | None = None

    SEED_EMPLOYEE1_EMAIL: str | None = None
    SEED_EMPLOYEE1_PASSWORD: str | None = None

    SEED_EMPLOYEE2_EMAIL: str | None = None
    SEED_EMPLOYEE2_PASSWORD: str | None = None


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()