import json
import random
import string

from mockserver import MockServerClient, json_equals, times

from .conf import USE_RESPONSES_API

random.seed(42)
MOCK_OPENAI_CLIENT = MockServerClient("http://mock-server:1080")

COMPLETIONS_API_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sparql_query",
            "description": "Query GraphDB by SPARQL SELECT, CONSTRUCT, DESCRIBE or ASK query and return result.",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "A valid SPARQL SELECT, CONSTRUCT, DESCRIBE or ASK query without prefixes",
                        "type": "string",
                    }
                },
                "required": ["query"],
                "type": "object",
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "autocomplete_search",
            "description": "Discover IRIs by searching their names and getting results in order of relevance.",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "autocomplete search query",
                        "type": "string",
                    },
                    "result_class": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "description": "Optionally, filter the results by class. ",
                    },
                    "limit": {
                        "anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}],
                        "default": 10,
                        "description": "limit the results",
                    },
                },
                "required": ["query"],
                "type": "object",
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "display_graphics",
            "description": "Displays a diagram specified by its IRI or "
            "a diagram specified by IRI of a diagram configuration and node IRI",
            "parameters": {
                "properties": {
                    "diagram_iri": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "description": "The IRI of a diagram. "
                        "Pass `diagram_iri` or `diagram_configuration_iri`, but not both.",
                    },
                    "diagram_configuration_iri": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "description": "The IRI of a diagram configuration. "
                        "Pass `diagram_iri` or `diagram_configuration_iri`, but not both. "
                        "When passing `diagram_configuration_iri`, argument `node_iri` is also required.",
                    },
                    "node_iri": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "description": "The IRI of a node. "
                        "When passing `node_iri`, argument `diagram_configuration_iri` is also required.",
                    },
                },
                "type": "object",
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "now",
            "description": "Returns the user's current date time in yyyy-mm-ddTHH:MM:SS±hhmm format (ISO 8601). "
            "Do not reuse responses.",
            "parameters": {"properties": {}, "type": "object"},
        },
    },
]


def transform_tools(completions_api_tools: list) -> list:
    """
    Transforms tools from the Chat Completions format to the Responses API format
    """
    transformed = []
    for tool in completions_api_tools:
        responses_api_tool = {"type": tool["type"]}
        if "function" in tool:
            responses_api_tool.update(tool["function"])
        transformed.append(responses_api_tool)
    return transformed


RESPONSES_API_TOOLS = transform_tools(COMPLETIONS_API_TOOLS)


def mock_openai_verify() -> None:
    # The latest version of the Python library is not working with the latest version of the mock
    # server. Hence, we need to override this method.
    for req, timing in MOCK_OPENAI_CLIENT.expectations:
        result = MOCK_OPENAI_CLIENT._call(
            "verify",
            json.dumps(
                {
                    "httpRequest": req,
                    "times": {"atLeast": timing.count, "atMost": timing.count},
                }
            ),
        )
        assert result.status_code == 202, result.content.decode("UTF-8").replace(
            "\n", "\r\n"
        )


def mock_openai_reset() -> None:
    MOCK_OPENAI_CLIENT.reset()


def mock_openai_error(
    n_times: int,
    request_messages: list,
    status_code: int,
    error_message: str,
    use_responses_api: bool = USE_RESPONSES_API,
):
    MOCK_OPENAI_CLIENT.expect(
        request=openai_request(
            request_messages=request_messages,
            use_responses_api=use_responses_api,
        ),
        response=openai_error_response(
            status_code=status_code,
            error_message=error_message,
        ),
        timing=times(n_times),
    )


def mock_openai(
    n_times: int,
    request_messages: list,
    response_prompt_tokens: int,
    response_completion_tokens: int,
    response_content: str | None = None,
    response_tool_calls: list | None = None,
    use_responses_api: bool = USE_RESPONSES_API,
) -> None:
    MOCK_OPENAI_CLIENT.expect(
        request=openai_request(
            request_messages=request_messages,
            use_responses_api=use_responses_api,
        ),
        response=openai_response(
            content=response_content,
            tool_calls=response_tool_calls,
            prompt_tokens=response_prompt_tokens,
            completion_tokens=response_completion_tokens,
            use_responses_api=use_responses_api,
        ),
        timing=times(n_times),
    )


def system_message(
    content: str,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    message = {"content": content, "role": "system"}
    if use_responses_api:
        message["type"] = "message"
    return message


def user_message(
    content: str,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    message = {"content": content, "role": "user"}
    if use_responses_api:
        message["type"] = "message"
    return message


def assistant_message(
    content: str,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    if use_responses_api:
        return {
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": content,
                    "annotations": [],
                }
            ],
            "id": "${json-unit.ignore-element}",
            "type": "message",
        }
    else:
        return {
            "role": "assistant",
            "content": content,
        }


def tool_call_message(
    call_id: str,
    name: str,
    arguments: str,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    if use_responses_api:
        return {
            "id": f"{call_id}",
            "name": f"{name}",
            "arguments": f"{arguments}",
            "call_id": f"call_{call_id}",
            "type": "function_call",
            "status": "completed",
        }
    else:
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "type": "function",
                    "id": f"{call_id}",
                    "function": {
                        "name": f"{name}",
                        "arguments": f"{arguments}",
                    },
                }
            ],
        }


def response_tool_call(
    call_id: str,
    name: str,
    arguments: str,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    if use_responses_api:
        return {
            "id": f"{call_id}",
            "call_id": f"call_{call_id}",
            "type": "function_call",
            "name": f"{name}",
            "arguments": f"{arguments}",
            "status": "completed",
        }
    else:
        return {
            "id": f"{call_id}",
            "type": "function",
            "function": {"name": f"{name}", "arguments": f"{arguments}"},
        }


def tool_output_message(
    call_id: str,
    output: str,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    if use_responses_api:
        return {
            "output": f"{output}",
            "call_id": f"call_{call_id}",
            "type": "function_call_output",
        }
    else:
        return {
            "content": f"{output}",
            "tool_call_id": f"{call_id}",
            "role": "tool",
        }


def openai_request(
    request_messages: list,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    messages = [
        system_message("Mocked responses. Prompt doesn't matter.\n")
    ] + request_messages

    if use_responses_api:
        path = "/openai/responses"
        body = {
            "input": messages,
            "model": "gpt-5.4",
            "tools": RESPONSES_API_TOOLS,
            "temperature": 0.0,
            "stream": False,
            "store": False,
            "reasoning": {"effort": "none"},
        }
    else:
        path = "/openai/deployments/gpt-5.4/chat/completions"
        body = {
            "messages": messages,
            "model": "gpt-5.4",
            "tools": COMPLETIONS_API_TOOLS,
            "temperature": 0.0,
            "stream": False,
            "store": False,
            "seed": 1,
            "reasoning_effort": "none",
        }

    return {
        "method": "POST",
        "path": path,
        "queryStringParameters": {"api-version": ["2025-04-01-preview"]},
        "body": json_equals(body),
    }


def openai_response(
    prompt_tokens: int,
    completion_tokens: int,
    content: str | None = None,
    tool_calls: list | None = None,
    use_responses_api: bool = USE_RESPONSES_API,
) -> dict:
    if use_responses_api:
        output_items = tool_calls if tool_calls else []
        if content:
            output_items.append(
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": content,
                            "annotations": [],
                        }
                    ],
                    "id": f"msg_{''.join(random.choices(string.digits, k=6))}",
                    "type": "message",
                    "status": "completed",
                }
            )
        body = {
            "id": f"response_mock_{''.join(random.choices(string.digits, k=6))}",
            "object": "response",
            "model": "gpt-5.4",
            "status": "completed",
            "output": output_items,
            "usage": {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
    else:
        finish_reason = "stop"
        message: dict = {
            "role": "assistant",
            "content": content,
        }
        if tool_calls:
            message.update({"tool_calls": tool_calls})
            finish_reason = "tool_calls"
        body = {
            "id": f"chat_completion_mock_{''.join(random.choices(string.digits, k=6))}",
            "object": "chat.completion",
            "model": "gpt-5.4",
            "choices": [
                {"index": 0, "message": message, "finish_reason": finish_reason}
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    return {"statusCode": 200, "body": body}


def openai_error_response(
    status_code: int,
    error_message: str,
) -> dict:
    return {"statusCode": status_code, "body": {"error": {"message": error_message}}}
