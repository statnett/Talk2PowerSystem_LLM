from abc import ABCMeta
from datetime import datetime, timezone
from pathlib import Path

import jwt
from cognite.client import CogniteClient
from cognite.client.config import ClientConfig
from cognite.client.credentials import CredentialProvider, OAuthInteractive
from langchain_core.tools import BaseTool


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
            token_file_path: Path | None = None,
            interactive_client_id: str | None = None,
            tenant_id: str | None = None,
    ):
        """
        Configure CogniteSession instance.

        Authentication is determined based on the provided parameters:
            - If `interactive_client_id` is provided, interactive authentication is used (for dev purposes)
            - Otherwise, `token_file_path` must be provided for client credentials authentication.
            The token is renewed, if its about to time out.

        Args:
            base_url (str): Base URL for the Cognite API.
            client_name (str): Name of the client for logging purposes.
            project (str): Cognite Data Fusion project name.
            token_file_path (Path | None): full path on the disk to the cognite token file.
            interactive_client_id (str | None): Client ID for interactive authentication.
            tenant_id (str | None): Azure tenant ID.
        """

        if token_file_path:
            self._token_file_path = token_file_path
            credentials = self._refresh()
        else:
            credentials = OAuthInteractive(
                authority_url=f"https://login.microsoftonline.com/{tenant_id}",
                client_id=interactive_client_id,
                scopes=[f"{base_url}/.default"],
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
        if hasattr(self, "_expires_at") and ((self._expires_at - datetime.now(timezone.utc)).total_seconds() < 60):
            self._refresh()

        return self._client


class BaseCogniteTool(BaseTool, metaclass=ABCMeta):
    """Base tool for interacting with Cognite"""

    cognite_session: CogniteSession
    """The Cognite Session"""
    handle_tool_error: bool = True
