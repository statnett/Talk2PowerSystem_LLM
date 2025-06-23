import os
from base64 import b64encode
from collections import OrderedDict
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
)

from talk2powersystemllm.tools import configure_cognite_client, RetrieveDataPointsTool, RetrieveTimeSeriesTool


def load_config(config_path: str) -> dict:
    config_path = Path(config_path).resolve()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())

    # Resolve paths relative to config file
    ontology_config = config.get("ontology", {})
    for key in ["string_enumerations_query_path"]:
        if key in ontology_config:
            rel_path = ontology_config[key]
            abs_path = config_path.parent / rel_path
            ontology_config[key] = str(abs_path.resolve())
    return config


def init_graphdb(config: dict) -> GraphDB:
    return GraphDB(
        base_url=config["graphdb"]["base_url"],
        repository_id=config["graphdb"]["repository_id"],
        auth_header="Basic " + b64encode(
            f"{config["graphdb"]["username"]}:{os.environ["GRAPHDB_PASSWORD"]}".encode("ascii")
        ).decode(),
    )


def init_cognite(cognite_config: dict) -> CogniteClient:
    return configure_cognite_client(
        cdf_project=cognite_config["cdf_project"],
        tenant_id=cognite_config["tenant_id"],
        client_name=cognite_config["client_name"],
        base_url=cognite_config["base_url"],
        interactive_client_id=cognite_config["interactive_client_id"]
    )


def init_llm(config: dict) -> BaseChatModel:
    model = AzureChatOpenAI(
        azure_endpoint=config["llm"]["azure_endpoint"],
        api_version=config["llm"]["api_version"],
        model=config["llm"]["model_name"],
        temperature=config["llm"]["temperature"],
        seed=config["llm"]["seed"],
        timeout=config["llm"]["timeout"],
    )
    return model


def get_talk_to_power_system_agent(
        config_path: str,
        checkpointer: Optional[Checkpointer] = None,
) -> CompiledGraph:
    config = load_config(config_path)
    graph = init_graphdb(config)

    tools: list[BaseTool] = []
    sparql_query_tool = SparqlQueryTool(
        graph=graph,
    )
    tools.append(sparql_query_tool)

    ontology_schema_file_path = Path(config["ontology"]["ontology_schema_file_path"])
    ontology_schema_and_vocabulary_tool = OntologySchemaAndVocabularyTool(
        graph=graph,
        ontology_schema_file_path=ontology_schema_file_path,
    )

    string_enumerations_query = Path(config["ontology"]["string_enumerations_query_path"]).read_text()
    results = graph.eval_sparql_query(string_enumerations_query)
    known_prefixes = graph.get_known_prefixes()
    sorted_known_prefixes = OrderedDict(sorted(known_prefixes.items(), key=lambda x: len(x[1]), reverse=True))
    string_enumerations_prompt = ""
    for r in results["results"]["bindings"]:
        shorten_property = r["property"]["value"]
        for prefix, namespace in sorted_known_prefixes.items():
            if shorten_property.startswith(namespace):
                shorten_property = shorten_property.replace(namespace, prefix + ":")
                break
        string_enumerations_prompt += f"""The unique string values of the property {shorten_property} separated with `;` are: {r["unique_objects"]["value"]}. \n"""

    tools_config = config["tools"]
    autocomplete_search_tool = AutocompleteSearchTool(
        graph=graph,
        property_path=tools_config["autocomplete"]["property_path"],
    )
    tools.append(autocomplete_search_tool)

    if "cognite" in tools_config:
        cognite_client: CogniteClient = init_cognite(tools_config["cognite"])
        tools.append(RetrieveTimeSeriesTool(cognite_client=cognite_client))
        tools.append(RetrieveDataPointsTool(cognite_client=cognite_client))

    tools.append(NowTool())

    instructions = f"""{config['prompts']['assistant_instructions']}

    The ontology schema to use in SPARQL queries is:

    ```turtle
    {ontology_schema_and_vocabulary_tool.schema_graph.serialize(format='turtle')}
    ```

    {string_enumerations_prompt}
    """

    model = init_llm(config)
    return create_react_agent(
        model=model,
        tools=tools,
        prompt=instructions,
        checkpointer=checkpointer,
    )
