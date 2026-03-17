import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Header,
)

from talk2powersystemllm.app.models import (
    GoodToGoInfo,
    HealthInfo,
    GoodToGoStatus,
    HealthStatus,
    Severity,
    AboutInfo,
    AboutOntologyInfo,
    AboutDatasetInfo,
    AboutGraphDBInfo,
    AboutAgentInfo,
    AboutLLMInfo,
    AboutBackendInfo,
)

router = APIRouter(tags=["Health-Check"])


async def update_gtg_info() -> None:
    logging.info("Updating gtg info")
    is_healthy = await __is_healthy()
    global gtg_info
    if is_healthy:
        gtg_info = GoodToGoInfo(gtg=GoodToGoStatus.OK)
    else:
        gtg_info = GoodToGoInfo(gtg=GoodToGoStatus.UNAVAILABLE)


async def __is_healthy():
    health_info = await health()
    if health_info.status == HealthStatus.OK:
        return True

    for health_check in health_info.healthChecks:
        if health_check.status == HealthStatus.ERROR and health_check.severity == Severity.HIGH:
            return False

    return True


# noinspection PyUnusedLocal
@app.get(
    "/__health",
    summary="Returns the health status of the application",
    tags=["Health-Check"],
    response_model=HealthInfo,
)
async def health(request: Request = None, x_request_id: Annotated[str | None, Header()] = None):
    health_info = await HealthChecks().get_health(request)
    return health_info


# noinspection PyUnusedLocal
@app.get(
    "/__gtg",
    summary="Returns if the service is good to go",
    tags=["Health-Check"],
    response_model=GoodToGoInfo,
    responses={
        503: {
            "model": GoodToGoInfo,
            "description": "The service is unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "gtg": GoodToGoStatus.UNAVAILABLE
                    },
                    "schema": {
                        "$ref": "#/components/schemas/GoodToGoInfo"
                    }
                }
            }
        }
    }
)
async def gtg(
    response: Response,
    x_request_id: Annotated[str | None, Header()] = None,
    cache: bool = True,
):
    if not cache:
        await update_gtg_info()
    global gtg_info
    if gtg_info.gtg == GoodToGoStatus.UNAVAILABLE:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return gtg_info


# noinspection PyUnusedLocal
@app.get(
    "/__trouble",
    summary="Returns an html rendering of the trouble document for the application",
    tags=["Health-Check"],
    response_class=HTMLResponse
)
async def trouble(x_request_id: Annotated[str | None, Header()] = None):
    return HTMLResponse(content=trouble_html)


async def update_about_info() -> None:
    logging.info("Updating about info")

    global about_info

    if about_info:
        about_info.ontologies = get_about_ontologies()
        about_info.datasets = get_about_datasets()
        about_info.graphdb = get_about_graphdb()
    else:
        about_ontologies = get_about_ontologies()
        about_datasets = get_about_datasets()
        about_graphdb = get_about_graphdb()
        about_agent = get_about_agent()
        about_backend = get_about_backend()

        about_info = AboutInfo(
            ontologies=about_ontologies,
            datasets=about_datasets,
            graphdb=about_graphdb,
            agent=about_agent,
            backend=about_backend,
        )


def get_about_ontologies() -> list[AboutOntologyInfo]:
    agent_factory = app.state.agent_factory
    query = files("talk2powersystemllm.app.server.queries").joinpath("about_ontologies_query.rq").read_text()
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(
        agent_factory.graphdb_repository_id, query, validation=False
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


def get_about_datasets() -> list[AboutDatasetInfo]:
    agent_factory = app.state.agent_factory
    query = files("talk2powersystemllm.app.server.queries").joinpath("about_datasets_query.rq").read_text()
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(
        agent_factory.graphdb_repository_id, query, validation=False
    )
    datasets: list[AboutDatasetInfo] = []
    for binding in query_results.bindings:
        datasets.append(AboutDatasetInfo(
            uri=binding[Variable("uri")],
            name=binding[Variable("name")].value if Variable("name") in binding else None,
            date=str(binding[Variable("date")].value) if Variable("date") in binding else None,
        ))
    return datasets


def get_about_graphdb() -> AboutGraphDBInfo:
    agent_factory = app.state.agent_factory
    query = files("talk2powersystemllm.app.server.queries").joinpath("about_graphdb_query.rq").read_text()
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(
        agent_factory.graphdb_repository_id, query, validation=False
    )
    onto = Namespace("http://www.ontotext.com/")
    return AboutGraphDBInfo(
        baseUrl=agent_factory.settings.graphdb.base_url,
        repository=agent_factory.graphdb_repository_id,
        version=list(query_results.graph.objects(onto.SI_has_Revision, None))[0].value,
        numberOfExplicitTriples=list(query_results.graph.objects(onto.SI_number_of_explicit_triples, None))[0].value,
        numberOfTriples=list(query_results.graph.objects(onto.SI_number_of_triples, None))[0].value,
        autocompleteIndexStatus=agent_factory.graphdb_client.get_autocomplete_status(
            agent_factory.graphdb_repository_id),
        rdfRankStatus=agent_factory.graphdb_client.get_rdf_rank_status(agent_factory.graphdb_repository_id),
    )


def get_about_agent() -> AboutAgentInfo:
    agent_factory = app.state.agent_factory
    tools: dict[str, dict[str, Any]] = dict()
    tools["sparql_query"] = {"enabled": True}
    tools["display_graphics"] = {"enabled": True}
    if (agent_factory.settings.tools.display_graphics and
        agent_factory.settings.tools.display_graphics.sparql_query_template):
        tools["display_graphics"].update({
            "sparql_query_template": agent_factory.settings.tools.display_graphics.sparql_query_template,
        })
    else:
        display_graphics_tool: GraphicsTool = \
            [tool for tool in agent_factory.tools if tool.name == "display_graphics"][0]
        tools["display_graphics"].update({
            "sparql_query_template": display_graphics_tool.sparql_query_template
        })
    tools["autocomplete_search"] = {
        "enabled": True,
        "property_path": agent_factory.settings.tools.autocomplete_search.property_path,
    }
    if agent_factory.settings.tools.autocomplete_search.sparql_query_template:
        tools["autocomplete_search"].update({
            "sparql_query_template": agent_factory.settings.tools.autocomplete_search.sparql_query_template,
        })
    else:
        autocomplete_search_tool: AutocompleteSearchTool = \
            [tool for tool in agent_factory.tools if tool.name == "autocomplete_search"][0]
        tools["autocomplete_search"].update({
            "sparql_query_template": autocomplete_search_tool.sparql_query_template
        })
    tools["sample_sparql_queries"] = {"enabled": True if agent_factory.settings.tools.retrieval_search else False}
    if agent_factory.settings.tools.retrieval_search:
        tools["sample_sparql_queries"].update({
            "sparql_query_template": agent_factory.settings.tools.retrieval_search.sparql_query_template,
            "connector_name": agent_factory.settings.tools.retrieval_search.connector_name,
        })
    tools["retrieve_data_points"] = {"enabled": True if agent_factory.settings.tools.cognite else False}
    tools["retrieve_time_series"] = {"enabled": True if agent_factory.settings.tools.cognite else False}
    if agent_factory.settings.tools.cognite:
        tools["retrieve_data_points"].update({
            "base_url": agent_factory.settings.tools.cognite.base_url,
            "project": agent_factory.settings.tools.cognite.project,
            "client_name": agent_factory.settings.tools.cognite.client_name,
        })
        tools["retrieve_time_series"].update({
            "base_url": agent_factory.settings.tools.cognite.base_url,
            "project": agent_factory.settings.tools.cognite.project,
            "client_name": agent_factory.settings.tools.cognite.client_name,
        })
    tools["now"] = {"enabled": True}
    return AboutAgentInfo(
        assistantInstructions=agent_factory.settings.prompts.assistant_instructions,
        llm=AboutLLMInfo(
            type=agent_factory.settings.llm.type,
            model=agent_factory.settings.llm.model,
            temperature=agent_factory.settings.llm.temperature,
            seed=agent_factory.settings.llm.seed,
        ),
        tools=tools,
    )


def get_about_backend() -> AboutBackendInfo:
    return AboutBackendInfo(
        description=API_DESCRIPTION,
        version=__version__,
        buildDate=__timestamp__,
        buildBranch=__branch__,
        gitSHA=__sha__,
        pythonVersion=sys.version,
        dependencies=__dependencies__,
    )


trouble_html = get_trouble_html()


# noinspection PyUnusedLocal
@app.get(
    "/__about",
    summary="Describes the application and provides build info about the component",
    tags=["Health-Check"],
    response_model=AboutInfo,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def about(x_request_id: Annotated[str | None, Header()] = None) -> AboutInfo:
    global about_info
    return about_info
