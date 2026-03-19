import logging
import time
from typing import Annotated

from fastapi import (
    APIRouter,
    Request,
    Header,
    Depends,
    HTTPException,
)
from langgraph.graph.state import CompiledStateGraph
from starlette.responses import FileResponse

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.app.models import (
    ChatRequest,
    ChatResponse,
    SvgGraphic,
    VizGraphGraphic,
    ExplainResponse,
    ExplainRequest,
)
from talk2powersystemllm.app.server.config import AppSettings
from talk2powersystemllm.app.server.dependencies import (
    get_chat_agent,
    get_agent_factory,
    get_llm_callbacks, get_settings, conditional_security,
)
from talk2powersystemllm.app.server.services.chat_service import get_or_create_conversation, run_agent_loop
from talk2powersystemllm.app.server.services.explain_service import get_query_methods
from talk2powersystemllm.tools import user_datetime_ctx

router = APIRouter(prefix="/rest/chat", tags=["Chat"], dependencies=[Depends(conditional_security)])
logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
@router.get(
    "/diagrams/{filename}",
    summary="Serves the static diagrams",
    tags=["Chat"],
    responses={
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
        404: {
            "description": "File not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File not found"
                    },
                }
            }
        },
    },
    name="diagrams"
)
async def diagrams(
    filename: str,
    settings: AppSettings = Depends(get_settings),
):
    file_path = settings.diagrams_path / filename

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, headers={"Cache-Control": "private, max-age=3600"})


# noinspection PyUnusedLocal
@router.post(
    "/conversations",
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
    agent: Annotated[CompiledStateGraph, Depends(get_chat_agent)],
    agent_factory: Annotated[Talk2PowerSystemAgentFactory, Depends(get_agent_factory)],
    request: Request,
    chat_request: ChatRequest,
    x_request_id: Annotated[str | None, Header()] = None,
    x_user_datetime: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
    callbacks: list = Depends(get_llm_callbacks),
) -> ChatResponse:
    user_datetime_ctx.set(x_user_datetime)
    conversation_id = await get_or_create_conversation(chat_request, agent)

    start = time.time()
    try:
        chat_response = await run_agent_loop(agent, conversation_id, chat_request.question, callbacks)

        for message in chat_response.messages:
            if message.graphics:
                for g in message.graphics:
                    if isinstance(g, SvgGraphic):
                        g.url = build_diagram_image_url(request, g.url)
                    elif isinstance(g, VizGraphGraphic):
                        g.url = build_gdb_visual_graph_url(agent_factory, g.url)

        return chat_response

    finally:
        logger.info(f"Conversation {conversation_id}: Elapsed {time.time() - start:.2f}s")


def build_diagram_image_url(request: Request, filename: str) -> str:
    return str(
        (
            request.app.state.settings.frontend_context_path if request.app.state.settings.frontend_context_path !=
                                                                "/" else "") + \
        request.app.url_path_for("diagrams", filename=filename)
    )


def build_gdb_visual_graph_url(agent_factory: Talk2PowerSystemAgentFactory, link: str) -> str:
    base_url = agent_factory.graphdb_base_url + ("" if agent_factory.graphdb_base_url.endswith("/") else "/")
    return base_url + link + "&embedded=true"


# noinspection PyUnusedLocal
@router.post(
    "/conversations/explain",
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
    explain_request: ExplainRequest,
    agent_factory: Annotated[Talk2PowerSystemAgentFactory, Depends(get_agent_factory)],
    x_request_id: Annotated[str | None, Header()] = None,
) -> ExplainResponse:
    conversation_id = explain_request.conversation_id
    message_id = explain_request.message_id

    query_methods = await get_query_methods(agent_factory, conversation_id, message_id)

    return ExplainResponse(
        conversationId=conversation_id,
        messageId=message_id,
        queryMethods=query_methods,
    )
