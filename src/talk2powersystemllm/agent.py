from base64 import b64encode
from pathlib import Path
from typing import Any

import yaml
from cognite.client import CogniteClient
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Checkpointer
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings
from ttyg.graphdb import GraphDB
from ttyg.tools import (
    AutocompleteSearchTool,
    NowTool,
    OntologySchemaAndVocabularyTool,
    RetrievalQueryTool,
    SparqlQueryTool,
)

from talk2powersystemllm.tools import configure_cognite_client, RetrieveDataPointsTool, RetrieveTimeSeriesTool


class GraphDBSettings(BaseSettings):
    model_config = {
        "env_prefix": "GRAPHDB_",
    }

    base_url: str
    repository_id: str
    connect_timeout: int = Field(default=2, ge=1)
    read_timeout: int = Field(default=10, ge=1)
    sparql_timeout: int = Field(default=15, ge=1)
    username: str | None = None
    password: SecretStr | None = None

    @classmethod
    @model_validator(mode="after")
    def check_password_required_if_username(cls, values: Any) -> Any:
        username = values.username
        password = values.password
        if username and not password:
            raise ValueError("password is required if username is provided")
        return values


class OntologySchemaSettings(BaseModel):
    file_path: Path


class AutocompleteSearchSettings(BaseModel):
    property_path: str
    sparql_query_template: str | None = None


class RetrievalSearchSettings(BaseModel):
    graphdb: GraphDBSettings
    connector_name: str
    name: str
    description: str
    sparql_query_template: str


class CogniteSettings(BaseModel):
    model_config = {
        "env_prefix": "COGNITE_",
    }

    cdf_project: str
    tenant_id: str
    client_name: str
    base_url: str
    interactive_client_id: str | None = None
    client_id: str | None = None
    client_secret: SecretStr | None = None

    @classmethod
    @model_validator(mode="after")
    def check_credentials(cls, values: Any) -> Any:
        if values.client_id and values.interactive_client_id:
            raise ValueError("Both client_id and interactive_client_id for Cognite are provided. Set only one of them!")
        if values.client_id and not values.client_secret:
            raise ValueError("Client secret for Cognite is not set!")
        return values


class ToolsSettings(BaseModel):
    ontology_schema: OntologySchemaSettings
    autocomplete_search: AutocompleteSearchSettings
    retrieval_search: RetrievalSearchSettings | None = None
    cognite: CogniteSettings | None = None


class LLMSettings(BaseSettings):
    model_config = {
        "env_prefix": "LLM_",
    }

    azure_endpoint: str
    model: str
    api_version: str
    temperature: float = Field(default=0, ge=0.0, le=2.0)
    seed: int = Field(default=1)
    timeout: int = Field(default=120, gt=0.0)
    api_key: SecretStr


class PromptsSettings(BaseModel):
    assistant_instructions: str


class Talk2PowerSystemAgentSettings(BaseSettings):
    graphdb: GraphDBSettings
    llm: LLMSettings
    tools: ToolsSettings
    prompts: PromptsSettings


def read_config(path_to_yaml_config: Path) -> Talk2PowerSystemAgentSettings:
    config_path = Path(path_to_yaml_config).resolve()

    # Resolve paths relative to config file
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())

    ontology_schema_config = config["tools"]["ontology_schema"]
    rel_path = ontology_schema_config["file_path"]
    abs_path = config_path.parent / rel_path
    ontology_schema_config["file_path"] = str(abs_path.resolve())
    return Talk2PowerSystemAgentSettings(**config)


def init_graphdb(graphdb_settings: GraphDBSettings) -> GraphDB:
    kwargs = {
        "base_url": graphdb_settings.base_url,
        "repository_id": graphdb_settings.repository_id,
        "connect_timeout": graphdb_settings.connect_timeout,
        "read_timeout": graphdb_settings.read_timeout,
        "sparql_timeout": graphdb_settings.sparql_timeout,
    }
    if graphdb_settings.username:
        kwargs.update({
            "auth_header": "Basic " + b64encode(
                f"{graphdb_settings.username}:{graphdb_settings.password.get_secret_value()}".encode("ascii")
            ).decode()
        })
    return GraphDB(**kwargs)


def init_cognite(cognite_settings: CogniteSettings) -> CogniteClient:
    return configure_cognite_client(
        cdf_project=cognite_settings.cdf_project,
        tenant_id=cognite_settings.tenant_id,
        client_name=cognite_settings.client_name,
        base_url=cognite_settings.base_url,
        interactive_client_id=cognite_settings.interactive_client_id,
    )


def init_llm(llm_settings: LLMSettings) -> BaseChatModel:
    return AzureChatOpenAI(
        azure_endpoint=llm_settings.azure_endpoint,
        api_version=llm_settings.api_version,
        model=llm_settings.model,
        temperature=llm_settings.temperature,
        seed=llm_settings.seed,
        timeout=llm_settings.timeout,
        api_key=llm_settings.api_key,
    )


class Talk2PowerSystemAgent:
    agent: CompiledStateGraph
    graphdb_client: GraphDB
    cognite_client: CogniteClient | None = None
    model: BaseChatModel

    def __init__(
            self,
            path_to_yaml_config: Path,
            checkpointer: Checkpointer | None = None,
    ):
        settings = read_config(path_to_yaml_config)
        self.graphdb_client = init_graphdb(settings.graphdb)

        tools_settings = settings.tools
        tools: list[BaseTool] = []

        sparql_query_tool = SparqlQueryTool(
            graph=self.graphdb_client,
        )
        tools.append(sparql_query_tool)

        ontology_schema_and_vocabulary_tool = OntologySchemaAndVocabularyTool(
            graph=self.graphdb_client,
            ontology_schema_file_path=tools_settings.ontology_schema.file_path,
        )

        autocomplete_search_settings = tools_settings.autocomplete_search
        autocomplete_search_kwargs = {
            "property_path": autocomplete_search_settings.property_path,
        }
        if autocomplete_search_settings.sparql_query_template:
            autocomplete_search_kwargs.update({
                "sparql_query_template": autocomplete_search_settings.sparql_query_template,
            })
        autocomplete_search_tool = AutocompleteSearchTool(
            graph=self.graphdb_client,
            **autocomplete_search_kwargs,
        )
        tools.append(autocomplete_search_tool)

        if tools_settings.retrieval_search:
            retrieval_search_settings = tools_settings.retrieval_search
            retrieval_query_tool = RetrievalQueryTool(
                graph=init_graphdb(retrieval_search_settings.graphdb),
                connector_name=retrieval_search_settings.connector_name,
                name=retrieval_search_settings.name,
                description=retrieval_search_settings.description,
                sparql_query_template=retrieval_search_settings.sparql_query_template,
            )
            tools.append(retrieval_query_tool)

        if tools_settings.cognite:
            cognite_settings = tools_settings.cognite
            self.cognite_client = init_cognite(cognite_settings)
            tools.append(RetrieveTimeSeriesTool(cognite_client=self.cognite_client))
            tools.append(RetrieveDataPointsTool(cognite_client=self.cognite_client))

        tools.append(NowTool())

        instructions = f"""{settings.prompts.assistant_instructions}""".replace(
            "{ontology_schema}", ontology_schema_and_vocabulary_tool.schema_graph.serialize(format="turtle")
        )

        self.model = init_llm(settings.llm)
        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            prompt=instructions,
            checkpointer=checkpointer,
        )
