import logging

from fastapi import FastAPI

from talk2powersystemllm.app.models import (
    GoodToGoInfo,
    GoodToGoStatus,
    HealthStatus,
    Severity,
)
from talk2powersystemllm.app.server.services.healthchecks import HealthChecks

logger = logging.getLogger(__name__)


async def update_gtg_info(fastapi_app: FastAPI) -> None:
    logger.info("Updating gtg info")
    try:
        health_info = await HealthChecks().get_health()

        is_healthy = True
        if health_info.status != HealthStatus.OK:
            for check in health_info.healthChecks:
                if check.status == HealthStatus.ERROR and check.severity == Severity.HIGH:
                    is_healthy = False
                    break

        status = GoodToGoStatus.OK if is_healthy else GoodToGoStatus.UNAVAILABLE
        fastapi_app.state.gtg_info = GoodToGoInfo(gtg=status)
    except Exception:
        logger.exception(f"Failed to update GTG info")
        fastapi_app.state.gtg_info = GoodToGoInfo(gtg=GoodToGoStatus.UNAVAILABLE)
