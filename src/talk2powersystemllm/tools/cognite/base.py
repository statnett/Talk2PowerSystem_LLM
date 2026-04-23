from abc import ABCMeta
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
from cognite.client import CogniteClient
from cognite.client.config import ClientConfig
from cognite.client.credentials import (
    CredentialProvider,
    OAuthClientCredentials,
    OAuthInteractive,
)
from langchain_core.tools import BaseTool
from pydantic import SecretStr


class CogniteSession:
    """Wrapper around CogniteClient to keep session from expiring."""

    _client: CogniteClient
    _token_file_path: Path | None
    _expires_at: datetime | None

    def __init__(
        self,
        base_url: str,
        client_name: str,
        project: str,
        interactive_client_id: str | None = None,
        client_id: str | None = None,
        client_secret: SecretStr | None = None,
        tenant_id: str | None = None,
        token_file_path: Path | None = None,
        obo_token: str | None = None,
    ):
        """
        Configure CogniteSession instance.

        Authentication is determined based on the provided parameters:
            - If `interactive_client_id` is provided, interactive authentication is used.
            (for dev purposes)
            - If `client_id` is provided, service account authentication is used.
            (for environment deployments, such as cim.ontotext)
            - If `token_file_path` is provided, it is used for authentication.
            (for environment deployments or RNDP)
            The token is renewed, if its about to time out.
            - Otherwise, `obo_token` must be provided for authentication.

        Args:
            base_url (str): Base URL for the Cognite API.
            client_name (str): Name of the client for logging purposes.
            project (str): Cognite Data Fusion project name.
            interactive_client_id (str | None): Client ID for interactive authentication.
            client_id (str | None): Client ID for authentication.
            client_secret (SecretStr | None): Client secret.
            tenant_id (str | None): Azure tenant ID.
            token_file_path (Path | None): full path on the disk to the Cognite token file.
            obo_token (str | None): OBO authentication token.
        """

        def exactly_one_is_not_none(*args: Any) -> bool:
            return sum(a is not None for a in args) == 1

        if not exactly_one_is_not_none(
            interactive_client_id,
            client_id,
            token_file_path,
            obo_token,
        ):
            raise ValueError(
                "Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
                "'obo_token'!"
            )

        if client_id and not client_secret:
            raise ValueError("'client_secret' is required!")

        if (interactive_client_id or client_id) and not tenant_id:
            raise ValueError("'tenant_id' is required!")

        if obo_token:
            credentials = CredentialProvider.load({"token": obo_token})
        elif token_file_path:
            self._token_file_path = token_file_path
            credentials = self._refresh()
        elif interactive_client_id:
            credentials = OAuthInteractive(
                authority_url=f"https://login.microsoftonline.com/{tenant_id}",
                client_id=interactive_client_id,
                scopes=[f"{base_url}/.default"],
            )
        elif client_id:
            credentials = OAuthClientCredentials(
                token_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                client_id=client_id,
                client_secret=client_secret.get_secret_value(),
                scopes=[f"{base_url}/.default"],
            )
        else:
            raise ValueError(
                "Cannot initialize a Cognite client with the provided configuration!"
            )

        config = ClientConfig(
            base_url=base_url,
            client_name=client_name,
            project=project,
            credentials=credentials,
        )
        self._client = CogniteClient(config=config)

    def _refresh(self):
        with open(self._token_file_path) as token_file:
            token = token_file.read()

        decoded = jwt.decode(token, options={"verify_signature": False})
        self._expires_at = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

        return CredentialProvider.load({"token": token})

    def client(self) -> CogniteClient:
        """
        Get CogniteClient.

        Use for every api request to ensure its not expired.
        """
        if hasattr(self, "_expires_at") and (
            (self._expires_at - datetime.now(timezone.utc)).total_seconds() < 60
        ):
            self._refresh()

        return self._client


class BaseCogniteTool(BaseTool, metaclass=ABCMeta):
    """Base tool for interacting with Cognite"""

    cognite_session: CogniteSession
    """The Cognite Session"""
    handle_tool_error: bool = True
