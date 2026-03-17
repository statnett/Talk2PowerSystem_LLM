from typing import Annotated

from fastapi import (
    APIRouter,
    Header,
)

router = APIRouter(prefix="/rest/authentication/config", tags=["Auth"])


# noinspection PyUnusedLocal
@router.get(
    "/rest/authentication/config",
    summary="Exposes auth config settings",
    tags=["Auth"],
    response_model=AuthConfig,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_auth_config(
    x_request_id: Annotated[str | None, Header()] = None,
) -> AuthConfig:
    scopes = ["openid", "profile", f"{settings.security.audience}/access_as_user"] if settings.security.enabled else \
        None
    return AuthConfig(
        enabled=settings.security.enabled,
        clientId=settings.security.client_id,
        frontendAppClientId=settings.security.frontend_app_client_id,
        scopes=scopes,
        authority=settings.security.authority,
        logout=settings.security.logout,
        loginRedirect=settings.security.login_redirect,
        logoutRedirect=settings.security.logout_redirect,
    )
