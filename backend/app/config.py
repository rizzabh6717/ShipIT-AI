from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "ShipIT API"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:22058@localhost:5432/shipit",
        validation_alias="DATABASE_URL",
    )

    # CORS - include frontend origins
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"]

    # JWT
    jwt_secret_key: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 5

    # Embeddings - OpenRouter with NVIDIA Nemotron embedding model
    embedding_provider: str = "openrouter"
    embedding_model: str = "nvidia/nemotron-3-embed-1b:free"
    embedding_dimensions: int = 2048
    embedding_api_key: str = ""
    embedding_base_url: str = "https://openrouter.ai/api/v1"

    # LLM - OpenRouter with NVIDIA Nemotron 3 Super
    llm_provider: str = "openrouter"
    llm_model: str = "nvidia/nemotron-3-super-120b-a12b"
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_temperature: float = 0.0

    # AI matching
    ai_match_top_k: int = 10
    ai_match_max_results: int = 5

    @model_validator(mode="after")
    def _ensure_async_driver(self) -> "Settings":
        """Render's managed Postgres provides a plain ``postgresql://`` URL;
        normalize it to the asyncpg driver the async engine requires."""
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self

    @property
    def database_url_sync(self) -> str:
        """SQLAlchemy sync URL (used by Alembic), derived from the async URL."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()