from abc import ABCMeta

from cognite.client import CogniteClient
from langchain_core.tools import BaseTool


class BaseCogniteTool(BaseTool, metaclass=ABCMeta):
    """Base tool for interacting with Cognite"""

    cognite_client: CogniteClient
    """The Cognite Client"""
