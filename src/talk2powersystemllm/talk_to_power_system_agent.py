import os
from base64 import b64encode
from pathlib import Path
from typing import Optional

import yaml
from cognite.client import CogniteClient
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI
from langgraph.graph.graph import CompiledGraph
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

from talk2powersystemllm.tools import configure_cognite_client, RetrieveDataPointsTool, RetrieveTimeSeriesTool


def load_config(config_path: str) -> dict:
    config_path = Path(config_path).resolve()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())

    # Resolve paths relative to config file
    ontology_schema_config = config["tools"]["ontology_schema"]
    for key in ontology_schema_config.keys():
        rel_path = ontology_schema_config[key]
        abs_path = config_path.parent / rel_path
        ontology_schema_config[key] = str(abs_path.resolve())
    return config


def init_graphdb(graphdb_config: dict) -> GraphDB:
    if "username" in graphdb_config:
        return GraphDB(
            base_url=graphdb_config["base_url"],
            repository_id=graphdb_config["repository_id"],
            auth_header="Basic " + b64encode(
                f"{graphdb_config["username"]}:{os.environ["GRAPHDB_PASSWORD"]}".encode("ascii")
            ).decode(),
        )
    else:
        return GraphDB(
            base_url=graphdb_config["base_url"],
            repository_id=graphdb_config["repository_id"],
        )


def init_cognite(cognite_config: dict) -> CogniteClient:
    return configure_cognite_client(
        cdf_project=cognite_config["cdf_project"],
        tenant_id=cognite_config["tenant_id"],
        client_name=cognite_config["client_name"],
        base_url=cognite_config["base_url"],
        interactive_client_id=cognite_config["interactive_client_id"]
    )


def init_llm(llm_config: dict) -> BaseChatModel:
    return AzureChatOpenAI(
        azure_endpoint=llm_config["azure_endpoint"],
        api_version=llm_config["api_version"],
        model=llm_config["model_name"],
        temperature=llm_config["temperature"],
        seed=llm_config["seed"],
        timeout=llm_config["timeout"],
    )


def get_talk_to_power_system_agent(
        config_path: str,
        checkpointer: Optional[Checkpointer] = None,
) -> CompiledGraph:
    config = load_config(config_path)

    graphdb = init_graphdb(config["graphdb"])

    tools_config = config["tools"]
    tools: list[BaseTool] = []

    sparql_query_tool = SparqlQueryTool(
        graph=graphdb,
    )
    tools.append(sparql_query_tool)

    ontology_schema_config = tools_config["ontology_schema"]
    ontology_schema_file_path = Path(ontology_schema_config["file_path"])
    ontology_schema_and_vocabulary_tool = OntologySchemaAndVocabularyTool(
        graph=graphdb,
        ontology_schema_file_path=ontology_schema_file_path,
    )

    autocomplete_search_config = tools_config["autocomplete_search"]
    autocomplete_search_kwargs = {
        "property_path": autocomplete_search_config["property_path"],
    }
    if "sparql_query_template" in autocomplete_search_config:
        autocomplete_search_kwargs.update({
            "sparql_query_template": autocomplete_search_config["sparql_query_template"],
        })
    autocomplete_search_tool = AutocompleteSearchTool(
        graph=graphdb,
        **autocomplete_search_kwargs,
    )
    tools.append(autocomplete_search_tool)

    if "retrieval_search" in tools_config:
        retrieval_search_config = tools_config["retrieval_search"]
        retrieval_query_tool = RetrievalQueryTool(
            graph=init_graphdb(retrieval_search_config["graphdb"]),
            connector_name=retrieval_search_config["connector_name"],
            name=retrieval_search_config["name"],
            description=retrieval_search_config["description"],
            sparql_query_template=retrieval_search_config["sparql_query_template"],
        )
        tools.append(retrieval_query_tool)

    if "cognite" in tools_config:
        cognite_config = tools_config["cognite"]
        cognite_client: CogniteClient = init_cognite(cognite_config)
        tools.append(RetrieveTimeSeriesTool(cognite_client=cognite_client))
        tools.append(RetrieveDataPointsTool(cognite_client=cognite_client))

    tools.append(NowTool())

    instructions = f"""{config['prompts']['assistant_instructions']}""".replace(
        "{ontology_schema}", ontology_schema_and_vocabulary_tool.schema_graph.serialize(format='turtle')
    )

    model = init_llm(config["llm"])
    return create_react_agent(
        model=model,
        tools=tools,
        prompt=instructions,
        checkpointer=checkpointer,
    )
