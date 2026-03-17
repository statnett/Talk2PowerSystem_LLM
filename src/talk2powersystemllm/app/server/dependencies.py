from fastapi import Request

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory


def get_agent_factory(request: Request) -> Talk2PowerSystemAgentFactory:
    return request.app.state.agent_factory


def get_llm_callbacks(request: Request) -> list:
    return request.app.state.callbacks


def get_msal_app(request: Request):
    return getattr(request.app.state, "confidential_app", None)
