from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    enabled: bool
    client_id: str | None = Field(alias="clientId")
    frontend_app_client_id: str | None = Field(alias="frontendAppClientId")
    scopes: list[str] | None
    authority: str | None
    logout: str | None
    login_redirect: str | None = Field(alias="loginRedirect")
    logout_redirect: str | None = Field(alias="logoutRedirect")
