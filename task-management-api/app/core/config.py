from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/taskdb"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
