from base64 import b64encode
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from langchain.agents import create_agent
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
    BaseGraphDBTool,
    OntologySchemaAndVocabularyTool,
    RetrievalQueryTool,
    SparqlQueryTool,
)

from talk2powersystemllm.tools import (
    CogniteSession,
    GraphicsTool,
    NowTool,
    RetrieveDataPointsTool,
    RetrieveTimeSeriesTool,
)


class GraphDBSettings(BaseSettings):
    model_config = {
        "env_prefix": "GRAPHDB_",
    }

    base_url: str
    repository_id: str
    connect_timeout: int = Field(default=2, ge=1)
    read_timeout: int = Field(default=10, ge=1)
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


class DisplayGraphicsSettings(BaseModel):
    sparql_query_template: str


class RetrievalSearchSettings(BaseModel):
    graphdb_repository_id: str
    connector_name: str
    name: str
    description: str
    sparql_query_template: str


class CogniteSettings(BaseSettings):
    model_config = {
        "env_prefix": "COGNITE_",
    }

    base_url: str
    project: str = "prod"
    client_name: str = "talk2powersystem"
    interactive_client_id: str | None = None
    client_id: str | None = None
    client_secret: SecretStr | None = None
    tenant_id: str | None = None
    token_file_path: Path | None = None
    obo_client_secret: SecretStr | None = None

    @model_validator(mode="after")
    def check_credentials(self) -> "CogniteSettings":
        def exactly_one_is_not_none(*args: Any) -> bool:
            return sum(a is not None for a in args) == 1

        if not exactly_one_is_not_none(
            self.interactive_client_id,
            self.client_id,
            self.token_file_path,
            self.obo_client_secret,
        ):
            raise ValueError(
                "Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
                "'obo_client_secret'!"
            )

        if self.client_id and not self.client_secret:
            raise ValueError("'client_secret' is required!")

        if (self.interactive_client_id or self.client_id) and not self.tenant_id:
            raise ValueError("'tenant_id' is required!")
        return self


class ToolsSettings(BaseModel):
    ontology_schema: OntologySchemaSettings
    autocomplete_search: AutocompleteSearchSettings
    display_graphics: DisplayGraphicsSettings | None = None
    retrieval_search: RetrievalSearchSettings | None = None
    cognite: CogniteSettings | None = None


class LLMType(Enum):
    openai = "openai"
    azure_openai = "azure_openai"
    hugging_face = "hugging_face"


class LLMSettings(BaseSettings):
    model_config = {
        "env_prefix": "LLM_",
    }

    type: LLMType = LLMType.azure_openai
    model: str
    azure_endpoint: str | None = None
    api_version: str | None = None
    hugging_face_endpoint: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    use_responses_api: bool | None = None
    seed: int | None = None
    reasoning_effort: str | None = None
    timeout: int = Field(default=120, gt=0.0)
    api_key: SecretStr

    @model_validator(mode="after")
    def validate_model(self) -> "LLMSettings":
        if self.type == LLMType.azure_openai:
            if not self.azure_endpoint:
                raise ValueError("azure_endpoint is required!")
            if not self.api_version:
                raise ValueError("api_version is required!")
        elif self.type == LLMType.hugging_face:
            if not self.hugging_face_endpoint:
                raise ValueError("hugging_face_endpoint is required!")

        if self.use_responses_api and self.seed is not None:
            raise ValueError(
                "`seed` is not supported by the Responses API. "
                "Please, remove it, or use the Completions API."
            )

        return self


class PromptsSettings(BaseModel):
    assistant_instructions: str


class Talk2PowerSystemAgentSettings(BaseSettings):
    graphdb: GraphDBSettings
    llm: LLMSettings
    tools: ToolsSettings
    prompts: PromptsSettings


class Talk2PowerSystemAgentFactory:
    instructions: str
    model: BaseChatModel
    checkpointer: Checkpointer | None = None
    graphdb_client: GraphDB
    cognite_session: CogniteSession | None
    tools: list[BaseTool]
    tools_metadata: dict[str, dict[str, Any]]
    tool_name_to_gdb_repository_id: dict[str, str]
    advanced_tools: set[str]
    __agent: CompiledStateGraph | None
    __settings: Talk2PowerSystemAgentSettings

    def __init__(
        self,
        path_to_yaml_config: Path,
        checkpointer: Checkpointer | None = None,
    ):
        self.__init_settings(path_to_yaml_config)
        self.checkpointer = checkpointer
        self.__init_model()
        self.__init_graphdb()
        self.__init_instructions()
        self.__init_tools()

    def __init_settings(self, path_to_yaml_config: Path) -> None:
        config_path = Path(path_to_yaml_config).resolve()

        # Resolve paths relative to config file
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f.read())

        ontology_schema_config = config["tools"]["ontology_schema"]
        rel_path = ontology_schema_config["file_path"]
        abs_path = config_path.parent / rel_path
        ontology_schema_config["file_path"] = str(abs_path.resolve())

        self.__settings = Talk2PowerSystemAgentSettings(**config)

    def __init_graphdb(self) -> None:
        def basic_auth_token(settings: GraphDBSettings) -> str:
            return b64encode(
                f"{settings.username}:{settings.password.get_secret_value()}".encode(
                    "ascii"
                )
            ).decode()

        graphdb_settings = self.__settings.graphdb
        kwargs = {
            "base_url": graphdb_settings.base_url,
            "connect_timeout": graphdb_settings.connect_timeout,
            "read_timeout": graphdb_settings.read_timeout,
        }
        if graphdb_settings.username:
            kwargs.update(
                {"auth_header": f"Basic {basic_auth_token(graphdb_settings)}"}
            )
        self.graphdb_client = GraphDB(**kwargs)

    def __init_tools(self) -> None:
        tools_settings = self.__settings.tools
        self.tools: list[BaseTool] = []
        self.tools_metadata: dict[str, dict[str, Any]] = dict()

        sparql_query_tool = SparqlQueryTool(
            graph=self.graphdb_client,
            graphdb_repository_id=self.graphdb_repository_id,
        )
        self.tools.append(sparql_query_tool)
        self.tools_metadata["sparql_query"] = {"enabled": True}

        autocomplete_search_settings = tools_settings.autocomplete_search
        autocomplete_search_kwargs = {
            "property_path": autocomplete_search_settings.property_path,
        }
        if autocomplete_search_settings.sparql_query_template:
            autocomplete_search_kwargs.update(
                {
                    "sparql_query_template": autocomplete_search_settings.sparql_query_template,
                }
            )
        autocomplete_search_tool = AutocompleteSearchTool(
            graph=self.graphdb_client,
            graphdb_repository_id=self.graphdb_repository_id,
            **autocomplete_search_kwargs,
        )
        self.tools.append(autocomplete_search_tool)
        self.tools_metadata["autocomplete_search"] = {
            "enabled": True,
            "property_path": autocomplete_search_tool.property_path,
            "sparql_query_template": autocomplete_search_tool.sparql_query_template,
        }

        display_graphics_tool = GraphicsTool(
            graph=self.graphdb_client,
            graphdb_repository_id=self.graphdb_repository_id,
        )
        self.tools.append(display_graphics_tool)
        self.tools_metadata["display_graphics"] = {
            "enabled": True,
            "sparql_query_template": display_graphics_tool.sparql_query_template,
        }

        sample_sparql_queries_enabled = bool(tools_settings.retrieval_search)
        sample_sparql_queries_meta: dict[str, Any] = {
            "enabled": sample_sparql_queries_enabled
        }
        if sample_sparql_queries_enabled:
            retrieval_search_settings = tools_settings.retrieval_search
            retrieval_query_tool = RetrievalQueryTool(
                graph=self.graphdb_client,
                graphdb_repository_id=retrieval_search_settings.graphdb_repository_id,
                connector_name=retrieval_search_settings.connector_name,
                name=retrieval_search_settings.name,
                description=retrieval_search_settings.description,
                sparql_query_template=retrieval_search_settings.sparql_query_template,
            )
            self.tools.append(retrieval_query_tool)
            sample_sparql_queries_meta.update(
                {
                    "sparql_query_template": retrieval_query_tool.sparql_query_template,
                    "connector_name": retrieval_query_tool.connector_name,
                }
            )
        self.tools_metadata["sample_sparql_queries"] = sample_sparql_queries_meta

        now_tool = NowTool()
        self.tools.append(now_tool)
        self.tools_metadata["now"] = {"enabled": True}

        cognite_settings = tools_settings.cognite
        cognite_enabled = bool(cognite_settings)
        cognite_meta: dict[str, Any] = {"enabled": cognite_enabled}

        self.cognite_session = None
        self.__agent = None
        if cognite_enabled:
            cognite_meta.update(
                {
                    "base_url": cognite_settings.base_url,
                    "project": cognite_settings.project,
                    "client_name": cognite_settings.client_name,
                }
            )

            if (
                cognite_settings.interactive_client_id
                or cognite_settings.client_id
                or cognite_settings.token_file_path
            ):
                self.cognite_session = self.__init_cognite()
                self.tools.append(
                    RetrieveTimeSeriesTool(cognite_session=self.cognite_session)
                )
                self.tools.append(
                    RetrieveDataPointsTool(cognite_session=self.cognite_session)
                )
                model_with_tools = self.model.bind_tools(
                    self.tools, parallel_tool_calls=False
                )
                self.__agent = create_agent(
                    model=model_with_tools,
                    tools=self.tools,
                    system_prompt=self.instructions,
                    checkpointer=self.checkpointer,
                )
        else:
            model_with_tools = self.model.bind_tools(
                self.tools, parallel_tool_calls=False
            )
            self.__agent = create_agent(
                model=model_with_tools,
                tools=self.tools,
                system_prompt=self.instructions,
                checkpointer=self.checkpointer,
            )

        self.tools_metadata["retrieve_data_points"] = cognite_meta
        self.tools_metadata["retrieve_time_series"] = cognite_meta

        self.tool_name_to_gdb_repository = {
            tool.name: tool.graphdb_repository_id
            for tool in self.tools
            if isinstance(tool, BaseGraphDBTool)
        }
        self.advanced_tools = {now_tool.name} | {
            tool.name
            for tool in self.tools
            if isinstance(tool, BaseGraphDBTool) and tool.name != sparql_query_tool.name
        }

    def __init_instructions(self) -> None:
        settings = self.__settings
        ontology_schema_and_vocabulary_tool = OntologySchemaAndVocabularyTool(
            graph=self.graphdb_client,
            ontology_schema_file_path=settings.tools.ontology_schema.file_path,
        )
        self.instructions = f"""{settings.prompts.assistant_instructions}""".replace(
            "{ontology_schema}",
            ontology_schema_and_vocabulary_tool.schema_graph.serialize(format="turtle"),
        )

    def __init_model(self) -> None:
        llm_settings = self.__settings.llm
        if llm_settings.type == LLMType.azure_openai:
            self.model = AzureChatOpenAI(
                azure_endpoint=llm_settings.azure_endpoint,
                api_version=llm_settings.api_version,
                model=llm_settings.model,
                temperature=llm_settings.temperature,
                use_responses_api=llm_settings.use_responses_api,
                reasoning_effort=llm_settings.reasoning_effort,
                store=False,
                seed=llm_settings.seed,
                timeout=llm_settings.timeout,
                api_key=llm_settings.api_key,
            )
        elif llm_settings.type == LLMType.openai:
            self.model = ChatOpenAI(
                model=llm_settings.model,
                temperature=llm_settings.temperature,
                use_responses_api=llm_settings.use_responses_api,
                reasoning_effort=llm_settings.reasoning_effort,
                store=False,
                seed=llm_settings.seed,
                timeout=llm_settings.timeout,
                api_key=llm_settings.api_key,
            )
        else:
            self.model = ChatOpenAI(
                base_url=llm_settings.hugging_face_endpoint,
                model=llm_settings.model,
                temperature=llm_settings.temperature,
                use_responses_api=llm_settings.use_responses_api,
                reasoning_effort=llm_settings.reasoning_effort,
                store=False,
                seed=llm_settings.seed,
                timeout=llm_settings.timeout,
                api_key=llm_settings.api_key,
            )

    def __init_cognite(self, obo_token: str | None = None) -> CogniteSession:
        cognite_settings = self.cognite_settings
        return CogniteSession(
            base_url=cognite_settings.base_url,
            client_name=cognite_settings.client_name,
            project=cognite_settings.project,
            token_file_path=cognite_settings.token_file_path,
            interactive_client_id=cognite_settings.interactive_client_id,
            client_id=cognite_settings.client_id,
            client_secret=cognite_settings.client_secret,
            tenant_id=cognite_settings.tenant_id,
            obo_token=obo_token,
        )

    def get_agent(self, cognite_obo_token: str | None = None) -> CompiledStateGraph:
        if self.__agent:
            return self.__agent
        else:
            tools = self.tools
            cognite_session = self.__init_cognite(cognite_obo_token)
            tools = tools + [
                RetrieveTimeSeriesTool(cognite_session=cognite_session),
                RetrieveDataPointsTool(cognite_session=cognite_session),
            ]
            model_with_tools = self.model.bind_tools(tools, parallel_tool_calls=False)
            return create_agent(
                model=model_with_tools,
                tools=tools,
                system_prompt=self.instructions,
                checkpointer=self.checkpointer,
            )

    @property
    def graphdb_base_url(self) -> str:
        return self.__settings.graphdb.base_url

    @property
    def graphdb_repository_id(self) -> str:
        return self.__settings.graphdb.repository_id

    @property
    def sample_sparql_queries_enabled(self) -> bool:
        return bool(self.__settings.tools.retrieval_search)

    @property
    def sample_sparql_queries_settings(self) -> RetrievalSearchSettings:
        return self.__settings.tools.retrieval_search

    @property
    def cognite_enabled(self) -> bool:
        return bool(self.__settings.tools.cognite)

    @property
    def cognite_settings(self) -> CogniteSettings:
        return self.__settings.tools.cognite

    @property
    def assistant_instructions(self) -> str:
        return self.__settings.prompts.assistant_instructions

    @property
    def llm_metadata(self) -> dict:
        metadata = self.__settings.llm.model_dump(
            include={"type", "model", "seed", "use_responses_api", "reasoning_effort"},
            exclude_none=True,
        )
        if hasattr(self.model, "temperature") and self.model.temperature is not None:
            metadata["temperature"] = self.model.temperature
        return metadata
