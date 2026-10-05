from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    #App
    APP_NAME: str = "Simple Cache Service"
    API_V1_PREFIX: str = "/api/v1"
    API_PORT: int

    #Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int



settings = Settings()
