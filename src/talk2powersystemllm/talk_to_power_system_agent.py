import os
from base64 import b64encode
from collections import OrderedDict
from pathlib import Path
from typing import Optional

import yaml
from langchain_core.language_models import BaseChatModel
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

    graph = init_graphdb(config["graphdb"])
    tools_config = config["tools"]
    tools = []

    sparql_query_tool = SparqlQueryTool(
        graph=graph,
    )
    tools.append(sparql_query_tool)

    ontology_schema_config = tools_config["ontology_schema"]
    ontology_schema_file_path = Path(ontology_schema_config["file_path"])
    ontology_schema_and_vocabulary_tool = OntologySchemaAndVocabularyTool(
        graph=graph,
        ontology_schema_file_path=ontology_schema_file_path,
    )

    string_enumerations_query = Path(ontology_schema_config["string_enumerations_query_path"]).read_text()
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

    autocomplete_search_config = tools_config["autocomplete_search"]
    autocomplete_search_kwargs = {
        "property_path": autocomplete_search_config["property_path"],
    }
    if "sparql_query_template" in autocomplete_search_config:
        autocomplete_search_kwargs.update({
            "sparql_query_template": autocomplete_search_config["sparql_query_template"],
        })
    autocomplete_search_tool = AutocompleteSearchTool(
        graph=graph,
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
