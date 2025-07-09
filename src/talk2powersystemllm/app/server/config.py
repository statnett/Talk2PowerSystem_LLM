from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    AGENT_CONFIG: Path
    GTG_REFRESH_INTERVAL: int | None = Field(default=30, ge=1,
                                             description="The gtg endpoint refresh interval in seconds")
    TROUBLE_MD_PATH: Path | None = "/code/trouble.md"
    DOCS_URL: str | None = "/docs"
    ROOT_PATH: str | None = "/"
    LOGGING_YAML_FILE: Path | None = "/code/logging.yaml"
    MANIFEST_PATH: Path | None = "/code/git-manifest.yaml"

    PYPROJECT_TOML_PATH: Path | None = "/code/pyproject.toml"


settings = AppSettings()
