from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    model_config = {
        "env_prefix": "SECURITY_",
    }

    enabled: bool = Field(
        default=False,
        description="Indicates if security is enabled. The value is also exposed to the UI."
    )
    client_id: str | None = Field(
        default=None,
        description="The registered application (client) ID. The value is also exposed to the UI."
    )
    frontend_app_client_id: str | None = Field(
        default=None,
        description="The registered frontend application (client) ID. The value is also exposed to the UI."
    )
    oidc_discovery_url: str | None = Field(
        default=None,
        description="OpenID Connect Discovery URL."
    )
    audience: str | None = Field(
        default=None,
        description="The expected audience of the security tokens"
    )
    issuer: str | None = Field(
        default=None,
        description="The expected issuer of the security tokens"
    )
    ttl: int = Field(
        default=86400,
        ge=1,
        description="Indicates how many seconds to cache the public keys and the issuer "
                    "obtained from the OpenID Configuration endpoint."
    )

    authority: str | None = Field(
        default=None,
        description="The authority URL used for authentication. The value is exposed to the UI."
    )
    logout: str | None = Field(
        default=None,
        description="The logout endpoint URL. The value is exposed to the UI."
    )
    login_redirect: str | None = Field(
        default=None,
        description="The URL to redirect to after a successful login. The value is exposed to the UI."
    )
    logout_redirect: str | None = Field(
        default=None,
        description="The URL to redirect to after logout. The value is exposed to the UI."
    )

    @model_validator(mode="after")
    def check_required_fields_and_set_default_oidc_discovery_url(self) -> "SecuritySettings":
        if self.enabled and ((not self.client_id) or (not self.frontend_app_client_id) or (not self.authority)
                             or (not self.logout) or (not self.login_redirect)
                             or (not self.logout_redirect) or (not self.audience) or (not self.issuer)):
            raise ValueError("If security is enabled, the following fields are required: "
                             "client_id, frontend_app_client_id, authority, logout, "
                             "login_redirect, logout_redirect, audience, issuer!")
        if self.enabled and not self.oidc_discovery_url:
            self.oidc_discovery_url = (
                self.authority.rstrip("/") + "/v2.0/.well-known/openid-configuration"
            )
        return self


class RedisSettings(BaseSettings):
    model_config = {
        "env_prefix": "REDIS_",
    }

    host: str = Field(description="Redis connection host")
    port: int = Field(default=6379, description="Redis connection port")
    connect_timeout: int = Field(2, ge=1, description="Redis connect timeout in seconds")
    read_timeout: int = Field(10, ge=1, description="Redis read timeout in seconds")
    healthcheck_interval: int = Field(
        3,
        ge=1,
        description="Redis health check interval. "
                    "See https://redis.io/docs/latest/develop/clients/redis-py/produsage/#health-checks"
    )
    username: str = Field(default="default", description="Redis username for basic authentication.")
    password: SecretStr | None = Field(default=None, description="Redis password for basic authentication.")
    ttl: int = Field(default=60, ge=1, description="Redis TTL in minutes")
    ttl_refresh_on_read: bool = Field(default=True, description="Redis Refresh TTL on read")


class AppSettings(BaseSettings):
    model_config = {
        "env_nested_delimiter": "_",
        "env_nested_max_split": 1,
    }

    agent_config: Path = Field(description="Path to the agent config yaml file")
    redis: RedisSettings
    security: SecuritySettings = SecuritySettings()
    gtg_refresh_interval: int = Field(default=30, ge=1,
                                      description="The __gtg endpoint refresh interval in seconds")
    about_refresh_interval: int = Field(default=30, ge=1,
                                        description="The __about endpoint refresh interval in seconds")
    trouble_md_path: Path = "/code/trouble.md"
    docs_url: str = "/docs"
    root_path: str = "/"
    logging_yaml_file: Path = "/code/logging.yaml"
    manifest_path: Path = "/code/git-manifest.yaml"
    pyproject_toml_path: Path = "/code/pyproject.toml"
    diagrams_path: Path = '/code/diagrams/'
    frontend_context_path: str = "/"


settings = AppSettings()
