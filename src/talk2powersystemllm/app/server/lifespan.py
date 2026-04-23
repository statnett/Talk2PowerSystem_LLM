import logging
from contextlib import asynccontextmanager
from pathlib import Path

import markdown
import msal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cachetools import TTLCache
from fastapi import FastAPI
from langgraph.checkpoint.redis import AsyncRedisSaver
from redis.asyncio import Redis, RedisCluster

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.app.server.services import (
    GraphDBHealthchecker,
    HealthChecks,
    LLMHealthchecker,
    RedisHealthchecker,
    create_redis_client,
    update_about_info,
    update_gtg_info,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    logger.info("Starting the application")

    settings = fastapi_app.state.settings

    async with (
        create_redis_client(settings.redis) as redis_client,
        AsyncRedisSaver.from_conn_string(
            redis_client=redis_client,
            ttl={
                "default_ttl": settings.redis.ttl,
                "refresh_on_read": settings.redis.ttl_refresh_on_read,
            },
        ) as redis_saver,
    ):
        await redis_saver.asetup()

        agent_factory = Talk2PowerSystemAgentFactory(
            settings.agent_config,
            checkpointer=redis_saver,
        )
        fastapi_app.state.agent_factory = agent_factory

        health_checks_registry = await create_health_checks_registry(
            fastapi_app, agent_factory, redis_client
        )
        fastapi_app.state.health_checks_registry = health_checks_registry

        if settings.security.enabled:
            fastapi_app.state.jwks_cache = TTLCache(
                maxsize=1, ttl=settings.security.ttl
            )
            if agent_factory.cognite_enabled:
                if not agent_factory.cognite_settings.client_secret:
                    raise ValueError(
                        "Cognite client secret must be provided in order to register the Cognite tools, "
                        "when the security is enabled."
                    )
                fastapi_app.state.confidential_app = msal.ConfidentialClientApplication(
                    settings.security.client_id,
                    authority=settings.security.authority,
                    client_credential=agent_factory.cognite_settings.client_secret,
                )
                fastapi_app.state.cognite_scopes = [
                    f"{agent_factory.cognite_settings.base_url}/.default"
                ]

        scheduler = await create_scheduler(fastapi_app, settings)

        await update_gtg_info(fastapi_app)
        await update_about_info(fastapi_app)
        fastapi_app.state.trouble_html = get_trouble_html(settings.trouble_md_path)

        logger.info("Application is running")

        yield

        logger.info("Destroying the application")
        scheduler.shutdown()
        logger.info("Scheduler is stopped")


async def create_health_checks_registry(
    fastapi_app: FastAPI,
    agent_factory: Talk2PowerSystemAgentFactory,
    redis_client: Redis | RedisCluster,
) -> HealthChecks:
    health_checks_registry = HealthChecks()
    health_checks_registry.add(GraphDBHealthchecker(agent_factory))
    health_checks_registry.add(RedisHealthchecker(redis_client))
    llm_health_check = LLMHealthchecker(redis_client)
    fastapi_app.state.callbacks = [llm_health_check]
    health_checks_registry.add(llm_health_check)
    return health_checks_registry


async def create_scheduler(fastapi_app: FastAPI, settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        update_gtg_info,
        "interval",
        args=[fastapi_app],
        seconds=settings.gtg_refresh_interval,
    )
    scheduler.add_job(
        update_about_info,
        "interval",
        args=[fastapi_app],
        seconds=settings.about_refresh_interval,
    )

    scheduler.start()
    return scheduler


def get_trouble_html(trouble_md_path: Path):
    with open(trouble_md_path, "r", encoding="utf-8") as trouble_md_file:
        trouble_md_text = trouble_md_file.read()
        return markdown.markdown(
            trouble_md_text,
            extensions=["toc", "fenced_code"],
            extension_configs={"toc": {"title": "Table of Contents"}},
        )
