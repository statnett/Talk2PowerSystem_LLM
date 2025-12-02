from base64 import b64encode
from enum import Enum
from pathlib import Path

import yaml
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Checkpointer
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings
from ttyg.graphdb import GraphDB
from ttyg.tools import (
    AutocompleteSearchTool,
    OntologySchemaAndVocabularyTool,
    RetrievalQueryTool,
    SparqlQueryTool,
)

from talk2powersystemllm.tools import (
    CogniteSession,
    RetrieveDataPointsTool,
    RetrieveTimeSeriesTool,
    NowTool,
)


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

    @model_validator(mode="after")
    def check_password_required_if_username(self) -> "GraphDBSettings":
        username = self.username
        password = self.password
        if username and not password:
            raise ValueError("password is required if username is provided")
        return self


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

    base_url: str
    project: str = "prod"
    client_name: str = "talk2powersystem"
    token_file_path: Path | None = None
    interactive_client_id: str | None = None
    tenant_id: str | None = None

    @model_validator(mode="after")
    def check_credentials(self) -> "CogniteSettings":
        if self.token_file_path and self.interactive_client_id:
            raise ValueError("Both token_file_path and interactive_client_id for Cognite are provided. "
                             "Set only one of them!")
        if self.interactive_client_id and not self.tenant_id:
            raise ValueError("Tenant id is required!")
        return self


class ToolsSettings(BaseModel):
    ontology_schema: OntologySchemaSettings
    autocomplete_search: AutocompleteSearchSettings
    retrieval_search: RetrievalSearchSettings | None = None
    cognite: CogniteSettings | None = None


class LLMType(Enum):
    openai = "openai"
    azure_openai = "azure_openai"


class LLMSettings(BaseSettings):
    model_config = {
        "env_prefix": "LLM_",
    }

    type: LLMType = LLMType.azure_openai
    model: str
    azure_endpoint: str | None = None
    api_version: str | None = None
    temperature: float = Field(default=0, ge=0.0, le=2.0)
    seed: int = Field(default=1)
    timeout: int = Field(default=120, gt=0.0)
    api_key: SecretStr

    @model_validator(mode="after")
    def check_required_if_properties(self) -> "LLMSettings":
        if self.type == LLMType.azure_openai:
            if not self.azure_endpoint:
                raise ValueError("azure_endpoint is required!")
            if not self.api_version:
                raise ValueError("api_version is required!")
        return self


class PromptsSettings(BaseModel):
    assistant_instructions: str


class Talk2PowerSystemAgentSettings(BaseSettings):
    graphdb: GraphDBSettings
    llm: LLMSettings
    tools: ToolsSettings
    prompts: PromptsSettings


def read_config(path_to_yaml_config: Path) -> Talk2PowerSystemAgentSettings:
    def merge_dicts(base: dict, override: dict) -> dict:
        merged = base.copy()
        for k, v in override.items():
            merged[k] = v
        return merged

    config_path = Path(path_to_yaml_config).resolve()

    # Resolve paths relative to config file
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())

    ontology_schema_config = config["tools"]["ontology_schema"]
    rel_path = ontology_schema_config["file_path"]
    abs_path = config_path.parent / rel_path
    ontology_schema_config["file_path"] = str(abs_path.resolve())

    # Copy GraphDB base configuration to the retrieval search configuration
    if "retrieval_search" in config["tools"]:
        config["tools"]["retrieval_search"]["graphdb"] = merge_dicts(
            config["graphdb"],
            config["tools"]["retrieval_search"]["graphdb"]
        )
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


def init_cognite(cognite_settings: CogniteSettings) -> CogniteSession:
    return CogniteSession(
        base_url=cognite_settings.base_url,
        client_name=cognite_settings.client_name,
        project=cognite_settings.project,
        token_file_path=cognite_settings.token_file_path,
        interactive_client_id=cognite_settings.interactive_client_id,
        tenant_id=cognite_settings.tenant_id,
    )


def init_llm(llm_settings: LLMSettings) -> BaseChatModel:
    if llm_settings.type == LLMType.azure_openai:
        return AzureChatOpenAI(
            azure_endpoint=llm_settings.azure_endpoint,
            api_version=llm_settings.api_version,
            model=llm_settings.model,
            temperature=llm_settings.temperature,
            seed=llm_settings.seed,
            timeout=llm_settings.timeout,
            api_key=llm_settings.api_key,
        )
    else:
        return ChatOpenAI(
            model=llm_settings.model,
            temperature=llm_settings.temperature,
            seed=llm_settings.seed,
            timeout=llm_settings.timeout,
            api_key=llm_settings.api_key,
        )


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )


class Talk2PowerSystemAgent:
    agent: CompiledStateGraph
    graphdb_client: GraphDB
    cognite_session: CogniteSession | None = None
    model: BaseChatModel

    def __init__(
        self,
        path_to_yaml_config: Path,
        checkpointer: Checkpointer | None = None,
    ):
        self.settings = read_config(path_to_yaml_config)
        self.graphdb_client = init_graphdb(self.settings.graphdb)

        tools_settings = self.settings.tools
        self.tools: list[BaseTool] = []

        sparql_query_tool = SparqlQueryTool(
            graph=self.graphdb_client,
        )
        self.tools.append(sparql_query_tool)

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
        self.tools.append(autocomplete_search_tool)

        if tools_settings.retrieval_search:
            retrieval_search_settings = tools_settings.retrieval_search
            retrieval_query_tool = RetrievalQueryTool(
                graph=init_graphdb(retrieval_search_settings.graphdb),
                connector_name=retrieval_search_settings.connector_name,
                name=retrieval_search_settings.name,
                description=retrieval_search_settings.description,
                sparql_query_template=retrieval_search_settings.sparql_query_template,
            )
            self.tools.append(retrieval_query_tool)

        if tools_settings.cognite:
            cognite_settings = tools_settings.cognite
            self.cognite_session = init_cognite(cognite_settings)
            self.tools.append(RetrieveTimeSeriesTool(cognite_session=self.cognite_session))
            self.tools.append(RetrieveDataPointsTool(cognite_session=self.cognite_session))

        self.tools.append(NowTool())

        instructions = f"""{self.settings.prompts.assistant_instructions}""".replace(
            "{ontology_schema}", ontology_schema_and_vocabulary_tool.schema_graph.serialize(format="turtle")
        )

        self.model = init_llm(self.settings.llm)
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=instructions,
            checkpointer=checkpointer,
            middleware=[handle_tool_errors],
        )
