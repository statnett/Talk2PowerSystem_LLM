from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    enabled: bool
    client_id: str | None = Field(alias="clientId")
    authority: str | None
    logout: str | None
    login_redirect: str | None = Field(alias="loginRedirect")
    logout_redirect: str | None = Field(alias="logoutRedirect")
