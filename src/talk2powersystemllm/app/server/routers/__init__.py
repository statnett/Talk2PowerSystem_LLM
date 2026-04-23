from .auth import router as auth_router
from .chat import router as chat_router
from .health import router as health_router

all_routers = [chat_router, health_router, auth_router]
