import asyncio
import logging
import platform
import sys
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Annotated

import fastapi
import uvicorn
from fastapi import FastAPI, Request, Response, Header, status
from fastapi.responses import HTMLResponse
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.redis import RedisSaver
from starlette.responses import JSONResponse

from talk2powersystemllm.agent import Talk2PowerSystemAgent
from .config import settings
from .healthchecks import (
    GraphDBHealthchecker,
    CogniteHealthchecker,
    HealthChecks,
)
from .healthchecks.redis_healthcheck import RedisHealthchecker
from .logging_config import LoggingConfig
from .manifest import __sha__, __branch__, __timestamp__, __version__
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
)

API_DESCRIPTION = "Talk2PowerSystem Chat Bot Application provides functionality for chatting with the Talk2PowerSystem Chat bot"
# noinspection PyTypeChecker
gtg_info: GoodToGoInfo = None
ctx_request = ContextVar("request", default=None)
LoggingConfig.config_logger(settings.LOGGING_YAML_FILE)

redis_password = settings.REDIS_PASSWORD
redis_auth = ""
if redis_password:
    redis_auth = f"{settings.REDIS_USERNAME}:{redis_password.get_secret_value()}@"

with RedisSaver.from_conn_string(
        f"redis://{redis_auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        connection_args={
            'socket_connect_timeout': settings.REDIS_CONNECT_TIMEOUT,
            'socket_timeout': settings.REDIS_READ_TIMEOUT,
            'health_check_interval': settings.REDIS_HEALTHCHECK_INTERVAL,
        },
        ttl={
            "default_ttl": settings.REDIS_TTL,
            "refresh_on_read": settings.REDIS_TTL_REFRESH_ON_READ,
        }
) as memory_saver:
    memory_saver.setup()
    redis_healthcheck = RedisHealthchecker(memory_saver._redis)
    agent = Talk2PowerSystemAgent(
        settings.AGENT_CONFIG,
        checkpointer=memory_saver
    )
graphdb_healthcheck = GraphDBHealthchecker(agent.graphdb_client)
if agent.cognite_client:
    cognite_healthcheck = CogniteHealthchecker(agent.cognite_client)
trouble_html = get_trouble_html()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.info("Starting the application")

    async def scheduled_gtg_update():
        while True:
            await update_gtg_info()
            await asyncio.sleep(settings.GTG_REFRESH_INTERVAL)

    scheduled_gtg_update_task = asyncio.create_task(scheduled_gtg_update())
    await update_gtg_info()
    logging.info("Application is running")

    yield

    logging.info("Destroying the application")
    scheduled_gtg_update_task.cancel()
    try:
        await scheduled_gtg_update_task
    except asyncio.CancelledError:
        logging.info("Scheduled gtg update task stopped cleanly")


app = FastAPI(
    title="Talk2PowerSystem Chat Bot Application",
    description=API_DESCRIPTION,
    version=__version__,
    docs_url=settings.DOCS_URL,
    redoc_url=None,
    root_path=settings.ROOT_PATH,
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
        if health_check.status != HealthStatus.OK and health_check.severity == Severity.HIGH:
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


# noinspection PyUnusedLocal
@app.get(
    "/__about",
    summary="Describes the application and provides build info about the component",
    tags=["Health-Check"],
)
async def about(x_request_id: Annotated[str | None, Header()] = None):
    return {
        "description": API_DESCRIPTION,
        "version": __version__,
        "buildDate": __timestamp__,
        "buildBranch": __branch__,
        "gitSHA": __sha__,
        "pythonVersion": platform.python_version(),
        "systemVersion": sys.version,
        "fastApiVersion": fastapi.__version__,
        "uvicornVersion": uvicorn.__version__,
    }


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
        }
    },
    response_model=ChatResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def conversations(
        request: ChatRequest,
        x_request_id: Annotated[str | None, Header()] = None,
) -> ChatResponse:
    conversation_id = request.conversation_id
    if conversation_id:
        checkpoint = memory_saver.get({"configurable": {"thread_id": conversation_id}})
        if not checkpoint:
            raise ConversationNotFound(f"Conversation with id \"{conversation_id}\" not found.")
    else:
        conversation_id = "thread_" + str(uuid.uuid4())

    logging.info(f"Adding message \"{request.question}\" to conversation with id {conversation_id}")
    runnable_config = RunnableConfig(configurable={"thread_id": conversation_id})
    input_ = {"messages": [{"role": "user", "content": request.question}]}

    sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0

    start = time.time()
    messages = []

    # noinspection PyTypeChecker
    for message in agent.agent.stream(input_, runnable_config, stream_mode="updates"):
        logging.debug(f"Received message {message}")
        if "agent" in message:
            for ai_message in message["agent"]["messages"]:
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

    logging.debug(
        f"Elapsed time: {time.time() - start:.2f} seconds"
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
        }
    },
    response_model=ExplainResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def explain(
        request: ExplainRequest,
        x_request_id: Annotated[str | None, Header()] = None,
) -> ExplainResponse:
    conversation_id, message_id = request.conversation_id, request.message_id
    checkpoint = memory_saver.get({"configurable": {"thread_id": conversation_id}})

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
