from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    PROJECT_NAME: str
    PROJECT_VERSION: str

    DEBUG: bool

    API_V1_PREFIX: str

    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_PROVIDER: str = "mock"

    # ==========================
    # Mail
    # ==========================

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""

    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "BusinessOS AI"

    MAIL_SERVER: str = "sandbox.smtp.mailtrap.io"
    MAIL_PORT: int = 2525

    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",   # Tanınmayan env değişkenlerini görmezden gel
    )

    EMBEDDING_PROVIDER: str = "mock"

    # ==========================
    # Time zone / background jobs
    # ==========================

    # Appointment dates and times are stored without a time zone and are
    # interpreted in this zone (reminder scheduling, "now" comparisons).
    APP_TIMEZONE: str = "Europe/Istanbul"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    # Appointment reminders
    REMINDER_SCAN_INTERVAL_SECONDS: int = 300
    REMINDER_MIN_LEAD_MINUTES: int = 60
    REMINDER_MAX_ATTEMPTS: int = 3
    MAIL_TIMEOUT_SECONDS: int = 10

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
