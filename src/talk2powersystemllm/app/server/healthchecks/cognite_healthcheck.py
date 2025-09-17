import logging

from talk2powersystemllm.tools import CogniteSession
from .healthchecks import HealthChecks
from ..singleton import SingletonMeta
from ...models import HealthCheck, Severity, HealthStatus


class CogniteHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/cognite-healthcheck"
    name: str = "Cognite Health Check"
    type: str = "cognite"
    impact: str = "Chat bot won't be able to query Cognite or tools may not function as expected."
    troubleshooting: str = "#cognite-health-check-status-is-not-ok"
    description: str = "Checks if Cognite can be queried by listing the time series with limit of 1."


class CogniteHealthchecker(metaclass=SingletonMeta):
    def __init__(
            self,
            cognite_session: CogniteSession,
    ):
        self.__cognite_session = cognite_session
        HealthChecks().add(self)

    async def health(self) -> CogniteHealthcheck:
        try:
            self.__cognite_session.client().time_series.list(
                limit=1
            )
            return CogniteHealthcheck(status=HealthStatus.OK, message="Cognite can be queried.")
        except Exception as error:
            logging.error("Exception while querying Cognite", exc_info=error)
            return CogniteHealthcheck(status=HealthStatus.ERROR, message=str(error))
