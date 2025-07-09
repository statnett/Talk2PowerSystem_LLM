from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = Field(default=None, alias="conversationId")


class Usage(BaseModel):
    completion_tokens: int = Field(alias="completionTokens")
    prompt_tokens: int = Field(alias="promptTokens")
    total_tokens: int = Field(alias="totalTokens")


class Message(BaseModel):
    id: str
    message: str
    usage: Usage


class ChatResponse(BaseModel):
    id: str
    messages: list[Message]
    usage: Usage


class ExplainRequest(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    message_id: str = Field(alias="messageId")


class QueryMethod(BaseModel):
    name: str
    args: dict
    query: str | None = None
    query_type: str | None = Field(default=None, alias="queryType")
    error_output: str | None = Field(default=None, alias="errorOutput")


class ExplainResponse(BaseModel):
    conversation_id: str = Field(alias="conversationId")
    message_id: str = Field(alias="messageId")
    query_methods: list[QueryMethod] = Field(default=None, alias="queryMethods")
