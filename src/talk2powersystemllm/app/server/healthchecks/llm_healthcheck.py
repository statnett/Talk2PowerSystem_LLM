import logging
from typing import Union

from redis import Redis, RedisCluster

from .healthchecks import HealthChecks
from ..singleton import SingletonMeta
from ...models import HealthCheck, Severity, HealthStatus


class LLMHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/llm-healthcheck"
    name: str = "LLM Health Check"
    type: str = "llm"
    impact: str = "Some requests to the chat bot failed during the last 60 seconds due to LLM errors!"
    troubleshooting: str = "#llm-health-check-status-is-not-ok"
    description: str = "Checks if any LLM calls resulted in errors during the last 60 seconds!"


class LLMHealthchecker(metaclass=SingletonMeta):
    def __init__(
        self,
        redis_client: Union[Redis, RedisCluster],
    ):
        self.__redis_client = redis_client
        HealthChecks().add(self)

    async def health(self) -> LLMHealthcheck:
        try:
            llm_errors = await self.__redis_client.get("llm_errors")
            if llm_errors:
                return LLMHealthcheck(status=HealthStatus.WARNING,
                                      message="LLM errors were hit in the last 60 seconds!")
            return LLMHealthcheck(status=HealthStatus.OK, message="No LLM errors were hit in the last 60 seconds!")
        except Exception as error:
            logging.error("Exception while checking for LLM errors", exc_info=error)
            return LLMHealthcheck(status=HealthStatus.ERROR, message=str(error))
