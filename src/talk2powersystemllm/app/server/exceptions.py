import logging

from fastapi import (
    FastAPI,
    Request,
)
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ConversationNotFound(Exception):
    pass


class MessageNotFound(Exception):
    pass


def setup_exception_handlers(fastapi_app: FastAPI):
    @fastapi_app.exception_handler(ConversationNotFound)
    async def conversation_not_found_error_handler(request: Request, exc: ConversationNotFound):
        logger.warning(f"Conversation not found: {exc} | Path: {request.url.path}")
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    @fastapi_app.exception_handler(MessageNotFound)
    async def message_not_found_error_handler(request: Request, exc: MessageNotFound):
        logger.warning(f"Message not found: {exc} | Path: {request.url.path}")
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )
