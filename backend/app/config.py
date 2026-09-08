from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rulescope:rulescope@localhost:5432/rulescope"
    redis_url: str = "redis://localhost:6379/0"

    keycloak_server_url: str = "http://localhost:8081"
    keycloak_realm: str = "rulescope"
    keycloak_client_id: str = "rulescope-backend"

    max_upload_size_mb: int = 25
    upload_dir: str = "/data/uploads"
    upload_encryption_key: str = ""

    ipinfo_token: str = ""
    ipwhois_enabled: bool = True
    ipapi_enabled: bool = True
    freeipapi_enabled: bool = True

    # Local/dev-only toggles - never enable these when Keycloak/Redis are reachable.
    auth_disabled: bool = False
    celery_task_always_eager: bool = False

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_server_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
