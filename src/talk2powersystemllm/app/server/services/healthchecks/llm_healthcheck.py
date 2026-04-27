import logging
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from redis.asyncio import Redis, RedisCluster

from talk2powersystemllm.app.models import HealthCheck, HealthStatus, Severity
from talk2powersystemllm.app.server.services.healthchecks.healthchecks import (
    HealthProvider,
)

logger = logging.getLogger(__name__)


class LLMHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/llm-healthcheck"
    name: str = "LLM Health Check"
    type: str = "llm"
    impact: str = "Some requests to the chatbot failed during the last 60 seconds due to LLM errors!"
    troubleshooting: str = "#llm-health-check-status-is-not-ok"
    description: str = (
        "Checks if any LLM calls resulted in errors during the last 60 seconds!"
    )


class LLMHealthchecker(AsyncCallbackHandler, HealthProvider):
    def __init__(
        self,
        redis_client: Redis | RedisCluster,
        prefix: str = "app:health:",
        key: str = "llm_error",
        ttl: int = 60,
    ):
        super().__init__()
        self.__redis_client = redis_client
        # the prefix becomes {prefix}, i.e. we use Redis hashtag for cluster compatibility
        self.__prefix = f"{{{prefix}}}"
        self.__key = key
        self.__ttl = ttl

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        logger.exception("Calling the LLM resulted in error")
        await self.__redis_client.set(
            f"{self.__prefix}{self.__key}", "true", ex=self.__ttl
        )

    async def health(self) -> LLMHealthcheck:
        try:
            llm_errors = await self.__redis_client.get(f"{self.__prefix}{self.__key}")
            if llm_errors:
                return LLMHealthcheck(
                    status=HealthStatus.WARNING,
                    message=f"LLM errors were hit in the last {self.__ttl} seconds!",
                )
            return LLMHealthcheck(
                status=HealthStatus.OK,
                message=f"No LLM errors were hit in the last {self.__ttl} seconds!",
            )
        except Exception as error:
            logger.exception("Exception while checking for LLM errors")
            return LLMHealthcheck(status=HealthStatus.ERROR, message=str(error))
