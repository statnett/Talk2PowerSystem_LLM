import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request

CTX_REQUEST: ContextVar[str | None] = ContextVar("request", default=None)


def setup_middleware(fastapi_app: FastAPI):
    @fastapi_app.middleware("http")
    async def add_x_request_id_header(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        token = CTX_REQUEST.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            CTX_REQUEST.reset(token)
