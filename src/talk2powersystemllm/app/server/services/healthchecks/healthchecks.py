import asyncio
from abc import ABC, abstractmethod

from talk2powersystemllm.app.models import HealthInfo, HealthStatus, HealthCheck


class HealthProvider(ABC):
    @abstractmethod
    async def health(self) -> HealthCheck:
        pass


class HealthChecks:

    def __init__(self):
        self.registered_health_checks: set[HealthProvider] = set()

    def add(self, health_provider: HealthProvider):
        self.registered_health_checks.add(health_provider)

    async def get_health(self) -> HealthInfo:
        health_checks = list(await asyncio.gather(*[hc.health() for hc in self.registered_health_checks]))

        overall_status = HealthStatus.OK
        if any(hc.status == HealthStatus.ERROR for hc in health_checks):
            overall_status = HealthStatus.ERROR
        elif any(hc.status == HealthStatus.WARNING for hc in health_checks):
            overall_status = HealthStatus.WARNING
        return HealthInfo(
            status=overall_status,
            healthChecks=health_checks,
        )
