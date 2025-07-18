import asyncio
import logging
from urllib.parse import urlparse, urlunparse

from fastapi import Request

from ..singleton import SingletonMeta
from ...models import HealthInfo, HealthStatus


class HealthChecks(metaclass=SingletonMeta):

    def __init__(self):
        self.registered_health_checks = set()

    def add(self, cls):
        self.registered_health_checks.add(cls)

    async def get_health(self, request: Request | None = None) -> HealthInfo:
        health_checks = await asyncio.gather(*[hc.health() for hc in self.registered_health_checks])

        health_info = HealthInfo(
            status=HealthStatus.OK,
            healthChecks=health_checks,
        )
        for health_check in health_checks:
            health_check.troubleshooting = self.get_trouble_link(health_check, request)
            if health_check.status == HealthStatus.WARNING and health_info.status != HealthStatus.ERROR:
                health_info.status = HealthStatus.WARNING
            elif health_check.status == HealthStatus.ERROR:
                health_info.status = HealthStatus.ERROR
        return health_info

    def get_trouble_link(self, health_check, request: Request | None = None) -> str:
        condition_section = health_check.troubleshooting
        try:
            trouble_link = self.build_trouble_doc_url(condition_section, request)
            if self.is_valid_url(trouble_link):
                return trouble_link
        except Exception as e:
            logging.error(f"Error while trying to get trouble link", exc_info=e)
        return condition_section

    @staticmethod
    def is_valid_url(url: str):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def build_trouble_doc_url(
            condition_section: str,
            request: Request | None = None,
    ) -> str:
        if request:
            url = urlparse(str(request.url))
            new_url = url._replace(
                path=f"{request.scope.get('root_path', '')}" + "__trouble"
            )
            return str(urlunparse(new_url)) + condition_section
        return condition_section
