from typing import Annotated

from fastapi import APIRouter, Header, Request, Response, status
from fastapi.responses import HTMLResponse

from talk2powersystemllm.app.models import (
    AboutInfo,
    GoodToGoInfo,
    GoodToGoStatus,
    HealthInfo,
)
from talk2powersystemllm.app.server.services import update_gtg_info

router = APIRouter(tags=["Health-Check"])


# noinspection PyUnusedLocal
@router.get(
    "/__trouble",
    summary="Returns an html rendering of the trouble document for the application",
    response_class=HTMLResponse,
    name="__trouble",
)
async def trouble(
    request: Request, x_request_id: Annotated[str | None, Header()] = None
):
    return HTMLResponse(content=request.app.state.trouble_html)


# noinspection PyUnusedLocal
@router.get(
    "/__health",
    summary="Returns the health status of the application",
    response_model=HealthInfo,
)
async def health(
    request: Request, x_request_id: Annotated[str | None, Header()] = None
):
    health_info = await request.app.state.health_checks_registry.get_health()
    for healthcheck in health_info.healthChecks:
        healthcheck.troubleshooting = (
            f"{request.url_for('__trouble')}{healthcheck.troubleshooting}"
        )
    return health_info


# noinspection PyUnusedLocal
@router.get(
    "/__gtg",
    summary="Returns if the service is good to go",
    response_model=GoodToGoInfo,
    responses={
        503: {
            "model": GoodToGoInfo,
            "description": "The service is unavailable",
            "content": {
                "application/json": {
                    "example": {"gtg": GoodToGoStatus.UNAVAILABLE},
                    "schema": {"$ref": "#/components/schemas/GoodToGoInfo"},
                }
            },
        }
    },
)
async def gtg(
    request: Request,
    response: Response,
    x_request_id: Annotated[str | None, Header()] = None,
    cache: bool = True,
):
    if not cache:
        await update_gtg_info(request.app)

    gtg_info = request.app.state.gtg_info

    if gtg_info.gtg == GoodToGoStatus.UNAVAILABLE:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return gtg_info


# noinspection PyUnusedLocal
@router.get(
    "/__about",
    summary="Describes the application and provides build info about the component",
    response_model=AboutInfo,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def about(
    request: Request, x_request_id: Annotated[str | None, Header()] = None
) -> AboutInfo:
    return request.app.state.about_info
