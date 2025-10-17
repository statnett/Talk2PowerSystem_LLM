import logging
from typing import Union

from redis import Redis, RedisCluster

from .healthchecks import HealthChecks
from ..singleton import SingletonMeta
from ...models import HealthCheck, Severity, HealthStatus


class RedisHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/redis-healthcheck"
    name: str = "Redis Health Check"
    type: str = "redis"
    impact: str = "Redis is inaccessible and the chat bot can't function"
    troubleshooting: str = "#redis-health-check-status-is-not-ok"
    description: str = "Checks if Redis can be queried."


class RedisHealthchecker(metaclass=SingletonMeta):
    def __init__(
            self,
            redis_client: Union[Redis, RedisCluster],
    ):
        self.__redis_client = redis_client
        HealthChecks().add(self)

    async def health(self) -> RedisHealthcheck:
        try:
            await self.__redis_client.ping()
            return RedisHealthcheck(status=HealthStatus.OK, message="Redis can be queried.")
        except Exception as error:
            logging.error("Exception while pinging Redis", exc_info=error)
            return RedisHealthcheck(status=HealthStatus.ERROR, message=str(error))
