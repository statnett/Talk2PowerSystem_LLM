from abc import ABCMeta

from cognite.client import CogniteClient, ClientConfig
from cognite.client.credentials import OAuthInteractive
from langchain_core.tools import BaseTool


class BaseCogniteTool(BaseTool, metaclass=ABCMeta):
    """Base tool for interacting with Cognite"""

    cognite_client: CogniteClient
    """The Cognite Client"""


def configure_cognite_client(
        cdf_project: str,
        tenant_id: str,
        client_name: str,
        base_url: str,
        interactive_client_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
) -> CogniteClient:
    """
    Configure a CogniteClient instance.

    Authentication is determined based on the provided parameters:
    - If `interactive_client_id` is provided, interactive authentication is used.
    - Otherwise, `client_id` and `client_secret` must be provided for client credentials authentication.

    Args:
        cdf_project (str): Cognite Data Fusion project name.
        tenant_id (str): Azure tenant ID.
        client_name (str): Name of the client for logging purposes.
        base_url (str): Base URL for the Cognite API.
        interactive_client_id (str | None): Client ID for interactive authentication.
        client_id (str | None): Client ID for client credentials authentication.
        client_secret (str | None): Client secret for client credentials authentication.

    Returns:
        CogniteClient: Configured Cognite client instance.

    Raises:
        ValueError: If neither interactive authentication nor client credentials are properly provided.
    """

    if interactive_client_id:
        creds = OAuthInteractive(
            authority_url=f"https://login.microsoftonline.com/{tenant_id}",
            client_id=interactive_client_id,
            scopes=[f"{base_url}/.default"],
        )
    elif client_id and client_secret:
        creds = OAuthClientCredentials(  # type: ignore
            token_url=f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[f"{base_url}/.default"],
        )
    else:
        raise ValueError(
            "Either 'interactive_client_id' or both 'client_id' and 'client_secret' must be provided."
        )

    config = ClientConfig(
        project=cdf_project,
        client_name=client_name,
        credentials=creds,
        base_url=base_url,
    )
    return CogniteClient(config=config)
