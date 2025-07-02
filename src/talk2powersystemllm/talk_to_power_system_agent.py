from base64 import b64encode
from typing import Optional

from cognite.client import CogniteClient
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Checkpointer
from ttyg.graphdb import GraphDB
from ttyg.tools import (
    AutocompleteSearchTool,
    NowTool,
    OntologySchemaAndVocabularyTool,
    SparqlQueryTool,
    RetrievalQueryTool,
)

from talk2powersystemllm.config import AppSettings, GraphDBSettings, CogniteSettings, LLMSettings
from talk2powersystemllm.tools import configure_cognite_client, RetrieveDataPointsTool, RetrieveTimeSeriesTool


def init_graphdb(graphdb_settings: GraphDBSettings) -> GraphDB:
    if graphdb_settings.username:
        return GraphDB(
            base_url=graphdb_settings.base_url,
            repository_id=graphdb_settings.repository_id,
            auth_header="Basic " + b64encode(
                f"{graphdb_settings.username}:{graphdb_settings.password.get_secret_value()}".encode("ascii")
            ).decode(),
        )
    else:
        return GraphDB(
            base_url=graphdb_settings.base_url,
            repository_id=graphdb_settings.repository_id,
        )


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


def get_talk_to_power_system_agent(
        settings: AppSettings,
        checkpointer: Optional[Checkpointer] = None,
) -> CompiledStateGraph:
    graphdb = init_graphdb(settings.graphdb)

    tools_settings = settings.tools
    tools: list[BaseTool] = []

    sparql_query_tool = SparqlQueryTool(
        graph=graphdb,
    )
    tools.append(sparql_query_tool)

    ontology_schema_and_vocabulary_tool = OntologySchemaAndVocabularyTool(
        graph=graphdb,
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
        graph=graphdb,
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
        cognite_client: CogniteClient = init_cognite(cognite_settings)
        tools.append(RetrieveTimeSeriesTool(cognite_client=cognite_client))
        tools.append(RetrieveDataPointsTool(cognite_client=cognite_client))

    tools.append(NowTool())

    instructions = f"""{settings.prompts.assistant_instructions}""".replace(
        "{ontology_schema}", ontology_schema_and_vocabulary_tool.schema_graph.serialize(format="turtle")
    )

    model = init_llm(settings.llm)
    return create_react_agent(
        model=model,
        tools=tools,
        prompt=instructions,
        checkpointer=checkpointer,
    )
