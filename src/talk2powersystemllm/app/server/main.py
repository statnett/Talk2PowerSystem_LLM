import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Annotated, Any

import msal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import (
    FastAPI,
    Request,
    Response,
    Header,
    status,
    Depends,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from importlib_resources import files
from langchain_core.messages import (
    AIMessage,
    ToolMessage,
    HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.redis import AsyncRedisSaver
from rdflib import Graph, Namespace
from starlette.responses import JSONResponse
from ttyg.tools import AutocompleteSearchTool

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.tools.user_datetime_context import user_datetime_ctx
from .about import (
    __version__,
    __timestamp__,
    __branch__,
    __sha__,
    __dependencies__,
)
from .auth import conditional_security
from .config import settings
from .healthchecks import (
    GraphDBHealthchecker,
    HealthChecks,
)
from .healthchecks.redis_healthcheck import RedisHealthchecker
from .logging_config import LoggingConfig
from .trouble import get_trouble_html
from ..models import (
    ChatRequest,
    ChatResponse,
    Message,
    Usage,
    ExplainRequest,
    ExplainResponse,
    QueryMethod,
    GoodToGoInfo,
    HealthInfo,
    GoodToGoStatus,
    HealthStatus,
    Severity,
    AuthConfig,
    AboutInfo,
    AboutOntologyInfo,
    AboutDatasetInfo,
    AboutGraphDBInfo,
    AboutAgentInfo,
    AboutLLMInfo,
    AboutBackendInfo,
)

API_DESCRIPTION = "Talk2PowerSystem Chat Bot Application provides functionality for chatting with the Talk2PowerSystem Chat bot"
# noinspection PyTypeChecker
gtg_info: GoodToGoInfo = None
# noinspection PyTypeChecker
about_info: AboutInfo = None
# noinspection PyTypeChecker
agent_factory: Talk2PowerSystemAgentFactory = None
# noinspection PyTypeChecker
confidential_app: msal.ConfidentialClientApplication = None
# noinspection PyTypeChecker
COGNITE_SCOPES: list[str] = None
ctx_request = ContextVar("request", default=None)
LoggingConfig.config_logger(settings.logging_yaml_file)
trouble_html = get_trouble_html()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.info("Starting the application")
    global agent_factory
    global confidential_app
    global COGNITE_SCOPES

    redis_password = settings.redis.password
    redis_auth = ""
    if redis_password:
        redis_auth = f"{settings.redis.username}:{redis_password.get_secret_value()}@"
    async with AsyncRedisSaver.from_conn_string(
        redis_url=f"redis://{redis_auth}{settings.redis.host}:{settings.redis.port}",
        connection_args={
            'socket_connect_timeout': settings.redis.connect_timeout,
            'socket_timeout': settings.redis.read_timeout,
            'health_check_interval': settings.redis.healthcheck_interval,
        },
        ttl={
            "default_ttl": settings.redis.ttl,
            "refresh_on_read": settings.redis.ttl_refresh_on_read,
        }
    ) as memory_saver:
        await memory_saver.asetup()
        RedisHealthchecker(memory_saver._redis)
        agent_factory = Talk2PowerSystemAgentFactory(
            settings.agent_config,
            checkpointer=memory_saver
        )
        if settings.security.enabled and agent_factory.settings.tools.cognite:
            if not agent_factory.settings.tools.cognite.client_secret:
                raise ValueError(
                    "Cognite client secret must be provided in order to register the Cognite tools, "
                    "when the security is enabled."
                )
            confidential_app = msal.ConfidentialClientApplication(
                settings.security.client_id,
                authority=settings.security.authority,
                client_credential=agent_factory.settings.tools.cognite.client_secret,
            )
            COGNITE_SCOPES = [f"{agent_factory.settings.tools.cognite.base_url}/.default"]

        GraphDBHealthchecker(agent_factory.graphdb_client)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(update_gtg_info, 'interval', seconds=settings.gtg_refresh_interval)
        scheduler.add_job(update_about_info, 'interval', seconds=settings.about_refresh_interval)

        scheduler.start()
        app.state.scheduler = scheduler

        await update_gtg_info()
        await update_about_info()

        logging.info("Application is running")

        yield

        logging.info("Destroying the application")
        scheduler.shutdown()
        logging.info("Scheduler is stopped")


app = FastAPI(
    title="Talk2PowerSystem Chat Bot Application",
    description=API_DESCRIPTION,
    version=__version__,
    docs_url=settings.docs_url,
    redoc_url=None,
    root_path=settings.root_path,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_x_request_id_header(request: Request, call_next):
    ctx_request.set(request.headers.get("X-Request-Id", str(uuid.uuid4())))
    response = await call_next(request)
    response.headers["X-Request-Id"] = ctx_request.get()
    return response


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
    query = files("talk2powersystemllm.app.server.queries").joinpath("about_ontologies_query.rq").read_text()
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(query, validation=False)
    ontologies: list[AboutOntologyInfo] = []
    for binding in query_results["results"]["bindings"]:
        ontologies.append(AboutOntologyInfo(
            uri=binding["uri"]["value"],
            name=binding["name"]["value"] if "name" in binding else None,
            version=binding["version"]["value"] if "version" in binding else None,
            date=binding["date"]["value"] if "date" in binding else None,
        ))
    return ontologies


def get_about_datasets() -> list[AboutDatasetInfo]:
    query = files("talk2powersystemllm.app.server.queries").joinpath("about_datasets_query.rq").read_text()
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(query, validation=False)
    datasets: list[AboutDatasetInfo] = []
    for binding in query_results["results"]["bindings"]:
        datasets.append(AboutDatasetInfo(
            uri=binding["uri"]["value"],
            name=binding["name"]["value"] if "name" in binding else None,
            date=binding["date"]["value"] if "date" in binding else None,
        ))
    return datasets


def get_about_graphdb() -> AboutGraphDBInfo:
    query = files("talk2powersystemllm.app.server.queries").joinpath("about_graphdb_query.rq").read_text()
    query_results, _ = agent_factory.graphdb_client.eval_sparql_query(query, validation=False)
    schema_graph = Graph().parse(
        data=query_results,
        format="turtle",
    )
    onto = Namespace("http://www.ontotext.com/")
    return AboutGraphDBInfo(
        baseUrl=agent_factory.settings.graphdb.base_url,
        repository=agent_factory.settings.graphdb.repository_id,
        version=list(schema_graph.objects(onto.SI_has_Revision, None))[0].value,
        numberOfExplicitTriples=list(schema_graph.objects(onto.SI_number_of_explicit_triples, None))[0].value,
        numberOfTriples=list(schema_graph.objects(onto.SI_number_of_triples, None))[0].value,
        autocompleteIndexStatus=agent_factory.graphdb_client.get_autocomplete_status(),
        rdfRankStatus=agent_factory.graphdb_client.get_rdf_rank_status(),
    )


def get_about_agent() -> AboutAgentInfo:
    tools: dict[str, dict[str, Any]] = dict()
    tools["sparql_query"] = {"enabled": True}
    tools["autocomplete_search"] = {
        "enabled": True,
        "property_path": agent_factory.settings.tools.autocomplete_search.property_path,
    }
    if agent_factory.settings.tools.autocomplete_search.sparql_query_template:
        tools["autocomplete_search"].update({
            "sparql_query_template": agent_factory.settings.tools.autocomplete_search.sparql_query_template,
        })
    else:
        tool: AutocompleteSearchTool = [tool for tool in agent_factory.tools if tool.name == "autocomplete_search"][0]
        tools["autocomplete_search"].update({
            "sparql_query_template": tool.sparql_query_template
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


# noinspection PyUnusedLocal
@app.get(
    "/rest/authentication/config",
    summary="Exposes auth config settings",
    tags=["Auth"],
    response_model=AuthConfig,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_auth_config(
    x_request_id: Annotated[str | None, Header()] = None,
) -> AuthConfig:
    return AuthConfig(
        enabled=settings.security.enabled,
        clientId=settings.security.client_id,
        frontendAppClientId=settings.security.frontend_app_client_id,
        scopes=["openid", "profile", f"{settings.security.audience}/.default"],
        authority=settings.security.authority,
        logout=settings.security.logout,
        loginRedirect=settings.security.login_redirect,
        logoutRedirect=settings.security.logout_redirect,
    )


def exchange_obo_for_cognite(user_access_token: str) -> dict:
    result = confidential_app.acquire_token_silent(COGNITE_SCOPES, account=None)
    if result:
        logging.debug("Cognite token acquired.")
        return result["access_token"]

    logging.debug("Acquiring token for Cognite using OBO.")
    result = confidential_app.acquire_token_on_behalf_of(
        user_assertion=user_access_token,
        scopes=COGNITE_SCOPES,
    )
    if "access_token" not in result:
        error_message = f"Failed to obtain OBO token for Cognite: {result}"
        logging.error(error_message)
        raise HTTPException(status_code=401, detail=error_message)
    return result


# noinspection PyUnusedLocal
@app.post(
    "/rest/chat/conversations",
    summary="Starts a new conversation or adds message to an existing conversation",
    tags=["Chat"],
    responses={
        400: {
            "description": "Conversation not found",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Conversation with id \"thread_bf9b14ec-cf63-4cd7-975a-42fc8dfbb2ab\" not found."
                    },
                }
            }
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    },
                }
            }
        },
    },
    response_model=ChatResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def conversations(
    request: ChatRequest,
    x_request_id: Annotated[str | None, Header()] = None,
    x_user_datetime: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
    claims=Depends(conditional_security),
) -> ChatResponse:
    cognite_obo_token = None
    if settings.security.enabled and agent_factory.settings.tools.cognite and agent_factory.settings.tools.cognite.client_secret:
        token_result = exchange_obo_for_cognite(authorization)
        cognite_obo_token = token_result["access_token"]

    agent = agent_factory.get_agent(cognite_obo_token)

    user_datetime_ctx.set(x_user_datetime)

    conversation_id = request.conversation_id
    if conversation_id:
        checkpoint = await agent.checkpointer.aget({"configurable": {"thread_id": conversation_id}})
        if not checkpoint:
            raise ConversationNotFound(f"Conversation with id \"{conversation_id}\" not found.")
    else:
        conversation_id = "thread_" + str(uuid.uuid4())

    logging.info(f"Conversation {conversation_id}: Input \"{request.question}\"")
    runnable_config = RunnableConfig(configurable={"thread_id": conversation_id})
    input_ = {"messages": [{"role": "user", "content": request.question}]}

    sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0

    start = time.time()
    messages = []

    # noinspection PyTypeChecker
    async for output in agent.astream(input_, runnable_config, stream_mode="updates"):
        logging.info(f"Conversation {conversation_id}: Output {output}")
        if "model" in output and "messages" in output["model"]:
            for ai_message in output["model"]["messages"]:
                usage_metadata = ai_message.usage_metadata
                input_tokens, output_tokens, total_tokens = usage_metadata["input_tokens"], usage_metadata[
                    "output_tokens"], usage_metadata["total_tokens"]
                sum_input_tokens += input_tokens
                sum_output_tokens += output_tokens
                sum_total_tokens += total_tokens
                if ai_message.content:
                    messages.append(
                        Message(
                            id=ai_message.id,
                            message=ai_message.content,
                            usage=Usage(promptTokens=input_tokens, completionTokens=output_tokens,
                                        totalTokens=total_tokens)
                        ),
                    )

    logging.info(
        f"Conversation {conversation_id}: Elapsed time: {time.time() - start:.2f} seconds"
    )

    return ChatResponse(
        id=conversation_id,
        messages=messages,
        usage=Usage(completionTokens=sum_output_tokens, promptTokens=sum_input_tokens, totalTokens=sum_total_tokens)
    )


class ConversationNotFound(Exception):
    pass


class MessageNotFound(Exception):
    pass


@app.exception_handler(ConversationNotFound)
async def conversation_not_found_error_handler(_, exc: ConversationNotFound):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


@app.exception_handler(MessageNotFound)
async def message_not_found_error_handler(_, exc: MessageNotFound):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


# noinspection PyUnusedLocal
@app.post(
    "/rest/chat/conversations/explain",
    summary="For a given message in a conversation returns the tools calls made by the AI agent.",
    tags=["Chat"],
    responses={
        400: {
            "description": "Conversation or message not found",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Conversation with id \"thread_bf9b14ec-cf63-4cd7-975a-42fc8dfbb2ab\" not found."
                    },
                }
            }
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    },
                }
            }
        },
    },
    response_model=ExplainResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def explain(
    request: ExplainRequest,
    x_request_id: Annotated[str | None, Header()] = None,
    claims=Depends(conditional_security),
) -> ExplainResponse:
    conversation_id, message_id = request.conversation_id, request.message_id
    checkpoint = await agent_factory.checkpointer.aget({"configurable": {"thread_id": conversation_id}})

    if not checkpoint:
        raise ConversationNotFound(f"Conversation with id \"{conversation_id}\" not found.")

    saved_messages = checkpoint["channel_values"]["messages"]

    message_found = False
    # take only the messages up to the one we're interested in
    messages = []
    for message in saved_messages:
        messages.append(message)
        if message.id == message_id:
            message_found = True
            break
    if not message_found:
        raise MessageNotFound(f"Message with id \"{message_id}\" not found.")

    # going backwards find a human message or AI message with content
    # all messages in between are the explanation
    explain_messages = []
    for message in reversed(messages[:-1]):
        if isinstance(message, HumanMessage) or (isinstance(message, AIMessage) and message.content != ""):
            break
        explain_messages.insert(0, message)

    # gather artifacts (these are the actual redacted executed SPARQL queries) and errors
    tools_calls_errors = dict()
    tools_calls_artifacts = dict()
    for message in explain_messages:
        if isinstance(message, ToolMessage):
            if message.artifact:
                tools_calls_artifacts[message.tool_call_id] = message.artifact
            if message.status == "error":
                tools_calls_errors[message.tool_call_id] = message.content

    query_methods: list[QueryMethod] = []
    for message in explain_messages:
        if isinstance(message, AIMessage) and message.tool_calls != []:
            for tool_call in message.tool_calls:
                query_method_kwargs = {
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                }
                # TODO this is not a good way, currently we rely on the fact that only the SPARQL tools produce artifacts
                if tool_call["id"] in tools_calls_artifacts:
                    query_method_kwargs.update({
                        "query": tools_calls_artifacts[tool_call["id"]],
                        "queryType": "sparql",
                    })
                if tool_call["id"] in tools_calls_errors:
                    query_method_kwargs.update({
                        "errorOutput": tools_calls_errors[tool_call["id"]],
                    })
                query_methods.append(QueryMethod(**query_method_kwargs))

    return ExplainResponse(
        conversationId=conversation_id,
        messageId=message_id,
        queryMethods=query_methods,
    )
