import logging

import requests
from cachetools import cached, TTLCache
from fastapi import (
    HTTPException,
    Security,
)
from fastapi.security import HTTPBearer
from jose import jwt, JWTError, ExpiredSignatureError
from jose.exceptions import JWTClaimsError

from .config import settings

security_scheme = HTTPBearer(auto_error=False)


def get_jwks_uri_and_issuer() -> tuple[str, str]:
    try:
        oid_config = requests.get(settings.security.oidc_discovery_url)
        oid_config.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(
            f"Failed to fetch OpenID Configuration from url {settings.security.oidc_discovery_url}",
            exc_info=err
        )
        raise HTTPException(status_code=500, detail="Fail to fetch OpenID Configuration")

    json_response_body = oid_config.json()
    if "jwks_uri" not in json_response_body:
        raise HTTPException(status_code=500, detail="jwks_uri not found in the OpenID Configuration")
    if "issuer" not in json_response_body:
        raise HTTPException(status_code=500, detail="issuer not found in the OpenID Configuration")

    return json_response_body["jwks_uri"], json_response_body["issuer"]


@cached(cache=TTLCache(maxsize=1, ttl=settings.security.ttl))
def get_jwks_keys_and_issuer() -> tuple[dict, str]:
    jwks_uri, issuer = get_jwks_uri_and_issuer()
    try:
        keys = requests.get(jwks_uri)
        keys.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.error(
            f"Failed to get issuer keys from {jwks_uri}",
            exc_info=err
        )
        raise HTTPException(status_code=500, detail="Fail to get issuer keys")
    return keys.json(), issuer


def verify_jwt(token: str):
    jwks_keys, issuer = get_jwks_keys_and_issuer()
    try:
        return jwt.decode(
            token,
            jwks_keys,
            audience=f"api://{settings.security.client_id}",
            issuer=issuer,
        )
    except ExpiredSignatureError as e:
        logging.warning("Expired Signature", exc_info=e)
        raise HTTPException(status_code=401, detail=f"Expired Signature: {str(e)}")
    except JWTClaimsError as e:
        logging.error("Any claim is invalid in any way", exc_info=e)
        raise HTTPException(status_code=401, detail=f"Any claim is invalid in any way: {str(e)}")
    except JWTError as e:
        logging.error("Signature is invalid", exc_info=e)
        raise HTTPException(status_code=401, detail=f"Signature is invalid: {str(e)}")


async def conditional_security(
        credentials=Security(security_scheme)
):
    if settings.security.enabled:
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return verify_jwt(credentials.credentials)
    return None
