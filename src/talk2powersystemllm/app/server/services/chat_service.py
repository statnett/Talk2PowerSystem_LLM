import logging
import uuid

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from talk2powersystemllm.app.models import ChatResponse, Message, Usage, SvgGraphic, VizGraphGraphic, Graphic
from talk2powersystemllm.app.server.exceptions import ConversationNotFound
from talk2powersystemllm.tools import SvgArtifact, GraphDBVisualGraphArtifact

logger = logging.getLogger(__name__)

async def get_or_create_conversation(chat_request, agent: CompiledStateGraph) -> str:
    conversation_id = chat_request.conversation_id
    if conversation_id:
        checkpoint = await agent.checkpointer.aget({"configurable": {"thread_id": conversation_id}})
        if not checkpoint:
            raise ConversationNotFound(f"Conversation with id \"{conversation_id}\" not found.")
    else:
        conversation_id = f"thread_{uuid.uuid4()}"
    return conversation_id


async def run_agent_loop(
    agent: CompiledStateGraph,
    conversation_id: str,
    question: str,
    callbacks: list
) -> ChatResponse:
    messages: list[Message] = []
    graphics: list[Graphic] = []
    sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0

    runnable_config = RunnableConfig(
        configurable={"thread_id": conversation_id},
        callbacks=callbacks,
    )
    input_ = {"messages": [{"role": "user", "content": question}]}
    # noinspection PyTypeChecker
    async for output in agent.astream(input_, runnable_config, stream_mode="updates"):
        output = dict(output)
        logger.debug(f"Conversation {conversation_id}: Output {output}")

        if "model" in output and "messages" in output["model"]:
            for ai_message in output["model"]["messages"]:
                usage_metadata = ai_message.usage_metadata
                input_tokens, output_tokens, total_tokens = usage_metadata["input_tokens"], usage_metadata[
                    "output_tokens"], usage_metadata["total_tokens"]
                sum_input_tokens += input_tokens
                sum_output_tokens += output_tokens
                sum_total_tokens += total_tokens
                if ai_message.content:
                    logger.info(f"Conversation {conversation_id}: AI Message: \"{ai_message.content}\"")
                    message_kwargs = {
                        "id": ai_message.id,
                        "message": ai_message.content,
                        "usage": Usage(
                            promptTokens=sum_input_tokens,
                            completionTokens=sum_output_tokens,
                            totalTokens=sum_total_tokens
                        )
                    }
                    if graphics:
                        message_kwargs["graphics"] = graphics
                    messages.append(Message(**message_kwargs))
                    sum_input_tokens, sum_output_tokens, sum_total_tokens = 0, 0, 0
                    graphics: list[Graphic] = []
                if ai_message.tool_calls:
                    for tool_call in ai_message.tool_calls:
                        logger.info(f"Conversation {conversation_id}: Tool Call: {tool_call}")

        elif "tools" in output and "messages" in output["tools"]:
            for tool_message in output["tools"]["messages"]:
                if tool_message.status == "success" and tool_message.artifact:
                    if isinstance(tool_message.artifact, SvgArtifact):
                        graphics.append(
                            SvgGraphic(type="svg", url=tool_message.artifact.link)
                        )
                    elif isinstance(tool_message.artifact, GraphDBVisualGraphArtifact):
                        graphics.append(
                            VizGraphGraphic(type="vizGraph", url=tool_message.artifact.link)
                        )

    total_input_tokens = sum([message.usage.prompt_tokens for message in messages])
    total_output_tokens = sum([message.usage.completion_tokens for message in messages])
    total_total_tokens = sum([message.usage.total_tokens for message in messages])

    return ChatResponse(
        id=conversation_id,
        messages=messages,
        usage=Usage(
            completionTokens=total_output_tokens,
            promptTokens=total_input_tokens,
            totalTokens=total_total_tokens
        )
    )
