from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CSV_PATH: str = "../Breach.csv"
    DB_PATH: str = "./data/breach.db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8
    APP_USERNAME: str = "admin"
    APP_PASSWORD: str = "Terpel2024!"
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
