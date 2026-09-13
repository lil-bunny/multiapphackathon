from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        extra="ignore",
    )

    UNIPILE_API_KEY: str = ""
    UNIPILE_DSN: str = "api11.unipile.com:14157"
    UNIPILE_ACCOUNT_ID: str = ""
    UNIPILE_WEBHOOK_SECRET: str = ""

    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_SHEET_ID: str = ""
    SLACK_WEBHOOK_URL: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    FIXTURE_MODE: bool = False

    # Connected inbox email — excluded from Reply All CC when sending via Unipile
    UNIPILE_ACCOUNT_EMAIL: str = ""
    DELIVERY_FOLLOWUP_DELAY_SECONDS: int = 10


settings = Settings()
