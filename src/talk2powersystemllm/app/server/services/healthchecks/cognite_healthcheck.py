import logging

from talk2powersystemllm.app.models import HealthCheck, HealthStatus, Severity
from talk2powersystemllm.app.server.services.healthchecks.healthchecks import (
    HealthProvider,
)
from talk2powersystemllm.tools import CogniteSession

logger = logging.getLogger(__name__)


class CogniteHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/cognite-healthcheck"
    name: str = "Cognite Health Check"
    type: str = "cognite"
    impact: str = (
        "Chat bot won't be able to query Cognite or tools may not function as expected."
    )
    troubleshooting: str = "#cognite-health-check-status-is-not-ok"
    description: str = (
        "Checks if Cognite can be queried by listing the time series with limit of 1."
    )


class CogniteHealthchecker(HealthProvider):
    def __init__(
        self,
        cognite_session: CogniteSession,
    ):
        self.__cognite_session = cognite_session

    async def health(self) -> CogniteHealthcheck:
        try:
            self.__cognite_session.client().time_series.list(limit=1)
            return CogniteHealthcheck(
                status=HealthStatus.OK, message="Cognite can be queried."
            )
        except Exception as error:
            logger.exception("Exception raised in Cognite health check")
            return CogniteHealthcheck(
                status=HealthStatus.ERROR, message="Cognite error " + str(error)
            )
