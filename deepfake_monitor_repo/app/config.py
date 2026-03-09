from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    youtube_api_key: str | None = None
    x_bearer_token: str | None = None

    enable_tiktok: bool = False
    tiktok_access_token: str | None = None
    tiktok_client_key: str | None = None
    tiktok_client_secret: str | None = None

    enable_email_alerts: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None

    enable_sms_alerts: bool = False
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None

    database_url: str
    redis_url: str
    storage_dir: str = "/data/storage"

    whisper_model: str = "small"
    face_model_name: str = "buffalo_l"

    default_monitor_interval_minutes: int = 10
    alert_risk_threshold: float = 0.80
    alert_viral_threshold: float = 0.60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
