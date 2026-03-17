import uuid
from contextvars import ContextVar

from fastapi import (
    FastAPI,
    Request,
)
from starlette.responses import JSONResponse

from .config import settings
from .exceptions import MessageNotFound, ConversationNotFound
from .lifespan import lifespan
from .logging_config import LoggingConfig
from .routes import all_routers
from .services.about import (
    __version__,
)

ctx_request = ContextVar("request", default=None)
LoggingConfig.config_logger(settings.logging_yaml_file)

app = FastAPI(
    title="Talk2PowerSystem Chat Bot Application",
    description=("Talk2PowerSystem Chat Bot Application provides functionality for chatting with the "
                 "Talk2PowerSystem Chat bot"),
    version=__version__,
    docs_url=settings.docs_url,
    redoc_url=None,
    root_path=settings.root_path,
    lifespan=lifespan,
)

for router in all_routers:
    app.include_router(router)


@app.middleware("http")
async def add_x_request_id_header(request: Request, call_next):
    ctx_request.set(request.headers.get("X-Request-Id", str(uuid.uuid4())))
    response = await call_next(request)
    response.headers["X-Request-Id"] = ctx_request.get()
    return response


@app.exception_handler(ConversationNotFound)
async def conversation_not_found_error_handler(_, exc: ConversationNotFound):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


@app.exception_handler(MessageNotFound)
async def message_not_found_error_handler(_, exc: MessageNotFound):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )
