from typing import Any

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.app.models import QueryMethod
from talk2powersystemllm.app.server.exceptions import MessageNotFound, ConversationNotFound


async def get_query_methods(
    agent_factory: Talk2PowerSystemAgentFactory,
    conversation_id: str,
    message_id: str,
) -> list[QueryMethod]:
    explain_messages = await get_explain_messages(agent_factory, conversation_id, message_id)
    executed_queries, tools_calls_errors = get_queries_and_errors(explain_messages)
    return build_query_methods(agent_factory, explain_messages, executed_queries, tools_calls_errors)


async def get_explain_messages(
    agent_factory: Talk2PowerSystemAgentFactory,
    conversation_id: str,
    message_id: str
) -> list[Any]:
    messages = await get_all_messages(agent_factory, conversation_id, message_id)

    # going backwards find a human message or AI message with content
    # all messages in between are the explanation
    explain_messages = []
    for message in reversed(messages[:-1]):
        if isinstance(message, HumanMessage) or (isinstance(message, AIMessage) and message.content != ""):
            break
        explain_messages.insert(0, message)
    return explain_messages


async def get_all_messages(
    agent_factory: Talk2PowerSystemAgentFactory,
    conversation_id: str,
    message_id: str
) -> list[Any]:
    checkpoint = await agent_factory.checkpointer.aget(
        {"configurable": {"thread_id": conversation_id}}
    )
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


def get_queries_and_errors(explain_messages: list[Any]) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
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


def build_query_methods(
    agent_factory: Talk2PowerSystemAgentFactory,
    explain_messages: list[Any],
    executed_queries: dict[str, dict[str, str]],
    tools_calls_errors: dict[str, Any]
) -> list[QueryMethod]:
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
