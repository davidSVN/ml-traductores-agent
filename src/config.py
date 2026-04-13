from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://mluser:mlpassword@localhost:5432/ml_traductores"

    # Anthropic
    anthropic_api_key: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_tracing: str = "false"
    langsmith_project: str = "ml-traductores-agent"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # WhatsApp
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_api_version: str = "v21.0"

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
