from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    youtube_api_key: str | None = None
    x_bearer_token: str | None = None

    database_url: str
    redis_url: str
    storage_dir: str = "/data/storage"

    whisper_model: str = "small"
    hf_token: str | None = None
    face_model_name: str = "buffalo_l"
    secret_key: str = "change-me"
    app_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
