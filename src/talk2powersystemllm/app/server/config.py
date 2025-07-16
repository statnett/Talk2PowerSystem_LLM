from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    AGENT_CONFIG: Path = Field(description="Path to the agent config yaml file")
    REDIS_HOST: str = Field(description="Redis connection host")
    REDIS_PORT: int = Field(default=6379, description="Redis connection port")
    REDIS_CONNECT_TIMEOUT: int = Field(2, ge=1, description="Redis connect timeout in seconds")
    REDIS_READ_TIMEOUT: int = Field(10, ge=1, description="Redis read timeout in seconds")
    REDIS_HEALTHCHECK_INTERVAL: int = Field(
        3,
        ge=1,
        description="Redis health check interval. "
                    "See https://redis.io/docs/latest/develop/clients/redis-py/produsage/#health-checks"
    )
    REDIS_USERNAME: str = Field(default="default", description="Redis username for basic authentication.")
    REDIS_PASSWORD: SecretStr | None = Field(default=None, description="Redis password for basic authentication.")
    REDIS_TTL: int | None = Field(default=60, ge=1, description="Redis TTL in minutes")
    REDIS_TTL_REFRESH_ON_READ: bool | None = Field(default=True, description="Redis Refresh TTL on read")
    GTG_REFRESH_INTERVAL: int | None = Field(default=30, ge=1,
                                             description="The gtg endpoint refresh interval in seconds")
    TROUBLE_MD_PATH: Path | None = "/code/trouble.md"
    DOCS_URL: str | None = "/docs"
    ROOT_PATH: str | None = "/"
    LOGGING_YAML_FILE: Path | None = "/code/logging.yaml"
    MANIFEST_PATH: Path | None = "/code/git-manifest.yaml"
    PYPROJECT_TOML_PATH: Path | None = "/code/pyproject.toml"


settings = AppSettings()
