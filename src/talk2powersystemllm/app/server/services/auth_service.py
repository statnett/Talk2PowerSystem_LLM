import logging

import requests
from cachetools import TTLCache
from fastapi import HTTPException
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError

from talk2powersystemllm.app.server.config import AppSettings

logger = logging.getLogger(__name__)


def get_jwks_uri(settings: AppSettings) -> str:
    try:
        oid_config = requests.get(settings.security.oidc_discovery_url)
        oid_config.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception(
            f"Failed to fetch OpenID Configuration from url {settings.security.oidc_discovery_url}"
        )
        raise HTTPException(
            status_code=500, detail="Fail to fetch OpenID Configuration"
        )

    json_response_body = oid_config.json()
    if "jwks_uri" not in json_response_body:
        raise HTTPException(
            status_code=500, detail="jwks_uri not found in the OpenID Configuration"
        )

    return json_response_body["jwks_uri"]


def get_jwks_keys(settings: AppSettings, jwks_cache: TTLCache) -> dict:
    if "keys" in jwks_cache:
        return jwks_cache["keys"]

    jwks_uri = get_jwks_uri(settings)
    try:
        response = requests.get(jwks_uri)
        response.raise_for_status()

        keys = response.json()

        jwks_cache["keys"] = keys  # Save to the injected cache
        return keys
    except requests.exceptions.HTTPError:
        logger.exception(f"Failed to get issuer keys from {jwks_uri}")
        raise HTTPException(status_code=500, detail="Fail to get issuer keys")


def verify_jwt(settings: AppSettings, jwks_cache: TTLCache, token: str):
    jwks_keys = get_jwks_keys(settings, jwks_cache)
    try:
        return jwt.decode(
            token,
            jwks_keys,
            audience=settings.security.audience,
            issuer=settings.security.issuer,
        )
    except ExpiredSignatureError as e:
        logger.warning("Expired Signature", exc_info=e)
        raise HTTPException(status_code=401, detail=f"Expired Signature: {str(e)}")
    except JWTClaimsError as e:
        logger.warning("Any claim is invalid in any way", exc_info=e)
        raise HTTPException(
            status_code=401, detail=f"Any claim is invalid in any way: {str(e)}"
        )
    except JWTError as e:
        logger.warning("Signature is invalid", exc_info=e)
        raise HTTPException(status_code=401, detail=f"Signature is invalid: {str(e)}")
