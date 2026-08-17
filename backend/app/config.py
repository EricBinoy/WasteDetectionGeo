from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/wastedetection"
    cors_origin: str = "http://localhost:3000"
    upload_dir: str = "uploads"
    # comma-separated public base URL used to build image_url values returned to clients
    public_base_url: str = "http://localhost:8000"


settings = Settings()
