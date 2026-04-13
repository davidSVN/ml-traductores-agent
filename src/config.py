from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database (credenciales separadas)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ml_traductores"
    db_user: str = "mluser"
    db_password: str = "mlpassword"

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Anthropic
    anthropic_api_key: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_tracing: str = "false"
    langsmith_project: str = "ml-traductores-agent"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Meta / WhatsApp Business API
    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_verify_token: str = ""
    meta_client_id: str = ""
    meta_client_secret: str = ""
    meta_waba_id: str = ""
    meta_api_version: str = "v21.0"

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "ml-traductores-cotizaciones"
    aws_region: str = "us-east-1"

    # Server
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
