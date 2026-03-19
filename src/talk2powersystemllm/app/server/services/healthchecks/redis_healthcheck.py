import logging

from redis.asyncio import Redis, RedisCluster

from talk2powersystemllm.app.models import HealthCheck, Severity, HealthStatus
from talk2powersystemllm.app.server.services.healthchecks.healthchecks import HealthProvider

logger = logging.getLogger(__name__)


class RedisHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/redis-healthcheck"
    name: str = "Redis Health Check"
    type: str = "redis"
    impact: str = "Redis is inaccessible and the chat bot can't function"
    troubleshooting: str = "#redis-health-check-status-is-not-ok"
    description: str = "Checks if Redis can be queried."


class RedisHealthchecker(HealthProvider):
    def __init__(
        self,
        redis_client: Redis | RedisCluster,
    ):
        self.__redis_client = redis_client

    async def health(self) -> RedisHealthcheck:
        try:
            await self.__redis_client.ping()
            return RedisHealthcheck(status=HealthStatus.OK, message="Redis can be queried.")
        except Exception as error:
            logger.exception("Exception while pinging Redis")
            return RedisHealthcheck(status=HealthStatus.ERROR, message=str(error))
