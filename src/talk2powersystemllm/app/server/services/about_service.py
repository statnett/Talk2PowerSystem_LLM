import asyncio
import logging
import sys

import yaml
from fastapi import FastAPI
from importlib_resources import files
from rdflib import Namespace, Variable

from talk2powersystemllm.agent import (
    Talk2PowerSystemAgentFactory,
    Talk2PowerSystemAgentSettings,
)
from talk2powersystemllm.app.models import (
    AboutInfo,
    AboutOntologyInfo,
    AboutDatasetInfo,
    AboutGraphDBInfo,
    AboutAgentInfo,
    AboutLLMInfo,
    AboutBackendInfo,
)

logger = logging.getLogger(__name__)

QUERIES_DIR = files("talk2powersystemllm.app.server.services.queries")

ONTOLOGIES_QUERY = QUERIES_DIR.joinpath("about_ontologies_query.rq").read_text()
DATASETS_QUERY = QUERIES_DIR.joinpath("about_datasets_query.rq").read_text()
GRAPHDB_QUERY = QUERIES_DIR.joinpath("about_graphdb_query.rq").read_text()


async def update_about_info(fastapi_app: FastAPI) -> None:
    logger.info("Updating about info")

    if not hasattr(fastapi_app.state, "agent_factory"):
        logger.warning("Agent factory not found. Skipping about info update.")
        return

    try:
        ontologies, datasets, graphdb = await asyncio.gather(
            get_about_ontologies(fastapi_app),
            get_about_datasets(fastapi_app),
            get_about_graphdb(fastapi_app)
        )
        current_about = getattr(fastapi_app.state, "about_info", None)

        if current_about:
            current_about.ontologies = ontologies
            current_about.datasets = datasets
            current_about.graphdb = graphdb
        else:
            fastapi_app.state.about_info = AboutInfo(
                ontologies=ontologies,
                datasets=datasets,
                graphdb=graphdb,
                agent=get_about_agent(fastapi_app),
                backend=get_about_backend(fastapi_app),
            )
    except Exception:
        logger.exception(f"Failed to update about info")


async def get_about_ontologies(fastapi_app: FastAPI) -> list[AboutOntologyInfo]:
    agent_factory = fastapi_app.state.agent_factory
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(
        agent_factory.graphdb_repository_id, ONTOLOGIES_QUERY, validation=False
    )
    ontologies: list[AboutOntologyInfo] = []
    for binding in query_results.bindings:
        ontologies.append(AboutOntologyInfo(
            uri=binding[Variable("uri")],
            name=binding[Variable("name")].value if Variable("name") in binding else None,
            version=binding[Variable("version")].value if Variable("version") in binding else None,
            date=str(binding[Variable("date")].value) if Variable("date") in binding else None,
        ))
    return ontologies


async def get_about_datasets(fastapi_app: FastAPI) -> list[AboutDatasetInfo]:
    agent_factory = fastapi_app.state.agent_factory
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(
        agent_factory.graphdb_repository_id, DATASETS_QUERY, validation=False
    )
    datasets: list[AboutDatasetInfo] = []
    for binding in query_results.bindings:
        datasets.append(AboutDatasetInfo(
            uri=binding[Variable("uri")],
            name=binding[Variable("name")].value if Variable("name") in binding else None,
            date=str(binding[Variable("date")].value) if Variable("date") in binding else None,
        ))
    return datasets


async def get_about_graphdb(fastapi_app: FastAPI) -> AboutGraphDBInfo:
    agent_factory = fastapi_app.state.agent_factory
    graphdb_client, graphdb_repository_id = agent_factory.graphdb_client, agent_factory.graphdb_repository_id
    query_results, _ = graphdb_client.eval_sparql_query(
        graphdb_repository_id, GRAPHDB_QUERY, validation=False
    )
    onto = Namespace("http://www.ontotext.com/")

    def get_object(predicate):
        obj = next(query_results.graph.objects(predicate, None), None)
        return obj.value if obj else None

    return AboutGraphDBInfo(
        baseUrl=agent_factory.settings.graphdb.base_url,
        repository=graphdb_repository_id,
        version=get_object(onto.SI_has_Revision),
        numberOfExplicitTriples=get_object(onto.SI_number_of_explicit_triples),
        numberOfTriples=get_object(onto.SI_number_of_triples),
        autocompleteIndexStatus=graphdb_client.get_autocomplete_status(graphdb_repository_id),
        rdfRankStatus=graphdb_client.get_rdf_rank_status(graphdb_repository_id),
    )


def get_about_agent(fastapi_app: FastAPI) -> AboutAgentInfo:
    agent_factory: Talk2PowerSystemAgentFactory = fastapi_app.state.agent_factory
    agent_settings: Talk2PowerSystemAgentSettings = fastapi_app.state.agent_factory.settings
    return AboutAgentInfo(
        assistantInstructions=agent_settings.prompts.assistant_instructions,
        llm=AboutLLMInfo(
            type=agent_settings.llm.type,
            model=agent_settings.llm.model,
            temperature=agent_settings.llm.temperature,
            seed=agent_settings.llm.seed,
        ),
        tools=agent_factory.tools_metadata,
    )


def get_about_backend(fastapi_app: FastAPI) -> AboutBackendInfo:
    def read_manifest() -> dict:
        with open(fastapi_app.state.settings.manifest_path, "r") as f:
            return yaml.safe_load(f.read())

    git_manifest = read_manifest()
    git_sha = git_manifest["Git-SHA"]
    build_branch = git_manifest["Build-Branch"]
    build_timestamp = git_manifest["Build-Timestamp"]

    return AboutBackendInfo(
        description=fastapi_app.description,
        version=fastapi_app.version,
        buildDate=build_timestamp,
        buildBranch=build_branch,
        gitSHA=git_sha,
        pythonVersion=sys.version,
        dependencies=fastapi_app.state.dependencies,
    )
