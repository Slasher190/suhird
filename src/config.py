from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "suhird"
    postgres_user: str = "suhird_user"
    postgres_password: str = "suhird_pass_2024"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6335

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6380

    # MemPalace
    mempalace_url: str = "http://localhost:8001"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "nomic-embed-text"

    # Storage
    storage_type: str = "local"
    local_storage_path: str = "./photos"

    # Security
    jwt_secret: str = "change_me_to_a_real_secret_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    encryption_key: str = "change_me_to_a_32_byte_base64_key_now"

    # OpenClaw Gateway
    openclaw_gateway_url: str = "http://localhost:18789"
    openclaw_gateway_token: str = ""

    # Suhird API token
    suhird_api_token: str = "suhird_api_token_change_me"

    # Known numbers
    known_personal_numbers: str = ""
    known_team_numbers: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def all_known_numbers(self) -> set[str]:
        numbers: set[str] = set()
        for field in [self.known_personal_numbers, self.known_team_numbers]:
            if field:
                numbers.update(n.strip() for n in field.split(",") if n.strip())
        return numbers

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
