import json
import random
import string

from mockserver import MockServerClient, times, json_equals

random.seed(42)
MOCK_OPENAI_CLIENT = MockServerClient("http://mock-server:1080")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sparql_query",
            "description": "Query GraphDB by SPARQL SELECT, CONSTRUCT, DESCRIBE or ASK query and return result.",
            "parameters": {
                "properties": {
                    "query": {
                        "description": "A valid SPARQL SELECT, CONSTRUCT, DESCRIBE or ASK query without prefixes",
                        "type": "string"
                    }
                },
                "required": ["query"],
                "type": "object"
            }
        }
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
                        "type": "string"
                    },
                    "result_class": {
                        "anyOf": [{
                            "type": "string"
                        }, {
                            "type": "null"
                        }],
                        "default": None,
                        "description": "Optionally, filter the results by class. "
                    },
                    "limit": {
                        "anyOf": [{
                            "minimum": 1,
                            "type": "integer"
                        }, {
                            "type": "null"
                        }],
                        "default": 10,
                        "description": "limit the results"
                    }
                },
                "required": ["query"],
                "type": "object"
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "now",
            "description": "Returns the current UTC date time in yyyy-mm-ddTHH:MM:SS format. Do not reuse responses.",
            "parameters": {
                "properties": {},
                "type": "object"
            }
        }
    }
]


def mock_openai_verify() -> None:
    # latest version of the python library is not working with the latest version of the mock server
    # hence we need to override this method
    for req, timing in MOCK_OPENAI_CLIENT.expectations:
        result = MOCK_OPENAI_CLIENT._call("verify", json.dumps({
            "httpRequest": req,
            "times": {"atLeast": timing.count, "atMost": timing.count}
        }))
        assert result.status_code == 202, result.content.decode('UTF-8').replace('\n', '\r\n')


def mock_openai_reset() -> None:
    MOCK_OPENAI_CLIENT.reset()


def mock_openai(
        n_times: int,
        request_messages: list,
        response_prompt_tokens: int,
        response_completion_tokens: int,
        response_content: str | None = None,
        response_tool_calls: list | None = None,
) -> None:
    MOCK_OPENAI_CLIENT.expect(
        request=openai_request(
            request_messages=request_messages,
        ),
        response=openai_response(
            content=response_content,
            tool_calls=response_tool_calls,
            prompt_tokens=response_prompt_tokens,
            completion_tokens=response_completion_tokens
        ),
        timing=times(n_times),
    )


def openai_request(request_messages: list) -> dict:
    messages = [{
        "content": "Mocked responses. Prompt doesn't matter.\n",
        "role": "system"
    }] + request_messages
    return {
        "method": "POST",
        "path": "/openai/deployments/gpt-4.1/chat/completions",
        "queryStringParameters": {
            "api-version": ["2024-12-01-preview"]
        },
        "body": json_equals(
            {
                "messages": messages,
                "model": "gpt-4.1",
                "seed": 1,
                "stream": False,
                "temperature": 0.0,
                "tools": TOOLS
            }
        )
    }


def openai_response(
        prompt_tokens: int,
        completion_tokens: int,
        content: str | None = None,
        tool_calls: list | None = None,
) -> dict:
    finish_reason = "stop"
    message: dict = {
        "role": "assistant",
        "content": content,
    }
    if tool_calls:
        message.update({"tool_calls": tool_calls})
        finish_reason = "tool_calls"
    return {
        "statusCode": 200,
        "body": {
            "id": "chat-completion-mock" + "".join(random.choices(string.digits, k=6)),
            "object": "chat.completion",
            "created": 1650000000,
            "model": "gpt-4.1",
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": finish_reason
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        }
    }
