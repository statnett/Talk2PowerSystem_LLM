import logging
from typing import Annotated, Optional

from cachetools import TTLCache
from fastapi import (
    Depends,
    Header,
    HTTPException,
    Request,
    Security,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.app.server.config import AppSettings
from talk2powersystemllm.app.server.services import verify_jwt

logger = logging.getLogger(__name__)


def get_agent_factory(request: Request) -> Talk2PowerSystemAgentFactory:
    return request.app.state.agent_factory


def get_llm_callbacks(request: Request) -> list:
    return request.app.state.callbacks


def get_msal_app(request: Request):
    return getattr(request.app.state, "confidential_app", None)


def get_settings(request: Request) -> AppSettings:
    return request.app.state.settings


def get_security_scheme() -> HTTPBearer:
    return HTTPBearer(auto_error=False)


def get_jwks_cache(request: Request) -> TTLCache:
    return getattr(request.app.state, "jwks_cache", None)


async def conditional_security(
    settings: Annotated[AppSettings, Depends(get_settings)],
    jwks_cache: Annotated[TTLCache, Depends(get_jwks_cache)],
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        get_security_scheme()
    ),
):
    if settings.security.enabled:
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return verify_jwt(settings, jwks_cache, credentials.credentials)
    return None


async def get_cognite_obo_token(
    request: Request,
    settings: Annotated[AppSettings, Depends(get_settings)],
    agent_factory: Annotated[Talk2PowerSystemAgentFactory, Depends(get_agent_factory)],
    authorization: Annotated[Optional[str], Header()] = None,
) -> Optional[str]:
    if not (settings.security.enabled and agent_factory.cognite_enabled):
        return None

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    confidential_app = request.app.state.confidential_app
    scopes = request.app.state.cognite_scopes

    result = confidential_app.acquire_token_silent(scopes, account=None)
    if result and "access_token" in result:
        return result["access_token"]

    logger.debug("Acquiring new Cognite token via OBO flow.")
    result = confidential_app.acquire_token_on_behalf_of(
        user_assertion=authorization,
        scopes=scopes,
    )

    if "access_token" not in result:
        error_desc = result.get(
            "error_description", result.get("error", "Unknown MSAL Error")
        )
        logger.error(f"MSAL OBO Error: {error_desc}")
        raise HTTPException(
            status_code=401, detail=f"Failed to acquire Cognite token: {error_desc}"
        )

    return result["access_token"]


async def get_chat_agent(
    token: Annotated[Optional[str], Depends(get_cognite_obo_token)],
    factory: Annotated[Talk2PowerSystemAgentFactory, Depends(get_agent_factory)],
):
    return factory.get_agent(token)
