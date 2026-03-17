from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Request,
    Header,
    Depends,
    HTTPException,
)
from langchain_core.messages import (
    AIMessage,
    ToolMessage,
    HumanMessage,
)

router = APIRouter(prefix="/rest/chat", tags=["Chat"])


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
    claims=Depends(conditional_security),
):
    file_path = settings.diagrams_path / filename

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, headers={"Cache-Control": "private, max-age=3600"})


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
    request: Request,
    chat_request: ChatRequest,
    x_request_id: Annotated[str | None, Header()] = None,
    x_user_datetime: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
    claims=Depends(conditional_security),
) -> ChatResponse:
    cognite_obo_token = await get_cognite_obo_token(authorization)
    agent = app.state.agent_factory.get_agent(cognite_obo_token)
    conversation_id = await get_or_create_conversation(chat_request, agent)
    logging.info(f"Conversation {conversation_id}: Input \"{chat_request.question}\"")
    user_datetime_ctx.set(x_user_datetime)

    start = time.time()
    try:
        return await run_agent_on_input(request, agent, conversation_id, chat_request.question)
    finally:
        logging.info(
            f"Conversation {conversation_id}: Elapsed time: {time.time() - start:.2f} seconds"
        )


async def get_cognite_obo_token(authorization: str | None) -> str | None:
    cognite_obo_token = None
    agent_factory = app.state.agent_factory
    if (settings.security.enabled and agent_factory.settings.tools.cognite and
        agent_factory.settings.tools.cognite.client_secret):
        token_result = exchange_obo_for_cognite(authorization)
        cognite_obo_token = token_result["access_token"]
    return cognite_obo_token


def exchange_obo_for_cognite(user_access_token: str) -> dict:
    confidential_app = app.state.confidential_app
    cognite_scopes = app.state.cognite_scopes
    result = confidential_app.acquire_token_silent(cognite_scopes, account=None)
    if result:
        logging.debug("Cognite token acquired.")
        return result["access_token"]

    logging.debug("Acquiring token for Cognite using OBO.")
    result = confidential_app.acquire_token_on_behalf_of(
        user_assertion=user_access_token,
        scopes=cognite_scopes,
    )
    if "access_token" not in result:
        error_message = f"Failed to obtain OBO token for Cognite: {result}"
        logging.error(error_message)
        raise HTTPException(status_code=401, detail=error_message)
    return result


async def get_or_create_conversation(
    chat_request: ChatRequest,
    agent: CompiledStateGraph,
) -> str:
    conversation_id = chat_request.conversation_id
    if conversation_id:
        checkpoint = await agent.checkpointer.aget({"configurable": {"thread_id": conversation_id}})
        if not checkpoint:
            raise ConversationNotFound(f"Conversation with id \"{conversation_id}\" not found.")
    else:
        conversation_id = "thread_" + str(uuid.uuid4())
    return conversation_id


async def run_agent_on_input(
    request: Request,
    agent: CompiledStateGraph,
    conversation_id: str,
    question: str
) -> ChatResponse:
    messages: list[Message] = []
    graphics: list[Graphic] = []
    sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0

    runnable_config = RunnableConfig(
        configurable={"thread_id": conversation_id},
        callbacks=app.state.callbacks,
    )
    input_ = {"messages": [{"role": "user", "content": question}]}
    # noinspection PyTypeChecker
    async for output in agent.astream(input_, runnable_config, stream_mode="updates"):
        output = dict(output)
        logging.debug(f"Conversation {conversation_id}: Output {output}")

        if "model" in output and "messages" in output["model"]:
            for ai_message in output["model"]["messages"]:
                usage_metadata = ai_message.usage_metadata
                input_tokens, output_tokens, total_tokens = usage_metadata["input_tokens"], usage_metadata[
                    "output_tokens"], usage_metadata["total_tokens"]
                sum_input_tokens += input_tokens
                sum_output_tokens += output_tokens
                sum_total_tokens += total_tokens
                if ai_message.content:
                    logging.info(f"Conversation {conversation_id}: AI Message: \"{ai_message.content}\"")
                    message_kwargs = {
                        "id": ai_message.id,
                        "message": ai_message.content,
                        "usage": Usage(promptTokens=sum_input_tokens, completionTokens=sum_output_tokens,
                                       totalTokens=sum_total_tokens)
                    }
                    if graphics:
                        message_kwargs["graphics"] = graphics
                    messages.append(Message(**message_kwargs))
                    sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0
                    graphics: list[Graphic] = []
                if ai_message.tool_calls:
                    for tool_call in ai_message.tool_calls:
                        logging.info(f"Conversation {conversation_id}: Tool Call: {tool_call}")

        elif "tools" in output and "messages" in output["tools"]:
            for tool_message in output["tools"]["messages"]:
                if tool_message.status == "success" and tool_message.artifact:
                    if isinstance(tool_message.artifact, SvgArtifact):
                        graphics.append(
                            SvgGraphic(type="svg", url=build_diagram_image_url(request, tool_message.artifact.link))
                        )
                    elif isinstance(tool_message.artifact, GraphDBVisualGraphArtifact):
                        graphics.append(
                            VizGraphGraphic(type="vizGraph",
                                            url=build_gdb_visual_graph_url(tool_message.artifact.link))
                        )

    total_input_tokens = sum([message.usage.prompt_tokens for message in messages])
    total_output_tokens = sum([message.usage.completion_tokens for message in messages])
    total_total_tokens = sum([message.usage.total_tokens for message in messages])

    return ChatResponse(
        id=conversation_id,
        messages=messages,
        usage=Usage(completionTokens=total_output_tokens, promptTokens=total_input_tokens,
                    totalTokens=total_total_tokens)
    )


def build_diagram_image_url(request: Request, filename: str) -> str:
    return str(
        (settings.frontend_context_path if settings.frontend_context_path != "/" else "") + \
        request.app.url_path_for("diagrams", filename=filename)
    )


def build_gdb_visual_graph_url(link: str) -> str:
    agent_factory = app.state.agent_factory
    return agent_factory.settings.graphdb.base_url + \
        ("" if agent_factory.settings.graphdb.base_url.endswith("/") else "/") + \
        link + "&embedded=true"


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
    request: ExplainRequest,
    x_request_id: Annotated[str | None, Header()] = None,
    claims=Depends(conditional_security),
) -> ExplainResponse:
    conversation_id, message_id = request.conversation_id, request.message_id
    explain_messages = await get_explain_messages(conversation_id, message_id)
    executed_queries, tools_calls_errors = await get_queries_and_errors(explain_messages)
    query_methods = await build_query_methods(explain_messages, executed_queries, tools_calls_errors)

    return ExplainResponse(
        conversationId=conversation_id,
        messageId=message_id,
        queryMethods=query_methods,
    )


async def get_all_messages(conversation_id: str, message_id: str) -> list[Any]:
    checkpoint = await app.state.agent_factory.checkpointer.aget({"configurable": {"thread_id": conversation_id}})
    if not checkpoint:
        raise ConversationNotFound(f"Conversation with id \"{conversation_id}\" not found.")

    message_found = False
    # take only the messages up to the one we're interested in
    messages = []
    for message in checkpoint["channel_values"]["messages"]:
        messages.append(message)
        if message.id == message_id:
            message_found = True
            break

    if not message_found:
        raise MessageNotFound(f"Message with id \"{message_id}\" not found.")

    return messages


async def get_explain_messages(conversation_id: str, message_id: str) -> list[Any]:
    messages = await get_all_messages(conversation_id, message_id)

    # going backwards find a human message or AI message with content
    # all messages in between are the explanation
    explain_messages = []
    for message in reversed(messages[:-1]):
        if isinstance(message, HumanMessage) or (isinstance(message, AIMessage) and message.content != ""):
            break
        explain_messages.insert(0, message)
    return explain_messages


async def get_queries_and_errors(explain_messages: list[Any]) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    executed_queries = dict()
    tools_calls_errors = dict()
    for message in explain_messages:
        if isinstance(message, ToolMessage):
            if message.artifact and "kwargs" in message.artifact and "type" in message.artifact["kwargs"] and \
                message.artifact["kwargs"]["type"] == "query":
                executed_queries[message.tool_call_id] = {
                    "query": message.artifact["kwargs"]["query"],
                    "queryType": message.artifact["kwargs"]["query_type"],
                }
            if message.status == "error":
                tools_calls_errors[message.tool_call_id] = message.content
    return executed_queries, tools_calls_errors


async def build_query_methods(
    explain_messages: list[Any],
    executed_queries: dict[str, dict[str, str]],
    tools_calls_errors: dict[str, Any]
) -> list[QueryMethod]:
    agent_factory = app.state.agent_factory
    query_methods: list[QueryMethod] = []
    for message in explain_messages:
        if isinstance(message, AIMessage) and message.tool_calls != []:
            for tool_call in message.tool_calls:
                tool_name = tool_call["name"]
                tool_call_id = tool_call["id"]
                query_method: dict[str, Any] = {
                    "name": tool_name,
                    "args": tool_call["args"],
                }

                if tool_name in agent_factory.advanced_tools or tool_call_id in tools_calls_errors:
                    query_method["advanced"] = True
                if tool_name in agent_factory.tool_name_to_gdb_repository:
                    query_method["graphdbRepositoryId"] = agent_factory.tool_name_to_gdb_repository[tool_name]
                if tool_call_id in executed_queries:
                    query_method.update(executed_queries[tool_call_id])
                if tool_call_id in tools_calls_errors:
                    query_method["errorOutput"] = tools_calls_errors[tool_call_id]
                if query_method.get("queryType") == "sparql" and "query" in query_method and \
                    "errorOutput" not in query_method:
                    query_method["hideArgs"] = True
                query_methods.append(QueryMethod(**query_method))
    return query_methods
