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


settings = Settings()